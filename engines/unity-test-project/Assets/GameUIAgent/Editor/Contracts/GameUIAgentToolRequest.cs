using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentToolRequest
    {
        public string tool_name;
        public string arguments_json;
    }
}
