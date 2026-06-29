# 功能地图与防遗漏清单

## 1. 功能总览

平台功能分为 10 个一级域：

- 官网门户
- 账号与团队
- 项目空间
- AI Studio
- AI 图像生成与处理
- UI 自动切分
- 资产管理
- 多引擎导出
- 引擎插件
- 文档与商业化

## 2. 官网门户

### 2.1 必备页面

- 首页
- 产品总览
- AI Studio 页面
- Engine MCP 页面
- AI 超强抠图页面
- Unity MCP 页面
- Cocos MCP 3.x 页面
- Cocos MCP 2.x 页面
- Godot MCP 页面
- 定价页面
- 文档中心
- 联系我们
- 服务条款
- 隐私政策

### 2.2 首页模块

- 顶部导航
- 登录/注册
- 汉堡菜单
- 语言切换
- 深色/浅色主题切换
- Hero 首屏
- 产品探索下拉
- 三大产品卡片
- 四步生产流程
- AI 抠图演示
- Production Stack
- AI Studio 介绍
- Engine MCP 介绍
- 最终 CTA
- Footer

### 2.3 官网交互

- 产品下拉菜单
- 锚点滚动
- 登录/注册跳转
- 体验 AI Studio 跳转
- 进入 AI 超强抠图跳转
- 定价跳转
- 外链：B 站、GitHub、客服
- 响应式移动菜单

## 3. 账号与团队

### 3.1 用户账号

- 注册
- 登录
- 退出
- 密码重置
- 用户资料
- 头像
- 语言偏好
- 默认目标引擎

### 3.2 团队空间

- 创建团队
- 邀请成员
- 移除成员
- 修改成员角色
- 团队项目列表
- 团队资产库
- 团队用量统计

### 3.3 权限

- Owner：所有权限
- Admin：项目和成员管理
- Designer：生成、编辑、切分、导出
- Developer：导出、插件导入、查看资产
- Viewer：只读

### 3.4 凭证

- API Key
- 插件访问 Token
- Token 过期时间
- Token 撤销
- 插件设备列表

## 4. 项目空间

### 4.1 项目管理

- 创建项目
- 编辑项目名称
- 设置目标引擎
- 设置分辨率
- 设置设计规范
- 归档项目
- 删除项目
- 复制项目

### 4.2 项目配置

- 目标引擎：Unity、Cocos 3.x、Cocos 2.x、Godot
- UI 类型：移动竖屏、移动横屏、PC、平板、自定义
- 设计尺寸
- 资源命名规则
- 导出路径模板
- 字体配置
- 图集配置

### 4.3 项目仪表盘

- 最近画布
- 最近生成任务
- 最近导出任务
- 插件连接状态
- 资源数量
- 错误提醒

## 5. AI Studio

### 5.1 工作区布局

- 顶部项目栏
- 左侧素材库
- 左侧图层树
- 中央画布
- 右侧属性面板
- 右侧 AI 参数面板
- 右侧 Design 面板
- AI Notes
- AI Chat
- 底部任务面板
- 导出入口

### 5.2 专业 UI 工具导入

- PSD 文件上传
- PSB 文件上传
- PSD 图层组解析
- PSD 文本图层解析
- PSD 智能对象识别
- PSD 可见性和透明度保留
- PSD 图层导出为切片
- Figma 文件链接导入
- Figma Frame 选择
- Figma Component 导入
- Figma Instance 展开
- Figma Auto Layout 解析
- Figma Constraints 解析
- Figma 图片资源下载
- Figma 文本样式解析
- Figma 组件状态识别
- 专业工具图层映射为资产 IR
- 专业工具图层直接导出 Unity UI
- 引擎场景/Prefab 反向导入为可编辑画布
- Unity 已有 UI 导出 Layout JSON
- Unity 已有 UI 导出 Sprite/Atlas 图片
- Unity 已有 UI 合成布局预览图
- Unity 已有 UI 保持布局换风格
- Unity 已有 UI 按原布局切回资源
- Unity 已有 UI 自动替换或生成新主题 Prefab

### 5.3 画布能力

- 图片放置
- 图片缩放
- 图片裁剪
- 图层选择
- 多选
- 对齐
- 锁定
- 隐藏
- 重命名
- 分组
- 撤销/重做

### 5.4 图层树

- 背景
- 面板
- 按钮
- 图标
- 文本
- 进度条
- 输入框
- 列表项
- 装饰元素
- 自定义组件

### 5.5 属性面板

- 名称
- 类型
- 坐标
- 尺寸
- 旋转
- 透明度
- 锚点
- 九宫格
- 交互状态
- 导出路径
- 引擎组件映射

## 6. AI 图像生成与处理

### 6.1 文生图

- Prompt 输入
- Negative Prompt
- 风格选择
- 尺寸选择
- Seed
- 生成数量
- 模型选择
- 结果保存

### 6.2 图生图

- 上传参考图
- 强度控制
- 风格迁移
- 构图保持
- 多候选生成
- 结果对比

### 6.3 局部重绘

- 选择重绘区域
- 蒙版编辑
- Prompt 控制
- 边缘融合
- 版本保存

### 6.4 抠图

- 人物抠图
- 物体抠图
- UI 元素抠图
- 半透明边缘
- 发丝边缘
- Alpha 通道输出

### 6.5 后处理

- 超分辨率
- 去噪
- 锐化
- 色彩调整
- 背景替换
- PNG/JPG/WebP 导出

## 7. UI 自动切分

### 7.1 检测能力

- 元素边界框
- 元素类型
- 图层层级
- 文本区域
- 按钮区域
- 图标区域
- 背景区域
- 面板区域
- 重复列表项

### 7.2 切分能力

- 自动切片
- 手动框选
- 合并切片
- 拆分切片
- 调整边界
- 忽略元素
- 重新识别

### 7.3 结构化能力

- 自动命名
- 自动分组
- 组件识别
- 按钮状态识别
- 九宫格区域识别
- 锚点推断
- 布局约束推断

### 7.4 人工修正

- 修改名称
- 修改类型
- 修改层级
- 修改坐标
- 修改状态
- 修改锚点
- 修改导出路径

## 8. 资产管理

### 8.1 资产类型

- 原始上传图
- AI 生成图
- 切片图
- 透明 PNG
- 图标
- 背景
- 字体
- 图集
- 元数据
- 导出包

### 8.2 资产操作

- 上传
- 下载
- 预览
- 重命名
- 标签
- 搜索
- 删除
- 复制
- 版本对比
- 恢复版本

## 9. 多引擎导出

### 9.1 Unity

- Texture
- Sprite
- Sprite Atlas
- Canvas
- RectTransform
- Image
- Button
- TextMeshPro
- Prefab
- Scene
- UnityPackage/ZIP

### 9.2 Cocos Creator 3.x

- ImageAsset
- SpriteFrame
- Node
- UITransform
- Sprite
- Label
- Button
- Prefab
- Scene JSON
- Extension Import

### 9.3 Cocos Creator 2.x

- cc.SpriteFrame
- cc.Node
- cc.Sprite
- cc.Label
- cc.Button
- Prefab JSON
- Fire/Scene
- Meta 文件

### 9.4 Godot

- Texture2D
- Control
- TextureRect
- Button
- Label
- NinePatchRect
- PackedScene
- TSCN
- EditorPlugin Import

### 9.5 通用导出

- 资产 IR JSON
- 切片 ZIP
- 图层树 JSON
- 坐标表 CSV
- Manifest
- 导入日志

## 10. 引擎插件

### 10.1 Unity 插件

- 插件安装
- 登录/Token
- 项目绑定
- 导出任务列表
- 下载导出包
- 导入资源
- 生成 Prefab
- 生成 Scene
- 冲突处理
- 日志回传

### 10.2 Cocos 插件

- 扩展安装
- 项目绑定
- 下载导出包
- 生成资源目录
- 创建 Prefab/Scene
- 资源刷新

### 10.3 Godot 插件

- EditorPlugin 安装
- 项目绑定
- 下载导出包
- 生成 TSCN
- 导入 Texture
- 创建 Control 节点树

## 11. 文档与商业化

### 11.1 文档

- 快速开始
- 官网介绍
- AI Studio 教程
- 生成参数说明
- UI 切分教程
- Unity 插件教程
- Cocos 插件教程
- Godot 插件教程
- API 文档
- 常见问题

### 11.2 商业化

- 免费额度
- 每日免费积分
- 每月订阅积分
- 永不过期购买积分
- 积分扣除优先级
- 生成点数
- 导出次数
- 并发 AI 任务数
- 云项目数量
- 本地项目数量
- API 调用权限
- 请求速率限制
- 加密热备份快照
- Pro 套餐
- Team 套餐
- 用量统计
- 账单
- 自动续费
- 订阅升级
- 订阅降级限制
- 月付转年付
- 充值

### 11.3 开发者 API

- API Key 管理
- API Key 认证 Header
- Rate Limit Header
- AI Super Matting Execute API
- Webhook 回调
- HMAC-SHA256 签名校验
- Poll Task Status
- Cancel Task
- Cost Estimate
- Error Code
- 结果签名 URL

## 12. 防遗漏验收矩阵

| 域 | 必须有页面 | 必须有 API | 必须有数据模型 | 必须有验收演示 |
| --- | --- | --- | --- | --- |
| 官网 | 是 | 否 | 否 | 是 |
| 登录注册 | 是 | 是 | 是 | 是 |
| 项目空间 | 是 | 是 | 是 | 是 |
| AI Studio | 是 | 是 | 是 | 是 |
| PSD 导入 | 是 | 是 | 是 | 是 |
| PSB 导入 | 是 | 是 | 是 | 是 |
| Figma 导入 | 是 | 是 | 是 | 是 |
| 引擎反向回流 | 是 | 是 | 是 | 是 |
| Unity UI 换风格 | 是 | 是 | 是 | 是 |
| 文生图 | 是 | 是 | 是 | 是 |
| 图生图 | 是 | 是 | 是 | 是 |
| 抠图 | 是 | 是 | 是 | 是 |
| UI 切分 | 是 | 是 | 是 | 是 |
| 资产 IR | 否 | 是 | 是 | 是 |
| Unity 导出 | 是 | 是 | 是 | 是 |
| Unity 插件 | 是 | 是 | 是 | 是 |
| Cocos 导出 | 是 | 是 | 是 | 是 |
| Cocos 插件 | 是 | 是 | 是 | 是 |
| Godot 导出 | 是 | 是 | 是 | 是 |
| Godot 插件 | 是 | 是 | 是 | 是 |
| 文档中心 | 是 | 否 | 否 | 是 |
| 开发者 API | 是 | 是 | 是 | 是 |
| 订阅积分 | 是 | 是 | 是 | 是 |
| 联系支持 | 是 | 是 | 是 | 是 |
