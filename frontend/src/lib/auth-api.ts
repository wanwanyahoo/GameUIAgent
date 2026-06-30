export type AuthUser = {
  id: string;
  email: string;
  name: string;
};

export type LoginResult = {
  accessToken: string;
  tokenType: string;
};

export type RegisterData = {
  email: string;
  password: string;
  name: string;
};

export type LoginData = {
  email: string;
  password: string;
};

const TOKEN_KEY = "gameuiagent_token";
const USER_KEY = "gameuiagent_user";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setAuthSession(token: string, user?: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearAuthSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export type AuthApiOptions = {
  baseUrl?: string;
  fetcher?: typeof fetch;
};

function defaultFetcher(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(input, init);
}

export async function registerApi(data: RegisterData, options: AuthApiOptions = {}): Promise<AuthUser> {
  const fetcher = options.fetcher || defaultFetcher;
  const baseUrl = options.baseUrl || "";
  const response = await fetcher(`${baseUrl}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new AuthError(response.status, detail || "Registration failed");
  }
  return response.json() as Promise<AuthUser>;
}

export async function loginApi(data: LoginData, options: AuthApiOptions = {}): Promise<LoginResult> {
  const fetcher = options.fetcher || defaultFetcher;
  const baseUrl = options.baseUrl || "";
  const response = await fetcher(`${baseUrl}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new AuthError(response.status, detail || "Login failed");
  }
  const body = await response.json();
  return {
    accessToken: body.access_token,
    tokenType: body.token_type,
  };
}

export async function requestPasswordResetApi(email: string, options: AuthApiOptions = {}): Promise<{ status: string; delivery: string }> {
  const fetcher = options.fetcher || defaultFetcher;
  const baseUrl = options.baseUrl || "";
  const response = await fetcher(`${baseUrl}/api/auth/password-reset/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new AuthError(response.status, detail || "Password reset request failed");
  }
  return response.json();
}

export async function confirmPasswordResetApi(
  token: string,
  newPassword: string,
  options: AuthApiOptions = {}
): Promise<{ status: string }> {
  const fetcher = options.fetcher || defaultFetcher;
  const baseUrl = options.baseUrl || "";
  const response = await fetcher(`${baseUrl}/api/auth/password-reset/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new AuthError(response.status, detail || "Password reset failed");
  }
  return response.json();
}

async function parseErrorDetail(response: Response): Promise<string | null> {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") return body.detail;
    if (body && typeof body.message === "string") return body.message;
  } catch {
  }
  return null;
}

export class AuthError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "AuthError";
    this.status = status;
  }
}
