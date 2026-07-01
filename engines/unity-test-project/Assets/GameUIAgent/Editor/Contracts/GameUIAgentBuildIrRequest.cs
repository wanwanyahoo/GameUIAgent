using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentBuildIrRequest
    {
        public string api_base_url;
        public string access_token;
        public string project_id;
        public string engine;
        public string source;
        public string snapshot_json;
        public string snapshot_id;
    }
}
