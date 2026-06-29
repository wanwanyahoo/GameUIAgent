# Loops 工作流

## 目标

Loops 是本项目的本地工作流入口，用于在每次开始开发、设计、审查或提交前，快速确认项目阶段、必要 skills 和推荐执行顺序。

本项目覆盖官网复刻、AI Studio、AI Pipeline、Unity/Cocos/Godot/Unreal 引擎插件、游戏 UI、游戏美术和技术美术流程。Loops 用来避免跨领域工作时遗漏关键能力。

## 快速开始

在仓库根目录执行：

```bash
bash scripts/loops/bootstrap.sh
```

只检查 skills：

```bash
bash scripts/loops/check-skills.sh
```

## 文档入口

- `docs/loops/required-skills.md`：项目必需和推荐 skills 清单。
- `docs/loops/project-workflow.md`：按项目阶段划分的工作流。
- `docs/loops/skill-installation.md`：skills 检查、缺失和创建策略。
- `scripts/loops/skills.manifest.json`：机器可读 skills 清单。

## 工作规则

- 新功能、行为变更、流程设计前，先使用 `brainstorming`。
- 涉及实现和 bugfix，先使用 `test-driven-development`。
- 涉及 Unity/Cocos/Godot/Unreal 时，优先使用对应游戏引擎专项 skill。
- 涉及游戏 UI、美术风格、技术美术流程时，启用对应 Game UI / Game Art / Game TA skill。
- 提交前运行 `bash scripts/loops/bootstrap.sh`，确认 skills 状态和工作流入口。

## 本地脚本边界

- 脚本只做本地检查和提示。
- 脚本不会自动修改全局 Trae 配置。
- 脚本不会下载未知外部依赖。
- 对当前环境没有安装的专项 skills，脚本会标记为 `required-custom`，后续可通过 `skill-creator` 创建。
