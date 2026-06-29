# AI Pipeline 技术方案

## 1. 目标

AI Pipeline 负责将文本、图片和设计素材转换为可编辑、可切分、可导出的游戏 UI 资产。

第一阶段使用云 API 优先，统一封装 provider adapter，后续可扩展 ComfyUI、自部署模型和自研服务。

## 2. 能力范围

- 文生图
- 图生图
- 局部重绘
- 抠图
- 超分
- 风格迁移
- 异步任务 webhook
- 任务轮询
- 任务取消
- 成本预估
- API Key 调用
- UI 元素检测
- UI 自动切分
- 图层树生成
- 命名与组件推断
- 资产 IR 生成

## 3. 总体流程

```text
Input
  ├─ Prompt
  ├─ Reference Image
  ├─ Uploaded UI Screenshot
  ├─ PSD/Figma Layered Design
  └─ Existing Game Assets
        │
        ▼
Input Router
  ├─ AI Job API
  └─ Professional Import API
        │
        ▼
Job Queue
        │
        ▼
Provider Adapter
  ├─ Text-to-Image
  ├─ Image-to-Image
  ├─ Inpainting
  ├─ Matting
  └─ Upscale
        │
        ▼
Generated Assets
        │
        ▼
Segmentation Pipeline
  ├─ Element Detection
  ├─ Slice Extraction
  ├─ OCR / Text Region
  ├─ Component Inference
  ├─ Layout Inference
  └─ IR Generation
        │
        ▼
AI Studio Review
        │
        ▼
Export Pipeline
```

PSD/Figma 输入优先进入 Professional Import API，保留已有图层结构；Prompt、参考图、扁平截图进入 AI Job API 和 Segmentation Pipeline。

## 4. 任务类型

### 4.1 Text To Image

输入：

- Prompt
- Negative Prompt
- Style
- Width
- Height
- Seed
- Count
- Model

输出：

- 生成图片列表
- Seed
- Provider metadata
- Cost
- Safety result

### 4.2 Image To Image

输入：

- Source image
- Prompt
- Denoise strength
- Style
- Preserve composition
- Count

输出：

- 变体图片列表
- 与原图关系
- Provider metadata

### 4.3 Inpainting

输入：

- Source image
- Mask
- Prompt
- Edge feather
- Strength

输出：

- 重绘图片
- Mask metadata

### 4.4 Matting

输入：

- Source image
- Mode：person、object、ui、auto
- Edge refinement

输出：

- Alpha PNG
- Matte mask
- Preview image

### 4.5 Upscale

输入：

- Source image
- Scale：2x、4x
- Denoise
- Sharpen

输出：

- Upscaled image
- Scale metadata

### 4.6 UI Segmentation

输入：

- Source image
- Optional design type
- Optional target engine
- Optional naming rules

输出：

- Slice images
- Element boxes
- Layer tree
- Draft IR
- Confidence scores

### 4.7 Professional UI Import

输入：

- PSD file 或 Figma file URL
- Figma node id
- Target engine
- Import options

输出：

- Design Layer Document
- Extracted image assets
- Text layers
- Component metadata
- Draft IR
- Import warnings

## 5. Provider Adapter

### 5.1 Adapter 接口

```ts
interface AiProviderAdapter {
  name: string;
  capabilities: AiCapability[];
  submit(job: AiJobInput): Promise<ProviderJobRef>;
  poll(ref: ProviderJobRef): Promise<ProviderJobStatus>;
  cancel(ref: ProviderJobRef): Promise<void>;
  estimateCost(input: AiJobInput): Promise<CreditEstimate>;
  normalize(result: ProviderResult): Promise<AiJobOutput>;
}
```

### 5.2 Capability

- `text_to_image`
- `image_to_image`
- `inpainting`
- `matting`
- `upscale`
- `segmentation`

### 5.3 云 API 优先策略

- 产品层不绑定具体供应商。
- 每个任务根据能力、成本、速度、质量选择 provider。
- 任务记录保存 provider 和模型版本，便于复现。
- Provider 失败时支持 fallback。

## 6. Job 数据模型

```json
{
  "id": "job_001",
  "project_id": "project_001",
  "type": "text_to_image",
  "status": "running",
  "progress": 45,
  "input": {},
  "output": {},
  "provider": {
    "name": "cloud_provider",
    "model": "model_name",
    "job_ref": "remote_job_id"
  },
  "cost": {
    "credits": 10,
    "estimated_usd": 0.12
  },
  "error": null,
  "created_at": "2026-06-29T00:00:00Z",
  "updated_at": "2026-06-29T00:00:30Z"
}
```

## 7. 状态机

```text
queued
  └─► running
        ├─► waiting_provider
        │     ├─► running
        │     └─► failed
        ├─► succeeded
        ├─► failed
        └─► cancelled
```

## 8. UI 自动切分 Pipeline

UI 自动切分主要用于扁平图片、AI 生成图、上传截图或 PSD/Figma 中缺失结构的局部图层。对于 PSD/Figma 已有分层，优先使用专业 UI 工具导入链路生成 IR。

### 8.1 输入预处理

- 格式转换为 PNG。
- 生成缩略图。
- 记录原图尺寸。
- 标准化透明通道。
- 对超大图进行分块或缩放检测。

### 8.2 元素检测

检测目标：

- 背景
- 大面板
- 按钮
- 图标
- 文本区域
- 装饰元素
- 头像/角色
- 进度条
- 输入框
- 列表项

输出：

```json
{
  "box": { "x": 100, "y": 200, "width": 320, "height": 90 },
  "type": "button",
  "confidence": 0.91,
  "suggested_name": "start_button"
}
```

### 8.3 切片提取

- 根据检测框裁剪图片。
- 保留 Alpha。
- 对边缘扩展 padding。
- 生成唯一 asset id。
- 写入对象存储。

### 8.4 OCR 与文本处理

- 识别文本区域。
- 文本内容作为占位。
- 若无法识别，生成 `Text_001`。
- 导出时映射为引擎文本组件。

### 8.5 组件推断

推断规则：

- 图标 + 文本 + 背景框 → Button。
- 背景框 + 多个同类子项 → List。
- 条形背景 + 填充区域 → ProgressBar。
- 多个相似区域重复 → ListItem Component。

### 8.6 布局推断

- 根据元素位置推断锚点。
- 根据画布边距推断 stretch。
- 根据重复项推断列表方向。
- 根据宽高比推断九宫格候选。

### 8.7 IR 生成

- 生成 Asset 列表。
- 生成 Node 树。
- 生成 Component。
- 写入 confidence。
- 标记需要人工确认的字段。

## 9. 人工修正闭环

AI 切分不是最终结果，用户必须能修正：

- 调整切片框。
- 合并/拆分元素。
- 修改元素类型。
- 修改名称。
- 修改层级。
- 修改锚点。
- 设置九宫格。
- 绑定按钮状态。
- 保存为新 IR 版本。

## 10. 质量策略

### 10.1 多候选

文生图和图生图默认生成多候选，用户选择后进入切分。

### 10.2 置信度

切分结果必须带置信度：

- 高置信度：直接进入 IR。
- 中置信度：进入 IR，但标记待确认。
- 低置信度：只作为候选框，不导出。

### 10.3 可回退

每次 AI 操作都生成版本，用户可回退到上一个结果。

### 10.4 人工优先

用户修正后的字段优先级高于 AI 再识别结果。

## 11. 成本与限流

- 每个任务估算 credits。
- 提交前显示预估消耗。
- 免费版限制并发和生成次数。
- Pro/Team 提升并发和额度。
- Provider 超时自动失败或 fallback。

## 12. 错误处理

### 12.1 AI Provider 错误

- 超时
- 限流
- 内容安全拒绝
- 模型不可用
- 返回格式异常

处理：

- 保存错误码。
- 展示用户可读消息。
- 支持重试。
- 必要时 fallback provider。

### 12.2 切分错误

- 无法识别元素。
- 切片为空。
- 原图尺寸过大。
- Alpha 处理失败。

处理：

- 返回部分结果。
- 提供手动切分模式。
- 标记失败元素。

## 13. 前端体验

### 13.1 任务提交

- 用户填写参数。
- 前端显示预估时间和 credits。
- 点击生成。
- 任务进入底部 Task Timeline。

### 13.2 任务进度

- SSE 或 WebSocket 推送。
- 展示状态、百分比、当前步骤。
- 支持取消。

### 13.3 结果处理

- 结果进入资产库。
- 用户可收藏、删除、再次编辑。
- 可一键进入切分。

## 14. 未来扩展

- ComfyUI 工作流适配器。
- 自部署 SDXL。
- 自定义 LoRA。
- 团队风格库。
- 项目级风格一致性。
- 动画帧生成。
- Spine/DragonBones 资产辅助生成。
- 3D 图标和材质生成。

## 15. Developer API 补充协议

开发者 API 使用 API Key 鉴权，适合外部系统直接调用 VberAI AI 服务。该协议优先覆盖 AI Super Matting，并可复用到后续文生图、图生图和局部重绘 API。

### 15.1 API Key

```http
X-API-Key: your_api_key_here
```

### 15.2 Execute

```http
POST /api/ai/services/super-matting/execute
```

输入：

- `input.imageSource`：`url` 或 `base64`。
- `input.imageValue`：图片 URL 或 Base64。
- `input.width`：64-2048。
- `input.height`：64-2048。
- `input.seed`：可选。
- `options.webhookUrl`：API Key 调用时必填。
- `options.webhookSecret`：可选，HMAC-SHA256 签名。

返回 `202 Accepted`，包含 `taskId`、`status` 和 `estimatedCredits`。

### 15.3 Webhook

任务完成后回调 `webhookUrl`。成功结果必须包含：

- `taskId`
- `serviceCode`
- `status`
- `outputs.alpha_mask.url`
- `outputs.final_image.url`

如果传入 `webhookSecret`，回调 Header 需要包含：

```http
X-Webhook-Signature: hmac_sha256_signature
```

### 15.4 Poll / Cancel / Cost

- `GET /api/ai/tasks/{taskId}`：查询任务状态和结果。
- `POST /api/ai/tasks/{taskId}/cancel`：取消未完成任务。
- `POST /api/ai/services/super-matting/cost`：按输出尺寸预估积分消耗。

任务状态：

- `pending`
- `submitted`
- `queued`
- `processing`
- `completed`
- `failed`
- `cancelled`

### 15.5 Rate Limit

响应 Header：

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

### 15.6 Credits

Super Matting 按最大边消耗积分：

- 512px 以内：2 credits。
- 513-768px：5 credits。
- 769-1024px：10 credits。
- 1025-1536px：15 credits。
- 1537-2048px：30 credits。

任务创建时扣除 credits，任务失败时按规则退还。
