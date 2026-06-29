# Unity 已有 UI 换风格专项方案

## 1. 目标

支持对 Unity 项目中已经存在的 UI 进行 AI 换风格，并保持原有布局、节点层级、组件绑定和交互逻辑不变。

用户希望的核心链路是：

```text
Unity 已有 UI
  │
  ▼
导出布局 JSON + 图片资源
  │
  ▼
还原为一张有布局的合成图
  │
  ▼
AI 保持布局不变进行换风格
  │
  ▼
按照原始布局切回独立 UI 资源
  │
  ▼
自动替换 Unity 原资源 / 生成新变体
```

该链路应作为「引擎反向回流」的核心子能力，不只是普通图片风格迁移。

## 2. 使用场景

### 2.1 已上线项目 UI 换皮

项目已有完整 Unity UI，策划或美术希望快速生成节日版、赛博朋克版、二次元版、暗黑版等新风格，但不能破坏已有按钮、锚点、脚本和事件绑定。

### 2.2 多主题批量生成

同一套 UI 布局需要生成多个主题包，例如：

- 默认主题。
- 春节主题。
- 万圣节主题。
- 科幻主题。
- 低饱和主题。

### 2.3 老项目美术升级

保留 Unity 现有 UI 结构和业务逻辑，仅替换 Sprite、背景、面板、按钮、图标等视觉资源。

## 3. Unity 导出内容

Unity 插件需要从 Scene 或 Prefab 中捕获完整 UI 快照。

### 3.1 Layout JSON

```json
{
  "snapshot_id": "snapshot_001",
  "engine": "unity",
  "scene_or_prefab": "Assets/UI/MainMenu.prefab",
  "canvas": {
    "width": 1920,
    "height": 1080,
    "scale_mode": "ScaleWithScreenSize"
  },
  "nodes": [
    {
      "id": "node_start_button",
      "path": "Canvas/MainPanel/StartButton",
      "type": "button",
      "rect": {
        "x": 760,
        "y": 820,
        "width": 400,
        "height": 96
      },
      "anchors": {
        "min": { "x": 0.5, "y": 0.5 },
        "max": { "x": 0.5, "y": 0.5 },
        "pivot": { "x": 0.5, "y": 0.5 }
      },
      "components": ["Image", "Button"],
      "sprite_asset_id": "asset_start_button",
      "text": null,
      "event_bindings": [
        {
          "event": "onClick",
          "target": "MainMenuController",
          "method": "OnStartClicked"
        }
      ]
    }
  ]
}
```

### 3.2 图片资源

需要导出：

- 原始 Sprite PNG。
- Sprite Atlas 中的子图。
- 九宫格 border。
- Image type：Simple、Sliced、Filled、Tiled。
- Sprite pivot。
- Pixels Per Unit。
- 资源 GUID。
- 原始 Asset 路径。

### 3.3 文本和字体

需要导出：

- Text 或 TextMeshProUGUI 内容。
- 字体。
- 字号。
- 颜色。
- 对齐。
- Outline/Shadow 等效果摘要。

### 3.4 保留项

换风格时默认不改：

- 节点层级。
- RectTransform。
- Anchor。
- Pivot。
- LayoutGroup。
- ContentSizeFitter。
- Button 事件。
- 脚本挂载。
- Localization key。
- Animator 绑定。
- 资源引用路径，除非用户选择生成新主题目录。

## 4. 合成布局图

平台根据 Layout JSON 和图片资源还原一张用于 AI 换风格的合成图。

### 4.1 合成规则

- 按 Unity 层级和 sorting 顺序绘制。
- 按 RectTransform 计算位置和大小。
- 按 alpha、颜色 tint、mask、九宫格进行近似渲染。
- 文本可选择保留、隐藏或转为占位块。
- 可导出辅助 mask 和 layout guide。

### 4.2 输出

```text
composite/
  ├─ layout_preview.png
  ├─ layout_mask.png
  ├─ element_masks/
  │   ├─ node_start_button.png
  │   └─ node_panel_bg.png
  └─ layout.json
```

## 5. AI 换风格

### 5.1 输入

- `layout_preview.png`
- `layout_mask.png`
- 原始 Layout JSON。
- 用户风格 Prompt。
- Negative Prompt。
- 风格参考图，可选。
- 保持布局强度。
- 保持文本区域策略。

### 5.2 约束

AI 换风格必须遵守：

- 不改变 UI 元素位置。
- 不改变主要元素尺寸。
- 不打乱按钮、面板、图标区域。
- 不破坏透明区域。
- 不生成额外不可切分装饰遮挡交互区域。
- 文本区域可留空、弱化或保留原文字。

### 5.3 输出

- `restyled_composite.png`
- `style_report.json`
- 可选多候选结果。

## 6. 按原布局切回资源

切回资源时不依赖 AI 重新猜布局，而是使用原始 Layout JSON。

### 6.1 切片规则

- 每个可替换视觉节点按原 rect 裁切。
- 保留原始透明边界。
- 按原节点类型决定输出格式。
- 九宫格资源保留原 border。
- Filled/Tiled 类型保留原 Unity Image 设置。
- 文本节点默认不裁切，除非用户选择文字也风格化为图片。

### 6.2 输出结构

```text
restyle-output/
  ├─ manifest.json
  ├─ layout.json
  ├─ replacements/
  │   ├─ node_start_button.png
  │   ├─ node_panel_bg.png
  │   └─ node_icon_shop.png
  └─ preview/
      ├─ before.png
      └─ after.png
```

## 7. 自动替换回 Unity

Unity 插件需要支持两种模式。

### 7.1 原地替换

- 根据 `resource_guid` 或 `asset_path` 找到原 Sprite。
- 备份原资源。
- 用新 PNG 覆盖或重新导入。
- 保持 GUID 尽量不变。
- 保持 Prefab 和 Scene 引用不变。

适合快速换皮，但风险较高。

### 7.2 新主题目录

- 在 `Assets/VberAI/Themes/{theme_name}` 创建新资源。
- 复制 Prefab 或生成 Variant。
- 将新 Sprite 绑定到新 Prefab。
- 原始 UI 不变。

推荐作为默认策略。

## 8. Manifest

```json
{
  "restyle_job_id": "restyle_001",
  "source_snapshot_id": "snapshot_001",
  "strategy": "theme_variant",
  "theme_name": "cyberpunk",
  "replacements": [
    {
      "node_id": "node_start_button",
      "unity_path": "Canvas/MainPanel/StartButton",
      "original_asset_path": "Assets/UI/Buttons/start.png",
      "new_asset_path": "Assets/VberAI/Themes/cyberpunk/start.png",
      "preserve_guid": false,
      "image_type": "Sliced",
      "border": { "left": 12, "right": 12, "top": 10, "bottom": 10 }
    }
  ]
}
```

## 9. 与 Asset IR 的关系

Unity Layout JSON 会转换为资产 IR，并额外保留 Unity 专属字段：

- `unity_guid`
- `unity_asset_path`
- `unity_component_type`
- `unity_image_type`
- `unity_sprite_border`
- `unity_event_bindings`
- `unity_prefab_path`

换风格后的资源通过 IR 的 asset replacement 关系回写。

## 10. AI Studio 交互

### 10.1 页面

- Unity UI 快照列表。
- 原始 UI 预览。
- 合成图预览。
- 风格 Prompt。
- 风格参考图。
- 保持布局强度。
- 文字处理策略。
- 多候选结果。
- 切片预览。
- 替换策略：原地替换 / 新主题目录。
- Unity 回写状态。

### 10.2 用户确认点

- 确认需要换风格的节点范围。
- 确认是否保留文本。
- 确认是否保留按钮状态。
- 确认替换策略。
- 确认生成主题名称。

## 11. 验收标准

### 11.1 Demo

1. Unity 打开已有 UI Prefab。
2. 插件导出 Layout JSON 和 Sprite 图片。
3. 平台合成完整布局图。
4. 用户输入风格 Prompt。
5. AI 生成保持布局的新风格图。
6. 平台按原 Layout JSON 切回资源。
7. Unity 插件拉取 replacement manifest。
8. 插件生成新主题 Prefab。
9. 新 Prefab 保持原布局、事件、脚本绑定。
10. 视觉资源已替换为新风格。

### 11.2 成功标准

- RectTransform 不变化。
- Button onClick 绑定不丢失。
- 原始 Prefab 可选择不被覆盖。
- 新主题 Prefab 可独立预览。
- 替换资源数量和 manifest 一致。
- 生成前后对比图可查看。

## 12. 风险和限制

- 复杂 Mask、Shader、粒子和动态运行时 UI 难以完全静态合成。
- TextMeshPro 特效和字体渲染可能无法 100% 复刻。
- 九宫格资源换风格后需要检查边缘是否仍可拉伸。
- 原地替换需要备份和回滚。
- AI 可能破坏局部边界，因此必须支持按原布局裁切和人工修正。

## 13. 实现优先级

### 13.1 第一版

- Unity Prefab/Scene 快照。
- Layout JSON。
- Sprite 图片导出。
- 合成布局图。
- Prompt 换风格。
- 按原 rect 切片。
- 新主题目录替换。

### 13.2 第二版

- 原地替换与回滚。
- 九宫格智能修正。
- 按节点选择换风格范围。
- 批量主题生成。

### 13.3 第三版

- 动态 UI 捕获。
- 多分辨率主题包。
- 自动风格一致性评估。
- 与 Localization 和皮肤系统集成。
