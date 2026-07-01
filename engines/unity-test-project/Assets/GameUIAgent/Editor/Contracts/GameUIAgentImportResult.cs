using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentImportResult
    {
        public string status;
        public string engine_version;
        public string plugin_version;
        public int duration_ms;
        public GameUIAgentImportSummary summary;
        public GameUIAgentLogEntry[] logs;
        public GameUIAgentSnapshot snapshot;
        public string prefab_path;
        public string scene_path;
        public string manifest_asset_path;
    }

    [Serializable]
    public sealed class GameUIAgentImportSummary
    {
        public int assets_imported;
        public int prefabs_created;
        public int scenes_created;
        public int warnings;
        public int errors;
    }

    [Serializable]
    public sealed class GameUIAgentLogEntry
    {
        public string level;
        public string message;
    }
}
