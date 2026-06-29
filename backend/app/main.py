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


store: dict[str, Any] = {
    "users": {},
    "tokens": {},
    "projects": {},
    "assets": {},
    "jobs": {},
    "irs": {},
    "exports": {},
    "snapshots": {},
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
        "package": build_export_package(project, payload.target_engine),
    }
    store["exports"][export["id"]] = export
    return export


@app.get("/api/plugin/export-jobs")
def plugin_export_jobs(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    owned_projects = {
        project["id"] for project in store["projects"].values() if project["owner_id"] == user["id"]
    }
    jobs = [export for export in store["exports"].values() if export["project_id"] in owned_projects]
    return {"jobs": jobs}


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
        "preserved_bindings": preserved_bindings,
        "replacements": [
            {
                "source": sprite["path"],
                "target": sprite["path"].replace(".png", f".{payload.theme_name}.png"),
                "role": sprite.get("role", "image"),
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


def build_export_package(project: dict[str, Any], target_engine: str) -> dict[str, Any]:
    slug = safe_slug(project["name"])
    if target_engine == "unity":
        return {
            "kind": "unity_package",
            "files": [
                f"Assets/GameUIAgent/Textures/{slug}_atlas.png",
                f"Assets/GameUIAgent/Prefabs/{slug}.prefab",
                f"Assets/GameUIAgent/Scenes/{slug}.unity",
                f"Assets/GameUIAgent/Manifests/{slug}.json",
            ],
        }
    return {
        "kind": f"{target_engine}_package",
        "files": [f"exports/{target_engine}/{slug}/manifest.json"],
    }


def safe_slug(value: str) -> str:
    words = sub(r"[^A-Za-z0-9]+", " ", value).strip().split()
    slug = "".join(word.capitalize() for word in words)
    return slug or "GameUi"
