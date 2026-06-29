# 多引擎导出方案

## 1. 目标

多引擎导出器负责将统一资产 IR 转换为 Unity、Cocos Creator 3.x、Cocos Creator 2.x、Godot 可直接使用的资源结构。

核心原则：

- 输入统一：所有导出器读取同一资产 IR。
- 输出差异化：每个导出器生成目标引擎原生结构。
- 插件友好：导出包必须能被对应引擎插件一键导入。
- 可追踪：每个导出包包含 manifest 和日志。

## 2. 导出器接口

```ts
interface EngineExporter {
  engine: "unity" | "cocos3" | "cocos2" | "godot";
  supportedIrVersions: string[];
  validate(ir: AssetIr): ExportValidationResult;
  build(ir: AssetIr, options: ExportOptions): Promise<ExportPackage>;
}
```

## 3. 通用导出包结构

```text
export-package.zip
  ├─ manifest.json
  ├─ ir.json
  ├─ assets/
  │   ├─ images/
  │   ├─ fonts/
  │   └─ atlases/
  ├─ engine/
  │   └─ target-engine-files
  └─ logs/
      └─ export.log
```

## 4. Manifest

```json
{
  "package_id": "export_001",
  "project_id": "project_001",
  "ir_id": "ir_001",
  "engine": "unity",
  "engine_version": "2022.3+",
  "created_at": "2026-06-29T00:00:00Z",
  "assets": [],
  "entry": {
    "type": "prefab",
    "path": "engine/Unity/Prefabs/Demo.prefab"
  },
  "checksums": {}
}
```

## 5. Unity 导出

### 5.1 支持版本

- Unity 2022.3 LTS+
- Unity 6
- Windows/macOS/Linux Editor

### 5.2 输出结构

```text
Unity/
  ├─ Assets/
  │   └─ VberAI/
  │       └─ ProjectName/
  │           ├─ Textures/
  │           ├─ Sprites/
  │           ├─ Prefabs/
  │           ├─ Scenes/
  │           ├─ Materials/
  │           └─ Metadata/
  └─ manifest.json
```

### 5.3 组件映射

| IR Node | Unity Object |
| --- | --- |
| root | Canvas |
| group | GameObject + RectTransform |
| panel | GameObject + Image |
| image | GameObject + Image |
| icon | GameObject + Image |
| button | GameObject + Button + Image |
| text | GameObject + TextMeshProUGUI |
| progress_bar | GameObject + Image Fill 或 Slider |
| list | GameObject + Vertical/HorizontalLayoutGroup |
| input | GameObject + TMP_InputField |

### 5.4 RectTransform 转换

IR 使用左上角坐标，Unity UI 通常使用锚点和 pivot。

转换规则：

- 画布中心为 Unity 坐标原点。
- `unity_x = ir_x - canvas_width / 2 + width * pivot_x`
- `unity_y = canvas_height / 2 - ir_y - height * pivot_y`
- `sizeDelta = (width, height)`
- `anchorMin/anchorMax` 来自 IR layout。
- `pivot` 来自 IR layout。

### 5.5 Sprite 导入

- PNG 写入 `Textures`。
- 设置 TextureImporter：
  - Texture Type: Sprite
  - Sprite Mode: Single
  - Alpha Is Transparency: true
  - Pixels Per Unit: from export config
- 九宫格写入 Sprite border。

### 5.6 Prefab 生成

- 根节点生成 Canvas。
- 递归生成 GameObject。
- 根据 node type 添加组件。
- 绑定 Sprite/Text/Button。
- 保存为 Prefab。
- 可选生成 Scene。

### 5.7 UnityPackage

第一版可使用 ZIP + 插件导入方式。后续可支持 `.unitypackage`。

## 6. Cocos Creator 3.x 导出

### 6.1 支持版本

- Cocos Creator 3.8.6+

### 6.2 输出结构

```text
Cocos3/
  ├─ assets/
  │   └─ vberai/
  │       ├─ textures/
  │       ├─ prefabs/
  │       ├─ scenes/
  │       └─ metadata/
  └─ manifest.json
```

### 6.3 组件映射

| IR Node | Cocos 3.x |
| --- | --- |
| root | Canvas Node |
| group | Node + UITransform |
| panel | Node + Sprite |
| image | Sprite |
| icon | Sprite |
| button | Button + Sprite |
| text | Label |
| progress_bar | ProgressBar |
| list | Layout |
| input | EditBox |

### 6.4 坐标转换

- Cocos 节点坐标默认以父节点中心为参考。
- IR 左上角坐标转换为相对父节点坐标。
- Anchor 对应 UITransform anchor。

### 6.5 Prefab/Scene

- 生成 Prefab JSON。
- 生成 Scene JSON。
- 图片生成 ImageAsset/SpriteFrame。
- Meta 文件由插件导入时生成或刷新。

## 7. Cocos Creator 2.x 导出

### 7.1 支持版本

- Cocos Creator 2.4.x+

### 7.2 输出结构

```text
Cocos2/
  ├─ assets/
  │   └─ resources/
  │       └─ vberai/
  │           ├─ textures/
  │           ├─ prefabs/
  │           └─ scenes/
  └─ manifest.json
```

### 7.3 组件映射

| IR Node | Cocos 2.x |
| --- | --- |
| root | Canvas Node |
| group | cc.Node |
| panel | cc.Sprite |
| image | cc.Sprite |
| button | cc.Button |
| text | cc.Label |
| progress_bar | cc.ProgressBar |
| list | cc.Layout |
| input | cc.EditBox |

### 7.4 注意事项

- Cocos 2.x JSON 结构与 3.x 不兼容。
- 需要独立导出器，不应复用 3.x 文件结构。
- 插件需处理资源 UUID 和 meta 生成。

## 8. Godot 导出

### 8.1 支持版本

- Godot 4.x

### 8.2 输出结构

```text
Godot/
  ├─ vberai/
  │   ├─ textures/
  │   ├─ scenes/
  │   └─ metadata/
  └─ manifest.json
```

### 8.3 组件映射

| IR Node | Godot |
| --- | --- |
| root | Control |
| group | Control |
| panel | Panel / NinePatchRect |
| image | TextureRect |
| icon | TextureRect |
| button | TextureButton |
| text | Label |
| progress_bar | ProgressBar |
| list | VBoxContainer / HBoxContainer |
| input | LineEdit |

### 8.4 Scene 文件

- 生成 `.tscn`。
- 资源路径使用 `res://vberai/...`。
- 九宫格使用 NinePatchRect。
- 插件导入时复制资源并刷新 FileSystem。

## 9. 导出校验

导出前必须校验：

- IR 版本兼容。
- 根节点存在。
- 节点树无环。
- 所有资产引用存在。
- 图片文件可访问。
- 文本节点字段完整。
- 目标引擎支持节点类型。
- 九宫格边界合法。
- 导出路径无非法字符。

## 10. 导出失败处理

失败类型：

- `invalid_ir`
- `missing_asset`
- `unsupported_node_type`
- `asset_download_failed`
- `package_write_failed`
- `engine_template_failed`

处理方式：

- 记录错误节点和资产。
- 返回用户可读错误。
- 支持修正后重试。
- 保留失败导出日志。

## 11. 导出模板

### 11.1 Unity 模板

- 默认 Canvas 模式。
- 是否使用 TextMeshPro。
- 图片目录。
- Prefab 命名规则。
- Scene 命名规则。

### 11.2 Cocos 模板

- 资源根目录。
- Prefab 目录。
- Scene 目录。
- 是否生成资源 UUID。

### 11.3 Godot 模板

- `res://` 根路径。
- Scene 入口名称。
- Texture 导入策略。

## 12. 插件导入策略

导出器只负责生成包，插件负责导入到真实项目中：

- 下载包。
- 解压到临时目录。
- 读取 manifest。
- 复制资源到项目。
- 创建或更新节点/Prefab/Scene。
- 处理冲突。
- 刷新编辑器资源。
- 回写状态。

## 13. 冲突处理

冲突类型：

- 同名资源存在。
- Prefab 已存在。
- Scene 已存在。
- 字体缺失。
- 插件版本不兼容。

策略：

- 覆盖
- 跳过
- 重命名
- 创建新版本
- 手动确认

## 14. 里程碑

### 14.1 M1 Unity

- IR 到 Unity ZIP。
- Unity 插件导入。
- Canvas/Prefab 可见。

### 14.2 M2 Cocos 3.x

- IR 到 Cocos 3.x Prefab。
- Cocos 插件导入。

### 14.3 M3 Godot

- IR 到 Godot TSCN。
- Godot 插件导入。

### 14.4 M4 Cocos 2.x

- IR 到 Cocos 2.x Prefab。
- 插件兼容老项目。
