using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentBuildIrResult
    {
        public string project_id;
        public string snapshot_id;
        public string ir_id;
        public string version_id;
        public string status;
        public string payload_json;
    }
}
