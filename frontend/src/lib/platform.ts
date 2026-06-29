export type EngineTarget = "unity" | "cocos" | "godot" | "unreal";

export type Capability = {
  id: string;
  title: string;
  summary: string;
  group: "website" | "studio" | "ai" | "engine" | "platform";
};

export type WorkflowStep = {
  title: string;
  detail: string;
};

export type ImportSource = {
  id: "psd" | "psb" | "figma" | "engine-snapshot";
  title: string;
  detail: string;
};

export type AiPipelineService = {
  id: "text-to-image" | "image-to-image" | "inpainting" | "super-matting" | "upscale";
  title: string;
  apiEnabled: boolean;
  controls: string[];
};

export type DemoTask = {
  kind: "text_to_image" | "ui_segmentation" | "unity_export" | "plugin_import";
  status: "ready" | "running" | "succeeded";
};

export type DemoProject = {
  name: string;
  targetEngine: EngineTarget;
  tasks: DemoTask[];
  ir: {
    engineTargets: EngineTarget[];
    nodes: Array<{ id: string; type: string; name: string }>;
  };
};

export const platformCapabilities: Capability[] = [
  {
    id: "official-site",
    title: "Official Site",
    summary: "VberAI-style marketing portal, product routes, pricing and conversion CTAs.",
    group: "website"
  },
  {
    id: "ai-studio",
    title: "AI Studio",
    summary: "Project canvas, asset library, layer tree, generation panel and task timeline.",
    group: "studio"
  },
  {
    id: "professional-import",
    title: "PSD / PSB / Figma",
    summary: "Preserve professional layers before converting designs into engine-ready IR.",
    group: "studio"
  },
  {
    id: "text-to-image",
    title: "Text to Image",
    summary: "Prompt-based generation for game UI, icons, panels, characters and scenes.",
    group: "ai"
  },
  {
    id: "image-to-image",
    title: "Image to Image",
    summary: "Reference-driven variations with style and strength controls.",
    group: "ai"
  },
  {
    id: "inpainting",
    title: "Inpainting",
    summary: "Mask-based local redraw for selected UI or art regions.",
    group: "ai"
  },
  {
    id: "matting",
    title: "Super Matting",
    summary: "Transparent PNG extraction for characters, props and UI elements.",
    group: "ai"
  },
  {
    id: "upscale",
    title: "Upscale",
    summary: "Resolution enhancement for production-ready game assets.",
    group: "ai"
  },
  {
    id: "ui-slicing",
    title: "UI Slicing",
    summary: "Detect panels, buttons, icons, text and nine-slice regions into editable layers.",
    group: "studio"
  },
  {
    id: "unity-export",
    title: "Unity-first Export",
    summary: "Generate sprites, atlases, prefabs, scenes and replacement manifests.",
    group: "engine"
  },
  {
    id: "cocos-export",
    title: "Cocos Export",
    summary: "Emit Cocos Creator 2.x/3.x prefab and scene packages from the same IR.",
    group: "engine"
  },
  {
    id: "godot-export",
    title: "Godot Export",
    summary: "Build Godot 4 Control scenes and texture import instructions.",
    group: "engine"
  },
  {
    id: "unreal-roadmap",
    title: "Unreal UMG Roadmap",
    summary: "Extend the asset pipeline to UMG, Widget Blueprint, Slate and asset imports.",
    group: "engine"
  },
  {
    id: "engine-mcp",
    title: "Engine MCP",
    summary: "Connect Unity, Cocos, Godot and Unreal editors to cloud production tasks.",
    group: "engine"
  },
  {
    id: "developer-api",
    title: "Developer API",
    summary: "API keys, polling, webhooks, cancellation, cost estimates and rate limits.",
    group: "platform"
  },
  {
    id: "billing",
    title: "Credits and Billing",
    summary: "Free, subscription and purchased credits with concurrent task quotas.",
    group: "platform"
  }
];

export const productionWorkflow: WorkflowStep[] = [
  {
    title: "Import or Generate",
    detail: "Start from prompt, image, PSD, PSB, Figma or an existing engine prefab."
  },
  {
    title: "Structure as Asset IR",
    detail: "Normalize layers, layout, transforms, visual state and engine export metadata."
  },
  {
    title: "Slice and Edit UI",
    detail: "Auto-detect UI elements, then manually correct names, boxes and states."
  },
  {
    title: "Export Engine Package",
    detail: "Produce Unity-first packages while keeping Cocos and Godot targets available."
  },
  {
    title: "Import Through Plugin",
    detail: "Use editor plugins to create scenes, prefabs and replacement manifests."
  }
];

export const importSources: ImportSource[] = [
  {
    id: "psd",
    title: "PSD layers",
    detail: "Layer groups, image layers, text layers, visibility, opacity and coordinates."
  },
  {
    id: "psb",
    title: "PSB large files",
    detail: "Large Photoshop documents keep the same Design Layer Document pipeline."
  },
  {
    id: "figma",
    title: "Figma frames",
    detail: "Frames, components, instances, constraints, Auto Layout and image fills."
  },
  {
    id: "engine-snapshot",
    title: "Engine snapshots",
    detail: "Unity prefabs and scenes can return to AI Studio as editable layout IR."
  }
];

export const aiPipelineServices: AiPipelineService[] = [
  {
    id: "text-to-image",
    title: "Text to Image",
    apiEnabled: false,
    controls: ["prompt", "style", "seed", "size"]
  },
  {
    id: "image-to-image",
    title: "Image to Image",
    apiEnabled: false,
    controls: ["reference", "strength", "style"]
  },
  {
    id: "inpainting",
    title: "Inpainting",
    apiEnabled: false,
    controls: ["mask", "prompt", "denoise"]
  },
  {
    id: "super-matting",
    title: "Super Matting",
    apiEnabled: true,
    controls: ["Cost", "Execute", "Poll", "Cancel", "Webhook"]
  },
  {
    id: "upscale",
    title: "Upscale",
    apiEnabled: false,
    controls: ["scale", "quality", "artifact removal"]
  }
];

export function createDemoProject(name: string, targetEngine: EngineTarget): DemoProject {
  return {
    name,
    targetEngine,
    tasks: [
      { kind: "text_to_image", status: "succeeded" },
      { kind: "ui_segmentation", status: "succeeded" },
      { kind: "unity_export", status: targetEngine === "unity" ? "succeeded" : "ready" },
      { kind: "plugin_import", status: "ready" }
    ],
    ir: {
      engineTargets: ["unity", "cocos", "godot"],
      nodes: [
        { id: "root", type: "canvas", name: name },
        { id: "panel_main", type: "panel", name: "Main Panel" },
        { id: "button_primary", type: "button", name: "Primary CTA" },
        { id: "icon_item", type: "icon", name: "Inventory Icon" },
        { id: "title_text", type: "text", name: "Screen Title" }
      ]
    }
  };
}
