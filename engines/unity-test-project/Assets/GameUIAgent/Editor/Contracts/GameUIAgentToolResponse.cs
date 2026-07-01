using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentToolResponse
    {
        public string tool_name;
        public string status;
        public string error_code;
        public string error_message;
        public string payload_json;
    }
}
