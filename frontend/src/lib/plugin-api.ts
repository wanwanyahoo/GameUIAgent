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

export async function fetchPluginProjectExports(options: {
  projectId: string;
  engine: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): Promise<PluginProjectExport[]> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(
    `/api/plugin/projects/${options.projectId}/exports?engine=${encodeURIComponent(options.engine)}`,
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
