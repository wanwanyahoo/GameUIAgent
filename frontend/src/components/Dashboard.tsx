import { useState } from "react";
import { useAuth } from "../lib/auth-context";

type Project = {
  id: string;
  name: string;
  targetEngine: string;
  updatedAt: string;
  assetCount: number;
};

const mockProjects: Project[] = [
  {
    id: "prj_cyberpunk",
    name: "Cyberpunk RPG UI",
    targetEngine: "unity",
    updatedAt: "2024-03-15T10:30:00Z",
    assetCount: 24,
  },
  {
    id: "prj_match3",
    name: "Match-3 Mobile Game",
    targetEngine: "cocos3",
    updatedAt: "2024-03-14T15:20:00Z",
    assetCount: 56,
  },
  {
    id: "prj_fantasy",
    name: "Fantasy MMORPG HUD",
    targetEngine: "unreal",
    updatedAt: "2024-03-12T09:00:00Z",
    assetCount: 128,
  },
  {
    id: "prj_2dplatformer",
    name: "2D Platformer UI Kit",
    targetEngine: "godot",
    updatedAt: "2024-03-10T18:45:00Z",
    assetCount: 42,
  },
];

export function Dashboard() {
  const { user, logout } = useAuth();
  const [showNewProject, setShowNewProject] = useState(false);

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
            <strong className="stat-value">{mockProjects.length}</strong>
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
            <strong className="stat-value">4</strong>
          </div>
        </section>

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

          <div className="projects-grid">
            {mockProjects.map((project) => (
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
                    <span className="engine-badge">{project.targetEngine}</span>
                    <span className="asset-count">{project.assetCount} assets</span>
                  </div>
                  <span className="project-updated">
                    Updated {new Date(project.updatedAt).toLocaleDateString()}
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
        </section>
      </main>

      {showNewProject && (
        <div className="modal-overlay" onClick={() => setShowNewProject(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Project</h2>
            <p>Start building your game UI with AI-powered asset generation.</p>
            <div className="modal-form">
              <label>
                <span>Project Name</span>
                <input type="text" placeholder="My Awesome Game UI" />
              </label>
              <label>
                <span>Target Engine</span>
                <select>
                  <option value="unity">Unity</option>
                  <option value="cocos3">Cocos Creator 3.x</option>
                  <option value="godot">Godot</option>
                  <option value="unreal">Unreal Engine 5</option>
                </select>
              </label>
              <label>
                <span>Canvas Size</span>
                <select>
                  <option>1920 x 1080 (Full HD)</option>
                  <option>1280 x 720 (HD)</option>
                  <option>2560 x 1440 (2K)</option>
                  <option>1080 x 1920 (Portrait)</option>
                </select>
              </label>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setShowNewProject(false)}>
                Cancel
              </button>
              <button type="button" className="btn-primary" onClick={() => setShowNewProject(false)}>
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
