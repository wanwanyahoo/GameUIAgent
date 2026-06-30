from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from os import getenv
from re import sub
from secrets import token_hex
from typing import Any
from urllib.parse import quote
from uuid import uuid4
from zlib import error as ZlibError, decompress

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field

from app.object_storage import LocalObjectStorage, create_object_storage
from app.persistence import ProductionStore, create_production_store


app = FastAPI(title="GameUIAgent API", version="0.1.0")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class TeamRequest(BaseModel):
    name: str


class TeamMemberRequest(BaseModel):
    email: EmailStr
    role: str


class TeamRoleUpdateRequest(BaseModel):
    role: str


class ProjectRequest(BaseModel):
    name: str
    target_engine: str
    canvas: dict[str, int]


class AssetRequest(BaseModel):
    name: str
    type: str
    url: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    usage: str
    tags: list[str] = Field(default_factory=list)


class AssetUpdateRequest(BaseModel):
    name: str | None = None
    tags: list[str] | None = None


class AiJobRequest(BaseModel):
    kind: str
    prompt: str
    style: str | None = None
    size: str = "landscape_16_9"
    input_asset_id: str | None = None
    reference_asset_id: str | None = None
    mask_asset_id: str | None = None
    negative_prompt: str | None = None
    seed: int | None = None
    model: str | None = None
    count: int = Field(default=1, ge=1, le=4)
    execution_mode: str = "inline"


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
    parent_id: str | None = None
    group_path: list[str] | None = None
    text: str | None = None
    text_style: dict[str, Any] | None = None
    component_key: str | None = None
    auto_layout: dict[str, Any] | None = None
    constraints: dict[str, Any] | None = None
    image_ref: str | None = None
    image_asset_id: str | None = None
    image_url: str | None = None
    opacity: float | None = None
    visible: bool | None = None
    is_group: bool | None = None
    smart_object: bool | None = None


class ProfessionalImportRequest(BaseModel):
    source_type: str
    file_name: str
    layers: list[ProfessionalLayer]
    frame_id: str | None = None
    parser: str | None = None
    binary_header: dict[str, Any] | None = None


class ProfessionalImportSourceRequest(BaseModel):
    source_type: str
    asset_id: str | None = None
    figma_url: str | None = None
    frame_id: str | None = None
    parser: str = "mock-layer-parser"


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


store: ProductionStore = create_production_store()
object_storage: LocalObjectStorage = create_object_storage()
worker_token: str | None = getenv("GAMEUIAGENT_WORKER_TOKEN")
inference_provider_name = getenv("GAMEUIAGENT_INFERENCE_PROVIDER", "local-deterministic")
MAX_PNG_ALPHA_SEGMENTATION_PIXELS = 2048 * 2048
MAX_FIGMA_IMAGE_FILL_BYTES = 25 * 1024 * 1024


def configure_persistent_store(db_path: str) -> None:
    store.configure(db_path)


def configure_object_storage(root_path: str) -> None:
    object_storage.configure(root_path)


def configure_worker_token(token: str | None) -> None:
    global worker_token
    worker_token = token


def configure_inference_provider(provider_name: str) -> None:
    global inference_provider_name
    inference_provider_name = provider_name


production_store_path = getenv("GAMEUIAGENT_STORE_DB")
if production_store_path:
    configure_persistent_store(production_store_path)

production_object_store_path = getenv("GAMEUIAGENT_OBJECT_STORE_DIR")
if production_object_store_path:
    configure_object_storage(production_object_store_path)


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


def smtp_email_configured() -> bool:
    return bool(getenv("GAMEUIAGENT_SMTP_HOST") and getenv("GAMEUIAGENT_EMAIL_FROM"))


def email_delivery_provider() -> str:
    return "smtp" if smtp_email_configured() else "local-outbox"


def deliver_password_reset_email(email: str, reset_token: str) -> dict[str, Any]:
    delivery = {
        "id": make_id("eml"),
        "template": "password_reset",
        "to": email,
        "provider": email_delivery_provider(),
        "status": "queued",
        "subject": "GameUIAgent Password reset",
    }
    store["email_deliveries"][delivery["id"]] = delivery
    if not smtp_email_configured():
        return delivery
    try:
        send_smtp_email(build_password_reset_email(email, reset_token))
    except Exception:
        delivery["status"] = "failed"
        delivery["error"] = "smtp_delivery_failed"
        store.flush()
        return delivery
    delivery["status"] = "sent"
    store.flush()
    return delivery


def build_password_reset_email(email: str, reset_token: str) -> EmailMessage:
    app_url = getenv("GAMEUIAGENT_APP_URL", "https://app.gameuiagent.dev").rstrip("/")
    reset_url = f"{app_url}/reset-password?token={reset_token}"
    message = EmailMessage()
    message["To"] = email
    message["From"] = getenv("GAMEUIAGENT_EMAIL_FROM", "no-reply@gameuiagent.dev")
    message["Subject"] = "GameUIAgent Password reset"
    message.set_content(
        "Reset your GameUIAgent password with the secure link below.\n\n"
        f"{reset_url}\n\n"
        "This link expires in 15 minutes. If you did not request this, you can ignore this email."
    )
    return message


def send_smtp_email(message: EmailMessage) -> None:
    host = getenv("GAMEUIAGENT_SMTP_HOST")
    if not host:
        raise RuntimeError("SMTP host is not configured")
    port = int(getenv("GAMEUIAGENT_SMTP_PORT", "587"))
    username = getenv("GAMEUIAGENT_SMTP_USERNAME")
    password = getenv("GAMEUIAGENT_SMTP_PASSWORD")
    use_tls = getenv("GAMEUIAGENT_SMTP_TLS", "true").lower() != "false"
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def append_audit_event(
    project_id: str,
    action: str,
    actor_id: str | None,
    entity_type: str,
    entity_id: str,
    *,
    status_value: str = "succeeded",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sequence = len(store["audit_events"]) + 1
    event = {
        "id": f"aud_{sequence:012d}",
        "sequence": sequence,
        "project_id": project_id,
        "actor_id": actor_id or "system",
        "action": action,
        "status": status_value,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metadata": metadata or {},
    }
    store["audit_events"][event["id"]] = event
    return event


def project_audit_events(project: dict[str, Any]) -> list[dict[str, Any]]:
    events = [
        event
        for event in store["audit_events"].values()
        if event["project_id"] == project["id"]
    ]
    return sorted(events, key=lambda event: event["sequence"])


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


def require_worker_token(x_worker_token: str = Header(default="", alias="X-Worker-Token")) -> bool:
    if worker_token and not compare_digest(x_worker_token, worker_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker token")
    return True


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/system/production-readiness")
def production_readiness() -> dict[str, Any]:
    durable = store.db_path is not None
    object_durable = object_storage.durable
    email_configured = smtp_email_configured()
    return {
        "status": "production_foundation_ready" if durable and object_durable else "ephemeral_demo_mode",
        "storage": {
            "driver": "sqlite" if durable else "memory",
            "durable": durable,
            "ephemeral": not durable,
            "path": store.db_path,
        },
        "object_storage": {
            "driver": "local_fs" if object_durable else "unconfigured",
            "durable": object_durable,
            "ephemeral": not object_durable,
            "root": str(object_storage.root) if object_storage.root else None,
        },
        "inference": {
            "provider": inference_provider_name,
            "configured": inference_provider_configured(),
            "qwen_endpoint": qwen_inference_endpoint() if inference_provider_name == "qwen" else None,
        },
        "email": {
            "provider": "smtp" if email_configured else "local-outbox",
            "configured": email_configured,
            "from": getenv("GAMEUIAGENT_EMAIL_FROM"),
        },
        "checks": [
            "durable_store" if durable else "ephemeral_store",
            "object_storage" if object_durable else "missing_object_storage",
            "ai_job_queue",
            "worker_auth" if worker_token else "missing_worker_auth",
            "inference_provider" if inference_provider_configured() else "missing_inference_provider",
            "smtp_email" if email_configured else "missing_smtp_email",
            "audit_events",
            "salted_password_hashes",
            "project_ownership_guards",
            "engine_manifest_contracts",
        ],
    }


@app.get("/api/system/metrics")
def system_metrics(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    queue_items = list(store["ai_job_queue"].values())
    queue_by_status: dict[str, int] = {}
    for item in queue_items:
        status = item.get("status", "unknown")
        queue_by_status[status] = queue_by_status.get(status, 0) + 1

    assets = list(store["assets"].values())
    assets_by_source: dict[str, int] = {}
    for asset in assets:
        source = asset.get("source", "unknown")
        assets_by_source[source] = assets_by_source.get(source, 0) + 1

    imports = list(store["imports"].values())
    imports_by_source: dict[str, int] = {}
    for imp in imports:
        source_type = imp.get("source", imp.get("source_type", "unknown"))
        imports_by_source[source_type] = imports_by_source.get(source_type, 0) + 1

    exports = list(store["exports"].values())
    exports_by_engine: dict[str, int] = {}
    for exp in exports:
        engine = exp.get("target_engine", exp.get("engine", "unknown"))
        exports_by_engine[engine] = exports_by_engine.get(engine, 0) + 1

    emails = list(store["email_deliveries"].values())
    emails_by_status: dict[str, int] = {}
    for email in emails:
        status = email.get("status", "unknown")
        emails_by_status[status] = emails_by_status.get(status, 0) + 1

    return {
        "queue": {
            "total": len(queue_items),
            **queue_by_status,
        },
        "assets": {
            "total": len(assets),
            "by_source": assets_by_source,
        },
        "audits": {
            "total": len(store["audit_events"]),
        },
        "imports": {
            "total": len(imports),
            "by_source": imports_by_source,
        },
        "exports": {
            "total": len(exports),
            "by_engine": exports_by_engine,
        },
        "email_deliveries": {
            "total": len(emails),
            "by_status": emails_by_status,
        },
        "projects": {
            "total": len(store["projects"]),
        },
        "users": {
            "total": len(store["users"]),
        },
    }


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
        ("team-roles", "Team Roles", "Invite collaborators with owner, admin, designer, developer and viewer roles."),
        ("password-reset", "Password Reset", "Issue reset tokens and rotate salted password hashes."),
        ("docs-center", "Docs Center", "Expose onboarding, Developer API and engine plugin guides."),
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


@app.post("/api/auth/password-reset/request")
def request_password_reset(payload: PasswordResetRequest) -> dict[str, Any]:
    user = store["users"].get(payload.email)
    if not user:
        return {"status": "queued", "delivery": email_delivery_provider()}
    reset_token = make_id("rst")
    store["password_reset_tokens"][reset_token] = {"email": payload.email, "user_id": user["id"]}
    delivery = deliver_password_reset_email(payload.email, reset_token)
    return {"status": "queued", "delivery": delivery["provider"], "expires_in": 900}


@app.post("/api/auth/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirmRequest) -> dict[str, str]:
    reset = store["password_reset_tokens"].pop(payload.token, None)
    if not reset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reset token not found")
    user = store["users"].get(reset["email"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user["password_hash"] = hash_password(payload.new_password)
    store.flush()
    return {"status": "password_reset"}


@app.post("/api/teams", status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    team = {
        "id": make_id("team"),
        "name": payload.name,
        "owner_id": user["id"],
    }
    store["teams"][team["id"]] = team
    membership = create_team_membership(team, user["email"], "owner", user["id"])
    return format_team(team, [membership])


@app.get("/api/teams")
def list_teams(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    teams = []
    for team in store["teams"].values():
        members = team_memberships(team["id"])
        if any(member["email"] == user["email"] for member in members):
            teams.append(format_team(team, members))
    return {"teams": teams}


@app.post("/api/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
def invite_team_member(
    team_id: str,
    payload: TeamMemberRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    team = require_team_admin(team_id, user)
    membership = create_team_membership(team, str(payload.email), payload.role)
    return membership


@app.patch("/api/teams/{team_id}/members/{membership_id}")
def update_team_member_role(
    team_id: str,
    membership_id: str,
    payload: TeamRoleUpdateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    require_team_admin(team_id, user)
    validate_team_role(payload.role)
    membership = store["memberships"].get(membership_id)
    if not membership or membership["team_id"] != team_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    membership["role"] = payload.role
    store.flush()
    return membership


@app.get("/api/docs")
def docs_center() -> dict[str, Any]:
    return {
        "docs": [
            {
                "slug": "getting-started",
                "title": "Getting Started",
                "sections": ["Create project", "Import or generate", "Slice UI", "Export package"],
            },
            {
                "slug": "developer-api",
                "title": "Developer API",
                "sections": ["Authentication", "Cost estimate", "Execute", "Poll", "Cancel", "Webhook"],
            },
            {
                "slug": "engine-plugins",
                "title": "Engine Plugins",
                "sections": ["Plugin auth", "Project sync", "Manifest", "Download", "Import log"],
                "engines": ["Unity", "Cocos", "Godot", "Unreal"],
            },
        ]
    }


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


@app.post("/api/projects/{project_id}/assets", status_code=status.HTTP_201_CREATED)
def create_project_asset(
    project_id: str,
    payload: AssetRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    asset = build_uploaded_asset(project, payload)
    store["assets"][asset["id"]] = asset
    record_asset_version(asset, "created")
    return asset


@app.post("/api/projects/{project_id}/assets/upload", status_code=status.HTTP_201_CREATED)
async def upload_project_asset(
    project_id: str,
    name: str = Form(),
    type: str = Form(),
    width: int = Form(gt=0),
    height: int = Form(gt=0),
    usage: str = Form(),
    tags: str = Form(default=""),
    file: UploadFile = File(),
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    validate_asset_type(type)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty upload file")
    detected_dimensions = detect_uploaded_image_dimensions(content, file.content_type or "", file.filename or name)
    asset_width = detected_dimensions["width"] if detected_dimensions else width
    asset_height = detected_dimensions["height"] if detected_dimensions else height
    try:
        stored = object_storage.put(
            project["id"],
            file.filename or name,
            content,
            file.content_type or "application/octet-stream",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    asset = {
        "id": make_id("ast"),
        "project_id": project["id"],
        "type": type,
        "name": name,
        "url": f"/api/projects/{project['id']}/assets/{{asset_id}}/download",
        "source": "object_storage",
        "metadata": {
            "width": asset_width,
            "height": asset_height,
            "usage": usage,
            "tags": parse_asset_tags(tags),
            "storage_key": stored.key,
            "size_bytes": stored.size_bytes,
            "sha256": stored.sha256,
            "content_type": stored.content_type,
            **({"detected_dimensions": detected_dimensions} if detected_dimensions else {}),
        },
    }
    asset["url"] = f"/api/projects/{project['id']}/assets/{asset['id']}/download"
    store["assets"][asset["id"]] = asset
    record_asset_version(asset, "created")
    return asset


@app.get("/api/projects/{project_id}/assets")
def list_project_assets(
    project_id: str,
    search: str | None = None,
    tag: str | None = None,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    return {
        "assets": [
            asset
            for asset in store["assets"].values()
            if asset_matches_library_filter(asset, project, search, tag)
        ]
    }


@app.patch("/api/projects/{project_id}/assets/{asset_id}")
def update_project_asset(
    project_id: str,
    asset_id: str,
    payload: AssetUpdateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    asset = require_project_asset(project, asset_id)
    if payload.name is not None:
        asset["name"] = payload.name
    if payload.tags is not None:
        asset.setdefault("metadata", {})["tags"] = payload.tags
    record_asset_version(asset, "updated")
    store.flush()
    return asset


@app.get("/api/projects/{project_id}/assets/{asset_id}/versions")
def list_project_asset_versions(
    project_id: str,
    asset_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    require_project_asset(project, asset_id)
    return {"versions": store["asset_versions"].get(asset_id, [])}


@app.get("/api/projects/{project_id}/assets/{asset_id}/download")
def download_project_asset(
    project_id: str,
    asset_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> FileResponse:
    project = require_project(project_id, user)
    asset = require_project_asset(project, asset_id)
    storage_key = asset.get("metadata", {}).get("storage_key")
    if not storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found")
    try:
        path = object_storage.path_for(storage_key)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object missing")
    return FileResponse(
        path,
        media_type=asset.get("metadata", {}).get("content_type", "application/octet-stream"),
        filename=asset["name"],
    )


@app.post("/api/projects/{project_id}/assets/{asset_id}/copy", status_code=status.HTTP_201_CREATED)
def copy_project_asset(
    project_id: str,
    asset_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    asset = require_project_asset(project, asset_id)
    copied = {
        **asset,
        "id": make_id("ast"),
        "name": f"{asset['name']} Copy",
        "metadata": dict(asset.get("metadata", {})),
    }
    if "tags" in asset.get("metadata", {}):
        copied["metadata"]["tags"] = list(asset["metadata"]["tags"])
    store["assets"][copied["id"]] = copied
    record_asset_version(copied, "created")
    return copied


@app.delete("/api/projects/{project_id}/assets/{asset_id}")
def delete_project_asset(
    project_id: str,
    asset_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, str]:
    project = require_project(project_id, user)
    require_project_asset(project, asset_id)
    del store["assets"][asset_id]
    return {"status": "deleted"}


@app.post("/api/projects/{project_id}/ai/jobs", status_code=status.HTTP_201_CREATED)
def create_ai_job(
    project_id: str,
    payload: AiJobRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    validate_ai_execution_mode(payload.execution_mode)
    input_asset = require_optional_project_asset(project, payload.input_asset_id)
    reference_asset = require_optional_project_asset(project, payload.reference_asset_id)
    mask_asset = require_optional_project_asset(project, payload.mask_asset_id)
    estimated_credits = estimate_ai_job_credits(payload)
    usage = deduct_credits(user, f"ai_{payload.kind}", estimated_credits)
    job = {
        "id": make_id("job"),
        "project_id": project["id"],
        "kind": payload.kind,
        "prompt": payload.prompt,
        "style": payload.style,
        "input_asset": input_asset,
        "reference_asset": reference_asset,
        "mask_asset": mask_asset,
        "parameters": {
            "negative_prompt": payload.negative_prompt,
            "seed": payload.seed,
            "model": payload.model,
            "count": payload.count,
            "size": payload.size,
        },
        "estimated_credits": estimated_credits,
        "cost_credits": estimated_credits,
        "billing_usage": usage,
        "execution_mode": payload.execution_mode,
        "status": "queued" if payload.execution_mode == "queued" else "running",
        "progress": 0 if payload.execution_mode == "queued" else 50,
    }
    append_audit_event(
        project["id"],
        "ai_job_created",
        user["id"],
        "ai_job",
        job["id"],
        status_value=job["status"],
        metadata={
            "kind": job["kind"],
            "execution_mode": job["execution_mode"],
            "model": payload.model or "game-ui-default",
        },
    )
    if payload.execution_mode == "queued":
        queue_item = {
            "id": make_id("aiq"),
            "job_id": job["id"],
            "project_id": project["id"],
            "status": "queued",
            "attempts": 0,
            "worker": "gameuiagent-local-worker",
            "model": payload.model or "game-ui-default",
        }
        job["queue"] = queue_item
        store["ai_job_queue"][queue_item["id"]] = queue_item
    elif inference_provider_name == "qwen":
        try:
            complete_ai_job(project, job, run_inference_provider(project, job))
        except RuntimeError as exc:
            job["status"] = "failed"
            job["progress"] = 0
            job["error"] = str(exc)
    else:
        complete_ai_job(project, job)
    store["jobs"][job["id"]] = job
    if job["status"] in {"succeeded", "failed"}:
        append_audit_event(
            project["id"],
            f"ai_job_{job['status']}",
            user["id"],
            "ai_job",
            job["id"],
            status_value=job["status"],
            metadata={"result_asset_id": job.get("result_asset", {}).get("id")},
        )
    return job


@app.post("/api/worker/jobs/dequeue")
def dequeue_ai_job(_worker_authorized: bool = Depends(require_worker_token)) -> dict[str, Any]:
    queue_item = next(
        (item for item in store["ai_job_queue"].values() if item["status"] == "queued"),
        None,
    )
    if not queue_item:
        return {"status": "idle", "queue_item": None}
    job = store["jobs"].get(queue_item["job_id"])
    project = store["projects"].get(queue_item["project_id"])
    if not job or not project:
        queue_item["status"] = "failed"
        queue_item["error"] = "Queued job lost its project or job record"
        store.flush()
        return {"status": "failed", "queue_item": queue_item, "job": None}
    queue_item["status"] = "locked"
    queue_item["worker"] = "worker-" + queue_item.get("id", "")[-8:]
    queue_item["locked_at"] = datetime.now(timezone.utc).isoformat()
    job["status"] = "running"
    job["progress"] = 25
    store.flush()
    return {"status": "dequeued", "queue_item": queue_item, "job": job, "project": {"id": project["id"], "name": project["name"]}}


class WorkerCompleteRequest(BaseModel):
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


@app.post("/api/worker/jobs/{queue_id}/complete")
def complete_worker_job(
    queue_id: str,
    payload: WorkerCompleteRequest,
    _worker_authorized: bool = Depends(require_worker_token),
) -> dict[str, Any]:
    queue_item = store["ai_job_queue"].get(queue_id)
    if not queue_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue item not found")
    if queue_item["status"] != "locked":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Queue item is not locked")
    job = store["jobs"].get(queue_item["job_id"])
    project = store["projects"].get(queue_item["project_id"])
    if not job or not project:
        queue_item["status"] = "failed"
        queue_item["error"] = "Job or project not found"
        store.flush()
        return {"status": "failed", "queue_item": queue_item}

    if payload.status == "succeeded":
        queue_item["status"] = "succeeded"
        job["status"] = "succeeded"
        job["progress"] = 100
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        if payload.result:
            job["result"] = payload.result
            if payload.result.get("asset_id"):
                job["output_asset_ids"] = [payload.result["asset_id"]]
    else:
        queue_item["status"] = "failed"
        queue_item["error"] = payload.error or "Worker failed"
        job["status"] = "failed"
        job["progress"] = 0
        job["error"] = payload.error or "Worker failed"

    job["queue"] = queue_item
    if job["status"] in {"succeeded", "failed"}:
        append_audit_event(
            project["id"],
            f"ai_job_{job['status']}",
            None,
            "ai_job",
            job["id"],
            status_value=job["status"],
            metadata={"queue_id": queue_item["id"], "worker": queue_item.get("worker")},
        )
    store.flush()
    return {"status": job["status"], "queue_item": queue_item, "job": job}


@app.post("/api/system/ai-worker/run-next")
def run_next_ai_worker_job(_worker_authorized: bool = Depends(require_worker_token)) -> dict[str, Any]:
    queue_item = next(
        (item for item in store["ai_job_queue"].values() if item["status"] == "queued"),
        None,
    )
    if not queue_item:
        return {"status": "idle", "job": None}
    job = store["jobs"].get(queue_item["job_id"])
    project = store["projects"].get(queue_item["project_id"])
    if not job or not project:
        queue_item["status"] = "failed"
        queue_item["error"] = "Queued job lost its project or job record"
        store.flush()
        return {"status": "failed", "job": None, "queue": queue_item}
    queue_item["status"] = "running"
    queue_item["attempts"] += 1
    job["status"] = "running"
    job["progress"] = 50
    try:
        complete_ai_job(project, job, run_inference_provider(project, job))
        queue_item["status"] = "succeeded"
    except RuntimeError as exc:
        queue_item["status"] = "failed"
        queue_item["error"] = str(exc)
        job["status"] = "failed"
        job["progress"] = 0
        job["error"] = str(exc)
    job["queue"] = queue_item
    if job["status"] in {"succeeded", "failed"}:
        append_audit_event(
            project["id"],
            f"ai_job_{job['status']}",
            None,
            "ai_job",
            job["id"],
            status_value=job["status"],
            metadata={"queue_id": queue_item["id"], "worker": queue_item["worker"]},
        )
    store.flush()
    return {"status": "processed" if job["status"] == "succeeded" else "failed", "job": job, "queue": queue_item}


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
    if asset.get("source") == "ai" and asset.get("metadata", {}).get("layered_slices"):
        ir = build_ir_from_layered_asset_segmentation(project, asset)
        slices = build_layered_asset_slices(asset)
    elif asset.get("source") == "ai":
        ir = build_demo_ir(project)
        slices = build_slices_from_ir(ir)
    else:
        ir = build_ir_from_asset_segmentation(project, asset)
        slices = build_segmentation_slices(project, asset)
    store["irs"][ir["id"]] = ir
    segmentation = {
        "id": make_id("seg"),
        "project_id": project["id"],
        "source_asset_id": payload.asset_id,
        "ir_id": ir["id"],
        "confidence": 0.88,
        "slices": slices,
        "ir": ir,
    }
    append_audit_event(
        project["id"],
        "ui_segmentation_created",
        user["id"],
        "segmentation",
        segmentation["id"],
        metadata={"source_asset_id": payload.asset_id, "ir_id": ir["id"], "slice_count": len(slices)},
    )
    return segmentation


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


@app.post("/api/projects/{project_id}/imports/professional-sources", status_code=status.HTTP_201_CREATED)
def create_professional_import_source(
    project_id: str,
    payload: ProfessionalImportSourceRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    project = require_project(project_id, user)
    if payload.source_type not in {"psd", "psb", "figma"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported source type")
    source_asset = require_optional_project_asset(project, payload.asset_id)
    if payload.source_type in {"psd", "psb"} and not source_asset:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Asset source required")
    if payload.source_type == "figma" and not payload.figma_url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Figma URL required")
    source = {
        "source_type": payload.source_type,
        "asset_id": source_asset["id"] if source_asset else None,
        "figma_url": payload.figma_url,
        "frame_id": payload.frame_id,
        "parser": payload.parser,
    }
    file_name = source_asset["name"] if source_asset else str(payload.figma_url)
    parsed_source = parse_professional_import_source(project, payload, source_asset)
    document = build_design_document(
        project,
        ProfessionalImportRequest(
            source_type=payload.source_type,
            file_name=file_name,
            frame_id=payload.frame_id,
            parser=parsed_source["parser"],
            binary_header=parsed_source.get("binary_header"),
            layers=parsed_source["layers"],
        ),
    )
    ir = build_ir_from_design_document(project, document)
    store["irs"][ir["id"]] = ir
    imported = {
        "id": make_id("imp"),
        "project_id": project["id"],
        "status": "parsed",
        "source": source,
        "design_document": document,
        "parse_summary": {
            "parser": parsed_source["parser"],
            "preserved_layers": document["preserved_layers"],
            "warnings": parsed_source.get("warnings", []),
            **({"binary_header": parsed_source["binary_header"]} if parsed_source.get("binary_header") else {}),
            **({"layer_source": parsed_source["layer_source"]} if parsed_source.get("layer_source") else {}),
        },
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
    append_audit_event(
        project["id"],
        "engine_export_created",
        user["id"],
        "export",
        export["id"],
        metadata={"target_engine": payload.target_engine, "ir_id": payload.ir_id},
    )
    return export


@app.get("/api/projects/{project_id}/audit-events")
def get_project_audit_events(project_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    project = require_project(project_id, user)
    return {"events": project_audit_events(project)}


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
    store.flush()
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
    store.flush()
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
    if payload.status not in {"succeeded", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported import log status",
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
    append_audit_event(
        export["project_id"],
        "plugin_import_logged",
        user["id"],
        "plugin_import_log",
        log["id"],
        status_value=payload.status,
        metadata={
            "export_id": export["id"],
            "engine": payload.engine,
            "plugin_version": payload.plugin_version,
            "duration_ms": payload.duration_ms,
        },
    )
    store.flush()
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


class RechargeRequest(BaseModel):
    amount: int = Field(gt=0)
    method: str = Field(pattern="^(stripe|paypal|alipay|wechat)$")
    transaction_id: str


@app.post("/api/user/billing/recharge")
def recharge_credits(payload: RechargeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    account = billing_account_for(user)
    account["credits"]["purchased"] += payload.amount
    store.flush()
    append_audit_event(
        None,
        "billing_recharge",
        user["id"],
        "billing",
        user["id"],
        metadata={"amount": payload.amount, "method": payload.method, "transaction_id": payload.transaction_id},
    )
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
    store.flush()
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
        store.flush()
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


def validate_team_role(role: str) -> None:
    if role not in {"owner", "admin", "designer", "developer", "viewer"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported team role")


def create_team_membership(
    team: dict[str, Any],
    email: str,
    role: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    validate_team_role(role)
    membership = {
        "id": make_id("mem"),
        "team_id": team["id"],
        "email": email,
        "user_id": user_id,
        "role": role,
        "status": "active" if user_id else "invited",
    }
    store["memberships"][membership["id"]] = membership
    return membership


def team_memberships(team_id: str) -> list[dict[str, Any]]:
    return [
        membership
        for membership in store["memberships"].values()
        if membership["team_id"] == team_id
    ]


def format_team(team: dict[str, Any], members: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": team["id"],
        "name": team["name"],
        "owner_id": team["owner_id"],
        "member_count": len(members),
        "members": members,
    }


def require_team_admin(team_id: str, user: dict[str, Any]) -> dict[str, Any]:
    team = store["teams"].get(team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    membership = next(
        (
            member
            for member in team_memberships(team_id)
            if member["email"] == user["email"] and member["role"] in {"owner", "admin"}
        ),
        None,
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team admin role required")
    return team


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
    export = latest_project_export(project, engine)
    export_ready = export is not None
    plugin_import = {
        "kind": "plugin_import",
        "status": "ready" if export_ready else "queued",
        "progress": 0,
    }
    if export:
        import_log = latest_export_import_log(export)
        if import_log:
            plugin_import = {
                "kind": "plugin_import",
                "status": import_log["status"],
                "progress": 100,
                "summary": import_log["summary"],
            }
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
        plugin_import,
    ]


def latest_project_export_engine(project: dict[str, Any]) -> str | None:
    exports = [export for export in store["exports"].values() if export["project_id"] == project["id"]]
    return exports[-1]["target_engine"] if exports else None


def latest_project_export(project: dict[str, Any], target_engine: str) -> dict[str, Any] | None:
    exports = [
        export
        for export in store["exports"].values()
        if export["project_id"] == project["id"] and export["target_engine"] == target_engine
    ]
    return exports[-1] if exports else None


def latest_export_import_log(export: dict[str, Any]) -> dict[str, Any] | None:
    logs = [
        log
        for log in store["import_logs"].values()
        if log["export_id"] == export["id"]
    ]
    return logs[-1] if logs else None


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
        return refresh_studio_runtime_state(project, studio)
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
    apply_studio_layered_slice_summary(studio, ir)
    store["studio_states"][project["id"]] = studio
    return studio


def refresh_studio_runtime_state(project: dict[str, Any], studio: dict[str, Any]) -> dict[str, Any]:
    studio["timeline"] = build_studio_timeline(project, studio["export_wizard"]["target_engine"])
    apply_studio_layered_slice_summary(studio, latest_project_ir(project))
    return studio


def apply_studio_layered_slice_summary(studio: dict[str, Any], ir: dict[str, Any] | None) -> None:
    summary = build_studio_layered_slice_summary(ir)
    if summary:
        studio["layered_slice_summary"] = summary
    else:
        studio.pop("layered_slice_summary", None)


def build_studio_layered_slice_summary(ir: dict[str, Any] | None) -> dict[str, Any] | None:
    if not ir or ir.get("source_asset", {}).get("segmentation_source") != "qwen-layered-slice":
        return None
    nodes = [
        {
            "id": node["id"],
            "type": node["type"],
            "name": node["name"],
            "rect": node["rect"],
            "editable_bounds": True,
        }
        for node in ir.get("nodes", [])
        if node.get("segmentation_source") == "qwen-layered-slice"
    ]
    if not nodes:
        return None
    return {
        "source": "qwen-layered-slice",
        "slice_count": len(nodes),
        "editable_node_count": len(nodes),
        "nodes": nodes,
    }


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


def build_uploaded_asset(project: dict[str, Any], payload: AssetRequest) -> dict[str, Any]:
    validate_asset_type(payload.type)
    return {
        "id": make_id("ast"),
        "project_id": project["id"],
        "type": payload.type,
        "name": payload.name,
        "url": payload.url,
        "source": "upload",
        "metadata": {
            "width": payload.width,
            "height": payload.height,
            "usage": payload.usage,
            "tags": payload.tags,
        },
    }


def validate_asset_type(asset_type: str) -> None:
    if asset_type not in {"original_upload", "reference_image", "mask", "psd", "psb", "figma_link"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported asset type")


def parse_asset_tags(tags: str) -> list[str]:
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def detect_uploaded_image_dimensions(content: bytes, content_type: str, filename: str) -> dict[str, Any] | None:
    if (content_type == "image/png" or filename.lower().endswith(".png")) and content.startswith(b"\x89PNG\r\n\x1a\n"):
        if len(content) < 24 or content[12:16] != b"IHDR":
            return None
        width = int.from_bytes(content[16:20], "big")
        height = int.from_bytes(content[20:24], "big")
        if width > 0 and height > 0:
            return {"width": width, "height": height, "format": "png"}
    return None


def require_optional_project_asset(project: dict[str, Any], asset_id: str | None) -> dict[str, Any] | None:
    if asset_id is None:
        return None
    return require_project_asset(project, asset_id)


def require_project_asset(project: dict[str, Any], asset_id: str) -> dict[str, Any]:
    asset = store["assets"].get(asset_id)
    if not asset or asset["project_id"] != project["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


def asset_matches_library_filter(
    asset: dict[str, Any],
    project: dict[str, Any],
    search: str | None,
    tag: str | None,
) -> bool:
    if asset["project_id"] != project["id"]:
        return False
    if search and search.lower() not in asset["name"].lower():
        return False
    if tag and tag not in asset.get("metadata", {}).get("tags", []):
        return False
    return True


def record_asset_version(asset: dict[str, Any], event: str) -> None:
    store["asset_versions"].setdefault(asset["id"], []).append(
        {
            "id": make_id("ver"),
            "asset_id": asset["id"],
            "event": event,
            "name": asset["name"],
            "metadata": dict(asset.get("metadata", {})),
        }
    )


def estimate_ai_job_credits(payload: AiJobRequest) -> int:
    base_costs = {
        "text_to_image": 2,
        "image_to_image": 2,
        "inpainting": 3,
        "matting": 2,
        "upscale": 2,
    }
    return base_costs.get(payload.kind, 2) * max(payload.count, 1)


def validate_ai_execution_mode(execution_mode: str) -> None:
    if execution_mode not in {"inline", "queued"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported AI execution mode")


def inference_provider_configured() -> bool:
    if inference_provider_name == "qwen":
        return bool(getenv("QWEN_API_KEY"))
    return inference_provider_name == "local-deterministic"


def qwen_inference_endpoint() -> str:
    return getenv("QWEN_IMAGE_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1/images/generations")


def build_inference_request(project: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    input_asset = job.get("input_asset")
    reference_asset = job.get("reference_asset")
    return {
        "job_id": job["id"],
        "project_id": project["id"],
        "kind": job["kind"],
        "prompt": job["prompt"],
        "model": job["parameters"].get("model") or "qwen-image",
        "seed": job["parameters"].get("seed"),
        "count": job["parameters"]["count"],
        "size": job["parameters"]["size"],
        "canvas": project["canvas"],
        "input_asset_id": input_asset["id"] if input_asset else None,
        "reference_asset": (
            {"id": reference_asset["id"], "url": reference_asset["url"]}
            if reference_asset
            else None
        ),
    }


def run_inference_provider(project: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    request = build_inference_request(project, job)
    run = {
        "id": make_id("inf"),
        "job_id": job["id"],
        "project_id": project["id"],
        "provider": inference_provider_name,
        "status": "running",
        "request": request,
    }
    store["inference_runs"][run["id"]] = run
    try:
        if inference_provider_name == "failing":
            raise RuntimeError("Inference provider failed")
        if inference_provider_name == "qwen":
            response = call_qwen_inference(request)
        elif inference_provider_name == "local-deterministic":
            response = {
                "asset_url": f"/inference/local-deterministic/{job['id']}.png",
                "provider_job_id": f"local-{job['id']}",
            }
        else:
            raise RuntimeError("Inference provider is not configured")
    except RuntimeError as exc:
        run["status"] = "failed"
        run["error"] = str(exc)
        store.flush()
        raise
    run["status"] = "succeeded"
    run["response"] = response
    store.flush()
    return {"run_id": run["id"], "provider": run["provider"], **response}


def call_qwen_inference(request: dict[str, Any]) -> dict[str, Any]:
    api_key = getenv("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("Inference provider is not configured")
    try:
        response = httpx.post(
            qwen_inference_endpoint(),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": request["model"],
                "prompt": request["prompt"],
                "n": request["count"],
                "size": "1024x1024",
                "response_format": "url_with_layered_slices",
                **({"reference_asset": request["reference_asset"]} if request.get("reference_asset") else {}),
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("Inference provider failed") from exc
    asset_url = (
        (payload.get("data") or [{}])[0].get("url")
        or (payload.get("output", {}).get("results") or [{}])[0].get("url")
    )
    if not asset_url:
        raise RuntimeError("Inference provider returned no asset URL")
    return {
        "asset_url": asset_url,
        "provider_job_id": payload.get("id") or payload.get("request_id"),
        "layered_slices": extract_qwen_layered_slices(payload),
    }


def extract_qwen_layered_slices(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        payload.get("layered_slices"),
        first_payload_item(payload.get("data")).get("layered_slices"),
        first_payload_item(payload.get("output", {}).get("results")).get("layered_slices"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return normalize_layered_slices(candidate, source="qwen-layered-slice")
    return []


def first_payload_item(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


def normalize_layered_slices(raw_slices: list[Any], source: str) -> list[dict[str, Any]]:
    slices: list[dict[str, Any]] = []
    for index, raw_slice in enumerate(raw_slices[:64]):
        if not isinstance(raw_slice, dict) or not isinstance(raw_slice.get("rect"), dict):
            continue
        rect = normalize_slice_rect(raw_slice["rect"])
        if not rect:
            continue
        slice_type = raw_slice.get("type") if isinstance(raw_slice.get("type"), str) else "image"
        name = raw_slice.get("name") if isinstance(raw_slice.get("name"), str) else f"Layered Slice {index + 1}"
        slice_id = raw_slice.get("id") if isinstance(raw_slice.get("id"), str) else f"layered_slice_{index + 1}"
        confidence = raw_slice.get("confidence") if isinstance(raw_slice.get("confidence"), (int, float)) else 0.9
        slices.append(
            {
                "id": slice_id,
                "type": slice_type,
                "name": name,
                "rect": rect,
                "confidence": max(0.0, min(float(confidence), 1.0)),
                "editable_bounds": True,
                "segmentation_source": source,
            }
        )
    return slices


def normalize_slice_rect(rect: dict[str, Any]) -> dict[str, int] | None:
    try:
        x = int(rect["x"])
        y = int(rect["y"])
        width = int(rect["width"])
        height = int(rect["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if width <= 0 or height <= 0 or x < 0 or y < 0:
        return None
    return {"x": x, "y": y, "width": width, "height": height}


def complete_ai_job(
    project: dict[str, Any],
    job: dict[str, Any],
    inference_result: dict[str, Any] | None = None,
) -> None:
    input_asset = job.get("input_asset")
    reference_asset = job.get("reference_asset")
    asset_url = inference_result["asset_url"] if inference_result else f"/generated/{project['id']}/{job['kind']}.png"
    layered_slices = inference_result.get("layered_slices", []) if inference_result else []
    asset = {
        "id": make_id("ast"),
        "project_id": project["id"],
        "type": "generated_image",
        "name": f"{project['name']} generated concept",
        "prompt": job["prompt"],
        "url": asset_url,
        "size": job["parameters"]["size"],
        "source": "ai",
        "metadata": {
            "width": project["canvas"]["width"],
            "height": project["canvas"]["height"],
            "usage": job["kind"],
            "input_asset_id": input_asset["id"] if input_asset else None,
            "reference_asset_id": reference_asset["id"] if reference_asset else None,
            "model": job["parameters"].get("model"),
            "execution_mode": job["execution_mode"],
            "inference_provider": inference_result["provider"] if inference_result else "inline-local",
            "inference_run_id": inference_result["run_id"] if inference_result else None,
            **({"layered_slice_provider": inference_result["provider"], "layered_slices": layered_slices} if layered_slices else {}),
        },
    }
    store["assets"][asset["id"]] = asset
    job["candidates"] = [
        {"asset_id": asset["id"], "rank": index + 1, "score": round(0.94 - index * 0.03, 2)}
        for index in range(job["parameters"]["count"])
    ]
    job["status"] = "succeeded"
    job["progress"] = 100
    job["result_asset"] = asset
    if inference_result:
        job["inference"] = {
            "run_id": inference_result["run_id"],
            "provider": inference_result["provider"],
            "provider_job_id": inference_result.get("provider_job_id"),
        }


def build_segmentation_slices(project: dict[str, Any], asset: dict[str, Any]) -> list[dict[str, Any]]:
    width = asset.get("metadata", {}).get("width", project["canvas"]["width"])
    height = asset.get("metadata", {}).get("height", project["canvas"]["height"])
    pixel_slices = build_png_alpha_component_slices(asset)
    if pixel_slices:
        return pixel_slices
    return [
        {
            "id": "slice_panel_main",
            "type": "panel",
            "name": "Main Panel",
            "confidence": 0.9,
            "editable_bounds": True,
            "rect": {"x": int(width * 0.12), "y": int(height * 0.12), "width": int(width * 0.76), "height": int(height * 0.7)},
        },
        {
            "id": "slice_button_primary",
            "type": "button",
            "name": "Primary Button",
            "confidence": 0.87,
            "editable_bounds": True,
            "rect": {"x": int(width * 0.68), "y": int(height * 0.76), "width": int(width * 0.16), "height": int(height * 0.09)},
        },
        {
            "id": "slice_title_text",
            "type": "text",
            "name": "Title Text",
            "confidence": 0.84,
            "editable_bounds": True,
            "rect": {"x": int(width * 0.17), "y": int(height * 0.15), "width": int(width * 0.32), "height": int(height * 0.07)},
        },
    ]


def build_png_alpha_component_slices(asset: dict[str, Any]) -> list[dict[str, Any]]:
    rgba = decode_stored_png_rgba(asset)
    if not rgba:
        return []
    width = rgba["width"]
    height = rgba["height"]
    pixels = rgba["pixels"]
    visited: set[tuple[int, int]] = set()
    components: list[dict[str, int]] = []
    for y in range(height):
        for x in range(width):
            if (x, y) in visited or not png_pixel_is_opaque(pixels, width, x, y):
                continue
            components.append(flood_fill_png_alpha_component(pixels, width, height, x, y, visited))
    components.sort(key=lambda rect: (rect["y"], rect["x"]))
    return [
        {
            "id": f"slice_alpha_component_{index + 1}",
            "type": "image",
            "name": f"Alpha Component {index + 1}",
            "confidence": 0.93,
            "editable_bounds": True,
            "segmentation_source": "png-alpha-components",
            "rect": rect,
        }
        for index, rect in enumerate(components[:64])
    ]


def decode_stored_png_rgba(asset: dict[str, Any]) -> dict[str, Any] | None:
    storage_key = asset.get("metadata", {}).get("storage_key")
    if not storage_key:
        return None
    try:
        content = object_storage.path_for(storage_key).read_bytes()
    except (RuntimeError, ValueError, OSError):
        return None
    return decode_png_rgba(content)


def decode_png_rgba(content: bytes) -> dict[str, Any] | None:
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    cursor = 8
    width = 0
    height = 0
    idat_chunks: list[bytes] = []
    while cursor + 8 <= len(content):
        length = read_uint(content[cursor : cursor + 4])
        chunk_type = content[cursor + 4 : cursor + 8]
        payload_start = cursor + 8
        payload_end = payload_start + length
        if payload_end + 4 > len(content):
            return None
        payload = content[payload_start:payload_end]
        cursor = payload_end + 4
        if chunk_type == b"IHDR":
            if (
                len(payload) < 13
                or payload[8] != 8
                or payload[9] != 6
                or payload[10] != 0
                or payload[11] != 0
                or payload[12] != 0
            ):
                return None
            width = read_uint(payload[0:4])
            height = read_uint(payload[4:8])
        elif chunk_type == b"IDAT":
            idat_chunks.append(payload)
        elif chunk_type == b"IEND":
            break
    if width <= 0 or height <= 0 or not idat_chunks:
        return None
    if width * height > MAX_PNG_ALPHA_SEGMENTATION_PIXELS:
        return None
    try:
        raw = decompress(b"".join(idat_chunks))
    except ZlibError:
        return None
    pixels = unfilter_png_rgba_scanlines(raw, width, height)
    if pixels is None:
        return None
    return {"width": width, "height": height, "pixels": pixels}


def unfilter_png_rgba_scanlines(raw: bytes, width: int, height: int) -> bytes | None:
    bytes_per_pixel = 4
    stride = width * bytes_per_pixel
    expected = height * (stride + 1)
    if len(raw) < expected:
        return None
    previous = bytearray(stride)
    pixels = bytearray()
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        row = bytearray(raw[cursor : cursor + stride])
        cursor += stride
        for index, value in enumerate(row):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 1:
                row[index] = (value + left) & 0xFF
            elif filter_type == 2:
                row[index] = (value + up) & 0xFF
            elif filter_type == 3:
                row[index] = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                row[index] = (value + png_paeth_predictor(left, up, upper_left)) & 0xFF
            elif filter_type != 0:
                return None
        pixels.extend(row)
        previous = row
    return bytes(pixels)


def png_paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def png_pixel_is_opaque(pixels: bytes, width: int, x: int, y: int) -> bool:
    return pixels[((y * width + x) * 4) + 3] > 0


def flood_fill_png_alpha_component(
    pixels: bytes,
    width: int,
    height: int,
    start_x: int,
    start_y: int,
    visited: set[tuple[int, int]],
) -> dict[str, int]:
    stack = [(start_x, start_y)]
    visited.add((start_x, start_y))
    min_x = max_x = start_x
    min_y = max_y = start_y
    while stack:
        x, y = stack.pop()
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
        for next_x, next_y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= next_x < width and 0 <= next_y < height):
                continue
            if (next_x, next_y) in visited or not png_pixel_is_opaque(pixels, width, next_x, next_y):
                continue
            visited.add((next_x, next_y))
            stack.append((next_x, next_y))
    return {"x": min_x, "y": min_y, "width": max_x - min_x + 1, "height": max_y - min_y + 1}


def build_slices_from_ir(ir: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": node["id"],
            "type": node["type"],
            "name": node["name"],
            "confidence": 0.9,
            "editable_bounds": True,
            "rect": node["rect"],
        }
        for node in ir["nodes"]
        if node["type"] != "canvas"
    ]


def build_layered_asset_slices(asset: dict[str, Any]) -> list[dict[str, Any]]:
    return normalize_layered_slices(
        asset.get("metadata", {}).get("layered_slices", []),
        source="qwen-layered-slice",
    )


def build_ir_from_layered_asset_segmentation(project: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    slices = build_layered_asset_slices(asset)
    nodes = [
        {
            "id": "root",
            "type": "canvas",
            "name": project["name"],
            "rect": {"x": 0, "y": 0, "width": project["canvas"]["width"], "height": project["canvas"]["height"]},
        }
    ]
    nodes.extend(
        {
            "id": item["id"],
            "type": item["type"],
            "name": item["name"],
            "rect": item["rect"],
            "source_asset_id": asset["id"],
            "confidence": item["confidence"],
            "segmentation_source": item["segmentation_source"],
        }
        for item in slices
    )
    return {
        "id": make_id("ir"),
        "project_id": project["id"],
        "version": "0.1.0",
        "engine_targets": ["unity", "cocos", "godot", "unreal"],
        "canvas": project["canvas"],
        "source_asset": {
            "id": asset["id"],
            "type": asset["type"],
            "name": asset["name"],
            "segmentation_source": "qwen-layered-slice",
            "inference_provider": asset.get("metadata", {}).get("inference_provider"),
            "inference_run_id": asset.get("metadata", {}).get("inference_run_id"),
        },
        "nodes": nodes,
    }


def build_ir_from_asset_segmentation(project: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    slices = build_segmentation_slices(project, asset)
    nodes = [
        {
            "id": "root",
            "type": "canvas",
            "name": project["name"],
            "rect": {"x": 0, "y": 0, "width": project["canvas"]["width"], "height": project["canvas"]["height"]},
        }
    ]
    nodes.extend(
        {
            "id": item["id"],
            "type": item["type"],
            "name": item["name"],
            "rect": item["rect"],
            "source_asset_id": asset["id"],
            "confidence": item["confidence"],
            **({"segmentation_source": item["segmentation_source"]} if item.get("segmentation_source") else {}),
        }
        for item in slices
    )
    return {
        "id": make_id("ir"),
        "project_id": project["id"],
        "version": "0.1.0",
        "engine_targets": ["unity", "cocos", "godot", "unreal"],
        "canvas": project["canvas"],
        "source_asset": {
            "id": asset["id"],
            "type": asset["type"],
            "name": asset["name"],
            **(
                {"detected_dimensions": asset["metadata"]["detected_dimensions"]}
                if asset.get("metadata", {}).get("detected_dimensions")
                else {}
            ),
            **(
                {"segmentation_source": "png-alpha-components"}
                if any(item.get("segmentation_source") == "png-alpha-components" for item in slices)
                else {}
            ),
        },
        "nodes": nodes,
    }


def mock_layers_for_import_source(project: dict[str, Any], source_type: str) -> list[ProfessionalLayer]:
    width = project["canvas"]["width"]
    height = project["canvas"]["height"]
    return [
        ProfessionalLayer(
            id=f"{source_type}_layer_panel",
            name="Imported Main Panel",
            kind="image",
            rect={"x": int(width * 0.1), "y": int(height * 0.12), "width": int(width * 0.8), "height": int(height * 0.68)},
        ),
        ProfessionalLayer(
            id=f"{source_type}_layer_button",
            name="Imported CTA Button",
            kind="image",
            rect={"x": int(width * 0.66), "y": int(height * 0.76), "width": int(width * 0.18), "height": int(height * 0.1)},
        ),
        ProfessionalLayer(
            id=f"{source_type}_layer_label",
            name="Imported Label",
            kind="text",
            text="START",
            rect={"x": int(width * 0.7), "y": int(height * 0.78), "width": int(width * 0.1), "height": int(height * 0.05)},
        ),
    ]


def parse_professional_import_source(
    project: dict[str, Any],
    payload: ProfessionalImportSourceRequest,
    source_asset: dict[str, Any] | None,
) -> dict[str, Any]:
    if payload.source_type == "figma":
        if getenv("FIGMA_API_TOKEN"):
            return parse_figma_api_source(project, payload)
        return {
            "parser": payload.parser,
            "layers": mock_layers_for_import_source(project, payload.source_type),
            "warnings": ["Figma API parser adapter is not configured; using contract-preserving fallback layers."],
        }
    if payload.parser == "mock-layer-parser":
        return {
            "parser": payload.parser,
            "layers": mock_layers_for_import_source(project, payload.source_type),
            "warnings": ["Mock parser requested explicitly; no binary PSD data was decoded."],
        }
    if payload.source_type in {"psd", "psb"}:
        if not source_asset:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Asset source required")
        header = parse_psd_binary_header(source_asset, payload.source_type)
        parsed_layers = parse_psd_layer_records(source_asset, payload.source_type)
        if parsed_layers:
            return {
                "parser": payload.parser,
                "binary_header": header,
                "layer_source": "psd-layer-records",
                "layers": parsed_layers,
                "warnings": [],
            }
        return {
            "parser": payload.parser,
            "binary_header": header,
            "layer_source": "composite-fallback",
            "layers": [
                ProfessionalLayer(
                    id=f"{payload.source_type}_composite_canvas",
                    name=f"{payload.source_type.upper()} Composite Canvas",
                    kind="image",
                    rect={"x": 0, "y": 0, "width": header["width"], "height": header["height"]},
                )
            ],
            "warnings": ["Layer records are not present in the minimal header parse; composite canvas fallback created."],
        }
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported source type")


def parse_figma_api_source(project: dict[str, Any], payload: ProfessionalImportSourceRequest) -> dict[str, Any]:
    file_key = extract_figma_file_key(str(payload.figma_url))
    frame_id = payload.frame_id
    if not frame_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Figma frame ID required")
    try:
        response = httpx.get(
            f"https://api.figma.com/v1/files/{file_key}/nodes?ids={quote(frame_id, safe='')}",
            headers={"X-Figma-Token": str(getenv("FIGMA_API_TOKEN"))},
            timeout=30,
        )
        response.raise_for_status()
        payload_json = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Figma API import failed") from exc
    frame_node = ((payload_json.get("nodes") or {}).get(frame_id) or {}).get("document")
    if not isinstance(frame_node, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Figma frame not found")
    layers = figma_node_to_layers(frame_node)
    warnings = attach_figma_image_assets(project, file_key, layers)
    return {
        "parser": payload.parser,
        "layer_source": "figma-api",
        "layers": layers,
        "warnings": warnings,
    }


def extract_figma_file_key(figma_url: str) -> str:
    parts = [part for part in figma_url.split("/") if part]
    for marker in ("file", "design"):
        if marker in parts and parts.index(marker) + 1 < len(parts):
            return parts[parts.index(marker) + 1]
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid Figma URL")


def figma_node_to_layers(node: dict[str, Any], parent_id: str | None = None) -> list[ProfessionalLayer]:
    layer = ProfessionalLayer(
        id=str(node.get("id")),
        name=str(node.get("name") or "Figma Layer"),
        kind=figma_node_kind(node),
        rect=figma_node_rect(node),
        parent_id=parent_id,
        text=node.get("characters") if isinstance(node.get("characters"), str) else None,
        text_style=figma_text_style(node),
        component_key=figma_component_key(node),
        auto_layout=figma_auto_layout(node),
        constraints=node.get("constraints") if isinstance(node.get("constraints"), dict) else None,
        image_ref=figma_image_ref(node),
        is_group=node.get("type") in {"FRAME", "GROUP", "SECTION"},
    )
    layers = [layer]
    for child in node.get("children", []):
        if isinstance(child, dict):
            layers.extend(figma_node_to_layers(child, layer.id))
    return layers


def figma_node_kind(node: dict[str, Any]) -> str:
    node_type = node.get("type")
    if node_type == "TEXT":
        return "text"
    if node_type in {"COMPONENT", "INSTANCE"}:
        return "component"
    if node_type in {"FRAME", "GROUP", "SECTION"}:
        return "frame"
    return "image"


def figma_node_rect(node: dict[str, Any]) -> dict[str, int]:
    bounds = node.get("absoluteBoundingBox") if isinstance(node.get("absoluteBoundingBox"), dict) else {}
    return {
        "x": int(bounds.get("x", 0)),
        "y": int(bounds.get("y", 0)),
        "width": max(1, int(bounds.get("width", 1))),
        "height": max(1, int(bounds.get("height", 1))),
    }


def figma_auto_layout(node: dict[str, Any]) -> dict[str, Any] | None:
    layout_mode = node.get("layoutMode")
    if layout_mode not in {"HORIZONTAL", "VERTICAL"}:
        return None
    return {
        "direction": str(layout_mode).lower(),
        "gap": int(node.get("itemSpacing", 0) or 0),
    }


def figma_component_key(node: dict[str, Any]) -> str | None:
    for key in ("key", "componentId"):
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def figma_image_ref(node: dict[str, Any]) -> str | None:
    fills = node.get("fills")
    if not isinstance(fills, list):
        return None
    for fill in fills:
        if isinstance(fill, dict) and fill.get("type") == "IMAGE" and isinstance(fill.get("imageRef"), str):
            return fill["imageRef"]
    return None


def attach_figma_image_assets(project: dict[str, Any], file_key: str, layers: list[ProfessionalLayer]) -> list[str]:
    image_layers = [layer for layer in layers if layer.image_ref]
    if not image_layers:
        return []
    if not object_storage.durable:
        return ["Figma image fills were detected but object storage is not configured."]
    warnings: list[str] = []
    image_urls = fetch_figma_image_urls(file_key, [layer.id for layer in image_layers])
    for layer in image_layers:
        image_url = image_urls.get(layer.id)
        if not image_url:
            warnings.append(f"Figma image export missing for node {layer.id}.")
            continue
        try:
            content, content_type = download_figma_image_fill(image_url)
        except httpx.HTTPError:
            warnings.append(f"Figma image download failed for node {layer.id}.")
            continue
        except ValueError as exc:
            warnings.append(f"Figma image download skipped for node {layer.id}: {exc}.")
            continue
        asset = store_figma_image_asset(project, layer, content, content_type)
        layer.image_asset_id = asset["id"]
        layer.image_url = asset["url"]
    return warnings


def download_figma_image_fill(image_url: str) -> tuple[bytes, str]:
    chunks: list[bytes] = []
    total_bytes = 0
    with httpx.stream("GET", image_url, timeout=30) as response:
        response.raise_for_status()
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_FIGMA_IMAGE_FILL_BYTES:
            raise ValueError("image exceeds 25MB limit")
        for chunk in response.iter_bytes():
            total_bytes += len(chunk)
            if total_bytes > MAX_FIGMA_IMAGE_FILL_BYTES:
                raise ValueError("image exceeds 25MB limit")
            chunks.append(chunk)
        return b"".join(chunks), response.headers.get("content-type", "image/png")


def fetch_figma_image_urls(file_key: str, node_ids: list[str]) -> dict[str, str]:
    if not node_ids:
        return {}
    ids = ",".join(quote(node_id, safe="") for node_id in node_ids)
    try:
        response = httpx.get(
            f"https://api.figma.com/v1/images/{file_key}?ids={ids}&format=png",
            headers={"X-Figma-Token": str(getenv("FIGMA_API_TOKEN"))},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Figma image export failed") from exc
    images = payload.get("images")
    if not isinstance(images, dict):
        return {}
    return {str(node_id): str(url) for node_id, url in images.items() if isinstance(url, str)}


def store_figma_image_asset(
    project: dict[str, Any],
    layer: ProfessionalLayer,
    content: bytes,
    content_type: str,
) -> dict[str, Any]:
    stored = object_storage.put(project["id"], f"{layer.id}-{layer.name}.png", content, content_type)
    asset = {
        "id": make_id("ast"),
        "project_id": project["id"],
        "type": "figma_image",
        "name": layer.name,
        "url": "",
        "source": "figma_image",
        "metadata": {
            "width": layer.rect["width"],
            "height": layer.rect["height"],
            "usage": "figma_image_fill",
            "storage_key": stored.key,
            "size_bytes": stored.size_bytes,
            "sha256": stored.sha256,
            "content_type": stored.content_type,
            "figma_node_id": layer.id,
            "figma_image_ref": layer.image_ref,
        },
    }
    asset["url"] = f"/api/projects/{project['id']}/assets/{asset['id']}/download"
    store["assets"][asset["id"]] = asset
    record_asset_version(asset, "created")
    return asset


def figma_text_style(node: dict[str, Any]) -> dict[str, Any] | None:
    style = node.get("style")
    if not isinstance(style, dict):
        return None
    parsed: dict[str, Any] = {}
    if isinstance(style.get("fontFamily"), str):
        parsed["font"] = style["fontFamily"]
    if isinstance(style.get("fontSize"), (int, float)):
        parsed["font_size"] = style["fontSize"]
    return parsed or None


def stored_asset_path(source_asset: dict[str, Any]) -> Any:
    storage_key = source_asset.get("metadata", {}).get("storage_key")
    if not storage_key:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Stored PSD/PSB binary asset required")
    try:
        path = object_storage.path_for(storage_key)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Stored PSD/PSB binary asset missing")
    return path


def parse_psd_binary_header(source_asset: dict[str, Any], source_type: str) -> dict[str, Any]:
    path = stored_asset_path(source_asset)
    with path.open("rb") as source_file:
        header = source_file.read(26)
    if len(header) < 26:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PSD/PSB header")
    signature = header[0:4].decode("ascii", errors="ignore")
    version = int.from_bytes(header[4:6], "big")
    expected_version = 2 if source_type == "psb" else 1
    if signature != "8BPS" or version != expected_version:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PSD/PSB signature or version")
    channels = int.from_bytes(header[12:14], "big")
    height = int.from_bytes(header[14:18], "big")
    width = int.from_bytes(header[18:22], "big")
    depth = int.from_bytes(header[22:24], "big")
    color_mode_id = int.from_bytes(header[24:26], "big")
    if width <= 0 or height <= 0 or channels <= 0 or depth <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PSD/PSB dimensions")
    return {
        "signature": signature,
        "version": version,
        "width": width,
        "height": height,
        "channels": channels,
        "depth": depth,
        "color_mode": psd_color_mode_name(color_mode_id),
    }


def parse_psd_layer_records(source_asset: dict[str, Any], source_type: str) -> list[ProfessionalLayer]:
    path = stored_asset_path(source_asset)
    length_size = 8 if source_type == "psb" else 4
    with path.open("rb") as source_file:
        source_file.seek(26)
        color_mode_length = read_uint(source_file.read(4))
        source_file.seek(color_mode_length, 1)
        image_resources_length = read_uint(source_file.read(4))
        source_file.seek(image_resources_length, 1)
        layer_mask_length = read_uint(source_file.read(length_size))
        if layer_mask_length <= 0 or layer_mask_length > 5_000_000:
            return []
        layer_mask_section = source_file.read(layer_mask_length)
    if len(layer_mask_section) < length_size + 2:
        return []
    layer_info_length = read_uint(layer_mask_section[0:length_size])
    layer_info = layer_mask_section[length_size : length_size + layer_info_length]
    if len(layer_info) < 2:
        return []
    layer_count = abs(int.from_bytes(layer_info[0:2], "big", signed=True))
    cursor = 2
    layers: list[ProfessionalLayer] = []
    group_stack: list[ProfessionalLayer] = []
    for index in range(layer_count):
        if cursor + 18 > len(layer_info):
            return []
        top = read_uint(layer_info[cursor : cursor + 4])
        left = read_uint(layer_info[cursor + 4 : cursor + 8])
        bottom = read_uint(layer_info[cursor + 8 : cursor + 12])
        right = read_uint(layer_info[cursor + 12 : cursor + 16])
        cursor += 16
        channel_count = read_uint(layer_info[cursor : cursor + 2])
        cursor += 2
        channel_records_length = channel_count * (2 + length_size)
        if cursor + channel_records_length + 16 > len(layer_info):
            return []
        cursor += channel_records_length
        cursor += 8
        opacity_byte = layer_info[cursor]
        cursor += 1
        cursor += 1
        flags = layer_info[cursor]
        cursor += 1
        cursor += 1
        extra_length = read_uint(layer_info[cursor : cursor + 4])
        cursor += 4
        extra_data = layer_info[cursor : cursor + extra_length]
        cursor += extra_length
        metadata = parse_psd_layer_metadata(extra_data)
        name = metadata.get("name") or f"Layer {index + 1}"
        section_divider_type = metadata.get("section_divider_type")
        if section_divider_type == 3:
            if group_stack:
                group_stack.pop()
            continue
        is_group = section_divider_type in {1, 2}
        smart_object = metadata.get("smart_object") is True
        text_content = metadata.get("text")
        text_style = metadata.get("text_style")
        kind = "group" if is_group else "text" if text_content else "component" if smart_object else "image"
        layer = ProfessionalLayer(
            id=f"psd_layer_{index + 1}_{sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower() or 'layer'}",
            name=name,
            kind=kind,
            rect={"x": left, "y": top, "width": max(right - left, 0), "height": max(bottom - top, 0)},
            text=text_content,
            text_style=text_style,
            opacity=round(opacity_byte / 255, 3),
            visible=(flags & 2) == 0,
            is_group=is_group,
            smart_object=smart_object,
        )
        if group_stack:
            layer.parent_id = group_stack[-1].id
            layer.group_path = [group.name for group in group_stack]
        if layer.is_group:
            group_stack.append(layer)
        layers.append(layer)
    return layers


def parse_psd_layer_metadata(extra_data: bytes) -> dict[str, Any]:
    if len(extra_data) < 9:
        return {}
    cursor = 0
    mask_length = read_uint(extra_data[cursor : cursor + 4])
    cursor += 4 + mask_length
    if cursor + 4 > len(extra_data):
        return {}
    blending_ranges_length = read_uint(extra_data[cursor : cursor + 4])
    cursor += 4 + blending_ranges_length
    if cursor >= len(extra_data):
        return {}
    name_length = extra_data[cursor]
    cursor += 1
    name = extra_data[cursor : cursor + name_length].decode("utf-8", errors="ignore")
    cursor += name_length
    cursor += (4 - (cursor % 4)) % 4
    metadata: dict[str, Any] = {"name": name}
    while cursor + 12 <= len(extra_data):
        signature = extra_data[cursor : cursor + 4]
        key = extra_data[cursor + 4 : cursor + 8]
        length = read_uint(extra_data[cursor + 8 : cursor + 12])
        cursor += 12
        payload = extra_data[cursor : cursor + length]
        cursor += length + (length % 2)
        if signature not in {b"8BIM", b"8B64"}:
            continue
        if key == b"luni" and len(payload) >= 4:
            char_count = read_uint(payload[0:4])
            unicode_bytes = payload[4 : 4 + char_count * 2]
            metadata["name"] = unicode_bytes.decode("utf-16-be", errors="ignore")
        elif key == b"lsct" and len(payload) >= 4:
            section_type = read_uint(payload[0:4])
            metadata["section_divider_type"] = section_type
            metadata["is_group"] = section_type in {1, 2}
        elif key in {b"SoLd", b"SoLE", b"SoCo"}:
            metadata["smart_object"] = True
        elif key in {b"TySh", b"tySh"}:
            type_tool = parse_psd_type_tool(payload)
            if type_tool.get("text"):
                metadata["text"] = type_tool["text"]
            if type_tool.get("style"):
                metadata["text_style"] = type_tool["style"]
    return metadata


def parse_psd_type_tool(payload: bytes) -> dict[str, Any]:
    for encoding in ("utf-8", "utf-16-be"):
        decoded = payload.decode(encoding, errors="ignore")
        parsed = {
            "text": extract_engine_data_text(decoded),
            "style": extract_engine_data_text_style(decoded),
        }
        if parsed["text"] or parsed["style"]:
            return parsed
    return {}


def extract_engine_data_text(engine_data: str) -> str | None:
    for marker in ("/Text", "/Txt"):
        marker_index = engine_data.find(marker)
        while marker_index != -1:
            open_index = engine_data.find("(", marker_index + len(marker))
            if open_index == -1:
                break
            text, close_index = read_parenthesized_text(engine_data, open_index)
            if text:
                return text
            marker_index = engine_data.find(marker, max(close_index, open_index + 1))
    return None


def extract_engine_data_text_style(engine_data: str) -> dict[str, Any] | None:
    style: dict[str, Any] = {}
    font = extract_engine_data_parenthesized_value(engine_data, "/Font")
    color = extract_engine_data_parenthesized_value(engine_data, "/FillColor")
    font_size = extract_engine_data_numeric_value(engine_data, "/FontSize")
    if font:
        style["font"] = font
    if font_size is not None:
        style["font_size"] = int(font_size) if font_size.is_integer() else font_size
    if color:
        style["fill_color"] = color
    return style or None


def extract_engine_data_parenthesized_value(engine_data: str, marker: str) -> str | None:
    for marker_index in find_engine_data_marker_positions(engine_data, marker):
        open_index = engine_data.find("(", marker_index + len(marker))
        if open_index != -1:
            text, _ = read_parenthesized_text(engine_data, open_index)
            return text
    return None


def extract_engine_data_numeric_value(engine_data: str, marker: str) -> float | None:
    marker_positions = find_engine_data_marker_positions(engine_data, marker)
    if not marker_positions:
        return None
    marker_index = marker_positions[0]
    cursor = marker_index + len(marker)
    while cursor < len(engine_data) and engine_data[cursor].isspace():
        cursor += 1
    end = cursor
    while end < len(engine_data) and (engine_data[end].isdigit() or engine_data[end] in ".-"):
        end += 1
    try:
        return float(engine_data[cursor:end])
    except ValueError:
        return None


def find_engine_data_marker_positions(engine_data: str, marker: str) -> list[int]:
    positions: list[int] = []
    marker_index = engine_data.find(marker)
    while marker_index != -1:
        next_index = marker_index + len(marker)
        if next_index >= len(engine_data) or not (engine_data[next_index].isalnum() or engine_data[next_index] == "_"):
            positions.append(marker_index)
        marker_index = engine_data.find(marker, marker_index + 1)
    return positions


def read_parenthesized_text(value: str, open_index: int) -> tuple[str | None, int]:
    text: list[str] = []
    escaped = False
    cursor = open_index + 1
    while cursor < len(value):
        char = value[cursor]
        if escaped:
            text.append({"n": "\n", "r": "\r", "t": "\t"}.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ")":
            return "".join(text), cursor
        else:
            text.append(char)
        cursor += 1
    return None, cursor


def read_uint(data: bytes) -> int:
    return int.from_bytes(data, "big") if data else 0


def psd_color_mode_name(color_mode_id: int) -> str:
    return {
        0: "bitmap",
        1: "grayscale",
        2: "indexed",
        3: "rgb",
        4: "cmyk",
        7: "multichannel",
        8: "duotone",
        9: "lab",
    }.get(color_mode_id, "unknown")


def build_design_document(project: dict[str, Any], payload: ProfessionalImportRequest) -> dict[str, Any]:
    return {
        "id": make_id("dld"),
        "project_id": project["id"],
        "source_type": payload.source_type,
        "file_name": payload.file_name,
        "frame_id": payload.frame_id,
        "parser": payload.parser,
        "binary_header": payload.binary_header,
        "preserved_layers": len(payload.layers),
        "layers": [layer.model_dump(exclude_none=True) for layer in payload.layers],
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
                **({"parser": document["parser"]} if document.get("parser") else {}),
            },
        }
        if layer.get("text"):
            node["text"] = {
                "content": layer["text"],
                **({"style": layer["text_style"]} if layer.get("text_style") else {}),
            }
        if layer.get("component_key"):
            node["component"] = {"key": layer["component_key"]}
        if layer.get("image_asset_id"):
            node["professional_source"]["image_asset_id"] = layer["image_asset_id"]
            node["source_asset_id"] = layer["image_asset_id"]
        if layer.get("image_url"):
            node["professional_source"]["image_url"] = layer["image_url"]
        if layer.get("auto_layout") or layer.get("constraints"):
            node["layout"] = {
                **({"auto_layout": layer["auto_layout"]} if layer.get("auto_layout") else {}),
                **({"constraints": layer["constraints"]} if layer.get("constraints") else {}),
            }
        if layer.get("opacity") is not None:
            node["opacity"] = layer["opacity"]
        if layer.get("visible") is not None:
            node["visible"] = layer["visible"]
        if layer.get("parent_id"):
            node["parent_id"] = layer["parent_id"]
        if layer.get("group_path"):
            node["professional_source"]["group_path"] = layer["group_path"]
        if layer.get("is_group") is not None:
            node["professional_source"]["is_group"] = layer["is_group"]
        if layer.get("smart_object") is not None:
            node["professional_source"]["smart_object"] = layer["smart_object"]
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
            **({"parser": document["parser"]} if document.get("parser") else {}),
            **({"binary_header": document["binary_header"]} if document.get("binary_header") else {}),
        },
        "nodes": nodes,
    }


def layer_type_to_node_type(layer: dict[str, Any]) -> str:
    name = layer["name"].lower()
    if layer["kind"] == "text":
        return "text"
    if layer["kind"] == "group":
        return "group"
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
            "professional_source": build_manifest_professional_source(ir),
            "asset_ir": build_manifest_asset_ir_summary(ir),
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


def build_manifest_professional_source(ir: dict[str, Any]) -> dict[str, Any]:
    source = ir.get("professional_source") or {}
    source_type = source.get("source_type", "")
    preserved_layers = sum(
        1
        for node in ir.get("nodes", [])
        if node.get("professional_source", {}).get("source_type") == source_type
    )
    return {
        "source_type": source_type,
        "file_name": source.get("file_name", ""),
        "frame_id": source.get("frame_id"),
        "design_document_id": source.get("design_document_id", ""),
        "preserved_layers": preserved_layers,
    }


def build_manifest_asset_ir_summary(ir: dict[str, Any]) -> dict[str, Any]:
    source = ir.get("source_asset", {})
    nodes = [
        {
            "id": node["id"],
            "type": node["type"],
            "name": node["name"],
            "rect": node["rect"],
            **({"segmentation_source": node["segmentation_source"]} if node.get("segmentation_source") else {}),
        }
        for node in ir.get("nodes", [])
        if node.get("type") != "canvas"
    ]
    return {
        "id": ir["id"],
        "version": ir.get("version", ""),
        "node_count": len(ir.get("nodes", [])),
        "engine_targets": ir.get("engine_targets", []),
        **({"segmentation_source": source["segmentation_source"]} if source.get("segmentation_source") else {}),
        **(
            {"layered_slice_count": sum(1 for node in nodes if node.get("segmentation_source") == "qwen-layered-slice")}
            if source.get("segmentation_source") == "qwen-layered-slice"
            else {}
        ),
        "nodes": nodes,
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
        "professional_source": build_manifest_professional_source(ir),
        "asset_ir": build_manifest_asset_ir_summary(ir),
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
