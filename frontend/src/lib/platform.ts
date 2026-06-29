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

export type UnityPluginStep = {
  id: "manifest" | "download" | "import-log" | "restyle-manifest";
  title: string;
  apiPath: string;
  detail: string;
  outputs: string[];
};

export type EngineExportTarget = {
  id: "unity" | "cocos3" | "cocos2" | "godot";
  title: string;
  engineVersion: string;
  entry: string;
  importSteps: string[];
};

export type PluginConnectionStep = {
  id: "auth" | "projects" | "exports" | "download";
  title: string;
  apiPath: string;
  detail: string;
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

export const unityPluginFlow: UnityPluginStep[] = [
  {
    id: "manifest",
    title: "Manifest",
    apiPath: "/api/plugin/exports/{export_id}/manifest",
    detail: "Unity Editor reads package metadata, prefab entry, import plan and checksum.",
    outputs: ["package id", "prefab entry", "unity import plan"]
  },
  {
    id: "download",
    title: "Download ZIP",
    apiPath: "/api/plugin/exports/{export_id}/download",
    detail: "Plugin downloads the Unity-ready package and verifies it before extraction.",
    outputs: ["Unity ZIP", "checksum", "prefab entry"]
  },
  {
    id: "import-log",
    title: "Import log",
    apiPath: "/api/plugin/import-logs",
    detail: "Editor reports imported assets, prefab creation, scene creation and warnings.",
    outputs: ["assets imported", "prefabs created", "warnings"]
  },
  {
    id: "restyle-manifest",
    title: "Replacement manifest",
    apiPath: "/api/plugin/engine-snapshots/{snapshot_id}/restyle",
    detail: "Existing Unity UI keeps layout and script bindings while sprites are restyled.",
    outputs: ["preserve RectTransform", "node path mapping", "replacement sprites"]
  }
];

export const engineExportTargets: EngineExportTarget[] = [
  {
    id: "unity",
    title: "Unity 2022.3+",
    engineVersion: "2022.3+",
    entry: "Unity prefab",
    importSteps: ["extract_zip", "import_textures_as_sprites", "create_prefab", "create_scene", "write_import_log"]
  },
  {
    id: "cocos3",
    title: "Cocos Creator 3.8.6+",
    engineVersion: "3.8.6+",
    entry: "Cocos3 prefab",
    importSteps: ["copy_textures", "create_sprite_frames", "create_prefab", "create_scene", "write_import_log"]
  },
  {
    id: "cocos2",
    title: "Cocos Creator 2.4.x+",
    engineVersion: "2.4.x+",
    entry: "Cocos2 prefab",
    importSteps: ["copy_textures", "create_sprite_frames", "create_prefab", "write_import_log"]
  },
  {
    id: "godot",
    title: "Godot 4.x",
    engineVersion: "4.x",
    entry: "Godot TSCN scene",
    importSteps: ["copy_textures", "write_tscn_scene", "refresh_filesystem", "write_import_log"]
  }
];

export const pluginConnectionSteps: PluginConnectionStep[] = [
  {
    id: "auth",
    title: "Plugin Auth",
    apiPath: "/api/plugin/auth",
    detail: "Exchange a Web-issued plugin token for a short-lived editor access token."
  },
  {
    id: "projects",
    title: "Project Sync",
    apiPath: "/api/plugin/projects",
    detail: "List owned projects with supported engine targets for the active editor."
  },
  {
    id: "exports",
    title: "Export Query",
    apiPath: "/api/plugin/projects/{project_id}/exports?engine=unity",
    detail: "Filter ready export packages by project and engine before import."
  },
  {
    id: "download",
    title: "Package Download",
    apiPath: "/api/plugin/exports/{export_id}/download",
    detail: "Download the package, verify checksum and start the native import plan."
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
