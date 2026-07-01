using System;
using System.IO;

namespace GameUIAgent.Editor
{
    public static class GameUIAgentPathUtility
    {
        public static string NormalizeAssetPath(string assetPath)
        {
            return (assetPath ?? string.Empty).Replace("\\", "/");
        }

        public static string ProjectPath(string projectRoot, string assetPath)
        {
            string normalized = NormalizeAssetPath(assetPath);
            if (!normalized.StartsWith("Assets/", StringComparison.Ordinal))
            {
                throw new InvalidOperationException("Expected Unity asset path, got " + assetPath);
            }
            return Path.Combine(projectRoot, normalized);
        }

        public static void EnsureAssetParent(string projectRoot, string assetPath)
        {
            string absolute = ProjectPath(projectRoot, assetPath);
            string directory = Path.GetDirectoryName(absolute);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }
        }
    }
}
