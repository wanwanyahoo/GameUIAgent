using System;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportAuthService
    {
        private static readonly string[] AuthorizedTools =
        {
            "import_package",
            "build_snapshot",
            "build_ir"
        };

        public GameUIAgentTransportAuthResponse Authenticate(
            GameUIAgentTransportAuthRequest request,
            GameUIAgentTransportSessionStore sessionStore)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.token))
            {
                throw new ArgumentException("token is required");
            }
            if (string.IsNullOrWhiteSpace(request.project_id))
            {
                throw new ArgumentException("project_id is required");
            }
            if (string.IsNullOrWhiteSpace(request.engine))
            {
                throw new ArgumentException("engine is required");
            }
            if (!string.Equals(request.engine, "unity", StringComparison.OrdinalIgnoreCase))
            {
                throw new ArgumentException("only unity engine is supported");
            }
            if (sessionStore == null)
            {
                throw new ArgumentException("sessionStore is required");
            }

            GameUIAgentTransportSessionStore.TransportSession session = sessionStore.Create(
                request.project_id,
                request.engine,
                AuthorizedTools);

            return new GameUIAgentTransportAuthResponse
            {
                session_id = session.session_id,
                connection_id = session.connection_id,
                authorized_tools = session.authorized_tools,
                plugin_version = "0.3.0"
            };
        }
    }
}
