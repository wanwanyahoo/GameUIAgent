import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildStudioEditorState,
  createStudioEditorPatch,
  redoStudioEditor,
  selectStudioEditorNode,
  undoStudioEditor,
  updateStudioEditorNode
} from "../lib/studio-editor";
import type { StudioIr } from "../lib/studio-api";

const editableIr: StudioIr = {
  id: "ir_1",
  projectId: "prj_1",
  version: "0.1.0",
  canvas: { width: 1920, height: 1080 },
  nodes: [
    {
      id: "root",
      type: "canvas",
      name: "HUD Canvas",
      rect: { x: 0, y: 0, width: 1920, height: 1080 }
    },
    {
      id: "panel_main",
      type: "panel",
      name: "Main Panel",
      rect: { x: 240, y: 120, width: 1440, height: 760 }
    },
    {
      id: "button_primary",
      type: "button",
      name: "Primary CTA",
      parentId: "panel_main",
      rect: { x: 1320, y: 820, width: 280, height: 96 }
    }
  ]
};

describe("studio editor state", () => {
  it("builds a selectable layer tree and inspector model from Asset IR", () => {
    const editor = buildStudioEditorState(editableIr, "button_primary");

    assert.equal(editor.selectedNode?.id, "button_primary");
    assert.deepEqual(editor.layerTree.map((node) => node.id), ["root"]);
    assert.deepEqual(editor.layerTree[0]?.children?.map((node) => node.id), ["panel_main"]);
    assert.deepEqual(editor.layerTree[0]?.children?.[0]?.children?.map((node) => node.id), ["button_primary"]);
    assert.deepEqual(editor.inspector.rect, { x: 1320, y: 820, width: 280, height: 96 });
  });

  it("tracks selection, patches and undo redo without mutating the source IR", () => {
    const selected = selectStudioEditorNode(buildStudioEditorState(editableIr, "root"), "button_primary");
    const updated = updateStudioEditorNode(selected, {
      name: "Safe CTA",
      rect: { x: 840, y: 760, width: 360, height: 112 },
      visible: false
    });

    assert.equal(editableIr.nodes[2]?.name, "Primary CTA");
    assert.equal(updated.selectedNode?.name, "Safe CTA");
    assert.equal(updated.undoStack.length, 1);

    const patch = createStudioEditorPatch(updated, "Move CTA into safe area");
    assert.deepEqual(patch, {
      baseVersion: "0.1.0",
      summary: "Move CTA into safe area",
      operations: [
        {
          op: "update_node",
          nodeId: "button_primary",
          fields: {
            name: "Safe CTA",
            rect: { x: 840, y: 760, width: 360, height: 112 },
            visible: false
          }
        }
      ]
    });

    const undone = undoStudioEditor(updated);
    assert.equal(undone.selectedNode?.name, "Primary CTA");
    assert.equal(undone.redoStack.length, 1);

    const redone = redoStudioEditor(undone);
    assert.equal(redone.selectedNode?.name, "Safe CTA");
    assert.equal(redone.undoStack.length, 1);
  });

  it("recomputes pending patch fields when undo removes all edits", () => {
    const selected = selectStudioEditorNode(buildStudioEditorState(editableIr, "root"), "button_primary");
    const updated = updateStudioEditorNode(selected, {
      name: "Safe CTA"
    });

    const undone = undoStudioEditor(updated);
    const patch = createStudioEditorPatch(undone, "Undo edit");

    assert.equal(undone.selectedNode?.name, "Primary CTA");
    assert.deepEqual(undone.pendingFields, {});
    assert.deepEqual(patch.operations, []);
  });
});
