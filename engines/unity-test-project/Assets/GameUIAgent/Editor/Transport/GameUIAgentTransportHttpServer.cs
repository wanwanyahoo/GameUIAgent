using System;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportHttpServer
    {
        private readonly GameUIAgentMcpToolRegistry registry = new GameUIAgentMcpToolRegistry();

        public string[] Routes =>
            new[]
            {
                "POST /authenticate",
                "GET /healthz",
                "GET /tools",
                "POST /invoke"
            };

        public GameUIAgentTransportAuthResponse Authenticate(
            GameUIAgentTransportAuthRequest request,
            GameUIAgentTransportAuthService authService,
            GameUIAgentTransportSessionStore sessionStore)
        {
            return authService.Authenticate(request, sessionStore);
        }

        public string Healthz()
        {
            return JsonUtility.ToJson(new HealthzPayload
            {
                status = "ok",
                engine = "unity",
                plugin_version = "0.3.0",
                transport_version = "v1"
            });
        }

        public string Tools(string sessionId, GameUIAgentTransportSessionStore sessionStore)
        {
            if (sessionStore.Get(sessionId) == null)
            {
                throw new InvalidOperationException("INVALID_SESSION");
            }
            return JsonUtility.ToJson(new ToolListPayload
            {
                import_package = "import_package",
                build_snapshot = "build_snapshot",
                build_ir = "build_ir",
                tools = registry.ListTools()
            });
        }

        public GameUIAgentTransportInvokeAcceptedResponse Invoke(
            GameUIAgentTransportInvokeRequest request,
            GameUIAgentTransportInvokeBridge invokeBridge,
            GameUIAgentTransportSessionStore sessionStore,
            GameUIAgentTransportEventBus eventBus)
        {
            return invokeBridge.Invoke(request, sessionStore, eventBus);
        }

        [Serializable]
        private sealed class HealthzPayload
        {
            public string status;
            public string engine;
            public string plugin_version;
            public string transport_version;
        }

        [Serializable]
        private sealed class ToolListPayload
        {
            public string import_package;
            public string build_snapshot;
            public string build_ir;
            public GameUIAgentToolDescriptor[] tools;
        }
    }
}
