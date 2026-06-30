import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  applyStudioCorrection,
  createStudioAiJob,
  createStudioAsset,
  createStudioSegmentation,
  copyStudioAsset,
  deleteStudioAsset,
  fetchStudioState,
  listStudioAssetVersions,
  listStudioAssets,
  previewStudioExportWizard,
  updateStudioAsset
} from "../lib/studio-api";
import { runStudioAction } from "../lib/studio-actions";

describe("studio API client", () => {
  it("maps backend studio state into frontend camelCase models", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({
        project_id: "prj_1",
        active_selection: {
          selected_layer_id: "button_primary",
          selected_asset_id: "asset_slice",
          active_task_id: "timeline_slice"
        },
        timeline: [
          { kind: "text_to_image", status: "succeeded", progress: 100 },
          { kind: "ui_segmentation", status: "succeeded", progress: 100 },
          { kind: "godot_export", status: "queued", progress: 0 },
          {
            kind: "plugin_import",
            status: "failed",
            progress: 100,
            summary: { warnings: 1, errors: 2 }
          }
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
          target_engine: "godot",
          steps: [{ id: "validate-ir", title: "Validate Asset IR", status: "active" }]
        }
      });
    };

    const studio = await fetchStudioState({
      projectId: "prj_1",
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/projects/prj_1/studio");
    assert.equal(calls[0]?.init?.headers?.["Authorization" as keyof HeadersInit], "Bearer tok_1");
    assert.equal(studio.projectId, "prj_1");
    assert.equal(studio.activeSelection.selectedLayerId, "button_primary");
    assert.deepEqual(studio.timeline.map((task) => task.kind), [
      "text_to_image",
      "ui_segmentation",
      "godot_export",
      "plugin_import"
    ]);
    assert.equal(studio.segmentationCorrections[0]?.targetLayerId, "button_primary");
    assert.equal(studio.exportWizard.targetEngine, "godot");
    assert.equal(studio.timeline[3]?.status, "failed");
    assert.equal(studio.timeline[3]?.summary?.errors, 2);
  });

  it("posts correction and export wizard actions to backend Studio routes", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return jsonResponse({ status: "ok" });
    };

    await applyStudioCorrection({
      projectId: "prj_1",
      correctionId: "correction_button_bounds",
      token: "tok_1",
      fetcher
    });
    await previewStudioExportWizard({
      projectId: "prj_1",
      targetEngine: "cocos3",
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/projects/prj_1/studio/corrections/correction_button_bounds/apply");
    assert.equal(calls[0]?.init?.method, "POST");
    assert.equal(calls[1]?.url, "/api/projects/prj_1/studio/export-wizard");
    assert.equal(calls[1]?.init?.method, "POST");
    assert.equal(calls[1]?.init?.body, JSON.stringify({ target_engine: "cocos3" }));
  });

  it("creates uploaded assets, AI jobs and segmentation requests", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.endsWith("/assets") && init?.method === "POST") {
        return jsonResponse({
          id: "ast_upload",
          project_id: "prj_1",
          type: "reference_image",
          name: "main-menu.png",
          url: "https://assets/main-menu.png",
          source: "upload",
          metadata: { width: 1920, height: 1080, usage: "image_to_image" }
        });
      }
      if (url.endsWith("/assets")) {
        return jsonResponse({
          assets: [
            {
              id: "ast_upload",
              project_id: "prj_1",
              type: "reference_image",
              name: "main-menu.png",
              url: "https://assets/main-menu.png",
              source: "upload",
              metadata: { width: 1920, height: 1080, usage: "image_to_image" }
            }
          ]
        });
      }
      if (url.endsWith("/ai/jobs")) {
        return jsonResponse({
          id: "job_1",
          project_id: "prj_1",
          kind: "image_to_image",
          prompt: "restyle uploaded HUD",
          input_asset: { id: "ast_upload" },
          result_asset: { id: "ast_generated" },
          candidates: [{ asset_id: "ast_generated" }],
          estimated_credits: 4
        });
      }
      return jsonResponse({
        id: "seg_1",
        project_id: "prj_1",
        source_asset_id: "ast_upload",
        ir_id: "ir_1",
        confidence: 0.88,
        slices: [{ id: "slice_button", type: "button", editable_bounds: true }]
      });
    };

    const asset = await createStudioAsset({
      projectId: "prj_1",
      token: "tok_1",
      fetcher,
      asset: {
        name: "main-menu.png",
        type: "reference_image",
        url: "https://assets/main-menu.png",
        width: 1920,
        height: 1080,
        usage: "image_to_image"
      }
    });
    const assets = await listStudioAssets({ projectId: "prj_1", token: "tok_1", fetcher });
    const job = await createStudioAiJob({
      projectId: "prj_1",
      token: "tok_1",
      fetcher,
      job: {
        kind: "image_to_image",
        prompt: "restyle uploaded HUD",
        inputAssetId: asset.id,
        negativePrompt: "blur",
        seed: 7,
        model: "game-ui-xl",
        count: 2,
        executionMode: "queued"
      }
    });
    const segmentation = await createStudioSegmentation({
      projectId: "prj_1",
      token: "tok_1",
      fetcher,
      assetId: asset.id
    });

    assert.equal(calls[0]?.url, "/api/projects/prj_1/assets");
    assert.equal(calls[0]?.init?.method, "POST");
    assert.equal(calls[2]?.init?.body, JSON.stringify({
      kind: "image_to_image",
      prompt: "restyle uploaded HUD",
      input_asset_id: "ast_upload",
      negative_prompt: "blur",
      seed: 7,
      model: "game-ui-xl",
      count: 2,
      execution_mode: "queued"
    }));
    assert.equal(asset.metadata.width, 1920);
    assert.equal(assets[0]?.id, "ast_upload");
    assert.equal(job.inputAsset?.id, "ast_upload");
    assert.equal(job.estimatedCredits, 4);
    assert.equal(segmentation.irId, "ir_1");
    assert.equal(segmentation.slices[0]?.editableBounds, true);
  });

  it("manages uploaded asset library operations", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetcher = async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.includes("/versions")) {
        return jsonResponse({
          versions: [
            { id: "ver_1", event: "created", name: "shop-panel.png" },
            { id: "ver_2", event: "updated", name: "shop-panel-v2.png" }
          ]
        });
      }
      if (url.endsWith("/copy")) {
        return jsonResponse(assetDto({ id: "ast_copy", name: "shop-panel-v2.png Copy" }));
      }
      if (init?.method === "PATCH") {
        return jsonResponse(assetDto({ name: "shop-panel-v2.png", tags: ["shop", "approved"] }));
      }
      if (init?.method === "DELETE") {
        return jsonResponse({ status: "deleted" });
      }
      return jsonResponse({ assets: [assetDto({})] });
    };

    const assets = await listStudioAssets({
      projectId: "prj_1",
      token: "tok_1",
      fetcher,
      search: "shop",
      tag: "panel"
    });
    const updated = await updateStudioAsset({
      projectId: "prj_1",
      assetId: "ast_upload",
      token: "tok_1",
      fetcher,
      patch: { name: "shop-panel-v2.png", tags: ["shop", "approved"] }
    });
    const versions = await listStudioAssetVersions({
      projectId: "prj_1",
      assetId: "ast_upload",
      token: "tok_1",
      fetcher
    });
    const copied = await copyStudioAsset({
      projectId: "prj_1",
      assetId: "ast_upload",
      token: "tok_1",
      fetcher
    });
    const deleted = await deleteStudioAsset({
      projectId: "prj_1",
      assetId: "ast_upload",
      token: "tok_1",
      fetcher
    });

    assert.equal(calls[0]?.url, "/api/projects/prj_1/assets?search=shop&tag=panel");
    assert.equal(calls[1]?.init?.method, "PATCH");
    assert.equal(calls[1]?.init?.body, JSON.stringify({ name: "shop-panel-v2.png", tags: ["shop", "approved"] }));
    assert.equal(calls[2]?.url, "/api/projects/prj_1/assets/ast_upload/versions");
    assert.equal(calls[3]?.init?.method, "POST");
    assert.equal(calls[4]?.init?.method, "DELETE");
    assert.equal(assets[0]?.id, "ast_upload");
    assert.equal(updated.name, "shop-panel-v2.png");
    assert.equal(versions[1]?.event, "updated");
    assert.equal(copied.id, "ast_copy");
    assert.equal(deleted.status, "deleted");
  });

  it("runs Studio action dock commands against real API operations", async () => {
    const calls: string[] = [];
    const studio = {
      project_id: "prj_1",
      active_selection: {
        selected_layer_id: "button_primary",
        selected_asset_id: "ast_generated",
        active_task_id: "timeline_slice",
      },
      action_dock: [],
      timeline: [],
      segmentation_corrections: [
        {
          id: "correction_button_bounds",
          target_layer_id: "button_primary",
          title: "Primary CTA bounds",
          change: "Resize hit box",
          confidence: 0.92,
          status: "pending",
        },
      ],
      export_wizard: {
        target_engine: "unity",
        steps: [],
      },
    };
    const project = {
      id: "prj_1",
      name: "Battle HUD",
      target_engine: "unity",
      canvas: { width: 1920, height: 1080 },
      status: "active",
      owner_id: "usr_1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };
    const clients = {
      createAiJob: async () => {
        calls.push("ai");
        return { id: "job_1" };
      },
      createSegmentation: async () => {
        calls.push("segment");
        return { id: "seg_1" };
      },
      applyCorrection: async () => {
        calls.push("correction");
        return { status: "applied" };
      },
      previewExport: async () => {
        calls.push("export");
        return { export: { id: "exp_1" } };
      },
    };

    await runStudioAction({ actionId: "regenerate", token: "tok_1", project, studio, clients });
    await runStudioAction({ actionId: "open-slice-editor", token: "tok_1", project, studio, clients });
    await runStudioAction({ actionId: "apply-correction", token: "tok_1", project, studio, clients });
    await runStudioAction({ actionId: "export-package", token: "tok_1", project, studio, clients });

    assert.deepEqual(calls, ["ai", "segment", "correction", "export"]);
  });
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}

function assetDto(overrides: Partial<{
  id: string;
  name: string;
  tags: string[];
}>) {
  return {
    id: overrides.id ?? "ast_upload",
    project_id: "prj_1",
    type: "original_upload",
    name: overrides.name ?? "shop-panel.png",
    url: "https://assets/shop-panel.png",
    source: "upload",
    metadata: { width: 1024, height: 512, usage: "source_ui", tags: overrides.tags ?? ["shop", "panel"] }
  };
}
