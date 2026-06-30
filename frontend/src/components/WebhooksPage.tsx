import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth-context";

type Webhook = {
  id: string;
  url: string;
  events: string[];
  description: string;
  active: boolean;
  created_at: string;
  last_sent_at: string | null;
  success_count: number;
  failure_count: number;
};

type NewWebhook = {
  id: string;
  url: string;
  events: string[];
  description: string;
  active: boolean;
  secret: string;
  created_at: string;
};

const AVAILABLE_EVENTS = [
  "ai.job.completed",
  "ai.job.failed",
  "ai.job.started",
  "export.completed",
  "export.failed",
  "import.completed",
  "import.failed",
  "asset.created",
  "asset.updated",
  "project.created",
  "project.updated",
];

export function WebhooksPage() {
  const { token } = useAuth();
  const [hooks, setHooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createdHook, setCreatedHook] = useState<NewWebhook | null>(null);
  const [copied, setCopied] = useState(false);

  const [formUrl, setFormUrl] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>(["ai.job.completed"]);

  const loadHooks = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/user/webhooks", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load webhooks");
      const data = await res.json();
      setHooks(data.webhooks || []);
    } catch (err: any) {
      setError(err.message || "Failed to load webhooks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHooks();
  }, [token]);

  const toggleEvent = (event: string) => {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  const handleCreate = async () => {
    if (!token || !formUrl.trim() || selectedEvents.length === 0) return;
    try {
      setError(null);
      const res = await fetch("/api/user/webhooks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          url: formUrl.trim(),
          events: selectedEvents,
          description: formDescription.trim(),
        }),
      });
      if (!res.ok) throw new Error("Failed to create webhook");
      const data = await res.json();
      setCreatedHook(data);
      setFormUrl("");
      setFormDescription("");
      setSelectedEvents(["ai.job.completed"]);
      await loadHooks();
    } catch (err: any) {
      setError(err.message || "Failed to create webhook");
    }
  };

  const handleToggle = async (hook: Webhook) => {
    if (!token) return;
    try {
      setError(null);
      const res = await fetch(`/api/user/webhooks/${hook.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ active: !hook.active }),
      });
      if (!res.ok) throw new Error("Failed to update webhook");
      await loadHooks();
    } catch (err: any) {
      setError(err.message || "Failed to update webhook");
    }
  };

  const handleTest = async (hookId: string) => {
    if (!token) return;
    try {
      setError(null);
      const res = await fetch(`/api/user/webhooks/${hookId}/test`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to send test webhook");
    } catch (err: any) {
      setError(err.message || "Failed to send test webhook");
    }
  };

  const handleDelete = async (hookId: string) => {
    if (!token) return;
    if (!confirm("Are you sure you want to delete this webhook? This cannot be undone.")) return;
    try {
      setError(null);
      const res = await fetch(`/api/user/webhooks/${hookId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to delete webhook");
      setHooks(hooks.filter((h) => h.id !== hookId));
    } catch (err: any) {
      setError(err.message || "Failed to delete webhook");
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div className="webhooks-page">
      <div className="page-header">
        <div>
          <h1>Webhooks</h1>
          <p className="page-subtitle">Configure webhooks to receive real-time event notifications</p>
        </div>
        <button type="button" className="btn-primary" onClick={() => { setCreateOpen(true); setCreatedHook(null); }}>
          + Add Endpoint
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="webhooks-info">
        <div className="info-icon">📡</div>
        <div>
          <strong>Webhooks let you build integrations.</strong>
          Set up HTTP endpoints to receive events from GameUIAgent in real time.
          All webhook deliveries are signed with HMAC-SHA256 for verification.
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading webhooks...</div>
      ) : (
        <div className="webhooks-list">
          {hooks.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔗</div>
              <h3>No webhooks yet</h3>
              <p>Create your first webhook endpoint to receive real-time event notifications.</p>
              <button type="button" className="btn-primary" onClick={() => { setCreateOpen(true); setCreatedHook(null); }}>
                Add Webhook
              </button>
            </div>
          ) : (
            <div className="webhook-cards">
              {hooks.map((hook) => (
                <div key={hook.id} className={`webhook-card ${hook.active ? "active" : "inactive"}`}>
                  <div className="webhook-card-header">
                    <div className="webhook-url">
                      <span className={`status-badge ${hook.active ? "status-active" : "status-inactive"}`}>
                        {hook.active ? "Active" : "Paused"}
                      </span>
                      <code>{hook.url}</code>
                    </div>
                    <div className="webhook-actions">
                      <button type="button" className="btn-outline btn-sm" onClick={() => handleToggle(hook)}>
                        {hook.active ? "Pause" : "Enable"}
                      </button>
                      <button type="button" className="btn-outline btn-sm" onClick={() => handleTest(hook.id)}>
                        Test
                      </button>
                      <button type="button" className="btn-danger-ghost btn-sm" onClick={() => handleDelete(hook.id)}>
                        Delete
                      </button>
                    </div>
                  </div>
                  {hook.description && (
                    <p className="webhook-description">{hook.description}</p>
                  )}
                  <div className="webhook-meta">
                    <div className="meta-item">
                      <span className="meta-label">Events</span>
                      <div className="event-tags">
                        {hook.events.slice(0, 3).map((ev) => (
                          <span key={ev} className="event-tag">{ev}</span>
                        ))}
                        {hook.events.length > 3 && (
                          <span className="event-tag more">+{hook.events.length - 3} more</span>
                        )}
                      </div>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Success</span>
                      <span className="meta-value success">{hook.success_count}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Failures</span>
                      <span className="meta-value failure">{hook.failure_count}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Created</span>
                      <span className="meta-value">{formatDate(hook.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="webhooks-docs">
        <h3>Available Events</h3>
        <div className="events-grid">
          {AVAILABLE_EVENTS.map((ev) => (
            <div key={ev} className="event-item">
              <code>{ev}</code>
            </div>
          ))}
        </div>
      </div>

      {createOpen && (
        <div className="modal-overlay" onClick={() => { setCreateOpen(false); setCreatedHook(null); }}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            {createdHook ? (
              <>
                <h2>Webhook Created</h2>
                <p className="modal-subtitle">
                  Save your signing secret. You won't be able to see it again.
                </p>
                <div className="new-key-display">
                  <code>{createdHook.secret}</code>
                  <button
                    type="button"
                    className="btn-outline copy-btn"
                    onClick={() => handleCopy(createdHook.secret)}
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <div className="key-warning">
                  ⚠️ This secret is only shown once. Store it securely to verify webhook signatures.
                </div>
                <div className="form-field">
                  <label>Endpoint URL</label>
                  <input type="text" value={createdHook.url} readOnly />
                </div>
                <div className="form-field">
                  <label>Events</label>
                  <div className="event-tags">
                    {createdHook.events.map((ev) => (
                      <span key={ev} className="event-tag">{ev}</span>
                    ))}
                  </div>
                </div>
                <div className="modal-actions">
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => { setCreateOpen(false); setCreatedHook(null); }}
                  >
                    Done
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2>Add Webhook Endpoint</h2>
                <p className="modal-subtitle">Configure a URL to receive event notifications.</p>
                <div className="form-field">
                  <label htmlFor="wh-url">Endpoint URL *</label>
                  <input
                    id="wh-url"
                    type="url"
                    placeholder="https://your-app.com/api/webhooks/gameuiagent"
                    value={formUrl}
                    onChange={(e) => setFormUrl(e.target.value)}
                    autoFocus
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="wh-desc">Description (optional)</label>
                  <input
                    id="wh-desc"
                    type="text"
                    placeholder="e.g., Production notifications"
                    value={formDescription}
                    onChange={(e) => setFormDescription(e.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Events to listen to *</label>
                  <div className="events-checklist">
                    {AVAILABLE_EVENTS.map((ev) => (
                      <label key={ev} className="check-item">
                        <input
                          type="checkbox"
                          checked={selectedEvents.includes(ev)}
                          onChange={() => toggleEvent(ev)}
                        />
                        <span>{ev}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-outline" onClick={() => setCreateOpen(false)}>
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleCreate}
                    disabled={!formUrl.trim() || selectedEvents.length === 0}
                  >
                    Create Webhook
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
