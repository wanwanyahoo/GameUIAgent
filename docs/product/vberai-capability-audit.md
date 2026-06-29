# VberAI 官网与关联能力复刻审计

## 1. 调研范围

本次复查覆盖以下入口：

- `https://vberai.com/`
- `/studio`
- `/ai-studio` 与 `/ai-studio/bg-removal`
- `/game-engines`
- `/game-engines/unity`
- `/game-engines/godot`
- `/game-engines/cocos`
- `/game-engines/cocos2x`
- `/developers/api-docs`
- `/pricing`
- `/contact`
- `/terms`

## 2. 首页能力

### 2.1 信息架构

- 深色科技风首页。
- 顶部导航。
- 登录/注册。
- 产品探索。
- 语言切换。
- 主题切换。
- AI Studio 入口。
- AI 超强抠图入口。
- 开发者 API 文档入口。
- 游戏引擎插件入口。
- 定价入口。
- 联系客服、B 站、GitHub 外链。
- 服务条款和隐私政策。

### 2.2 首页主张

- 一站式 AI 游戏开发解决方案。
- 从游戏 AI 美术设计到游戏引擎自动化 AI 编程。
- 导入 PSD、Figma 类设计稿或游戏项目资产。
- AI Studio 中创作、编辑、优化。
- 导出引擎可直接使用的场景、预制体和美术资源。
- Engine MCP 完成引擎操作与代码编写自动化。

### 2.3 首页流程

- 导入设计与项目资产。
- AI Studio 创作与优化。
- 导出引擎可用资产。
- AI 自动化开发落地。

## 3. AI Studio 能力

### 3.1 官方描述

AI Studio 是游戏原生 AI 设计平台，面向游戏美术和 UI，把 Unity、Cocos Creator、Godot 作为一等导出目标。

### 3.2 工作区结构

- 左侧 PSB / 图层面板。
- 中央真实游戏 UI 画布。
- 右侧 Design / AI Notes / AI Chat 检查器。

### 3.3 工作流

- 导入 PSD / PSB / Figma 或现有引擎工程。
- AI 协作生成场景、批量改皮、高频工具。
- 组件化输出引擎可用 Prefab。
- 导出 Cocos 场景/预制体、Unity Prefab、Godot 场景。
- 通过 MCP 同步。
- 反向回流：把引擎场景拉回画布作为可编辑资产。

## 4. AI 超强抠图能力

### 4.1 在线工具

- 支持 PNG、JPG、WebP。
- 最大 20MB。
- 最大 2048px。
- 积分消耗 5-30 / 次。
- 登录后使用。
- 图片处理后删除。

### 4.2 能力点

- 发丝级边缘。
- 光效保留。
- 半透明材质。
- 复杂背景。
- 阴影和网格背景。
- 透明 PNG 输出。
- Alpha mask 输出。

### 4.3 API 能力

- Service Code：`super-matting`。
- Base URL：`https://api.vberai.com/api`。
- API Key Header：`X-API-Key`。
- 异步执行：`POST /ai/services/super-matting/execute`。
- 任务轮询：`GET /ai/tasks/{taskId}`。
- 任务取消：`POST /ai/tasks/{taskId}/cancel`。
- 成本预估：`POST /ai/services/super-matting/cost`。
- Webhook 回调。
- HMAC-SHA256 webhook 签名。
- 输出 `final_image` 和 `alpha_mask`。
- 结果签名 URL 有效期 7 天。

## 5. Game Engine MCP 能力

### 5.1 通用能力

- MCP 服务运行在游戏引擎编辑器内部。
- 兼容 Claude Desktop、Claude Code、Cursor、Windsurf、Cline 等 MCP 客户端。
- 一键配置向导生成客户端 JSON。
- 让 AI 读写场景、组件、资源、动画、脚本和编辑器状态。

### 5.2 Unity MCP

- 支持 Unity 2022.3+ 和 Unity 6。
- Windows / macOS / Linux。
- 10 语言 UI。
- 15 个意图工具。
- 84+ 原子操作。
- 免费试用、月付、年付、永久授权。
- 首次激活联网，之后支持 7 天离线。

能力范围：

- GameObject 创建、查找、删除、批量属性、层级快照。
- 组件增删、读写属性、UnityEvent 绑定。
- 场景创建、打开、保存、层级快照、切换。
- Prefab 创建、实例化、Apply、Revert、Unpack。
- 材质与 Shader 创建和绑定。
- 编辑器菜单、选区、ProjectSettings、Play 模式、Console。
- Animator、AnimatorController、AnimationClip。
- UI 规则、布局规范、Anchor 预设知识库。
- 缺脚本、重名、贴图审计、Test Runner。

### 5.3 Cocos MCP 3.x Pro

- 支持 Cocos Creator 3.8.6+。
- 17 个意图工具。
- 220+ 操作。
- 9 大领域。
- Streamable HTTP。
- 开源版免费，Pro 版提供高级能力。

九大领域：

- 场景管理。
- 节点操作。
- 组件系统。
- Prefab 系统。
- 资源管理。
- UI 与模板。
- 动画和 Spine。
- 知识库。
- 校验与调试。

Pro 能力：

- Streamable HTTP。
- Token 优化。
- 操作码。
- 一键客户端配置。
- 工具自定义。
- 一键建场景。
- 内置知识库。

### 5.4 Cocos MCP 2.x Pro

- 支持 Cocos Creator 2.4.x+ 老项目。
- 17 个意图工具。
- 110+ 操作。
- JS/TS 组件生成。
- 场景编辑。
- 节点和组件管理。
- 资源导入、整理、优化。
- Prefab 创建与编辑。
- 脚本编写与挂载。
- Spine、动画、UI 模板、知识库、校验调试。

### 5.5 Godot MCP

- Godot 4.x。
- MIT 开源免费。
- 100+ 工具命令。
- 21 个核心系统。
- Windows / macOS / Linux。
- GDScript 和 C# 项目。
- 默认端口 3000，可配置 1024-65535。
- 非阻塞 I/O，主线程轻量调用。

系统覆盖：

- 场景与节点。
- 脚本与代码。
- 动画。
- 物理。
- 视觉效果。
- UI 系统。

## 6. 定价与积分能力

### 6.1 AI Studio 订阅

- Free。
- Base。
- Plus。
- PRO。
- MAX Expert Program。

### 6.2 计费维度

- 每日免费积分。
- 每月积分。
- 购买积分。
- AI 并发任务数。
- AI Studio 云项目数。
- AI Studio 本地项目数。
- Base AI 模型 / 全部 AI 模型。
- API 调用权限。
- 更高请求速率。
- 企业级加密热备份快照。
- 工作日专家客服优先支持。

### 6.3 积分规则

- Daily Free Credits 每天 00:00 重置，不结转。
- Monthly Credits 每月重置，不结转。
- Purchased Credits 永不过期。
- 扣除顺序：每日免费积分 → 每月积分 → 购买积分。

### 6.4 订阅规则

- 首次付费订阅默认开启自动续费。
- 可在账号设置关闭自动续费。
- 升级立即生效并按剩余价值折算。
- 年付不能直接降级到月付。
- 月付可切换同档年付。
- 集成 Stripe 支付脚本。

## 7. 联系与支持

- Contact 页面支持提交工单。
- Telegram、WeChat、WhatsApp。
- 一个工作日内回复。
- 邮箱：`support@vberai.com`。

## 8. 与当前文档对照结果

### 8.1 已覆盖

- 官网复刻。
- AI Studio。
- PSD/Figma 导入。
- 多引擎 Unity/Cocos/Godot 导出。
- UI 自动切分。
- AI 抠图。
- API Key。
- 积分和订阅基础。
- Unity/Cocos/Godot 插件。
- MCP 通信。

### 8.2 需补强

- PSB 导入。
- AI Notes 与 AI Chat。
- 引擎场景/Prefab 反向回流到 AI Studio。
- Webhook、轮询、取消任务、成本预估、签名校验。
- API 限流矩阵。
- Daily/Monthly/Purchased Credits 的精确规则。
- 云项目、本地项目、并发任务限制。
- 企业级加密热备份快照。
- 自动续费、升级、降级和月转年规则。
- 语言切换、主题切换。
- 联系支持渠道。
