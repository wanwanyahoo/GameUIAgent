import { useState, type FormEvent } from "react";
import { navigateTo } from "../lib/hash-router";
import { requestPasswordResetApi, confirmPasswordResetApi } from "../lib/auth-api";

type PasswordResetPageProps = {
  mode: "request" | "confirm";
  token?: string;
};

export function PasswordResetPage({ mode, token }: PasswordResetPageProps) {
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const isConfirm = mode === "confirm";

  async function handleRequest(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email) {
      setError("Please enter your email address");
      return;
    }
    try {
      setIsLoading(true);
      await requestPasswordResetApi(email);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Failed to send reset email");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleConfirm(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError("Reset token is missing");
      return;
    }
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      setIsLoading(true);
      await confirmPasswordResetApi(token, newPassword);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Failed to reset password");
    } finally {
      setIsLoading(false);
    }
  }

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-brand">
            <span className="brand-mark">G</span>
            <h1>GameUIAgent</h1>
          </div>

          <div className="success-message">
            <div className="success-icon">✓</div>
            <h2>
              {isConfirm ? "Password Reset Successful" : "Check Your Email"}
            </h2>
            <p>
              {isConfirm
                ? "Your password has been reset successfully. You can now sign in with your new password."
                : `If an account exists for ${email}, we've sent a password reset link to your email.`}
            </p>
            <button
              type="button"
              className="btn-primary btn-block"
              onClick={() => navigateTo("/login")}
            >
              Back to Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="brand-mark">G</span>
          <h1>GameUIAgent</h1>
        </div>

        <h2 className="auth-title">
          {isConfirm ? "Reset Your Password" : "Reset Password"}
        </h2>
        <p className="auth-subtitle">
          {isConfirm
            ? "Enter your new password below."
            : "Enter your email and we'll send you a reset link."}
        </p>

        {error && <div className="error-banner">{error}</div>}

        <form className="auth-form" onSubmit={isConfirm ? handleConfirm : handleRequest}>
          {!isConfirm ? (
            <div className="form-field">
              <label htmlFor="reset-email">Email address</label>
              <input
                id="reset-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
            </div>
          ) : (
            <>
              <div className="form-field">
                <label htmlFor="new-password">New Password</label>
                <input
                  id="new-password"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="form-field">
                <label htmlFor="confirm-password">Confirm Password</label>
                <input
                  id="confirm-password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleConfirm(e as any)}
                />
              </div>
            </>
          )}

          <button
            type="submit"
            className="btn-primary btn-block"
            disabled={isLoading}
          >
            {isLoading
              ? "Please wait..."
              : isConfirm
              ? "Reset Password"
              : "Send Reset Link"}
          </button>
        </form>

        <p className="auth-footer">
          <button
            type="button"
            className="link-button"
            onClick={() => navigateTo("/login")}
          >
            Back to Sign In
          </button>
        </p>
      </div>
    </div>
  );
}
