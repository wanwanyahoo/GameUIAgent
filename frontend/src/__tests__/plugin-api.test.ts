import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { fetchPluginImportLogs, fetchPluginProjectExports } from "../lib/plugin-api";

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
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
