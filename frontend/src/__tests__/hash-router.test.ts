import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

function createLocalStorageMock() {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => { store.set(key, value); },
    removeItem: (key: string) => { store.delete(key); },
    clear: () => { store.clear(); },
  };
}

function createWindowMock() {
  let hash = "";
  const listeners: Map<string, Set<() => void>> = new Map();

  return {
    get location() {
      return {
        get hash() { return hash; },
        set hash(v: string) {
          hash = v;
          const ev = listeners.get("hashchange");
          if (ev) ev.forEach((fn) => fn());
        },
      };
    },
    addEventListener(event: string, fn: () => void) {
      if (!listeners.has(event)) listeners.set(event, new Set());
      listeners.get(event)!.add(fn);
    },
    removeEventListener(event: string, fn: () => void) {
      listeners.get(event)?.delete(fn);
    },
    dispatchEvent(_ev: any) {
      return true;
    },
  };
}

describe("hash-router utility", () => {
  beforeEach(() => {
    (globalThis as any).localStorage = createLocalStorageMock();
    (globalThis as any).window = createWindowMock();
  });

  test("navigateTo updates window.location.hash", async () => {
    const { navigateTo } = await import("../lib/hash-router");
    navigateTo("/dashboard");
    assert.equal(window.location.hash, "/dashboard");
  });

  test("navigateTo supports nested settings paths", async () => {
    const { navigateTo } = await import("../lib/hash-router");
    navigateTo("/settings/billing");
    assert.equal(window.location.hash, "/settings/billing");
  });

  test("navigateTo supports studio path", async () => {
    const { navigateTo } = await import("../lib/hash-router");
    navigateTo("/studio");
    assert.equal(window.location.hash, "/studio");
  });
});
