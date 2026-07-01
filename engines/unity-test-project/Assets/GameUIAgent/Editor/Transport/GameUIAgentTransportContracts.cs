using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentTransportAuthRequest
    {
        public string token;
        public string project_id;
        public string engine;
        public string client_version;
    }

    [Serializable]
    public sealed class GameUIAgentTransportAuthResponse
    {
        public string session_id;
        public string connection_id;
        public string[] authorized_tools;
        public string plugin_version;
    }

    [Serializable]
    public sealed class GameUIAgentTransportInvokeRequest
    {
        public string session_id;
        public string request_id;
        public string tool_name;
        public string arguments_json;
    }

    [Serializable]
    public sealed class GameUIAgentTransportInvokeAcceptedResponse
    {
        public string status;
        public string request_id;
        public string task_id;
    }

    [Serializable]
    public sealed class GameUIAgentTransportEvent
    {
        public string type;
        public string session_id;
        public string request_id;
        public string task_id;
        public string timestamp;
        public string tool_name;
        public string status;
        public float progress;
        public string message;
        public string payload_json;
        public string error_code;
        public string error_message;
    }
}
