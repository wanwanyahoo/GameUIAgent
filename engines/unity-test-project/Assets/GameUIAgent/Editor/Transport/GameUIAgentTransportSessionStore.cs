using System;
using System.Collections.Generic;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportSessionStore
    {
        private readonly Dictionary<string, TransportSession> sessions = new Dictionary<string, TransportSession>();

        public TransportSession Create(string projectId, string engine, string[] authorizedTools)
        {
            TransportSession session = new TransportSession
            {
                session_id = Guid.NewGuid().ToString("N"),
                connection_id = Guid.NewGuid().ToString("N"),
                project_id = projectId,
                engine = engine,
                authorized_tools = authorizedTools,
                created_at = DateTime.UtcNow.ToString("o"),
                last_seen_at = DateTime.UtcNow.ToString("o")
            };
            sessions[session.session_id] = session;
            return session;
        }

        public TransportSession Get(string sessionId)
        {
            if (string.IsNullOrWhiteSpace(sessionId))
            {
                return null;
            }
            sessions.TryGetValue(sessionId, out TransportSession session);
            return session;
        }

        public void Touch(string sessionId)
        {
            TransportSession session = Get(sessionId);
            if (session != null)
            {
                session.last_seen_at = DateTime.UtcNow.ToString("o");
            }
        }

        [Serializable]
        public sealed class TransportSession
        {
            public string session_id;
            public string connection_id;
            public string project_id;
            public string engine;
            public string[] authorized_tools;
            public string created_at;
            public string last_seen_at;
        }
    }
}
