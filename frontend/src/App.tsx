import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./lib/auth-context";
import { useHashRouter } from "./lib/hash-router";
import { LandingPage } from "./components/LandingPage";
import { AuthPage } from "./components/AuthPage";
import { Dashboard } from "./components/Dashboard";
import { SettingsLayout } from "./components/SettingsLayout";
import { BillingPage } from "./components/BillingPage";
import { ApiKeysPage } from "./components/ApiKeysPage";
import { WebhooksPage } from "./components/WebhooksPage";
import { DeveloperPage } from "./components/DeveloperPage";
import { PasswordResetPage } from "./components/PasswordResetPage";
import { TeamPage } from "./components/TeamPage";
import { ProfilePage } from "./components/ProfilePage";
import { StudioPage } from "./components/StudioPage";

function RouteRenderer() {
  const { route, navigate } = useHashRouter();
  const { user, isLoading } = useAuth();
  const [settingsTab, setSettingsTab] = useState("billing");

  useEffect(() => {
    if (isLoading) return;

    const protectedRoutes = ["/dashboard", "/studio", "/settings"];
    const isProtected = protectedRoutes.some((r) => route.path.startsWith(r));

    if (isProtected && !user) {
      navigate("/login");
      return;
    }

    if ((route.path === "/login" || route.path === "/register") && user) {
      navigate("/dashboard");
      return;
    }
  }, [route.path, user, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading GameUIAgent...</p>
      </div>
    );
  }

  if (route.path === "/" || route.path === "") {
    return <LandingPage />;
  }

  if (route.path === "/login") {
    return <AuthPage mode="login" />;
  }

  if (route.path === "/register") {
    return <AuthPage mode="register" />;
  }

  if (route.path === "/password-reset") {
    return <PasswordResetPage mode="request" />;
  }

  if (route.path.startsWith("/reset-password")) {
    const token = route.params.token || route.path.split("/").pop() || "";
    return <PasswordResetPage mode="confirm" token={token} />;
  }

  if (route.path === "/dashboard") {
    return <Dashboard />;
  }

  if (route.path.startsWith("/studio")) {
    const parts = route.path.split("/").filter(Boolean);
    const projectId = parts.length >= 2 ? parts[1] : "";
    return <StudioPage projectId={projectId} />;
  }

  if (route.path.startsWith("/settings")) {
    const tab = route.path.replace("/settings/", "").replace("/settings", "");
    const activeTab = tab || "billing";
    return (
      <SettingsLayout activeTab={activeTab} onTabChange={(t) => navigate(`/settings/${t}`)}>
        {activeTab === "billing" && <BillingPage />}
        {activeTab === "api-keys" && <ApiKeysPage />}
        {activeTab === "webhooks" && <WebhooksPage />}
        {activeTab === "developer" && <DeveloperPage />}
        {activeTab === "team" && <TeamPage />}
        {activeTab === "profile" && <ProfilePage />}
      </SettingsLayout>
    );
  }

  return <LandingPage />;
}

export function App() {
  return (
    <AuthProvider>
      <RouteRenderer />
    </AuthProvider>
  );
}
