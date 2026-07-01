using System;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentBuildIrTool
    {
        private readonly GameUIAgentBackendBridge backendBridge = new GameUIAgentBackendBridge();

        public GameUIAgentToolDescriptor Descriptor => new GameUIAgentToolDescriptor
        {
            name = "build_ir",
            description = "Bridge a Unity snapshot into backend IR construction for AI Studio.",
            input_schema_json = "{\"type\":\"object\",\"required\":[\"project_id\",\"engine\"]}"
        };

        public GameUIAgentToolResponse Execute(GameUIAgentToolRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.arguments_json))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "build_ir",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "build_ir requires arguments_json"
                };
            }

            BuildIrArguments arguments = JsonUtility.FromJson<BuildIrArguments>(request.arguments_json);
            if (arguments == null || string.IsNullOrWhiteSpace(arguments.project_id) || string.IsNullOrWhiteSpace(arguments.engine))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "build_ir",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "build_ir requires project_id and engine"
                };
            }

            if (string.IsNullOrWhiteSpace(arguments.snapshot_json) && string.IsNullOrWhiteSpace(arguments.snapshot_id))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "build_ir",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "build_ir requires snapshot_json or snapshot_id"
                };
            }

            GameUIAgentBuildIrRequest bridgeRequest = new GameUIAgentBuildIrRequest
            {
                api_base_url = ResolveSetting(arguments.api_base_url, "GAMEUIAGENT_API_BASE_URL"),
                access_token = ResolveSetting(arguments.access_token, "GAMEUIAGENT_API_TOKEN"),
                project_id = arguments.project_id,
                engine = arguments.engine,
                source = string.IsNullOrWhiteSpace(arguments.source) ? "unity_mcp_build_ir" : arguments.source,
                snapshot_json = arguments.snapshot_json,
                snapshot_id = arguments.snapshot_id
            };

            GameUIAgentBuildIrResult result = backendBridge.BuildIr(bridgeRequest);
            return new GameUIAgentToolResponse
            {
                tool_name = "build_ir",
                status = "ok",
                payload_json = JsonUtility.ToJson(result)
            };
        }

        private static string ResolveSetting(string explicitValue, string envName)
        {
            return string.IsNullOrWhiteSpace(explicitValue)
                ? Environment.GetEnvironmentVariable(envName)
                : explicitValue;
        }

        [Serializable]
        private sealed class BuildIrArguments
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
}
