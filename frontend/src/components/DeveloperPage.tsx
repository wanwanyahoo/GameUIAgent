import { useState } from "react";

const apiEndpoints = [
  {
    category: "AI Generation",
    endpoints: [
      { method: "POST", path: "/api/ai/jobs", desc: "Create a new AI generation job" },
      { method: "GET", path: "/api/ai/jobs/{id}", desc: "Get job status and result" },
      { method: "GET", path: "/api/ai/jobs", desc: "List all AI jobs for a project" },
    ],
  },
  {
    category: "Projects & Assets",
    endpoints: [
      { method: "GET", path: "/api/projects", desc: "List all projects" },
      { method: "POST", path: "/api/projects", desc: "Create a new project" },
      { method: "GET", path: "/api/projects/{id}", desc: "Get project details" },
      { method: "GET", path: "/api/projects/{id}/assets", desc: "List project assets" },
      { method: "POST", path: "/api/projects/{id}/assets/upload", desc: "Upload an asset" },
    ],
  },
  {
    category: "Professional Import",
    endpoints: [
      { method: "POST", path: "/api/import/figma", desc: "Import from Figma file" },
      { method: "POST", path: "/api/import/psd", desc: "Import PSD/PSB file" },
    ],
  },
  {
    category: "Engine Export",
    endpoints: [
      { method: "POST", path: "/api/export/{engine}", desc: "Export project for engine" },
      { method: "GET", path: "/api/export/{job_id}", desc: "Get export status" },
    ],
  },
  {
    category: "Billing",
    endpoints: [
      { method: "GET", path: "/api/user/billing", desc: "Get billing and credit info" },
      { method: "POST", path: "/api/user/billing/orders", desc: "Create a pending credit purchase order" },
      { method: "POST", path: "/api/user/billing/orders/{id}/confirm", desc: "Confirm a provider-paid billing order" },
    ],
  },
];

export function DeveloperPage() {
  const [activeCategory, setActiveCategory] = useState("AI Generation");
  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(id);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      /* ignore */
    }
  };

  const active = apiEndpoints.find((e) => e.category === activeCategory);

  return (
    <div className="developer-page">
      <div className="page-header">
        <h1>Developer Documentation</h1>
        <p className="page-subtitle">Build with the GameUIAgent API</p>
      </div>

      <div className="docs-layout">
        <aside className="docs-sidebar">
          <nav className="docs-nav">
            {apiEndpoints.map((section) => (
              <button
                key={section.category}
                type="button"
                className={`docs-nav-item ${activeCategory === section.category ? "active" : ""}`}
                onClick={() => setActiveCategory(section.category)}
              >
                {section.category}
              </button>
            ))}
          </nav>
        </aside>

        <main className="docs-content">
          <section className="docs-section">
            <h2>{activeCategory}</h2>
            <div className="endpoint-list">
              {active?.endpoints.map((ep, i) => (
                <div key={i} className="endpoint-card">
                  <div className="endpoint-header">
                    <span className={`method-badge method-${ep.method.toLowerCase()}`}>{ep.method}</span>
                    <code className="endpoint-path">{ep.path}</code>
                  </div>
                  <p className="endpoint-desc">{ep.desc}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="docs-section">
            <h2>Authentication</h2>
            <p>All API requests require authentication using an API key passed in the <code>X-API-Key</code> header.</p>
            <div className="code-block-wrapper">
              <pre><code>{`curl https://api.gameuiagent.com/api/ai/jobs \\
  -H "X-API-Key: guk_your_api_key_here" \\
  -H "Content-Type: application/json"`}</code></pre>
              <button
                type="button"
                className="copy-btn"
                onClick={() => handleCopy('curl https://api.gameuiagent.com/api/ai/jobs \\\n  -H "X-API-Key: guk_your_api_key_here" \\\n  -H "Content-Type: application/json"', "auth")}
              >
                {copied === "auth" ? "Copied!" : "Copy"}
              </button>
            </div>
          </section>

          <section className="docs-section">
            <h2>Rate Limits</h2>
            <div className="rate-limits-table">
              <table>
                <thead>
                  <tr>
                    <th>Plan</th>
                    <th>Rate Limit</th>
                    <th>Burst</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Free</td>
                    <td>5 requests/min</td>
                    <td>10</td>
                  </tr>
                  <tr>
                    <td>Pro</td>
                    <td>60 requests/min</td>
                    <td>100</td>
                  </tr>
                  <tr>
                    <td>Enterprise</td>
                    <td>500 requests/min</td>
                    <td>1000</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="docs-note">
              Rate limit headers are returned with every response:
              <code>X-RateLimit-Limit</code>, <code>X-RateLimit-Remaining</code>, <code>X-RateLimit-Reset</code>.
            </p>
          </section>

          <section className="docs-section">
            <h2>Webhooks</h2>
            <p>Configure webhooks in your dashboard to receive real-time notifications when jobs complete.</p>
            <ul className="webhook-events">
              <li><code>ai.job.completed</code> — AI generation job completed successfully</li>
              <li><code>ai.job.failed</code> — AI generation job failed</li>
              <li><code>export.completed</code> — Engine export completed</li>
              <li><code>import.completed</code> — Professional import completed</li>
            </ul>
          </section>

          <section className="docs-section">
            <h2>Example: Text to Image</h2>
            <div className="code-block-wrapper">
              <pre><code>{`curl -X POST https://api.gameuiagent.com/api/ai/jobs \\
  -H "X-API-Key: guk_your_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "kind": "text_to_image",
    "prompt": "cyberpunk game UI main menu",
    "size": "1024x1024",
    "style": "cyberpunk",
    "num_images": 1
  }'`}</code></pre>
              <button
                type="button"
                className="copy-btn"
                onClick={() => handleCopy(
                  'curl -X POST https://api.gameuiagent.com/api/ai/jobs \\\n  -H "X-API-Key: guk_your_api_key" \\\n  -H "Content-Type: application/json" \\\n  -d \'{\n    "kind": "text_to_image",\n    "prompt": "cyberpunk game UI main menu",\n    "size": "1024x1024",\n    "style": "cyberpunk",\n    "num_images": 1\n  }\'',
                  "example"
                )}
              >
                {copied === "example" ? "Copied!" : "Copy"}
              </button>
            </div>
          </section>

          <section className="docs-section">
            <h2>SDK Libraries</h2>
            <div className="sdk-grid">
              <div className="sdk-card">
                <div className="sdk-icon">📦</div>
                <h3>Python</h3>
                <code>pip install gameuiagent</code>
              </div>
              <div className="sdk-card">
                <div className="sdk-icon">📦</div>
                <h3>Node.js</h3>
                <code>npm install @gameuiagent/sdk</code>
              </div>
              <div className="sdk-card">
                <div className="sdk-icon">📦</div>
                <h3>Unity</h3>
                <code>UPM package</code>
              </div>
              <div className="sdk-card">
                <div className="sdk-icon">📦</div>
                <h3>REST API</h3>
                <code>OpenAPI 3.0 spec</code>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
