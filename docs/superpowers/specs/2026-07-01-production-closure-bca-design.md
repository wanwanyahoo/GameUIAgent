# GameUIAgent 生产闭环 B-C-A 推进设计

## 1. 背景

GameUIAgent 已经具备基础闭环：

- Unity/Cocos/Godot/Unreal 导出包、插件 manifest/download、插件导入日志回写、Studio timeline 展示已连通。
- PSD/Figma/图片导入到 Asset IR、多引擎导出已有基础链路。
- 文生图、参考图、Qwen layered slice、拆图到 IR、导出已有基础链路。
- 生产支付网关暂缓，不纳入本设计的近期实现范围。

用户明确要求剩余能力都达到生产闭环，并指定执行顺序为 `B -> C -> A`：

- `B`：真实编辑器闭环。
- `C`：真实引擎插件/MCP 深闭环。
- `A`：AI 队列、Provider Adapter、Qwen 异步与拆图生产化。

## 2. 总体目标

### 2.1 必须实现

- Studio 能真实编辑 Asset IR，而不是只展示占位状态。
- 用户能在画布和 Layer Tree 中选择节点、修改属性、保存为 IR 版本并回滚。
- 引擎插件/MCP 不只下载包，还能上传引擎快照、构建 IR、发起 restyle job、查询状态、下载 replacement manifest 并回写导入日志。
- AI 任务系统具备可靠队列、Provider Adapter、Qwen 异步任务、取消、轮询、重试、fallback 和错误归一化。
- 拆图结果能产出真实 slice assets，包含置信度、OCR/组件推断、九宫格候选、人工确认状态和导出门禁。
- 每个阶段都必须有 RED-GREEN-REFACTOR 测试闭环、全量回归、提交和推送。

### 2.2 暂不实现

- 不推进生产支付网关、支付 webhook、真实 Stripe/PayPal/Alipay/Wechat 验签。
- 不依赖真实 Unity/Cocos/Godot/Unreal 编辑器运行环境做自动化 E2E；本阶段以插件协议、MCP API、manifest、import log 和模拟插件客户端测试作为可重复验收。
- 不引入重量级外部服务作为强依赖；需要外部 AI 能力时必须保留 local deterministic/fake provider 测试路径。

## 3. 执行顺序

### 3.1 Phase B：真实编辑器闭环

目标是让 Studio 成为 Asset IR 的真实编辑器。

核心能力：

- IR 读取：从最新 project IR 或指定 IR version 加载节点树。
- Layer Tree：按 `parent_id` / node hierarchy 展示层级、可见性、锁定状态、类型和名称。
- Canvas：支持节点选择、选中框、拖拽移动、缩放尺寸、键盘微调。
- Inspector：支持名称、类型、rect、visible、opacity、text、layout hints、nine-slice、component role 等属性编辑。
- IR Patch：前端提交结构化 patch，后端校验权限、节点存在、字段合法性和冲突版本。
- Versioning：每次保存生成 IR version，记录 author、base version、patch summary，可查询、回滚。
- Undo/Redo：前端本地维护操作栈；保存后以后端版本为准。
- Export Gate：存在未确认低置信度节点、非法 rect、缺失 asset 引用时，导出返回可读错误。

后端新增/强化接口：

- `GET /api/projects/{project_id}/irs/{ir_id}`：读取 IR。
- `GET /api/projects/{project_id}/irs/{ir_id}/versions`：列出版本。
- `POST /api/projects/{project_id}/irs/{ir_id}/patches`：提交编辑 patch 并生成新版本。
- `POST /api/projects/{project_id}/irs/{ir_id}/versions/{version_id}/restore`：回滚版本。
- `POST /api/projects/{project_id}/irs/{ir_id}/validate`：导出前校验。

验收标准：

- 从 PSD/Figma/Qwen layered slices 生成的 IR 都能进入同一编辑器。
- 修改节点位置、文本、可见性、九宫格后，刷新页面仍保留。
- 导出包 manifest 使用最新 IR 版本内容。
- 版本回滚后导出恢复到旧内容。

## 4. Phase C：引擎插件/MCP 深闭环

目标是让 Unity/Cocos/Godot/Unreal 与 Studio 形成双向生产闭环。

核心能力：

- Plugin Session：插件获取 scope 化 token，包含 engine、device、project、过期时间。
- Engine Snapshot：插件上传当前场景/UI 层级、资产引用、组件属性、截图和诊断。
- Build IR：后端从 engine snapshot 构建 editable Asset IR，进入 Studio 编辑器。
- Restyle Job：基于 snapshot + style prompt/reference asset 创建换风格任务。
- Replacement Manifest：生成替换计划，包含保留布局、替换纹理、更新文本/组件、冲突列表。
- Plugin Pull：插件查询 restyle/export job，下载 manifest/ZIP。
- Import Log：插件回写每一步导入结果，Studio timeline 实时展示成功、警告和错误。
- MCP Tool Catalog：为四个引擎提供统一 MCP 工具描述和 engine-specific operation plan。

后端新增/强化接口：

- `POST /api/auth/plugin-token`：签发 scope 化插件 token。
- `POST /api/projects/{project_id}/engine-snapshots/{snapshot_id}/build-ir`：从引擎快照构建 IR。
- `GET /api/plugin/restyle-jobs/{job_id}`：查询 restyle job。
- `GET /api/plugin/restyle-jobs/{job_id}/replacement-manifest`：下载 replacement manifest。
- `GET /api/plugin/mcp/tools`：返回当前引擎可用 MCP 工具。
- `POST /api/plugin/mcp/operations`：提交 MCP 操作执行结果。

验收标准：

- Unity/Cocos/Godot/Unreal 至少各有一条 snapshot -> build-ir -> edit -> export/restyle -> download -> import-log 的测试链路。
- 插件导入日志能映射到 Studio timeline，并显示 engine-specific metrics。
- 不支持的引擎操作返回明确错误，不生成伪成功。
- token 过期、scope 不匹配、项目不匹配会被拒绝。

## 5. Phase A：AI 队列、Provider 与拆图生产化

目标是让 AI 生成和拆图从“可演示”升级为可恢复、可观察、可降级的生产链路。

### 5.1 可靠队列

核心能力：

- Queue Item 使用结构化持久记录，不再依赖不可租约的 dict 状态。
- 原子 dequeue：同一任务不能被多个 worker 同时领取。
- Lease Timeout：worker 超时后任务可重试。
- Retry Backoff：失败按指数退避，超过最大次数进入 dead-letter。
- Idempotent Complete：重复 complete 不重复创建资产、不重复扣费。
- Cancellation：queued/running/waiting_provider 状态都可取消。

验收标准：

- 并发 worker 只能领取同一个 queued job 一次。
- lease 过期后 job 可被再次领取。
- provider 失败后按重试策略进入 retry 或 dead-letter。

### 5.2 Provider Adapter

统一接口：

```python
class AiProviderAdapter:
    name: str
    capabilities: list[str]
    def submit(self, job): ...
    def poll(self, provider_ref): ...
    def cancel(self, provider_ref): ...
    def normalize(self, provider_result): ...
    def estimate_cost(self, job): ...
```

Provider：

- `local-deterministic`：用于测试、离线 demo 和 fallback。
- `qwen`：真实 Qwen/DashScope 异步生成与 layered slice。
- `failing`：用于错误路径测试。

验收标准：

- 业务代码只依赖 Adapter，不直接写 `if provider == qwen` 的调用分支。
- provider 原始响应、标准化结果、耗时、错误码写入 `inference_runs`。
- provider 不可用时可按策略 fallback 到 local 或返回可读失败。

### 5.3 Qwen 异步闭环

核心能力：

- Submit：创建远端任务并保存 provider job ref。
- Poll：轮询状态，支持 queued/running/succeeded/failed/cancelled。
- Cancel：取消远端任务并同步本地状态。
- Normalize：下载图片，提取 layered_slices，保存原始响应摘要。
- Error Taxonomy：限流、内容安全、模型不可用、网络超时、格式异常分开处理。

验收标准：

- Qwen 异步任务从 submit 到 poll succeeded 后生成 asset。
- 用户取消后不会再生成结果资产。
- Qwen 返回 malformed layered_slices 时任务失败且记录标准错误。

### 5.4 拆图生产化

核心能力：

- 预处理：图片尺寸、格式、alpha、缩略图和安全校验。
- Slice Assets：根据检测框真实裁剪 PNG，写入对象存储。
- OCR/Text：文本区域生成 text node，并保留识别置信度。
- Component Inference：按钮、列表、进度条、输入框等组件推断。
- Layout Inference：anchors、pivot、margin、nine-slice 候选。
- Human Review：低置信度节点必须标记 `requires_review=true`。
- Export Gate：未确认低置信度关键节点不能导出生产包。

验收标准：

- Qwen layered_slices 和普通上传图都能生成 slice assets。
- 每个 slice node 都有 bounds、asset_ref、confidence、editable state。
- 手动确认/修改后导出门禁解除。

## 6. 数据模型

新增或强化 store sections：

- `ir_versions`：IR 版本。
- `ir_patches`：编辑 patch 审计。
- `engine_snapshots`：引擎快照。
- `restyle_jobs`：引擎 restyle job。
- `provider_jobs`：AI provider 远端任务引用。
- `queue_leases` 或扩展 `ai_job_queue`：worker lease 状态。
- `slice_assets`：切片资产索引。

所有新增记录必须可持久化到现有 `ProductionStore`，并有测试覆盖 reload 后状态不丢失。

## 7. 错误处理

- 权限错误：返回 `401/403`，不泄露项目存在性。
- 版本冲突：返回 `409 IR_VERSION_CONFLICT`。
- 导出校验失败：返回 `422 EXPORT_VALIDATION_FAILED`，包含节点级 errors。
- Provider 失败：返回标准错误码，保留 provider 原始错误摘要。
- 队列失败：超过重试进入 dead-letter，用户可 retry。
- 插件失败：import log 必须展示失败阶段、engine、operation、error。

## 8. 测试策略

每个阶段必须先写失败测试：

- Phase B：IR patch、版本回滚、导出使用最新 IR、低置信度门禁。
- Phase C：四引擎 snapshot build-ir、scope token、replacement manifest、import log timeline。
- Phase A：并发 dequeue、lease timeout、Qwen submit/poll/cancel、slice asset 裁剪、export gate。

全量回归命令：

```bash
npm run build
npm test
python3 -m pytest backend/tests -q
git diff --check
```

## 9. 实现批次

### Batch B1：IR 编辑 API 与版本

- 后端 IR read/patch/version/restore/validate。
- 前端 API client 和测试。
- 导出使用最新 IR version。

### Batch B2：Studio 真实编辑器

- Layer Tree。
- Canvas selection and transform。
- Inspector。
- Undo/Redo。

### Batch C1：Plugin Token 与 Engine Snapshot Build IR

- Scope token。
- snapshot -> IR。
- 四引擎 fixture 测试。

### Batch C2：Restyle/Replacement/MCP

- restyle job 状态。
- replacement manifest。
- MCP tool catalog 和 operation result。

### Batch A1：可靠队列与 Provider Adapter

- lease/retry/dead-letter/idempotency。
- adapter 接口。
- local/qwen/failing provider。

### Batch A2：Qwen 异步与拆图生产化

- Qwen submit/poll/cancel。
- slice asset 裁剪。
- OCR/组件/布局推断基础版。
- 低置信度导出门禁。

## 10. 完成定义

- `B -> C -> A` 所有批次均有测试和提交。
- 从任一输入源进入 Studio：PSD/Figma/图片/Qwen/引擎快照。
- Studio 可编辑并保存 IR 版本。
- 可导出 Unity/Cocos/Godot/Unreal。
- 插件/MCP 可下载、导入、回写日志、回流快照。
- AI 任务可排队、异步、取消、重试、fallback。
- 拆图有真实 assets、置信度、人工确认和导出门禁。
