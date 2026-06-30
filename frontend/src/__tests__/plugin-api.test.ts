import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { fetchPluginExportArchive, fetchPluginExportDownload, fetchPluginImportLogs, fetchPluginProjectExports, submitPluginImportLog } from "../lib/plugin-api";

describe("plugin API client", () => {
  it("queries Unreal plugin exports with engine metadata", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({
        exports: [
          {
            id: "exp_unreal",
            engine: "unreal",
            engine_version: "5.3+",
            status: "ready",
            name: "Unreal Wizard HUD unreal",
            entry: {
              type: "umg_widget_blueprint",
              path: "Unreal/Content/GameUIAgent/Widgets/WBP_UnrealWizardHud.uasset"
            },
            manifest_url: "/api/plugin/exports/exp_unreal/manifest",
            download_url: "/api/plugin/exports/exp_unreal/download"
          }
        ]
      });
    };

    const exports = await fetchPluginProjectExports({
      projectId: "prj_1",
      engine: "unreal",
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/plugin/projects/prj_1/exports?engine=unreal");
    assert.equal(calls[0]?.init?.headers?.["Authorization" as keyof HeadersInit], "Bearer tok_1");
    assert.equal(exports[0]?.engineVersion, "5.3+");
    assert.equal(exports[0]?.entry.type, "umg_widget_blueprint");
    assert.match(exports[0]?.entry.path ?? "", /WBP_UnrealWizardHud/);
  });

  it("queries Unreal plugin import log summaries", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({
        export_id: "exp_unreal",
        engine: "unreal",
        summary: {
          textures_created: 4,
          umg_widgets_created: 1,
          slate_slots_bound: 7,
          warnings: 1,
          errors: 0
        },
        latest_log: {
          id: "ilog_1",
          export_id: "exp_unreal",
          engine: "unreal",
          status: "succeeded",
          plugin_version: "0.2.0",
          engine_version: "5.3+",
          duration_ms: 5200,
          summary: {
            textures_created: 4,
            umg_widgets_created: 1,
            slate_slots_bound: 7,
            warnings: 1,
            errors: 0
          },
          logs: [{ level: "warning", message: "Texture compression preset was normalized" }]
        },
        logs: []
      });
    };

    const importLogs = await fetchPluginImportLogs({
      exportId: "exp_unreal",
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/plugin/exports/exp_unreal/import-logs");
    assert.equal(calls[0]?.init?.headers?.["Authorization" as keyof HeadersInit], "Bearer tok_1");
    assert.equal(importLogs.engine, "unreal");
    assert.equal(importLogs.summary.umg_widgets_created, 1);
    assert.equal(importLogs.latestLog?.engineVersion, "5.3+");
    assert.equal(importLogs.latestLog?.logs[0]?.level, "warning");
  });

  it("submits Unity plugin import logs back to the platform", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({
        id: "ilog_1",
        export_id: "exp_unity",
        engine: "unity",
        status: "succeeded",
        plugin_version: "0.4.0",
        engine_version: "2022.3.40f1",
        duration_ms: 3900,
        summary: { assets_imported: 4, prefabs_created: 1, scenes_created: 1, warnings: 0, errors: 0 },
        logs: [{ level: "info", message: "Imported Unity prefab" }]
      });
    };

    const log = await submitPluginImportLog({
      exportId: "exp_unity",
      engine: "unity",
      status: "succeeded",
      pluginVersion: "0.4.0",
      engineVersion: "2022.3.40f1",
      durationMs: 3900,
      summary: { assets_imported: 4, prefabs_created: 1, scenes_created: 1, warnings: 0, errors: 0 },
      logs: [{ level: "info", message: "Imported Unity prefab" }],
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/plugin/import-logs");
    assert.equal(calls[0]?.init?.method, "POST");
    assert.equal(calls[0]?.init?.body, JSON.stringify({
      export_id: "exp_unity",
      engine: "unity",
      status: "succeeded",
      plugin_version: "0.4.0",
      engine_version: "2022.3.40f1",
      duration_ms: 3900,
      summary: { assets_imported: 4, prefabs_created: 1, scenes_created: 1, warnings: 0, errors: 0 },
      logs: [{ level: "info", message: "Imported Unity prefab" }]
    }));
    assert.equal(log.exportId, "exp_unity");
    assert.equal(log.summary.prefabs_created, 1);
  });

  it("downloads plugin export packages with manifest and files", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({
        content_type: "application/zip",
        export_id: "exp_unreal",
        manifest: {
          engine: "unreal",
          checksum: "sha256:abc",
          entry: { type: "umg_widget_blueprint", path: "Widgets/WBP_HUD.uasset" }
        },
        files: [{ path: "manifest.json", content: "{}" }],
        checksum: "sha256:abc"
      });
    };

    const download = await fetchPluginExportDownload({
      exportId: "exp_unreal",
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/plugin/exports/exp_unreal/download");
    assert.equal(calls[0]?.init?.headers?.["Authorization" as keyof HeadersInit], "Bearer tok_1");
    assert.equal(download.exportId, "exp_unreal");
    assert.equal(download.contentType, "application/zip");
    assert.equal(download.manifest.engine, "unreal");
    assert.equal(download.files[0]?.path, "manifest.json");
  });

  it("downloads plugin export archives as binary zip payloads", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const zip = new Uint8Array([80, 75, 3, 4]).buffer;
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return {
        ok: true,
        headers: {
          get: (name: string) => name.toLowerCase() === "content-disposition"
            ? 'attachment; filename="exp_unreal.zip"'
            : null,
        },
        arrayBuffer: async () => zip,
      } as Response;
    };

    const archive = await fetchPluginExportArchive({
      exportId: "exp_unreal",
      token: "tok_1",
      fetcher
    });

    const headers = calls[0]?.init?.headers as Record<string, string>;
    assert.equal(calls[0]?.url, "/api/plugin/exports/exp_unreal/download");
    assert.equal(headers.Authorization, "Bearer tok_1");
    assert.equal(headers.Accept, "application/zip");
    assert.equal(archive.exportId, "exp_unreal");
    assert.equal(archive.fileName, "exp_unreal.zip");
    assert.equal(new Uint8Array(archive.content)[0], 80);
  });
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
