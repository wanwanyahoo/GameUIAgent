namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentTransportHost
    {
        private readonly GameUIAgentTransportSessionStore sessionStore = new GameUIAgentTransportSessionStore();
        private readonly GameUIAgentTransportEventBus eventBus = new GameUIAgentTransportEventBus();
        private readonly GameUIAgentTransportAuthService authService = new GameUIAgentTransportAuthService();
        private readonly GameUIAgentTransportInvokeBridge invokeBridge = new GameUIAgentTransportInvokeBridge();

        public GameUIAgentTransportHost()
        {
            HttpServer = new GameUIAgentTransportHttpServer();
            WebSocketServer = new GameUIAgentTransportWebSocketServer(eventBus);
        }

        public GameUIAgentTransportHttpServer HttpServer { get; }

        public GameUIAgentTransportWebSocketServer WebSocketServer { get; }

        public GameUIAgentTransportSessionStore SessionStore => sessionStore;

        public GameUIAgentTransportAuthService AuthService => authService;

        public GameUIAgentTransportInvokeBridge InvokeBridge => invokeBridge;

        public GameUIAgentTransportEventBus EventBus => eventBus;
    }
}
