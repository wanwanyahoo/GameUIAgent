import type { StudioIr, StudioIrNode, StudioIrPatchOperation } from "./studio-api";

export type StudioEditorLayerNode = StudioIrNode & {
  children: StudioEditorLayerNode[];
};

export type StudioEditorInspector = {
  nodeId: string;
  name: string;
  type: string;
  rect: { x: number; y: number; width: number; height: number };
  visible: boolean;
  opacity: number;
};

export type StudioEditorState = {
  baseVersion: string;
  baseIr: StudioIr;
  draftIr: StudioIr;
  selectedNodeId: string;
  selectedNode?: StudioIrNode;
  layerTree: StudioEditorLayerNode[];
  inspector: StudioEditorInspector;
  undoStack: StudioIr[];
  redoStack: StudioIr[];
  pendingFields: Record<string, Record<string, unknown>>;
};

export function buildStudioEditorState(ir: StudioIr, selectedNodeId?: string): StudioEditorState {
  const draftIr = cloneIr(ir);
  return hydrateEditorState({
    baseVersion: ir.version,
    baseIr: cloneIr(ir),
    draftIr,
    selectedNodeId: selectedNodeId ?? firstEditableNodeId(draftIr),
    undoStack: [],
    redoStack: [],
    pendingFields: {}
  });
}

export function selectStudioEditorNode(state: StudioEditorState, nodeId: string): StudioEditorState {
  if (!state.draftIr.nodes.some((node) => node.id === nodeId)) {
    return state;
  }
  return hydrateEditorState({ ...state, selectedNodeId: nodeId });
}

export function updateStudioEditorNode(
  state: StudioEditorState,
  fields: Record<string, unknown>
): StudioEditorState {
  const draftIr = cloneIr(state.draftIr);
  const node = draftIr.nodes.find((item) => item.id === state.selectedNodeId);
  if (!node) {
    return state;
  }
  Object.assign(node, fields);
  return hydrateEditorState({
    ...state,
    draftIr,
    undoStack: [...state.undoStack, cloneIr(state.draftIr)],
    redoStack: [],
    pendingFields: {
      ...state.pendingFields,
      [node.id]: {
        ...(state.pendingFields[node.id] ?? {}),
        ...fields
      }
    }
  });
}

export function undoStudioEditor(state: StudioEditorState): StudioEditorState {
  const previous = state.undoStack.at(-1);
  if (!previous) {
    return state;
  }
  return hydrateEditorState({
    ...state,
    draftIr: cloneIr(previous),
    undoStack: state.undoStack.slice(0, -1),
    redoStack: [cloneIr(state.draftIr), ...state.redoStack]
  });
}

export function redoStudioEditor(state: StudioEditorState): StudioEditorState {
  const next = state.redoStack[0];
  if (!next) {
    return state;
  }
  return hydrateEditorState({
    ...state,
    draftIr: cloneIr(next),
    undoStack: [...state.undoStack, cloneIr(state.draftIr)],
    redoStack: state.redoStack.slice(1)
  });
}

export function createStudioEditorPatch(state: StudioEditorState, summary: string): {
  baseVersion: string;
  summary: string;
  operations: StudioIrPatchOperation[];
} {
  const pendingFields = diffIrNodes(state.baseIr, state.draftIr);
  return {
    baseVersion: state.baseVersion,
    summary,
    operations: Object.entries(pendingFields).map(([nodeId, fields]) => ({
      op: "update_node",
      nodeId,
      fields
    }))
  };
}

function hydrateEditorState(state: Omit<StudioEditorState, "selectedNode" | "layerTree" | "inspector">): StudioEditorState {
  const selectedNode = state.draftIr.nodes.find((node) => node.id === state.selectedNodeId)
    ?? state.draftIr.nodes[0];
  return {
    ...state,
    selectedNode,
    selectedNodeId: selectedNode?.id ?? state.selectedNodeId,
    layerTree: buildLayerTree(state.draftIr),
    inspector: buildInspector(selectedNode),
    pendingFields: diffIrNodes(state.baseIr, state.draftIr)
  };
}

function buildLayerTree(ir: StudioIr): StudioEditorLayerNode[] {
  const byId = new Map<string, StudioEditorLayerNode>();
  for (const node of ir.nodes) {
    byId.set(node.id, { ...node, children: [] });
  }
  const roots: StudioEditorLayerNode[] = [];
  for (const node of byId.values()) {
    if (node.parentId && byId.has(node.parentId)) {
      byId.get(node.parentId)?.children.push(node);
    } else if (node.type === "canvas" || node.id === "root") {
      roots.push(node);
    } else {
      const root = byId.get("root");
      if (root) {
        root.children.push(node);
      } else {
        roots.push(node);
      }
    }
  }
  return roots;
}

function buildInspector(node: StudioIrNode | undefined): StudioEditorInspector {
  return {
    nodeId: node?.id ?? "",
    name: node?.name ?? "",
    type: node?.type ?? "",
    rect: node?.rect ?? { x: 0, y: 0, width: 1, height: 1 },
    visible: node?.visible ?? true,
    opacity: node?.opacity ?? 1
  };
}

function firstEditableNodeId(ir: StudioIr): string {
  return ir.nodes.find((node) => node.type !== "canvas")?.id ?? ir.nodes[0]?.id ?? "";
}

function diffIrNodes(baseIr: StudioIr, draftIr: StudioIr): Record<string, Record<string, unknown>> {
  const baseById = new Map(baseIr.nodes.map((node) => [node.id, node]));
  const editableFields = ["name", "rect", "visible", "opacity", "text", "layout", "component", "nineSlice"] as const;
  const pendingFields: Record<string, Record<string, unknown>> = {};

  for (const node of draftIr.nodes) {
    const baseNode = baseById.get(node.id);
    if (!baseNode) continue;
    const fields: Record<string, unknown> = {};
    for (const field of editableFields) {
      if (!isEqualJson(node[field], baseNode[field])) {
        fields[field] = node[field];
      }
    }
    if (Object.keys(fields).length > 0) {
      pendingFields[node.id] = fields;
    }
  }
  return pendingFields;
}

function isEqualJson(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function cloneIr(ir: StudioIr): StudioIr {
  return JSON.parse(JSON.stringify(ir)) as StudioIr;
}
