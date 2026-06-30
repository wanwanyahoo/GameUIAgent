import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  applyStudioCorrection,
  createStudioAiJob,
  createStudioAsset,
  createStudioSegmentation,
  fetchStudioState,
  listStudioAssets,
  previewStudioExportWizard
} from "../lib/studio-api";

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
        count: 2
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
      count: 2
    }));
    assert.equal(asset.metadata.width, 1920);
    assert.equal(assets[0]?.id, "ast_upload");
    assert.equal(job.inputAsset?.id, "ast_upload");
    assert.equal(job.estimatedCredits, 4);
    assert.equal(segmentation.irId, "ir_1");
    assert.equal(segmentation.slices[0]?.editableBounds, true);
  });
});

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
