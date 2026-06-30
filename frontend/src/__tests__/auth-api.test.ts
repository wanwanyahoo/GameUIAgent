import assert from "node:assert/strict";
import { describe, it, beforeEach, afterEach, before } from "node:test";

import {
  AuthError,
  clearAuthSession,
  getStoredToken,
  getStoredUser,
  loginApi,
  registerApi,
  setAuthSession,
  requestPasswordResetApi,
  confirmPasswordResetApi,
} from "../lib/auth-api";

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

function mockFetch(status: number, body: unknown, headers?: Record<string, string>) {
  return async function (_input: RequestInfo | URL, _init?: RequestInit): Promise<Response> {
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
      text: async () => JSON.stringify(body),
      headers: new Headers(headers || {}),
    } as Response;
  };
}

describe("auth-api", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("registerApi returns user on success", async () => {
    const fetcher = mockFetch(201, {
      id: "usr_123",
      email: "test@example.com",
      name: "Test User",
    });

    const user = await registerApi(
      { email: "test@example.com", password: "secret123", name: "Test User" },
      { fetcher }
    );

    assert.equal(user.id, "usr_123");
    assert.equal(user.email, "test@example.com");
    assert.equal(user.name, "Test User");
  });

  it("registerApi throws AuthError on conflict", async () => {
    const fetcher = mockFetch(409, { detail: "Email already registered" });

    try {
      await registerApi(
        { email: "exists@example.com", password: "secret123", name: "Test" },
        { fetcher }
      );
      assert.fail("expected AuthError");
    } catch (err) {
      assert.ok(err instanceof AuthError);
      assert.equal((err as AuthError).status, 409);
      assert.equal((err as AuthError).message, "Email already registered");
    }
  });

  it("loginApi returns access token on success", async () => {
    const fetcher = mockFetch(200, {
      access_token: "tok_abc123",
      token_type: "bearer",
    });

    const result = await loginApi(
      { email: "test@example.com", password: "secret123" },
      { fetcher }
    );

    assert.equal(result.accessToken, "tok_abc123");
    assert.equal(result.tokenType, "bearer");
  });

  it("loginApi throws AuthError on invalid credentials", async () => {
    const fetcher = mockFetch(401, { detail: "Invalid credentials" });

    try {
      await loginApi(
        { email: "wrong@example.com", password: "wrong" },
        { fetcher }
      );
      assert.fail("expected AuthError");
    } catch (err) {
      assert.ok(err instanceof AuthError);
      assert.equal((err as AuthError).status, 401);
    }
  });

  it("session storage persists token and user", () => {
    assert.equal(getStoredToken(), null);
    assert.equal(getStoredUser(), null);

    setAuthSession("tok_123", { id: "usr_1", email: "a@b.com", name: "A" });

    assert.equal(getStoredToken(), "tok_123");
    const user = getStoredUser();
    assert.ok(user);
    assert.equal(user.email, "a@b.com");
    assert.equal(user.name, "A");

    clearAuthSession();

    assert.equal(getStoredToken(), null);
    assert.equal(getStoredUser(), null);
  });

  it("requestPasswordResetApi returns queued status", async () => {
    const fetcher = mockFetch(200, {
      status: "queued",
      delivery: "smtp",
      expires_in: 900,
    });

    const result = await requestPasswordResetApi("test@example.com", { fetcher });

    assert.equal(result.status, "queued");
    assert.equal(result.delivery, "smtp");
  });

  it("confirmPasswordResetApi returns success status", async () => {
    const fetcher = mockFetch(200, { status: "password_reset" });

    const result = await confirmPasswordResetApi("rst_token", "newpass123", { fetcher });

    assert.equal(result.status, "password_reset");
  });
});
