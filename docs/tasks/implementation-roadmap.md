# 实现路线图与链路拆解

## 1. 路线图目标

路线图用于防止功能遗漏，确保从官网复刻到 AI 游戏资产生产平台的每条链路都有明确交付物、依赖和验收标准。

项目采用「先完整文档，后分阶段实现」策略。第一条生产级主链路以 Unity 为验收基准，Cocos/Godot 在同一资产 IR 上扩展。

## 2. 总体阶段

| 阶段 | 名称 | 目标 |
| --- | --- | --- |
| P0 | 文档与架构 | 完成 PRD、技术方案、IR、协议和实现计划 |
| P1 | 官网复刻 | 完成 VberAI 风格官网和产品门户 |
| P2 | 平台基础 | 完成账号、项目、资产、任务基础能力 |
| P3 | 专业 UI 工具导入 | 完成 PSD/Figma 分层导入并生成 IR |
| P4 | AI Studio | 完成 Web 画布、生成任务和资产库 |
| P5 | AI Pipeline | 完成云 API 文生图、图生图、抠图、超分 |
| P6 | UI 自动切分 | 完成元素识别、切片、图层树和 IR |
| P7 | Unity 主链路 | 完成 Unity 导出和插件导入 |
| P8 | Cocos/Godot 扩展 | 完成 Cocos 2/3 与 Godot 导出和插件 |
| P9 | 平台化补齐 | 完成团队、计费、文档、稳定性和商业化 |

## 3. P0 文档与架构

### 3.1 交付物

- PRD 产品需求文档
- 功能地图与防遗漏清单
- 技术架构文档
- 资产 IR 文档
- AI Pipeline 文档
- 多引擎导出文档
- 插件协议文档
- 实现路线图

### 3.2 验收标准

- 所有一级功能域都有文档覆盖。
- Unity/Cocos/Godot 都有导出设计。
- AI 生成、切分、导出、插件导入链路完整。
- 每个阶段都有交付物和验收标准。

## 4. P1 官网复刻

### 4.1 功能

- 深色科技风首页
- 顶部导航
- 汉堡菜单
- 登录/注册入口
- 产品下拉菜单
- Hero 首屏
- 产品矩阵
- 工作流模块
- AI 抠图模块
- AI Studio 模块
- Engine MCP 模块
- CTA 模块
- Footer
- 响应式适配

### 4.2 页面

- `/`
- `/products`
- `/ai-studio`
- `/engine-mcp`
- `/matting`
- `/pricing`
- `/docs`
- `/login`
- `/register`

### 4.3 验收

- 桌面端视觉接近目标站点。
- 移动端导航可用。
- 所有 CTA 有目标路径。
- Footer 链接完整。
- 官网可作为平台入口。

## 5. P2 平台基础

### 5.1 后端基础

- 用户注册
- 用户登录
- JWT/Session
- 项目 CRUD
- 资产上传
- 任务模型
- 对象存储
- 数据库迁移

### 5.2 前端基础

- 登录页
- 注册页
- 项目列表
- 创建项目
- 项目详情
- 资产库基础页面

### 5.3 数据模型

- User
- Team
- Membership
- Project
- Asset
- Job
- ExportJob
- PluginToken

### 5.4 验收

- 用户能注册登录。
- 用户能创建项目。
- 用户能上传图片资产。
- 后端能保存资产元数据。
- 前端能展示项目和资产。

## 6. P3 专业 UI 工具导入

### 6.1 PSD 导入

- PSD 文件上传
- PSB 文件上传
- PSD 图层组解析
- PSD 图片图层导出
- PSD 文本图层解析
- PSD 图层坐标、尺寸、透明度、可见性保留
- PSD 图层树转换为 Design Layer Document
- Design Layer Document 转资产 IR

### 6.2 Figma 导入

- Figma Token 配置
- Figma 文件链接导入
- Frame/Node 选择
- Group/Component/Instance 解析
- Auto Layout 解析
- Constraints 解析
- Text 和 Image Fill 导出
- Figma 结构转换为 Design Layer Document
- Design Layer Document 转资产 IR

### 6.3 Unity 转换验收

- PSD/Figma 已有分层能生成图层树。
- 图片图层能导出为 Unity Sprite/Image。
- 文本图层能导出为 TextMeshProUGUI。
- 图层组/Frame 能导出为 GameObject/Canvas 层级。
- Component 能导出为 Prefab 或 Prefab-like 结构。

## 7. P4 AI Studio

### 7.1 页面结构

- 顶部项目栏
- 左侧素材库
- 左侧 PSB / 图层树
- 中央画布
- 右侧 Design 面板
- 右侧 AI Notes
- 右侧 AI Chat
- 右侧生成参数
- 右侧属性面板
- 底部任务列表

### 7.2 画布能力

- 图片展示
- 图片拖拽
- 缩放和平移
- 图层选择
- 属性编辑
- 图层树同步

### 7.3 任务面板

- 显示 AI 任务
- 显示切分任务
- 显示导出任务
- 任务状态刷新
- 错误信息展示

### 7.4 验收

- 项目内能打开 AI Studio。
- 资产能放到画布。
- 图层树能展示画布元素。
- 属性修改能更新画布。

## 8. P5 AI Pipeline

### 8.1 文生图

- Prompt 表单
- 参数选择
- 提交任务
- 云 API 调用
- 任务进度
- 结果保存
- 多候选展示

### 8.2 图生图

- 上传参考图
- 参数选择
- 提交任务
- 结果展示

### 8.3 抠图

- 图片选择
- 抠图任务
- Alpha PNG 输出
- Before/After 对比

### 8.4 超分和局部重绘

- 超分任务
- 蒙版区域
- 局部重绘结果

### 8.5 验收

- 至少一个云 AI provider 可用。
- 文生图返回真实图片。
- 图生图返回真实变体。
- 抠图返回透明 PNG。
- 任务失败有错误提示。

## 9. P6 UI 自动切分

### 9.1 自动识别

- 元素检测
- 文本区域识别
- 按钮识别
- 面板识别
- 图标识别
- 背景识别

### 9.2 切分编辑

- 切片框显示
- 手动框选
- 合并切片
- 拆分切片
- 删除切片
- 修改类型
- 修改名称

### 9.3 IR 生成

- Asset 列表
- Node 树
- Transform
- Layout
- Visual
- Text
- Interaction
- Component

### 9.4 验收

- 上传 UI 图能生成切片。
- 切片能在画布中编辑。
- 能保存用户修正。
- 能生成合法 IR。
- IR 能通过校验。

## 10. P7 Unity 主链路

### 10.1 Unity Exporter

- 读取 IR
- 生成 Unity manifest
- 生成图片资源
- 生成 Prefab 数据
- 生成 Scene 数据
- 打包 ZIP

### 10.2 Unity Plugin

- EditorWindow
- Token 登录
- 项目列表
- 导出任务列表
- 下载 ZIP
- 解压
- 导入 Texture
- 配置 Sprite
- 创建 Canvas
- 创建 Prefab
- 创建 Scene
- 上传日志
- 捕获 Unity Scene/Prefab 快照
- 上传 Engine Snapshot
- 从 Engine Snapshot 反向生成 AI Studio 画布
- 导出 Unity UI Layout JSON 和 Sprite 图片
- 生成 UI 合成布局图
- 执行保持布局的 AI 换风格
- 按原 Layout JSON 切回资源
- 生成新主题 Prefab 或原地替换资源

### 10.3 验收

- 用户能从 AI Studio 触发 Unity 导出。
- 用户能从 PSD/Figma 分层导入结果触发 Unity 导出。
- Unity 插件能看到导出任务。
- Unity 插件能导入资源。
- Unity 场景中能看到自动生成 UI。
- 按钮、文本、图片层级基本正确。
- Unity Scene/Prefab 能反向回流到 AI Studio。
- Unity 已有 UI 能在保持布局、事件和脚本绑定不变的情况下换风格。

## 11. P8 Cocos/Godot 扩展

### 11.1 Cocos 3.x

- Cocos 3.x Exporter
- Cocos 3.x Extension
- Prefab 生成
- Scene 生成
- 资源导入

### 11.2 Cocos 2.x

- Cocos 2.x Exporter
- Cocos 2.x Plugin
- Prefab JSON
- 资源导入

### 11.3 Godot

- Godot Exporter
- Godot EditorPlugin
- TSCN 生成
- Texture 导入
- Control 节点树生成

### 11.4 验收

- 同一个 IR 能导出到 Cocos 3.x。
- 同一个 IR 能导出到 Cocos 2.x。
- 同一个 IR 能导出到 Godot。
- 插件能完成基础导入。

## 12. P9 平台化补齐

### 12.1 团队协作

- 团队空间
- 成员邀请
- 成员角色
- 项目权限

### 12.2 商业化

- Free/Base/Plus/PRO/MAX 套餐
- 每日免费积分
- 月度订阅积分
- 购买积分
- 积分扣除优先级
- 并发任务限制
- 云项目和本地项目额度
- API 调用权限
- 请求速率限制
- 自动续费
- 升级和降级规则
- Stripe 支付集成
- 加密热备份快照
- 用量统计
- 账单

### 12.3 稳定性

- 队列重试
- Provider fallback
- 导出失败重试
- 插件版本升级
- 日志聚合

### 12.4 文档中心

- 快速开始
- AI Studio 教程
- Unity 插件教程
- Cocos 插件教程
- Godot 插件教程
- API 文档

## 13. 端到端验收 Demo

### 13.1 Demo A：文生图到 Unity

1. 打开官网。
2. 注册并进入 AI Studio。
3. 创建 Unity 项目。
4. 输入 Prompt 生成 UI。
5. 选择生成结果。
6. 自动切分 UI。
7. 修正图层名称。
8. 导出 Unity。
9. 打开 Unity 插件。
10. 下载并导入。
11. Unity 场景显示 UI。

### 13.2 Demo B：上传图片到 Unity

1. 上传 UI 效果图。
2. 自动识别元素。
3. 调整切片。
4. 生成 IR。
5. 导出 Unity。
6. 插件导入。

### 13.3 Demo C：PSD/Figma 分层到 Unity

1. 上传 PSD，或输入 Figma Frame 链接。
2. 系统解析已有图层、文本、组件和布局。
3. 生成 Design Layer Document。
4. 转换为资产 IR。
5. 用户在 AI Studio 中检查和修正。
6. 导出 Unity。
7. Unity 插件导入并生成 Canvas/Prefab/Scene。

### 13.4 Demo D：同一 IR 导出三引擎

1. 使用同一 IR。
2. 导出 Unity。
3. 导出 Cocos 3.x。
4. 导出 Godot。
5. 分别由插件导入。

### 13.5 Demo E：Unity 反向回流到 AI Studio

1. 在 Unity 插件中选择已有 Scene 或 Prefab。
2. 插件捕获节点、组件、资源引用和布局。
3. 上传 Engine Snapshot。
4. 平台生成资产 IR。
5. AI Studio 打开为可编辑画布。
6. 用户通过 AI Notes / AI Chat 提出修改。
7. 修改后重新导出回 Unity。

### 13.6 Demo F：Unity 已有 UI 保持布局换风格

1. 在 Unity 插件中选择已有 UI Prefab。
2. 插件导出 Layout JSON 和 Sprite/Atlas 图片资源。
3. 平台还原合成布局图。
4. 用户输入目标风格 Prompt 或上传风格参考图。
5. AI 生成保持布局不变的新风格合成图。
6. 平台按原 Layout JSON 切回独立资源。
7. Unity 插件拉取 replacement manifest。
8. 插件生成新主题 Prefab 或原地替换。
9. 新 UI 保持 RectTransform、Button onClick、脚本和 Animator 绑定不变。

## 14. 依赖关系

```text
P1 官网复刻
  └─ 可独立进行

P2 平台基础
  ├─ P3 专业 UI 工具导入
  ├─ P4 AI Studio
  ├─ P5 AI Pipeline
  ├─ P6 UI 自动切分
  └─ P7/P8 导出插件

P6 UI 自动切分
  └─ 依赖 P5 图片结果和 P4 画布

P7 Unity 主链路
  └─ 依赖 P3/P6 IR

P8 Cocos/Godot
  └─ 依赖 P3/P6 IR 和 P7 导出经验
```

## 15. 优先级

### 15.1 P0 必须完成

- PRD
- 技术架构
- IR
- Pipeline
- Exporter
- Plugin Protocol
- Roadmap

### 15.2 第一版必须完成

- 官网
- 登录注册
- 项目
- 图片上传
- PSD 导入
- PSB 导入
- Figma 导入
- 引擎反向回流
- 文生图
- 图生图
- 抠图
- 自动切分
- IR
- Unity 导出
- Unity 插件导入
- Developer API 抠图
- Webhook / Poll / Cancel / Cost

### 15.3 第二版完成

- Cocos 3.x
- Godot
- Cocos 2.x
- 团队协作
- 文档中心
- 订阅积分
- 联系支持

### 15.4 第三版完成

- 高级计费
- 插件市场
- API 开放平台
- ComfyUI/自部署模型
- 批量生产

## 16. 风险控制

### 16.1 功能范围过大

策略：

- 文档完整覆盖。
- 实现分阶段。
- Unity 作为第一主链路。
- Cocos/Godot 复用 IR。

### 16.2 AI 质量不稳定

策略：

- 多候选。
- 人工编辑。
- 可回退版本。
- Provider fallback。

### 16.3 UI 切分不准确

策略：

- 切分结果可编辑。
- 置信度标记。
- 手动切分模式。
- 保存用户修正。

### 16.4 引擎差异复杂

策略：

- 统一 IR。
- 独立 exporter。
- 插件本地适配。
- 明确版本支持范围。

## 17. 文档更新规则

实现过程中如发现功能缺口，需要先更新：

1. `docs/product/feature-map.md`
2. 对应技术文档
3. `docs/tasks/implementation-roadmap.md`

再进入代码实现。
