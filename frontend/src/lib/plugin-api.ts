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
