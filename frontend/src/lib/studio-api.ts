export type StudioApiFetcher = (url: string, init?: RequestInit) => Promise<Response>;

export type StudioApiTimelineTask = {
  kind: string;
  status: "queued" | "ready" | "running" | "succeeded";
  progress: number;
};

export type StudioApiAction = {
  id: string;
  title: string;
  shortcut: string;
};

export type StudioApiCorrection = {
  id: string;
  targetLayerId: string;
  title: string;
  change: string;
  confidence: number;
  status: "pending" | "applied";
};

export type StudioApiWizardStep = {
  id: string;
  title: string;
  status: "complete" | "active" | "pending";
};

export type StudioApiState = {
  projectId: string;
  activeSelection: {
    selectedLayerId: string;
    selectedAssetId: string;
    activeTaskId: string;
  };
  timeline: StudioApiTimelineTask[];
  actionDock: StudioApiAction[];
  segmentationCorrections: StudioApiCorrection[];
  exportWizard: {
    targetEngine: string;
    steps: StudioApiWizardStep[];
  };
};

type StudioStateDto = {
  project_id: string;
  active_selection: {
    selected_layer_id: string;
    selected_asset_id: string;
    active_task_id: string;
  };
  timeline: StudioApiTimelineTask[];
  action_dock: StudioApiAction[];
  segmentation_corrections: Array<{
    id: string;
    target_layer_id: string;
    title: string;
    change: string;
    confidence: number;
    status: "pending" | "applied";
  }>;
  export_wizard: {
    target_engine: string;
    steps: StudioApiWizardStep[];
  };
};

export async function fetchStudioState(options: {
  projectId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioApiState> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/studio`,
    options.token,
    options.fetcher
  );
  return mapStudioStateDto(await response.json() as StudioStateDto);
}

export async function applyStudioCorrection(options: {
  projectId: string;
  correctionId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<unknown> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/studio/corrections/${options.correctionId}/apply`,
    options.token,
    options.fetcher,
    { method: "POST" }
  );
  return response.json();
}

export async function previewStudioExportWizard(options: {
  projectId: string;
  targetEngine: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<unknown> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/studio/export-wizard`,
    options.token,
    options.fetcher,
    {
      method: "POST",
      body: JSON.stringify({ target_engine: options.targetEngine })
    }
  );
  return response.json();
}

function mapStudioStateDto(dto: StudioStateDto): StudioApiState {
  return {
    projectId: dto.project_id,
    activeSelection: {
      selectedLayerId: dto.active_selection.selected_layer_id,
      selectedAssetId: dto.active_selection.selected_asset_id,
      activeTaskId: dto.active_selection.active_task_id
    },
    timeline: dto.timeline,
    actionDock: dto.action_dock,
    segmentationCorrections: dto.segmentation_corrections.map((correction) => ({
      id: correction.id,
      targetLayerId: correction.target_layer_id,
      title: correction.title,
      change: correction.change,
      confidence: correction.confidence,
      status: correction.status
    })),
    exportWizard: {
      targetEngine: dto.export_wizard.target_engine,
      steps: dto.export_wizard.steps
    }
  };
}

async function requestStudioApi(
  url: string,
  token: string,
  fetcher: StudioApiFetcher = fetch,
  init: RequestInit = {}
): Promise<Response> {
  const response = await fetcher(url, {
    ...init,
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(`Studio API request failed: ${url}`);
  }
  return response;
}
