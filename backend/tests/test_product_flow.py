from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app, store


client = TestClient(app)


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
    }.issubset(capabilities)


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
    assert segmentation["ir"]["engine_targets"] == ["unity", "cocos", "godot"]
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
