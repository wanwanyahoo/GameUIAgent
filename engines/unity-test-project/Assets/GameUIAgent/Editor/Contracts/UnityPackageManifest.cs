using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class UnityPackageManifest
    {
        public string package_id;
        public string project_id;
        public string ir_id;
        public string engine;
        public string engine_version;
        public UnityPackageEntry entry;
        public UnityPackageAsset[] assets;
    }

    [Serializable]
    public sealed class UnityPackageEntry
    {
        public string type;
        public string path;
    }

    [Serializable]
    public sealed class UnityPackageAsset
    {
        public string path;
        public string kind;
    }
}
