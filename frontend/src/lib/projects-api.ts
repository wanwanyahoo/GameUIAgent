export type Project = {
  id: string;
  name: string;
  target_engine: string;
  canvas: { width: number; height: number };
  status: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
};

export type ProjectCreateRequest = {
  name: string;
  target_engine: string;
  canvas: { width: number; height: number };
};

export type ProjectsListResponse = {
  projects: Project[];
};

export type StudioState = {
  project_id: string;
  active_selection: {
    selected_layer_id: string;
    selected_asset_id: string;
    active_task_id: string;
  };
  action_dock: Array<{ id: string; title: string; shortcut: string }>;
  timeline: Array<Record<string, unknown>>;
  segmentation_corrections: Array<{
    id: string;
    target_layer_id: string;
    title: string;
    change: string;
    confidence: number;
    status: string;
  }>;
  export_wizard: {
    target_engine: string;
    steps: Array<{ id: string; title: string; status: string }>;
  };
};

export async function listProjectsApi(
  token: string,
  options?: { fetcher?: typeof fetch }
): Promise<Project[]> {
  const fetchFn = options?.fetcher || fetch;
  const res = await fetchFn("/api/projects", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    let detail = `Failed to list projects (${res.status})`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  const data: ProjectsListResponse = await res.json();
  return data.projects;
}

export async function createProjectApi(
  token: string,
  payload: ProjectCreateRequest,
  options?: { fetcher?: typeof fetch }
): Promise<Project> {
  const fetchFn = options?.fetcher || fetch;
  const res = await fetchFn("/api/projects", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = `Failed to create project (${res.status})`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<Project>;
}

export async function getProjectApi(
  token: string,
  projectId: string,
  options?: { fetcher?: typeof fetch }
): Promise<Project> {
  const fetchFn = options?.fetcher || fetch;
  const res = await fetchFn(`/api/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    let detail = `Failed to get project (${res.status})`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<Project>;
}

export async function getStudioStateApi(
  token: string,
  projectId: string,
  options?: { fetcher?: typeof fetch }
): Promise<StudioState> {
  const fetchFn = options?.fetcher || fetch;
  const res = await fetchFn(`/api/projects/${projectId}/studio`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    let detail = `Failed to get studio state (${res.status})`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<StudioState>;
}
