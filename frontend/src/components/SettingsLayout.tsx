import { useState } from "react";
import { useAuth } from "../lib/auth-context";

type SettingsPageProps = {
  activeTab: string;
  onTabChange: (tab: string) => void;
  children: React.ReactNode;
};

const tabs = [
  { id: "billing", label: "Billing", icon: "💳" },
  { id: "api-keys", label: "API Keys", icon: "🔑" },
  { id: "webhooks", label: "Webhooks", icon: "🔗" },
  { id: "developer", label: "Developer", icon: "⚡" },
  { id: "team", label: "Team", icon: "👥" },
  { id: "profile", label: "Profile", icon: "👤" },
];

export function SettingsLayout({ activeTab, onTabChange, children }: SettingsPageProps) {
  const { user, logout } = useAuth();

  return (
    <div className="settings-page">
      <header className="settings-header">
        <div className="settings-brand">
          <span className="brand-mark">G</span>
          <span>GameUIAgent</span>
        </div>
        <div className="settings-user">
          <span className="user-email">{user?.email || "user"}</span>
          <button type="button" className="user-menu" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="settings-body">
        <aside className="settings-sidebar">
          <nav className="settings-nav">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`settings-nav-item ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => onTabChange(tab.id)}
              >
                <span className="nav-icon">{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        <main className="settings-content">
          {children}
        </main>
      </div>
    </div>
  );
}
