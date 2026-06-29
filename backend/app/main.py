from __future__ import annotations

from hashlib import pbkdf2_hmac
from hmac import compare_digest
from re import sub
from secrets import token_hex
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field


app = FastAPI(title="GameUIAgent API", version="0.1.0")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProjectRequest(BaseModel):
    name: str
    target_engine: str
    canvas: dict[str, int]


class AiJobRequest(BaseModel):
    kind: str
    prompt: str
    style: str | None = None
    size: str = "landscape_16_9"


class SegmentationRequest(BaseModel):
    asset_id: str


class ExportRequest(BaseModel):
    ir_id: str
    target_engine: str


class EngineSnapshotRequest(BaseModel):
    engine: str
    source: str
    layout: dict[str, Any]
    sprites: list[dict[str, Any]]


class RestyleRequest(BaseModel):
    style_prompt: str
    preserve_layout: bool = True
    replacement_strategy: str = "theme_variant"
    theme_name: str


class ProfessionalLayer(BaseModel):
    id: str
    name: str
    kind: str
    rect: dict[str, int]
    text: str | None = None
    component_key: str | None = None
    auto_layout: dict[str, Any] | None = None


class ProfessionalImportRequest(BaseModel):
    source_type: str
    file_name: str
    layers: list[ProfessionalLayer]
    frame_id: str | None = None


class ApiKeyRequest(BaseModel):
    name: str


class MattingCostRequest(BaseModel):
    image_url: str
    output: str = "alpha_png"


class MattingExecuteRequest(MattingCostRequest):
    webhook_url: str | None = None


class PluginImportLogRequest(BaseModel):
    export_id: str
    engine: str
    status: str
    plugin_version: str
    engine_version: str
    duration_ms: int
    summary: dict[str, int]
    logs: list[dict[str, str]]


store: dict[str, Any] = {
    "users": {},
    "tokens": {},
    "projects": {},
    "assets": {},
    "jobs": {},
    "irs": {},
    "exports": {},
    "snapshots": {},
    "imports": {},
    "api_keys": {},
    "developer_tasks": {},
    "import_logs": {},
}


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def hash_password(password: str) -> str:
    iterations = 120_000
    salt = token_hex(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def current_user(authorization: str = Header(default="")) -> dict[str, Any]:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token not in store["tokens"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return store["users"][store["tokens"][token]]


def current_api_user(x_api_key: str = Header(default="", alias="X-API-Key")) -> dict[str, Any]:
    api_key = store["api_keys"].get(x_api_key)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key["user"]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/marketing/capabilities")
def marketing_capabilities() -> dict[str, Any]:
    capabilities = [
        ("ai-studio", "AI Studio", "Web canvas for game UI production."),
        ("text-to-image", "Text to Image", "Generate game UI and art from prompts."),
        ("image-to-image", "Image to Image", "Create style and layout variants from references."),
        ("inpainting", "Inpainting", "Regenerate selected regions."),
        ("matting", "AI Super Matting", "Export transparent PNG assets."),
        ("upscale", "Upscale", "Improve production asset resolution."),
        ("ui-slicing", "UI Slicing", "Detect UI elements and build editable layer trees."),
        ("unity-export", "Unity Export", "Export sprites, prefabs, scenes and manifests."),
        ("cocos-export", "Cocos Export", "Export Cocos 2.x/3.x prefabs and scenes."),
        ("godot-export", "Godot Export", "Export Godot 4 control scenes."),
        ("engine-mcp", "Engine MCP", "Connect editor plugins with platform automation."),
        ("professional-import", "PSD / PSB / Figma Import", "Preserve professional design layers."),
        ("developer-api", "Developer API", "API keys, webhook, polling, cancellation and cost estimates."),
    ]
    return {
        "capabilities": [
            {"id": item_id, "title": title, "description": description}
            for item_id, title, description in capabilities
        ]
    }


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> dict[str, Any]:
    if payload.email in store["users"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = {
        "id": make_id("usr"),
        "email": payload.email,
        "name": payload.name,
        "password_hash": hash_password(payload.password),
    }
    store["users"][payload.email] = user
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, str]:
    user = store["users"].get(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = make_id("tok")
    store["tokens"][token] = payload.email
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/projects", status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    project = {
        "id": make_id("prj"),
        "owner_id": user["id"],
        "name": payload.name,
        "target_engine": payload.target_engine,
        "canvas": payload.canvas,
        "status": "active",
    }
    store["projects"][project["id"]] = project
    return project


@app.get("/api/projects")
def list_projects(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "projects": [
            project for project in store["projects"].values() if project["owner_id"] == user["id"]
        ]
    }


@app.post("/api/projects/{project_id}/ai/jobs", status_code=status.HTTP_201_CREATED)
def create_ai_job(
    project_id: str,
    payload: AiJobRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    asset = {
        "id": make_id("ast"),
        "project_id": project["id"],
        "type": "generated_image",
        "name": f"{project['name']} generated concept",
        "prompt": payload.prompt,
        "url": f"/generated/{project['id']}/{payload.kind}.png",
        "size": payload.size,
    }
    store["assets"][asset["id"]] = asset
    job = {
        "id": make_id("job"),
        "project_id": project["id"],
        "kind": payload.kind,
        "prompt": payload.prompt,
        "style": payload.style,
        "status": "succeeded",
        "progress": 100,
        "result_asset": asset,
    }
    store["jobs"][job["id"]] = job
    return job


@app.post("/api/projects/{project_id}/segmentations", status_code=status.HTTP_201_CREATED)
def create_segmentation(
    project_id: str,
    payload: SegmentationRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    asset = store["assets"].get(payload.asset_id)
    if not asset or asset["project_id"] != project["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    ir = build_demo_ir(project)
    store["irs"][ir["id"]] = ir
    return {"id": make_id("seg"), "project_id": project["id"], "source_asset_id": payload.asset_id, "ir": ir}


@app.post("/api/projects/{project_id}/imports/professional", status_code=status.HTTP_201_CREATED)
def create_professional_import(
    project_id: str,
    payload: ProfessionalImportRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    if payload.source_type not in {"psd", "psb", "figma"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported source type")
    design_document = build_design_document(project, payload)
    ir = build_ir_from_design_document(project, design_document)
    store["irs"][ir["id"]] = ir
    imported = {
        "id": make_id("imp"),
        "project_id": project["id"],
        "design_document": design_document,
        "ir": ir,
    }
    store["imports"][imported["id"]] = imported
    return imported


@app.post("/api/projects/{project_id}/exports", status_code=status.HTTP_201_CREATED)
def create_export(
    project_id: str,
    payload: ExportRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    ir = store["irs"].get(payload.ir_id)
    if not ir or ir["project_id"] != project["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IR not found")
    export = {
        "id": make_id("exp"),
        "project_id": project["id"],
        "target_engine": payload.target_engine,
        "status": "ready",
        "package": build_export_package(project, ir, payload.target_engine),
    }
    export["package"]["manifest"]["package_id"] = export["id"]
    export["package"]["manifest"]["download_url"] = f"/api/plugin/exports/{export['id']}/download"
    store["exports"][export["id"]] = export
    return export


@app.get("/api/plugin/export-jobs")
def plugin_export_jobs(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    owned_projects = {
        project["id"] for project in store["projects"].values() if project["owner_id"] == user["id"]
    }
    jobs = [export for export in store["exports"].values() if export["project_id"] in owned_projects]
    return {"jobs": jobs}


@app.get("/api/plugin/exports/{export_id}/manifest")
def plugin_export_manifest(export_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    export = require_export(export_id, user)
    return export["package"]["manifest"]


@app.get("/api/plugin/exports/{export_id}/download")
def plugin_export_download(export_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    export = require_export(export_id, user)
    return {
        "content_type": "application/zip",
        "export_id": export["id"],
        "manifest": export["package"]["manifest"],
        "files": export["package"]["files"],
        "checksum": export["package"]["manifest"]["checksum"],
    }


@app.post("/api/plugin/import-logs", status_code=status.HTTP_201_CREATED)
def plugin_import_log(
    payload: PluginImportLogRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    export = require_export(payload.export_id, user)
    log = {
        "id": make_id("ilog"),
        "export_id": export["id"],
        "engine": payload.engine,
        "status": payload.status,
        "plugin_version": payload.plugin_version,
        "engine_version": payload.engine_version,
        "duration_ms": payload.duration_ms,
        "summary": payload.summary,
        "logs": payload.logs,
    }
    store["import_logs"][log["id"]] = log
    export["last_import_log_id"] = log["id"]
    return log


@app.post("/api/user/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    raw_key = f"guk_{token_hex(24)}"
    api_key = {"id": make_id("key"), "name": payload.name, "user": user}
    store["api_keys"][raw_key] = api_key
    return {"id": api_key["id"], "name": payload.name, "api_key": raw_key}


@app.post("/api/ai/services/super-matting/cost")
def estimate_super_matting_cost(
    payload: MattingCostRequest,
    _: dict[str, Any] = Depends(current_api_user),
) -> dict[str, Any]:
    return {
        "service": "super-matting",
        "estimated_credits": 2,
        "input": {"image_url": payload.image_url, "output": payload.output},
    }


@app.post("/api/ai/services/super-matting/execute", status_code=status.HTTP_201_CREATED)
def execute_super_matting(
    payload: MattingExecuteRequest,
    user: dict[str, Any] = Depends(current_api_user),
) -> dict[str, Any]:
    task = {
        "task_id": make_id("ait"),
        "user_id": user["id"],
        "service": "super-matting",
        "status": "queued",
        "progress": 0,
        "cost_credits": 2,
        "input": {"image_url": payload.image_url, "output": payload.output},
        "webhook": {
            "url": payload.webhook_url,
            "signature_algorithm": "HMAC-SHA256",
        },
    }
    store["developer_tasks"][task["task_id"]] = task
    return task


@app.get("/api/ai/tasks/{task_id}")
def get_ai_task(task_id: str, user: dict[str, Any] = Depends(current_api_user)) -> dict[str, Any]:
    task = require_developer_task(task_id, user)
    return task


@app.post("/api/ai/tasks/{task_id}/cancel")
def cancel_ai_task(task_id: str, user: dict[str, Any] = Depends(current_api_user)) -> dict[str, Any]:
    task = require_developer_task(task_id, user)
    if task["status"] not in {"succeeded", "failed"}:
        task["status"] = "cancelled"
        task["progress"] = 0
    return task


@app.post("/api/projects/{project_id}/engine-snapshots", status_code=status.HTTP_201_CREATED)
def create_engine_snapshot(
    project_id: str,
    payload: EngineSnapshotRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    snapshot = {
        "id": make_id("snp"),
        "project_id": project["id"],
        "engine": payload.engine,
        "source": payload.source,
        "layout": payload.layout,
        "sprites": payload.sprites,
    }
    store["snapshots"][snapshot["id"]] = snapshot
    return snapshot


@app.post("/api/plugin/engine-snapshots/{snapshot_id}/restyle", status_code=status.HTTP_201_CREATED)
def restyle_engine_snapshot(
    snapshot_id: str,
    payload: RestyleRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    snapshot = store["snapshots"].get(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
    project = require_project(snapshot["project_id"], user)
    preserved_bindings = [
        binding
        for node in snapshot["layout"].get("nodes", [])
        for binding in node.get("bindings", [])
    ]
    manifest = {
        "project_id": project["id"],
        "strategy": payload.replacement_strategy,
        "theme_name": payload.theme_name,
        "preserve_layout": payload.preserve_layout,
        "layout_policy": "preserve_rect_transform",
        "preserved_bindings": preserved_bindings,
        "replacements": [
            {
                "source": sprite["path"],
                "target": sprite["path"].replace(".png", f".{payload.theme_name}.png"),
                "role": sprite.get("role", "image"),
                "node_path": matching_layout_node(snapshot, sprite).get("path"),
                "rect": matching_layout_node(snapshot, sprite).get("rect"),
            }
            for sprite in snapshot["sprites"]
        ],
    }
    return {
        "id": make_id("rst"),
        "snapshot_id": snapshot_id,
        "status": "ready",
        "style_prompt": payload.style_prompt,
        "replacement_manifest": manifest,
    }


def require_project(project_id: str, user: dict[str, Any]) -> dict[str, Any]:
    project = store["projects"].get(project_id)
    if not project or project["owner_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def require_export(export_id: str, user: dict[str, Any]) -> dict[str, Any]:
    export = store["exports"].get(export_id)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    require_project(export["project_id"], user)
    return export


def require_developer_task(task_id: str, user: dict[str, Any]) -> dict[str, Any]:
    task = store["developer_tasks"].get(task_id)
    if not task or task["user_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def build_demo_ir(project: dict[str, Any]) -> dict[str, Any]:
    width = project["canvas"]["width"]
    height = project["canvas"]["height"]
    return {
        "id": make_id("ir"),
        "project_id": project["id"],
        "version": "0.1.0",
        "engine_targets": ["unity", "cocos", "godot"],
        "canvas": {"width": width, "height": height},
        "nodes": [
            {"id": "root", "type": "canvas", "name": project["name"], "rect": {"x": 0, "y": 0, "width": width, "height": height}},
            {"id": "panel_main", "type": "panel", "name": "Main Panel", "rect": {"x": 240, "y": 120, "width": 1440, "height": 760}},
            {"id": "button_primary", "type": "button", "name": "Primary CTA", "rect": {"x": 1320, "y": 820, "width": 280, "height": 96}},
            {"id": "icon_item", "type": "icon", "name": "Inventory Icon", "rect": {"x": 360, "y": 220, "width": 128, "height": 128}},
            {"id": "title_text", "type": "text", "name": "Screen Title", "rect": {"x": 320, "y": 150, "width": 640, "height": 72}},
        ],
    }


def build_design_document(project: dict[str, Any], payload: ProfessionalImportRequest) -> dict[str, Any]:
    return {
        "id": make_id("dld"),
        "project_id": project["id"],
        "source_type": payload.source_type,
        "file_name": payload.file_name,
        "frame_id": payload.frame_id,
        "preserved_layers": len(payload.layers),
        "layers": [layer.model_dump() for layer in payload.layers],
    }


def build_ir_from_design_document(project: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {
            "id": "root",
            "type": "canvas",
            "name": project["name"],
            "rect": {"x": 0, "y": 0, "width": project["canvas"]["width"], "height": project["canvas"]["height"]},
        }
    ]
    for layer in document["layers"]:
        node_type = layer_type_to_node_type(layer)
        node = {
            "id": layer["id"],
            "type": node_type,
            "name": layer["name"],
            "rect": layer["rect"],
            "professional_source": {
                "source_type": document["source_type"],
                "layer_id": layer["id"],
            },
        }
        if layer.get("text"):
            node["text"] = {"content": layer["text"]}
        if layer.get("component_key"):
            node["component"] = {"key": layer["component_key"]}
        if layer.get("auto_layout"):
            node["layout"] = {"auto_layout": layer["auto_layout"]}
        nodes.append(node)
    return {
        "id": make_id("ir"),
        "project_id": project["id"],
        "version": "0.1.0",
        "engine_targets": ["unity", "cocos", "godot"],
        "canvas": project["canvas"],
        "professional_source": {
            "source_type": document["source_type"],
            "file_name": document["file_name"],
            "frame_id": document["frame_id"],
            "design_document_id": document["id"],
        },
        "nodes": nodes,
    }


def layer_type_to_node_type(layer: dict[str, Any]) -> str:
    name = layer["name"].lower()
    if layer["kind"] == "text":
        return "text"
    if "button" in name:
        return "button"
    if layer["kind"] == "component":
        return "component"
    return "image"


def build_export_package(project: dict[str, Any], ir: dict[str, Any], target_engine: str) -> dict[str, Any]:
    slug = safe_slug(project["name"])
    if target_engine == "unity":
        files = [
            f"Assets/GameUIAgent/Textures/{slug}_atlas.png",
            f"Assets/GameUIAgent/Prefabs/{slug}.prefab",
            f"Assets/GameUIAgent/Scenes/{slug}.unity",
            f"Assets/GameUIAgent/Manifests/{slug}.json",
        ]
        manifest = {
            "package_id": "",
            "project_id": project["id"],
            "ir_id": ir["id"],
            "engine": "unity",
            "engine_version": "2022.3+",
            "entry": {"type": "prefab", "path": files[1]},
            "download_url": "",
            "checksum": f"sha256:{slug.lower()}",
            "assets": [{"path": file_path, "kind": unity_asset_kind(file_path)} for file_path in files],
            "unity_import_plan": {
                "root": "Assets/GameUIAgent",
                "steps": [
                    "extract_zip",
                    "import_textures_as_sprites",
                    "create_prefab",
                    "create_scene",
                    "write_import_log",
                ],
            },
        }
        return {
            "kind": "unity_package",
            "files": files,
            "manifest": manifest,
        }
    return {
        "kind": f"{target_engine}_package",
        "files": [f"exports/{target_engine}/{slug}/manifest.json"],
        "manifest": {
            "package_id": "",
            "project_id": project["id"],
            "ir_id": ir["id"],
            "engine": target_engine,
            "entry": {"type": "manifest", "path": f"exports/{target_engine}/{slug}/manifest.json"},
            "download_url": "",
            "checksum": f"sha256:{target_engine}-{slug.lower()}",
        },
    }


def safe_slug(value: str) -> str:
    words = sub(r"[^A-Za-z0-9]+", " ", value).strip().split()
    slug = "".join(word.capitalize() for word in words)
    return slug or "GameUi"


def unity_asset_kind(file_path: str) -> str:
    if "/Textures/" in file_path:
        return "texture"
    if "/Prefabs/" in file_path:
        return "prefab"
    if "/Scenes/" in file_path:
        return "scene"
    return "manifest"


def matching_layout_node(snapshot: dict[str, Any], sprite: dict[str, Any]) -> dict[str, Any]:
    nodes = snapshot["layout"].get("nodes", [])
    if not nodes:
        return {}
    role = sprite.get("role", "").lower()
    for node in nodes:
        if role and role in node.get("path", "").lower():
            return node
    return nodes[0]
