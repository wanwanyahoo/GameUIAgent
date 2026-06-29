# 项目 Skills 清单

## 基础流程 Skills

| Skill | 状态 | 用途 |
| --- | --- | --- |
| `brainstorming` | 必需 | 新功能、行为变更、流程设计前进行需求澄清和方案设计。 |
| `test-driven-development` | 必需 | 实现功能或修复问题前制定测试驱动流程。 |
| `git-commit` | 必需 | 生成规范提交信息并完成提交。 |
| `bits-code-guard` | 必需 | 代码审查、缺陷发现、MR/PR 或本地变更自检。 |

## Web 与全栈 Skills

| Skill | 状态 | 用途 |
| --- | --- | --- |
| `frontend-design` | 推荐 | 官网复刻、Web AI Studio、可视化交互页面。 |
| `fullstack-developer` | 推荐 | 前后端联动、API、任务系统、平台功能。 |
| `agent-browser` | 推荐 | 浏览器调研、交互验证、页面测试。 |
| `dogfood` | 推荐 | Web 应用探索测试和 UX 问题发现。 |

## 游戏引擎专项 Skills

这些 skills 是本项目必须具备的专项能力。如果当前环境没有安装，应先标记为 `required-custom`，后续通过 `skill-creator` 创建。

| Skill | 状态 | 用途 |
| --- | --- | --- |
| `unity-developer` | 必需专项 | Unity Editor 插件、UGUI、Prefab、Scene、AssetDatabase、Sprite/Atlas、TextMeshPro、Unity UI 换风格。 |
| `cocos-developer` | 必需专项 | Cocos Creator 2.x/3.x 插件、Prefab、Scene、Node、SpriteFrame、Editor Extension。 |
| `godot-developer` | 必需专项 | Godot 4.x EditorPlugin、Control、TextureRect、PackedScene、TSCN。 |
| `unreal-developer` | 必需专项 | Unreal Editor、UMG、Widget Blueprint、Slate、Asset 管线、C++/Blueprint 集成。 |

## 游戏资产专项 Skills

| Skill | 状态 | 用途 |
| --- | --- | --- |
| `game-ui-designer` | 必需专项 | 游戏 UI 层级、布局、按钮状态、九宫格、主题换皮、UI 规范。 |
| `game-art-director` | 必需专项 | 游戏美术风格、角色、场景、图标、宣传图、风格一致性、批量改皮。 |
| `game-ta` | 必需专项 | 技术美术流程、图集、材质、Shader、资源规范、引擎导入、性能约束。 |

## 可选扩展 Skills

| Skill | 状态 | 用途 |
| --- | --- | --- |
| `figma` | 可选 | Figma 节点、变量、资源和设计稿导入。 |
| `ai-app-designer` | 可选 | AI 交互和产品体验设计。 |
| `taste-ui-designer` | 可选 | 高审美 UI/UX 设计。 |
| `web-design-guidelines` | 可选 | Web 可访问性和设计规范审查。 |

## 缺失处理

- 内置 skill 缺失：检查 Trae 环境是否启用。
- 必需专项 skill 缺失：保留清单状态，后续使用 `skill-creator` 创建。
- 有 fallback 的 skill：可临时使用 fallback，但实现专项模块前应补齐真实 skill。
