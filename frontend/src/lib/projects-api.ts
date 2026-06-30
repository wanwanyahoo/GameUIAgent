export type Project = {
  id: string;
  name: string;
  target_engine: string;
  canvas: { width: number; height: number };
  status: string;
  owner_id: string;
};

export type ProjectCreateRequest = {
  name: string;
  target_engine: string;
  canvas: { width: number; height: number };
};

export type ProjectsListResponse = {
  projects: Project[];
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
