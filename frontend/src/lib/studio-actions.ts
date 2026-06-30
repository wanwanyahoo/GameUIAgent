import { createStudioAiJob, createStudioSegmentation, applyStudioCorrection, previewStudioExportWizard } from "./studio-api";
import type { Project, StudioState } from "./projects-api";

export type StudioActionId = "regenerate" | "open-slice-editor" | "apply-correction" | "export-package";

export type StudioActionClients = {
  createAiJob: (options: Parameters<typeof createStudioAiJob>[0]) => Promise<unknown>;
  createSegmentation: (options: Parameters<typeof createStudioSegmentation>[0]) => Promise<unknown>;
  applyCorrection: (options: Parameters<typeof applyStudioCorrection>[0]) => Promise<unknown>;
  previewExport: (options: Parameters<typeof previewStudioExportWizard>[0]) => Promise<unknown>;
};

export type RunStudioActionOptions = {
  actionId: string;
  token: string;
  project: Project;
  studio: StudioState;
  clients?: Partial<StudioActionClients>;
};

export type RunStudioActionResult = {
  status: "ok";
  message: string;
  result: unknown;
};

export type GeneratedAssetActionId = "slice-generated-asset" | "export-generated-asset";

export type RunGeneratedAssetActionOptions = {
  actionId: string;
  assetId: string;
  token: string;
  project: Project;
  studio: StudioState;
  clients?: Partial<Pick<StudioActionClients, "createSegmentation" | "previewExport">>;
};

const defaultClients: StudioActionClients = {
  createAiJob: createStudioAiJob,
  createSegmentation: createStudioSegmentation,
  applyCorrection: applyStudioCorrection,
  previewExport: previewStudioExportWizard,
};

export async function runStudioAction(options: RunStudioActionOptions): Promise<RunStudioActionResult> {
  const clients = { ...defaultClients, ...options.clients };
  const projectId = options.project.id;

  if (options.actionId === "regenerate") {
    const result = await clients.createAiJob({
      projectId,
      token: options.token,
      job: {
        kind: "text_to_image",
        prompt: `Regenerate production-ready game UI for ${options.project.name}`,
        referenceAssetId: options.studio.active_selection.selected_asset_id,
        count: 1,
        executionMode: "queued",
      },
    });
    return { status: "ok", message: "AI regeneration job created", result };
  }

  if (options.actionId === "open-slice-editor") {
    const assetId = options.studio.active_selection.selected_asset_id;
    if (!assetId) {
      throw new Error("No selected asset is available for slicing");
    }
    const result = await clients.createSegmentation({
      projectId,
      token: options.token,
      assetId,
    });
    return { status: "ok", message: "Layered slice request created", result };
  }

  if (options.actionId === "apply-correction") {
    const correction = options.studio.segmentation_corrections.find((item) => item.status === "pending")
      || options.studio.segmentation_corrections[0];
    if (!correction) {
      throw new Error("No segmentation correction is available");
    }
    const result = await clients.applyCorrection({
      projectId,
      token: options.token,
      correctionId: correction.id,
    });
    return { status: "ok", message: "Segmentation correction applied", result };
  }

  if (options.actionId === "export-package") {
    const result = await clients.previewExport({
      projectId,
      token: options.token,
      targetEngine: options.studio.export_wizard.target_engine || options.project.target_engine,
    });
    return { status: "ok", message: "Engine export package generated", result };
  }

  throw new Error(`Unsupported Studio action: ${options.actionId}`);
}

export async function runGeneratedAssetAction(options: RunGeneratedAssetActionOptions): Promise<RunStudioActionResult> {
  const clients = { ...defaultClients, ...options.clients };
  const projectId = options.project.id;

  if (!options.assetId) {
    throw new Error("No generated asset is available for this action");
  }

  if (options.actionId === "slice-generated-asset") {
    const result = await clients.createSegmentation({
      projectId,
      token: options.token,
      assetId: options.assetId,
    });
    return { status: "ok", message: "Generated asset sent to layered slice", result };
  }

  if (options.actionId === "export-generated-asset") {
    await clients.createSegmentation({
      projectId,
      token: options.token,
      assetId: options.assetId,
    });
    const result = await clients.previewExport({
      projectId,
      token: options.token,
      targetEngine: options.studio.export_wizard.target_engine || options.project.target_engine,
    });
    return { status: "ok", message: "Generated asset sliced and export package generated", result };
  }

  throw new Error(`Unsupported generated asset action: ${options.actionId}`);
}
