import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { getStudioStateApi, getProjectApi, type StudioState, type Project } from "../lib/projects-api";
import { navigateTo } from "../lib/hash-router";
import { runStudioAction } from "../lib/studio-actions";
import {
  fetchPluginExportDownload,
  fetchPluginProjectExports,
  type PluginProjectExport,
  type PluginExportDownload,
} from "../lib/plugin-api";
import {
  cancelStudioAiJob,
  listStudioAiJobs,
  retryStudioAiJob,
  type StudioAiJob,
} from "../lib/studio-api";

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
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [aiJobs, setAiJobs] = useState<StudioAiJob[]>([]);
  const [activeJobActionId, setActiveJobActionId] = useState<string | null>(null);
  const [exportsList, setExportsList] = useState<PluginProjectExport[]>([]);
  const [downloadPreview, setDownloadPreview] = useState<PluginExportDownload | null>(null);
  const [activeExportId, setActiveExportId] = useState<string | null>(null);

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
        const [proj, state, jobs, exports] = await Promise.all([
          getProjectApi(authToken, projectId),
          getStudioStateApi(authToken, projectId),
          listStudioAiJobs({ projectId, token: authToken }),
          fetchPluginProjectExports({ projectId, engine: "all", token: authToken }),
        ]);
        if (cancelled) return;
        setProject(proj);
        setStudio(state);
        setAiJobs(jobs);
        setExportsList(exports);
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

  const handleStudioAction = async (actionId: string) => {
    if (!token || !project || !studio || activeActionId) return;
    try {
      setActiveActionId(actionId);
      setError(null);
      setActionMessage(null);
      const result = await runStudioAction({ actionId, token, project, studio });
      setActionMessage(result.message);
      const [latestStudio, latestJobs, latestExports] = await Promise.all([
        getStudioStateApi(token, project.id),
        listStudioAiJobs({ projectId: project.id, token }),
        fetchPluginProjectExports({ projectId: project.id, engine: "all", token }),
      ]);
      setStudio(latestStudio);
      setAiJobs(latestJobs);
      setExportsList(latestExports);
    } catch (err: any) {
      setError(err.message || "Failed to run Studio action");
    } finally {
      setActiveActionId(null);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    if (!token || !project || activeJobActionId) return;
    try {
      setActiveJobActionId(jobId);
      setError(null);
      await cancelStudioAiJob({ projectId: project.id, jobId, token });
      setAiJobs(await listStudioAiJobs({ projectId: project.id, token }));
    } catch (err: any) {
      setError(err.message || "Failed to cancel AI job");
    } finally {
      setActiveJobActionId(null);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    if (!token || !project || activeJobActionId) return;
    try {
      setActiveJobActionId(jobId);
      setError(null);
      await retryStudioAiJob({ projectId: project.id, jobId, token });
      setAiJobs(await listStudioAiJobs({ projectId: project.id, token }));
    } catch (err: any) {
      setError(err.message || "Failed to retry AI job");
    } finally {
      setActiveJobActionId(null);
    }
  };

  const handleDownloadExport = async (exportId: string) => {
    if (!token || activeExportId) return;
    try {
      setActiveExportId(exportId);
      setError(null);
      const download = await fetchPluginExportDownload({ exportId, token });
      setDownloadPreview(download);
      setActionMessage(`Export ${download.exportId} ready: ${download.files.length} files, ${download.checksum}`);
    } catch (err: any) {
      setError(err.message || "Failed to download export package");
    } finally {
      setActiveExportId(null);
    }
  };

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
                <button
                  key={action.id}
                  className="action-btn"
                  type="button"
                  onClick={() => handleStudioAction(action.id)}
                  disabled={activeActionId !== null}
                >
                  {activeActionId === action.id ? "Running..." : action.title}
                  <span className="shortcut">{action.shortcut}</span>
                </button>
              ))}
            </div>
            {actionMessage && <div className="studio-action-message">{actionMessage}</div>}
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

          <div className="sidebar-section">
            <h3>Export Packages</h3>
            <div className="studio-exports-list">
              {exportsList.length === 0 ? (
                <p className="studio-empty-state">No export packages yet</p>
              ) : (
                exportsList.slice(0, 4).map((item) => (
                  <div key={item.id} className="studio-export-card">
                    <div className="studio-job-header">
                      <span className="studio-job-kind">{item.engine}</span>
                      <span className="studio-job-status">{item.status}</span>
                    </div>
                    <p className="studio-job-prompt">{item.entry.path}</p>
                    <div className="studio-job-actions">
                      <button
                        type="button"
                        onClick={() => handleDownloadExport(item.id)}
                        disabled={activeExportId !== null}
                      >
                        {activeExportId === item.id ? "Loading..." : "Download"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
            {downloadPreview && (
              <div className="studio-download-preview">
                <span>{downloadPreview.contentType}</span>
                <b>{downloadPreview.manifest.entry.path}</b>
              </div>
            )}
          </div>

          <div className="sidebar-section">
            <h3>AI Jobs</h3>
            <div className="studio-jobs-list">
              {aiJobs.length === 0 ? (
                <p className="studio-empty-state">No AI jobs yet</p>
              ) : (
                aiJobs.slice(0, 5).map((job) => (
                  <div key={job.id} className={`studio-job-card ${job.status || "unknown"}`}>
                    <div className="studio-job-header">
                      <span className="studio-job-kind">{job.kind}</span>
                      <span className="studio-job-status">{job.status || "unknown"}</span>
                    </div>
                    <p className="studio-job-prompt">{job.prompt}</p>
                    {typeof job.progress === "number" && (
                      <div className="task-progress-bar">
                        <div
                          className="task-progress-fill"
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                    )}
                    <div className="studio-job-actions">
                      {job.status === "queued" || job.status === "running" ? (
                        <button
                          type="button"
                          onClick={() => handleCancelJob(job.id)}
                          disabled={activeJobActionId !== null}
                        >
                          Cancel
                        </button>
                      ) : null}
                      {job.status === "failed" || job.status === "cancelled" ? (
                        <button
                          type="button"
                          onClick={() => handleRetryJob(job.id)}
                          disabled={activeJobActionId !== null}
                        >
                          Retry
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))
              )}
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
