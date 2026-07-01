from binascii import crc32
import hashlib
import hmac
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from threading import Thread
from uuid import uuid4
from zipfile import ZipFile
from zlib import compress

from fastapi.testclient import TestClient

from app.main import (
    MAX_FIGMA_IMAGE_FILL_BYTES,
    app,
    configure_inference_provider,
    configure_object_storage,
    configure_persistent_store,
    configure_worker_token,
    decode_png_rgba,
    extract_qwen_layered_slices,
    store,
)
from app.persistence import create_production_store


client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[2]


def minimal_psd_header(width: int, height: int, *, version: int = 1) -> bytes:
    return (
        b"8BPS"
        + version.to_bytes(2, "big")
        + b"\x00" * 6
        + (4).to_bytes(2, "big")
        + height.to_bytes(4, "big")
        + width.to_bytes(4, "big")
        + (8).to_bytes(2, "big")
        + (3).to_bytes(2, "big")
    )


def psd_additional_layer_info(key: bytes, payload: bytes) -> bytes:
    if len(key) != 4:
        raise ValueError("PSD additional layer info key must be 4 bytes")
    padded_payload = payload + (b"\x00" if len(payload) % 2 else b"")
    return b"8BIM" + key + len(payload).to_bytes(4, "big") + padded_payload


def psd_unicode_layer_name(name: str) -> bytes:
    encoded = name.encode("utf-16-be")
    return psd_additional_layer_info(b"luni", len(name).to_bytes(4, "big") + encoded)


def psd_type_tool_text(text: str, *, font: str = "Game UI Sans", size: int = 32, color: str = "#ffcc33") -> bytes:
    font_entry = f"/Font ({font}) " if font else ""
    engine_data = (
        f"/EngineDict << /Editor << /Text ({text}) >> "
        f"/StyleRun << /RunArray [ << /StyleSheet << /StyleSheetData "
        f"<< {font_entry}/FontSize {size} /FillColor ({color}) >> >> >> ] >> >>"
    ).encode("utf-8")
    return psd_additional_layer_info(b"TySh", engine_data)


def psd_layer_record(
    name: str,
    rect: dict[str, int],
    *,
    opacity: int = 255,
    hidden: bool = False,
    unicode_name: str | None = None,
    section_divider: int | None = None,
    smart_object: bool = False,
    type_tool_text: str | None = None,
) -> bytes:
    name_bytes = name.encode("utf-8")
    pascal_name = bytes([len(name_bytes)]) + name_bytes
    pascal_name += b"\x00" * ((4 - (len(pascal_name) % 4)) % 4)
    additional_info = b""
    if unicode_name:
        additional_info += psd_unicode_layer_name(unicode_name)
    if section_divider is not None:
        additional_info += psd_additional_layer_info(b"lsct", section_divider.to_bytes(4, "big"))
    if smart_object:
        additional_info += psd_additional_layer_info(b"SoLd", b"\x00\x00\x00\x01")
    if type_tool_text:
        additional_info += psd_type_tool_text(type_tool_text)
    extra_data = (0).to_bytes(4, "big") + (0).to_bytes(4, "big") + pascal_name + additional_info
    return (
        rect["y"].to_bytes(4, "big")
        + rect["x"].to_bytes(4, "big")
        + (rect["y"] + rect["height"]).to_bytes(4, "big")
        + (rect["x"] + rect["width"]).to_bytes(4, "big")
        + (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big", signed=True)
        + (2).to_bytes(4, "big")
        + b"8BIM"
        + b"norm"
        + opacity.to_bytes(1, "big")
        + b"\x00"
        + ((2 if hidden else 0).to_bytes(1, "big"))
        + b"\x00"
        + len(extra_data).to_bytes(4, "big")
        + extra_data
    )


def minimal_psd_with_layers(width: int, height: int) -> bytes:
    layer_records = [
        psd_layer_record("Main Panel", {"x": 24, "y": 32, "width": 240, "height": 120}, opacity=255),
        psd_layer_record("Hidden CTA Button", {"x": 180, "y": 170, "width": 96, "height": 44}, opacity=128, hidden=True),
    ]
    channel_pixels = b"\x00\x00" * len(layer_records)
    layer_info = len(layer_records).to_bytes(2, "big") + b"".join(layer_records) + channel_pixels
    layer_mask_section = len(layer_info).to_bytes(4, "big") + layer_info
    return (
        minimal_psd_header(width, height)
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + len(layer_mask_section).to_bytes(4, "big")
        + layer_mask_section
    )


def minimal_psd_with_advanced_layers(width: int, height: int) -> bytes:
    layer_records = [
        psd_layer_record(
            "Group",
            {"x": 0, "y": 0, "width": width, "height": height},
            unicode_name="商店弹窗组",
            section_divider=1,
        ),
        psd_layer_record(
            "Smart",
            {"x": 48, "y": 64, "width": 180, "height": 96},
            unicode_name="购买按钮智能对象",
            smart_object=True,
        ),
    ]
    channel_pixels = b"\x00\x00" * len(layer_records)
    layer_info = len(layer_records).to_bytes(2, "big") + b"".join(layer_records) + channel_pixels
    layer_mask_section = len(layer_info).to_bytes(4, "big") + layer_info
    return (
        minimal_psd_header(width, height)
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + len(layer_mask_section).to_bytes(4, "big")
        + layer_mask_section
    )


def minimal_psd_with_closed_group(width: int, height: int) -> bytes:
    layer_records = [
        psd_layer_record(
            "Group",
            {"x": 0, "y": 0, "width": width, "height": height},
            unicode_name="商店弹窗组",
            section_divider=1,
        ),
        psd_layer_record(
            "Smart",
            {"x": 48, "y": 64, "width": 180, "height": 96},
            unicode_name="购买按钮智能对象",
            smart_object=True,
        ),
        psd_layer_record(
            "Group End",
            {"x": 0, "y": 0, "width": 0, "height": 0},
            section_divider=3,
        ),
        psd_layer_record(
            "Badge",
            {"x": 420, "y": 20, "width": 48, "height": 48},
            unicode_name="外部角标",
        ),
    ]
    channel_pixels = b"\x00\x00" * len(layer_records)
    layer_info = len(layer_records).to_bytes(2, "big") + b"".join(layer_records) + channel_pixels
    layer_mask_section = len(layer_info).to_bytes(4, "big") + layer_info
    return (
        minimal_psd_header(width, height)
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + len(layer_mask_section).to_bytes(4, "big")
        + layer_mask_section
    )


def minimal_psd_with_text_layer(width: int, height: int) -> bytes:
    layer_records = [
        psd_layer_record(
            "Title",
            {"x": 80, "y": 42, "width": 220, "height": 64},
            unicode_name="主标题文本",
            type_tool_text="START",
        ),
    ]
    channel_pixels = b"\x00\x00" * len(layer_records)
    layer_info = len(layer_records).to_bytes(2, "big") + b"".join(layer_records) + channel_pixels
    layer_mask_section = len(layer_info).to_bytes(4, "big") + layer_info
    return (
        minimal_psd_header(width, height)
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + len(layer_mask_section).to_bytes(4, "big")
        + layer_mask_section
    )


def minimal_psd_with_text_style_without_font(width: int, height: int) -> bytes:
    layer_records = [
        psd_layer_record(
            "Title",
            {"x": 80, "y": 42, "width": 220, "height": 64},
            unicode_name="主标题文本",
            type_tool_text="START",
        ).replace(b"/Font (Game UI Sans) ", b""),
    ]
    channel_pixels = b"\x00\x00" * len(layer_records)
    layer_info = len(layer_records).to_bytes(2, "big") + b"".join(layer_records) + channel_pixels
    layer_mask_section = len(layer_info).to_bytes(4, "big") + layer_info
    return (
        minimal_psd_header(width, height)
        + (0).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + len(layer_mask_section).to_bytes(4, "big")
        + layer_mask_section
    )


def minimal_png_header(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + (13).to_bytes(4, "big")
        + b"IHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "big") + chunk_type + payload + crc32(chunk_type + payload).to_bytes(4, "big")


def rgba_png_with_opaque_rects(width: int, height: int, rects: list[dict[str, int]]) -> bytes:
    rows: list[bytes] = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            alpha = 0
            for rect in rects:
                inside_x = rect["x"] <= x < rect["x"] + rect["width"]
                inside_y = rect["y"] <= y < rect["y"] + rect["height"]
                if inside_x and inside_y:
                    alpha = 255
                    break
            row.extend([255, 255, 255, alpha])
        rows.append(bytes(row))
    ihdr = (
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
    )
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", compress(b"".join(rows))) + png_chunk(b"IEND", b"")


def auth_headers() -> dict[str, str]:
    payload = {
        "email": f"designer-{uuid4().hex}@gameuiagent.dev",
        "password": "secret-pass",
        "name": "Game Designer",
    }
    created = client.post("/api/auth/register", json=payload)
    assert created.status_code == 201

    logged_in = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_homepage_capabilities_match_platform_scope():
    response = client.get("/api/marketing/capabilities")

    assert response.status_code == 200
    capabilities = {item["id"] for item in response.json()["capabilities"]}
    assert {
        "ai-studio",
        "text-to-image",
        "image-to-image",
        "ui-slicing",
        "unity-export",
        "cocos-export",
        "godot-export",
        "engine-mcp",
        "team-roles",
        "password-reset",
        "docs-center",
    }.issubset(capabilities)


def test_project_detail_loads_created_project_for_studio_navigation():
    headers = auth_headers()
    created = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Studio Navigation Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    )
    assert created.status_code == 201
    project = created.json()

    detail_response = client.get(f"/api/projects/{project['id']}", headers=headers)

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == project["id"]
    assert detail_response.json()["name"] == "Studio Navigation Project"
    assert detail_response.json()["target_engine"] == "unity"


def test_auth_stores_salted_password_hashes():
    email = f"secure-{uuid4().hex}@gameuiagent.dev"
    password = "secret-pass"

    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": "Secure User"},
    )

    assert response.status_code == 201
    stored_hash = store["users"][email]["password_hash"]
    assert stored_hash.startswith("pbkdf2_sha256$")
    assert password not in stored_hash
    assert len(stored_hash.split("$")) == 4


def test_sqlite_store_persists_users_projects_and_assets_across_reload(tmp_path):
    db_path = tmp_path / "gameuiagent.sqlite3"
    configure_persistent_store(str(db_path))
    email = f"persist-{uuid4().hex}@gameuiagent.dev"
    password = "secret-pass"

    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": "Persistent User"},
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    project_response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Persistent Production Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    )
    project = project_response.json()
    asset_response = client.post(
        f"/api/projects/{project['id']}/assets",
        headers=headers,
        json={
            "name": "persistent-hud.png",
            "type": "original_upload",
            "url": "s3://gameuiagent-production/persistent-hud.png",
            "width": 1920,
            "height": 1080,
            "usage": "source_ui",
            "tags": ["production"],
        },
    )
    asset = asset_response.json()

    reloaded_store = create_production_store()
    reloaded_store.configure(str(db_path))

    assert register_response.status_code == 201
    assert project_response.status_code == 201
    assert asset_response.status_code == 201
    assert db_path.exists()
    assert reloaded_store["users"][email]["name"] == "Persistent User"
    assert reloaded_store["projects"][project["id"]]["name"] == "Persistent Production Project"
    assert reloaded_store["assets"][asset["id"]]["url"].startswith("s3://gameuiagent-production/")


def test_binary_asset_upload_persists_file_metadata_and_downloads(tmp_path):
    db_path = tmp_path / "object-store.sqlite3"
    object_store_path = tmp_path / "objects"
    configure_persistent_store(str(db_path))
    configure_object_storage(str(object_store_path))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Binary Upload Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    payload = b"real-binary-game-ui-asset"

    upload_response = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "binary-hud.png",
            "type": "original_upload",
            "width": "1920",
            "height": "1080",
            "usage": "source_ui",
            "tags": "hud,production",
        },
        files={"file": ("binary-hud.png", payload, "image/png")},
    )

    assert upload_response.status_code == 201
    asset = upload_response.json()
    assert asset["source"] == "object_storage"
    assert asset["metadata"]["size_bytes"] == len(payload)
    assert asset["metadata"]["content_type"] == "image/png"
    assert asset["metadata"]["sha256"]
    assert (object_store_path / asset["metadata"]["storage_key"]).exists()

    reloaded_store = create_production_store()
    reloaded_store.configure(str(db_path))
    assert reloaded_store["assets"][asset["id"]]["metadata"]["storage_key"] == asset["metadata"]["storage_key"]

    download_response = client.get(
        f"/api/projects/{project['id']}/assets/{asset['id']}/download",
        headers=headers,
    )

    assert download_response.status_code == 200
    assert download_response.content == payload
    assert download_response.headers["content-type"] == "image/png"


def test_binary_asset_upload_rejects_unsupported_type_and_empty_file(tmp_path):
    configure_persistent_store(str(tmp_path / "invalid-object.sqlite3"))
    configure_object_storage(str(tmp_path / "invalid-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Invalid Binary Upload Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    unsupported_response = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "script.exe",
            "type": "executable",
            "width": "1920",
            "height": "1080",
            "usage": "source_ui",
        },
        files={"file": ("script.exe", b"binary", "application/octet-stream")},
    )
    empty_response = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "empty.png",
            "type": "original_upload",
            "width": "1920",
            "height": "1080",
            "usage": "source_ui",
        },
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert unsupported_response.status_code == 422
    assert empty_response.status_code == 422


def test_production_readiness_reports_durable_sqlite_store(tmp_path):
    db_path = tmp_path / "readiness.sqlite3"
    object_store_path = tmp_path / "readiness-objects"
    configure_persistent_store(str(db_path))
    configure_object_storage(str(object_store_path))

    response = client.get("/api/system/production-readiness")

    assert response.status_code == 200
    readiness = response.json()
    assert readiness["status"] == "production_foundation_ready"
    assert readiness["storage"]["driver"] == "sqlite"
    assert readiness["storage"]["durable"] is True
    assert readiness["storage"]["ephemeral"] is False
    assert readiness["object_storage"]["driver"] == "local_fs"
    assert readiness["object_storage"]["durable"] is True
    assert "durable_store" in readiness["checks"]
    assert "object_storage" in readiness["checks"]


def test_sqlite_store_persists_nested_password_hash_updates(tmp_path):
    db_path = tmp_path / "nested-update.sqlite3"
    configure_persistent_store(str(db_path))
    email = f"nested-{uuid4().hex}@gameuiagent.dev"
    old_password = "old-secret"
    new_password = "new-secret"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": old_password, "name": "Nested Update User"},
    )
    client.post("/api/auth/password-reset/request", json={"email": email})
    reset_token = next(
        token
        for token, reset in store["password_reset_tokens"].items()
        if reset["email"] == email
    )

    confirm_response = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": new_password},
    )
    reloaded_store = create_production_store()
    reloaded_store.configure(str(db_path))

    assert confirm_response.status_code == 200
    assert reloaded_store["users"][email]["password_hash"] == store["users"][email]["password_hash"]
    assert old_password not in reloaded_store["users"][email]["password_hash"]


def test_password_reset_rotates_password_and_consumes_token():
    email = f"reset-{uuid4().hex}@gameuiagent.dev"
    old_password = "old-secret"
    new_password = "new-secret"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": old_password, "name": "Reset User"},
    )

    request_response = client.post("/api/auth/password-reset/request", json={"email": email})

    assert request_response.status_code == 200
    assert "reset_token" not in request_response.json()
    reset_token = next(
        token
        for token, reset in store["password_reset_tokens"].items()
        if reset["email"] == email
    )
    assert reset_token.startswith("rst_")

    confirm_response = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": new_password},
    )

    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "password_reset"
    assert client.post(
        "/api/auth/login",
        json={"email": email, "password": old_password},
    ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"email": email, "password": new_password},
    ).status_code == 200
    assert client.post(
        "/api/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "another-secret"},
    ).status_code == 404


def test_password_reset_sends_configured_smtp_email_and_persists_delivery(tmp_path, monkeypatch):
    db_path = tmp_path / "smtp-email.sqlite3"
    configure_persistent_store(str(db_path))
    email = f"smtp-reset-{uuid4().hex}@gameuiagent.dev"
    sent_messages: list[object] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            assert host == "smtp.gameuiagent.dev"
            assert port == 2525
            assert timeout == 10

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *_args) -> None:
            return None

        def starttls(self) -> None:
            return None

        def login(self, username: str, password: str) -> None:
            assert username == "mailer"
            assert password == "mailer-secret"

        def send_message(self, message: object) -> None:
            sent_messages.append(message)

    monkeypatch.setenv("GAMEUIAGENT_SMTP_HOST", "smtp.gameuiagent.dev")
    monkeypatch.setenv("GAMEUIAGENT_SMTP_PORT", "2525")
    monkeypatch.setenv("GAMEUIAGENT_SMTP_USERNAME", "mailer")
    monkeypatch.setenv("GAMEUIAGENT_SMTP_PASSWORD", "mailer-secret")
    monkeypatch.setenv("GAMEUIAGENT_EMAIL_FROM", "no-reply@gameuiagent.dev")
    monkeypatch.setenv("GAMEUIAGENT_APP_URL", "https://app.gameuiagent.dev")
    monkeypatch.setattr("app.main.smtplib.SMTP", FakeSMTP)
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "old-secret", "name": "SMTP Reset User"},
    )

    request_response = client.post("/api/auth/password-reset/request", json={"email": email})

    assert request_response.status_code == 200
    response_payload = request_response.json()
    assert response_payload["delivery"] == "smtp"
    assert "reset_token" not in response_payload
    assert len(sent_messages) == 1
    message = sent_messages[0]
    assert message["To"] == email
    assert message["From"] == "no-reply@gameuiagent.dev"
    assert "Password reset" in message["Subject"]
    reset_token = next(
        token
        for token, reset in store["password_reset_tokens"].items()
        if reset["email"] == email
    )
    assert reset_token in message.get_content()
    assert "https://app.gameuiagent.dev/reset-password" in message.get_content()
    delivery = next(iter(store["email_deliveries"].values()))
    assert delivery["status"] == "sent"
    assert delivery["provider"] == "smtp"
    assert delivery["template"] == "password_reset"
    assert delivery["to"] == email

    reloaded_store = create_production_store()
    reloaded_store.configure(str(db_path))
    assert next(iter(reloaded_store["email_deliveries"].values()))["status"] == "sent"


def test_team_roles_allow_owner_to_manage_members():
    headers = auth_headers()

    team_response = client.post("/api/teams", headers=headers, json={"name": "Live Ops UI Team"})

    assert team_response.status_code == 201
    team = team_response.json()
    assert team["name"] == "Live Ops UI Team"
    assert team["members"][0]["role"] == "owner"

    invite_response = client.post(
        f"/api/teams/{team['id']}/members",
        headers=headers,
        json={"email": "artist@gameuiagent.dev", "role": "designer"},
    )

    assert invite_response.status_code == 201
    membership = invite_response.json()
    assert membership["email"] == "artist@gameuiagent.dev"
    assert membership["role"] == "designer"

    update_response = client.patch(
        f"/api/teams/{team['id']}/members/{membership['id']}",
        headers=headers,
        json={"role": "developer"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["role"] == "developer"

    teams_response = client.get("/api/teams", headers=headers)
    assert teams_response.status_code == 200
    listed_team = teams_response.json()["teams"][0]
    assert listed_team["member_count"] == 2
    assert {member["role"] for member in listed_team["members"]} == {"owner", "developer"}


def test_docs_center_returns_product_api_and_plugin_guides():
    response = client.get("/api/docs")

    assert response.status_code == 200
    docs = response.json()["docs"]
    assert [doc["slug"] for doc in docs] == [
        "getting-started",
        "developer-api",
        "engine-plugins",
    ]
    assert docs[1]["sections"] == ["Authentication", "Cost estimate", "Execute", "Poll", "Cancel", "Webhook"]
    assert "Unity" in docs[2]["engines"]
    assert "Unreal" in docs[2]["engines"]


def test_uploaded_asset_drives_image_to_image_segmentation_and_unity_export():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Uploaded HUD Flow",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    upload_response = client.post(
        f"/api/projects/{project['id']}/assets",
        headers=headers,
        json={
            "name": "main-menu-reference.png",
            "type": "reference_image",
            "url": "https://assets.gameuiagent.dev/main-menu-reference.png",
            "width": 1920,
            "height": 1080,
            "usage": "image_to_image",
        },
    )

    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["source"] == "upload"
    assert uploaded["metadata"]["width"] == 1920

    listed_assets = client.get(f"/api/projects/{project['id']}/assets", headers=headers).json()["assets"]
    assert listed_assets[0]["id"] == uploaded["id"]

    job_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "image_to_image",
            "prompt": "turn this into a sci-fi battle HUD",
            "input_asset_id": uploaded["id"],
            "negative_prompt": "blur, low quality",
            "seed": 42,
            "model": "game-ui-xl",
            "count": 2,
        },
    )

    assert job_response.status_code == 201
    job = job_response.json()
    assert job["input_asset"]["id"] == uploaded["id"]
    assert job["parameters"]["negative_prompt"] == "blur, low quality"
    assert job["candidates"][0]["asset_id"] == job["result_asset"]["id"]
    assert job["estimated_credits"] == 4

    segmentation_response = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": uploaded["id"]},
    )

    assert segmentation_response.status_code == 201
    segmentation = segmentation_response.json()
    assert segmentation["source_asset_id"] == uploaded["id"]
    assert segmentation["ir_id"] == segmentation["ir"]["id"]
    assert segmentation["slices"][0]["editable_bounds"] is True
    assert segmentation["slices"][1]["type"] == "button"
    assert segmentation["confidence"] >= 0.8

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": "unity"},
    )

    assert export_response.status_code == 201
    assert export_response.json()["package"]["manifest"]["asset_ir"]["node_count"] >= 4


def test_queued_ai_job_persists_and_worker_completes_result_asset(tmp_path):
    db_path = tmp_path / "queued-ai.sqlite3"
    configure_persistent_store(str(db_path))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Queued AI Production Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    job_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text_to_image",
            "prompt": "production worker generated RPG HUD",
            "model": "game-ui-xl",
            "count": 2,
            "execution_mode": "queued",
        },
    )

    assert job_response.status_code == 201
    job = job_response.json()
    assert job["status"] == "queued"
    assert job["progress"] == 0
    assert job["queue"]["status"] == "queued"
    assert "result_asset" not in job

    reloaded_store = create_production_store()
    reloaded_store.configure(str(db_path))
    assert reloaded_store["jobs"][job["id"]]["status"] == "queued"
    assert reloaded_store["ai_job_queue"][job["queue"]["id"]]["job_id"] == job["id"]

    worker_response = client.post("/api/system/ai-worker/run-next")

    assert worker_response.status_code == 200
    completed = worker_response.json()["job"]
    assert completed["id"] == job["id"]
    assert completed["status"] == "succeeded"
    assert completed["progress"] == 100
    assert completed["result_asset"]["source"] == "ai"
    assert completed["candidates"][0]["asset_id"] == completed["result_asset"]["id"]

    completed_reload = create_production_store()
    completed_reload.configure(str(db_path))
    assert completed_reload["jobs"][job["id"]]["status"] == "succeeded"
    assert completed_reload["ai_job_queue"][job["queue"]["id"]]["status"] == "succeeded"


def test_ai_worker_endpoint_requires_configured_worker_token(tmp_path):
    configure_persistent_store(str(tmp_path / "worker-auth.sqlite3"))
    configure_worker_token("worker-secret")
    try:
        unauthorized_response = client.post("/api/system/ai-worker/run-next")
        authorized_response = client.post(
            "/api/system/ai-worker/run-next",
            headers={"X-Worker-Token": "worker-secret"},
        )
        readiness_response = client.get("/api/system/production-readiness")

        assert unauthorized_response.status_code == 401
        assert authorized_response.status_code == 200
        assert "worker_auth" in readiness_response.json()["checks"]
    finally:
        configure_worker_token(None)


def test_ai_worker_uses_configured_inference_provider_and_persists_run(tmp_path):
    db_path = tmp_path / "inference-provider.sqlite3"
    configure_persistent_store(str(db_path))
    configure_inference_provider("local-deterministic")
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "Inference Provider Project",
                "target_engine": "unity",
                "canvas": {"width": 1280, "height": 720},
            },
        ).json()
        job = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={
                "kind": "text_to_image",
                "prompt": "production inference provider HUD",
                "model": "game-ui-xl",
                "seed": 77,
                "count": 1,
                "execution_mode": "queued",
            },
        ).json()

        worker_response = client.post("/api/system/ai-worker/run-next")

        assert worker_response.status_code == 200
        completed = worker_response.json()["job"]
        assert completed["status"] == "succeeded"
        assert completed["inference"]["provider"] == "local-deterministic"
        assert completed["result_asset"]["url"].startswith("/inference/local-deterministic/")
        assert completed["result_asset"]["metadata"]["inference_run_id"] == completed["inference"]["run_id"]

        reloaded_store = create_production_store()
        reloaded_store.configure(str(db_path))
        inference_run = reloaded_store["inference_runs"][completed["inference"]["run_id"]]
        assert inference_run["request"]["prompt"] == "production inference provider HUD"
        assert inference_run["request"]["model"] == "game-ui-xl"
        assert inference_run["response"]["asset_url"] == completed["result_asset"]["url"]
        assert "inference_provider" in client.get("/api/system/production-readiness").json()["checks"]
    finally:
        configure_inference_provider("local-deterministic")


def test_ai_queue_lease_timeout_requeues_and_dead_letters(tmp_path):
    configure_persistent_store(str(tmp_path / "queue-lease.sqlite3"))
    configure_inference_provider("failing")
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Reliable Queue UI", "target_engine": "unity", "canvas": {"width": 1280, "height": 720}},
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "lease protected job", "execution_mode": "queued"},
    ).json()
    queue_id = job["queue"]["id"]

    first_dequeue = client.post("/api/worker/jobs/dequeue")
    second_dequeue = client.post("/api/worker/jobs/dequeue")
    assert first_dequeue.json()["status"] == "dequeued"
    assert second_dequeue.json()["status"] == "idle"

    store["ai_job_queue"][queue_id]["locked_at"] = "2026-06-30T00:00:00+00:00"
    store.flush()
    reclaimed = client.post("/api/worker/jobs/dequeue").json()
    assert reclaimed["status"] == "dequeued"
    assert reclaimed["queue_item"]["attempts"] == 2

    failed_once = client.post(
        f"/api/worker/jobs/{queue_id}/complete",
        json={"status": "failed", "error": "temporary provider failure"},
    ).json()
    assert failed_once["queue_item"]["status"] == "queued"
    assert failed_once["job"]["status"] == "queued"

    for _ in range(3):
        client.post("/api/worker/jobs/dequeue")
        final_failure = client.post(
            f"/api/worker/jobs/{queue_id}/complete",
            json={"status": "failed", "error": "provider still unavailable"},
        ).json()

    assert final_failure["queue_item"]["status"] == "dead_letter"
    assert final_failure["job"]["status"] == "failed"
    assert final_failure["job"]["error"] == "provider still unavailable"
    configure_inference_provider("local-deterministic")


def test_worker_completion_is_idempotent_for_locked_queue_item(tmp_path):
    configure_persistent_store(str(tmp_path / "queue-idempotent.sqlite3"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Idempotent Queue UI", "target_engine": "unity", "canvas": {"width": 1280, "height": 720}},
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "idempotent worker result", "execution_mode": "queued"},
    ).json()
    queue_id = job["queue"]["id"]
    client.post("/api/worker/jobs/dequeue")

    first_complete = client.post(
        f"/api/worker/jobs/{queue_id}/complete",
        json={"status": "succeeded", "result": {"asset_id": "ast_external_worker"}},
    )
    second_complete = client.post(
        f"/api/worker/jobs/{queue_id}/complete",
        json={"status": "succeeded", "result": {"asset_id": "ast_external_worker"}},
    )

    assert first_complete.status_code == 200
    assert second_complete.status_code == 200
    assert second_complete.json()["status"] == "succeeded"
    audit_events = [
        event for event in store["audit_events"].values()
        if event["entity_id"] == job["id"] and event["action"] == "ai_job_succeeded"
    ]
    assert len(audit_events) == 1


def test_project_ai_job_list_cancel_and_retry(tmp_path):
    configure_persistent_store(str(tmp_path / "job-management.sqlite3"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Job Management Project",
            "target_engine": "unity",
            "canvas": {"width": 1280, "height": 720},
        },
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text_to_image",
            "prompt": "queued HUD generation",
            "model": "game-ui-xl",
            "execution_mode": "queued",
        },
    ).json()

    list_response = client.get(f"/api/projects/{project['id']}/ai/jobs", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["jobs"][0]["id"] == job["id"]

    get_response = client.get(f"/api/projects/{project['id']}/ai/jobs/{job['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "queued"

    cancel_response = client.post(f"/api/projects/{project['id']}/ai/jobs/{job['id']}/cancel", headers=headers)
    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()
    assert cancelled["status"] == "cancelled"
    assert cancelled["queue"]["status"] == "cancelled"

    retry_response = client.post(f"/api/projects/{project['id']}/ai/jobs/{job['id']}/retry", headers=headers)
    assert retry_response.status_code == 201
    retried = retry_response.json()
    assert retried["id"] != job["id"]
    assert retried["prompt"] == "queued HUD generation"
    assert retried["execution_mode"] == "queued"
    assert retried["retry_of"] == job["id"]
    assert retried["status"] == "queued"

    jobs = client.get(f"/api/projects/{project['id']}/ai/jobs", headers=headers).json()["jobs"]
    assert [item["id"] for item in jobs] == [retried["id"], job["id"]]


def test_qwen_async_provider_submit_poll_and_cancel(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "qwen-async.sqlite3"))
    configure_inference_provider("qwen-async")
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Qwen Async UI", "target_engine": "unity", "canvas": {"width": 1280, "height": 720}},
    ).json()

    submitted_payloads: list[dict[str, object]] = []
    cancelled_provider_jobs: list[str] = []

    def fake_qwen_async_submit(request):
        submitted_payloads.append(request)
        return {"provider_job_id": f"qwen_async_{request['job_id']}", "status": "submitted"}

    def fake_qwen_async_poll(provider_job):
        return {
            "status": "succeeded",
            "asset_url": "/qwen/async/result.png",
            "provider_job_id": provider_job["provider_job_id"],
            "layered_slices": [
                {"id": "async_panel", "type": "panel", "name": "Async Panel", "rect": {"x": 48, "y": 32, "width": 400, "height": 220}, "confidence": 0.91}
            ],
        }

    def fake_qwen_async_cancel(provider_job):
        cancelled_provider_jobs.append(provider_job["provider_job_id"])
        return {"status": "cancelled"}

    monkeypatch.setattr("app.main.qwen_async_submit", fake_qwen_async_submit)
    monkeypatch.setattr("app.main.qwen_async_poll", fake_qwen_async_poll)
    monkeypatch.setattr("app.main.qwen_async_cancel", fake_qwen_async_cancel)

    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "async qwen hud", "execution_mode": "queued"},
    ).json()

    submitted = client.post("/api/system/ai-worker/run-next").json()
    assert submitted["status"] == "provider_waiting"
    assert submitted["job"]["status"] == "processing"
    provider_job_id = submitted["job"]["inference"]["provider_job_id"]
    assert submitted_payloads[0]["prompt"] == "async qwen hud"
    assert store["provider_jobs"][provider_job_id]["status"] == "submitted"

    polled = client.post(f"/api/system/ai-worker/provider-jobs/{provider_job_id}/poll").json()
    assert polled["status"] == "succeeded"
    assert polled["job"]["status"] == "succeeded"
    assert polled["job"]["result_asset"]["metadata"]["layered_slices"][0]["id"] == "async_panel"

    cancellable = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "async qwen cancellable", "execution_mode": "queued"},
    ).json()
    submitted_cancel = client.post("/api/system/ai-worker/run-next").json()
    cancel_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs/{submitted_cancel['job']['id']}/cancel",
        headers=headers,
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert cancelled_provider_jobs == [submitted_cancel["job"]["inference"]["provider_job_id"]]
    assert cancellable["id"] != job["id"]
    configure_inference_provider("local-deterministic")


def test_qwen_async_provider_polls_configured_endpoint_and_blocks_cancelled_completion(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "qwen-async-http.sqlite3"))
    configure_object_storage(str(tmp_path / "objects-qwen-async-http"))
    configure_inference_provider("qwen-async")
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")
    monkeypatch.setenv("QWEN_ASYNC_SUBMIT_ENDPOINT", "https://qwen.example.test/tasks")
    monkeypatch.setenv("QWEN_ASYNC_POLL_ENDPOINT", "https://qwen.example.test/tasks/{provider_job_id}")
    monkeypatch.setenv("QWEN_ASYNC_CANCEL_ENDPOINT", "https://qwen.example.test/tasks/{provider_job_id}/cancel")
    monkeypatch.setattr("app.main.download_generated_image", lambda *_args: "/objects/qwen-async-http.png")

    class FakeQwenResponse:
        def __init__(self, payload: dict[str, object]):
            self.payload = payload
            self.status_code = 200
            self.text = json.dumps(payload)

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self.payload

    posted_urls: list[str] = []
    fetched_urls: list[str] = []

    def fake_post(url, *_args, **_kwargs):
        posted_urls.append(url)
        if url.endswith("/cancel"):
            return FakeQwenResponse({"status": "CANCELLED"})
        return FakeQwenResponse({"task_id": "qwen-task-001", "status": "PENDING"})

    def fake_get(url, *_args, **_kwargs):
        fetched_urls.append(url)
        return FakeQwenResponse(
            {
                "task_id": "qwen-task-001",
                "status": "SUCCEEDED",
                "output": {
                    "results": [
                        {
                            "url": "https://cdn.example.test/qwen-result.png",
                            "layered_slices": [
                                {
                                    "id": "qwen_async_button",
                                    "type": "button",
                                    "name": "Qwen Async Button",
                                    "rect": {"x": 96, "y": 120, "width": 240, "height": 88},
                                    "confidence": 0.93,
                                }
                            ],
                        }
                    ]
                },
            }
        )

    monkeypatch.setattr("app.main.httpx.post", fake_post)
    monkeypatch.setattr("app.main.httpx.get", fake_get)
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={"name": "Configured Qwen Async", "target_engine": "unity", "canvas": {"width": 1280, "height": 720}},
        ).json()

        job = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={"kind": "text_to_image", "prompt": "configured async hud", "execution_mode": "queued"},
        ).json()
        submitted = client.post("/api/system/ai-worker/run-next").json()

        provider_job_id = submitted["job"]["inference"]["provider_job_id"]
        assert provider_job_id == "qwen-task-001"
        assert posted_urls[0] == "https://qwen.example.test/tasks"

        polled = client.post(f"/api/system/ai-worker/provider-jobs/{provider_job_id}/poll").json()
        assert polled["status"] == "succeeded"
        assert polled["job"]["id"] == job["id"]
        assert polled["job"]["result_asset"]["url"] == "/objects/qwen-async-http.png"
        assert polled["job"]["result_asset"]["metadata"]["layered_slices"][0]["id"] == "qwen_async_button"
        assert fetched_urls == ["https://qwen.example.test/tasks/qwen-task-001"]

        cancelled = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={"kind": "text_to_image", "prompt": "cancel before poll", "execution_mode": "queued"},
        ).json()
        submitted_cancel = client.post("/api/system/ai-worker/run-next").json()
        cancelled_provider_job_id = submitted_cancel["job"]["inference"]["provider_job_id"]
        cancel_response = client.post(
            f"/api/projects/{project['id']}/ai/jobs/{submitted_cancel['job']['id']}/cancel",
            headers=headers,
        )

        assert cancel_response.status_code == 200
        assert posted_urls[-1] == "https://qwen.example.test/tasks/qwen-task-001/cancel"
        polled_after_cancel = client.post(f"/api/system/ai-worker/provider-jobs/{cancelled_provider_job_id}/poll")
        assert polled_after_cancel.status_code == 200
        assert polled_after_cancel.json()["status"] == "cancelled"
        assert "result_asset" not in polled_after_cancel.json()["job"]
        assert cancelled["id"] != job["id"]
    finally:
        configure_inference_provider("local-deterministic")


def test_qwen_async_poll_normalizes_remote_failure(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "qwen-async-failed.sqlite3"))
    configure_inference_provider("qwen-async")
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")
    monkeypatch.setenv("QWEN_ASYNC_SUBMIT_ENDPOINT", "https://qwen.example.test/tasks")
    monkeypatch.setenv("QWEN_ASYNC_POLL_ENDPOINT", "https://qwen.example.test/tasks/{provider_job_id}")

    class FakeQwenResponse:
        status_code = 200
        text = '{"status": "FAILED"}'

        def __init__(self, payload: dict[str, object]):
            self.payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self.payload

    monkeypatch.setattr("app.main.httpx.post", lambda *_args, **_kwargs: FakeQwenResponse({"id": "qwen-task-failed", "status": "PENDING"}))
    monkeypatch.setattr(
        "app.main.httpx.get",
        lambda *_args, **_kwargs: FakeQwenResponse({"id": "qwen-task-failed", "status": "FAILED", "code": "ContentSafety", "message": "blocked"}),
    )
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={"name": "Failed Qwen Async", "target_engine": "unity", "canvas": {"width": 512, "height": 512}},
        ).json()
        client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={"kind": "text_to_image", "prompt": "unsafe", "execution_mode": "queued"},
        )
        submitted = client.post("/api/system/ai-worker/run-next").json()
        provider_job_id = submitted["job"]["inference"]["provider_job_id"]

        polled = client.post(f"/api/system/ai-worker/provider-jobs/{provider_job_id}/poll")

        assert polled.status_code == 200
        body = polled.json()
        assert body["status"] == "failed"
        assert body["provider_job"]["error"]["code"] == "ContentSafety"
        assert body["job"]["status"] == "failed"
        assert body["job"]["error"] == "ContentSafety: blocked"
    finally:
        configure_inference_provider("local-deterministic")


def test_qwen_layered_slice_result_drives_ai_asset_segmentation(tmp_path, monkeypatch):
    db_path = tmp_path / "qwen-layered-slice.sqlite3"
    configure_persistent_store(str(db_path))
    configure_object_storage(str(tmp_path / "objects"))
    configure_inference_provider("qwen")
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")
    captured_payload: dict[str, object] = {}

    class FakeQwenResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "id": "qwen-layered-job-1",
                "data": [
                    {
                        "url": "https://qwen.example/generated-layered-ui.png",
                        "layered_slices": [
                            {
                                "id": "qwen_panel",
                                "type": "panel",
                                "name": "Generated Panel",
                                "rect": {"x": 64, "y": 48, "width": 420, "height": 240},
                                "confidence": 0.96,
                            },
                            {
                                "id": "qwen_cta_button",
                                "type": "button",
                                "name": "Generated CTA Button",
                                "rect": {"x": 220, "y": 330, "width": 180, "height": 72},
                                "confidence": 0.94,
                            },
                        ],
                    }
                ],
            }

    def fake_qwen_post(*_args, **kwargs):
        captured_payload.update(kwargs["json"])
        return FakeQwenResponse()

    def fake_download_generated_image(project_id, job_id, remote_url, size_label):
        return f"/api/objects/{project_id}/{job_id}-{size_label}.png"

    monkeypatch.setattr("app.main.httpx.post", fake_qwen_post)
    monkeypatch.setattr("app.main.download_generated_image", fake_download_generated_image)
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "Qwen Layered Slice UI",
                "target_engine": "unity",
                "canvas": {"width": 640, "height": 480},
            },
        ).json()
        reference_asset = client.post(
            f"/api/projects/{project['id']}/assets",
            headers=headers,
            json={
                "name": "reference-hud.png",
                "type": "reference_image",
                "url": "s3://gameuiagent/reference-hud.png",
                "width": 640,
                "height": 480,
                "usage": "reference_ui",
            },
        ).json()
        job = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={
                "kind": "image_to_image",
                "prompt": "Generate layered sci-fi game shop UI and return layer slices",
                "reference_asset_id": reference_asset["id"],
                "model": "qwen-layered-slice",
                "execution_mode": "queued",
            },
        ).json()

        worker_response = client.post("/api/system/ai-worker/run-next")

        assert worker_response.status_code == 200
        completed = worker_response.json()["job"]
        assert captured_payload["model"] == "qwen-layered-slice"
        assert captured_payload["reference_image"] == "s3://gameuiagent/reference-hud.png"
        assert completed["status"] == "succeeded"
        assert completed["result_asset"]["metadata"]["layered_slice_provider"] == "qwen"
        assert completed["result_asset"]["metadata"]["layered_slices"][0]["id"] == "qwen_panel"

        segmentation = client.post(
            f"/api/projects/{project['id']}/segmentations",
            headers=headers,
            json={"asset_id": completed["result_asset"]["id"]},
        ).json()

        assert [item["id"] for item in segmentation["slices"]] == ["qwen_panel", "qwen_cta_button"]
        assert segmentation["slices"][1]["rect"] == {"x": 220, "y": 330, "width": 180, "height": 72}
        assert segmentation["ir"]["nodes"][1]["name"] == "Generated Panel"
        assert segmentation["ir"]["source_asset"]["segmentation_source"] == "qwen-layered-slice"

        studio_response = client.get(f"/api/projects/{project['id']}/studio", headers=headers)
        assert studio_response.status_code == 200
        layered_summary = studio_response.json()["layered_slice_summary"]
        assert layered_summary["source"] == "qwen-layered-slice"
        assert layered_summary["slice_count"] == 2
        assert layered_summary["editable_node_count"] == 2
        assert layered_summary["nodes"][1] == {
            "id": "qwen_cta_button",
            "type": "button",
            "name": "Generated CTA Button",
            "rect": {"x": 220, "y": 330, "width": 180, "height": 72},
            "editable_bounds": True,
        }

        export_response = client.post(
            f"/api/projects/{project['id']}/exports",
            headers=headers,
            json={"ir_id": segmentation["ir"]["id"], "target_engine": "unity"},
        )

        assert export_response.status_code == 201
        manifest_ir = export_response.json()["package"]["manifest"]["asset_ir"]
        assert manifest_ir["segmentation_source"] == "qwen-layered-slice"
        assert manifest_ir["layered_slice_count"] == 2
        assert manifest_ir["nodes"][1] == {
            "id": "qwen_cta_button",
            "type": "button",
            "name": "Generated CTA Button",
            "rect": {"x": 220, "y": 330, "width": 180, "height": 72},
            "segmentation_source": "qwen-layered-slice",
        }
    finally:
        configure_inference_provider("local-deterministic")


def test_layered_slice_segmentation_creates_slice_assets_and_blocks_low_confidence_export(tmp_path):
    configure_persistent_store(str(tmp_path / "slice-quality.sqlite3"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Slice Quality UI", "target_engine": "unity", "canvas": {"width": 1280, "height": 720}},
    ).json()
    asset = {
        "id": "ast_low_confidence",
        "project_id": project["id"],
        "type": "generated_image",
        "name": "Low confidence generated UI",
        "url": "/generated/low-confidence.png",
        "source": "ai",
        "metadata": {
            "width": 1280,
            "height": 720,
            "inference_provider": "qwen",
            "layered_slices": [
                {
                    "id": "uncertain_cta",
                    "type": "button",
                    "name": "Uncertain CTA",
                    "rect": {"x": 240, "y": 420, "width": 220, "height": 88},
                    "confidence": 0.52,
                }
            ],
        },
    }
    store["assets"][asset["id"]] = asset

    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": asset["id"]},
    ).json()

    node = segmentation["ir"]["nodes"][1]
    assert node["asset_ref"]["asset_id"].startswith("ast_slice")
    assert node["requires_review"] is True
    assert store["assets"][node["asset_ref"]["asset_id"]]["type"] == "slice_image"

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": "unity"},
    )
    assert export_response.status_code == 422
    assert export_response.json()["detail"]["errors"][0]["field"] == "requires_review"

    reviewed = client.post(
        f"/api/projects/{project['id']}/irs/{segmentation['ir']['id']}/patches",
        headers=headers,
        json={
            "base_version": segmentation["ir"]["version"],
            "summary": "Approve low confidence slice",
            "operations": [
                {"op": "update_node", "node_id": "uncertain_cta", "fields": {"requires_review": False}}
            ],
        },
    ).json()
    export_after_review = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": reviewed["ir"]["id"], "target_engine": "unity"},
    )
    assert export_after_review.status_code == 201


def test_qwen_layered_slice_parser_ignores_malformed_provider_shapes():
    assert extract_qwen_layered_slices({"data": {"layered_slices": "bad-shape"}}) == []
    assert extract_qwen_layered_slices({"output": {"results": {"layered_slices": []}}}) == []


def test_qwen_http_error_propagates_status_detail(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "qwen-http-error.sqlite3"))
    configure_object_storage(str(tmp_path / "objects-http-error"))
    configure_inference_provider("qwen")
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")

    class FakeErrorResponse:
        status_code = 400
        text = '{"code": "InvalidParameter", "message": "model not found"}'

        def json(self):
            return {"code": "InvalidParameter", "message": "model not found"}

        def raise_for_status(self):
            import httpx
            raise httpx.HTTPStatusError(
                "Bad Request",
                request=None,
                response=self,
            )

    def fake_qwen_post(*_args, **kwargs):
        return FakeErrorResponse()

    monkeypatch.setattr("app.main.httpx.post", fake_qwen_post)
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "Qwen HTTP Error",
                "target_engine": "unity",
                "canvas": {"width": 512, "height": 512},
            },
        ).json()

        worker_response = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={
                "kind": "text_to_image",
                "prompt": "test",
                "execution_mode": "queued",
            },
        )
        assert worker_response.status_code == 201

        run_response = client.post("/api/system/ai-worker/run-next")
        assert run_response.status_code == 200
        job = run_response.json()["job"]
        assert job["status"] == "failed"
        assert "400" in job["error"] or "InvalidParameter" in job["error"]
    finally:
        configure_inference_provider("local-deterministic")


def test_stream_download_image_rejects_oversize(tmp_path, monkeypatch):
    from app.main import stream_download_image

    fake_png = rgba_png_with_opaque_rects(100, 100, [{"x": 0, "y": 0, "width": 100, "height": 100}])
    small_limit = len(fake_png) - 1

    class FakeStreamResponse:
        def __init__(self):
            self.headers = {"content-type": "image/png", "content-length": str(len(fake_png))}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def raise_for_status(self):
            pass

        def iter_bytes(self):
            yield fake_png

    def fake_stream(*_args, **kwargs):
        return FakeStreamResponse()

    monkeypatch.setattr("app.main.httpx.stream", fake_stream)
    try:
        stream_download_image("https://example.com/big.png", small_limit)
        assert False, "expected ValueError for oversized image"
    except ValueError as exc:
        assert "exceeds" in str(exc)


def test_inline_qwen_text_to_image_preserves_layered_slices(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "inline-qwen-layered.sqlite3"))
    configure_object_storage(str(tmp_path / "objects-inline"))
    configure_inference_provider("qwen")
    monkeypatch.setenv("QWEN_API_KEY", "test-qwen-key")
    captured_payload: dict[str, object] = {}

    class FakeQwenResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "id": "qwen-inline-layered-job",
                "data": [
                    {
                        "url": "https://qwen.example/inline-layered-ui.png",
                        "layered_slices": [
                            {
                                "id": "inline_inventory_panel",
                                "type": "panel",
                                "name": "Inline Inventory Panel",
                                "rect": {"x": 40, "y": 36, "width": 360, "height": 260},
                                "confidence": 0.95,
                            }
                        ],
                    }
                ],
            }

    def fake_qwen_post(*_args, **kwargs):
        captured_payload.update(kwargs["json"])
        return FakeQwenResponse()

    def fake_download_generated_image(project_id, job_id, remote_url, size_label):
        return f"/api/objects/{project_id}/{job_id}-{size_label}.png"

    monkeypatch.setattr("app.main.httpx.post", fake_qwen_post)
    monkeypatch.setattr("app.main.download_generated_image", fake_download_generated_image)
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "Inline Qwen Slice UI",
                "target_engine": "unity",
                "canvas": {"width": 512, "height": 384},
            },
        ).json()

        job_response = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={
                "kind": "text_to_image",
                "prompt": "Generate inventory UI with layered slices",
                "model": "qwen-layered-slice",
                "execution_mode": "inline",
            },
        )

        assert job_response.status_code == 201
        job = job_response.json()
        assert captured_payload["model"] == "qwen-layered-slice"
        assert job["status"] == "succeeded"
        assert job["inference"]["provider"] == "qwen"
        assert "/api/objects/" in job["result_asset"]["url"]
        assert job["result_asset"]["metadata"]["layered_slices"][0]["id"] == "inline_inventory_panel"
    finally:
        configure_inference_provider("local-deterministic")


def test_ai_worker_marks_job_failed_when_inference_provider_fails(tmp_path):
    db_path = tmp_path / "inference-failure.sqlite3"
    configure_persistent_store(str(db_path))
    configure_inference_provider("failing")
    try:
        headers = auth_headers()
        project = client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "Inference Failure Project",
                "target_engine": "unity",
                "canvas": {"width": 1280, "height": 720},
            },
        ).json()
        job = client.post(
            f"/api/projects/{project['id']}/ai/jobs",
            headers=headers,
            json={
                "kind": "text_to_image",
                "prompt": "provider failure should not fake success",
                "execution_mode": "queued",
            },
        ).json()

        worker_response = client.post("/api/system/ai-worker/run-next")

        assert worker_response.status_code == 200
        failed = worker_response.json()["job"]
        assert failed["id"] == job["id"]
        assert failed["status"] == "failed"
        assert failed["progress"] == 0
        assert failed["error"] == "Inference provider failed"
        assert worker_response.json()["queue"]["status"] == "failed"
        assert "result_asset" not in failed

        reloaded_store = create_production_store()
        reloaded_store.configure(str(db_path))
        assert reloaded_store["jobs"][job["id"]]["status"] == "failed"
        assert reloaded_store["ai_job_queue"][job["queue"]["id"]]["status"] == "failed"
    finally:
        configure_inference_provider("local-deterministic")


def test_professional_import_source_submission_creates_parser_job():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Source Import UI",
            "target_engine": "unity",
            "canvas": {"width": 1440, "height": 900},
        },
    ).json()
    psd_asset = client.post(
        f"/api/projects/{project['id']}/assets",
        headers=headers,
        json={
            "name": "shop.psd",
            "type": "psd",
            "url": "s3://gameuiagent/imports/shop.psd",
            "width": 1440,
            "height": 900,
            "usage": "professional_import",
        },
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": psd_asset["id"],
            "frame_id": None,
            "parser": "mock-layer-parser",
        },
    )

    assert source_response.status_code == 201
    source = source_response.json()
    assert source["status"] == "parsed"
    assert source["source"]["asset_id"] == psd_asset["id"]
    assert source["design_document"]["source_type"] == "psd"
    assert source["ir"]["professional_source"]["file_name"] == "shop.psd"
    assert source["parse_summary"]["preserved_layers"] >= 3

    figma_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "figma",
            "figma_url": "https://figma.com/file/gameuiagent-shop",
            "frame_id": "12:34",
            "parser": "figma-api",
        },
    )

    assert figma_response.status_code == 201
    assert figma_response.json()["source"]["figma_url"].endswith("gameuiagent-shop")
    assert figma_response.json()["ir"]["professional_source"]["frame_id"] == "12:34"


def test_professional_import_source_uses_configured_figma_api(monkeypatch):
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Figma API UI",
            "target_engine": "unity",
            "canvas": {"width": 1440, "height": 900},
        },
    ).json()
    captured_request: dict[str, object] = {}

    class FakeFigmaResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "nodes": {
                    "12:34": {
                        "document": {
                            "id": "12:34",
                            "name": "Shop HUD Frame",
                            "type": "FRAME",
                            "absoluteBoundingBox": {"x": 0, "y": 0, "width": 1440, "height": 900},
                            "layoutMode": "VERTICAL",
                            "itemSpacing": 16,
                            "children": [
                                {
                                    "id": "12:35",
                                    "name": "Reward Card",
                                    "type": "COMPONENT",
                                    "key": "reward-card-key",
                                    "absoluteBoundingBox": {"x": 96, "y": 120, "width": 360, "height": 520},
                                    "layoutMode": "HORIZONTAL",
                                    "itemSpacing": 8,
                                    "constraints": {"horizontal": "MIN", "vertical": "MIN"},
                                },
                                {
                                    "id": "12:36",
                                    "name": "Buy Label",
                                    "type": "TEXT",
                                    "characters": "BUY",
                                    "absoluteBoundingBox": {"x": 220, "y": 680, "width": 120, "height": 42},
                                    "style": {"fontFamily": "Inter", "fontSize": 32},
                                },
                            ],
                        }
                    }
                }
            }

    def fake_figma_get(url: str, **kwargs):
        captured_request["url"] = url
        captured_request["headers"] = kwargs["headers"]
        return FakeFigmaResponse()

    monkeypatch.setenv("FIGMA_API_TOKEN", "figma-test-token")
    monkeypatch.setattr("app.main.httpx.get", fake_figma_get)

    response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "figma",
            "figma_url": "https://www.figma.com/file/gameuiagent-shop/Shop-HUD",
            "frame_id": "12:34",
            "parser": "figma-api",
        },
    )

    assert response.status_code == 201
    imported = response.json()
    assert captured_request["url"] == "https://api.figma.com/v1/files/gameuiagent-shop/nodes?ids=12%3A34"
    assert captured_request["headers"] == {"X-Figma-Token": "figma-test-token"}
    assert imported["parse_summary"]["layer_source"] == "figma-api"
    assert imported["parse_summary"]["preserved_layers"] == 3
    assert imported["parse_summary"]["warnings"] == []
    frame = imported["design_document"]["layers"][0]
    assert frame["id"] == "12:34"
    assert frame["kind"] == "frame"
    assert frame["auto_layout"] == {"direction": "vertical", "gap": 16}
    card_node = imported["ir"]["nodes"][2]
    assert card_node["component"]["key"] == "reward-card-key"
    assert card_node["layout"]["constraints"] == {"horizontal": "MIN", "vertical": "MIN"}
    text_node = imported["ir"]["nodes"][3]
    assert text_node["text"]["content"] == "BUY"
    assert text_node["text"]["style"] == {"font": "Inter", "font_size": 32}


def test_figma_import_downloads_image_fills_to_object_storage(tmp_path, monkeypatch):
    object_store_path = tmp_path / "figma-image-objects"
    configure_persistent_store(str(tmp_path / "figma-images.sqlite3"))
    configure_object_storage(str(object_store_path))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Figma Image UI",
            "target_engine": "unity",
            "canvas": {"width": 1024, "height": 768},
        },
    ).json()
    calls: list[str] = []

    class FakeResponse:
        def __init__(self, json_payload: dict[str, object] | None = None, content: bytes = b"") -> None:
            self._json_payload = json_payload
            self.content = content
            self.headers = {"content-type": "image/png"} if content else {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._json_payload or {}

    def fake_figma_get(url: str, **_kwargs):
        calls.append(url)
        if url == "https://api.figma.com/v1/files/gameuiagent-shop/nodes?ids=12%3A34":
            return FakeResponse(
                {
                    "nodes": {
                        "12:34": {
                            "document": {
                                "id": "12:34",
                                "name": "Shop HUD Frame",
                                "type": "FRAME",
                                "absoluteBoundingBox": {"x": 0, "y": 0, "width": 1024, "height": 768},
                                "children": [
                                    {
                                        "id": "12:40",
                                        "name": "Hero Splash Art",
                                        "type": "RECTANGLE",
                                        "absoluteBoundingBox": {"x": 80, "y": 72, "width": 640, "height": 360},
                                        "fills": [{"type": "IMAGE", "imageRef": "hero-ref"}],
                                    }
                                ],
                            }
                        }
                    }
                }
            )
        if url == "https://api.figma.com/v1/images/gameuiagent-shop?ids=12%3A40&format=png":
            return FakeResponse({"images": {"12:40": "https://figma.example/hero-splash.png"}})
        raise AssertionError(f"Unexpected Figma request: {url}")

    class FakeStreamResponse:
        headers = {"content-type": "image/png", "content-length": "25"}

        def __enter__(self) -> "FakeStreamResponse":
            return self

        def __exit__(self, *_args) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self):
            yield b"\x89PNG\r\n\x1a\nfigma-image-bytes"

    def fake_figma_stream(method: str, url: str, **_kwargs):
        assert method == "GET"
        assert url == "https://figma.example/hero-splash.png"
        calls.append(url)
        return FakeStreamResponse()

    monkeypatch.setenv("FIGMA_API_TOKEN", "figma-test-token")
    monkeypatch.setattr("app.main.httpx.get", fake_figma_get)
    monkeypatch.setattr("app.main.httpx.stream", fake_figma_stream)

    response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "figma",
            "figma_url": "https://www.figma.com/file/gameuiagent-shop/Shop-HUD",
            "frame_id": "12:34",
            "parser": "figma-api",
        },
    )

    assert response.status_code == 201
    imported = response.json()
    assert calls == [
        "https://api.figma.com/v1/files/gameuiagent-shop/nodes?ids=12%3A34",
        "https://api.figma.com/v1/images/gameuiagent-shop?ids=12%3A40&format=png",
        "https://figma.example/hero-splash.png",
    ]
    image_layer = imported["design_document"]["layers"][1]
    assert image_layer["image_asset_id"].startswith("ast_")
    assert image_layer["image_url"].endswith(f"/assets/{image_layer['image_asset_id']}/download")
    assert imported["ir"]["nodes"][2]["professional_source"]["image_asset_id"] == image_layer["image_asset_id"]
    asset = store["assets"][image_layer["image_asset_id"]]
    assert asset["source"] == "figma_image"
    assert asset["metadata"]["figma_node_id"] == "12:40"
    assert "figma_image_url" not in asset["metadata"]
    assert (object_store_path / asset["metadata"]["storage_key"]).read_bytes() == b"\x89PNG\r\n\x1a\nfigma-image-bytes"


def test_figma_import_skips_oversized_image_fills(tmp_path, monkeypatch):
    configure_persistent_store(str(tmp_path / "figma-oversized.sqlite3"))
    configure_object_storage(str(tmp_path / "figma-oversized-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Figma Oversized Image UI",
            "target_engine": "unity",
            "canvas": {"width": 1024, "height": 768},
        },
    ).json()

    class FakeResponse:
        def __init__(self, json_payload: dict[str, object]) -> None:
            self._json_payload = json_payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._json_payload

    def fake_figma_get(url: str, **_kwargs):
        if url == "https://api.figma.com/v1/files/gameuiagent-shop/nodes?ids=12%3A34":
            return FakeResponse(
                {
                    "nodes": {
                        "12:34": {
                            "document": {
                                "id": "12:34",
                                "name": "Shop HUD Frame",
                                "type": "FRAME",
                                "absoluteBoundingBox": {"x": 0, "y": 0, "width": 1024, "height": 768},
                                "children": [
                                    {
                                        "id": "12:40",
                                        "name": "Oversized Hero Art",
                                        "type": "RECTANGLE",
                                        "absoluteBoundingBox": {"x": 80, "y": 72, "width": 640, "height": 360},
                                        "fills": [{"type": "IMAGE", "imageRef": "hero-ref"}],
                                    }
                                ],
                            }
                        }
                    }
                }
            )
        if url == "https://api.figma.com/v1/images/gameuiagent-shop?ids=12%3A40&format=png":
            return FakeResponse({"images": {"12:40": "https://figma.example/oversized-hero.png"}})
        raise AssertionError(f"Unexpected Figma request: {url}")

    class FakeOversizedStreamResponse:
        headers = {"content-type": "image/png", "content-length": str(MAX_FIGMA_IMAGE_FILL_BYTES + 1)}

        def __enter__(self) -> "FakeOversizedStreamResponse":
            return self

        def __exit__(self, *_args) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self):
            raise AssertionError("oversized response should be rejected before reading body")

    def fake_figma_stream(method: str, url: str, **_kwargs):
        assert method == "GET"
        assert url == "https://figma.example/oversized-hero.png"
        return FakeOversizedStreamResponse()

    monkeypatch.setenv("FIGMA_API_TOKEN", "figma-test-token")
    monkeypatch.setattr("app.main.httpx.get", fake_figma_get)
    monkeypatch.setattr("app.main.httpx.stream", fake_figma_stream)

    response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "figma",
            "figma_url": "https://www.figma.com/file/gameuiagent-shop/Shop-HUD",
            "frame_id": "12:34",
            "parser": "figma-api",
        },
    )

    assert response.status_code == 201
    imported = response.json()
    image_layer = imported["design_document"]["layers"][1]
    assert "image_asset_id" not in image_layer
    assert imported["parse_summary"]["warnings"] == [
        "Figma image download skipped for node 12:40: image exceeds 25MB limit."
    ]


def test_professional_import_source_parses_uploaded_psd_binary_header(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-parser.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Real PSD Parser UI",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    psd_bytes = minimal_psd_header(2048, 1024)
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "real-hud.psd",
            "type": "psd",
            "width": "2048",
            "height": "1024",
            "usage": "professional_import",
            "tags": "psd,production",
        },
        files={"file": ("real-hud.psd", psd_bytes, "image/vnd.adobe.photoshop")},
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    imported = source_response.json()
    assert imported["source"]["parser"] == "psd-binary-header"
    assert imported["parse_summary"]["parser"] == "psd-binary-header"
    assert imported["parse_summary"]["binary_header"] == {
        "signature": "8BPS",
        "version": 1,
        "width": 2048,
        "height": 1024,
        "channels": 4,
        "depth": 8,
        "color_mode": "rgb",
    }
    assert imported["design_document"]["layers"][0]["name"] == "PSD Composite Canvas"
    assert imported["design_document"]["layers"][0]["rect"] == {"x": 0, "y": 0, "width": 2048, "height": 1024}
    assert imported["ir"]["nodes"][1]["professional_source"]["parser"] == "psd-binary-header"


def test_professional_import_source_preserves_psd_layer_records(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-layers.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-layer-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Real PSD Layers UI",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 256},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "layered-hud.psd",
            "type": "psd",
            "width": "512",
            "height": "256",
            "usage": "professional_import",
        },
        files={"file": ("layered-hud.psd", minimal_psd_with_layers(512, 256), "image/vnd.adobe.photoshop")},
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    imported = source_response.json()
    assert imported["parse_summary"]["preserved_layers"] == 2
    assert imported["parse_summary"]["layer_source"] == "psd-layer-records"
    assert [layer["name"] for layer in imported["design_document"]["layers"]] == ["Main Panel", "Hidden CTA Button"]
    assert imported["design_document"]["layers"][0]["rect"] == {"x": 24, "y": 32, "width": 240, "height": 120}
    assert imported["design_document"]["layers"][0]["opacity"] == 1
    assert imported["design_document"]["layers"][0]["visible"] is True
    assert imported["design_document"]["layers"][1]["opacity"] == 0.502
    assert imported["design_document"]["layers"][1]["visible"] is False
    assert imported["ir"]["nodes"][2]["opacity"] == 0.502
    assert imported["ir"]["nodes"][2]["visible"] is False


def test_professional_import_source_preserves_psd_unicode_groups_and_smart_objects(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-advanced.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-advanced-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Advanced PSD UI",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 256},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "advanced-layered-hud.psd",
            "type": "psd",
            "width": "512",
            "height": "256",
            "usage": "professional_import",
        },
        files={"file": ("advanced-layered-hud.psd", minimal_psd_with_advanced_layers(512, 256), "image/vnd.adobe.photoshop")},
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    imported = source_response.json()
    layers = imported["design_document"]["layers"]
    assert [layer["name"] for layer in layers] == ["商店弹窗组", "购买按钮智能对象"]
    assert layers[0]["kind"] == "group"
    assert layers[0]["is_group"] is True
    assert layers[1]["kind"] == "component"
    assert layers[1]["smart_object"] is True
    assert imported["ir"]["nodes"][1]["type"] == "group"
    assert imported["ir"]["nodes"][1]["professional_source"]["is_group"] is True
    assert imported["ir"]["nodes"][2]["type"] == "component"
    assert imported["ir"]["nodes"][2]["professional_source"]["smart_object"] is True


def test_professional_import_source_reconstructs_psd_group_hierarchy(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-hierarchy.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-hierarchy-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Hierarchical PSD UI",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 256},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "hierarchical-hud.psd",
            "type": "psd",
            "width": "512",
            "height": "256",
            "usage": "professional_import",
        },
        files={"file": ("hierarchical-hud.psd", minimal_psd_with_advanced_layers(512, 256), "image/vnd.adobe.photoshop")},
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    imported = source_response.json()
    group_layer, child_layer = imported["design_document"]["layers"]
    assert child_layer["parent_id"] == group_layer["id"]
    assert child_layer["group_path"] == ["商店弹窗组"]
    assert imported["ir"]["nodes"][2]["parent_id"] == group_layer["id"]
    assert imported["ir"]["nodes"][2]["professional_source"]["group_path"] == ["商店弹窗组"]


def test_professional_import_source_does_not_parent_layers_after_psd_group_end(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-closed-group.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-closed-group-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Closed PSD Group UI",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 256},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "closed-group-hud.psd",
            "type": "psd",
            "width": "512",
            "height": "256",
            "usage": "professional_import",
        },
        files={"file": ("closed-group-hud.psd", minimal_psd_with_closed_group(512, 256), "image/vnd.adobe.photoshop")},
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    imported = source_response.json()
    group_layer, child_layer, badge_layer = imported["design_document"]["layers"]
    assert [layer["name"] for layer in imported["design_document"]["layers"]] == ["商店弹窗组", "购买按钮智能对象", "外部角标"]
    assert child_layer["parent_id"] == group_layer["id"]
    assert "parent_id" not in badge_layer
    assert "group_path" not in imported["ir"]["nodes"][3]["professional_source"]


def test_professional_import_source_preserves_psd_text_layer_content(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-text.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-text-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Text PSD UI",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 256},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "text-layer-hud.psd",
            "type": "psd",
            "width": "512",
            "height": "256",
            "usage": "professional_import",
        },
        files={"file": ("text-layer-hud.psd", minimal_psd_with_text_layer(512, 256), "image/vnd.adobe.photoshop")},
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    imported = source_response.json()
    layer = imported["design_document"]["layers"][0]
    assert layer["name"] == "主标题文本"
    assert layer["kind"] == "text"
    assert layer["text"] == "START"
    assert layer["text_style"] == {"font": "Game UI Sans", "font_size": 32, "fill_color": "#ffcc33"}
    assert imported["ir"]["nodes"][1]["type"] == "text"
    assert imported["ir"]["nodes"][1]["text"]["content"] == "START"
    assert imported["ir"]["nodes"][1]["text"]["style"] == {
        "font": "Game UI Sans",
        "font_size": 32,
        "fill_color": "#ffcc33",
    }


def test_professional_import_source_does_not_confuse_psd_font_size_with_font(tmp_path):
    configure_persistent_store(str(tmp_path / "psd-text-no-font.sqlite3"))
    configure_object_storage(str(tmp_path / "psd-text-no-font-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Text PSD Style UI",
            "target_engine": "unity",
            "canvas": {"width": 512, "height": 256},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "text-layer-style-hud.psd",
            "type": "psd",
            "width": "512",
            "height": "256",
            "usage": "professional_import",
        },
        files={
            "file": (
                "text-layer-style-hud.psd",
                minimal_psd_with_text_style_without_font(512, 256),
                "image/vnd.adobe.photoshop",
            )
        },
    ).json()

    source_response = client.post(
        f"/api/projects/{project['id']}/imports/professional-sources",
        headers=headers,
        json={
            "source_type": "psd",
            "asset_id": uploaded["id"],
            "parser": "psd-binary-header",
        },
    )

    assert source_response.status_code == 201
    style = source_response.json()["design_document"]["layers"][0]["text_style"]
    assert style == {"font_size": 32, "fill_color": "#ffcc33"}
    assert "font" not in style


def test_uploaded_png_segmentation_uses_detected_binary_dimensions(tmp_path):
    configure_persistent_store(str(tmp_path / "png-dimensions.sqlite3"))
    configure_object_storage(str(tmp_path / "png-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Detected Slice UI",
            "target_engine": "unity",
            "canvas": {"width": 999, "height": 999},
        },
    ).json()
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "detected-hud.png",
            "type": "reference_image",
            "width": "999",
            "height": "999",
            "usage": "source_ui",
        },
        files={"file": ("detected-hud.png", minimal_png_header(320, 180), "image/png")},
    ).json()

    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": uploaded["id"]},
    ).json()

    assert uploaded["metadata"]["width"] == 320
    assert uploaded["metadata"]["height"] == 180
    assert uploaded["metadata"]["detected_dimensions"] == {"width": 320, "height": 180, "format": "png"}
    assert segmentation["slices"][0]["rect"] == {"x": 38, "y": 21, "width": 243, "height": 125}
    assert segmentation["ir"]["source_asset"]["detected_dimensions"]["format"] == "png"


def test_uploaded_png_segmentation_uses_alpha_connected_components(tmp_path):
    configure_persistent_store(str(tmp_path / "png-alpha-components.sqlite3"))
    configure_object_storage(str(tmp_path / "png-alpha-objects"))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Pixel Slice UI",
            "target_engine": "unity",
            "canvas": {"width": 32, "height": 20},
        },
    ).json()
    png_bytes = rgba_png_with_opaque_rects(
        32,
        20,
        [
            {"x": 2, "y": 3, "width": 5, "height": 4},
            {"x": 20, "y": 11, "width": 7, "height": 6},
        ],
    )
    uploaded = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "alpha-components.png",
            "type": "reference_image",
            "width": "32",
            "height": "20",
            "usage": "source_ui",
        },
        files={"file": ("alpha-components.png", png_bytes, "image/png")},
    ).json()

    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": uploaded["id"]},
    ).json()

    assert [item["rect"] for item in segmentation["slices"]] == [
        {"x": 2, "y": 3, "width": 5, "height": 4},
        {"x": 20, "y": 11, "width": 7, "height": 6},
    ]
    assert [item["type"] for item in segmentation["slices"]] == ["image", "image"]
    assert segmentation["ir"]["nodes"][1]["rect"] == {"x": 2, "y": 3, "width": 5, "height": 4}
    assert segmentation["ir"]["source_asset"]["segmentation_source"] == "png-alpha-components"


def test_png_alpha_decoder_rejects_oversized_pixel_maps():
    width = 2048
    height = 2049
    oversized_raw = b"".join(b"\x00" + (b"\x00\x00\x00\x00" * width) for _ in range(height))
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(
            b"IHDR",
            width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x06\x00\x00\x00",
        )
        + png_chunk(b"IDAT", compress(oversized_raw))
        + png_chunk(b"IEND", b"")
    )

    assert decode_png_rgba(png_bytes) is None


def test_uploaded_asset_and_ai_job_reject_invalid_production_bounds():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Invalid Upload Bounds",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    invalid_asset_response = client.post(
        f"/api/projects/{project['id']}/assets",
        headers=headers,
        json={
            "name": "broken-reference.png",
            "type": "reference_image",
            "url": "https://assets.gameuiagent.dev/broken-reference.png",
            "width": -1920,
            "height": 0,
            "usage": "image_to_image",
        },
    )

    assert invalid_asset_response.status_code == 422

    invalid_job_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "image_to_image",
            "prompt": "restyle this HUD",
            "count": 0,
        },
    )

    excessive_job_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text_to_image",
            "prompt": "too many paid provider candidates",
            "count": 5,
        },
    )

    assert invalid_job_response.status_code == 422
    assert excessive_job_response.status_code == 422


def test_project_asset_library_supports_search_update_copy_delete_and_versions():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Asset Library Ops",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    asset = client.post(
        f"/api/projects/{project['id']}/assets",
        headers=headers,
        json={
            "name": "shop-panel.png",
            "type": "original_upload",
            "url": "https://assets.gameuiagent.dev/shop-panel.png",
            "width": 1024,
            "height": 512,
            "usage": "source_ui",
            "tags": ["shop", "panel"],
        },
    ).json()

    filtered = client.get(
        f"/api/projects/{project['id']}/assets?search=shop&tag=panel",
        headers=headers,
    )

    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["assets"]] == [asset["id"]]

    update_response = client.patch(
        f"/api/projects/{project['id']}/assets/{asset['id']}",
        headers=headers,
        json={"name": "shop-panel-v2.png", "tags": ["shop", "panel", "approved"]},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "shop-panel-v2.png"
    assert updated["metadata"]["tags"] == ["shop", "panel", "approved"]

    versions_response = client.get(
        f"/api/projects/{project['id']}/assets/{asset['id']}/versions",
        headers=headers,
    )

    assert versions_response.status_code == 200
    versions = versions_response.json()["versions"]
    assert [version["event"] for version in versions] == ["created", "updated"]
    assert versions[-1]["name"] == "shop-panel-v2.png"

    copy_response = client.post(
        f"/api/projects/{project['id']}/assets/{asset['id']}/copy",
        headers=headers,
    )

    assert copy_response.status_code == 201
    copied = copy_response.json()
    assert copied["id"] != asset["id"]
    assert copied["name"] == "shop-panel-v2.png Copy"
    assert copied["metadata"]["tags"] == ["shop", "panel", "approved"]

    delete_response = client.delete(
        f"/api/projects/{project['id']}/assets/{asset['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 200
    remaining = client.get(f"/api/projects/{project['id']}/assets", headers=headers).json()["assets"]
    assert [item["id"] for item in remaining] == [copied["id"]]


def test_project_ai_segmentation_and_unity_export_flow():
    headers = auth_headers()

    project_response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Cyberpunk RPG UI",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["target_engine"] == "unity"

    job_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text_to_image",
            "prompt": "cyberpunk neon RPG inventory UI",
            "style": "dark sci-fi",
            "size": "landscape_16_9",
        },
    )
    assert job_response.status_code == 201
    job = job_response.json()
    assert job["status"] == "succeeded"
    assert job["result_asset"]["type"] == "generated_image"

    segmentation_response = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": job["result_asset"]["id"]},
    )
    assert segmentation_response.status_code == 201
    segmentation = segmentation_response.json()
    assert segmentation["ir"]["engine_targets"] == ["unity", "cocos", "godot", "unreal"]
    assert [node["type"] for node in segmentation["ir"]["nodes"]] == [
        "canvas",
        "panel",
        "button",
        "icon",
        "text",
    ]

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": "unity"},
    )
    assert export_response.status_code == 201
    export = export_response.json()
    assert export["target_engine"] == "unity"
    assert export["package"]["kind"] == "unity_package"
    assert "Assets/GameUIAgent/Prefabs/CyberpunkRpgUi.prefab" in export["package"]["files"]

    plugin_response = client.get("/api/plugin/export-jobs", headers=headers)
    assert plugin_response.status_code == 200
    assert plugin_response.json()["jobs"][0]["id"] == export["id"]


def test_plugin_token_lifecycle_authenticates_and_revokes_engine_device():
    headers = auth_headers()

    token_response = client.post(
        "/api/plugin/tokens",
        headers=headers,
        json={"name": "Unity editor", "engine": "unity", "scopes": ["projects:read", "exports:read", "imports:write"]},
    )

    assert token_response.status_code == 201
    plugin_token = token_response.json()
    assert plugin_token["token"].startswith("gup_")
    assert plugin_token["engine"] == "unity"
    assert plugin_token["status"] == "active"

    auth_response = client.post(
        "/api/plugin/auth",
        json={
            "token": plugin_token["token"],
            "engine": "unity",
            "engine_version": "2022.3",
            "plugin_version": "1.0.0",
            "device_name": "CI Unity",
        },
    )

    assert auth_response.status_code == 200
    auth_payload = auth_response.json()
    assert auth_payload["access_token"].startswith("ptok")
    assert auth_payload["device"]["plugin_token_id"] == plugin_token["id"]
    assert auth_payload["device"]["scopes"] == ["projects:read", "exports:read", "imports:write"]

    revoke_response = client.delete(f"/api/plugin/tokens/{plugin_token['id']}", headers=headers)
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    revoked_auth = client.post(
        "/api/plugin/auth",
        json={
            "token": plugin_token["token"],
            "engine": "unity",
            "engine_version": "2022.3",
            "plugin_version": "1.0.0",
            "device_name": "CI Unity",
        },
    )
    assert revoked_auth.status_code == 401


def test_engine_snapshot_builds_asset_ir_and_mcp_tool_invokes_it():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Unity Snapshot UI", "target_engine": "unity", "canvas": {"width": 1920, "height": 1080}},
    ).json()
    snapshot = client.post(
        f"/api/projects/{project['id']}/engine-snapshots",
        headers=headers,
        json={
            "engine": "unity",
            "source": "unity-editor",
            "layout": {
                "canvas": {"width": 1920, "height": 1080},
                "nodes": [
                    {"id": "Canvas", "name": "HUD Canvas", "type": "canvas", "path": "Canvas", "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080}},
                    {"id": "StartButton", "name": "Start Button", "type": "button", "path": "Canvas/StartButton", "parent_id": "Canvas", "rect": {"x": 840, "y": 760, "width": 360, "height": 112}, "bindings": ["StartButton"]},
                ],
            },
            "sprites": [{"path": "Assets/UI/start.png", "role": "button", "node_path": "Canvas/StartButton"}],
        },
    ).json()

    build_response = client.post(
        f"/api/plugin/engine-snapshots/{snapshot['id']}/build-ir",
        headers=headers,
    )

    assert build_response.status_code == 201
    built = build_response.json()
    assert built["ir"]["professional_source"]["source_type"] == "unity-engine-snapshot"
    assert [node["id"] for node in built["ir"]["nodes"]] == ["Canvas", "StartButton"]
    assert built["ir"]["nodes"][1]["component"]["engine_path"] == "Canvas/StartButton"

    tools_response = client.get("/api/plugin/mcp/tools", headers=headers)
    assert tools_response.status_code == 200
    assert "engine.snapshot.build_ir" in [tool["name"] for tool in tools_response.json()["tools"]]

    invoke_response = client.post(
        "/api/plugin/mcp/tools/engine.snapshot.build_ir/invoke",
        headers=headers,
        json={"arguments": {"snapshot_id": snapshot["id"]}},
    )

    assert invoke_response.status_code == 201
    invocation = invoke_response.json()
    assert invocation["tool"] == "engine.snapshot.build_ir"
    assert invocation["status"] == "succeeded"
    assert invocation["result"]["ir"]["id"].startswith("ir")


def test_engine_snapshot_restyle_returns_production_replacement_manifest():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Restyle Snapshot UI", "target_engine": "unity", "canvas": {"width": 1280, "height": 720}},
    ).json()
    snapshot = client.post(
        f"/api/projects/{project['id']}/engine-snapshots",
        headers=headers,
        json={
            "engine": "unity",
            "source": "unity-editor",
            "layout": {
                "nodes": [
                    {"id": "ShopPanel", "path": "Canvas/ShopPanel", "rect": {"x": 120, "y": 80, "width": 800, "height": 480}, "bindings": ["shop_bg"]},
                ],
            },
            "sprites": [{"path": "Assets/UI/shop_bg.png", "role": "panel"}],
        },
    ).json()

    restyle_response = client.post(
        f"/api/plugin/engine-snapshots/{snapshot['id']}/restyle",
        headers=headers,
        json={
            "style_prompt": "dark fantasy obsidian shop UI",
            "preserve_layout": True,
            "replacement_strategy": "theme_variant",
            "theme_name": "obsidian",
        },
    )

    assert restyle_response.status_code == 201
    manifest = restyle_response.json()["replacement_manifest"]
    assert manifest["schema_version"] == "gameuiagent.restyle.v1"
    assert manifest["engine"] == "unity"
    assert manifest["apply_url"].startswith("/api/plugin/restyles/")
    assert manifest["replacements"][0]["checksum"].startswith("sha256:")
    assert manifest["operations"][0]["op"] == "replace_sprite_preserve_rect"


def test_export_rejects_unsupported_target_engine():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Unsupported Engine UI",
            "target_engine": "unity",
            "canvas": {"width": 1280, "height": 720},
        },
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "unsupported engine export"},
    ).json()
    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": job["result_asset"]["id"]},
    ).json()

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": "flash"},
    )

    assert export_response.status_code == 400
    assert export_response.json()["detail"] == "Unsupported target engine"


def test_project_audit_events_trace_ai_export_and_plugin_import(tmp_path):
    db_path = tmp_path / "audit-events.sqlite3"
    configure_persistent_store(str(db_path))
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Audited UI",
            "target_engine": "unity",
            "canvas": {"width": 1280, "height": 720},
        },
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "audited production ui"},
    ).json()
    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": job["result_asset"]["id"]},
    ).json()
    export = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": "unity"},
    ).json()
    client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export["id"],
            "engine": "unity",
            "status": "succeeded",
            "plugin_version": "0.3.0",
            "engine_version": "2022.3",
            "duration_ms": 321,
            "summary": {"prefabs": 1, "sprites": 3},
            "logs": [{"level": "info", "message": "Imported audited UI"}],
        },
    )

    audit_response = client.get(f"/api/projects/{project['id']}/audit-events", headers=headers)

    assert audit_response.status_code == 200
    audit_events = audit_response.json()["events"]
    assert [event["action"] for event in audit_events] == [
        "ai_job_created",
        "ai_job_succeeded",
        "ui_segmentation_created",
        "engine_export_created",
        "plugin_import_logged",
    ]
    assert audit_events[0]["actor_id"].startswith("usr_")
    assert audit_events[1]["entity_id"] == job["id"]
    assert audit_events[3]["metadata"]["target_engine"] == "unity"
    assert audit_events[4]["metadata"]["plugin_version"] == "0.3.0"
    assert "audit_events" in client.get("/api/system/production-readiness").json()["checks"]

    reloaded_store = create_production_store()
    reloaded_store.configure(str(db_path))
    persisted_events = [
        event
        for event in reloaded_store["audit_events"].values()
        if event["project_id"] == project["id"]
    ]
    assert [event["action"] for event in persisted_events] == [event["action"] for event in audit_events]


def test_studio_state_applies_corrections_and_previews_export_wizard():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Studio Actions UI",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "actionable studio ui"},
    ).json()
    client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": job["result_asset"]["id"]},
    )

    state_response = client.get(f"/api/projects/{project['id']}/studio", headers=headers)
    assert state_response.status_code == 200
    studio = state_response.json()
    assert [action["id"] for action in studio["action_dock"]] == [
        "regenerate",
        "open-slice-editor",
        "apply-correction",
        "export-package",
    ]
    assert studio["active_selection"]["active_ir_id"]
    assert studio["active_selection"]["selected_layer_id"] == "button_primary"
    assert [task["kind"] for task in studio["timeline"]] == [
        "text_to_image",
        "ui_segmentation",
        "unity_export",
        "plugin_import",
    ]
    assert studio["timeline"][0]["status"] == "succeeded"
    assert studio["segmentation_corrections"][0]["status"] == "pending"
    assert [step["status"] for step in studio["export_wizard"]["steps"]] == [
        "complete",
        "active",
        "pending",
        "pending",
    ]

    correction_id = studio["segmentation_corrections"][0]["id"]
    apply_response = client.post(
        f"/api/projects/{project['id']}/studio/corrections/{correction_id}/apply",
        headers=headers,
    )
    assert apply_response.status_code == 200
    applied = apply_response.json()
    assert applied["correction"]["status"] == "applied"
    assert applied["updated_node"]["correction_status"] == "applied"
    assert applied["updated_node"]["rect"] == {
        "x": 1308,
        "y": 808,
        "width": 304,
        "height": 120,
    }

    wizard_response = client.post(
        f"/api/projects/{project['id']}/studio/export-wizard",
        headers=headers,
        json={"target_engine": "unity"},
    )
    assert wizard_response.status_code == 200
    preview = wizard_response.json()
    assert preview["export_preview"]["target_engine"] == "unity"
    assert preview["export_preview"]["entry"].endswith("StudioActionsUi.prefab")
    assert preview["export"]["status"] == "ready"
    assert preview["studio"]["timeline"][2]["status"] == "succeeded"

    plugin_response = client.get("/api/plugin/export-jobs", headers=headers)
    assert plugin_response.status_code == 200
    assert plugin_response.json()["jobs"][0]["id"] == preview["export"]["id"]


def test_studio_timeline_uses_selected_engine_export_task():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Godot Studio UI",
            "target_engine": "godot",
            "canvas": {"width": 1280, "height": 720},
        },
    ).json()

    state_response = client.get(f"/api/projects/{project['id']}/studio", headers=headers)
    assert state_response.status_code == 200
    assert state_response.json()["timeline"][2]["kind"] == "godot_export"

    wizard_response = client.post(
        f"/api/projects/{project['id']}/studio/export-wizard",
        headers=headers,
        json={"target_engine": "cocos3"},
    )
    assert wizard_response.status_code == 200
    assert wizard_response.json()["studio"]["timeline"][2]["kind"] == "cocos3_export"


def test_new_project_studio_active_ir_is_readable():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Fresh Studio IR",
            "target_engine": "unity",
            "canvas": {"width": 1280, "height": 720},
        },
    ).json()

    state_response = client.get(f"/api/projects/{project['id']}/studio", headers=headers)
    assert state_response.status_code == 200
    active_ir_id = state_response.json()["active_selection"]["active_ir_id"]

    ir_response = client.get(f"/api/projects/{project['id']}/irs/{active_ir_id}", headers=headers)
    assert ir_response.status_code == 200
    assert ir_response.json()["ir"]["id"] == active_ir_id


def test_studio_timeline_reflects_plugin_import_log_status():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Timeline Import HUD",
            "target_engine": "unreal",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    wizard_response = client.post(
        f"/api/projects/{project['id']}/studio/export-wizard",
        headers=headers,
        json={"target_engine": "unreal"},
    )
    export_id = wizard_response.json()["export"]["id"]

    client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export_id,
            "engine": "unreal",
            "status": "succeeded",
            "plugin_version": "0.2.0",
            "engine_version": "5.3+",
            "duration_ms": 5200,
            "summary": {
                "textures_created": 4,
                "umg_widgets_created": 1,
                "warnings": 1,
                "errors": 0,
            },
            "logs": [{"level": "warning", "message": "Texture compression preset was normalized"}],
        },
    )

    state_response = client.get(f"/api/projects/{project['id']}/studio", headers=headers)

    assert state_response.status_code == 200
    plugin_import = state_response.json()["timeline"][3]
    assert plugin_import["kind"] == "plugin_import"
    assert plugin_import["status"] == "succeeded"
    assert plugin_import["progress"] == 100
    assert plugin_import["summary"]["warnings"] == 1
    assert plugin_import["summary"]["errors"] == 0


def test_segmentation_rejects_assets_from_other_projects():
    owner_headers = auth_headers()
    owner_project = client.post(
        "/api/projects",
        headers=owner_headers,
        json={
            "name": "Owner Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    owner_job = client.post(
        f"/api/projects/{owner_project['id']}/ai/jobs",
        headers=owner_headers,
        json={"kind": "text_to_image", "prompt": "owner asset"},
    ).json()

    other_headers = auth_headers()
    other_project = client.post(
        "/api/projects",
        headers=other_headers,
        json={
            "name": "Other Project",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    response = client.post(
        f"/api/projects/{other_project['id']}/segmentations",
        headers=other_headers,
        json={"asset_id": owner_job["result_asset"]["id"]},
    )

    assert response.status_code == 404


def test_export_paths_sanitize_project_names():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "../Bad UI!",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "safe export"},
    ).json()
    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": job["result_asset"]["id"]},
    ).json()

    export = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": "unity"},
    ).json()

    assert all(".." not in file_path for file_path in export["package"]["files"])
    assert "Assets/GameUIAgent/Prefabs/BadUi.prefab" in export["package"]["files"]


def test_professional_import_converts_psd_layers_to_asset_ir():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "PSD Import UI",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    response = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "psd",
            "file_name": "inventory.psd",
            "layers": [
                {
                    "id": "layer_bg",
                    "name": "Background",
                    "kind": "image",
                    "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                },
                {
                    "id": "layer_button",
                    "name": "Start Button",
                    "kind": "image",
                    "rect": {"x": 760, "y": 820, "width": 400, "height": 120},
                },
                {
                    "id": "layer_label",
                    "name": "Start Text",
                    "kind": "text",
                    "text": "START",
                    "rect": {"x": 820, "y": 850, "width": 280, "height": 60},
                },
            ],
        },
    )

    assert response.status_code == 201
    imported = response.json()
    assert imported["design_document"]["source_type"] == "psd"
    assert imported["design_document"]["preserved_layers"] == 3
    assert imported["ir"]["professional_source"]["file_name"] == "inventory.psd"
    assert [node["type"] for node in imported["ir"]["nodes"]] == [
        "canvas",
        "image",
        "button",
        "text",
    ]
    assert imported["ir"]["nodes"][3]["text"]["content"] == "START"


def test_ir_patch_creates_version_and_export_uses_latest_ir():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Editable HUD",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    imported = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "psd",
            "file_name": "editable-hud.psd",
            "layers": [
                {
                    "id": "layer_button",
                    "name": "Start Button",
                    "kind": "image",
                    "rect": {"x": 760, "y": 820, "width": 400, "height": 120},
                },
            ],
        },
    ).json()
    ir = imported["ir"]

    patch_response = client.post(
        f"/api/projects/{project['id']}/irs/{ir['id']}/patches",
        headers=headers,
        json={
            "base_version": ir["version"],
            "summary": "Move CTA into safe area",
            "operations": [
                {
                    "op": "update_node",
                    "node_id": "layer_button",
                    "fields": {
                        "name": "Safe Area CTA",
                        "rect": {"x": 840, "y": 760, "width": 360, "height": 112},
                        "visible": False,
                    },
                }
            ],
        },
    )

    assert patch_response.status_code == 201
    patched = patch_response.json()
    assert patched["ir"]["version"] == "0.1.1"
    assert patched["version"]["summary"] == "Move CTA into safe area"
    edited_node = next(node for node in patched["ir"]["nodes"] if node["id"] == "layer_button")
    assert edited_node["name"] == "Safe Area CTA"
    assert edited_node["visible"] is False

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": ir["id"], "target_engine": "unity"},
    )
    assert export_response.status_code == 201
    manifest_node = export_response.json()["package"]["manifest"]["asset_ir"]["nodes"][0]
    assert manifest_node["name"] == "Safe Area CTA"
    assert manifest_node["rect"] == {"x": 840, "y": 760, "width": 360, "height": 112}


def test_ir_version_restore_reverts_export_manifest():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Rollback HUD",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    imported = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "psd",
            "file_name": "rollback-hud.psd",
            "layers": [
                {
                    "id": "layer_title",
                    "name": "Original Title",
                    "kind": "text",
                    "text": "START",
                    "rect": {"x": 120, "y": 80, "width": 320, "height": 72},
                },
            ],
        },
    ).json()
    ir = imported["ir"]
    versions = client.get(
        f"/api/projects/{project['id']}/irs/{ir['id']}/versions",
        headers=headers,
    )
    assert versions.status_code == 200
    initial_version_id = versions.json()["versions"][0]["id"]

    patched = client.post(
        f"/api/projects/{project['id']}/irs/{ir['id']}/patches",
        headers=headers,
        json={
            "base_version": ir["version"],
            "summary": "Rename title for experiment",
            "operations": [
                {
                    "op": "update_node",
                    "node_id": "layer_title",
                    "fields": {"name": "Experimental Title", "text": {"content": "PLAY"}},
                }
            ],
        },
    )
    assert patched.status_code == 201

    restored = client.post(
        f"/api/projects/{project['id']}/irs/{ir['id']}/versions/{initial_version_id}/restore",
        headers=headers,
    )
    assert restored.status_code == 200
    restored_node = next(node for node in restored.json()["ir"]["nodes"] if node["id"] == "layer_title")
    assert restored_node["name"] == "Original Title"
    assert restored_node["text"]["content"] == "START"

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": ir["id"], "target_engine": "unity"},
    )
    assert export_response.status_code == 201
    manifest_node = export_response.json()["package"]["manifest"]["asset_ir"]["nodes"][0]
    assert manifest_node["name"] == "Original Title"


def test_ir_validation_blocks_export_with_invalid_nodes():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Invalid IR HUD",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    imported = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "psd",
            "file_name": "invalid-ir.psd",
            "layers": [
                {
                    "id": "layer_bad",
                    "name": "Broken Slice",
                    "kind": "image",
                    "rect": {"x": 100, "y": 100, "width": 200, "height": 80},
                },
            ],
        },
    ).json()
    ir_id = imported["ir"]["id"]
    store["irs"][ir_id]["nodes"][1]["rect"]["width"] = 0
    store.flush()

    validation_response = client.post(
        f"/api/projects/{project['id']}/irs/{ir_id}/validate",
        headers=headers,
    )
    assert validation_response.status_code == 422
    assert validation_response.json()["detail"]["code"] == "EXPORT_VALIDATION_FAILED"
    assert validation_response.json()["detail"]["errors"][0]["node_id"] == "layer_bad"

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": ir_id, "target_engine": "unity"},
    )
    assert export_response.status_code == 422
    assert export_response.json()["detail"]["code"] == "EXPORT_VALIDATION_FAILED"


def test_core_psd_to_unity_plugin_import_chain_is_connected():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "PSD Unity Core Chain",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "psd",
            "file_name": "battle-hud.psd",
            "layers": [
                {
                    "id": "layer_panel",
                    "name": "Main Panel",
                    "kind": "image",
                    "rect": {"x": 120, "y": 160, "width": 1680, "height": 720},
                },
                {
                    "id": "layer_start_button",
                    "name": "Start Button",
                    "kind": "image",
                    "rect": {"x": 760, "y": 820, "width": 400, "height": 120},
                },
                {
                    "id": "layer_start_label",
                    "name": "Start Label",
                    "kind": "text",
                    "text": "START",
                    "rect": {"x": 835, "y": 850, "width": 250, "height": 60},
                },
            ],
        },
    )
    assert import_response.status_code == 201
    imported = import_response.json()
    assert imported["ir"]["professional_source"]["source_type"] == "psd"

    export_response = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": imported["ir"]["id"], "target_engine": "unity"},
    )
    assert export_response.status_code == 201
    export = export_response.json()
    export_id = export["id"]

    manifest_response = client.get(f"/api/plugin/exports/{export_id}/manifest", headers=headers)
    assert manifest_response.status_code == 200
    manifest = manifest_response.json()
    assert manifest["engine"] == "unity"
    assert manifest["entry"]["path"].endswith("PsdUnityCoreChain.prefab")
    assert manifest["professional_source"]["source_type"] == "psd"
    assert manifest["professional_source"]["file_name"] == "battle-hud.psd"
    assert manifest["professional_source"]["preserved_layers"] == 3
    assert manifest["asset_ir"]["node_count"] == 4
    assert manifest["unity_import_plan"]["steps"] == [
        "extract_zip",
        "import_textures_as_sprites",
        "create_prefab",
        "create_scene",
        "write_import_log",
    ]

    download_response = client.get(f"/api/plugin/exports/{export_id}/download", headers=headers)
    assert download_response.status_code == 200
    package = download_response.json()
    assert package["content_type"] == "application/zip"
    assert package["manifest"]["professional_source"]["file_name"] == "battle-hud.psd"
    assert "Assets/GameUIAgent/Prefabs/PsdUnityCoreChain.prefab" in package["files"]

    import_log_response = client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export_id,
            "engine": "unity",
            "status": "succeeded",
            "plugin_version": "0.3.0",
            "engine_version": "2022.3.40f1",
            "duration_ms": 4100,
            "summary": {
                "assets_imported": 4,
                "prefabs_created": 1,
                "scenes_created": 1,
                "warnings": 0,
                "errors": 0,
            },
            "logs": [{"level": "info", "message": "Imported PSD Unity Core Chain prefab"}],
        },
    )
    assert import_log_response.status_code == 201

    studio_response = client.get(f"/api/projects/{project['id']}/studio", headers=headers)
    assert studio_response.status_code == 200
    timeline = studio_response.json()["timeline"]
    assert timeline[2]["kind"] == "unity_export"
    assert timeline[2]["status"] == "succeeded"
    assert timeline[3]["kind"] == "plugin_import"
    assert timeline[3]["status"] == "succeeded"
    assert timeline[3]["summary"]["prefabs_created"] == 1


def test_core_psd_asset_ir_reaches_all_engine_plugin_imports():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "PSD Multi Engine Chain",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    imported = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "psd",
            "file_name": "multi-engine-hud.psd",
            "layers": [
                {
                    "id": "layer_panel",
                    "name": "Main Panel",
                    "kind": "image",
                    "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                },
                {
                    "id": "layer_start_button",
                    "name": "Start Button",
                    "kind": "image",
                    "rect": {"x": 760, "y": 820, "width": 400, "height": 120},
                },
                {
                    "id": "layer_start_text",
                    "name": "Start Text",
                    "kind": "text",
                    "text": "START",
                    "rect": {"x": 820, "y": 850, "width": 280, "height": 60},
                },
            ],
        },
    ).json()

    cases = [
        ("cocos3", "create_scene", {"prefabs_created": 1, "scenes_created": 1, "warnings": 0, "errors": 0}),
        ("cocos2", "create_prefab", {"prefabs_created": 1, "warnings": 0, "errors": 0}),
        ("godot", "write_tscn_scene", {"scenes_created": 1, "controls_created": 4, "warnings": 0, "errors": 0}),
        ("unreal", "create_umg_widget_blueprint", {"umg_widgets_created": 1, "textures_created": 1, "warnings": 0, "errors": 0}),
    ]
    for engine, expected_step, summary in cases:
        export_response = client.post(
            f"/api/projects/{project['id']}/exports",
            headers=headers,
            json={"ir_id": imported["ir"]["id"], "target_engine": engine},
        )
        assert export_response.status_code == 201
        export = export_response.json()

        manifest_response = client.get(f"/api/plugin/exports/{export['id']}/manifest", headers=headers)
        assert manifest_response.status_code == 200
        manifest = manifest_response.json()
        assert manifest["engine"] == engine
        assert manifest["professional_source"]["source_type"] == "psd"
        assert manifest["professional_source"]["file_name"] == "multi-engine-hud.psd"
        assert manifest["professional_source"]["preserved_layers"] == 3
        assert manifest["asset_ir"]["node_count"] == 4
        assert expected_step in manifest["import_plan"]["steps"]

        log_response = client.post(
            "/api/plugin/import-logs",
            headers=headers,
            json={
                "export_id": export["id"],
                "engine": engine,
                "status": "succeeded",
                "plugin_version": "0.3.0",
                "engine_version": manifest["engine_version"],
                "duration_ms": 4300,
                "summary": summary,
                "logs": [{"level": "info", "message": f"Imported {engine} package"}],
            },
        )
        assert log_response.status_code == 201

        import_logs = client.get(f"/api/plugin/exports/{export['id']}/import-logs", headers=headers).json()
        assert import_logs["engine"] == engine
        assert import_logs["latest_log"]["summary"] == summary


def test_figma_import_preserves_component_and_auto_layout_metadata():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Figma Import UI",
            "target_engine": "unity",
            "canvas": {"width": 1440, "height": 900},
        },
    ).json()

    response = client.post(
        f"/api/projects/{project['id']}/imports/professional",
        headers=headers,
        json={
            "source_type": "figma",
            "file_name": "https://figma.com/file/game-ui",
            "frame_id": "42:100",
            "layers": [
                {
                    "id": "42:101",
                    "name": "Shop Card",
                    "kind": "component",
                    "component_key": "shop-card",
                    "auto_layout": {"direction": "vertical", "gap": 12},
                    "rect": {"x": 100, "y": 100, "width": 360, "height": 520},
                }
            ],
        },
    )

    assert response.status_code == 201
    imported = response.json()
    node = imported["ir"]["nodes"][1]
    assert node["component"]["key"] == "shop-card"
    assert node["layout"]["auto_layout"]["direction"] == "vertical"
    assert imported["ir"]["professional_source"]["frame_id"] == "42:100"


def test_developer_api_super_matting_cost_execute_poll_cancel():
    headers = auth_headers()

    key_response = client.post("/api/user/api-keys", headers=headers, json={"name": "ci"})
    assert key_response.status_code == 201
    api_key = key_response.json()["api_key"]
    api_headers = {"X-API-Key": api_key}

    cost_response = client.post(
        "/api/ai/services/super-matting/cost",
        headers=api_headers,
        json={"image_url": "https://example.com/hero.png", "output": "alpha_png"},
    )
    assert cost_response.status_code == 200
    assert cost_response.json()["estimated_credits"] == 2

    execute_response = client.post(
        "/api/ai/services/super-matting/execute",
        headers=api_headers,
        json={
            "image_url": "https://example.com/hero.png",
            "output": "alpha_png",
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert execute_response.status_code == 201
    task = execute_response.json()
    assert task["status"] == "queued"
    assert task["webhook"]["signature_algorithm"] == "HMAC-SHA256"

    poll_response = client.get(f"/api/ai/tasks/{task['task_id']}", headers=api_headers)
    assert poll_response.status_code == 200
    assert poll_response.json()["status"] in {"queued", "succeeded"}

    cancel_response = client.post(f"/api/ai/tasks/{task['task_id']}/cancel", headers=api_headers)
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


def test_developer_api_deducts_credits_and_returns_rate_limit_headers():
    headers = auth_headers()

    key_response = client.post("/api/user/api-keys", headers=headers, json={"name": "billing-ci"})
    assert key_response.status_code == 201
    api_headers = {"X-API-Key": key_response.json()["api_key"]}

    billing_response = client.get("/api/user/billing", headers=headers)
    assert billing_response.status_code == 200
    initial_billing = billing_response.json()
    assert initial_billing["plan"]["id"] == "pro_trial"
    assert initial_billing["credits"]["total_available"] == 120

    cost_response = client.post(
        "/api/ai/services/super-matting/cost",
        headers=api_headers,
        json={
            "image_url": "https://example.com/large-hero.png",
            "output": "alpha_png",
            "width": 1024,
            "height": 1024,
        },
    )
    assert cost_response.status_code == 200
    assert cost_response.json()["estimated_credits"] == 10
    assert cost_response.headers["X-RateLimit-Limit"] == "60"
    assert int(cost_response.headers["X-RateLimit-Remaining"]) >= 0
    assert cost_response.headers["X-RateLimit-Reset"] == "60"

    execute_response = client.post(
        "/api/ai/services/super-matting/execute",
        headers=api_headers,
        json={
            "image_url": "https://example.com/large-hero.png",
            "output": "alpha_png",
            "width": 1024,
            "height": 1024,
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert execute_response.status_code == 201
    task = execute_response.json()
    assert task["cost_credits"] == 10
    assert task["billing_usage"]["deducted"] == {"daily_free": 10, "monthly": 0, "purchased": 0}

    updated_billing = client.get("/api/user/billing", headers=headers).json()
    assert updated_billing["credits"]["daily_free"] == 10
    assert updated_billing["credits"]["total_available"] == 110

    usage_response = client.get("/api/user/usage", headers=headers)
    assert usage_response.status_code == 200
    usage_event = usage_response.json()["events"][0]
    assert usage_event["service"] == "super-matting"
    assert usage_event["credits"] == 10
    assert usage_event["task_id"] == task["task_id"]


def test_api_key_creation_requires_api_entitlement(tmp_path):
    configure_persistent_store(str(tmp_path / "api-entitlement.sqlite3"))
    configure_object_storage(str(tmp_path / "api-entitlement-objects"))

    email = f"api-entitlement-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "No API"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    user_id = client.get("/api/user/me", headers=headers).json()["id"]
    account = store["billing_accounts"][user_id]
    account["plan"] = {
        "id": "free",
        "name": "Free",
        "api_enabled": False,
        "rate_limit_per_minute": 5,
        "concurrent_ai_tasks": 1,
    }
    store.flush()

    response = client.post("/api/user/api-keys", headers=headers, json={"name": "blocked"})
    assert response.status_code == 403
    assert response.json()["detail"] == "API access is not enabled for the current plan"


def test_existing_api_key_is_blocked_after_plan_loses_api_entitlement(tmp_path):
    configure_persistent_store(str(tmp_path / "api-runtime-entitlement.sqlite3"))
    configure_object_storage(str(tmp_path / "api-runtime-entitlement-objects"))

    headers = auth_headers()
    key_response = client.post("/api/user/api-keys", headers=headers, json={"name": "runtime-gate"})
    assert key_response.status_code == 201
    api_headers = {"X-API-Key": key_response.json()["api_key"]}

    user_id = client.get("/api/user/me", headers=headers).json()["id"]
    account = store["billing_accounts"][user_id]
    account["plan"] = {
        "id": "free",
        "name": "Free",
        "api_enabled": False,
        "rate_limit_per_minute": 5,
        "concurrent_ai_tasks": 1,
    }
    store.flush()

    response = client.post(
        "/api/ai/services/super-matting/cost",
        headers=api_headers,
        json={
            "image_url": "https://example.com/no-api.png",
            "output": "alpha_png",
            "width": 512,
            "height": 512,
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "API access is not enabled for the current plan"


def test_developer_api_rate_limit_resets_after_window(tmp_path):
    configure_persistent_store(str(tmp_path / "api-rate-limit.sqlite3"))
    configure_object_storage(str(tmp_path / "api-rate-limit-objects"))

    headers = auth_headers()
    user_id = client.get("/api/user/me", headers=headers).json()["id"]
    account = store["billing_accounts"][user_id]
    account["plan"]["rate_limit_per_minute"] = 1
    store.flush()

    key_response = client.post("/api/user/api-keys", headers=headers, json={"name": "rate-window"})
    api_headers = {"X-API-Key": key_response.json()["api_key"]}
    payload = {
        "image_url": "https://example.com/rate-limit.png",
        "output": "alpha_png",
        "width": 512,
        "height": 512,
    }

    first = client.post("/api/ai/services/super-matting/cost", headers=api_headers, json=payload)
    assert first.status_code == 200
    assert first.headers["X-RateLimit-Remaining"] == "0"

    blocked = client.post("/api/ai/services/super-matting/cost", headers=api_headers, json=payload)
    assert blocked.status_code == 429

    store["rate_limits"][user_id] = {"window_start": "2000-01-01T00:00:00+00:00", "count": 1}
    store.flush()

    reset = client.post("/api/ai/services/super-matting/cost", headers=api_headers, json=payload)
    assert reset.status_code == 200
    assert reset.headers["X-RateLimit-Remaining"] == "0"


def create_engine_export(headers: dict[str, str], target_engine: str, name: str = "Plugin HUD") -> dict:
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": name,
            "target_engine": target_engine,
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()
    job = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={"kind": "text_to_image", "prompt": "unity plugin import hud"},
    ).json()
    segmentation = client.post(
        f"/api/projects/{project['id']}/segmentations",
        headers=headers,
        json={"asset_id": job["result_asset"]["id"]},
    ).json()
    export = client.post(
        f"/api/projects/{project['id']}/exports",
        headers=headers,
        json={"ir_id": segmentation["ir"]["id"], "target_engine": target_engine},
    ).json()
    return {"project": project, "export": export}


def create_unity_export(headers: dict[str, str], name: str = "Plugin HUD") -> dict:
    return create_engine_export(headers, "unity", name)


def test_unity_plugin_manifest_download_and_import_log_flow():
    headers = auth_headers()
    created = create_unity_export(headers)
    export_id = created["export"]["id"]

    manifest_response = client.get(f"/api/plugin/exports/{export_id}/manifest", headers=headers)
    assert manifest_response.status_code == 200
    manifest = manifest_response.json()
    assert manifest["engine"] == "unity"
    assert manifest["entry"]["type"] == "prefab"
    assert manifest["entry"]["path"].endswith("PluginHud.prefab")
    assert manifest["download_url"] == f"/api/plugin/exports/{export_id}/download"
    assert manifest["unity_import_plan"]["steps"] == [
        "extract_zip",
        "import_textures_as_sprites",
        "create_prefab",
        "create_scene",
        "write_import_log",
    ]

    download_response = client.get(f"/api/plugin/exports/{export_id}/download", headers=headers)
    assert download_response.status_code == 200
    package = download_response.json()
    assert package["content_type"] == "application/zip"
    assert package["manifest"]["package_id"] == export_id
    assert "Assets/GameUIAgent/Prefabs/PluginHud.prefab" in package["files"]

    zip_response = client.get(
        f"/api/plugin/exports/{export_id}/download",
        headers={**headers, "Accept": "application/zip"},
    )
    assert zip_response.status_code == 200
    assert zip_response.headers["content-type"] == "application/zip"
    assert zip_response.headers["content-disposition"] == f'attachment; filename="{export_id}.zip"'
    with ZipFile(BytesIO(zip_response.content)) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert "Assets/GameUIAgent/Prefabs/PluginHud.prefab" in names
        assert export_id in archive.read("manifest.json").decode("utf-8")

    log_response = client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export_id,
            "engine": "unity",
            "status": "succeeded",
            "plugin_version": "0.1.0",
            "engine_version": "2022.3.40f1",
            "duration_ms": 3400,
            "summary": {
                "assets_imported": 4,
                "prefabs_created": 1,
                "scenes_created": 1,
                "warnings": 0,
                "errors": 0,
            },
            "logs": [{"level": "info", "message": "Imported PluginHud.prefab"}],
        },
    )
    assert log_response.status_code == 201
    assert log_response.json()["summary"]["prefabs_created"] == 1


def test_real_engine_e2e_runner_executes_editor_and_records_import_snapshot_ir(tmp_path, monkeypatch):
    headers = auth_headers()
    created = create_unity_export(headers, "Real Editor HUD")
    export_id = created["export"]["id"]
    runner = tmp_path / "unity-e2e-runner"
    runner.write_text(
        """#!/bin/sh
cat <<'JSON'
{
  "status": "succeeded",
  "engine_version": "2022.3.40f1",
  "plugin_version": "0.3.0",
  "duration_ms": 4200,
  "summary": {"assets_imported": 4, "prefabs_created": 1, "warnings": 0, "errors": 0},
  "logs": [{"level": "info", "message": "Imported from real Unity batch mode"}],
  "snapshot": {
    "source": "unity_batchmode",
    "layout": {
      "screen": "RuntimeHUD",
      "nodes": [
        {"id": "root", "name": "Runtime HUD", "type": "canvas", "rect": {"x": 0, "y": 0, "width": 1280, "height": 720}},
        {"id": "cta", "name": "Play CTA", "type": "button", "rect": {"x": 480, "y": 560, "width": 320, "height": 96}, "parent_id": "root"}
      ]
    },
    "sprites": [{"id": "cta_sprite", "name": "Play CTA Sprite", "path": "Assets/GameUIAgent/Textures/cta.png"}]
  }
}
JSON
""",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    monkeypatch.setenv("GAMEUIAGENT_UNITY_EXECUTABLE", str(runner))

    response = client.post(f"/api/system/engine-e2e/exports/{export_id}/run")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["engine"] == "unity"
    assert body["import_log"]["summary"]["prefabs_created"] == 1
    assert body["snapshot"]["source"] == "unity_batchmode"
    assert body["ir"]["nodes"][1]["name"] == "Play CTA"
    assert body["command"]["executable"] == str(runner)


def test_engine_e2e_runner_extracts_json_from_unity_stdout_noise(tmp_path, monkeypatch):
    headers = auth_headers()
    created = create_unity_export(headers, "Noisy Unity Editor HUD")
    export_id = created["export"]["id"]
    runner = tmp_path / "noisy-unity-e2e-runner"
    runner.write_text(
        """#!/bin/sh
printf 'unable to open database file\\n'
printf 'Unity licensing noise before result\\n'
cat <<'JSON'
{"status":"succeeded","engine_version":"2022.3.11f1","plugin_version":"0.3.0","duration_ms":7,"summary":{"assets_imported":2,"prefabs_created":1,"warnings":0,"errors":0},"logs":[{"level":"info","message":"Noisy Unity stdout tolerated"}],"snapshot":{"source":"unity_batchmode","layout":{"screen":"NoisyHUD","nodes":[{"id":"root","name":"Noisy HUD","type":"canvas","rect":{"x":0,"y":0,"width":1280,"height":720}}]},"sprites":[]}}
JSON
""",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    monkeypatch.setenv("GAMEUIAGENT_UNITY_EXECUTABLE", str(runner))

    response = client.post(f"/api/system/engine-e2e/exports/{export_id}/run")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["engine_version"] == "2022.3.11f1"
    assert body["import_log"]["logs"][0]["message"] == "Noisy Unity stdout tolerated"


def test_unity_test_project_contains_real_plugin_and_batchmode_runner():
    project_root = REPO_ROOT / "engines" / "unity-test-project"
    runner_script = project_root / "run-gameuiagent-e2e.sh"
    editor_runner = project_root / "Assets" / "GameUIAgent" / "Editor" / "GameUIAgentE2ERunner.cs"
    package_manifest = project_root / "Packages" / "manifest.json"
    project_version = project_root / "ProjectSettings" / "ProjectVersion.txt"

    assert project_version.exists()
    assert package_manifest.exists()
    assert editor_runner.exists()
    assert runner_script.exists()

    runner_source = runner_script.read_text(encoding="utf-8")
    assert "-batchmode" in runner_source
    assert "-executeMethod GameUIAgent.Editor.GameUIAgentE2ERunner.Run" in runner_source
    assert "UNITY_EDITOR_EXECUTABLE" in runner_source
    assert "GAMEUIAGENT_E2E_PACKAGE_JSON" in runner_source
    assert "GAMEUIAGENT_E2E_RESULT_PATH" in runner_source
    assert "cat \"$RESULT_PATH\"" in runner_source
    assert "-logFile \"$LOG_PATH\"" in runner_source

    editor_source = editor_runner.read_text(encoding="utf-8")
    assert "namespace GameUIAgent.Editor" in editor_source
    assert "public static void Run()" in editor_source
    assert "Environment.GetEnvironmentVariable(\"GAMEUIAGENT_E2E_PACKAGE_JSON\")" in editor_source
    assert "Environment.GetEnvironmentVariable(\"GAMEUIAGENT_E2E_RESULT_PATH\")" in editor_source
    assert "PrefabUtility.SaveAsPrefabAsset" in editor_source
    assert "File.WriteAllText(resultPath" in editor_source
    assert "JsonUtility.ToJson" in editor_source
    assert "Console.Out.WriteLine" in editor_source


def test_unreal_plugin_import_logs_can_be_queried_with_summary():
    headers = auth_headers()
    created = create_engine_export(headers, "unreal", "Unreal Import HUD")
    export_id = created["export"]["id"]

    log_response = client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export_id,
            "engine": "unreal",
            "status": "succeeded",
            "plugin_version": "0.2.0",
            "engine_version": "5.3+",
            "duration_ms": 5200,
            "summary": {
                "textures_created": 4,
                "umg_widgets_created": 1,
                "slate_slots_bound": 7,
                "warnings": 1,
                "errors": 0,
            },
            "logs": [{"level": "warning", "message": "Texture compression preset was normalized"}],
        },
    )
    assert log_response.status_code == 201

    query_response = client.get(f"/api/plugin/exports/{export_id}/import-logs", headers=headers)

    assert query_response.status_code == 200
    import_logs = query_response.json()
    assert import_logs["export_id"] == export_id
    assert import_logs["engine"] == "unreal"
    assert import_logs["summary"]["textures_created"] == 4
    assert import_logs["summary"]["umg_widgets_created"] == 1
    assert import_logs["summary"]["warnings"] == 1
    assert import_logs["latest_log"]["engine_version"] == "5.3+"
    assert import_logs["latest_log"]["logs"][0]["level"] == "warning"


def test_plugin_import_log_rejects_engine_mismatch():
    headers = auth_headers()
    export_id = create_engine_export(headers, "unreal", "Mismatched Import HUD")["export"]["id"]

    log_response = client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export_id,
            "engine": "unity",
            "status": "succeeded",
            "plugin_version": "0.2.0",
            "engine_version": "2022.3.40f1",
            "duration_ms": 1200,
            "summary": {"prefabs_created": 1, "warnings": 0, "errors": 0},
            "logs": [{"level": "info", "message": "Wrong engine log"}],
        },
    )

    assert log_response.status_code == 422
    assert log_response.json()["detail"] == "Import log engine does not match export engine"


def test_plugin_import_log_rejects_unknown_status():
    headers = auth_headers()
    export_id = create_engine_export(headers, "unreal", "Unknown Status HUD")["export"]["id"]

    log_response = client.post(
        "/api/plugin/import-logs",
        headers=headers,
        json={
            "export_id": export_id,
            "engine": "unreal",
            "status": "partial",
            "plugin_version": "0.2.0",
            "engine_version": "5.3+",
            "duration_ms": 1800,
            "summary": {"warnings": 1, "errors": 0},
            "logs": [{"level": "warning", "message": "Unknown status should be rejected"}],
        },
    )

    assert log_response.status_code == 422
    assert log_response.json()["detail"] == "Unsupported import log status"


def test_multi_engine_exports_have_native_manifest_import_plans():
    headers = auth_headers()
    cases = [
        (
            "cocos3",
            "Cocos3/assets/vberai/prefabs/PluginHud.prefab",
            "3.8.6+",
            ["copy_textures", "create_sprite_frames", "create_prefab", "create_scene", "write_import_log"],
        ),
        (
            "cocos2",
            "Cocos2/assets/resources/vberai/prefabs/PluginHud.prefab",
            "2.4.x+",
            ["copy_textures", "create_sprite_frames", "create_prefab", "write_import_log"],
        ),
        (
            "godot",
            "Godot/vberai/scenes/PluginHud.tscn",
            "4.x",
            ["copy_textures", "write_tscn_scene", "refresh_filesystem", "write_import_log"],
        ),
        (
            "unreal",
            "Unreal/Content/GameUIAgent/Widgets/WBP_PluginHud.uasset",
            "5.3+",
            ["copy_textures", "create_texture_assets", "create_umg_widget_blueprint", "bind_slate_slots", "write_import_log"],
        ),
    ]

    for engine, entry_path, engine_version, steps in cases:
        export_id = create_engine_export(headers, engine)["export"]["id"]
        manifest_response = client.get(f"/api/plugin/exports/{export_id}/manifest", headers=headers)

        assert manifest_response.status_code == 200
        manifest = manifest_response.json()
        assert manifest["engine"] == engine
        assert manifest["engine_version"] == engine_version
        assert manifest["entry"]["path"] == entry_path
        assert manifest["import_plan"]["steps"] == steps
        assert any(asset["kind"] == "texture" for asset in manifest["assets"])


def test_plugin_cannot_read_other_users_export_manifest():
    owner_headers = auth_headers()
    export_id = create_unity_export(owner_headers, "Private HUD")["export"]["id"]
    other_headers = auth_headers()

    response = client.get(f"/api/plugin/exports/{export_id}/manifest", headers=other_headers)

    assert response.status_code == 404


def test_plugin_auth_lists_projects_and_project_exports():
    headers = auth_headers()
    unity_created = create_unity_export(headers, "Plugin Portal")
    godot_created = create_engine_export(headers, "godot", "Plugin Portal Godot")
    web_token = headers["Authorization"].split(" ", 1)[1]

    auth_response = client.post(
        "/api/plugin/auth",
        json={
            "token": web_token,
            "engine": "unity",
            "engine_version": "2022.3.40f1",
            "plugin_version": "0.1.0",
            "device_name": "MacBook Pro",
        },
    )
    assert auth_response.status_code == 200
    plugin_token = auth_response.json()["access_token"]
    plugin_headers = {"Authorization": f"Bearer {plugin_token}"}

    projects_response = client.get("/api/plugin/projects", headers=plugin_headers)
    assert projects_response.status_code == 200
    projects = projects_response.json()["projects"]
    assert {project["id"] for project in projects} == {
        unity_created["project"]["id"],
        godot_created["project"]["id"],
    }
    assert projects[0]["target_engines"] == ["unity", "cocos3", "cocos2", "godot", "unreal"]

    exports_response = client.get(
        f"/api/plugin/projects/{unity_created['project']['id']}/exports?engine=unity",
        headers=plugin_headers,
    )
    assert exports_response.status_code == 200
    exports = exports_response.json()["exports"]
    assert [export["id"] for export in exports] == [unity_created["export"]["id"]]
    assert exports[0]["manifest_url"] == f"/api/plugin/exports/{unity_created['export']['id']}/manifest"


def test_studio_unreal_wizard_export_is_queryable_by_unreal_plugin():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Unreal Wizard HUD",
            "target_engine": "unreal",
            "canvas": {"width": 1920, "height": 1080},
        },
    ).json()

    wizard_response = client.post(
        f"/api/projects/{project['id']}/studio/export-wizard",
        headers=headers,
        json={"target_engine": "unreal"},
    )
    assert wizard_response.status_code == 200
    wizard = wizard_response.json()
    assert wizard["export_preview"]["target_engine"] == "unreal"
    assert wizard["export_preview"]["entry"].endswith("WBP_UnrealWizardHud.uasset")

    exports_response = client.get(
        f"/api/plugin/projects/{project['id']}/exports?engine=unreal",
        headers=headers,
    )
    assert exports_response.status_code == 200
    exports = exports_response.json()["exports"]
    assert [export["id"] for export in exports] == [wizard["export"]["id"]]
    assert exports[0]["engine_version"] == "5.3+"
    assert exports[0]["entry"]["type"] == "umg_widget_blueprint"
    assert exports[0]["entry"]["path"].endswith("WBP_UnrealWizardHud.uasset")


def test_unity_restyle_preserves_layout_bindings():
    headers = auth_headers()
    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Existing HUD",
            "target_engine": "unity",
            "canvas": {"width": 1334, "height": 750},
        },
    ).json()

    snapshot_response = client.post(
        f"/api/projects/{project['id']}/engine-snapshots",
        headers=headers,
        json={
            "engine": "unity",
            "source": "prefab",
            "layout": {
                "root": "Canvas/HUD",
                "nodes": [
                    {
                        "path": "Canvas/HUD/StartButton",
                        "rect": {"x": 512, "y": 600, "width": 300, "height": 88},
                        "bindings": ["Button.onClick", "StartGameController"],
                    }
                ],
            },
            "sprites": [{"path": "Assets/UI/start.png", "role": "button"}],
        },
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()

    restyle_response = client.post(
        f"/api/plugin/engine-snapshots/{snapshot['id']}/restyle",
        headers=headers,
        json={
            "style_prompt": "fantasy gold ornate mobile game ui",
            "preserve_layout": True,
            "replacement_strategy": "theme_variant",
            "theme_name": "fantasy_gold",
        },
    )
    assert restyle_response.status_code == 201
    restyle = restyle_response.json()
    assert restyle["replacement_manifest"]["preserved_bindings"] == [
        "Button.onClick",
        "StartGameController",
    ]
    assert restyle["replacement_manifest"]["strategy"] == "theme_variant"
    assert restyle["replacement_manifest"]["layout_policy"] == "preserve_rect_transform"
    assert restyle["replacement_manifest"]["replacements"][0]["node_path"] == "Canvas/HUD/StartButton"
    assert restyle["replacement_manifest"]["replacements"][0]["rect"] == {
        "x": 512,
        "y": 600,
        "width": 300,
        "height": 88,
    }


def test_system_metrics_endpoint_returns_running_counts(tmp_path):
    db_path = tmp_path / "metrics.sqlite3"
    object_store_path = tmp_path / "metrics-objects"
    configure_persistent_store(str(db_path))
    configure_object_storage(str(object_store_path))

    email = f"metrics-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "Metrics User"})
    login_response = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Metrics Test Project",
            "target_engine": "unity",
            "canvas": {"width": 1024, "height": 768},
        },
    ).json()

    png_bytes = rgba_png_with_opaque_rects(512, 512, [{"x": 0, "y": 0, "width": 512, "height": 512}])

    upload_response = client.post(
        f"/api/projects/{project['id']}/assets/upload",
        headers=headers,
        data={
            "name": "splash.png",
            "type": "original_upload",
            "width": "512",
            "height": "512",
            "usage": "source_ui",
        },
        files={"file": ("splash.png", png_bytes, "image/png")},
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["id"].startswith("ast_")

    client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text-to-image",
            "prompt": "game ui button",
            "execution_mode": "queued",
        },
    )

    metrics_response = client.get("/api/system/metrics", headers=headers)

    assert metrics_response.status_code == 200
    metrics = metrics_response.json()

    assert metrics["queue"]["total"] >= 1
    assert metrics["queue"]["queued"] >= 1
    assert metrics["assets"]["total"] >= 1
    assert metrics["assets"]["by_source"]["object_storage"] >= 1
    assert metrics["audits"]["total"] >= 1


def test_worker_dequeue_and_task_completion_flow(tmp_path):
    db_path = tmp_path / "worker.sqlite3"
    object_store_path = tmp_path / "worker-objects"
    configure_persistent_store(str(db_path))
    configure_object_storage(str(object_store_path))
    configure_worker_token("test-worker-token")

    email = f"worker-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "Worker Test User"})
    login_response = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Worker Test Project",
            "target_engine": "unity",
            "canvas": {"width": 1024, "height": 768},
        },
    ).json()

    client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text-to-image",
            "prompt": "game ui button",
            "execution_mode": "queued",
        },
    )

    worker_headers = {"X-Worker-Token": "test-worker-token"}

    dequeue_response = client.post("/api/worker/jobs/dequeue", headers=worker_headers)
    assert dequeue_response.status_code == 200
    dequeued = dequeue_response.json()
    assert dequeued["status"] == "dequeued"
    assert dequeued["queue_item"]["status"] == "locked"
    assert "worker" in dequeued["queue_item"]

    complete_response = client.post(
        f"/api/worker/jobs/{dequeued['queue_item']['id']}/complete",
        headers=worker_headers,
        json={
            "status": "succeeded",
            "result": {
                "asset_id": "ast_test_123",
                "image_url": "/api/assets/ast_test_123/download",
                "credits_used": 10,
            },
        },
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["queue_item"]["status"] == "succeeded"
    assert completed["job"]["status"] == "succeeded"


def test_billing_credits_recharge_and_deduction_flow(tmp_path):
    configure_persistent_store(str(tmp_path / "billing.sqlite3"))
    configure_object_storage(str(tmp_path / "billing-objects"))

    email = f"billing-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "Billing User"})
    login_response = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    billing_before = client.get("/api/user/billing", headers=headers).json()
    assert billing_before["credits"]["purchased"] == 0
    assert billing_before["credits"]["total_available"] == 120

    order_response = client.post(
        "/api/user/billing/orders",
        headers=headers,
        json={
            "amount": 100,
            "method": "stripe",
            "external_reference": f"checkout_{uuid4().hex}",
        },
    )
    assert order_response.status_code == 201
    order = order_response.json()
    assert order["status"] == "pending"
    assert order["credits"] == 100
    assert order["provider"] == "stripe"
    assert order["entitlement_snapshot"]["plan_id"] == "pro_trial"

    confirm_response = client.post(
        f"/api/user/billing/orders/{order['id']}/confirm",
        headers=headers,
        json={"provider_payment_id": f"pi_{uuid4().hex}"},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()
    assert confirmed["order"]["status"] == "paid"
    assert confirmed["billing"]["credits"]["purchased"] == 100

    confirm_again = client.post(
        f"/api/user/billing/orders/{order['id']}/confirm",
        headers=headers,
        json={"provider_payment_id": "ignored_duplicate"},
    )
    assert confirm_again.status_code == 200
    assert confirm_again.json()["order"]["status"] == "paid"
    assert confirm_again.json()["billing"]["credits"]["purchased"] == 100

    recharged = client.get("/api/user/billing", headers=headers).json()
    assert recharged["credits"]["purchased"] == 100
    assert recharged["credits"]["total_available"] == 220

    legacy_recharge = client.post(
        "/api/user/billing/recharge",
        headers=headers,
        json={
            "amount": 100,
            "method": "stripe",
            "transaction_id": f"txn_{uuid4().hex}",
        },
    )
    assert legacy_recharge.status_code == 410

    project = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Billing Test Project",
            "target_engine": "unity",
            "canvas": {"width": 1024, "height": 768},
        },
    ).json()

    job_response = client.post(
        f"/api/projects/{project['id']}/ai/jobs",
        headers=headers,
        json={
            "kind": "text-to-image",
            "prompt": "test",
            "execution_mode": "inline",
        },
    )
    assert job_response.status_code == 201
    job = job_response.json()
    assert "cost_credits" in job

    billing_after = client.get("/api/user/billing", headers=headers).json()
    assert billing_after["credits"]["total_available"] == 220 - job.get("cost_credits", 0)


def test_api_keys_create_list_and_revoke(tmp_path):
    configure_persistent_store(str(tmp_path / "apikeys.sqlite3"))
    configure_object_storage(str(tmp_path / "apikeys-objects"))

    email = f"apikeys-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "API Keys User"})
    login_response = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    list_empty = client.get("/api/user/api-keys", headers=headers).json()
    assert list_empty["api_keys"] == []

    create_resp = client.post("/api/user/api-keys", headers=headers, json={"name": "Production Key"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Production Key"
    assert created["api_key"].startswith("guk_")
    assert "id" in created
    assert "created_at" in created

    list_after = client.get("/api/user/api-keys", headers=headers).json()
    assert len(list_after["api_keys"]) == 1
    key = list_after["api_keys"][0]
    assert key["name"] == "Production Key"
    assert key["prefix"].startswith("guk_")
    assert "..." in key["prefix"]
    assert "created_at" in key

    create_resp2 = client.post("/api/user/api-keys", headers=headers, json={"name": "Dev Key"})
    assert create_resp2.status_code == 201

    list_two = client.get("/api/user/api-keys", headers=headers).json()
    assert len(list_two["api_keys"]) == 2

    revoke_resp = client.delete(f"/api/user/api-keys/{key['id']}", headers=headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "revoked"

    list_final = client.get("/api/user/api-keys", headers=headers).json()
    assert len(list_final["api_keys"]) == 1
    assert list_final["api_keys"][0]["name"] == "Dev Key"


def test_api_keys_revoke_unknown_returns_404(tmp_path):
    configure_persistent_store(str(tmp_path / "apikeys404.sqlite3"))
    configure_object_storage(str(tmp_path / "apikeys404-objects"))

    email = f"apikeys404-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "User"})
    login_response = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    resp = client.delete("/api/user/api-keys/key_nonexistent", headers=headers)
    assert resp.status_code == 404


def test_api_keys_isolated_per_user(tmp_path):
    configure_persistent_store(str(tmp_path / "apikeysiso.sqlite3"))
    configure_object_storage(str(tmp_path / "apikeysiso-objects"))

    email1 = f"user1-{uuid4().hex}@gameuiagent.dev"
    email2 = f"user2-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email1, "password": "secret-pass", "name": "User 1"})
    client.post("/api/auth/register", json={"email": email2, "password": "secret-pass", "name": "User 2"})
    h1 = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': email1, 'password': 'secret-pass'}).json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': email2, 'password': 'secret-pass'}).json()['access_token']}"}

    client.post("/api/user/api-keys", headers=h1, json={"name": "User1 Key"})
    client.post("/api/user/api-keys", headers=h2, json={"name": "User2 Key"})

    list1 = client.get("/api/user/api-keys", headers=h1).json()
    list2 = client.get("/api/user/api-keys", headers=h2).json()
    assert len(list1["api_keys"]) == 1
    assert list1["api_keys"][0]["name"] == "User1 Key"
    assert len(list2["api_keys"]) == 1
    assert list2["api_keys"][0]["name"] == "User2 Key"


def test_webhooks_crud_flow(tmp_path):
    configure_persistent_store(str(tmp_path / "webhooks.sqlite3"))
    configure_object_storage(str(tmp_path / "webhooks-objects"))

    email = f"wh-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "WH User"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    events_resp = client.get("/api/user/webhook-events", headers=headers)
    assert events_resp.status_code == 200
    assert "ai.job.completed" in events_resp.json()["events"]

    list_empty = client.get("/api/user/webhooks", headers=headers).json()
    assert list_empty["webhooks"] == []

    create_resp = client.post("/api/user/webhooks", headers=headers, json={
        "url": "https://example.com/webhook",
        "events": ["ai.job.completed", "ai.job.failed"],
        "description": "Production webhook",
    })
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["url"] == "https://example.com/webhook"
    assert len(created["events"]) == 2
    assert created["active"] is True
    assert created["secret"].startswith("whsec_")
    assert "id" in created
    assert "created_at" in created

    list_after = client.get("/api/user/webhooks", headers=headers).json()
    assert len(list_after["webhooks"]) == 1
    assert "secret" not in list_after["webhooks"][0]
    assert list_after["webhooks"][0]["url"] == "https://example.com/webhook"

    get_resp = client.get(f"/api/user/webhooks/{created['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["description"] == "Production webhook"

    update_resp = client.patch(f"/api/user/webhooks/{created['id']}", headers=headers, json={
        "active": False,
        "description": "Disabled",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["active"] is False
    assert update_resp.json()["description"] == "Disabled"

    test_resp = client.post(f"/api/user/webhooks/{created['id']}/test", headers=headers)
    assert test_resp.status_code == 200
    assert test_resp.json()["status"] == "test_queued"

    delete_resp = client.delete(f"/api/user/webhooks/{created['id']}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"

    list_final = client.get("/api/user/webhooks", headers=headers).json()
    assert len(list_final["webhooks"]) == 0


def test_webhook_test_event_posts_signed_delivery_and_updates_metrics(tmp_path):
    configure_persistent_store(str(tmp_path / "webhook-delivery.sqlite3"))
    configure_object_storage(str(tmp_path / "webhook-delivery-objects"))

    deliveries: list[dict[str, object]] = []

    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            deliveries.append({
                "path": self.path,
                "headers": dict(self.headers),
                "body": body,
            })
            self.send_response(204)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Receiver)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        email = f"wh-delivery-{uuid4().hex}@gameuiagent.dev"
        client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "WH User"})
        login = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        create_resp = client.post("/api/user/webhooks", headers=headers, json={
            "url": f"http://127.0.0.1:{server.server_port}/gameuiagent",
            "events": ["ai.job.completed"],
            "description": "Signed local receiver",
        })
        assert create_resp.status_code == 201
        created = create_resp.json()

        test_resp = client.post(f"/api/user/webhooks/{created['id']}/test", headers=headers)
        assert test_resp.status_code == 200
        assert test_resp.json()["status"] == "test_queued"
        assert test_resp.json()["delivery"]["status"] == "succeeded"

        assert len(deliveries) == 1
        delivery = deliveries[0]
        body = delivery["body"]
        delivery_headers = delivery["headers"]
        assert delivery["path"] == "/gameuiagent"
        assert delivery_headers["X-GameUIAgent-Event"] == "ai.job.completed"
        assert delivery_headers["X-GameUIAgent-Delivery"].startswith("whd_")
        timestamp = delivery_headers["X-GameUIAgent-Timestamp"]
        expected_signature = "sha256=" + hmac.new(
            created["secret"].encode("utf-8"),
            f"{timestamp}.".encode("utf-8") + body,
            hashlib.sha256,
        ).hexdigest()
        assert delivery_headers["X-GameUIAgent-Signature"] == expected_signature
        payload = json.loads(body)
        assert payload["type"] == "ai.job.completed"
        assert payload["webhook_id"] == created["id"]
        assert payload["data"]["test"] is True

        listed = client.get("/api/user/webhooks", headers=headers).json()["webhooks"][0]
        assert listed["success_count"] == 1
        assert listed["failure_count"] == 0
        assert listed["last_sent_at"] is not None

        delivery_log = client.get(f"/api/user/webhooks/{created['id']}/deliveries", headers=headers)
        assert delivery_log.status_code == 200
        logged = delivery_log.json()["deliveries"][0]
        assert logged["event"] == "ai.job.completed"
        assert logged["status"] == "succeeded"
        assert logged["response_status"] == 204
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_export_completed_event_delivers_to_subscribed_webhook(tmp_path):
    configure_persistent_store(str(tmp_path / "webhook-export.sqlite3"))
    configure_object_storage(str(tmp_path / "webhook-export-objects"))

    deliveries: list[dict[str, object]] = []

    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            deliveries.append({
                "headers": dict(self.headers),
                "body": body,
            })
            self.send_response(200)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Receiver)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        email = f"wh-export-{uuid4().hex}@gameuiagent.dev"
        client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "Export WH"})
        login = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        project = client.post("/api/projects", headers=headers, json={
            "name": "Webhook Export",
            "target_engine": "unity",
            "canvas": {"width": 1920, "height": 1080},
        }).json()

        create_resp = client.post("/api/user/webhooks", headers=headers, json={
            "url": f"http://127.0.0.1:{server.server_port}/export",
            "events": ["export.completed"],
            "description": "Export receiver",
        })
        assert create_resp.status_code == 201
        created = create_resp.json()

        export_resp = client.post(
            f"/api/projects/{project['id']}/studio/export-wizard",
            headers=headers,
            json={"target_engine": "unity"},
        )
        assert export_resp.status_code == 200
        export = export_resp.json()["export"]

        assert len(deliveries) == 1
        delivery = deliveries[0]
        assert delivery["headers"]["X-GameUIAgent-Event"] == "export.completed"
        payload = json.loads(delivery["body"])
        assert payload["type"] == "export.completed"
        assert payload["data"]["project_id"] == project["id"]
        assert payload["data"]["export_id"] == export["id"]
        assert payload["data"]["target_engine"] == "unity"
        assert payload["webhook_id"] == created["id"]

        listed = client.get("/api/user/webhooks", headers=headers).json()["webhooks"][0]
        assert listed["success_count"] == 1
        assert listed["failure_count"] == 0
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_webhooks_validation(tmp_path):
    configure_persistent_store(str(tmp_path / "whval.sqlite3"))
    configure_object_storage(str(tmp_path / "whval-objects"))

    email = f"whval-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "secret-pass", "name": "User"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret-pass"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    bad_url = client.post("/api/user/webhooks", headers=headers, json={
        "url": "ftp://bad.url",
        "events": ["ai.job.completed"],
    })
    assert bad_url.status_code == 400

    bad_event = client.post("/api/user/webhooks", headers=headers, json={
        "url": "https://example.com/hook",
        "events": ["nonexistent.event"],
    })
    assert bad_event.status_code == 400

    not_found = client.get("/api/user/webhooks/wh_nonexistent", headers=headers)
    assert not_found.status_code == 404


def test_end_to_end_register_project_ai_export(tmp_path):
    """End-to-end flow: register -> create project -> AI text_to_image -> export"""
    configure_persistent_store(str(tmp_path / "e2e.sqlite3"))
    configure_object_storage(str(tmp_path / "e2e-objects"))

    email = f"e2e-{uuid4().hex}@gameuiagent.dev"
    password = "SecurePass123!"

    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "email": email, "password": password, "name": "E2E User"
    })
    assert reg_resp.status_code == 201

    # 2. Login
    login_resp = client.post("/api/auth/login", json={
        "email": email, "password": password
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get current user
    me_resp = client.get("/api/user/me", headers=headers)
    assert me_resp.status_code == 200
    me = me_resp.json()
    assert me["email"] == email
    assert me["name"] == "E2E User"
    assert me["id"]

    # 4. Update user name
    update_resp = client.patch("/api/user/me", headers=headers, json={
        "name": "Updated Name"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Name"

    # 5. Create project
    proj_resp = client.post("/api/projects", headers=headers, json={
        "name": "My Game UI",
        "target_engine": "unity",
        "canvas": {"width": 1920, "height": 1080},
    })
    assert proj_resp.status_code == 201
    project = proj_resp.json()
    assert project["name"] == "My Game UI"
    assert project["target_engine"] == "unity"
    project_id = project["id"]

    # 6. List projects
    list_resp = client.get("/api/projects", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["projects"]) >= 1

    # 7. Get billing
    billing_resp = client.get("/api/user/billing", headers=headers)
    assert billing_resp.status_code == 200
    billing = billing_resp.json()
    assert "credits" in billing
    assert billing["credits"]["daily_free"] > 0

    # 8. List API keys (empty)
    keys_resp = client.get("/api/user/api-keys", headers=headers)
    assert keys_resp.status_code == 200
    assert "api_keys" in keys_resp.json()

    # 9. Create API key
    key_resp = client.post("/api/user/api-keys", headers=headers, json={"name": "E2E Key"})
    assert key_resp.status_code == 201
    assert key_resp.json()["api_key"]

    # 10. List webhooks (empty)
    hooks_resp = client.get("/api/user/webhooks", headers=headers)
    assert hooks_resp.status_code == 200
    assert hooks_resp.json()["webhooks"] == []

    # 11. Get project studio state
    studio_resp = client.get(f"/api/projects/{project_id}/studio", headers=headers)
    assert studio_resp.status_code == 200
    studio = studio_resp.json()
    assert studio["project_id"] == project_id
    assert "timeline" in studio
    assert "action_dock" in studio
    assert "export_wizard" in studio

    # 12. Default Studio selected asset must be a real, sliceable asset.
    selected_asset_id = studio["active_selection"]["selected_asset_id"]
    segmentation_resp = client.post(
        f"/api/projects/{project_id}/segmentations",
        headers=headers,
        json={"asset_id": selected_asset_id},
    )
    assert segmentation_resp.status_code == 201
    assert segmentation_resp.json()["source_asset_id"] == selected_asset_id

    # 13. Create team
    team_resp = client.post("/api/teams", headers=headers, json={"name": "E2E Team"})
    assert team_resp.status_code == 201
    team = team_resp.json()
    assert team["name"] == "E2E Team"
    assert len(team["members"]) == 1
    assert team["members"][0]["role"] == "owner"

    # 14. List teams
    teams_resp = client.get("/api/teams", headers=headers)
    assert teams_resp.status_code == 200
    assert len(teams_resp.json()["teams"]) >= 1

    # 15. Get usage
    usage_resp = client.get("/api/user/usage", headers=headers)
    assert usage_resp.status_code == 200
    assert "events" in usage_resp.json()


def test_production_readiness_and_metrics(tmp_path):
    configure_persistent_store(str(tmp_path / "readiness.sqlite3"))
    configure_object_storage(str(tmp_path / "readiness-objects"))

    # Readiness check
    ready = client.get("/api/system/production-readiness")
    assert ready.status_code == 200
    data = ready.json()
    assert "status" in data
    assert "storage" in data
    assert data["storage"]["driver"] == "sqlite"
    assert data["storage"]["durable"] is True

    # System metrics (requires auth)
    email = f"metrics-{uuid4().hex}@gameuiagent.dev"
    client.post("/api/auth/register", json={"email": email, "password": "pass1234", "name": "Metrics"})
    login = client.post("/api/auth/login", json={"email": email, "password": "pass1234"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    metrics = client.get("/api/system/metrics", headers=headers)
    assert metrics.status_code == 200
    data = metrics.json()
    assert "queue" in data
    assert "assets" in data
    assert "audits" in data
    assert "exports" in data
