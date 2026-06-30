import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth-context";
import { createProjectApi, listProjectsApi, type Project } from "../lib/projects-api";

const engineLabels: Record<string, string> = {
  unity: "Unity",
  cocos3: "Cocos Creator 3.x",
  cocos2: "Cocos Creator 2.x",
  godot: "Godot",
  unreal: "Unreal Engine 5",
};

const canvasPresets = [
  { label: "1920 x 1080 (Full HD)", width: 1920, height: 1080 },
  { label: "1280 x 720 (HD)", width: 1280, height: 720 },
  { label: "2560 x 1440 (2K)", width: 2560, height: 1440 },
  { label: "1080 x 1920 (Portrait)", width: 1080, height: 1920 },
  { label: "1024 x 768 (iPad)", width: 1024, height: 768 },
];

export function Dashboard() {
  const { user, logout, token } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newName, setNewName] = useState("");
  const [newEngine, setNewEngine] = useState("unity");
  const [newCanvas, setNewCanvas] = useState(canvasPresets[0].label);
  const [creating, setCreating] = useState(false);

  const loadProjects = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const data = await listProjectsApi(token);
      setProjects(data);
    } catch (err: any) {
      setError(err.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [token]);

  const handleCreateProject = async () => {
    if (!token || !newName.trim()) return;
    const preset = canvasPresets.find((p) => p.label === newCanvas) || canvasPresets[0];
    try {
      setCreating(true);
      setError(null);
      const project = await createProjectApi(token, {
        name: newName.trim(),
        target_engine: newEngine,
        canvas: { width: preset.width, height: preset.height },
      });
      setProjects([project, ...projects]);
      setShowNewProject(false);
      setNewName("");
      setNewEngine("unity");
      setNewCanvas(canvasPresets[0].label);
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <span className="brand-mark">G</span>
          <span>GameUIAgent</span>
        </div>
        <div className="dashboard-nav">
          <a href="#projects" className="nav-active">Projects</a>
          <a href="#billing">Billing</a>
          <a href="#api-keys">API Keys</a>
          <a href="#docs">Docs</a>
        </div>
        <div className="dashboard-user">
          <span className="user-email">{user?.email || "user"}</span>
          <button type="button" className="user-menu" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <section className="dashboard-hero">
          <div>
            <h1>Welcome back{user?.name ? `, ${user.name}` : ""}</h1>
            <p>Create stunning game UI assets with AI. Generate, slice, and export to your engine.</p>
          </div>
          <button
            type="button"
            className="btn-primary"
            onClick={() => setShowNewProject(true)}
          >
            + New Project
          </button>
        </section>

        <section className="dashboard-stats">
          <div className="stat-card">
            <span className="stat-label">Total Projects</span>
            <strong className="stat-value">{projects.length}</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Credits Remaining</span>
            <strong className="stat-value">1,250</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Assets Generated</span>
            <strong className="stat-value">250</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Active Engines</span>
            <strong className="stat-value">{new Set(projects.map((p) => p.target_engine)).size}</strong>
          </div>
        </section>

        {error && <div className="error-banner">{error}</div>}

        <section className="projects-section">
          <div className="section-header">
            <h2>Your Projects</h2>
            <div className="section-actions">
              <input type="search" placeholder="Search projects..." className="search-input" />
              <select className="filter-select">
                <option>All engines</option>
                <option>Unity</option>
                <option>Cocos Creator</option>
                <option>Godot</option>
                <option>Unreal Engine</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="loading">Loading projects...</div>
          ) : (
            <div className="projects-grid">
              {projects.map((project) => (
                <a
                  key={project.id}
                  href={`#studio/${project.id}`}
                  className="project-card"
                >
                  <div className="project-thumb">
                    <span className="thumb-placeholder">{project.name.charAt(0)}</span>
                  </div>
                  <div className="project-info">
                    <h3>{project.name}</h3>
                    <div className="project-meta">
                      <span className="engine-badge">{engineLabels[project.target_engine] || project.target_engine}</span>
                      <span className="asset-count">{project.canvas.width}x{project.canvas.height}</span>
                    </div>
                    <span className="project-updated">
                      {project.status === "active" ? "Active" : project.status}
                    </span>
                  </div>
                </a>
              ))}

              <button
                type="button"
                className="project-card new-project-card"
                onClick={() => setShowNewProject(true)}
              >
                <div className="new-project-icon">+</div>
                <span>Create New Project</span>
              </button>
            </div>
          )}
        </section>
      </main>

      {showNewProject && (
        <div className="modal-overlay" onClick={() => !creating && setShowNewProject(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Project</h2>
            <p className="modal-subtitle">Start building your game UI with AI-powered asset generation.</p>
            <div className="modal-form">
              <label>
                <span>Project Name</span>
                <input
                  type="text"
                  placeholder="My Awesome Game UI"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreateProject()}
                  autoFocus
                  disabled={creating}
                />
              </label>
              <label>
                <span>Target Engine</span>
                <select value={newEngine} onChange={(e) => setNewEngine(e.target.value)} disabled={creating}>
                  <option value="unity">Unity</option>
                  <option value="cocos3">Cocos Creator 3.x</option>
                  <option value="cocos2">Cocos Creator 2.x</option>
                  <option value="godot">Godot</option>
                  <option value="unreal">Unreal Engine 5</option>
                </select>
              </label>
              <label>
                <span>Canvas Size</span>
                <select value={newCanvas} onChange={(e) => setNewCanvas(e.target.value)} disabled={creating}>
                  {canvasPresets.map((p) => (
                    <option key={p.label} value={p.label}>{p.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setShowNewProject(false)} disabled={creating}>
                Cancel
              </button>
              <button type="button" className="btn-primary" onClick={handleCreateProject} disabled={creating || !newName.trim()}>
                {creating ? "Creating..." : "Create Project"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
