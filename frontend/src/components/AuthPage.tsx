import { useState, type FormEvent } from "react";
import { useAuth } from "../lib/auth-context";

type AuthPageProps = {
  mode: "login" | "register";
  onModeChange: (mode: "login" | "register") => void;
  onSuccess?: () => void;
};

export function AuthPage({ mode, onModeChange, onSuccess }: AuthPageProps) {
  const { login, register, isLoading, error, clearError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const isLogin = mode === "login";
  const title = isLogin ? "Welcome back" : "Create your account";
  const subtitle = isLogin
    ? "Sign in to your GameUIAgent workspace"
    : "Start building game UI with AI in seconds";
  const buttonText = isLoading ? "Please wait..." : isLogin ? "Sign in" : "Create account";
  const toggleText = isLogin ? "Don't have an account?" : "Already have an account?";
  const toggleAction = isLogin ? "Sign up" : "Sign in";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (!email || !password) {
      setFormError("Please fill in all required fields");
      return;
    }
    if (password.length < 6) {
      setFormError("Password must be at least 6 characters");
      return;
    }
    if (!isLogin && !name) {
      setFormError("Please enter your name");
      return;
    }

    try {
      if (isLogin) {
        await login({ email, password });
      } else {
        await register({ email, password, name });
      }
      onSuccess?.();
    } catch {
    }
  }

  function switchMode() {
    setFormError(null);
    clearError();
    onModeChange(isLogin ? "register" : "login");
  }

  const displayError = formError || error;

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="brand-mark">G</span>
          <span>GameUIAgent</span>
        </div>
        <h1>{title}</h1>
        <p className="auth-subtitle">{subtitle}</p>

        {displayError && <div className="auth-error">{displayError}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          {!isLogin && (
            <label className="auth-field">
              <span>Name</span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                disabled={isLoading}
                autoComplete="name"
              />
            </label>
          )}
          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@studio.com"
              disabled={isLoading}
              autoComplete="email"
            />
          </label>
          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              disabled={isLoading}
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
          </label>
          <button type="submit" className="auth-submit" disabled={isLoading}>
            {buttonText}
          </button>
        </form>

        <div className="auth-toggle">
          {toggleText}{" "}
          <button type="button" onClick={switchMode} className="auth-link">
            {toggleAction}
          </button>
        </div>

        <div className="auth-divider">
          <span>or</span>
        </div>

        <div className="auth-sso">
          <button type="button" className="sso-btn">
            <span>Continue with Google</span>
          </button>
          <button type="button" className="sso-btn">
            <span>Continue with GitHub</span>
          </button>
        </div>
      </div>
    </div>
  );
}
