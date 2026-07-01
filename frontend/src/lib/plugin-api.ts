import type { StudioApiFetcher } from "./studio-api";

export type PluginProjectExport = {
  id: string;
  engine: string;
  engineVersion: string;
  status: string;
  name: string;
  entry: {
    type: string;
    path: string;
  };
  manifestUrl: string;
  downloadUrl: string;
};

export type PluginImportLog = {
  id: string;
  exportId: string;
  engine: string;
  status: string;
  pluginVersion: string;
  engineVersion: string;
  durationMs: number;
  summary: Record<string, number>;
  logs: Array<{
    level: string;
    message: string;
  }>;
};

export type PluginImportLogSummary = {
  exportId: string;
  engine: string;
  summary: Record<string, number>;
  latestLog: PluginImportLog | null;
  logs: PluginImportLog[];
};

export type PluginExportDownload = {
  contentType: string;
  exportId: string;
  manifest: {
    engine: string;
    checksum: string;
    entry: {
      type: string;
      path: string;
    };
    [key: string]: unknown;
  };
  files: Array<Record<string, unknown> & { path: string }>;
  checksum: string;
};

export type PluginExportArchive = {
  exportId: string;
  fileName: string;
  content: ArrayBuffer;
};

export type PluginToken = {
  id: string;
  name: string;
  engine: string;
  scopes: string[];
  status: string;
  token: string;
  createdAt: string;
};

export type McpTool = {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
};

export type McpInvocation = {
  id: string;
  tool: string;
  status: string;
  result: any;
};

export type EngineSnapshotIrResult = {
  snapshotId: string;
  ir: any;
};

type PluginProjectExportsDto = {
  exports: Array<{
    id: string;
    engine: string;
    engine_version: string;
    status: string;
    name: string;
    entry: {
      type: string;
      path: string;
    };
    manifest_url: string;
    download_url: string;
  }>;
};

type PluginImportLogDto = {
  id: string;
  export_id: string;
  engine: string;
  status: string;
  plugin_version: string;
  engine_version: string;
  duration_ms: number;
  summary: Record<string, number>;
  logs: Array<{
    level: string;
    message: string;
  }>;
};

type PluginImportLogSummaryDto = {
  export_id: string;
  engine: string;
  summary: Record<string, number>;
  latest_log: PluginImportLogDto | null;
  logs: PluginImportLogDto[];
};

type PluginExportDownloadDto = {
  content_type: string;
  export_id: string;
  manifest: PluginExportDownload["manifest"];
  files: PluginExportDownload["files"];
  checksum: string;
};

type PluginTokenDto = {
  id: string;
  name: string;
  engine: string;
  scopes: string[];
  status: string;
  token: string;
  created_at: string;
};

type McpToolDto = {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
};

type McpInvocationDto = {
  id: string;
  tool: string;
  status: string;
  result: any;
};

type EngineSnapshotIrResultDto = {
  snapshot_id: string;
  ir: any;
};

export async function createPluginToken(options: {
  name: string;
  engine: string;
  scopes: string[];
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginToken> {
  const dto = await pluginJsonRequest<PluginTokenDto>({
    path: "/api/plugin/tokens",
    token: options.token,
    fetcher: options.fetcher,
    init: {
      method: "POST",
      body: JSON.stringify({ name: options.name, engine: options.engine, scopes: options.scopes })
    }
  });
  return mapPluginToken(dto);
}

export async function revokePluginToken(options: {
  tokenId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<{ id: string; status: string }> {
  return pluginJsonRequest({
    path: `/api/plugin/tokens/${options.tokenId}`,
    token: options.token,
    fetcher: options.fetcher,
    init: { method: "DELETE" }
  });
}

export async function fetchMcpTools(options: {
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<McpTool[]> {
  const dto = await pluginJsonRequest<{ tools: McpToolDto[] }>({
    path: "/api/plugin/mcp/tools",
    token: options.token,
    fetcher: options.fetcher
  });
  return dto.tools.map(mapMcpTool);
}

export async function invokeMcpTool(options: {
  toolName: string;
  arguments: Record<string, unknown>;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<McpInvocation> {
  const dto = await pluginJsonRequest<McpInvocationDto>({
    path: `/api/plugin/mcp/tools/${options.toolName}/invoke`,
    token: options.token,
    fetcher: options.fetcher,
    init: {
      method: "POST",
      body: JSON.stringify({ arguments: options.arguments })
    }
  });
  return dto;
}

export async function buildEngineSnapshotIr(options: {
  snapshotId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<EngineSnapshotIrResult> {
  const dto = await pluginJsonRequest<EngineSnapshotIrResultDto>({
    path: `/api/plugin/engine-snapshots/${options.snapshotId}/build-ir`,
    token: options.token,
    fetcher: options.fetcher,
    init: { method: "POST" }
  });
  return { snapshotId: dto.snapshot_id, ir: dto.ir };
}

export async function fetchPluginProjectExports(options: {
  projectId: string;
  engine?: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginProjectExport[]> {
  const fetcher = options.fetcher ?? fetch;
  const query = options.engine && options.engine !== "all"
    ? `?engine=${encodeURIComponent(options.engine)}`
    : "";
  const response = await fetcher(
    `/api/plugin/projects/${options.projectId}/exports${query}`,
    {
      headers: {
        "Authorization": `Bearer ${options.token}`,
        "Content-Type": "application/json"
      }
    }
  );
  if (!response.ok) {
    throw new Error(`Plugin export query failed: ${options.engine}`);
  }
  const dto = await response.json() as PluginProjectExportsDto;
  return dto.exports.map((item) => ({
    id: item.id,
    engine: item.engine,
    engineVersion: item.engine_version,
    status: item.status,
    name: item.name,
    entry: item.entry,
    manifestUrl: item.manifest_url,
    downloadUrl: item.download_url
  }));
}

export async function fetchPluginImportLogs(options: {
  exportId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginImportLogSummary> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    `/api/plugin/exports/${options.exportId}/import-logs`,
    {
      headers: {
        "Authorization": `Bearer ${options.token}`,
        "Content-Type": "application/json"
      }
    }
  );
  if (!response.ok) {
    throw new Error(`Plugin import log query failed: ${options.exportId}`);
  }
  const dto = await response.json() as PluginImportLogSummaryDto;
  return {
    exportId: dto.export_id,
    engine: dto.engine,
    summary: dto.summary,
    latestLog: dto.latest_log ? mapPluginImportLog(dto.latest_log) : null,
    logs: dto.logs.map(mapPluginImportLog)
  };
}

export async function submitPluginImportLog(options: {
  exportId: string;
  engine: string;
  status: "succeeded" | "failed";
  pluginVersion: string;
  engineVersion: string;
  durationMs: number;
  summary: Record<string, number>;
  logs: Array<{ level: string; message: string }>;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginImportLog> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    "/api/plugin/import-logs",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${options.token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        export_id: options.exportId,
        engine: options.engine,
        status: options.status,
        plugin_version: options.pluginVersion,
        engine_version: options.engineVersion,
        duration_ms: options.durationMs,
        summary: options.summary,
        logs: options.logs
      })
    }
  );
  if (!response.ok) {
    throw new Error(`Plugin import log submit failed: ${options.exportId}`);
  }
  return mapPluginImportLog(await response.json() as PluginImportLogDto);
}

export async function fetchPluginExportDownload(options: {
  exportId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginExportDownload> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    `/api/plugin/exports/${options.exportId}/download`,
    {
      headers: {
        "Authorization": `Bearer ${options.token}`,
        "Content-Type": "application/json"
      }
    }
  );
  if (!response.ok) {
    throw new Error(`Plugin export download failed: ${options.exportId}`);
  }
  const dto = await response.json() as PluginExportDownloadDto;
  return {
    contentType: dto.content_type,
    exportId: dto.export_id,
    manifest: dto.manifest,
    files: dto.files,
    checksum: dto.checksum
  };
}

export async function fetchPluginExportArchive(options: {
  exportId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginExportArchive> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    `/api/plugin/exports/${options.exportId}/download`,
    {
      headers: {
        "Authorization": `Bearer ${options.token}`,
        "Accept": "application/zip"
      }
    }
  );
  if (!response.ok) {
    throw new Error(`Plugin export archive download failed: ${options.exportId}`);
  }
  const disposition = response.headers.get("content-disposition");
  return {
    exportId: options.exportId,
    fileName: parseAttachmentFileName(disposition) ?? `${options.exportId}.zip`,
    content: await response.arrayBuffer()
  };
}

function mapPluginImportLog(dto: PluginImportLogDto): PluginImportLog {
  return {
    id: dto.id,
    exportId: dto.export_id,
    engine: dto.engine,
    status: dto.status,
    pluginVersion: dto.plugin_version,
    engineVersion: dto.engine_version,
    durationMs: dto.duration_ms,
    summary: dto.summary,
    logs: dto.logs
  };
}

async function pluginJsonRequest<T>(options: {
  path: string;
  token: string;
  fetcher?: StudioApiFetcher;
  init?: RequestInit;
}): Promise<T> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    options.path,
    {
      ...options.init,
      headers: {
        "Authorization": `Bearer ${options.token}`,
        "Content-Type": "application/json",
        ...(options.init?.headers ?? {})
      }
    }
  );
  if (!response.ok) {
    throw new Error(`Plugin request failed: ${options.path}`);
  }
  return await response.json() as T;
}

function mapPluginToken(dto: PluginTokenDto): PluginToken {
  return {
    id: dto.id,
    name: dto.name,
    engine: dto.engine,
    scopes: dto.scopes,
    status: dto.status,
    token: dto.token,
    createdAt: dto.created_at
  };
}

function mapMcpTool(dto: McpToolDto): McpTool {
  return {
    name: dto.name,
    description: dto.description,
    inputSchema: dto.input_schema,
    outputSchema: dto.output_schema
  };
}

function parseAttachmentFileName(disposition: string | null): string | null {
  if (!disposition) return null;
  const match = disposition.match(/filename="([^"]+)"/);
  return match?.[1] ?? null;
}
