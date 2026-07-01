using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentToolDescriptor
    {
        public string name;
        public string description;
        public string input_schema_json;
    }
}
