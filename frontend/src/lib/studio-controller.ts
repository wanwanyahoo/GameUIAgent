import {
  applyStudioCorrection,
  fetchStudioState,
  previewStudioExportWizard,
  type StudioApiFetcher,
  type StudioApiState
} from "./studio-api";
import { fetchPluginProjectExports, type PluginProjectExport } from "./plugin-api";

export type StudioControllerAction = "apply-correction" | "export-package";
export type StudioControllerPluginExport = PluginProjectExport;

export type StudioControllerState = {
  phase: "idle" | "loading" | "ready" | "error";
  activeAction?: StudioControllerAction;
  error?: string;
  studio?: StudioApiState;
  pluginExports?: StudioControllerPluginExport[];
};

export type StudioController = {
  getState: () => StudioControllerState;
  subscribe: (listener: StudioControllerListener) => () => void;
  load: () => Promise<void>;
  applyCorrection: (correctionId: string) => Promise<void>;
  previewExport: (targetEngine: string) => Promise<void>;
};

type StudioControllerListener = (state: StudioControllerState) => void;

export function createStudioController(options: {
  projectId: string;
  token: string;
  fetcher?: StudioApiFetcher;
}): StudioController {
  let state: StudioControllerState = { phase: "idle" };
  const listeners = new Set<StudioControllerListener>();

  const publish = (nextState: StudioControllerState) => {
    state = nextState;
    listeners.forEach((listener) => listener(state));
  };

  const loadStudio = async (phase: "loading" | "ready") => {
    if (phase === "loading") {
      publish({ phase: "loading", studio: state.studio, pluginExports: state.pluginExports });
    }
    const studio = await fetchStudioState(options);
    return studio;
  };

  const run = async (work: () => Promise<StudioControllerState>) => {
    try {
      publish(await work());
    } catch (error) {
      publish({
        phase: "error",
        error: error instanceof Error ? error.message : "Studio action failed",
        studio: state.studio,
        pluginExports: state.pluginExports
      });
    }
  };

  return {
    getState: () => state,
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    load: () => run(async () => ({ phase: "ready", studio: await loadStudio("loading") })),
    applyCorrection: async (correctionId) => {
      publish({ ...state, phase: "ready", activeAction: "apply-correction" });
      await run(async () => {
        await applyStudioCorrection({ ...options, correctionId });
        return { phase: "ready", studio: await loadStudio("ready"), pluginExports: state.pluginExports };
      });
    },
    previewExport: async (targetEngine) => {
      publish({ ...state, phase: "ready", activeAction: "export-package" });
      await run(async () => {
        await previewStudioExportWizard({ ...options, targetEngine });
        const studio = await loadStudio("ready");
        const pluginExports = await fetchPluginProjectExports({
          ...options,
          engine: targetEngine
        });
        return { phase: "ready", studio, pluginExports };
      });
    }
  };
}
