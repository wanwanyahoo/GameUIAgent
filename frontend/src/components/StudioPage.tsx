import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth-context";
import { getStudioStateApi, getProjectApi, type StudioState, type Project } from "../lib/projects-api";
import { navigateTo } from "../lib/hash-router";
import { runGeneratedAssetAction, runProfessionalImportAction, runStudioAction } from "../lib/studio-actions";
import { collectGeneratedAssets } from "../lib/studio-generated-assets";
import {
  fetchPluginExportArchive,
  fetchPluginExportDownload,
  fetchPluginProjectExports,
  submitPluginImportLog,
  type PluginProjectExport,
  type PluginExportArchive,
  type PluginExportDownload,
  type PluginImportLog,
} from "../lib/plugin-api";
import {
  cancelStudioAiJob,
  fetchStudioIr,
  listStudioAssets,
  listStudioAiJobs,
  patchStudioIr,
  retryStudioAiJob,
  validateStudioIr,
  type StudioAsset,
  type StudioAiJob,
} from "../lib/studio-api";
import {
  buildStudioEditorState,
  createStudioEditorPatch,
  redoStudioEditor,
  selectStudioEditorNode,
  undoStudioEditor,
  updateStudioEditorNode,
  type StudioEditorLayerNode,
  type StudioEditorState,
} from "../lib/studio-editor";

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
  const [assets, setAssets] = useState<StudioAsset[]>([]);
  const [aiJobs, setAiJobs] = useState<StudioAiJob[]>([]);
  const [activeJobActionId, setActiveJobActionId] = useState<string | null>(null);
  const [exportsList, setExportsList] = useState<PluginProjectExport[]>([]);
  const [downloadPreview, setDownloadPreview] = useState<PluginExportDownload | null>(null);
  const [downloadArchive, setDownloadArchive] = useState<PluginExportArchive | null>(null);
  const [activeExportId, setActiveExportId] = useState<string | null>(null);
  const [activeGeneratedActionId, setActiveGeneratedActionId] = useState<string | null>(null);
  const [activeProfessionalImport, setActiveProfessionalImport] = useState(false);
  const [activePluginImportId, setActivePluginImportId] = useState<string | null>(null);
  const [latestPluginImportLog, setLatestPluginImportLog] = useState<PluginImportLog | null>(null);
  const [professionalImportFile, setProfessionalImportFile] = useState<File | null>(null);
  const [figmaImportUrl, setFigmaImportUrl] = useState("");
  const [figmaImportFrameId, setFigmaImportFrameId] = useState("");
  const [editor, setEditor] = useState<StudioEditorState | null>(null);
  const [savingEditor, setSavingEditor] = useState(false);

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
        const [proj, state, projectAssets, jobs, exports] = await Promise.all([
          getProjectApi(authToken, projectId),
          getStudioStateApi(authToken, projectId),
          listStudioAssets({ projectId, token: authToken }),
          listStudioAiJobs({ projectId, token: authToken }),
          fetchPluginProjectExports({ projectId, engine: "all", token: authToken }),
        ]);
        if (cancelled) return;
        setProject(proj);
        setStudio(state);
        setAssets(projectAssets);
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

  useEffect(() => {
    const activeIrId = studio?.active_selection.active_ir_id;
    const selectedLayerId = studio?.active_selection.selected_layer_id;
    const currentProjectId = project?.id;
    const authToken = token;
    if (!authToken || !currentProjectId || !activeIrId) return;
    const projectIdForEditor: string = currentProjectId;
    const irIdForEditor: string = activeIrId;
    const tokenForEditor: string = authToken;

    let cancelled = false;
    async function loadEditor() {
      try {
        const ir = await fetchStudioIr({
          projectId: projectIdForEditor,
          irId: irIdForEditor,
          token: tokenForEditor,
        });
        if (!cancelled) {
          setEditor(buildStudioEditorState(ir, selectedLayerId));
        }
      } catch (err: any) {
        if (!cancelled) setError(err.message || "Failed to load editable Asset IR");
      }
    }
    loadEditor();
    return () => {
      cancelled = true;
    };
  }, [token, project?.id, studio?.active_selection.active_ir_id, studio?.active_selection.selected_layer_id]);

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
  const generatedAssets = collectGeneratedAssets({ aiJobs, assets });

  const handleStudioAction = async (actionId: string) => {
    if (!token || !project || !studio || activeActionId) return;
    try {
      setActiveActionId(actionId);
      setError(null);
      setActionMessage(null);
      const result = await runStudioAction({ actionId, token, project, studio });
      setActionMessage(result.message);
      const [latestStudio, latestAssets, latestJobs, latestExports] = await Promise.all([
        getStudioStateApi(token, project.id),
        listStudioAssets({ projectId: project.id, token }),
        listStudioAiJobs({ projectId: project.id, token }),
        fetchPluginProjectExports({ projectId: project.id, engine: "all", token }),
      ]);
      setStudio(latestStudio);
      setAssets(latestAssets);
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
      const [download, archive] = await Promise.all([
        fetchPluginExportDownload({ exportId, token }),
        fetchPluginExportArchive({ exportId, token }),
      ]);
      setDownloadPreview(download);
      setDownloadArchive(archive);
      setActionMessage(`Export ${download.exportId} ready: ${archive.fileName}, ${archive.content.byteLength} bytes`);
    } catch (err: any) {
      setError(err.message || "Failed to download export package");
    } finally {
      setActiveExportId(null);
    }
  };

  const handleGeneratedAssetAction = async (actionId: string, assetId: string) => {
    if (!token || !project || !studio || activeGeneratedActionId) return;
    try {
      setActiveGeneratedActionId(`${actionId}:${assetId}`);
      setError(null);
      setActionMessage(null);
      const result = await runGeneratedAssetAction({ actionId, assetId, token, project, studio });
      setActionMessage(result.message);
      const [latestStudio, latestAssets, latestJobs, latestExports] = await Promise.all([
        getStudioStateApi(token, project.id),
        listStudioAssets({ projectId: project.id, token }),
        listStudioAiJobs({ projectId: project.id, token }),
        fetchPluginProjectExports({ projectId: project.id, engine: "all", token }),
      ]);
      setStudio(latestStudio);
      setAssets(latestAssets);
      setAiJobs(latestJobs);
      setExportsList(latestExports);
    } catch (err: any) {
      setError(err.message || "Failed to run generated asset action");
    } finally {
      setActiveGeneratedActionId(null);
    }
  };

  const handleProfessionalImport = async () => {
    if (!token || !project || activeProfessionalImport) return;
    try {
      setActiveProfessionalImport(true);
      setError(null);
      setActionMessage(null);
      const result = await runProfessionalImportAction({
        token,
        project,
        file: professionalImportFile,
        figmaUrl: figmaImportUrl,
        frameId: figmaImportFrameId,
      });
      setActionMessage(result.message);
      const [latestStudio, latestAssets, latestExports] = await Promise.all([
        getStudioStateApi(token, project.id),
        listStudioAssets({ projectId: project.id, token }),
        fetchPluginProjectExports({ projectId: project.id, engine: "all", token }),
      ]);
      setStudio(latestStudio);
      setAssets(latestAssets);
      setExportsList(latestExports);
    } catch (err: any) {
      setError(err.message || "Failed to import professional PSD");
    } finally {
      setActiveProfessionalImport(false);
    }
  };

  const handleSelectEditorNode = (nodeId: string) => {
    if (!editor) return;
    setEditor(selectStudioEditorNode(editor, nodeId));
  };

  const handleEditorFieldChange = (field: string, value: string | number | boolean) => {
    if (!editor) return;
    if (["x", "y", "width", "height"].includes(field)) {
      setEditor(updateStudioEditorNode(editor, {
        rect: {
          ...editor.inspector.rect,
          [field]: Number(value),
        },
      }));
      return;
    }
    setEditor(updateStudioEditorNode(editor, { [field]: value }));
  };

  const handleUndoEditor = () => {
    if (editor) setEditor(undoStudioEditor(editor));
  };

  const handleRedoEditor = () => {
    if (editor) setEditor(redoStudioEditor(editor));
  };

  const handleSaveEditor = async () => {
    if (!token || !project || !editor || savingEditor) return;
    const patch = createStudioEditorPatch(editor, `Studio edit ${editor.selectedNode?.name ?? editor.selectedNodeId}`);
    if (patch.operations.length === 0) {
      setActionMessage("No editor changes to save");
      return;
    }
    try {
      setSavingEditor(true);
      setError(null);
      await validateStudioIr({ projectId: project.id, irId: editor.draftIr.id, token });
      const result = await patchStudioIr({
        projectId: project.id,
        irId: editor.draftIr.id,
        token,
        ...patch,
      });
      setEditor(buildStudioEditorState(result.ir, editor.selectedNodeId));
      setActionMessage(`Saved Asset IR ${result.version.version}`);
    } catch (err: any) {
      setError(err.message || "Failed to save Asset IR edits");
    } finally {
      setSavingEditor(false);
    }
  };

  const handlePluginImportLog = async (item: PluginProjectExport) => {
    if (!token || !project || activePluginImportId) return;
    try {
      setActivePluginImportId(item.id);
      setError(null);
      const log = await submitPluginImportLog({
        exportId: item.id,
        engine: item.engine,
        status: "succeeded",
        pluginVersion: "0.4.0",
        engineVersion: item.engineVersion || defaultEngineVersion(item.engine),
        durationMs: 3900,
        summary: pluginImportSummary(item.engine),
        logs: [{ level: "info", message: `Imported ${item.entry.path} through GameUIAgent ${item.engine} plugin` }],
        token,
      });
      setLatestPluginImportLog(log);
      setStudio(await getStudioStateApi(token, project.id));
      setActionMessage(`${item.engine} plugin import logged: ${log.status}`);
    } catch (err: any) {
      setError(err.message || "Failed to log plugin import");
    } finally {
      setActivePluginImportId(null);
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
          {editor && (
            <div className="studio-editor-panel">
              <h3>Layer Tree</h3>
              <div className="studio-layer-tree">
                {editor.layerTree.map((node) => (
                  <LayerTreeItem
                    key={node.id}
                    node={node}
                    selectedNodeId={editor.selectedNodeId}
                    onSelect={handleSelectEditorNode}
                  />
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="studio-canvas-area">
          <div className={editor ? "studio-canvas-workbench" : "studio-canvas-placeholder"}>
            <h2>AI Canvas</h2>
            <p>
              {project.name} — {project.canvas.width}×{project.canvas.height}
            </p>
            {editor && (
              <div className="studio-ir-canvas">
                {editor.draftIr.nodes.filter((node) => node.type !== "canvas").map((node) => (
                  <button
                    key={node.id}
                    type="button"
                    className={`studio-ir-node ${node.type} ${editor.selectedNodeId === node.id ? "selected" : ""}`}
                    style={{
                      left: `${(node.rect.x / project.canvas.width) * 100}%`,
                      top: `${(node.rect.y / project.canvas.height) * 100}%`,
                      width: `${(node.rect.width / project.canvas.width) * 100}%`,
                      height: `${(node.rect.height / project.canvas.height) * 100}%`,
                    }}
                    onClick={() => handleSelectEditorNode(node.id)}
                  >
                    {node.name}
                  </button>
                ))}
              </div>
            )}
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
          {editor && (
            <div className="sidebar-section">
              <h3>Inspector</h3>
              <div className="studio-inspector">
                <label>
                  <span>Name</span>
                  <input
                    type="text"
                    value={editor.inspector.name}
                    onChange={(event) => handleEditorFieldChange("name", event.currentTarget.value)}
                  />
                </label>
                <div className="studio-inspector-grid">
                  {(["x", "y", "width", "height"] as const).map((field) => (
                    <label key={field}>
                      <span>{field}</span>
                      <input
                        type="number"
                        value={editor.inspector.rect[field]}
                        onChange={(event) => handleEditorFieldChange(field, Number(event.currentTarget.value))}
                      />
                    </label>
                  ))}
                </div>
                <label className="studio-inspector-toggle">
                  <input
                    type="checkbox"
                    checked={editor.inspector.visible}
                    onChange={(event) => handleEditorFieldChange("visible", event.currentTarget.checked)}
                  />
                  <span>Visible</span>
                </label>
                <div className="studio-editor-actions">
                  <button type="button" onClick={handleUndoEditor} disabled={editor.undoStack.length === 0}>Undo</button>
                  <button type="button" onClick={handleRedoEditor} disabled={editor.redoStack.length === 0}>Redo</button>
                  <button type="button" onClick={handleSaveEditor} disabled={savingEditor}>
                    {savingEditor ? "Saving..." : "Save IR"}
                  </button>
                </div>
                <p className="studio-asset-id">Version {editor.baseVersion} | {editor.selectedNodeId}</p>
              </div>
            </div>
          )}

          <div className="sidebar-section">
            <h3>Professional Import</h3>
            <div className="studio-professional-import">
              <p>PSD/PSB/Figma layers become editable Asset IR before export.</p>
              <label className="studio-file-picker">
                <span>{professionalImportFile ? professionalImportFile.name : "Choose PSD / PSB file"}</span>
                <input
                  type="file"
                  accept=".psd,.psb,application/octet-stream"
                  onChange={(event) => setProfessionalImportFile(event.currentTarget.files?.[0] ?? null)}
                  disabled={activeProfessionalImport}
                />
              </label>
              <input
                className="studio-import-input"
                type="url"
                value={figmaImportUrl}
                onChange={(event) => setFigmaImportUrl(event.currentTarget.value)}
                placeholder="Paste Figma file or frame URL"
                disabled={activeProfessionalImport}
              />
              <input
                className="studio-import-input"
                type="text"
                value={figmaImportFrameId}
                onChange={(event) => setFigmaImportFrameId(event.currentTarget.value)}
                placeholder="Optional frame/node id, e.g. 12:34"
                disabled={activeProfessionalImport}
              />
              <button
                type="button"
                onClick={handleProfessionalImport}
                disabled={activeProfessionalImport}
              >
                {activeProfessionalImport ? "Importing..." : figmaImportUrl.trim() ? "Import Figma + Export Unity" : professionalImportFile ? "Upload PSD + Export Unity" : "Import PSD + Export Unity"}
              </button>
            </div>
          </div>

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
                      <button
                        type="button"
                        onClick={() => handlePluginImportLog(item)}
                        disabled={activePluginImportId !== null}
                      >
                        {activePluginImportId === item.id ? "Logging..." : "Log Plugin Import"}
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
                {downloadArchive && (
                  <span>{downloadArchive.fileName} | {downloadArchive.content.byteLength} bytes</span>
                )}
              </div>
            )}
            {latestPluginImportLog && (
              <div className="studio-download-preview">
                <span>{latestPluginImportLog.engine} plugin import</span>
                <b>{latestPluginImportLog.status}</b>
                <span>{latestPluginImportLog.pluginVersion} | {latestPluginImportLog.durationMs}ms</span>
              </div>
            )}
          </div>

          <div className="sidebar-section">
            <h3>Generated Assets</h3>
            <div className="studio-generated-assets-list">
              {generatedAssets.length === 0 ? (
                <p className="studio-empty-state">No generated assets yet</p>
              ) : (
                generatedAssets.slice(0, 5).map((asset) => (
                  <div key={asset.id} className="studio-generated-asset-card">
                    <div className="studio-job-header">
                      <span className="studio-job-kind">{asset.sourceKind}</span>
                      {asset.rank !== undefined && <span className="studio-job-status">rank {asset.rank}</span>}
                    </div>
                    <p className="studio-job-prompt">{asset.name || asset.prompt}</p>
                    {(asset.width && asset.height) || asset.usage ? (
                      <p className="studio-asset-meta">
                        {asset.width && asset.height ? `${asset.width}x${asset.height}` : "unknown size"}
                        {asset.usage ? ` | ${asset.usage}` : ""}
                      </p>
                    ) : null}
                    <p className="studio-asset-id">{asset.id}</p>
                    <div className="studio-job-actions">
                      <button
                        type="button"
                        onClick={() => handleGeneratedAssetAction("slice-generated-asset", asset.id)}
                        disabled={activeGeneratedActionId !== null}
                      >
                        {activeGeneratedActionId === `slice-generated-asset:${asset.id}` ? "Slicing..." : "Slice"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleGeneratedAssetAction("export-generated-asset", asset.id)}
                        disabled={activeGeneratedActionId !== null}
                      >
                        {activeGeneratedActionId === `export-generated-asset:${asset.id}` ? "Exporting..." : "Export"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
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

function pluginImportSummary(engine: string): Record<string, number> {
  if (engine === "unity") {
    return { assets_imported: 4, prefabs_created: 1, scenes_created: 1, warnings: 0, errors: 0 };
  }
  if (engine === "godot") {
    return { scenes_created: 1, controls_created: 4, warnings: 0, errors: 0 };
  }
  if (engine === "unreal") {
    return { textures_created: 1, umg_widgets_created: 1, warnings: 0, errors: 0 };
  }
  return { prefabs_created: 1, warnings: 0, errors: 0 };
}

function defaultEngineVersion(engine: string): string {
  if (engine === "unity") return "2022.3.40f1";
  if (engine === "unreal") return "5.3+";
  if (engine === "godot") return "4.x";
  if (engine === "cocos2") return "2.4.x+";
  return "3.8.6+";
}

function LayerTreeItem({
  node,
  selectedNodeId,
  onSelect,
}: {
  node: StudioEditorLayerNode;
  selectedNodeId: string;
  onSelect: (nodeId: string) => void;
}) {
  return (
    <div className="studio-layer-tree-item">
      <button
        type="button"
        className={selectedNodeId === node.id ? "selected" : ""}
        onClick={() => onSelect(node.id)}
      >
        <span>{node.name}</span>
        <small>{node.type}</small>
      </button>
      {node.children.length > 0 && (
        <div className="studio-layer-tree-children">
          {node.children.map((child) => (
            <LayerTreeItem
              key={child.id}
              node={child}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
