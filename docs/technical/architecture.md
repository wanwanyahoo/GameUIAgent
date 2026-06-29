# 技术架构文档

## 1. 架构目标

技术架构需要同时支撑两类目标：

- 官网复刻：提供高质量深色科技风 Landing Page、产品页、定价页、文档入口和登录注册入口。
- AI 游戏资产生产平台：提供 Web AI Studio、AI 任务、UI 切分、资产管理、多引擎导出和插件导入能力。

第一版采用「快速大 Demo」路径，但需要保留模块边界，避免后续扩展 Unity/Cocos/Godot 时推倒重来。

## 2. 总体架构

```text
Browser
  ├─ Marketing Site
  ├─ Auth Pages
  └─ AI Studio Web App
       │
       ▼
Backend API
  ├─ User / Team / Project API
  ├─ Asset API
  ├─ Professional Import API
  ├─ AI Job API
  ├─ Segmentation API
  ├─ Export API
  ├─ Plugin API
  ├─ Developer API
  └─ Billing API
       │
       ├──────────────► Professional Design Importers
       │                 ├─ PSD Parser
       │                 ├─ Figma Importer
       │                 ├─ Design Layer Document
       │                 └─ IR Builder
       │
       ├──────────────► Cloud AI Providers
       │                 ├─ Text-to-Image
       │                 ├─ Image-to-Image
       │                 ├─ Inpainting
       │                 ├─ Matting
       │                 └─ Upscale
       │
       ├──────────────► Object Storage
       │                 ├─ Original Assets
       │                 ├─ Generated Images
       │                 ├─ Slices
       │                 └─ Export Packages
       │
       ├──────────────► Database
       │                 ├─ Users
       │                 ├─ Projects
       │                 ├─ Assets
       │                 ├─ Jobs
       │                 ├─ IR Documents
       │                 └─ Export Records
       │
       └──────────────► Engine Exporters
                         ├─ Unity Exporter
                         ├─ Cocos 3.x Exporter
                         ├─ Cocos 2.x Exporter
                         └─ Godot Exporter

Engine Editors
  ├─ Unity Editor Plugin
  ├─ Cocos Creator Extension
  └─ Godot EditorPlugin
       │
       ▼
Plugin API / Export Packages
```

## 3. 推荐技术栈

### 3.1 前端

- React
- TypeScript
- Vite 或 Next.js
- Tailwind CSS 或 CSS Modules
- Canvas/SVG 编辑层
- Zustand 或 Redux Toolkit
- TanStack Query
- React Router 或 Next Router

### 3.2 后端

- Python FastAPI 或 Node.js NestJS
- PostgreSQL
- Redis
- 对象存储：S3/R2/火山 TOS/阿里 OSS
- 异步任务：Celery/RQ/BullMQ
- WebSocket/SSE 任务进度

### 3.3 AI 服务

- 云 API 优先
- 模型适配层统一封装
- 每种能力通过 provider adapter 接入
- 保留 ComfyUI、自部署 SDXL、自研模型的扩展点

### 3.4 引擎插件

- Unity：C# EditorWindow + UnityWebRequest + AssetDatabase + PrefabUtility
- Cocos 3.x：Editor Extension + TypeScript/JavaScript
- Cocos 2.x：Editor Package + JavaScript
- Godot：GDScript 或 C# EditorPlugin

## 4. 前端模块

### 4.1 Marketing Site

负责官网复刻：

- `HomePage`
- `ProductMenu`
- `HeroSection`
- `WorkflowSection`
- `MattingSection`
- `StudioSection`
- `EngineMcpSection`
- `FinalCtaSection`
- `Footer`

### 4.2 Auth App

- 登录
- 注册
- 密码重置
- 插件 Token 登录

### 4.3 Workspace App

- 项目列表
- 项目详情
- 最近任务
- 团队空间
- 资产库
- 导出中心

### 4.4 AI Studio App

- `CanvasViewport`
- `AssetPanel`
- `LayerTree`
- `GenerationPanel`
- `SegmentationEditor`
- `PropertyInspector`
- `TaskTimeline`
- `ExportPanel`

### 4.5 插件连接 UI

- 插件状态
- 已连接设备
- Token 管理
- 导入日志

## 5. 后端模块

### 5.1 Auth Service

- 用户注册
- 用户登录
- Session/JWT
- 团队权限
- 插件 Token

### 5.2 Project Service

- 项目 CRUD
- 项目配置
- 团队成员权限
- 默认引擎和导出配置

### 5.3 Asset Service

- 上传素材
- 存储元数据
- 生成预览图
- 管理版本
- 提供下载签名 URL

### 5.4 AI Job Service

- 创建任务
- 调用云 AI API
- 轮询或接收回调
- 写入任务结果
- 任务失败重试
- 任务进度推送

### 5.5 Professional Import Service

- 处理 PSD 文件上传。
- 处理 PSB 文件上传。
- 处理 Figma 文件链接和 Node 导入。
- 解析 PSD 图层组、图片图层、文本图层、智能对象和图层元数据。
- 解析 Figma Frame、Group、Component、Instance、Auto Layout、Constraints、Text 和图片 Fill。
- 生成 Design Layer Document。
- 将 Design Layer Document 转换为资产 IR。
- 对缺失结构的扁平图层调用 AI 切分补全。

### 5.6 Segmentation Service

- 接收图片资产
- 运行 UI 元素检测
- 生成切片
- 生成图层树
- 生成初版资产 IR
- 支持人工修正后的 IR 保存

### 5.7 Export Service

- 接收资产 IR
- 选择目标引擎
- 调用对应 exporter
- 生成导出包
- 写入导出记录
- 提供插件拉取接口

### 5.8 Plugin Service

- 插件认证
- 查询项目
- 查询导出任务
- 下载导出包
- 回写导入状态
- 上传引擎侧日志
- 上传 Engine Snapshot
- 将引擎 Scene/Prefab 反向转换为资产 IR

### 5.9 Developer API Service

- API Key 管理。
- AI Super Matting Execute API。
- Task Poll API。
- Task Cancel API。
- Cost Estimate API。
- Webhook 回调。
- HMAC-SHA256 webhook 签名。
- Rate Limit Header。
- Error Code 标准化。

### 5.10 Billing Service

- 订阅计划。
- Daily Free Credits。
- Monthly Credits。
- Purchased Credits。
- 积分扣除优先级。
- 并发任务限制。
- 云项目和本地项目额度。
- 自动续费。
- 升级和降级规则。
- Stripe 支付集成。
- 加密热备份快照策略。

## 6. 数据存储

### 6.1 PostgreSQL

核心结构化数据：

- users
- teams
- memberships
- projects
- assets
- ai_jobs
- segmentation_jobs
- ir_documents
- export_jobs
- plugin_tokens
- plugin_devices
- import_logs

### 6.2 Redis

- 任务队列
- 任务锁
- 任务进度
- 短期缓存
- 限流计数

### 6.3 Object Storage

- 上传原图
- AI 生成图
- 切片图
- Alpha PNG
- IR JSON
- 导出包
- 日志文件

## 7. 核心数据流

### 7.1 文生图到 Unity 导入

1. 前端提交 Prompt。
2. Backend 创建 `ai_job`。
3. Worker 调用云 AI API。
4. 生成图写入对象存储。
5. 前端展示结果。
6. 用户选择结果并触发切分。
7. Segmentation Service 生成切片和 IR。
8. 用户修正 IR。
9. Export Service 生成 Unity 包。
10. Unity 插件查询导出任务。
11. 插件下载包并导入。
12. 插件回写导入状态。

### 7.2 图片上传到多引擎导出

1. 用户上传图片。
2. Asset Service 保存原图。
3. 用户触发抠图或图生图。
4. AI Job Service 生成处理结果。
5. Segmentation Service 切分 UI。
6. IR 文档保存。
7. Export Service 根据目标引擎导出。
8. 对应插件导入。

## 8. API 分组

### 8.1 Auth API

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/plugin-token`

### 8.2 Project API

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PATCH /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`

### 8.3 Asset API

- `POST /api/projects/{project_id}/assets`
- `GET /api/projects/{project_id}/assets`
- `GET /api/assets/{asset_id}`
- `DELETE /api/assets/{asset_id}`

### 8.4 AI Job API

- `POST /api/projects/{project_id}/ai/text-to-image`
- `POST /api/projects/{project_id}/ai/image-to-image`
- `POST /api/projects/{project_id}/ai/inpaint`
- `POST /api/projects/{project_id}/ai/matting`
- `POST /api/projects/{project_id}/ai/upscale`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/cancel`

### 8.5 Professional Import API

- `POST /api/projects/{project_id}/imports/psd`
- `POST /api/projects/{project_id}/imports/figma`
- `GET /api/import-jobs/{import_job_id}`
- `GET /api/design-documents/{design_document_id}`
- `POST /api/design-documents/{design_document_id}/build-ir`

### 8.6 Segmentation API

- `POST /api/projects/{project_id}/segment`
- `GET /api/segment-jobs/{job_id}`
- `GET /api/ir/{ir_id}`
- `PATCH /api/ir/{ir_id}`

### 8.7 Export API

- `POST /api/projects/{project_id}/exports`
- `GET /api/exports/{export_id}`
- `GET /api/exports/{export_id}/download`

### 8.8 Plugin API

- `POST /api/plugin/auth`
- `GET /api/plugin/projects`
- `GET /api/plugin/projects/{project_id}/exports`
- `GET /api/plugin/exports/{export_id}/download`
- `POST /api/plugin/import-logs`
- `POST /api/plugin/engine-snapshots`
- `POST /api/plugin/engine-snapshots/{snapshot_id}/build-ir`

### 8.9 Developer API

- `POST /api/ai/services/super-matting/execute`
- `GET /api/ai/tasks/{task_id}`
- `POST /api/ai/tasks/{task_id}/cancel`
- `POST /api/ai/services/super-matting/cost`
- `GET /api/user/api-keys`
- `POST /api/user/api-keys`
- `DELETE /api/user/api-keys/{key_id}`

### 8.10 Billing API

- `GET /api/billing/plans`
- `GET /api/billing/credits`
- `GET /api/billing/subscription`
- `POST /api/billing/checkout`
- `POST /api/billing/cancel-auto-renew`
- `POST /api/billing/upgrade`

## 9. 任务状态模型

所有异步任务使用统一状态：

- `queued`
- `running`
- `waiting_provider`
- `succeeded`
- `failed`
- `cancelled`

任务必须包含：

- `id`
- `type`
- `project_id`
- `created_by`
- `status`
- `progress`
- `input`
- `output`
- `error`
- `created_at`
- `updated_at`

## 10. 扩展原则

### 10.1 统一资产 IR

所有 AI 切分结果和导出器都围绕统一资产 IR，不直接把 Web 画布状态写死到 Unity/Cocos/Godot。

### 10.2 Provider Adapter

AI 云 API 不直接散落在业务代码中，统一通过 provider adapter 调用。

### 10.3 Exporter Adapter

每个引擎一个 exporter，输入同一 IR，输出目标引擎包。

### 10.4 Plugin Protocol

所有引擎插件使用统一插件 API，只在本地导入逻辑不同。

## 11. 安全

- 插件 Token 最小权限。
- 下载 URL 使用短期签名。
- AI API Key 仅后端保存。
- 项目资源按团队隔离。
- 任务输入输出需要权限校验。
- 用户上传文件需要类型和大小限制。

## 12. 性能

- 大图上传使用分片或直传对象存储。
- 生成任务异步处理。
- 画布编辑使用局部状态更新。
- 切片图使用缩略图预览。
- 导出包生成后缓存。
- 插件下载支持断点或重试。

## 13. 可观测性

- API 日志
- AI Provider 调用日志
- 任务耗时
- 导出耗时
- 插件导入日志
- 失败原因聚合
- 用户操作审计

## 14. 部署形态

### 14.1 Demo 形态

- 单前端应用
- 单后端 API
- 单 Worker
- PostgreSQL
- Redis
- 对象存储

### 14.2 平台化形态

- Marketing 独立部署
- App 独立部署
- API Gateway
- Auth Service
- Asset Service
- AI Job Service
- Export Service
- Plugin Service
- 多 Worker 队列
