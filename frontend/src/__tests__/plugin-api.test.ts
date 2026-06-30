import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { fetchPluginProjectExports } from "../lib/plugin-api";

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
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
