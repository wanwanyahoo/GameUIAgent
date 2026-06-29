# 游戏 UI 资产中间表示 IR

## 1. 设计目标

资产 IR 是平台的核心协议。它把 AI Studio 中的 UI 画布、AI 切分结果和多引擎导出解耦。

IR 必须满足：

- 能表达游戏 UI 图片切分后的元素层级。
- 能表达坐标、尺寸、锚点、九宫格、状态和资源引用。
- 能映射到 Unity、Cocos Creator、Godot。
- 能被 Web 编辑器读写。
- 能被导出器稳定转换。
- 能支持人工修正和版本管理。

## 2. IR 生命周期

```text
Uploaded Image / Generated Image
  │
  ▼
Segmentation Result
  │
  ▼
Draft IR
  │
  ▼
User Edited IR
  │
  ├─► Unity Exporter
  ├─► Cocos 3.x Exporter
  ├─► Cocos 2.x Exporter
  └─► Godot Exporter
```

## 3. 顶层结构

```json
{
  "version": "1.0.0",
  "project_id": "project_001",
  "document_id": "ir_001",
  "name": "rpg_inventory_screen",
  "target": {
    "primary_engine": "unity",
    "supported_engines": ["unity", "cocos3", "cocos2", "godot"]
  },
  "canvas": {},
  "assets": [],
  "nodes": [],
  "components": [],
  "states": [],
  "export": {},
  "metadata": {}
}
```

## 4. Canvas

Canvas 描述设计画布和目标分辨率。

```json
{
  "canvas": {
    "width": 1920,
    "height": 1080,
    "orientation": "landscape",
    "background_color": "#000000",
    "unit": "px",
    "safe_area": {
      "left": 0,
      "top": 0,
      "right": 0,
      "bottom": 0
    }
  }
}
```

字段说明：

- `width`：画布宽度。
- `height`：画布高度。
- `orientation`：`landscape` 或 `portrait`。
- `unit`：默认 `px`。
- `safe_area`：移动设备安全区。

## 5. Asset

Asset 描述图片、字体、图集、材质等资源。

```json
{
  "id": "asset_button_bg",
  "type": "image",
  "name": "button_bg",
  "source": {
    "kind": "slice",
    "uri": "assets/slices/button_bg.png",
    "original_asset_id": "asset_source_image"
  },
  "size": {
    "width": 320,
    "height": 96
  },
  "format": "png",
  "alpha": true,
  "hash": "sha256",
  "tags": ["button", "fantasy"]
}
```

### 5.1 Asset Type

- `image`
- `font`
- `atlas`
- `material`
- `audio`
- `json`
- `unknown`

### 5.2 Source Kind

- `upload`
- `generated`
- `slice`
- `matting`
- `inpaint`
- `psd_layer`
- `figma_node`
- `external`

## 6. Node

Node 是 UI 层级树的基础单位。

```json
{
  "id": "node_start_button",
  "parent_id": "node_root",
  "name": "StartButton",
  "type": "button",
  "active": true,
  "locked": false,
  "transform": {},
  "layout": {},
  "visual": {},
  "interaction": {},
  "children": []
}
```

## 7. Node Type

基础类型：

- `root`
- `group`
- `panel`
- `image`
- `button`
- `icon`
- `text`
- `input`
- `progress_bar`
- `slider`
- `list`
- `list_item`
- `decorator`
- `custom`

## 8. Transform

```json
{
  "transform": {
    "x": 120,
    "y": 80,
    "width": 320,
    "height": 96,
    "rotation": 0,
    "scale_x": 1,
    "scale_y": 1,
    "opacity": 1,
    "z_index": 10
  }
}
```

坐标默认以画布左上角为原点。导出器负责转换为目标引擎坐标系。

## 9. Layout

```json
{
  "layout": {
    "anchor_min": { "x": 0.5, "y": 0.5 },
    "anchor_max": { "x": 0.5, "y": 0.5 },
    "pivot": { "x": 0.5, "y": 0.5 },
    "margin": {
      "left": 0,
      "top": 0,
      "right": 0,
      "bottom": 0
    },
    "fit": "fixed",
    "responsive": false
  }
}
```

### 9.1 Fit

- `fixed`
- `stretch`
- `contain`
- `cover`
- `center`

## 10. Visual

```json
{
  "visual": {
    "asset_id": "asset_button_bg",
    "color": "#FFFFFF",
    "tint": "#FFFFFF",
    "slice_9": {
      "enabled": true,
      "left": 24,
      "right": 24,
      "top": 20,
      "bottom": 20
    },
    "raycast_target": true
  }
}
```

## 11. Text

```json
{
  "text": {
    "content": "Start",
    "font_asset_id": "font_main",
    "font_size": 32,
    "color": "#FFFFFF",
    "align": "center",
    "vertical_align": "middle",
    "overflow": "shrink"
  }
}
```

### 11.1 Text Align

- `left`
- `center`
- `right`
- `justify`

### 11.2 Vertical Align

- `top`
- `middle`
- `bottom`

## 12. Interaction

```json
{
  "interaction": {
    "clickable": true,
    "states": {
      "normal": "asset_button_normal",
      "pressed": "asset_button_pressed",
      "disabled": "asset_button_disabled",
      "hover": "asset_button_hover"
    },
    "action": {
      "type": "event",
      "name": "on_start_clicked"
    }
  }
}
```

## 13. Component

Component 用于表达可复用 UI 组件。

```json
{
  "id": "component_inventory_item",
  "name": "InventoryItem",
  "root_node_id": "node_inventory_item",
  "slots": [
    {
      "name": "icon",
      "node_id": "node_item_icon",
      "type": "image"
    },
    {
      "name": "count",
      "node_id": "node_item_count",
      "type": "text"
    }
  ]
}
```

## 14. State

State 描述不同 UI 状态。

```json
{
  "id": "state_button_pressed",
  "target_node_id": "node_start_button",
  "name": "pressed",
  "overrides": {
    "visual.asset_id": "asset_button_pressed",
    "transform.scale_x": 0.98,
    "transform.scale_y": 0.98
  }
}
```

## 15. Export Config

```json
{
  "export": {
    "unity": {
      "canvas_mode": "ScreenSpaceOverlay",
      "pixels_per_unit": 100,
      "use_text_mesh_pro": true,
      "generate_prefab": true,
      "generate_scene": true,
      "sprite_atlas": true
    },
    "cocos3": {
      "generate_prefab": true,
      "generate_scene": true,
      "asset_root": "assets/vberai"
    },
    "cocos2": {
      "generate_prefab": true,
      "asset_root": "assets/resources/vberai"
    },
    "godot": {
      "generate_tscn": true,
      "asset_root": "res://vberai"
    }
  }
}
```

## 16. Metadata

```json
{
  "metadata": {
    "created_by": "user_001",
    "created_at": "2026-06-29T00:00:00Z",
    "updated_at": "2026-06-29T00:00:00Z",
    "source_job_id": "job_001",
    "source_import_id": "import_001",
    "source_design_document_id": "design_doc_001",
    "source_tool": "figma",
    "source_prompt": "fantasy rpg inventory ui",
    "model": "provider/model",
    "confidence": 0.86
  }
}
```

## 17. Professional Source

当 IR 来自 PSD/Figma 导入时，节点和资产需要保留原始专业工具来源，便于回溯、增量更新和重新导入。

```json
{
  "professional_source": {
    "tool": "figma",
    "file_id": "figma_file_id",
    "node_id": "12:34",
    "layer_path": "MainMenu/StartButton/Text",
    "component_id": "component_001",
    "is_instance": true
  }
}
```

PSD 示例：

```json
{
  "professional_source": {
    "tool": "psd",
    "file_asset_id": "asset_psd_001",
    "layer_id": "layer_42",
    "layer_path": "MainMenu/Buttons/Start",
    "layer_kind": "text"
  }
}
```

## 18. 引擎映射

### 17.1 Unity

| IR | Unity |
| --- | --- |
| `root` | Canvas |
| `panel` | GameObject + Image |
| `image` | Image |
| `button` | Button + Image |
| `text` | TextMeshProUGUI |
| `progress_bar` | Slider 或 Image Fill |
| `transform` | RectTransform |
| `slice_9` | Sprite Border |

### 17.2 Cocos Creator 3.x

| IR | Cocos 3.x |
| --- | --- |
| `root` | Canvas Node |
| `panel` | Node + Sprite |
| `image` | Sprite |
| `button` | Button + Sprite |
| `text` | Label |
| `transform` | UITransform |
| `slice_9` | Sprite Type Sliced |

### 17.3 Cocos Creator 2.x

| IR | Cocos 2.x |
| --- | --- |
| `root` | Canvas Node |
| `panel` | cc.Node + cc.Sprite |
| `image` | cc.Sprite |
| `button` | cc.Button |
| `text` | cc.Label |
| `transform` | Node position/size |
| `slice_9` | cc.Sprite.Type.SLICED |

### 17.4 Godot

| IR | Godot |
| --- | --- |
| `root` | Control |
| `panel` | Panel 或 NinePatchRect |
| `image` | TextureRect |
| `button` | TextureButton |
| `text` | Label |
| `transform` | Control position/size |
| `slice_9` | NinePatchRect |

## 19. 校验规则

- 所有 `id` 必须唯一。
- 所有 `asset_id` 必须存在。
- `parent_id` 必须形成无环树。
- 根节点必须存在且唯一。
- 坐标和尺寸必须为数字。
- 导出目标必须在 `supported_engines` 中。
- 交互状态引用的资产必须存在。
- 文本节点必须包含 `text.content`。

## 20. 版本策略

- `version` 使用语义化版本。
- 向后兼容字段只能新增，不能改变含义。
- 导出器需要声明支持的 IR 版本范围。
- 迁移脚本负责旧 IR 升级。

## 21. 最小可用 IR 示例

```json
{
  "version": "1.0.0",
  "project_id": "project_demo",
  "document_id": "ir_demo",
  "name": "demo_ui",
  "target": {
    "primary_engine": "unity",
    "supported_engines": ["unity", "cocos3", "cocos2", "godot"]
  },
  "canvas": {
    "width": 1920,
    "height": 1080,
    "orientation": "landscape",
    "unit": "px"
  },
  "assets": [
    {
      "id": "asset_bg",
      "type": "image",
      "name": "background",
      "source": { "kind": "slice", "uri": "assets/background.png" },
      "size": { "width": 1920, "height": 1080 },
      "format": "png",
      "alpha": true
    }
  ],
  "nodes": [
    {
      "id": "node_root",
      "parent_id": null,
      "name": "Root",
      "type": "root",
      "transform": { "x": 0, "y": 0, "width": 1920, "height": 1080, "z_index": 0 },
      "children": ["node_bg"]
    },
    {
      "id": "node_bg",
      "parent_id": "node_root",
      "name": "Background",
      "type": "image",
      "transform": { "x": 0, "y": 0, "width": 1920, "height": 1080, "z_index": 1 },
      "visual": { "asset_id": "asset_bg" },
      "children": []
    }
  ]
}
```
