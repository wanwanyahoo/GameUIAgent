# 引擎插件通信协议

## 1. 目标

插件协议负责连接 Web 平台与 Unity、Cocos Creator、Godot 编辑器。

插件需要完成：

- 登录或 Token 认证。
- 查询用户项目。
- 查询导出任务。
- 下载导出包。
- 导入资产到本地工程。
- 回写导入状态和日志。
- 上报插件版本和引擎版本。
- 上传引擎场景/Prefab 快照。
- 将已有引擎项目反向回流为 AI Studio 可编辑画布。

## 2. 插件类型

### 2.1 Unity Plugin

- 形态：Unity EditorWindow。
- 语言：C#。
- 主要 API：UnityWebRequest、AssetDatabase、PrefabUtility、EditorSceneManager。

### 2.2 Cocos Creator Plugin

- 形态：Editor Extension。
- 语言：TypeScript/JavaScript。
- 支持：Cocos Creator 3.x 与 2.x 分开适配。

### 2.3 Godot Plugin

- 形态：EditorPlugin。
- 语言：GDScript 或 C#。
- 支持：Godot 4.x。

## 3. 认证方式

### 3.1 Token 认证

Web 端生成插件 Token，用户复制到插件。

```http
Authorization: Bearer plugin_token_xxx
```

### 3.2 设备绑定

插件首次认证后生成设备记录：

```json
{
  "device_id": "unity_editor_mac_001",
  "engine": "unity",
  "engine_version": "2022.3.40f1",
  "plugin_version": "0.1.0",
  "project_path_hash": "hash"
}
```

### 3.3 Token 权限

- 读取项目列表
- 读取导出任务
- 下载导出包
- 回写导入日志
- 不允许修改用户账号信息
- 不允许访问无权限团队项目

## 4. API 总览

### 4.1 插件认证

```http
POST /api/plugin/auth
```

请求：

```json
{
  "token": "plugin_token_xxx",
  "engine": "unity",
  "engine_version": "2022.3.40f1",
  "plugin_version": "0.1.0",
  "device_name": "MacBook Pro"
}
```

响应：

```json
{
  "access_token": "short_lived_token",
  "expires_in": 3600,
  "user": {
    "id": "user_001",
    "name": "Designer"
  },
  "team": {
    "id": "team_001",
    "name": "Game Team"
  }
}
```

### 4.2 查询项目

```http
GET /api/plugin/projects
```

响应：

```json
{
  "projects": [
    {
      "id": "project_001",
      "name": "RPG UI",
      "target_engines": ["unity", "cocos3", "godot"],
      "updated_at": "2026-06-29T00:00:00Z"
    }
  ]
}
```

### 4.3 查询导出任务

```http
GET /api/plugin/projects/{project_id}/exports?engine=unity
```

响应：

```json
{
  "exports": [
    {
      "id": "export_001",
      "engine": "unity",
      "status": "succeeded",
      "name": "inventory_ui_unity",
      "created_at": "2026-06-29T00:00:00Z",
      "manifest_url": "/api/plugin/exports/export_001/manifest"
    }
  ]
}
```

### 4.4 获取 Manifest

```http
GET /api/plugin/exports/{export_id}/manifest
```

响应：

```json
{
  "package_id": "export_001",
  "engine": "unity",
  "engine_version": "2022.3+",
  "entry": {
    "type": "prefab",
    "path": "Unity/Assets/VberAI/RPG/Prefabs/Inventory.prefab"
  },
  "download_url": "/api/plugin/exports/export_001/download",
  "checksum": "sha256"
}
```

### 4.5 下载导出包

```http
GET /api/plugin/exports/{export_id}/download
```

响应：

- `application/zip`
- 或重定向到短期签名 URL。

### 4.6 回写导入日志

```http
POST /api/plugin/import-logs
```

请求：

```json
{
  "export_id": "export_001",
  "engine": "unity",
  "status": "succeeded",
  "plugin_version": "0.1.0",
  "engine_version": "2022.3.40f1",
  "duration_ms": 3400,
  "summary": {
    "assets_imported": 42,
    "prefabs_created": 1,
    "scenes_created": 1,
    "warnings": 0,
    "errors": 0
  },
  "logs": [
    {
      "level": "info",
      "message": "Imported texture button_bg.png"
    }
  ]
}
```

### 4.7 上传 Engine Snapshot

```http
POST /api/plugin/engine-snapshots
```

请求：

```json
{
  "project_id": "project_001",
  "engine": "unity",
  "engine_version": "2022.3.40f1",
  "snapshot_type": "scene",
  "source_path": "Assets/Scenes/MainMenu.unity",
  "nodes": [],
  "assets": [],
  "components": [],
  "metadata": {
    "captured_by": "unity_plugin",
    "plugin_version": "0.1.0"
  }
}
```

响应：

```json
{
  "snapshot_id": "snapshot_001",
  "status": "uploaded"
}
```

### 4.8 Engine Snapshot 转 IR

```http
POST /api/plugin/engine-snapshots/{snapshot_id}/build-ir
```

响应：

```json
{
  "ir_id": "ir_from_engine_001",
  "design_document_id": "design_doc_from_engine_001",
  "status": "succeeded"
}
```

### 4.9 Unity UI 换风格任务

```http
POST /api/plugin/engine-snapshots/{snapshot_id}/restyle
```

请求：

```json
{
  "style_prompt": "cyberpunk neon sci-fi game ui",
  "reference_asset_id": "asset_style_ref",
  "preserve_layout": true,
  "text_strategy": "preserve_text",
  "replacement_strategy": "theme_variant",
  "theme_name": "cyberpunk"
}
```

响应：

```json
{
  "restyle_job_id": "restyle_001",
  "status": "queued"
}
```

### 4.10 Unity UI 换风格结果

```http
GET /api/plugin/restyle-jobs/{restyle_job_id}
```

响应：

```json
{
  "restyle_job_id": "restyle_001",
  "status": "succeeded",
  "manifest_url": "/api/plugin/restyle-jobs/restyle_001/manifest",
  "package_url": "/api/plugin/restyle-jobs/restyle_001/download"
}
```

## 5. 插件状态

插件本地状态：

- `unauthenticated`
- `authenticated`
- `project_selected`
- `downloading`
- `importing`
- `succeeded`
- `failed`

平台导入状态：

- `not_imported`
- `importing`
- `imported`
- `failed`

## 6. Unity 插件导入流程

```text
Open VberAI Window
  │
  ▼
Paste Token / Login
  │
  ▼
Fetch Projects
  │
  ▼
Select Project
  │
  ▼
Fetch Unity Exports
  │
  ▼
Download Package
  │
  ▼
Unzip Temp Folder
  │
  ▼
Copy Textures / Metadata
  │
  ▼
Configure TextureImporter
  │
  ▼
Build Prefab / Scene
  │
  ▼
Refresh AssetDatabase
  │
  ▼
Post Import Logs
```

## 7. Cocos 插件导入流程

```text
Open VberAI Panel
  │
  ▼
Authenticate
  │
  ▼
Fetch Project Exports
  │
  ▼
Download Cocos Package
  │
  ▼
Copy Assets
  │
  ▼
Generate / Refresh Meta
  │
  ▼
Create Prefab / Scene
  │
  ▼
Refresh Asset Database
  │
  ▼
Post Import Logs
```

## 8. Godot 插件导入流程

```text
Open VberAI Dock
  │
  ▼
Authenticate
  │
  ▼
Fetch Godot Exports
  │
  ▼
Download Package
  │
  ▼
Copy Files To res://vberai
  │
  ▼
Generate TSCN
  │
  ▼
Refresh FileSystem
  │
  ▼
Open Imported Scene
  │
  ▼
Post Import Logs
```

## 9. 引擎反向回流流程

```text
Select Scene / Prefab In Engine
  │
  ▼
Capture Node Tree / Components / Assets
  │
  ▼
Upload Engine Snapshot
  │
  ▼
Build Asset IR
  │
  ▼
Open As Editable Canvas In AI Studio
  │
  ▼
AI Notes / AI Chat Review
  │
  ▼
Export Back To Engine
```

## 10. Unity UI 换风格回写流程

```text
Select Unity UI Scene / Prefab
  │
  ▼
Export Layout JSON + Sprites
  │
  ▼
Upload Engine Snapshot
  │
  ▼
Generate Layout Preview Image
  │
  ▼
AI Restyle With Layout Preserved
  │
  ▼
Slice By Original Layout JSON
  │
  ▼
Download Replacement Manifest
  │
  ▼
Create Theme Variant Prefab / Replace Original Assets
```

## 11. 冲突处理协议

插件导入前检查冲突：

```json
{
  "conflicts": [
    {
      "type": "asset_exists",
      "path": "Assets/VberAI/RPG/button_bg.png",
      "recommended_action": "overwrite"
    }
  ]
}
```

支持策略：

- `overwrite`
- `skip`
- `rename`
- `create_version`
- `ask_user`

## 12. 插件 UI

### 12.1 连接页

- Token 输入框
- 连接按钮
- 当前账号
- 插件版本
- 引擎版本

### 12.2 项目页

- 项目列表
- 目标引擎标识
- 最近导出时间
- 刷新按钮

### 12.3 导入页

- 导出任务列表
- Manifest 预览
- 导入选项
- 冲突策略
- 导入按钮

### 12.4 日志页

- 进度条
- 导入日志
- 警告
- 错误
- 打开生成 Prefab/Scene

### 12.5 反向回流页

- 当前引擎场景列表。
- 当前选中 Prefab。
- 资源依赖预览。
- 上传 Engine Snapshot。
- 转换为 AI Studio 画布。
- 回流日志。

### 12.6 Unity UI 换风格页

- 选择 Unity Scene / Prefab。
- 导出 Layout JSON 和图片。
- 合成布局预览。
- 风格 Prompt。
- 风格参考图。
- 保持布局强度。
- 替换策略：新主题 Prefab / 原地替换。
- 下载 replacement manifest。
- 应用新主题。

## 13. 错误码

| 错误码 | 含义 |
| --- | --- |
| `PLUGIN_AUTH_FAILED` | Token 无效或过期 |
| `PROJECT_ACCESS_DENIED` | 无项目权限 |
| `EXPORT_NOT_FOUND` | 导出任务不存在 |
| `ENGINE_MISMATCH` | 导出包与当前引擎不匹配 |
| `PLUGIN_VERSION_UNSUPPORTED` | 插件版本过低 |
| `DOWNLOAD_FAILED` | 下载失败 |
| `PACKAGE_INVALID` | 导出包无效 |
| `IMPORT_FAILED` | 导入失败 |
| `ASSET_CONFLICT` | 资源冲突 |
| `SNAPSHOT_CAPTURE_FAILED` | 引擎快照采集失败 |
| `SNAPSHOT_TO_IR_FAILED` | 引擎快照转 IR 失败 |
| `RESTYLE_LAYOUT_FAILED` | UI 换风格布局合成失败 |
| `RESTYLE_SLICE_FAILED` | UI 换风格切回资源失败 |
| `RESTYLE_APPLY_FAILED` | Unity 新主题应用失败 |

## 14. 版本兼容

插件启动时上报：

- 插件版本
- 引擎类型
- 引擎版本
- 操作系统
- 项目路径 hash

服务端返回兼容策略：

```json
{
  "compatible": true,
  "min_plugin_version": "0.1.0",
  "latest_plugin_version": "0.2.0",
  "update_url": "https://example.com/download"
}
```

## 15. 安全要求

- 插件 Token 可撤销。
- Access Token 短期有效。
- 下载 URL 短期签名。
- 插件不能获取用户密码。
- 插件日志不能上传本地敏感路径全文。
- 项目路径只上传 hash。

## 16. MVP 范围

### 16.1 Unity MVP

- Token 登录。
- 项目列表。
- 导出任务列表。
- 下载 Unity ZIP。
- 导入 Texture。
- 创建 Prefab。
- 创建 Scene。
- 上传日志。
- 上传 Unity UI 快照。
- 执行 UI 换风格任务。
- 生成新主题 Prefab。

### 16.2 Cocos MVP

- Token 登录。
- 下载 Cocos ZIP。
- 复制资源。
- 创建基础 Prefab。
- 上传日志。

### 16.3 Godot MVP

- Token 登录。
- 下载 Godot ZIP。
- 复制资源。
- 创建 TSCN。
- 上传日志。
