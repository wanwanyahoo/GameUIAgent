# Skill 检查与安装策略

## 1. 原则

Loops 第一版只做本地检查和提示，不自动安装未知外部依赖，不修改全局 Trae 配置。

如果某个项目必需 skill 当前不存在，脚本会把它标记为 `required-custom`，并提示后续通过 `skill-creator` 创建。

## 2. 状态定义

| 状态 | 含义 |
| --- | --- |
| `installed-or-builtin` | 当前环境已存在或由 Trae 内置提供。 |
| `required-custom` | 项目必须具备，但当前环境未提供，需要后续创建。 |
| `recommended` | 推荐使用，但不是启动项目的硬性阻塞。 |
| `optional` | 可选增强能力。 |
| `missing` | 清单中声明，但本地未检测到。 |

## 3. 检查目录

`check-skills.sh` 会检查以下目录：

- `$HOME/.trae-cn/skills`
- `$HOME/.trae/skills`
- 仓库内 `.skills`
- 仓库内 `skills`

如果目录不存在，脚本不会失败，只会跳过。

## 4. 专项 Skill 创建策略

以下 skills 如果不存在，应后续用 `skill-creator` 创建：

- `unity-developer`
- `cocos-developer`
- `godot-developer`
- `unreal-developer`
- `game-ui-designer`
- `game-art-director`
- `game-ta`

创建时应参考：

- `docs/product/prd.md`
- `docs/product/feature-map.md`
- `docs/technical/engine-exporters.md`
- `docs/technical/plugin-protocol.md`
- `docs/technical/unity-ui-restyle.md`

## 5. Fallback 策略

在真实专项 skill 创建前，可以临时使用 fallback：

- 引擎开发：`fullstack-developer` + 对应技术文档。
- Game UI：`frontend-design` + `game-ui-designer` 清单描述。
- Game Art：`ai-app-designer` + `game-art-director` 清单描述。
- Game TA：`fullstack-developer` + `game-ta` 清单描述。

Fallback 只能用于文档和轻量规划，不应替代实际引擎插件实现阶段的专项 skill。

## 6. 推荐执行

```bash
bash scripts/loops/bootstrap.sh
```

输出中如果出现 `required-custom`，说明项目需要该能力，但当前环境还没有真实 skill。
