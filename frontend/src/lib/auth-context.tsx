import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import {
  AuthUser,
  LoginData,
  RegisterData,
  clearAuthSession,
  getStoredToken,
  getStoredUser,
  loginApi,
  registerApi,
  setAuthSession,
  getCurrentUserApi,
  updateUserApi,
} from "./auth-api";

export type AuthState = {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
};

export type AuthContextValue = AuthState & {
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  updateProfile: (data: { name?: string }) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children, baseUrl }: { children: ReactNode; baseUrl?: string }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    const token = getStoredToken();
    const storedUser = getStoredUser();
    if (token && storedUser?.id) {
      setState({ user: storedUser, token, isLoading: false, error: null });
    } else if (token) {
      getCurrentUserApi(token, { baseUrl })
        .then((user) => {
          setAuthSession(token, user);
          setState({ user, token, isLoading: false, error: null });
        })
        .catch(() => {
          clearAuthSession();
          setState({ user: null, token: null, isLoading: false, error: null });
        });
    } else {
      setState({ user: null, token: null, isLoading: false, error: null });
    }
  }, [baseUrl]);

  const login = useCallback(async (data: LoginData) => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result = await loginApi(data, { baseUrl });
      const user = await getCurrentUserApi(result.accessToken, { baseUrl });
      setAuthSession(result.accessToken, user);
      setState({ user, token: result.accessToken, isLoading: false, error: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setState((s) => ({ ...s, isLoading: false, error: message }));
      throw err;
    }
  }, [baseUrl]);

  const register = useCallback(async (data: RegisterData) => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      await registerApi(data, { baseUrl });
      const loginResult = await loginApi({ email: data.email, password: data.password }, { baseUrl });
      const user = await getCurrentUserApi(loginResult.accessToken, { baseUrl });
      setAuthSession(loginResult.accessToken, user);
      setState({ user, token: loginResult.accessToken, isLoading: false, error: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setState((s) => ({ ...s, isLoading: false, error: message }));
      throw err;
    }
  }, [baseUrl]);

  const logout = useCallback(() => {
    clearAuthSession();
    setState({ user: null, token: null, isLoading: false, error: null });
  }, []);

  const clearError = useCallback(() => {
    setState((s) => ({ ...s, error: null }));
  }, []);

  const updateProfile = useCallback(async (data: { name?: string }) => {
    if (!state.token) throw new Error("Not authenticated");
    setState((s) => ({ ...s, error: null }));
    try {
      const updated = await updateUserApi(state.token, data, { baseUrl });
      setAuthSession(state.token!, updated);
      setState((s) => ({ ...s, user: updated }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Update failed";
      setState((s) => ({ ...s, error: message }));
      throw err;
    }
  }, [state.token, baseUrl]);

  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
    clearError,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
