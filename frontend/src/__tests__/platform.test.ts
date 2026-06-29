import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  aiPipelineServices,
  billingPlans,
  createDemoProject,
  creditBuckets,
  engineExportTargets,
  importSources,
  platformCapabilities,
  pluginConnectionSteps,
  productionWorkflow,
  studioActionDock,
  studioActiveSelection,
  studioAssets,
  studioExportWizardSteps,
  studioInspectorControls,
  studioLayerTree,
  studioSegmentationCorrections,
  studioTimeline,
  unityPluginFlow
} from "../lib/platform";

describe("platform model", () => {
  it("covers the complete replicated capability set", () => {
    const ids = platformCapabilities.map((item) => item.id);

    assert.deepEqual(
      [
        "official-site",
        "ai-studio",
        "professional-import",
        "text-to-image",
        "image-to-image",
        "inpainting",
        "matting",
        "upscale",
        "ui-slicing",
        "unity-export",
        "cocos-export",
        "godot-export",
        "unreal-roadmap",
        "engine-mcp",
        "developer-api",
        "billing"
      ].every((id) => ids.includes(id)),
      true
    );
  });

  it("creates a Unity-first demo project with AI, slicing and export tasks", () => {
    const project = createDemoProject("Cyberpunk RPG UI", "unity");

    assert.equal(project.targetEngine, "unity");
    assert.deepEqual(project.tasks.map((task) => task.kind), [
      "text_to_image",
      "ui_segmentation",
      "unity_export",
      "plugin_import"
    ]);
    assert.deepEqual(project.ir.engineTargets, ["unity", "cocos", "godot"]);
  });

  it("orders the production workflow from input to engine import", () => {
    assert.deepEqual(productionWorkflow.map((step) => step.title), [
      "Import or Generate",
      "Structure as Asset IR",
      "Slice and Edit UI",
      "Export Engine Package",
      "Import Through Plugin"
    ]);
  });

  it("models professional imports and developer AI services", () => {
    assert.deepEqual(importSources.map((source) => source.id), ["psd", "psb", "figma", "engine-snapshot"]);
    assert.deepEqual(aiPipelineServices.map((service) => service.id), [
      "text-to-image",
      "image-to-image",
      "inpainting",
      "super-matting",
      "upscale"
    ]);
    assert.equal(aiPipelineServices.find((service) => service.id === "super-matting")?.apiEnabled, true);
  });

  it("models Unity plugin export and restyle protocol checkpoints", () => {
    assert.deepEqual(unityPluginFlow.map((step) => step.id), [
      "manifest",
      "download",
      "import-log",
      "restyle-manifest"
    ]);
    assert.equal(unityPluginFlow[0]?.apiPath, "/api/plugin/exports/{export_id}/manifest");
    assert.deepEqual(unityPluginFlow[1]?.outputs, ["Unity ZIP", "checksum", "prefab entry"]);
    assert.deepEqual(unityPluginFlow[3]?.outputs, [
      "preserve RectTransform",
      "node path mapping",
      "replacement sprites"
    ]);
  });

  it("models native export plans for Unity, Cocos and Godot", () => {
    assert.deepEqual(engineExportTargets.map((target) => target.id), ["unity", "cocos3", "cocos2", "godot"]);
    assert.equal(engineExportTargets.find((target) => target.id === "cocos3")?.entry, "Cocos3 prefab");
    assert.equal(engineExportTargets.find((target) => target.id === "godot")?.engineVersion, "4.x");
    assert.deepEqual(engineExportTargets.find((target) => target.id === "cocos2")?.importSteps, [
      "copy_textures",
      "create_sprite_frames",
      "create_prefab",
      "write_import_log"
    ]);
  });

  it("models engine plugin connection steps", () => {
    assert.deepEqual(pluginConnectionSteps.map((step) => step.id), [
      "auth",
      "projects",
      "exports",
      "download"
    ]);
    assert.equal(pluginConnectionSteps[0]?.apiPath, "/api/plugin/auth");
    assert.equal(pluginConnectionSteps[2]?.apiPath, "/api/plugin/projects/{project_id}/exports?engine=unity");
  });

  it("models billing plans, credit buckets and API limits", () => {
    assert.deepEqual(billingPlans.map((plan) => plan.id), ["free", "base", "plus", "pro", "max"]);
    assert.equal(billingPlans.find((plan) => plan.id === "pro")?.apiEnabled, true);
    assert.equal(billingPlans.find((plan) => plan.id === "max")?.concurrentAiTasks, 20);
    assert.deepEqual(creditBuckets.map((bucket) => bucket.id), ["daily_free", "monthly", "purchased"]);
    assert.equal(creditBuckets[0]?.priority, 1);
  });

  it("models AI Studio assets, timeline, layers and inspector controls", () => {
    assert.deepEqual(studioAssets.map((asset) => asset.kind), ["generated", "slice", "layout", "prefab"]);
    assert.deepEqual(studioTimeline.map((task) => task.status), ["succeeded", "succeeded", "running", "queued"]);
    assert.equal(studioLayerTree[0]?.children?.[1]?.type, "button");
    assert.deepEqual(studioInspectorControls.map((control) => control.id), [
      "bounds",
      "anchor",
      "nine-slice",
      "binding"
    ]);
  });

  it("models actionable AI Studio correction and export state", () => {
    assert.deepEqual(studioActionDock.map((action) => action.id), [
      "regenerate",
      "open-slice-editor",
      "apply-correction",
      "export-package"
    ]);
    assert.equal(studioActiveSelection.selectedLayerId, "start_button");
    assert.equal(studioSegmentationCorrections[0]?.targetLayerId, "start_button");
    assert.deepEqual(studioExportWizardSteps.map((step) => step.status), [
      "complete",
      "active",
      "pending",
      "pending"
    ]);
  });
});
