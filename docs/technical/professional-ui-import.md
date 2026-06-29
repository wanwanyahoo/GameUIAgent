# PSD/Figma 专业 UI 工具导入方案

## 1. 目标

平台必须支持从 PSD、Figma 等专业 UI 工具导入已有分层设计，并自动转换为 Unity、Cocos、Godot 可用资产。

该能力不是把设计稿当作单张图片重新 AI 识别，而是优先读取专业工具中的结构化信息：

- 图层
- 图层组
- Frame
- Component
- Instance
- Auto Layout
- Constraints
- 文本样式
- 图片资源
- 可见性
- 透明度
- 层级和坐标

只有当输入是扁平图片，或 PSD/Figma 某些结构信息缺失时，才使用 AI 自动切分补全。

## 2. 支持范围

### 2.1 PSD

必须支持：

- PSD 文件上传
- 图层组解析
- 普通图层解析
- 文本图层解析
- 智能对象识别
- 图层可见性
- 图层透明度
- 图层坐标和尺寸
- 图层裁剪为 PNG
- 图层命名保留
- 图层顺序保留
- 图层组转 UI Group/Panel
- 文本图层转 Text/TMP
- 图片图层转 Image/Sprite

建议支持：

- 混合模式近似映射
- 图层效果栅格化
- 剪贴蒙版展开
- 九宫格候选推断
- 按钮状态命名识别

暂不强制支持：

- 完整 Photoshop 特效无损还原
- 复杂智能对象内部编辑
- 复杂 3D 图层

### 2.2 Figma

必须支持：

- Figma 文件链接导入
- Figma API Token
- File/Node 获取
- Frame 选择
- Group 解析
- Component 解析
- Instance 展开
- Auto Layout 解析
- Constraints 解析
- 文本节点解析
- 图片 Fill 导出
- Vector 导出 SVG/PNG
- 节点命名保留
- 组件层级保留

建议支持：

- Variant 转按钮状态
- Component Set 转 UI Component
- Figma Tokens/Variables 映射样式
- Auto Layout 转 Unity LayoutGroup
- Constraints 转锚点

## 3. 导入架构

```text
PSD File / Figma Link
  │
  ▼
Professional Import API
  │
  ├─ PSD Parser
  │   ├─ Layer Tree
  │   ├─ Text Layers
  │   ├─ Rasterized Slices
  │   └─ Metadata
  │
  └─ Figma Importer
      ├─ File Nodes
      ├─ Frames
      ├─ Components
      ├─ Images
      └─ Metadata
        │
        ▼
Design Layer Document
        │
        ▼
IR Builder
        │
        ▼
Asset IR
        │
        ├─ Unity Exporter
        ├─ Cocos Exporter
        └─ Godot Exporter
```

## 4. 专业导入 API

### 4.1 上传 PSD

```http
POST /api/projects/{project_id}/imports/psd
Content-Type: multipart/form-data
```

请求：

- `file`: PSD 文件
- `target_engine`: `unity` / `cocos3` / `cocos2` / `godot`
- `parse_text`: 是否解析文本图层
- `rasterize_effects`: 是否栅格化图层效果

响应：

```json
{
  "import_job_id": "import_001",
  "status": "queued"
}
```

### 4.2 导入 Figma

```http
POST /api/projects/{project_id}/imports/figma
```

请求：

```json
{
  "file_url": "https://www.figma.com/file/xxx",
  "node_id": "1:2",
  "figma_token_id": "token_001",
  "target_engine": "unity",
  "include_components": true,
  "expand_instances": true
}
```

响应：

```json
{
  "import_job_id": "import_002",
  "status": "queued"
}
```

### 4.3 查询导入任务

```http
GET /api/import-jobs/{import_job_id}
```

响应：

```json
{
  "id": "import_001",
  "type": "psd",
  "status": "succeeded",
  "progress": 100,
  "output": {
    "design_document_id": "design_doc_001",
    "ir_id": "ir_001",
    "asset_count": 48,
    "node_count": 73,
    "warnings": []
  }
}
```

## 5. Design Layer Document

Design Layer Document 是 PSD/Figma 到资产 IR 之间的中间结构，保留专业工具原始语义。

```json
{
  "id": "design_doc_001",
  "source": {
    "type": "figma",
    "file_id": "figma_file_id",
    "node_id": "1:2"
  },
  "canvas": {
    "width": 1920,
    "height": 1080
  },
  "layers": [
    {
      "id": "layer_001",
      "source_id": "12:34",
      "parent_id": null,
      "name": "StartButton",
      "kind": "component",
      "visible": true,
      "opacity": 1,
      "bounds": {
        "x": 100,
        "y": 200,
        "width": 320,
        "height": 96
      },
      "style": {},
      "text": null,
      "asset_id": "asset_button_png",
      "children": []
    }
  ]
}
```

## 6. PSD 映射规则

| PSD 元素 | Design Layer | Asset IR | Unity |
| --- | --- | --- | --- |
| Root Document | canvas | root | Canvas |
| Layer Group | group | group/panel | GameObject |
| Raster Layer | bitmap | image/icon/panel | Image |
| Text Layer | text | text | TextMeshProUGUI |
| Smart Object | smart_object | image/component | Image/Prefab |
| Hidden Layer | visible=false | active=false | GameObject inactive |
| Opacity | opacity | transform.opacity | CanvasGroup/Image alpha |
| Layer Bounds | bounds | transform | RectTransform |

## 7. Figma 映射规则

| Figma 元素 | Design Layer | Asset IR | Unity |
| --- | --- | --- | --- |
| Page/Frame | frame | root/panel | Canvas/GameObject |
| Group | group | group | GameObject |
| Component | component | component | Prefab |
| Instance | instance | component instance | Prefab instance 或展开节点 |
| Rectangle/Image Fill | shape/image | image/panel | Image |
| Text | text | text | TextMeshProUGUI |
| Auto Layout | layout | layout | LayoutGroup |
| Constraints | constraints | anchor | RectTransform anchors |
| Variant | variant | interaction states | Button states |

## 8. Unity 转换规则

### 8.1 图层到 GameObject

- 每个可见图层默认生成一个 GameObject。
- 图层组生成空 GameObject。
- 图片图层生成 Image。
- 文本图层生成 TextMeshProUGUI。
- 按钮组件生成 Button + Image + Text。
- Component 可生成 Prefab。

### 8.2 坐标转换

专业工具坐标通常为左上角原点，Unity UI 需要转换为 RectTransform：

```text
unity_x = layer_x - canvas_width / 2 + layer_width * pivot_x
unity_y = canvas_height / 2 - layer_y - layer_height * pivot_y
```

### 8.3 Auto Layout 到 Unity

Figma Auto Layout 映射：

- Vertical Auto Layout → VerticalLayoutGroup
- Horizontal Auto Layout → HorizontalLayoutGroup
- Padding → LayoutGroup padding
- Gap → spacing
- Hug contents → ContentSizeFitter
- Fill container → anchors stretch

### 8.4 Constraints 到 Unity

Figma Constraints 映射：

- Left/Top → fixed anchor near left/top
- Right/Bottom → fixed anchor near right/bottom
- Left and Right → horizontal stretch
- Top and Bottom → vertical stretch
- Center → center anchor
- Scale → proportional layout metadata

### 8.5 PSD 文本到 Unity

- PSD 文本内容 → TextMeshProUGUI.text
- 字号 → fontSize
- 颜色 → color
- 对齐 → alignment
- 字体名 → font fallback 或待绑定字体
- 不支持字体时标记 warning

## 9. Cocos/Godot 转换

PSD/Figma 首先转换到资产 IR，再由现有 exporter 转目标引擎。

### 9.1 Cocos

- 图层组 → Node
- 图片 → Sprite
- 文本 → Label
- Auto Layout → Layout
- Button Component → Button

### 9.2 Godot

- 图层组 → Control
- 图片 → TextureRect
- 文本 → Label
- Button Component → Button/TextureButton
- 九宫格 → NinePatchRect

## 10. 与 AI 自动切分的关系

专业工具导入优先级高于 AI 切分：

1. 如果 PSD/Figma 有完整图层，直接用图层生成 IR。
2. 如果某个图层是扁平合成图，可对该图层局部运行 AI 切分。
3. 如果图层命名不规范，可用 AI 自动命名。
4. 如果组件状态不完整，可用 AI 推断按钮状态。
5. 如果锚点缺失，可根据位置和 Figma Constraints 推断。

## 11. 导入检查项

导入完成后需要给用户展示检查结果：

- 图层数量
- 资源数量
- 文本数量
- 组件数量
- 未支持图层效果
- 缺失字体
- 过大图片
- 无法映射的图层
- 需要人工确认的布局

## 12. 错误处理

| 错误码 | 含义 |
| --- | --- |
| `PSD_PARSE_FAILED` | PSD 解析失败 |
| `PSD_LAYER_UNSUPPORTED` | 存在不支持的 PSD 图层 |
| `FIGMA_AUTH_FAILED` | Figma Token 无效 |
| `FIGMA_FILE_NOT_FOUND` | Figma 文件不存在或无权限 |
| `FIGMA_NODE_NOT_FOUND` | 指定 Node 不存在 |
| `FONT_MISSING` | 字体缺失 |
| `ASSET_EXPORT_FAILED` | 图层资源导出失败 |
| `IR_BUILD_FAILED` | IR 生成失败 |

## 13. 验收标准

### 13.1 PSD 到 Unity

- 上传包含图层组、图片图层、文本图层的 PSD。
- 系统生成 Design Layer Document。
- 系统生成资产 IR。
- Unity Exporter 生成导出包。
- Unity 插件导入后生成 Canvas、Image、TextMeshPro、Prefab/Scene。
- 图层层级、坐标、尺寸、可见性基本一致。

### 13.2 Figma 到 Unity

- 输入 Figma 文件链接和 Frame。
- 系统读取 Frame、Group、Component、Text、Auto Layout。
- 系统生成资产 IR。
- Unity 导入后保留基础层级、文本、图片和布局。
- Component 可作为 Prefab 或 Prefab-like 结构导入。

### 13.3 缺失信息补全

- 不支持的图层效果有 warning。
- 缺失字体有 warning。
- 扁平图层可选择 AI 自动切分。
- 用户能在 AI Studio 中人工修正。

## 14. 实现优先级

### 14.1 第一版

- Figma Frame 导入
- PSD 基础图层解析
- 图片/文本/组映射
- Design Layer Document
- IR Builder
- Unity 导出

### 14.2 第二版

- Figma Component/Instance
- Auto Layout 映射
- PSD 智能对象
- 字体管理
- Cocos/Godot 导出

### 14.3 第三版

- Figma Variables
- Component Variants 转按钮状态
- PSD 图层效果近似还原
- 批量导入多个 Frame
