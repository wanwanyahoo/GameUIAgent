export type StudioApiFetcher = (url: string, init?: RequestInit) => Promise<Response>;

export type StudioApiTimelineTask = {
  kind: string;
  status: "queued" | "ready" | "running" | "succeeded" | "failed";
  progress: number;
  summary?: Record<string, number>;
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

export type StudioAsset = {
  id: string;
  projectId: string;
  type: string;
  name: string;
  url: string;
  source: string;
  metadata: {
    width: number;
    height: number;
    usage: string;
    tags?: string[];
    [key: string]: unknown;
  };
};

export type StudioAssetVersion = {
  id: string;
  assetId: string;
  event: string;
  name: string;
};

export type StudioAiJob = {
  id: string;
  projectId: string;
  kind: string;
  prompt: string;
  status?: string;
  progress?: number;
  executionMode?: string;
  inputAsset?: { id: string } | null;
  resultAsset?: { id: string };
  candidates: Array<{ assetId: string; rank?: number; score?: number }>;
  estimatedCredits: number;
  retryOf?: string;
};

export type StudioSegmentation = {
  id: string;
  projectId: string;
  sourceAssetId: string;
  irId: string;
  confidence: number;
  slices: Array<{
    id: string;
    type: string;
    editableBounds: boolean;
  }>;
};

export type ProfessionalImportSource = {
  id: string;
  projectId: string;
  status: string;
  source: {
    sourceType: string;
    assetId?: string | null;
    figmaUrl?: string | null;
    frameId?: string | null;
    parser: string;
  };
  parseSummary: {
    parser: string;
    preservedLayers: number;
    warnings: string[];
  };
  ir: {
    id: string;
    projectId: string;
    professionalSource?: Record<string, unknown>;
  };
};

export type StudioIrNode = {
  id: string;
  type: string;
  name: string;
  rect: { x: number; y: number; width: number; height: number };
  visible?: boolean;
  opacity?: number;
  text?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  component?: Record<string, unknown>;
  nineSlice?: Record<string, unknown>;
  parentId?: string | null;
  [key: string]: unknown;
};

export type StudioIr = {
  id: string;
  projectId: string;
  version: string;
  canvas?: { width: number; height: number };
  nodes: StudioIrNode[];
  professionalSource?: Record<string, unknown>;
};

export type StudioIrVersion = {
  id: string;
  projectId: string;
  irId: string;
  version: string;
  summary: string;
  patchId: string | null;
  authorId: string;
  createdAt: string;
};

export type StudioIrPatchOperation = {
  op: "update_node";
  nodeId: string;
  fields: Record<string, unknown>;
};

export type StudioIrPatchResult = {
  ir: StudioIr;
  patch: Record<string, unknown>;
  version: StudioIrVersion;
};

export type StudioIrValidation = {
  irId: string;
  status: "valid";
  errors: Array<Record<string, unknown>>;
};

export type StudioIrRestoreResult = {
  ir: StudioIr;
  version: StudioIrVersion;
  restoredFrom?: StudioIrVersion;
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

type StudioAssetDto = {
  id: string;
  project_id: string;
  type: string;
  name: string;
  url: string;
  source: string;
  metadata: {
    width: number;
    height: number;
    usage: string;
    tags?: string[];
  };
};

type StudioAssetVersionDto = {
  id: string;
  asset_id?: string;
  event: string;
  name: string;
};

type StudioAiJobDto = {
  id: string;
  project_id: string;
  kind: string;
  prompt: string;
  status?: string;
  progress?: number;
  execution_mode?: string;
  input_asset?: { id: string } | null;
  result_asset?: { id: string };
  candidates?: Array<{ asset_id: string; rank?: number; score?: number }>;
  estimated_credits: number;
  retry_of?: string;
};

type StudioSegmentationDto = {
  id: string;
  project_id: string;
  source_asset_id: string;
  ir_id: string;
  confidence: number;
  slices: Array<{
    id: string;
    type: string;
    editable_bounds: boolean;
  }>;
};

type ProfessionalImportSourceDto = {
  id: string;
  project_id: string;
  status: string;
  source: {
    source_type: string;
    asset_id?: string | null;
    figma_url?: string | null;
    frame_id?: string | null;
    parser: string;
  };
  parse_summary: {
    parser: string;
    preserved_layers: number;
    warnings: string[];
  };
  ir: {
    id: string;
    project_id: string;
    professional_source?: Record<string, unknown>;
  };
};

type StudioIrNodeDto = {
  id: string;
  type: string;
  name: string;
  rect: { x: number; y: number; width: number; height: number };
  visible?: boolean;
  opacity?: number;
  text?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  component?: Record<string, unknown>;
  nine_slice?: Record<string, unknown>;
  parent_id?: string | null;
  [key: string]: unknown;
};

type StudioIrDto = {
  id: string;
  project_id: string;
  version: string;
  canvas?: { width: number; height: number };
  nodes: StudioIrNodeDto[];
  professional_source?: Record<string, unknown>;
};

type StudioIrVersionDto = {
  id: string;
  project_id: string;
  ir_id: string;
  version: string;
  summary: string;
  patch_id: string | null;
  author_id: string;
  created_at: string;
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

export async function createStudioAsset(options: {
  projectId: string;
  token: string;
  asset: {
    name: string;
    type: string;
    url: string;
    width: number;
    height: number;
    usage: string;
    tags?: string[];
  };
  fetcher?: StudioApiFetcher;
}): Promise<StudioAsset> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/assets`,
    options.token,
    options.fetcher,
    {
      method: "POST",
      body: JSON.stringify(options.asset)
    }
  );
  return mapStudioAssetDto(await response.json() as StudioAssetDto);
}

export async function uploadStudioAsset(options: {
  projectId: string;
  token: string;
  file: File;
  type: string;
  width: number;
  height: number;
  usage: string;
  tags?: string[];
  fetcher?: StudioApiFetcher;
}): Promise<StudioAsset> {
  const form = new FormData();
  form.set("name", options.file.name);
  form.set("type", options.type);
  form.set("width", String(options.width));
  form.set("height", String(options.height));
  form.set("usage", options.usage);
  form.set("tags", (options.tags ?? []).join(","));
  form.set("file", options.file);
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    `/api/projects/${options.projectId}/assets/upload`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${options.token}`
      },
      body: form
    }
  );
  if (!response.ok) {
    throw new Error(`Studio asset upload failed: ${options.file.name}`);
  }
  return mapStudioAssetDto(await response.json() as StudioAssetDto);
}

export async function listStudioAssets(options: {
  projectId: string;
  token: string;
  search?: string;
  tag?: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAsset[]> {
  const query = new URLSearchParams();
  if (options.search) {
    query.set("search", options.search);
  }
  if (options.tag) {
    query.set("tag", options.tag);
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/assets${suffix}`,
    options.token,
    options.fetcher
  );
  const dto = await response.json() as { assets: StudioAssetDto[] };
  return dto.assets.map(mapStudioAssetDto);
}

export async function createProfessionalImportSource(options: {
  projectId: string;
  token: string;
  source: {
    sourceType: "psd" | "psb" | "figma";
    assetId?: string;
    figmaUrl?: string;
    frameId?: string;
    parser?: string;
  };
  fetcher?: StudioApiFetcher;
}): Promise<ProfessionalImportSource> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/imports/professional-sources`,
    options.token,
    options.fetcher,
    {
      method: "POST",
      body: JSON.stringify({
        source_type: options.source.sourceType,
        asset_id: options.source.assetId,
        figma_url: options.source.figmaUrl,
        frame_id: options.source.frameId,
        parser: options.source.parser ?? "mock-layer-parser"
      })
    }
  );
  return mapProfessionalImportSourceDto(await response.json() as ProfessionalImportSourceDto);
}

export async function updateStudioAsset(options: {
  projectId: string;
  assetId: string;
  token: string;
  patch: {
    name?: string;
    tags?: string[];
  };
  fetcher?: StudioApiFetcher;
}): Promise<StudioAsset> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/assets/${options.assetId}`,
    options.token,
    options.fetcher,
    {
      method: "PATCH",
      body: JSON.stringify(options.patch)
    }
  );
  return mapStudioAssetDto(await response.json() as StudioAssetDto);
}

export async function listStudioAssetVersions(options: {
  projectId: string;
  assetId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAssetVersion[]> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/assets/${options.assetId}/versions`,
    options.token,
    options.fetcher
  );
  const dto = await response.json() as { versions: StudioAssetVersionDto[] };
  return dto.versions.map((version) => ({
    id: version.id,
    assetId: version.asset_id ?? options.assetId,
    event: version.event,
    name: version.name
  }));
}

export async function fetchStudioIr(options: {
  projectId: string;
  irId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioIr> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/irs/${options.irId}`,
    options.token,
    options.fetcher
  );
  const dto = await response.json() as { ir: StudioIrDto };
  return mapStudioIrDto(dto.ir);
}

export async function listStudioIrVersions(options: {
  projectId: string;
  irId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioIrVersion[]> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/irs/${options.irId}/versions`,
    options.token,
    options.fetcher
  );
  const dto = await response.json() as { versions: StudioIrVersionDto[] };
  return dto.versions.map(mapStudioIrVersionDto);
}

export async function patchStudioIr(options: {
  projectId: string;
  irId: string;
  token: string;
  baseVersion: string;
  summary: string;
  operations: StudioIrPatchOperation[];
  fetcher?: StudioApiFetcher;
}): Promise<StudioIrPatchResult> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/irs/${options.irId}/patches`,
    options.token,
    options.fetcher,
    {
      method: "POST",
      body: JSON.stringify({
        base_version: options.baseVersion,
        summary: options.summary,
        operations: options.operations.map((operation) => ({
          op: operation.op,
          node_id: operation.nodeId,
          fields: operation.fields
        }))
      })
    }
  );
  const dto = await response.json() as {
    ir: StudioIrDto;
    patch: Record<string, unknown>;
    version: StudioIrVersionDto;
  };
  return {
    ir: mapStudioIrDto(dto.ir),
    patch: dto.patch,
    version: mapStudioIrVersionDto(dto.version)
  };
}

export async function validateStudioIr(options: {
  projectId: string;
  irId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioIrValidation> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/irs/${options.irId}/validate`,
    options.token,
    options.fetcher,
    { method: "POST" }
  );
  const dto = await response.json() as { ir_id: string; status: "valid"; errors: Array<Record<string, unknown>> };
  return { irId: dto.ir_id, status: dto.status, errors: dto.errors };
}

export async function restoreStudioIrVersion(options: {
  projectId: string;
  irId: string;
  versionId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioIrRestoreResult> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/irs/${options.irId}/versions/${options.versionId}/restore`,
    options.token,
    options.fetcher,
    { method: "POST" }
  );
  const dto = await response.json() as {
    ir: StudioIrDto;
    version: StudioIrVersionDto;
    restored_from?: StudioIrVersionDto;
  };
  return {
    ir: mapStudioIrDto(dto.ir),
    version: mapStudioIrVersionDto(dto.version),
    restoredFrom: dto.restored_from ? mapStudioIrVersionDto(dto.restored_from) : undefined
  };
}

export async function copyStudioAsset(options: {
  projectId: string;
  assetId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAsset> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/assets/${options.assetId}/copy`,
    options.token,
    options.fetcher,
    { method: "POST" }
  );
  return mapStudioAssetDto(await response.json() as StudioAssetDto);
}

export async function deleteStudioAsset(options: {
  projectId: string;
  assetId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<{ status: string }> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/assets/${options.assetId}`,
    options.token,
    options.fetcher,
    { method: "DELETE" }
  );
  return response.json() as Promise<{ status: string }>;
}

export async function createStudioAiJob(options: {
  projectId: string;
  token: string;
  job: {
    kind: string;
    prompt: string;
    inputAssetId?: string;
    referenceAssetId?: string;
    maskAssetId?: string;
    negativePrompt?: string;
    seed?: number;
    model?: string;
    count?: number;
    executionMode?: "inline" | "queued";
  };
  fetcher?: StudioApiFetcher;
}): Promise<StudioAiJob> {
  const payload = {
    kind: options.job.kind,
    prompt: options.job.prompt,
    input_asset_id: options.job.inputAssetId,
    reference_asset_id: options.job.referenceAssetId,
    mask_asset_id: options.job.maskAssetId,
    negative_prompt: options.job.negativePrompt,
    seed: options.job.seed,
    model: options.job.model,
    count: options.job.count,
    execution_mode: options.job.executionMode
  };
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/ai/jobs`,
    options.token,
    options.fetcher,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
  return mapStudioAiJobDto(await response.json() as StudioAiJobDto);
}

export async function listStudioAiJobs(options: {
  projectId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAiJob[]> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/ai/jobs`,
    options.token,
    options.fetcher
  );
  const dto = await response.json() as { jobs: StudioAiJobDto[] };
  return dto.jobs.map(mapStudioAiJobDto);
}

export async function getStudioAiJob(options: {
  projectId: string;
  jobId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAiJob> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/ai/jobs/${options.jobId}`,
    options.token,
    options.fetcher
  );
  return mapStudioAiJobDto(await response.json() as StudioAiJobDto);
}

export async function cancelStudioAiJob(options: {
  projectId: string;
  jobId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAiJob> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/ai/jobs/${options.jobId}/cancel`,
    options.token,
    options.fetcher,
    { method: "POST" }
  );
  return mapStudioAiJobDto(await response.json() as StudioAiJobDto);
}

export async function retryStudioAiJob(options: {
  projectId: string;
  jobId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioAiJob> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/ai/jobs/${options.jobId}/retry`,
    options.token,
    options.fetcher,
    { method: "POST" }
  );
  return mapStudioAiJobDto(await response.json() as StudioAiJobDto);
}

export async function createStudioSegmentation(options: {
  projectId: string;
  token: string;
  assetId: string;
  fetcher?: StudioApiFetcher;
}): Promise<StudioSegmentation> {
  const response = await requestStudioApi(
    `/api/projects/${options.projectId}/segmentations`,
    options.token,
    options.fetcher,
    {
      method: "POST",
      body: JSON.stringify({ asset_id: options.assetId })
    }
  );
  return mapStudioSegmentationDto(await response.json() as StudioSegmentationDto);
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

function mapStudioAssetDto(dto: StudioAssetDto): StudioAsset {
  return {
    id: dto.id,
    projectId: dto.project_id,
    type: dto.type,
    name: dto.name,
    url: dto.url,
    source: dto.source,
    metadata: dto.metadata
  };
}

function mapStudioAiJobDto(dto: StudioAiJobDto): StudioAiJob {
  return {
    id: dto.id,
    projectId: dto.project_id,
    kind: dto.kind,
    prompt: dto.prompt,
    status: dto.status,
    progress: dto.progress,
    executionMode: dto.execution_mode,
    inputAsset: dto.input_asset,
    resultAsset: dto.result_asset,
    candidates: (dto.candidates ?? []).map((candidate) => ({
      assetId: candidate.asset_id,
      rank: candidate.rank,
      score: candidate.score
    })),
    estimatedCredits: dto.estimated_credits,
    retryOf: dto.retry_of
  };
}

function mapStudioSegmentationDto(dto: StudioSegmentationDto): StudioSegmentation {
  return {
    id: dto.id,
    projectId: dto.project_id,
    sourceAssetId: dto.source_asset_id,
    irId: dto.ir_id,
    confidence: dto.confidence,
    slices: dto.slices.map((slice) => ({
      id: slice.id,
      type: slice.type,
      editableBounds: slice.editable_bounds
    }))
  };
}

function mapProfessionalImportSourceDto(dto: ProfessionalImportSourceDto): ProfessionalImportSource {
  return {
    id: dto.id,
    projectId: dto.project_id,
    status: dto.status,
    source: {
      sourceType: dto.source.source_type,
      assetId: dto.source.asset_id,
      figmaUrl: dto.source.figma_url,
      frameId: dto.source.frame_id,
      parser: dto.source.parser
    },
    parseSummary: {
      parser: dto.parse_summary.parser,
      preservedLayers: dto.parse_summary.preserved_layers,
      warnings: dto.parse_summary.warnings
    },
    ir: {
      id: dto.ir.id,
      projectId: dto.ir.project_id,
      professionalSource: dto.ir.professional_source
    }
  };
}

function mapStudioIrDto(dto: StudioIrDto): StudioIr {
  return {
    id: dto.id,
    projectId: dto.project_id,
    version: dto.version,
    canvas: dto.canvas,
    nodes: dto.nodes.map(mapStudioIrNodeDto),
    professionalSource: dto.professional_source
  };
}

function mapStudioIrNodeDto(dto: StudioIrNodeDto): StudioIrNode {
  const { parent_id, nine_slice, ...rest } = dto;
  return {
    ...rest,
    parentId: parent_id,
    nineSlice: nine_slice
  };
}

function mapStudioIrVersionDto(dto: StudioIrVersionDto): StudioIrVersion {
  return {
    id: dto.id,
    projectId: dto.project_id,
    irId: dto.ir_id,
    version: dto.version,
    summary: dto.summary,
    patchId: dto.patch_id,
    authorId: dto.author_id,
    createdAt: dto.created_at
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
