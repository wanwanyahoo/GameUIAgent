import {
  aiPipelineServices,
  billingPlans,
  createDemoProject,
  creditBuckets,
  engineExportTargets,
  importSources,
  platformCapabilities,
  pluginConnectionSteps,
  productionWorkflow,
  studioActionDock,
  studioActiveSelection,
  studioAssets,
  studioExportWizardSteps,
  studioInspectorControls,
  studioLayerTree,
  studioSegmentationCorrections,
  studioTimeline,
  unityPluginFlow
} from "./lib/platform";

const demoProject = createDemoProject("Cyberpunk RPG UI", "unity");
const pluginImportTelemetry = [
  ["textures_created", 4],
  ["umg_widgets_created", 1],
  ["slate_slots_bound", 7],
  ["warnings", 1]
] as const;
const coreChainSelfTest = [
  "PSD layered import",
  "Unity package export",
  "Unity plugin import",
  "Studio timeline synced"
] as const;
const accountPlatformCapabilities = [
  "Team Roles",
  "Password Reset",
  "Docs Center"
] as const;
const teamRoleMatrix = [
  "Owner",
  "Admin",
  "Designer",
  "Developer",
  "Viewer"
] as const;
const passwordResetFlow = [
  "Request email",
  "Reset token",
  "Rotate password hash",
  "Login with new password"
] as const;
const docsCenterGuides = [
  "Getting Started",
  "Developer API",
  "Engine Plugins"
] as const;
const uploadToSliceChain = [
  {
    title: "Uploaded Asset API",
    endpoint: "/api/projects/{project_id}/assets",
    detail: "Register uploaded PNG, PSD, PSB, Figma link, mask and reference images with size metadata."
  },
  {
    title: "Image-to-Image input asset",
    endpoint: "/api/projects/{project_id}/ai/jobs",
    detail: "AI jobs now bind input_asset_id, model, seed, negative prompt and candidate outputs."
  },
  {
    title: "Editable slices",
    endpoint: "/api/projects/{project_id}/segmentations",
    detail: "Uploaded UI images produce slices, confidence, editable_bounds and Asset IR nodes."
  },
  {
    title: "Professional source parser",
    endpoint: "/api/projects/{project_id}/imports/professional-sources",
    detail: "PSD, PSB and Figma sources can submit parser jobs before layer-to-IR conversion."
  }
] as const;
const assetLibraryOperations = [
  {
    title: "Search and tags",
    endpoint: "/api/projects/{project_id}/assets?search=&tag=",
    detail: "Filter production assets by filename and team-approved tags before generation, slicing or export."
  },
  {
    title: "Rename and version",
    endpoint: "/api/projects/{project_id}/assets/{asset_id}/versions",
    detail: "Rename assets, update tags and keep created/updated snapshots for review and rollback planning."
  },
  {
    title: "Copy and delete",
    endpoint: "/api/projects/{project_id}/assets/{asset_id}",
    detail: "Duplicate approved assets for variants, or remove obsolete uploads from the active project library."
  }
] as const;
const productionRuntimeChecks = [
  {
    title: "SQLite durable store",
    endpoint: "/api/system/production-readiness",
    detail: "Users, projects and assets persist to a SQLite runtime database and reload after process restart."
  },
  {
    title: "No in-memory-only data loss",
    endpoint: "GAMEUIAGENT_STORE_DB",
    detail: "Production deployments set a database path instead of relying on ephemeral process memory."
  },
  {
    title: "Local object storage",
    endpoint: "GAMEUIAGENT_OBJECT_STORE_DIR",
    detail: "Binary upload and download endpoints persist original files with size, content type and SHA-256 metadata."
  },
  {
    title: "AI worker queue",
    endpoint: "GAMEUIAGENT_WORKER_TOKEN / X-Worker-Token",
    detail: "Queued AI jobs call /api/system/ai-worker/run-next with worker auth and move through queued -> running -> succeeded."
  },
  {
    title: "Qwen inference provider",
    endpoint: "GAMEUIAGENT_INFERENCE_PROVIDER=qwen / QWEN_API_KEY",
    detail: "Worker inference calls persist request and response metadata into inference_runs before attaching result assets."
  },
  {
    title: "Readiness checks",
    endpoint: "durable_store / object_storage / inference_provider",
    detail: "Runtime checks expose storage durability, object storage, queued AI processing, inference provider and ownership safeguards."
  }
] as const;
const vberProductCards = [
  {
    title: "Art to engine AI Studio",
    body: "从 PSD、Figma 类设计稿或游戏项目加载场景与预制体，在 AI 画布中创作、编辑、优化并导回引擎。",
    label: "Flagship"
  },
  {
    title: "Engine automation Engine MCP",
    body: "让 AI 进入 Unity、Cocos Creator 2.x / 3.x、Godot、Unreal，执行编码、场景、预制体、资源和调试任务。",
    label: "Backbone"
  },
  {
    title: "Quick services AI 超强抠图",
    body: "高精度 AI 超强抠图工具，让美术资源准备更快、更轻松。",
    label: "Utility"
  }
] as const;
const vberTokenSteps = [
  {
    index: "01",
    eyebrow: "导入来源",
    title: "导入设计与项目资产",
    detail: "从 PSD、Figma 类设计稿、场景、预制体、UI、图片和游戏项目中导入生产素材。",
    tags: ["PSD 分层稿", "Figma 类设计", "项目资产"]
  },
  {
    index: "02",
    eyebrow: "AI Studio",
    title: "AI Studio 创作与优化",
    detail: "在 AI Studio 中完成游戏资产生成、编辑、精修、结构整理和可交付检查。",
    tags: ["AI 创建游戏资产", "AI 编辑游戏资产", "AI 优化游戏 UI"]
  },
  {
    index: "03",
    eyebrow: "引擎交付",
    title: "导出引擎可用资产",
    detail: "输出 Unity、Cocos、Godot、Unreal 可导入的 Prefab、Scene、Sprite、UMG 和 Control 资源。",
    tags: ["Unity Prefab", "Cocos Scene", "Godot Control", "Unreal UMG"]
  },
  {
    index: "04",
    eyebrow: "自动化落地",
    title: "AI 自动化开发落地",
    detail: "通过 Engine MCP 与插件把资源导入、布局替换、Prefab 生成和导入日志连接为闭环。",
    tags: ["Engine MCP", "插件导入", "任务回写"]
  }
] as const;
const vberStackSteps = [
  "01 导入设计与项目资产",
  "02 AI Studio 创作与优化",
  "03 导出引擎可用资产",
  "04 AI 自动化开发落地"
] as const;
const vberEngineCards = [
  ["Unity MCP", "unity-mcp", "订阅制"],
  ["Godot MCP", "godot-mcp", "开源免费"],
  ["Cocos MCP 3.x", "cocos-mcp-3", "Creator 3.x"],
  ["Cocos MCP 2.x", "cocos-mcp-2", "Creator 2.x"],
  ["Unreal MCP", "unreal-mcp", "UMG 扩展"]
] as const;

export function App() {
  return (
    <main className="app-shell">
      <header className="nav vber-nav">
        <button className="menu-button" type="button" aria-label="open navigation menu">
          <span />
          <span />
        </button>
        <a className="brand" href="#top" aria-label="GameUIAgent home">
          <span className="brand-mark">G</span>
          <span>GameUIAgent</span>
        </a>
        <nav className="nav-links" aria-label="Primary navigation">
          <a href="#top">首页</a>
          <a href="#engine-mcp">游戏引擎 MCP 插件</a>
          <a href="#vber-studio">AI Studio</a>
          <a href="#matting">AI 超强抠图</a>
          <a href="#platform-extension">开发者</a>
        </nav>
        <button className="nav-link-button" type="button">探索产品</button>
        <button className="nav-link-button" type="button">Switch language</button>
        <button className="nav-link-button" type="button">Switch to light mode</button>
        <div className="auth-actions">
          <button type="button">登录</button>
          <button type="button">注册</button>
        </div>
      </header>

      <section id="top" className="vber-hero">
        <div className="vber-hero-copy">
          <p className="eyebrow">GAMEUIAGENT / AI GAME DEVELOPMENT SUITE</p>
          <p className="vber-titleline">GameUIAgent · AI 原生游戏生产力平台</p>
          <h1>一站式 AI 游戏开发<br />解决方案</h1>
          <p>
            GameUIAgent 覆盖从游戏 AI 美术设计到游戏引擎自动化 AI 编程的完整链路：
            导入 PSD、Figma 类设计稿或游戏项目资产，在 AI Studio 中创作、编辑和优化，
            再导出为引擎可直接使用的场景、预制体和美术资源，并通过 Engine MCP 完成落地。
          </p>
          <div className="hero-actions">
            <a className="button primary" href="#vber-studio">访问 AI Studio</a>
            <a className="button secondary" href="#pricing">查看平台定价</a>
          </div>
        </div>
        <div className="vber-product-grid" aria-label="核心产品入口">
          {vberProductCards.map((product) => (
            <a className="vber-product-card" href="#platform-extension" key={product.title}>
              <span>{product.title}</span>
              <p>{product.body}</p>
              <b>{product.label}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="vber-token-section">
        <div className="vber-token-grid">
          {vberTokenSteps.map((step) => (
            <article className="vber-token-card" key={step.index}>
              <span>{step.index}</span>
              <small>{step.eyebrow}</small>
              <h3>{step.title}</h3>
              <p>{step.detail}</p>
              <div className="vber-tags">
                {step.tags.map((tag) => <b key={tag}>{tag}</b>)}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="vber-token-section vber-matting-section" id="matting">
        <div className="vber-section-copy">
          <p className="eyebrow">最佳 AI 工具</p>
          <h2>AI 超强抠图，<br />现由 GameUIAgent 独家提供</h2>
          <p>
            处理常见抠图工具难以抠除的人物发丝、光效、半透材质和复杂边缘，
            让游戏角色、宣传图和 UI 素材更快进入生产流程。
          </p>
          <div className="vber-tags">
            <b>发丝级边缘</b>
            <b>光效保留</b>
            <b>半透材质</b>
          </div>
          <a className="button primary" href="#platform-extension">体验 AI 超强抠图</a>
        </div>
        <div className="matting-demo" aria-label="AI matting before and after demo">
          <div>复杂原图</div>
          <div>透明结果</div>
        </div>
      </section>

      <section className="vber-token-section">
        <div className="vber-section-copy">
          <p className="eyebrow">GAMEUIAGENT PRODUCTION STACK</p>
          <h2>重塑游戏开发的 AI 工作流</h2>
          <p>
            设计软件、AI Studio、Engine MCP 和 AI 超强抠图不再是孤立工具。
            GameUIAgent 把游戏资产设计、AI 创作、引擎资产交付、代码编写和引擎操作连接成一条可持续迭代的生产流程。
          </p>
        </div>
        <div className="stack-rail">
          {vberStackSteps.map((step) => <span key={step}>{step}</span>)}
        </div>
      </section>

      <section className="vber-token-section vber-studio-section" id="vber-studio">
        <div className="vber-section-copy">
          <p className="eyebrow">AI Studio 平台</p>
          <h2>游戏原生设计平台<br />连接画布与引擎</h2>
          <p>
            从 PSD、Figma 类设计稿或游戏项目中导入素材，还原为可协作的 AI 画布；
            生成、拆分、编辑和组件化游戏资产，并实时同步回 Unity、Cocos Creator、Godot 或 Unreal。
          </p>
          <div className="vber-tags">
            <b>PSD / Figma / 项目资源导入</b>
            <b>团队协作 AI 画布</b>
            <b>素材实时同步到项目</b>
            <b>AI 生成 UI、原画、动画</b>
          </div>
        </div>
        <aside className="hero-console" aria-label="Production console preview">
          <div className="console-topline">
            <span>Unity-first</span>
            <strong>Pipeline Ready</strong>
          </div>
          <div className="canvas-preview">
            <div className="preview-panel">
              <span className="preview-chip">PSD / PSB / Figma</span>
              <span className="preview-title">Cyberpunk RPG UI</span>
              <span className="preview-button">Generated CTA</span>
            </div>
          </div>
          <div className="task-grid">
            {demoProject.tasks.map((task) => (
              <span key={task.kind} className={`task-pill ${task.status}`}>
                {task.kind.replaceAll("_", " ")}
              </span>
            ))}
          </div>
        </aside>
      </section>

      <section className="vber-token-section" id="engine-mcp" aria-label="让 AI 真正进入 游戏引擎">
        <div className="vber-section-copy">
          <p className="eyebrow">核心产品</p>
          <h2>让 AI 真正进入<br />游戏引擎</h2>
          <p>
            让 AI 直接控制 Unity、Cocos Creator 2.x、Cocos Creator 3.x、Godot、Unreal，
            完成编码、场景编辑、预制体处理、资源管理和调试任务。
          </p>
        </div>
        <div className="engine-product-grid">
          {vberEngineCards.map(([title, slug, note]) => (
            <article className="engine-product-card" key={title}>
              <h3>{title}</h3>
              <code>{slug}</code>
              <span>{note}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="vber-token-section vber-action-section" aria-label="让下一次迭代 直接进入引擎">
        <p className="eyebrow">START</p>
        <h2>让下一次迭代<br />直接进入引擎</h2>
        <p>从导入资产开始，把 AI 生成、协作编辑和引擎同步放进一条可控流程。</p>
        <div className="hero-actions">
          <a className="button primary" href="#studio">免费注册</a>
          <a className="button secondary" href="#matting">进入 AI 超强抠图</a>
          <a className="button secondary" href="#platform-extension">GitHub</a>
        </div>
      </section>

      <div id="platform-extension" className="platform-extension-label">
        <span>GameUIAgent extended production platform</span>
      </div>

      <section className="section" id="studio">
        <div className="section-heading">
          <p className="eyebrow">AI Studio</p>
          <h2>One canvas for generation, import, slicing and export.</h2>
        </div>
        <div className="studio-workspace">
          <div className="panel asset-panel">
            <h3>Asset Library</h3>
            {studioAssets.map((asset) => (
              <span key={asset.id}>
                {asset.title} <b>{asset.kind}</b>
              </span>
            ))}
          </div>
          <div className="panel timeline-panel">
            <h3>Task Timeline</h3>
            {studioTimeline.map((task) => (
              <div className="timeline-row" key={task.id}>
                <span>{task.title}</span>
                <b>{task.status}</b>
                <i style={{ inlineSize: `${Math.max(task.progress, 8)}%` }} />
              </div>
            ))}
          </div>
          <div className="panel studio-canvas">
            <div className="canvas-card">
              <span>Asset IR</span>
              <strong>{demoProject.ir.nodes.length} structured nodes</strong>
              <em>Slice Editor</em>
            </div>
          </div>
          <div className="panel layer-tree">
            <h3>Layer Tree</h3>
            {studioLayerTree.map((node) => (
              <div className="layer-root" key={node.id}>
                <span>{node.name}</span>
                {node.children?.map((child) => (
                  <small key={child.id}>{child.name} / {child.type}</small>
                ))}
              </div>
            ))}
          </div>
          <div className="panel inspector-panel">
            <h3>Inspector</h3>
            {studioInspectorControls.map((control) => (
              <p key={control.id}>
                <b>{control.title}</b>
                <span>{control.value}</span>
              </p>
            ))}
          </div>
        </div>
        <div className="studio-ops">
          <div className="panel action-dock">
            <h3>Action Dock</h3>
            <small>Synced via Studio API</small>
            <p>Selected layer: {studioActiveSelection.selectedLayerId}</p>
            <div className="control-row">
              {studioActionDock.map((action) => (
                <b key={action.id}>{action.title} / {action.shortcut}</b>
              ))}
            </div>
          </div>
          <div className="panel correction-queue">
            <h3>Segmentation Corrections</h3>
            {studioSegmentationCorrections.map((correction) => (
              <article key={correction.id}>
                <span>{correction.targetLayerId}</span>
                <strong>{correction.title}</strong>
                <p>{correction.change}</p>
                <small>{Math.round(correction.confidence * 100)}% confidence</small>
              </article>
            ))}
          </div>
          <div className="panel export-wizard">
            <h3>Export Wizard</h3>
            {studioExportWizardSteps.map((step, index) => (
              <div className="wizard-step" key={step.id}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{step.title}</strong>
                <b>{step.status}</b>
              </div>
            ))}
          </div>
          <div className="panel import-telemetry">
            <h3>Plugin Import Telemetry</h3>
            <small>Unreal 5.3+ import summary</small>
            <strong>Plugin import succeeded</strong>
            <em>Warnings: 1</em>
            {pluginImportTelemetry.map(([label, value]) => (
              <p key={label}>
                <b>{label}</b>
                <span>{value}</span>
              </p>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="workflow">
        <div className="section-heading">
          <p className="eyebrow">End-to-end workflow</p>
          <h2>From professional design layers to engine-ready packages.</h2>
        </div>
        <div className="workflow">
          {productionWorkflow.map((step, index) => (
            <article className="workflow-step" key={step.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{step.title}</h3>
              <p>{step.detail}</p>
            </article>
          ))}
        </div>
        <div className="core-chain panel">
          <div>
            <p className="eyebrow">Core Chain Self-Test</p>
            <h3>PSD to Unity plugin import path verified by API flow.</h3>
          </div>
          <div className="control-row">
            {coreChainSelfTest.map((step) => (
              <b key={step}>{step}</b>
            ))}
          </div>
        </div>
        <div className="completeness panel">
          <div>
            <p className="eyebrow">Completeness Status</p>
            <h3>Core engine chain: verified</h3>
            <small>Account and docs: covered</small>
          </div>
          <div className="control-row">
            {accountPlatformCapabilities.map((capability) => (
              <b key={capability}>{capability}</b>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="docs">
        <div className="section-heading">
          <p className="eyebrow">Account Platform</p>
          <h2>Team roles, password recovery and docs center are covered.</h2>
        </div>
        <div className="account-grid">
          <article className="account-card">
            <span>RBAC</span>
            <h3>Team Roles</h3>
            <p>Invite game UI collaborators and assign scoped production permissions.</p>
            <div className="control-row">
              {teamRoleMatrix.map((role) => (
                <b key={role}>{role}</b>
              ))}
            </div>
          </article>
          <article className="account-card">
            <span>Auth</span>
            <h3>Password Reset</h3>
            <p>Issue reset tokens, rotate salted password hashes and invalidate used tokens.</p>
            <div className="control-row">
              {passwordResetFlow.map((step) => (
                <b key={step}>{step}</b>
              ))}
            </div>
          </article>
          <article className="account-card">
            <span>Docs</span>
            <h3>Docs Center</h3>
            <p>Product onboarding, Developer API and Engine Plugins guides are exposed together.</p>
            <div className="control-row">
              {docsCenterGuides.map((guide) => (
                <b key={guide}>{guide}</b>
              ))}
            </div>
          </article>
        </div>
      </section>

      <section className="section" id="upload-chain">
        <div className="section-heading">
          <p className="eyebrow">Upload-to-Slice Chain</p>
          <h2>Real project assets now enter generation, slicing and professional import flows.</h2>
        </div>
        <div className="upload-chain">
          {uploadToSliceChain.map((step, index) => (
            <article className="upload-step" key={step.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{step.title}</h3>
              <code>{step.endpoint}</code>
              <p>{step.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="asset-ops">
        <div className="section-heading">
          <p className="eyebrow">Asset Library Operations</p>
          <h2>Uploaded assets can now be searched, renamed, versioned, copied and deleted.</h2>
        </div>
        <div className="asset-ops">
          {assetLibraryOperations.map((operation, index) => (
            <article className="asset-op-card" key={operation.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{operation.title}</h3>
              <code>{operation.endpoint}</code>
              <p>{operation.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="production-runtime">
        <div className="section-heading">
          <p className="eyebrow">Production Runtime</p>
          <h2>Core platform state now has a durable runtime store instead of in-memory-only data.</h2>
        </div>
        <div className="runtime-grid">
          {productionRuntimeChecks.map((check, index) => (
            <article className="runtime-card" key={check.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{check.title}</h3>
              <code>{check.endpoint}</code>
              <p>{check.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section split-section" id="imports">
        <div className="section-heading">
          <p className="eyebrow">Professional imports</p>
          <h2>PSD, PSB, Figma and engine snapshots become structured Asset IR.</h2>
        </div>
        <div className="import-grid">
          {importSources.map((source) => (
            <article className="import-card" key={source.id}>
              <span>{source.id}</span>
              <h3>{source.title}</h3>
              <p>{source.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section split-section" id="api-pipeline">
        <div className="section-heading">
          <p className="eyebrow">Developer API pipeline</p>
          <h2>AI services expose cost estimates, queued execution, polling, Cancel and Webhook hooks.</h2>
        </div>
        <div className="pipeline-grid">
          {aiPipelineServices.map((service) => (
            <article className="pipeline-card" key={service.id}>
              <div>
                <span>{service.apiEnabled ? "API enabled" : "Studio flow"}</span>
                <h3>{service.title}</h3>
              </div>
              <div className="control-row">
                {service.controls.map((control) => (
                  <b key={control}>{control}</b>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="unity-plugin">
        <div className="section-heading">
          <p className="eyebrow">Unity plugin protocol</p>
          <h2>Manifest, package download, import logs and restyle replacement stay connected.</h2>
        </div>
        <div className="unity-flow">
          {unityPluginFlow.map((step, index) => (
            <article className="unity-step" key={step.id}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{step.title}</h3>
              <code>{step.apiPath}</code>
              <p>{step.detail}</p>
              <div className="control-row">
                {step.outputs.map((output) => (
                  <b key={output}>{output}</b>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="engine-matrix">
        <div className="section-heading">
          <p className="eyebrow">Multi-engine export matrix</p>
          <h2>One Asset IR now emits native import plans for Unity, Cocos, Godot and Unreal.</h2>
        </div>
        <div className="engine-matrix">
          {engineExportTargets.map((target) => (
            <article className="engine-card" key={target.id}>
              <span>{target.id}</span>
              <h3>{target.title}</h3>
              <p>{target.entry}</p>
              <small>Engine version: {target.engineVersion}</small>
              <div className="control-row">
                {target.importSteps.map((step) => (
                  <b key={step}>{step}</b>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="plugin-connection">
        <div className="section-heading">
          <p className="eyebrow">Engine plugin connection</p>
          <h2>Editor plugins authenticate, sync projects, query exports and download packages.</h2>
        </div>
        <div className="connection-lane">
          {pluginConnectionSteps.map((step, index) => (
            <article className="connection-step" key={step.id}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{step.title}</h3>
              <code>{step.apiPath}</code>
              <p>{step.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="billing">
        <div className="section-heading">
          <p className="eyebrow">Credits and billing</p>
          <h2>Plans, credit buckets, rate limits and API usage stay visible.</h2>
        </div>
        <div className="billing-layout">
          <div className="credit-ledger">
            {creditBuckets.map((bucket) => (
              <article className="credit-bucket" key={bucket.id}>
                <span>Priority {bucket.priority}</span>
                <h3>{bucket.title}</h3>
                <p>{bucket.detail}</p>
              </article>
            ))}
          </div>
          <div className="plan-table">
            {billingPlans.map((plan) => (
              <article className="plan-card" key={plan.id}>
                <span>{plan.apiEnabled ? "API enabled" : "Studio plan"}</span>
                <h3>{plan.title}</h3>
                <p>{plan.dailyCredits} daily / {plan.monthlyCredits} monthly credits</p>
                <small>{plan.concurrentAiTasks} concurrent AI tasks</small>
                <code>X-RateLimit-Limit: {plan.rateLimitPerMinute}</code>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="engines">
        <div className="section-heading">
          <p className="eyebrow">Complete capability map</p>
          <h2>Website, AI tools, engine automation and platform APIs.</h2>
        </div>
        <div className="capability-grid">
          {platformCapabilities.map((capability) => (
            <article className="capability-card" key={capability.id}>
              <span>{capability.group}</span>
              <h3>{capability.title}</h3>
              <p>{capability.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section pricing" id="pricing">
        <div>
          <p className="eyebrow">Credits, API and plugins</p>
          <h2>Built for demos now, structured for commercial plans later.</h2>
        </div>
        <a className="button primary" href="#top">
          Start Full Replication
        </a>
      </section>
    </main>
  );
}

export default App;
