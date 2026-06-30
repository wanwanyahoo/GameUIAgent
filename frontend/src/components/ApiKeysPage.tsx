import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth-context";

type ApiKey = {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
};

type NewKey = {
  id: string;
  name: string;
  api_key: string;
};

export function ApiKeysPage() {
  const { token } = useAuth();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<NewKey | null>(null);
  const [copied, setCopied] = useState(false);

  const loadKeys = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/user/api-keys", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load API keys");
      const data = await res.json();
      setKeys(data.api_keys || []);
    } catch (err: any) {
      setError(err.message || "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, [token]);

  const handleCreate = async () => {
    if (!token || !newKeyName.trim()) return;
    try {
      setError(null);
      const res = await fetch("/api/user/api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newKeyName.trim() }),
      });
      if (!res.ok) throw new Error("Failed to create API key");
      const data = await res.json();
      setCreatedKey(data);
      setNewKeyName("");
      await loadKeys();
    } catch (err: any) {
      setError(err.message || "Failed to create API key");
    }
  };

  const handleRevoke = async (keyId: string) => {
    if (!token) return;
    if (!confirm("Are you sure you want to revoke this API key? This cannot be undone.")) return;
    try {
      setError(null);
      const res = await fetch(`/api/user/api-keys/${keyId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to revoke API key");
      setKeys(keys.filter((k) => k.id !== keyId));
    } catch (err: any) {
      setError(err.message || "Failed to revoke API key");
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

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div className="api-keys-page">
      <div className="page-header">
        <div>
          <h1>API Keys</h1>
          <p className="page-subtitle">Manage your API keys for programmatic access</p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setCreateOpen(true)}>
          + Create New Key
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="api-keys-info">
        <div className="info-icon">🔒</div>
        <div>
          <strong>Keep your API keys secure.</strong>
          Never share your API keys in client-side code, public repositories, or support tickets.
          If a key is compromised, revoke it immediately and create a new one.
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading API keys...</div>
      ) : (
        <div className="api-keys-table">
          {keys.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔑</div>
              <h3>No API keys yet</h3>
              <p>Create your first API key to start building with the GameUIAgent API.</p>
              <button type="button" className="btn-primary" onClick={() => setCreateOpen(true)}>
                Create API Key
              </button>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Key</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr key={key.id}>
                    <td className="key-name">{key.name}</td>
                    <td className="key-prefix">
                      <code>{key.prefix}</code>
                    </td>
                    <td className="key-date">{key.created_at ? formatDate(key.created_at) : "—"}</td>
                    <td className="key-actions">
                      <button
                        type="button"
                        className="btn-danger-ghost"
                        onClick={() => handleRevoke(key.id)}
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="api-keys-docs">
        <h3>Quick Start</h3>
        <div className="code-block">
          <pre>{`curl -X POST https://api.gameuiagent.com/v1/ai/generate \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "kind": "text_to_image",
    "prompt": "futuristic game menu UI, cyberpunk style",
    "size": "1024x1024"
  }'`}</pre>
        </div>
        <p>See the <a href="#developer">Developer Documentation</a> for the full API reference.</p>
      </div>

      {createOpen && (
        <div className="modal-overlay" onClick={() => { setCreateOpen(false); setCreatedKey(null); }}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {createdKey ? (
              <>
                <h2>API Key Created</h2>
                <p className="modal-subtitle">
                  Copy your key now. You won't be able to see it again.
                </p>
                <div className="new-key-display">
                  <code>{createdKey.api_key}</code>
                  <button
                    type="button"
                    className="btn-outline copy-btn"
                    onClick={() => handleCopy(createdKey.api_key)}
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <div className="key-warning">
                  ⚠️ This key is only shown once. Store it securely.
                </div>
                <div className="modal-actions">
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => { setCreateOpen(false); setCreatedKey(null); }}
                  >
                    Done
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2>Create API Key</h2>
                <p className="modal-subtitle">Give your key a name to identify its purpose.</p>
                <div className="form-field">
                  <label htmlFor="key-name">Key Name</label>
                  <input
                    id="key-name"
                    type="text"
                    placeholder="e.g., Production API, CI/CD Pipeline"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                    autoFocus
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-outline" onClick={() => setCreateOpen(false)}>
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleCreate}
                    disabled={!newKeyName.trim()}
                  >
                    Create Key
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
