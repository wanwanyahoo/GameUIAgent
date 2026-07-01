using System;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportWebSocketServer
    {
        private readonly GameUIAgentTransportEventBus eventBus;

        public GameUIAgentTransportWebSocketServer(GameUIAgentTransportEventBus eventBus)
        {
            this.eventBus = eventBus;
        }

        public string[] SupportedEvents =>
            new[]
            {
                "connected",
                "authenticated",
                "tool_started",
                "tool_progress",
                "tool_log",
                "tool_succeeded",
                "tool_failed",
                "heartbeat"
            };

        public void Connect(string connectionId)
        {
            eventBus.Publish(new GameUIAgentTransportEvent
            {
                type = "connected",
                payload_json = connectionId,
                timestamp = DateTime.UtcNow.ToString("o")
            });
        }

        public void PublishAuthenticated(string sessionId)
        {
            eventBus.Publish(new GameUIAgentTransportEvent
            {
                type = "authenticated",
                session_id = sessionId,
                timestamp = DateTime.UtcNow.ToString("o")
            });
        }

        public void PublishHeartbeat(string sessionId)
        {
            eventBus.PublishHeartbeat(sessionId);
        }
    }
}
