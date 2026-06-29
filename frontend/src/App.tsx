import {
  aiPipelineServices,
  createDemoProject,
  engineExportTargets,
  importSources,
  platformCapabilities,
  productionWorkflow,
  unityPluginFlow
} from "./lib/platform";

const demoProject = createDemoProject("Cyberpunk RPG UI", "unity");

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
          <p className="eyebrow">VberAI-inspired production platform</p>
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
        <div className="studio-layout">
          <div className="panel asset-panel">
            <h3>Assets</h3>
            <span>generated concept</span>
            <span>button atlas</span>
            <span>layout json</span>
          </div>
          <div className="panel studio-canvas">
            <div className="canvas-card">
              <span>Asset IR</span>
              <strong>{demoProject.ir.nodes.length} structured nodes</strong>
            </div>
          </div>
          <div className="panel inspector">
            <h3>Export</h3>
            <p>Unity Prefab + Scene + Sprite Atlas</p>
            <p>Cocos and Godot packages share the same IR.</p>
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
          <h2>One Asset IR now emits native import plans for Unity, Cocos and Godot.</h2>
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
