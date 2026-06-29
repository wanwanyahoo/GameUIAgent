import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  aiPipelineServices,
  createDemoProject,
  engineExportTargets,
  importSources,
  platformCapabilities,
  pluginConnectionSteps,
  productionWorkflow,
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
});
