import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth-context";

type Team = {
  id: string;
  name: string;
  owner_id: string;
  members: TeamMember[];
};

type TeamMember = {
  id: string;
  team_id: string;
  email: string;
  role: string;
  user_id: string | null;
  joined_at: string;
};

const ROLE_LABELS: Record<string, string> = {
  owner: "Owner",
  admin: "Admin",
  designer: "Designer",
  developer: "Developer",
  viewer: "Viewer",
};

export function TeamPage() {
  const { token, user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [activeTeam, setActiveTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("developer");
  const [newTeamName, setNewTeamName] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const loadTeams = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/teams", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load teams");
      const data = await res.json();
      const teamList = data.teams || [];
      setTeams(teamList);
      if (teamList.length > 0 && !activeTeam) {
        setActiveTeam(teamList[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load teams");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeams();
  }, [token]);

  const handleCreateTeam = async () => {
    if (!token || !newTeamName.trim()) return;
    try {
      setActionLoading(true);
      setError(null);
      const res = await fetch("/api/teams", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newTeamName.trim() }),
      });
      if (!res.ok) throw new Error("Failed to create team");
      const created = await res.json();
      setTeams([...teams, created]);
      setActiveTeam(created);
      setNewTeamName("");
      setCreateOpen(false);
    } catch (err: any) {
      setError(err.message || "Failed to create team");
    } finally {
      setActionLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!token || !activeTeam || !inviteEmail.trim()) return;
    try {
      setActionLoading(true);
      setError(null);
      const res = await fetch(`/api/teams/${activeTeam.id}/members`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }),
      });
      if (!res.ok) throw new Error("Failed to invite member");
      setInviteEmail("");
      setInviteRole("developer");
      setInviteOpen(false);
      await loadTeams();
    } catch (err: any) {
      setError(err.message || "Failed to invite member");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRoleChange = async (memberId: string, newRole: string) => {
    if (!token || !activeTeam) return;
    try {
      setError(null);
      const res = await fetch(`/api/teams/${activeTeam.id}/members/${memberId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ role: newRole }),
      });
      if (!res.ok) throw new Error("Failed to update role");
      await loadTeams();
    } catch (err: any) {
      setError(err.message || "Failed to update role");
    }
  };

  const isOwner = activeTeam?.owner_id === user?.id;
  const isAdmin = isOwner || activeTeam?.members.some(
    (m) => m.email === user?.email && (m.role === "admin" || m.role === "owner")
  );

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div className="team-page">
      <div className="page-header">
        <div>
          <h1>Team</h1>
          <p className="page-subtitle">Manage your team members and collaboration settings</p>
        </div>
        {teams.length > 0 && isAdmin && (
          <button type="button" className="btn-primary" onClick={() => setInviteOpen(true)}>
            + Invite Member
          </button>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading teams...</div>
      ) : teams.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">👥</div>
          <h3>No team yet</h3>
          <p>Create a team to collaborate with your teammates on game UI projects.</p>
          <button type="button" className="btn-primary" onClick={() => setCreateOpen(true)}>
            Create Team
          </button>
        </div>
      ) : (
        <>
          {teams.length > 1 && (
            <div className="team-switcher">
              {teams.map((team) => (
                <button
                  key={team.id}
                  type="button"
                  className={`team-tab ${activeTeam?.id === team.id ? "active" : ""}`}
                  onClick={() => setActiveTeam(team)}
                >
                  {team.name}
                </button>
              ))}
              <button
                type="button"
                className="team-tab add-team"
                onClick={() => setCreateOpen(true)}
              >
                + New
              </button>
            </div>
          )}

          {activeTeam && (
            <div className="team-content">
              <div className="team-info-card">
                <div className="team-info-header">
                  <h2>{activeTeam.name}</h2>
                  <span className="team-role-badge">
                    {activeTeam.members.find((m) => m.email === user?.email)?.role || "member"}
                  </span>
                </div>
                <p className="team-stats">
                  {activeTeam.members.length} member{activeTeam.members.length !== 1 ? "s" : ""}
                </p>
              </div>

              <div className="members-section">
                <h3>Members</h3>
                <div className="members-list">
                  {activeTeam.members.map((member) => (
                    <div key={member.id} className="member-item">
                      <div className="member-avatar">
                        {member.email.charAt(0).toUpperCase()}
                      </div>
                      <div className="member-info">
                        <div className="member-email">{member.email}</div>
                        <div className="member-joined">
                          Joined {formatDate(member.joined_at)}
                        </div>
                      </div>
                      {isAdmin && member.role !== "owner" && (
                        <select
                          className="role-select"
                          value={member.role}
                          onChange={(e) => handleRoleChange(member.id, e.target.value)}
                          disabled={!isAdmin}
                        >
                          {Object.entries(ROLE_LABELS).filter(([k]) => k !== "owner").map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      )}
                      {member.role === "owner" && (
                        <span className="owner-badge">Owner</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create Team</h2>
            <p className="modal-subtitle">Create a new team workspace for collaboration.</p>
            <div className="form-field">
              <label htmlFor="team-name">Team Name</label>
              <input
                id="team-name"
                type="text"
                placeholder="e.g., My Game Studio"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateTeam()}
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
                onClick={handleCreateTeam}
                disabled={!newTeamName.trim() || actionLoading}
              >
                {actionLoading ? "Creating..." : "Create Team"}
              </button>
            </div>
          </div>
        </div>
      )}

      {inviteOpen && (
        <div className="modal-overlay" onClick={() => setInviteOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Invite Team Member</h2>
            <p className="modal-subtitle">Send an invitation to collaborate on your team.</p>
            <div className="form-field">
              <label htmlFor="invite-email">Email Address</label>
              <input
                id="invite-email"
                type="email"
                placeholder="teammate@example.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleInvite()}
                autoFocus
              />
            </div>
            <div className="form-field">
              <label htmlFor="invite-role">Role</label>
              <select
                id="invite-role"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
              >
                {Object.entries(ROLE_LABELS).filter(([k]) => k !== "owner").map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-outline" onClick={() => setInviteOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleInvite}
                disabled={!inviteEmail.trim() || actionLoading}
              >
                {actionLoading ? "Sending..." : "Send Invite"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
