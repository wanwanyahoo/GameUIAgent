using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentImportRequest
    {
        public string export_id;
        public string engine;
        public string zip_path;
        public string manifest_json;
        public string package_json;
        public bool build_scene = true;
        public bool build_snapshot = true;
    }
}
