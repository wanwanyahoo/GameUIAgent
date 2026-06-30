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
import { App as StudioApp } from "./StudioApp";

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

  if (route.path === "/dashboard") {
    return <Dashboard />;
  }

  if (route.path === "/studio") {
    return <StudioApp />;
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
        {activeTab === "team" && <TeamPagePlaceholder />}
        {activeTab === "profile" && <ProfilePagePlaceholder />}
      </SettingsLayout>
    );
  }

  return <LandingPage />;
}

function TeamPagePlaceholder() {
  return (
    <div className="placeholder-page">
      <h1>Team</h1>
      <p className="page-subtitle">Manage your team members and roles</p>
      <div className="empty-state">
        <div className="empty-icon">👥</div>
        <h3>Team management coming soon</h3>
        <p>Invite team members, set roles and permissions, and collaborate on projects.</p>
      </div>
    </div>
  );
}

function ProfilePagePlaceholder() {
  return (
    <div className="placeholder-page">
      <h1>Profile</h1>
      <p className="page-subtitle">Manage your account settings</p>
      <div className="empty-state">
        <div className="empty-icon">👤</div>
        <h3>Profile settings coming soon</h3>
        <p>Update your personal information, password, and notification preferences.</p>
      </div>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <RouteRenderer />
    </AuthProvider>
  );
}
