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
    assert projects[0]["target_engines"] == ["unity", "cocos3", "cocos2", "godot"]

    exports_response = client.get(
        f"/api/plugin/projects/{unity_created['project']['id']}/exports?engine=unity",
        headers=plugin_headers,
    )
    assert exports_response.status_code == 200
    exports = exports_response.json()["exports"]
    assert [export["id"] for export in exports] == [unity_created["export"]["id"]]
    assert exports[0]["manifest_url"] == f"/api/plugin/exports/{unity_created['export']['id']}/manifest"


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
