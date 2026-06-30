import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { createStudioController, type StudioControllerPluginExport } from "../lib/studio-controller";

describe("studio controller", () => {
  it("loads studio state and publishes action status transitions", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const controller = createStudioController({
      projectId: "prj_1",
      token: "tok_1",
      fetcher: async (url, init) => {
        calls.push({ url, init });
        if (url.endsWith("/corrections/correction_button_bounds/apply")) {
          return jsonResponse({ status: "applied" });
        }
        if (url.endsWith("/export-wizard")) {
          return jsonResponse({ export_preview: { target_engine: "cocos3" } });
        }
        if (url.endsWith("/exports?engine=cocos3")) {
          return jsonResponse({ exports: [] });
        }
        return jsonResponse(studioStateDto(calls.length > 3 ? "cocos3" : "unity"));
      }
    });
    const phases: string[] = [];
    const actions: string[] = [];
    controller.subscribe((state) => {
      phases.push(state.phase);
      if (state.activeAction) {
        actions.push(state.activeAction);
      }
    });

    assert.equal(controller.getState().phase, "idle");

    await controller.load();
    await controller.applyCorrection("correction_button_bounds");
    await controller.previewExport("cocos3");

    assert.deepEqual(phases, [
      "loading",
      "ready",
      "ready",
      "ready",
      "ready",
      "ready"
    ]);
    assert.deepEqual(actions, ["apply-correction", "export-package"]);
    assert.deepEqual(calls.map((call) => call.url), [
      "/api/projects/prj_1/studio",
      "/api/projects/prj_1/studio/corrections/correction_button_bounds/apply",
      "/api/projects/prj_1/studio",
      "/api/projects/prj_1/studio/export-wizard",
      "/api/projects/prj_1/studio",
      "/api/plugin/projects/prj_1/exports?engine=cocos3"
    ]);
    assert.equal(controller.getState().studio?.exportWizard.targetEngine, "cocos3");
  });

  it("refreshes Unreal plugin exports after export wizard preview", async () => {
    const pluginExports: StudioControllerPluginExport[][] = [];
    const controller = createStudioController({
      projectId: "prj_unreal",
      token: "tok_1",
      fetcher: async (url) => {
        if (url.endsWith("/export-wizard")) {
          return jsonResponse({ export_preview: { target_engine: "unreal" } });
        }
        if (url.endsWith("/exports?engine=unreal")) {
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
        }
        return jsonResponse(studioStateDto("unreal"));
      }
    });
    controller.subscribe((state) => {
      if (state.pluginExports) {
        pluginExports.push(state.pluginExports);
      }
    });

    await controller.load();
    await controller.previewExport("unreal");

    assert.equal(controller.getState().pluginExports?.[0]?.engine, "unreal");
    assert.equal(controller.getState().pluginExports?.[0]?.entry.type, "umg_widget_blueprint");
    assert.equal(pluginExports.at(-1)?.[0]?.engineVersion, "5.3+");
  });
});

function studioStateDto(targetEngine: string) {
  return {
    project_id: "prj_1",
    active_selection: {
      selected_layer_id: "button_primary",
      selected_asset_id: "asset_slice",
      active_task_id: "timeline_slice"
    },
    timeline: [
      { kind: "text_to_image", status: "succeeded", progress: 100 },
      { kind: "ui_segmentation", status: "succeeded", progress: 100 },
      { kind: `${targetEngine}_export`, status: "queued", progress: 0 }
    ],
    action_dock: [{ id: "apply-correction", title: "Apply Correction", shortcut: "A" }],
    segmentation_corrections: [
      {
        id: "correction_button_bounds",
        target_layer_id: "button_primary",
        title: "Primary CTA bounds",
        change: "Resize hit box to match nine-slice button art.",
        confidence: 0.92,
        status: "pending"
      }
    ],
    export_wizard: {
      target_engine: targetEngine,
      steps: [{ id: "validate-ir", title: "Validate Asset IR", status: "active" }]
    }
  };
}

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
