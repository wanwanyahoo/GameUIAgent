using System;
using System.Collections.Generic;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportEventBus
    {
        private readonly List<GameUIAgentTransportEvent> events = new List<GameUIAgentTransportEvent>();

        public void Publish(GameUIAgentTransportEvent transportEvent)
        {
            events.Add(transportEvent);
        }

        public void PublishConnected(string connectionId)
        {
            Publish(new GameUIAgentTransportEvent
            {
                type = "connected",
                message = "connected",
                request_id = string.Empty,
                task_id = string.Empty,
                session_id = string.Empty,
                payload_json = connectionId,
                timestamp = DateTime.UtcNow.ToString("o")
            });
        }

        public void PublishHeartbeat(string sessionId)
        {
            Publish(new GameUIAgentTransportEvent
            {
                type = "heartbeat",
                session_id = sessionId,
                request_id = string.Empty,
                task_id = string.Empty,
                message = "heartbeat",
                timestamp = DateTime.UtcNow.ToString("o")
            });
        }

        public IReadOnlyList<GameUIAgentTransportEvent> Snapshot()
        {
            return events;
        }
    }
}
