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
