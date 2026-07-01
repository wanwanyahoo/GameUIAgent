using UnityEditor;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public static class GameUIAgentMcpMenu
    {
        [MenuItem("GameUIAgent/MCP/List Tools")]
        public static void ListTools()
        {
            GameUIAgentMcpToolRegistry registry = new GameUIAgentMcpToolRegistry();
            GameUIAgentToolDescriptor[] tools = registry.ListTools();
            Debug.Log("GameUIAgent MCP tools: " + JsonUtility.ToJson(new ToolDescriptorList { tools = tools }));
        }

        [MenuItem("GameUIAgent/MCP/Run Import Package")]
        public static void RunImportPackage()
        {
            string zipPath = EditorUtility.OpenFilePanel("Select GameUIAgent export zip", string.Empty, "zip");
            if (string.IsNullOrWhiteSpace(zipPath))
            {
                return;
            }

            GameUIAgentMcpDispatcher dispatcher = new GameUIAgentMcpDispatcher();
            GameUIAgentToolResponse response = dispatcher.Dispatch(new GameUIAgentToolRequest
            {
                tool_name = "import_package",
                arguments_json = JsonUtility.ToJson(new ImportPackageMenuArguments
                {
                    export_id = "local-mcp-import",
                    engine = "unity",
                    zip_path = zipPath
                })
            });
            Debug.Log("GameUIAgent MCP import response: " + JsonUtility.ToJson(response));
        }

        [MenuItem("GameUIAgent/MCP/Run Build Snapshot")]
        public static void RunBuildSnapshot()
        {
            string assetPath = EditorUtility.OpenFilePanel("Select imported texture", Application.dataPath, "png");
            if (string.IsNullOrWhiteSpace(assetPath))
            {
                return;
            }

            string unityAssetPath = assetPath.Replace(Application.dataPath, "Assets");
            GameUIAgentMcpDispatcher dispatcher = new GameUIAgentMcpDispatcher();
            GameUIAgentToolResponse response = dispatcher.Dispatch(new GameUIAgentToolRequest
            {
                tool_name = "build_snapshot",
                arguments_json = JsonUtility.ToJson(new BuildSnapshotMenuArguments
                {
                    texture_asset_path = unityAssetPath
                })
            });
            Debug.Log("GameUIAgent MCP snapshot response: " + JsonUtility.ToJson(response));
        }

        [System.Serializable]
        private sealed class ToolDescriptorList
        {
            public GameUIAgentToolDescriptor[] tools;
        }

        [System.Serializable]
        private sealed class ImportPackageMenuArguments
        {
            public string export_id;
            public string engine;
            public string zip_path;
        }

        [System.Serializable]
        private sealed class BuildSnapshotMenuArguments
        {
            public string texture_asset_path;
        }
    }
}
