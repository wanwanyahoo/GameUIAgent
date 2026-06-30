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
const remainingCompletenessGaps = [
  "team roles",
  "password reset",
  "docs center"
] as const;

export function App() {
  return (
    <main className="app-shell">
      <header className="nav">
        <a className="brand" href="#top" aria-label="GameUIAgent home">
          <span className="brand-mark">G</span>
          <span>GameUIAgent</span>
        </a>
        <nav className="nav-links" aria-label="Primary navigation">
          <a href="#studio">AI Studio</a>
          <a href="#workflow">Workflow</a>
          <a href="#engines">Engines</a>
          <a href="#pricing">Pricing</a>
        </nav>
        <a className="nav-cta" href="#studio">
          Launch Studio
        </a>
      </header>

      <section id="top" className="hero">
        <div className="hero-copy">
          <p className="eyebrow">GameUIAgent-inspired production platform</p>
          <h1>AI Game Asset Production from concept to engine import.</h1>
          <p className="hero-subtitle">
            Replicate the official site experience and extend it into a complete AI Studio for
            game UI generation, slicing, Asset IR, Unity-first export and engine plugin loops.
          </p>
          <div className="hero-actions">
            <a className="button primary" href="#studio">
              Open AI Studio
            </a>
            <a className="button secondary" href="#workflow">
              View Production Chain
            </a>
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
            <small>Remaining gaps</small>
          </div>
          <div className="control-row">
            {remainingCompletenessGaps.map((gap) => (
              <b key={gap}>{gap}</b>
            ))}
          </div>
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
