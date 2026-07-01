using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentBuildSnapshotTool
    {
        private readonly GameUIAgentSnapshotBuilder snapshotBuilder = new GameUIAgentSnapshotBuilder();
        public GameUIAgentToolDescriptor Descriptor => new GameUIAgentToolDescriptor
        {
            name = "build_snapshot",
            description = "Build a Unity snapshot payload for AI Studio readback.",
            input_schema_json = "{\"type\":\"object\",\"required\":[\"texture_asset_path\"]}"
        };

        public GameUIAgentToolResponse Execute(GameUIAgentToolRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.arguments_json))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "build_snapshot",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "build_snapshot requires arguments_json"
                };
            }

            BuildSnapshotArguments arguments = JsonUtility.FromJson<BuildSnapshotArguments>(request.arguments_json);
            if (arguments == null || string.IsNullOrWhiteSpace(arguments.texture_asset_path))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "build_snapshot",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "build_snapshot requires texture_asset_path"
                };
            }

            GameUIAgentSnapshot snapshot = snapshotBuilder.BuildImportedSnapshot(arguments.texture_asset_path);
            return new GameUIAgentToolResponse
            {
                tool_name = "build_snapshot",
                status = "ok",
                payload_json = JsonUtility.ToJson(snapshot)
            };
        }

        [System.Serializable]
        private sealed class BuildSnapshotArguments
        {
            public string texture_asset_path;
        }
    }
}
