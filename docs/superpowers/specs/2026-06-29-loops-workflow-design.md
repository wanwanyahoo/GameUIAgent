# Loops 工作流与项目 Skills 自动化设计

## 1. 背景

当前项目是一个 AI 游戏资产生产平台规划仓库，已经包含 PRD、功能地图、技术架构、AI Pipeline、Unity/Cocos/Godot 导出、插件协议、Unity 已有 UI 换风格等文档。

后续实现会跨越官网、Web AI Studio、后端任务系统、Unity/Cocos/Godot/Unreal 引擎插件、游戏 UI、游戏美术和技术美术流程。为了避免每次进入项目时遗漏必要能力，需要建立 Loops 工作流：

- 用项目内文档固定工作流程。
- 用项目内脚本检查必要 skills 和工作入口。
- 用清单区分必需 skills、专项 skills 和阶段性推荐 skills。
- 不依赖 CI，先提供本地可运行的 bootstrap/check 能力。

## 2. 目标

### 2.1 必须实现

- 创建 `docs/loops` 工作流文档。
- 创建 `scripts/loops` 本地脚本。
- 建立项目必要 skills 清单。
- 建立专项游戏开发 skills 清单。
- 脚本能检查本地 Trae skills 目录是否存在对应 skill。
- 脚本能输出缺失 skills、推荐 skills 和下一步操作。
- 不自动安装未知外部依赖，不伪造不存在的 Trae skill。

### 2.2 暂不实现

- 不建立 GitHub Actions。
- 不自动下载第三方 skill 包。
- 不修改全局 Trae 配置。
- 不强制创建真实自定义 skill，除非后续用户明确要求。

## 3. 目录设计

```text
docs/
  loops/
    README.md
    required-skills.md
    project-workflow.md
    skill-installation.md

scripts/
  loops/
    README.md
    bootstrap.sh
    check-skills.sh
    skills.manifest.json
```

## 4. 文档设计

### 4.1 `docs/loops/README.md`

Loops 工作流总入口，说明：

- 什么是本项目 Loops。
- 每次开始工作前运行什么命令。
- 哪些 skills 是必须检查的。
- 如何处理缺失 skills。
- 如何进入不同阶段的工作流。

### 4.2 `docs/loops/required-skills.md`

定义 skills 分组：

- 基础流程 skills。
- Web/全栈实现 skills。
- 游戏引擎专项 skills。
- 游戏资产专项 skills。
- QA/审查/提交 skills。
- 可选扩展 skills。

### 4.3 `docs/loops/project-workflow.md`

定义项目阶段工作流：

- 产品/规格阶段。
- 官网复刻阶段。
- AI Studio 阶段。
- AI Pipeline 阶段。
- Unity 插件阶段。
- Cocos 插件阶段。
- Godot 插件阶段。
- Unreal 扩展阶段。
- Game UI / Game Art / Game TA 阶段。
- 测试、审查和提交阶段。

### 4.4 `docs/loops/skill-installation.md`

说明如何处理 skills：

- 已安装 skill：直接使用。
- 未安装但已有等价内置 skill：记录映射。
- 未安装且没有等价 skill：标记为 required-custom，后续通过 `skill-creator` 创建。
- 外部依赖型 skill：只提示，不自动安装。

## 5. 脚本设计

### 5.1 `scripts/loops/skills.manifest.json`

作为机器可读清单，字段：

```json
{
  "skills": [
    {
      "id": "unity-developer",
      "name": "Unity Developer",
      "category": "game-engine",
      "required": true,
      "status": "required-custom",
      "triggers": ["Unity", "Unity 插件", "Prefab", "Scene", "UGUI"],
      "fallback": "fullstack-developer"
    }
  ]
}
```

### 5.2 `scripts/loops/check-skills.sh`

能力：

- 检查 `skills.manifest.json` 是否存在。
- 检查常见 Trae skills 安装目录。
- 检查每个 skill 是否可在本地找到。
- 输出 `installed`、`missing`、`required-custom`、`optional`。
- 对缺失的 required-custom skill 输出创建建议。

检查目录：

- `$HOME/.trae-cn/skills`
- `$HOME/.trae/skills`
- 仓库内 `.skills`
- 仓库内 `skills`

### 5.3 `scripts/loops/bootstrap.sh`

能力：

- 打印项目 Loops 概览。
- 调用 `check-skills.sh`。
- 提示应优先阅读的文档。
- 提示当前阶段推荐执行的工作流。

## 6. Skills 清单

### 6.1 基础流程 Skills

- `brainstorming`：新功能、行为变更、流程设计前必须使用。
- `test-driven-development`：功能实现和 bugfix 前使用。
- `git-commit`：提交变更时使用。
- `bits-code-guard`：代码审查、缺陷发现、MR/PR 自检。

### 6.2 Web 与全栈 Skills

- `frontend-design`：官网、Web AI Studio、可视化页面设计。
- `fullstack-developer`：前后端联动、API、任务系统、平台功能。
- `agent-browser`：浏览器验证、交互检查、网站调研。
- `dogfood`：Web 应用探索测试和 UX 问题发现。

### 6.3 游戏引擎专项 Skills

这些是用户明确要求必须纳入的项目专项 skills：

- `unity-developer`：Unity Editor 插件、UGUI、Prefab、Scene、AssetDatabase、Sprite/Atlas、TextMeshPro、Unity UI 换风格。
- `cocos-developer`：Cocos Creator 2.x/3.x 插件、Prefab、Scene、Node、SpriteFrame、Editor Extension。
- `godot-developer`：Godot 4.x EditorPlugin、Control、TextureRect、PackedScene、TSCN。
- `unreal-developer`：Unreal Editor 工具、UMG、Widget Blueprint、Slate、Asset 管线、C++/Blueprint 集成。

### 6.4 游戏资产专项 Skills

这些是用户明确要求必须纳入的项目专项 skills：

- `game-ui-designer`：游戏 UI 层级、布局、按钮状态、九宫格、主题换皮、UI 规范。
- `game-art-director`：游戏美术风格、角色/场景/图标/宣传图、风格一致性、批量改皮。
- `game-ta`：技术美术流程、图集、材质、Shader、资源规范、引擎导入、性能约束。

### 6.5 可选扩展 Skills

- `figma`：Figma 设计稿、节点、变量、资源导入。
- `ai-app-designer`：AI 交互和产品体验设计。
- `taste-ui-designer`：高审美 UI/UX 设计。
- `web-design-guidelines`：Web 可访问性和设计规范审查。

## 7. Skill 状态策略

项目内置 skills 与用户要求的专项 skills 状态不同：

- 已存在内置 skill：标记为 `installed-or-builtin`。
- 当前环境未提供但项目必须具备：标记为 `required-custom`。
- 可用其他 skill 临时代替：填写 `fallback`。
- 后续需要创建真实 Trae skill 时，使用 `skill-creator` 单独创建。

第一版 Loops 只做检测和提示，不自动创建自定义 skill。

## 8. 工作流触发规则

### 8.1 开始新任务

1. 阅读 `docs/loops/README.md`。
2. 运行 `scripts/loops/bootstrap.sh`。
3. 根据任务类型查看推荐 skills。
4. 如果是新功能或行为变更，先使用 `brainstorming`。

### 8.2 官网和 Web Studio

推荐顺序：

1. `brainstorming`
2. `frontend-design`
3. `fullstack-developer`
4. `agent-browser`
5. `dogfood`
6. `git-commit`

### 8.3 Unity 链路

推荐顺序：

1. `brainstorming`
2. `unity-developer`
3. `game-ui-designer`
4. `game-ta`
5. `test-driven-development`
6. `bits-code-guard`
7. `git-commit`

### 8.4 Cocos/Godot/Unreal 链路

按目标引擎替换对应 engine skill：

- Cocos：`cocos-developer`
- Godot：`godot-developer`
- Unreal：`unreal-developer`

其余配套 skills 保持一致。

### 8.5 Game Art / Game UI / Game TA

推荐组合：

- Game UI：`game-ui-designer` + `unity-developer` 或目标引擎 skill。
- Game Art：`game-art-director` + `ai-app-designer`。
- Game TA：`game-ta` + 目标引擎 skill。

## 9. 错误处理

### 9.1 Manifest 缺失

脚本应提示：

- `scripts/loops/skills.manifest.json` 不存在。
- 请重新运行 bootstrap 或恢复文件。

### 9.2 Skill 缺失

脚本应输出：

- 缺失 skill 名称。
- 是否必需。
- 是否有 fallback。
- 是否建议后续通过 `skill-creator` 创建。

### 9.3 环境不可识别

如果无法找到 Trae skills 目录：

- 不报错中断。
- 输出提示：当前只能做清单校验，无法确认本地安装状态。

## 10. 验收标准

- `docs/loops` 下有完整工作流说明。
- `scripts/loops` 下有可运行的 `bootstrap.sh` 和 `check-skills.sh`。
- `skills.manifest.json` 包含基础 skills、Web/全栈 skills、Unity/Cocos/Godot/Unreal、Game UI、Game Art、Game TA。
- 运行 `bash scripts/loops/bootstrap.sh` 能输出项目 Loops 概览和 skill 检查结果。
- 运行 `bash scripts/loops/check-skills.sh` 能列出 installed/missing/required-custom。
- 不会自动修改全局 Trae 配置。
- 不会自动安装未知外部依赖。

## 11. 后续扩展

- 如果用户明确要求创建自定义 skills，再使用 `skill-creator` 为 Unity/Cocos/Godot/Unreal/Game UI/Game Art/Game TA 分别生成真实 skill。
- 可以追加 `npm run loops` 入口，但第一版不引入 `package.json`，避免把文档仓库误标为 Node 项目。
- 可以在后续加入 GitHub Actions，但当前版本不做 CI。

## 12. 自检结果

- 没有未决项或空白章节。
- 范围聚焦在项目内脚本和 Trae 流程文档。
- 明确包含用户要求的 Unity、Cocos、Godot、Unreal、Game UI、Game Art、Game TA skills。
- 明确第一版不自动安装未知依赖，只检查、提示和建立规范。
