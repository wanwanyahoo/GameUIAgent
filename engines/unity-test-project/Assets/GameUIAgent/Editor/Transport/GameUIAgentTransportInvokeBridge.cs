using System;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportInvokeBridge
    {
        private readonly GameUIAgentMcpDispatcher dispatcher = new GameUIAgentMcpDispatcher();

        public GameUIAgentTransportInvokeAcceptedResponse Invoke(
            GameUIAgentTransportInvokeRequest request,
            GameUIAgentTransportSessionStore sessionStore,
            GameUIAgentTransportEventBus eventBus)
        {
            if (request == null)
            {
                throw new ArgumentException("request is required");
            }
            if (sessionStore == null)
            {
                throw new ArgumentException("sessionStore is required");
            }
            if (eventBus == null)
            {
                throw new ArgumentException("eventBus is required");
            }

            GameUIAgentTransportSessionStore.TransportSession session = sessionStore.Get(request.session_id);
            if (session == null)
            {
                throw new InvalidOperationException("INVALID_SESSION");
            }

            if (Array.IndexOf(session.authorized_tools, request.tool_name) < 0)
            {
                throw new InvalidOperationException("TOOL_NOT_AUTHORIZED");
            }

            string taskId = Guid.NewGuid().ToString("N");
            sessionStore.Touch(request.session_id);

            eventBus.Publish(new GameUIAgentTransportEvent
            {
                type = "tool_started",
                session_id = request.session_id,
                request_id = request.request_id,
                task_id = taskId,
                tool_name = request.tool_name,
                status = "running",
                timestamp = DateTime.UtcNow.ToString("o")
            });

            GameUIAgentToolResponse response = dispatcher.Dispatch(new GameUIAgentToolRequest
            {
                tool_name = request.tool_name,
                arguments_json = request.arguments_json
            });

            eventBus.Publish(new GameUIAgentTransportEvent
            {
                type = response.status == "ok" ? "tool_succeeded" : "tool_failed",
                session_id = request.session_id,
                request_id = request.request_id,
                task_id = taskId,
                tool_name = request.tool_name,
                status = response.status,
                payload_json = response.payload_json,
                error_code = response.error_code,
                error_message = response.error_message,
                timestamp = DateTime.UtcNow.ToString("o")
            });

            return new GameUIAgentTransportInvokeAcceptedResponse
            {
                status = "accepted",
                request_id = request.request_id,
                task_id = taskId
            };
        }
    }
}
