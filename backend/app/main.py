from __future__ import annotations

from hashlib import pbkdf2_hmac
from hmac import compare_digest
from re import sub
from secrets import token_hex
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
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


class StudioExportWizardRequest(BaseModel):
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
    width: int = 512
    height: int = 512


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


class PluginAuthRequest(BaseModel):
    token: str
    engine: str
    engine_version: str
    plugin_version: str
    device_name: str


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
    "plugin_devices": {},
    "billing_accounts": {},
    "usage_events": {},
    "rate_limits": {},
    "studio_states": {},
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
    store["billing_accounts"][user["id"]] = create_billing_account(user)
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


@app.get("/api/projects/{project_id}/studio")
def get_studio_state(project_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    project = require_project(project_id, user)
    return ensure_studio_state(project)


@app.post("/api/projects/{project_id}/studio/corrections/{correction_id}/apply")
def apply_studio_correction(
    project_id: str,
    correction_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    studio = ensure_studio_state(project)
    correction = next(
        (
            item
            for item in studio["segmentation_corrections"]
            if item["id"] == correction_id
        ),
        None,
    )
    if not correction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Correction not found")
    correction["status"] = "applied"
    studio["active_selection"]["selected_layer_id"] = correction["target_layer_id"]
    updated_node = apply_correction_to_latest_ir(project, correction)
    studio["timeline"] = build_studio_timeline(project)
    return {
        "status": "applied",
        "correction": correction,
        "updated_node": updated_node,
        "studio": studio,
    }


@app.post("/api/projects/{project_id}/studio/export-wizard")
def preview_studio_export_wizard(
    project_id: str,
    payload: StudioExportWizardRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    studio = ensure_studio_state(project)
    ir = latest_project_ir(project) or build_demo_ir(project)
    package = build_export_package(project, ir, payload.target_engine)
    export = {
        "id": make_id("exp"),
        "project_id": project["id"],
        "target_engine": payload.target_engine,
        "status": "ready",
        "package": package,
    }
    export["package"]["manifest"]["package_id"] = export["id"]
    export["package"]["manifest"]["download_url"] = f"/api/plugin/exports/{export['id']}/download"
    store["exports"][export["id"]] = export
    studio["export_wizard"]["target_engine"] = payload.target_engine
    for step in studio["export_wizard"]["steps"]:
        if step["id"] in {"select-engine", "validate-ir"}:
            step["status"] = "complete"
        elif step["id"] == "build-package":
            step["status"] = "complete"
        elif step["id"] == "sync-plugin":
            step["status"] = "active"
    studio["timeline"] = build_studio_timeline(project)
    return {
        "project_id": project["id"],
        "studio": studio,
        "export": export,
        "export_preview": {
            "target_engine": payload.target_engine,
            "entry": package["manifest"]["entry"]["path"],
            "package_kind": package["kind"],
            "steps": package["manifest"].get("unity_import_plan", package["manifest"].get("import_plan", {})).get("steps", []),
        },
    }


@app.get("/api/plugin/export-jobs")
def plugin_export_jobs(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    owned_projects = {
        project["id"] for project in store["projects"].values() if project["owner_id"] == user["id"]
    }
    jobs = [export for export in store["exports"].values() if export["project_id"] in owned_projects]
    return {"jobs": jobs}


@app.post("/api/plugin/auth")
def plugin_auth(payload: PluginAuthRequest) -> dict[str, Any]:
    email = store["tokens"].get(payload.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid plugin token")
    user = store["users"][email]
    access_token = make_id("ptok")
    device = {
        "id": make_id("dev"),
        "user_id": user["id"],
        "engine": payload.engine,
        "engine_version": payload.engine_version,
        "plugin_version": payload.plugin_version,
        "device_name": payload.device_name,
    }
    store["plugin_devices"][device["id"]] = device
    store["tokens"][access_token] = email
    return {
        "access_token": access_token,
        "expires_in": 3600,
        "user": {"id": user["id"], "name": user["name"]},
        "device": device,
    }


@app.get("/api/plugin/projects")
def plugin_projects(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {
        "projects": [
            {
                "id": project["id"],
                "name": project["name"],
                "target_engines": supported_plugin_engines(),
                "updated_at": "2026-06-29T00:00:00Z",
            }
            for project in store["projects"].values()
            if project["owner_id"] == user["id"]
        ]
    }


@app.get("/api/plugin/projects/{project_id}/exports")
def plugin_project_exports(
    project_id: str,
    engine: str | None = None,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    exports = [
        {
            "id": export["id"],
            "engine": export["package"]["manifest"]["engine"],
            "engine_version": export["package"]["manifest"].get("engine_version", ""),
            "status": export["status"],
            "name": f"{project['name']} {export['package']['manifest']['engine']}",
            "entry": export["package"]["manifest"]["entry"],
            "manifest_url": f"/api/plugin/exports/{export['id']}/manifest",
            "download_url": f"/api/plugin/exports/{export['id']}/download",
        }
        for export in store["exports"].values()
        if export["project_id"] == project["id"]
        and (engine is None or export["package"]["manifest"]["engine"] == engine)
    ]
    return {"exports": exports}


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
    if payload.engine != export["package"]["manifest"]["engine"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Import log engine does not match export engine",
        )
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


@app.get("/api/plugin/exports/{export_id}/import-logs")
def plugin_export_import_logs(export_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    export = require_export(export_id, user)
    logs = [
        log
        for log in store["import_logs"].values()
        if log["export_id"] == export["id"]
    ]
    summary: dict[str, int] = {}
    for log in logs:
        for key, value in log["summary"].items():
            summary[key] = summary.get(key, 0) + value
    return {
        "export_id": export["id"],
        "engine": export["package"]["manifest"]["engine"],
        "summary": summary,
        "latest_log": logs[-1] if logs else None,
        "logs": logs,
    }


@app.post("/api/user/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    raw_key = f"guk_{token_hex(24)}"
    api_key = {"id": make_id("key"), "name": payload.name, "user": user}
    store["api_keys"][raw_key] = api_key
    return {"id": api_key["id"], "name": payload.name, "api_key": raw_key}


@app.get("/api/user/billing")
def get_billing(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    account = billing_account_for(user)
    return format_billing_account(account)


@app.get("/api/user/usage")
def get_usage(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    events = [
        event for event in store["usage_events"].values() if event["user_id"] == user["id"]
    ]
    return {"events": list(reversed(events))}


@app.post("/api/ai/services/super-matting/cost")
def estimate_super_matting_cost(
    payload: MattingCostRequest,
    response: Response,
    api_user: dict[str, Any] = Depends(current_api_user),
) -> dict[str, Any]:
    apply_rate_limit_headers(api_user, response)
    estimated_credits = estimate_matting_credits(payload.width, payload.height)
    return {
        "service": "super-matting",
        "estimated_credits": estimated_credits,
        "input": {
            "image_url": payload.image_url,
            "output": payload.output,
            "width": payload.width,
            "height": payload.height,
        },
    }


@app.post("/api/ai/services/super-matting/execute", status_code=status.HTTP_201_CREATED)
def execute_super_matting(
    payload: MattingExecuteRequest,
    response: Response,
    user: dict[str, Any] = Depends(current_api_user),
) -> dict[str, Any]:
    apply_rate_limit_headers(user, response)
    cost_credits = estimate_matting_credits(payload.width, payload.height)
    usage = deduct_credits(user, "super-matting", cost_credits)
    task = {
        "task_id": make_id("ait"),
        "user_id": user["id"],
        "service": "super-matting",
        "status": "queued",
        "progress": 0,
        "cost_credits": cost_credits,
        "input": {
            "image_url": payload.image_url,
            "output": payload.output,
            "width": payload.width,
            "height": payload.height,
        },
        "webhook": {
            "url": payload.webhook_url,
            "signature_algorithm": "HMAC-SHA256",
        },
        "billing_usage": usage,
    }
    store["developer_tasks"][task["task_id"]] = task
    usage["task_id"] = task["task_id"]
    store["usage_events"][usage["id"]] = usage
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


def latest_project_ir(project: dict[str, Any]) -> dict[str, Any] | None:
    project_irs = [ir for ir in store["irs"].values() if ir["project_id"] == project["id"]]
    return project_irs[-1] if project_irs else None


def build_studio_timeline(project: dict[str, Any], target_engine: str | None = None) -> list[dict[str, Any]]:
    engine = target_engine or latest_project_export_engine(project) or project["target_engine"]
    jobs = [job for job in store["jobs"].values() if job["project_id"] == project["id"]]
    ir_ready = latest_project_ir(project) is not None
    export_ready = any(export["project_id"] == project["id"] for export in store["exports"].values())
    return [
        {
            "kind": "text_to_image",
            "status": "succeeded" if jobs else "queued",
            "progress": 100 if jobs else 0,
        },
        {
            "kind": "ui_segmentation",
            "status": "succeeded" if ir_ready else "queued",
            "progress": 100 if ir_ready else 0,
        },
        {
            "kind": f"{engine}_export",
            "status": "succeeded" if export_ready else "queued",
            "progress": 100 if export_ready else 0,
        },
        {
            "kind": "plugin_import",
            "status": "ready" if export_ready else "queued",
            "progress": 0,
        },
    ]


def latest_project_export_engine(project: dict[str, Any]) -> str | None:
    exports = [export for export in store["exports"].values() if export["project_id"] == project["id"]]
    return exports[-1]["target_engine"] if exports else None


def apply_correction_to_latest_ir(project: dict[str, Any], correction: dict[str, Any]) -> dict[str, Any]:
    ir = latest_project_ir(project)
    if not ir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IR not found")
    node = next(
        (item for item in ir["nodes"] if item["id"] == correction["target_layer_id"]),
        None,
    )
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    rect = node["rect"]
    node["rect"] = {
        "x": rect["x"] - 12,
        "y": rect["y"] - 12,
        "width": rect["width"] + 24,
        "height": rect["height"] + 24,
    }
    node["correction_status"] = "applied"
    node["correction_id"] = correction["id"]
    return node


def ensure_studio_state(project: dict[str, Any]) -> dict[str, Any]:
    studio = store["studio_states"].get(project["id"])
    if studio:
        studio["timeline"] = build_studio_timeline(project, studio["export_wizard"]["target_engine"])
        return studio
    ir = latest_project_ir(project) or build_demo_ir(project)
    button_node = next((node for node in ir["nodes"] if node["type"] == "button"), ir["nodes"][0])
    studio = {
        "project_id": project["id"],
        "active_selection": {
            "selected_layer_id": button_node["id"],
            "selected_asset_id": "asset_slice",
            "active_task_id": "timeline_slice",
        },
        "action_dock": [
            {"id": "regenerate", "title": "Regenerate", "shortcut": "R"},
            {"id": "open-slice-editor", "title": "Open Slice Editor", "shortcut": "S"},
            {"id": "apply-correction", "title": "Apply Correction", "shortcut": "A"},
            {"id": "export-package", "title": "Export Package", "shortcut": "E"},
        ],
        "timeline": build_studio_timeline(project, project["target_engine"]),
        "segmentation_corrections": [
            {
                "id": "correction_button_bounds",
                "target_layer_id": button_node["id"],
                "title": f"{button_node['name']} bounds",
                "change": "Resize hit box to match nine-slice button art.",
                "confidence": 0.92,
                "status": "pending",
            },
            {
                "id": "correction_label_binding",
                "target_layer_id": "title_text",
                "title": "Text binding",
                "change": "Attach text node to the selected button hierarchy.",
                "confidence": 0.87,
                "status": "pending",
            },
        ],
        "export_wizard": {
            "target_engine": project["target_engine"],
            "steps": [
                {"id": "select-engine", "title": "Select Target Engine", "status": "complete"},
                {"id": "validate-ir", "title": "Validate Asset IR", "status": "active"},
                {"id": "build-package", "title": "Build Engine Package", "status": "pending"},
                {"id": "sync-plugin", "title": "Sync Through Plugin", "status": "pending"},
            ],
        },
    }
    store["studio_states"][project["id"]] = studio
    return studio


def build_demo_ir(project: dict[str, Any]) -> dict[str, Any]:
    width = project["canvas"]["width"]
    height = project["canvas"]["height"]
    return {
        "id": make_id("ir"),
        "project_id": project["id"],
        "version": "0.1.0",
        "engine_targets": ["unity", "cocos", "godot", "unreal"],
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
        "engine_targets": ["unity", "cocos", "godot", "unreal"],
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
    if target_engine in {"cocos", "cocos3"}:
        files = [
            f"Cocos3/assets/vberai/textures/{slug}_atlas.png",
            f"Cocos3/assets/vberai/prefabs/{slug}.prefab",
            f"Cocos3/assets/vberai/scenes/{slug}.scene",
            f"Cocos3/assets/vberai/metadata/{slug}.json",
        ]
        manifest = build_engine_manifest(
            project=project,
            ir=ir,
            engine="cocos3",
            engine_version="3.8.6+",
            entry_type="prefab",
            entry_path=files[1],
            files=files,
            import_plan={
                "root": "Cocos3/assets/vberai",
                "steps": [
                    "copy_textures",
                    "create_sprite_frames",
                    "create_prefab",
                    "create_scene",
                    "write_import_log",
                ],
            },
        )
        return {"kind": "cocos3_package", "files": files, "manifest": manifest}
    if target_engine == "cocos2":
        files = [
            f"Cocos2/assets/resources/vberai/textures/{slug}_atlas.png",
            f"Cocos2/assets/resources/vberai/prefabs/{slug}.prefab",
            f"Cocos2/assets/resources/vberai/metadata/{slug}.json",
        ]
        manifest = build_engine_manifest(
            project=project,
            ir=ir,
            engine="cocos2",
            engine_version="2.4.x+",
            entry_type="prefab",
            entry_path=files[1],
            files=files,
            import_plan={
                "root": "Cocos2/assets/resources/vberai",
                "steps": ["copy_textures", "create_sprite_frames", "create_prefab", "write_import_log"],
            },
        )
        return {"kind": "cocos2_package", "files": files, "manifest": manifest}
    if target_engine == "godot":
        files = [
            f"Godot/vberai/textures/{slug}_atlas.png",
            f"Godot/vberai/scenes/{slug}.tscn",
            f"Godot/vberai/metadata/{slug}.json",
        ]
        manifest = build_engine_manifest(
            project=project,
            ir=ir,
            engine="godot",
            engine_version="4.x",
            entry_type="scene",
            entry_path=files[1],
            files=files,
            import_plan={
                "root": "Godot/vberai",
                "steps": ["copy_textures", "write_tscn_scene", "refresh_filesystem", "write_import_log"],
            },
        )
        return {"kind": "godot_package", "files": files, "manifest": manifest}
    if target_engine == "unreal":
        files = [
            f"Unreal/Content/GameUIAgent/Textures/T_{slug}_Atlas.uasset",
            f"Unreal/Content/GameUIAgent/Widgets/WBP_{slug}.uasset",
            f"Unreal/Content/GameUIAgent/Metadata/{slug}.json",
        ]
        manifest = build_engine_manifest(
            project=project,
            ir=ir,
            engine="unreal",
            engine_version="5.3+",
            entry_type="umg_widget_blueprint",
            entry_path=files[1],
            files=files,
            import_plan={
                "root": "Unreal/Content/GameUIAgent",
                "steps": [
                    "copy_textures",
                    "create_texture_assets",
                    "create_umg_widget_blueprint",
                    "bind_slate_slots",
                    "write_import_log",
                ],
            },
        )
        return {"kind": "unreal_package", "files": files, "manifest": manifest}
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


def build_engine_manifest(
    project: dict[str, Any],
    ir: dict[str, Any],
    engine: str,
    engine_version: str,
    entry_type: str,
    entry_path: str,
    files: list[str],
    import_plan: dict[str, Any],
) -> dict[str, Any]:
    return {
        "package_id": "",
        "project_id": project["id"],
        "ir_id": ir["id"],
        "engine": engine,
        "engine_version": engine_version,
        "entry": {"type": entry_type, "path": entry_path},
        "download_url": "",
        "checksum": f"sha256:{engine}-{safe_slug(project['name']).lower()}",
        "assets": [{"path": file_path, "kind": engine_asset_kind(file_path)} for file_path in files],
        "import_plan": import_plan,
    }


def supported_plugin_engines() -> list[str]:
    return ["unity", "cocos3", "cocos2", "godot", "unreal"]


def create_billing_account(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": user["id"],
        "plan": {
            "id": "pro_trial",
            "name": "PRO Trial",
            "api_enabled": True,
            "rate_limit_per_minute": 60,
            "concurrent_ai_tasks": 8,
        },
        "credits": {
            "daily_free": 20,
            "monthly": 100,
            "purchased": 0,
        },
    }


def billing_account_for(user: dict[str, Any]) -> dict[str, Any]:
    account = store["billing_accounts"].get(user["id"])
    if not account:
        account = create_billing_account(user)
        store["billing_accounts"][user["id"]] = account
    return account


def format_billing_account(account: dict[str, Any]) -> dict[str, Any]:
    credits = account["credits"]
    return {
        "plan": account["plan"],
        "credits": {
            **credits,
            "total_available": sum(credits.values()),
            "deduction_order": ["daily_free", "monthly", "purchased"],
        },
        "rate_limit": {
            "limit": account["plan"]["rate_limit_per_minute"],
            "window_seconds": 60,
        },
    }


def estimate_matting_credits(width: int, height: int) -> int:
    max_edge = max(width, height)
    if max_edge <= 512:
        return 2
    if max_edge <= 768:
        return 5
    if max_edge <= 1024:
        return 10
    if max_edge <= 1536:
        return 15
    return 30


def deduct_credits(user: dict[str, Any], service: str, credits: int) -> dict[str, Any]:
    account = billing_account_for(user)
    balances = account["credits"]
    if sum(balances.values()) < credits:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="INSUFFICIENT_CREDITS")
    remaining = credits
    deducted = {"daily_free": 0, "monthly": 0, "purchased": 0}
    for bucket in ["daily_free", "monthly", "purchased"]:
        amount = min(balances[bucket], remaining)
        balances[bucket] -= amount
        deducted[bucket] = amount
        remaining -= amount
        if remaining == 0:
            break
    return {
        "id": make_id("use"),
        "user_id": user["id"],
        "service": service,
        "credits": credits,
        "deducted": deducted,
    }


def apply_rate_limit_headers(user: dict[str, Any], response: Response) -> None:
    account = billing_account_for(user)
    limit = account["plan"]["rate_limit_per_minute"]
    usage = store["rate_limits"].setdefault(user["id"], 0) + 1
    store["rate_limits"][user["id"]] = usage
    remaining = max(limit - usage, 0)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = "60"
    if usage > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT_EXCEEDED")


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


def engine_asset_kind(file_path: str) -> str:
    normalized = file_path.lower()
    if "/textures/" in normalized:
        return "texture"
    if "/prefabs/" in normalized:
        return "prefab"
    if "/scenes/" in normalized:
        return "scene"
    return "metadata"


def matching_layout_node(snapshot: dict[str, Any], sprite: dict[str, Any]) -> dict[str, Any]:
    nodes = snapshot["layout"].get("nodes", [])
    if not nodes:
        return {}
    role = sprite.get("role", "").lower()
    for node in nodes:
        if role and role in node.get("path", "").lower():
            return node
    return nodes[0]
