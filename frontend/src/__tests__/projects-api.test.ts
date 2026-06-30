import assert from "node:assert/strict";
import { describe, it, beforeEach, afterEach, before } from "node:test";

import { createProjectApi, getProjectApi, getStudioStateApi, listProjectsApi } from "../lib/projects-api";

function createLocalStorageMock(): Storage {
  const store = new Map<string, string>();
  return {
    get length() { return store.size; },
    clear() { store.clear(); },
    getItem(key: string) { return store.get(key) ?? null; },
    key(index: number) { return Array.from(store.keys())[index] ?? null; },
    removeItem(key: string) { store.delete(key); },
    setItem(key: string, value: string) { store.set(key, value); },
  };
}

before(() => {
  (globalThis as any).localStorage = createLocalStorageMock();
});

describe("projects-api", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("listProjectsApi returns projects list", async () => {
    const mockProjects = [
      {
        id: "prj_1",
        name: "Test Project",
        target_engine: "unity",
        canvas: { width: 1920, height: 1080 },
        status: "active",
        owner_id: "usr_1",
      },
    ];

    const fetcher = async (_input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const headers = init?.headers as Record<string, string>;
      assert.equal(headers.Authorization, "Bearer tok_test");
      return {
        ok: true,
        status: 200,
        json: async () => ({ projects: mockProjects }),
        text: async () => JSON.stringify({ projects: mockProjects }),
        headers: new Headers(),
      } as Response;
    };

    const projects = await listProjectsApi("tok_test", { fetcher });
    assert.equal(projects.length, 1);
    assert.equal(projects[0].name, "Test Project");
    assert.equal(projects[0].target_engine, "unity");
    assert.equal(projects[0].canvas.width, 1920);
  });

  it("listProjectsApi throws on error", async () => {
    const fetcher = async (_input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
      return {
        ok: false,
        status: 401,
        json: async () => ({ detail: "Unauthorized" }),
        text: async () => JSON.stringify({ detail: "Unauthorized" }),
        headers: new Headers(),
      } as Response;
    };

    try {
      await listProjectsApi("bad_token", { fetcher });
      assert.fail("expected error");
    } catch (err) {
      assert.ok(err instanceof Error);
      assert.match((err as Error).message, /Unauthorized/);
    }
  });

  it("createProjectApi sends correct payload", async () => {
    let capturedBody: string | undefined;

    const fetcher = async (_input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      capturedBody = init?.body as string;
      const body = JSON.parse(capturedBody || "{}");
      return {
        ok: true,
        status: 201,
        json: async () => ({
          id: "prj_new",
          name: body.name,
          target_engine: body.target_engine,
          canvas: body.canvas,
          status: "active",
          owner_id: "usr_1",
        }),
        text: async () => capturedBody || "",
        headers: new Headers(),
      } as Response;
    };

    const project = await createProjectApi(
      "tok_test",
      {
        name: "New Game UI",
        target_engine: "godot",
        canvas: { width: 1280, height: 720 },
      },
      { fetcher }
    );

    assert.equal(project.id, "prj_new");
    assert.equal(project.name, "New Game UI");
    assert.equal(project.target_engine, "godot");
    assert.equal(project.canvas.width, 1280);
    assert.equal(project.canvas.height, 720);

    const sent = JSON.parse(capturedBody || "{}");
    assert.equal(sent.name, "New Game UI");
    assert.equal(sent.target_engine, "godot");
    assert.deepEqual(sent.canvas, { width: 1280, height: 720 });
  });

  it("createProjectApi throws on validation error", async () => {
    const fetcher = async (_input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
      return {
        ok: false,
        status: 422,
        json: async () => ({ detail: "Validation error" }),
        text: async () => JSON.stringify({ detail: "Validation error" }),
        headers: new Headers(),
      } as Response;
    };

    try {
      await createProjectApi("tok_test", { name: "", target_engine: "unity", canvas: { width: 0, height: 0 } }, { fetcher });
      assert.fail("expected error");
    } catch (err) {
      assert.ok(err instanceof Error);
      assert.match((err as Error).message, /Validation error/);
    }
  });

  it("getProjectApi loads one project by id", async () => {
    let capturedInput = "";
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      capturedInput = String(input);
      const headers = init?.headers as Record<string, string>;
      assert.equal(headers.Authorization, "Bearer tok_test");
      return {
        ok: true,
        status: 200,
        json: async () => ({
          id: "prj_live",
          name: "Live Project",
          target_engine: "unity",
          canvas: { width: 1920, height: 1080 },
          status: "active",
          owner_id: "usr_1",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
        text: async () => "",
        headers: new Headers(),
      } as Response;
    };

    const project = await getProjectApi("tok_test", "prj_live", { fetcher });

    assert.equal(capturedInput, "/api/projects/prj_live");
    assert.equal(project.id, "prj_live");
    assert.equal(project.name, "Live Project");
  });

  it("getStudioStateApi loads studio state for a project", async () => {
    let capturedInput = "";
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      capturedInput = String(input);
      const headers = init?.headers as Record<string, string>;
      assert.equal(headers.Authorization, "Bearer tok_test");
      return {
        ok: true,
        status: 200,
        json: async () => ({
          project_id: "prj_live",
          active_selection: {
            selected_layer_id: "layer_button",
            selected_asset_id: "asset_slice",
            active_task_id: "timeline_slice",
          },
          action_dock: [{ id: "export", title: "Export", shortcut: "E" }],
          timeline: [{ id: "timeline_slice", title: "Slice UI", status: "ready" }],
          segmentation_corrections: [],
          export_wizard: {
            target_engine: "unity",
            steps: [{ id: "validate", title: "Validate IR", status: "active" }],
          },
        }),
        text: async () => "",
        headers: new Headers(),
      } as Response;
    };

    const studio = await getStudioStateApi("tok_test", "prj_live", { fetcher });

    assert.equal(capturedInput, "/api/projects/prj_live/studio");
    assert.equal(studio.project_id, "prj_live");
    assert.equal(studio.action_dock[0].title, "Export");
    assert.equal(studio.export_wizard.target_engine, "unity");
  });
});
