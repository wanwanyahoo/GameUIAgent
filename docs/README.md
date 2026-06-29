# AI 游戏资产生产平台文档索引

## 文档目标

本目录用于完整规划「复刻官网 + AI 游戏资产生产平台」项目，先确保产品范围、技术架构和实现链路完整，再进入编码实现。

## 产品文档

- `docs/product/prd.md`：产品需求文档，定义产品定位、用户角色、核心场景、功能模块和验收标准。
- `docs/product/feature-map.md`：功能地图与防遗漏清单，覆盖官网、AI Studio、AI 图像处理、UI 切分、多引擎导出、插件和商业化。
- `docs/product/vberai-capability-audit.md`：VberAI 官网与关联页面能力审计，记录复刻对照项和补强项。
- `docs/product/pricing-billing.md`：定价、积分、订阅、API 权限、并发、热备份和支付规则。

## 技术文档

- `docs/technical/architecture.md`：总体技术架构，定义前端、后端、AI 服务、对象存储、数据库、导出器和插件。
- `docs/technical/professional-ui-import.md`：PSD/Figma 专业 UI 工具导入方案，定义分层导入、Design Layer Document、IR 转换和 Unity 映射。
- `docs/technical/asset-ir.md`：游戏 UI 资产中间表示 IR，定义跨 Unity/Cocos/Godot 的统一数据协议。
- `docs/technical/ai-pipeline.md`：AI Pipeline，定义文生图、图生图、抠图、局部重绘、超分和 UI 自动切分流程。
- `docs/technical/engine-exporters.md`：多引擎导出方案，定义 Unity、Cocos 3.x、Cocos 2.x、Godot 导出结构。
- `docs/technical/plugin-protocol.md`：引擎插件通信协议，定义插件认证、导出任务拉取、下载、导入日志回写和引擎反向回流。
- `docs/technical/unity-ui-restyle.md`：Unity 已有 UI 换风格方案，定义 Layout JSON、合成布局图、保持布局换风格、按原布局切回资源和自动替换。

## 实现文档

- `docs/tasks/implementation-roadmap.md`：实现路线图与链路拆解，定义 P0-P8 阶段、交付物、依赖关系和验收 Demo。

## Loops 工作流

- `docs/loops/README.md`：Loops 工作流入口。
- `docs/loops/required-skills.md`：项目必需、推荐和专项 skills 清单。
- `docs/loops/project-workflow.md`：按项目阶段划分的 skills 启用顺序。
- `docs/loops/skill-installation.md`：skills 检查、缺失和创建策略。
- `scripts/loops/bootstrap.sh`：本地 Loops 启动和检查脚本。

## 推荐阅读顺序

1. `docs/product/prd.md`
2. `docs/product/feature-map.md`
3. `docs/product/vberai-capability-audit.md`
4. `docs/product/pricing-billing.md`
5. `docs/technical/architecture.md`
6. `docs/technical/asset-ir.md`
7. `docs/technical/professional-ui-import.md`
8. `docs/technical/ai-pipeline.md`
9. `docs/technical/engine-exporters.md`
10. `docs/technical/plugin-protocol.md`
11. `docs/technical/unity-ui-restyle.md`
12. `docs/tasks/implementation-roadmap.md`

## 核心原则

- 官网复刻和 AI 工具平台同时规划，但实现阶段可以拆分。
- Unity 作为第一条生产级验收主链路。
- Cocos/Godot 通过统一资产 IR 扩展，不重复设计。
- PSD/PSB/Figma 专业工具导入优先保留已有分层，不退化为扁平图片识别。
- 引擎场景和 Prefab 必须支持反向回流到 AI Studio 成为可编辑画布。
- Unity 已有 UI 换风格必须保持原布局、节点路径、事件、脚本和资源替换关系。
- Developer API 必须支持 API Key、Webhook、轮询、取消、成本预估和限流。
- 定价系统必须支持每日积分、月度积分、购买积分、并发限制和自动续费规则。
- AI 云 API 优先，保留 ComfyUI 和自部署模型扩展点。
- UI 自动切分必须支持人工修正，不能假设 AI 一次性完全准确。
- 每次新增功能前，先检查功能地图，避免遗漏端到端链路。
