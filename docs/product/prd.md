# AI 游戏资产生产平台 PRD

## 1. 产品定位

本项目目标是复刻 `https://vberai.com/` 的官网表达，并进一步建设一个完整的 AI 游戏资产生产平台。平台面向游戏开发者、美术、UI 设计师、技术美术和内容团队，提供从设计稿、图片、文本到 Unity、Cocos、Godot 可用资产的端到端生产链路。

产品不是单点工具，而是一个覆盖「官网获客 - AI Studio 创作 - AI 图像生成 - UI 自动切分 - 多引擎导出 - 插件导入 - 引擎内自动化」的完整工作流平台。

## 2. 产品目标

### 2.1 核心目标

- 完整复刻 VberAI 官网的视觉风格、信息架构、产品入口和营销转化路径。
- 建设 Web 版 AI Studio，让用户能创建项目、导入 PSD/PSB/Figma/引擎工程、上传素材、生成资产、切分 UI、编辑层级并导出。
- 支持文生图、图生图、局部重绘、抠图、超分、风格迁移等 AI 图像能力。
- 支持自动识别 UI 元素、切分图片、生成图层树、识别按钮状态和布局约束。
- 支持 Unity、Cocos Creator 2.x/3.x、Godot 的资产导出。
- 支持从 Unity/Cocos/Godot 引擎场景和 Prefab 反向回流到 AI Studio 画布。
- 支持 Unity 优先的插件导入闭环，并扩展到 Cocos/Godot 插件。
- 形成可演示、可扩展、可继续商业化的平台基础。

### 2.2 非目标

- 第一阶段不追求完全替代专业设计工具，如 Photoshop、Figma、Spine。
- 第一阶段不追求所有美术资源类型的完美结构化，优先游戏 UI、图标、角色立绘、宣传素材。
- 第一阶段不实现完整企业级权限、审计、计费和 SLA，但需要预留数据结构和接口。

## 3. 目标用户

### 3.1 游戏 UI 设计师

- 上传 UI 效果图、PSD/Figma 导出图或参考图。
- 使用文生图/图生图生成按钮、面板、图标、背景。
- 自动切分 UI 元素并编辑层级、命名和状态。
- 导出给 Unity/Cocos/Godot 开发使用。

### 3.2 游戏开发工程师

- 从 AI Studio 导入 UI 资产包。
- 在 Unity/Cocos/Godot 中自动生成 Prefab、Scene、Control 节点。
- 调整布局、脚本挂载和资源引用。
- 将引擎内修改同步回平台或生成变更记录。

### 3.3 技术美术

- 定义切分规则、命名规范、九宫格规则和导出模板。
- 管理资源压缩、图集、材质、字体和 Shader 配置。
- 维护引擎导出标准和项目资产规范。

### 3.4 团队管理员

- 管理团队成员、项目、资产权限。
- 查看任务消耗、AI 调用量和导出记录。
- 维护插件版本、模型配置和项目模板。

## 4. 核心场景

### 4.1 官网转化

用户访问官网，了解 AI 游戏资产平台能力，浏览 AI Studio、Engine MCP、AI 抠图、Unity/Cocos/Godot 插件等产品介绍，点击注册或体验 AI Studio。

### 4.2 从文本生成游戏 UI

用户新建项目，输入「赛博朋克风格 RPG 背包界面」，选择目标平台 Unity，系统生成 UI 效果图，并进一步自动切分为背景、面板、按钮、图标、文本占位等元素。

### 4.3 从 PSD/Figma 分层设计稿导入 Unity

用户上传 PSD/PSB 文件，或通过 Figma 链接/Token 导入 Frame、Component、Auto Layout 和图层结构。系统解析已有分层、命名、坐标、尺寸、文本、图片、组件、约束和状态，生成统一资产 IR，再导出为 Unity 可用的 Texture、Sprite、Canvas、RectTransform、Image、Button、TextMeshPro、Prefab 和 Scene。

该链路优先保留专业 UI 工具中的已有结构，不把 PSD/Figma 简化为单张图片再重新识别。只有当图层信息缺失或用户上传的是扁平图片时，才启用 AI 自动切分补全。

### 4.4 从参考图生成 UI 变体

用户上传参考图，选择图生图和风格参数，系统生成多张变体，用户选择一张进入编辑画布，继续进行局部重绘、抠图和切分。

### 4.5 从图片自动切分为 UI 层级

用户上传完整 UI 效果图，系统识别可切分元素，输出层级树、切片资源、元素类别、坐标、尺寸、锚点、按钮状态和可编辑属性。

### 4.6 导出 Unity 可用资产

用户选择 Unity 导出，系统将资产 IR 转换为 Unity Package 或 ZIP，包含 Texture、Sprite、Prefab、Scene、Canvas、RectTransform、Text/TMP 占位、Meta 信息和导入说明。

### 4.7 Unity 插件导入

用户在 Unity Editor 插件中登录或填写导入 Token，选择平台项目和导出任务，一键拉取资产包并在 Unity 中生成 Canvas/Prefab/Scene。

### 4.8 Unity 已有 UI 保持布局换风格

用户在 Unity 插件中选择已有 UI Scene 或 Prefab，插件导出 Layout JSON 和 Sprite 图片资源。平台根据原始布局还原合成图，AI 在保持位置、尺寸、锚点、按钮事件和脚本绑定不变的前提下生成新风格，再按原 Layout JSON 切回独立 UI 资源，最后由 Unity 插件生成新主题 Prefab 或原地替换原资源。

### 4.9 扩展到 Cocos/Godot

同一份资产 IR 可转换为 Cocos Creator 2.x/3.x Prefab/Scene 与 Godot Control Scene。插件负责拉取导出包、创建节点、写入资源引用并同步状态。

## 5. 产品模块

### 5.1 官网门户

- 首页 Landing Page
- 产品矩阵
- AI Studio 介绍
- Engine MCP / 引擎插件介绍
- AI 超强抠图介绍
- 定价页
- 文档中心入口
- 登录/注册入口
- 联系客服、B 站、GitHub、Footer 法务链接

### 5.2 账号与团队

- 邮箱/手机号/第三方登录
- 注册、登录、退出
- 用户个人空间
- 团队空间
- 项目成员邀请
- 角色权限：Owner、Admin、Designer、Developer、Viewer
- API Key 和插件 Token 管理

### 5.3 项目空间

- 创建项目
- 选择目标引擎：Unity、Cocos 3.x、Cocos 2.x、Godot
- 选择画布规格：移动端、PC、横屏、竖屏、自定义
- 项目资源库
- 任务历史
- 导出记录
- 版本记录

### 5.4 AI Studio 画布

- 多画布管理
- 图片上传
- PSD 分层文件导入
- Figma 文件/Frame/Component 导入
- 文本 Prompt 输入
- 参考图上传
- 生成结果对比
- 图层树
- 元素属性面板
- 资源预览
- 局部重绘区域选择
- 切分结果编辑
- 画布缩放、拖拽、选择、对齐

### 5.5 AI 生成与图像处理

- 文生图
- 图生图
- 局部重绘
- 背景去除
- 透明 PNG 输出
- 超分辨率
- 风格迁移
- 多候选结果
- Seed、尺寸、风格、模型选择
- 任务队列和进度展示

### 5.6 UI 自动切分

- 自动识别 UI 元素
- 读取 PSD/Figma 已有图层
- 保留 PSD 图层组、可见性、透明度、混合模式和图层命名
- 保留 Figma Frame、Group、Component、Instance、Auto Layout 和约束
- 自动生成切片
- 元素分类：背景、面板、按钮、图标、文本、装饰、头像、进度条、输入框
- 识别按钮状态：normal、pressed、disabled、hover、selected
- 识别九宫格区域
- 识别锚点和布局约束
- 识别重复组件和列表项
- 生成图层树和命名建议
- 支持人工修正

### 5.7 资产管理

- 原始图片
- 生成图片
- 切片资源
- 图标资源
- 字体资源
- 材质资源
- 图集
- 元数据
- 版本管理
- 标签和搜索

### 5.8 导出中心

- Unity 导出
- Cocos Creator 3.x 导出
- Cocos Creator 2.x 导出
- Godot 导出
- 通用 JSON/ZIP 导出
- 预览导出结构
- 导出任务记录
- 导出失败重试
- 导出模板配置

### 5.9 引擎插件

- Unity Editor 插件
- Cocos Creator 扩展
- Godot Editor 插件
- 登录或 Token 连接
- 项目列表
- 导出任务列表
- 一键导入
- 导入进度
- 导入日志
- 资源冲突处理
- 状态回写

### 5.10 文档与开发者中心

- 快速开始
- AI Studio 使用指南
- Unity 插件安装
- Cocos 插件安装
- Godot 插件安装
- 导出格式说明
- API 文档
- 插件协议
- 常见问题

## 6. 端到端主流程

### 6.1 Unity 主链路

1. 用户注册并进入 AI Studio。
2. 创建 Unity 项目。
3. 输入 Prompt、上传参考图、上传 PSD/PSB，导入 Figma Frame，或连接已有引擎项目。
4. 云 AI API 生成 UI 图片，或专业 UI 导入器解析 PSD/PSB/Figma 分层结构。
5. 用户选择最佳结果，或确认导入后的分层画布。
6. 系统根据 PSD/PSB/Figma 原始层级生成 IR；若输入为扁平图片，则自动进行抠图、元素检测和 UI 切分。
7. 用户在画布中调整图层、命名、锚点和组件类型。
8. 系统生成资产 IR。
9. 用户选择 Unity 导出。
10. 后端生成 Unity 资产包。
11. Unity 插件拉取导出任务。
12. 插件导入 Texture/Sprite/Prefab/Scene。
13. Unity 中生成可见 UI。
14. 插件回写导入状态和日志。

### 6.2 Cocos/Godot 扩展链路

- 复用同一资产 IR。
- 后端增加 Cocos/Godot exporter。
- 插件按目标引擎读取导出包。
- 引擎侧生成对应节点树和资源引用。

### 6.3 引擎反向回流链路

1. 用户在 Unity/Cocos/Godot 插件中选择已有 Scene 或 Prefab。
2. 插件提取节点树、组件、资源引用、布局、文本和脚本绑定摘要。
3. 插件上传 Engine Snapshot。
4. 平台将 Engine Snapshot 转换为资产 IR。
5. AI Studio 以可编辑画布方式打开引擎场景。
6. 用户使用 AI Notes 和 AI Chat 生成修改建议或批量改皮。
7. 修改后的 IR 再导出回引擎。

### 6.4 Unity UI 换风格链路

1. 用户在 Unity 插件中选择已有 UI Scene 或 Prefab。
2. 插件导出 Layout JSON，包含节点路径、RectTransform、Anchor、Pivot、组件、事件绑定和资源 GUID。
3. 插件导出 Sprite、Atlas 子图、九宫格 border、Image type、字体和文本摘要。
4. 平台按布局 JSON 和图片资源合成 `layout_preview.png`。
5. 用户输入目标风格 Prompt 或上传风格参考图。
6. AI 生成保持布局不变的 `restyled_composite.png`。
7. 平台按原始 Layout JSON 切回每个可替换节点的新资源。
8. Unity 插件根据 replacement manifest 生成新主题目录和 Prefab Variant，或按用户选择原地替换。
9. 原 UI 的 RectTransform、脚本、Button onClick、Animator 和 Localization key 默认保持不变。

## 7. 信息架构

### 7.1 未登录官网

- 首页
- 产品
- AI Studio
- Engine MCP
- AI 超强抠图
- 定价
- 文档
- 登录
- 注册

### 7.2 登录后工作台

- 项目列表
- 最近任务
- 资源库
- AI Studio
- 导出中心
- 插件连接
- 团队设置
- API Key
- 账单用量

### 7.3 AI Studio 内部导航

- 画布
- 素材
- 生成
- 切分
- 图层
- 属性
- 导出
- 历史

## 8. 关键页面

### 8.1 官网首页

- 深色网格背景
- 顶部导航
- 登录/注册按钮
- 首屏标题：一站式 AI 游戏开发解决方案
- 产品入口卡片
- 工作流介绍
- AI Studio 平台介绍
- Engine MCP 产品区
- AI 超强抠图区
- CTA 区
- Footer

### 8.2 项目列表

- 项目卡片
- 目标引擎标识
- 最近更新时间
- 任务状态
- 创建项目按钮

### 8.3 AI Studio

- 顶部项目栏
- 左侧资源/图层
- 中央画布
- 右侧 Design / AI Notes / AI Chat / 生成参数
- 底部任务流和日志
- 导出按钮

### 8.4 切分编辑器

- 原图/切片叠加视图
- 框选和合并切片
- 元素类型选择
- 命名规则
- 锚点和布局设置
- 一键生成 IR

### 8.5 导出中心

- 目标引擎选择
- 导出模板
- 导出检查项
- 导出进度
- 下载包
- 插件导入指引

### 8.6 插件界面

- 登录/Token
- 项目选择
- 导出任务列表
- 导入按钮
- 导入日志
- 资源冲突提示

## 9. 权限与套餐

### 9.1 免费版

- 少量项目
- 限量 AI 生成
- 每日免费积分
- Unity 导出试用
- 基础抠图

### 9.2 Pro 版

- 更多生成额度
- 更多并发任务
- 云项目和本地项目额度
- Unity/Cocos/Godot 导出
- 高级切分
- API 调用权限
- 批量导出
- 版本历史
- 企业级加密热备份

### 9.3 Team 版

- 团队空间
- 成员权限
- 共享素材库
- 插件 Token 管理
- 用量统计
- 自动续费和账单管理

### 9.4 积分系统

- Daily Free Credits：每日重置，不结转。
- Monthly Credits：每月重置，不结转。
- Purchased Credits：购买积分，永不过期。
- 扣除顺序：每日免费积分 → 每月积分 → 购买积分。
- 不同 AI 任务根据尺寸、模型和复杂度消耗不同积分。

## 10. 验收标准

### 10.1 官网

- 视觉风格接近目标站点。
- 页面结构完整。
- 导航、CTA、Footer、响应式适配可用。

### 10.2 AI Studio

- 能创建项目。
- 能上传图片。
- 能提交文生图/图生图任务。
- 能展示任务进度和结果。
- 能进入切分编辑。

### 10.3 UI 切分

- 能对 UI 图片输出切片。
- 能对 PSD/Figma 已有分层生成图层树。
- 能把 PSD/Figma 图层映射为 Unity UI 节点。
- 能生成图层树。
- 能人工修正元素类型、名称、坐标和层级。
- 能生成统一资产 IR。

### 10.4 Unity 导出

- 能从 IR 生成 Unity 可导入资产包。
- 能从 PSD/Figma 分层导入结果生成 Unity 可导入资产包。
- Unity 插件能导入资产。
- Unity 场景中能看到自动生成的 UI。

### 10.5 多引擎扩展

- Cocos/Godot 导出器能读取同一 IR。
- 插件能完成基础导入。
- 导出结构和日志可追踪。

## 11. 风险

- AI 生成质量不稳定，需要多候选、人工编辑和重试机制。
- UI 自动切分无法完全准确，需要可视化修正能力。
- 三引擎导出差异较大，需要统一 IR 降低重复开发。
- 插件安装和版本兼容复杂，需要明确支持版本。
- 云 AI API 成本和速率限制需要队列、限流和用量管理。

## 12. 成功指标

- 用户能在 10 分钟内从 Prompt 生成一个 Unity 可见 UI。
- 用户能在 5 分钟内从图片切分并导出 Unity 资产包。
- Unity 插件一键导入成功率达到 90% 以上。
- Cocos/Godot 导出器能复用 70% 以上 IR 字段。
- 官网注册转化路径完整可用。
