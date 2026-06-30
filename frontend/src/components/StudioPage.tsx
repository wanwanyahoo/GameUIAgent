import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { getStudioStateApi, getProjectApi, type StudioState, type Project } from "../lib/projects-api";
import { navigateTo } from "../lib/hash-router";

type StudioPageProps = {
  projectId: string;
};

type TimelineTask = {
  id: string;
  title: string;
  status: string;
  progress?: number;
  type: string;
};

export function StudioPage({ projectId }: StudioPageProps) {
  const { token, user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [studio, setStudio] = useState<StudioState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setError("Missing project id");
      setLoading(false);
      return;
    }
    if (!token) return;

    const authToken = token;
    let cancelled = false;

    async function load(showLoading: boolean) {
      try {
        if (showLoading) setLoading(true);
        setError(null);
        const [proj, state] = await Promise.all([
          getProjectApi(authToken, projectId),
          getStudioStateApi(authToken, projectId),
        ]);
        if (cancelled) return;
        setProject(proj);
        setStudio(state);
      } catch (err: any) {
        if (cancelled) return;
        setError(err.message || "Failed to load studio");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    setIsPolling(true);
    load(true);
    const interval = window.setInterval(() => load(false), 2000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
      setIsPolling(false);
    };
  }, [token, projectId]);

  if (!token || !user) {
    return null;
  }

  if (loading) {
    return (
      <div className="studio-loading">
        <div className="loading-spinner"></div>
        <p>Loading Studio...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="studio-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => navigateTo("/dashboard")}>Back to Dashboard</button>
      </div>
    );
  }

  if (!project || !studio) {
    return null;
  }

  const tasks: TimelineTask[] = studio.timeline.map((item, index) => ({
    id: String(item.id ?? `task-${index}`),
    title: String(item.title ?? item.kind ?? item.id ?? "Studio task"),
    status: String(item.status ?? "ready"),
    progress: typeof item.progress === "number" ? item.progress : undefined,
    type: String(item.type ?? item.kind ?? "studio"),
  }));
  const activeTasks = tasks.filter((task) => task.status === "queued" || task.status === "processing" || task.status === "running");
  const completedTasks = tasks.filter((task) => task.status === "completed" || task.status === "succeeded" || task.status === "failed" || task.status === "ready");
  const liveStatus = isPolling ? "live" : "idle";

  return (
    <div className="studio-layout">
      <header className="studio-topbar">
        <div className="studio-topbar-left">
          <button
            className="studio-back-btn"
            onClick={() => navigateTo("/dashboard")}
            type="button"
          >
            ← Back
          </button>
          <div className="studio-brand">
            <span className="brand-mark">G</span>
            <span>GameUIAgent</span>
          </div>
          <span className="studio-project-name">{project.name}</span>
          <span className="studio-engine-badge">{project.target_engine}</span>
        </div>
        <div className="studio-topbar-right">
          <div className={`studio-live-indicator ${isPolling ? "live" : "idle"}`}>
            <span className="live-dot"></span>
            <span className="live-label">{liveStatus}</span>
          </div>
          <span className="studio-user">{user.name || user.email}</span>
        </div>
      </header>

      <div className="studio-main">
        <aside className="studio-sidebar left-sidebar">
          <h3>Timeline</h3>
          <div className="studio-timeline">
            {tasks.map((item) => (
              <div key={item.id} className={`timeline-item ${item.status}`}>
                <div className="timeline-dot"></div>
                <div className="timeline-content">
                  <p className="timeline-title">{item.title}</p>
                  <p className="timeline-status">{item.status}</p>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <main className="studio-canvas-area">
          <div className="studio-canvas-placeholder">
            <h2>AI Canvas</h2>
            <p>
              {project.name} — {project.canvas.width}×{project.canvas.height}
            </p>
            <div className="canvas-actions">
              {studio.action_dock.map((action) => (
                <button key={action.id} className="action-btn" type="button">
                  {action.title}
                  <span className="shortcut">{action.shortcut}</span>
                </button>
              ))}
            </div>
            {activeTasks.length > 0 && (
              <div className="active-tasks">
                <h4>Active AI Tasks ({activeTasks.length})</h4>
                {activeTasks.map((task) => (
                  <div key={task.id} className={`task-card ${task.status}`}>
                    <p className="task-title">{task.type}</p>
                    <p className="task-status">{task.status}</p>
                    {task.progress !== undefined && task.progress !== null && (
                      <div className="task-progress-bar">
                        <div
                          className="task-progress-fill"
                          style={{ width: `${task.progress}%` }}
                        ></div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            {completedTasks.length > 0 && activeTasks.length === 0 && (
              <div className="completed-tasks">
                <h4>Recent Tasks</h4>
                {completedTasks.slice(0, 3).map((task) => (
                  <div key={task.id} className={`task-card ${task.status}`}>
                    <p className="task-title">{task.type}</p>
                    <p className="task-status">{task.status}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>

        <aside className="studio-sidebar right-sidebar">
          <div className="sidebar-section">
            <h3>Export Wizard</h3>
            <div className="export-steps">
              {studio.export_wizard.steps.map((step) => (
                <div key={step.id} className={`export-step ${step.status}`}>
                  <span className="step-dot"></span>
                  <span className="step-title">{step.title}</span>
                  <span className="step-status">{step.status}</span>
                </div>
              ))}
            </div>
          </div>

          {studio.segmentation_corrections.length > 0 && (
            <div className="sidebar-section">
              <h3>AI Corrections</h3>
              {studio.segmentation_corrections.map((corr) => (
                <div key={corr.id} className={`correction-card ${corr.status}`}>
                  <p className="correction-title">{corr.title}</p>
                  <p className="correction-change">{corr.change}</p>
                  <p className="correction-confidence">
                    Confidence: {Math.round(corr.confidence * 100)}%
                  </p>
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
