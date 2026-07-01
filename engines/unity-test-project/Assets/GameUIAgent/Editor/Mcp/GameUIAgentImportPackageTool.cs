using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentImportPackageTool
    {
        private readonly GameUIAgentImportService importService = new GameUIAgentImportService();
        public GameUIAgentToolDescriptor Descriptor => new GameUIAgentToolDescriptor
        {
            name = "import_package",
            description = "Import a GameUIAgent export package into Unity.",
            input_schema_json = "{\"type\":\"object\",\"required\":[\"export_id\",\"engine\",\"zip_path\"]}"
        };

        public GameUIAgentToolResponse Execute(GameUIAgentToolRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.arguments_json))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "import_package",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "import_package requires arguments_json"
                };
            }

            ImportPackageArguments arguments = JsonUtility.FromJson<ImportPackageArguments>(request.arguments_json);
            if (arguments == null || string.IsNullOrWhiteSpace(arguments.export_id) || string.IsNullOrWhiteSpace(arguments.engine) || string.IsNullOrWhiteSpace(arguments.zip_path))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = "import_package",
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "import_package requires export_id, engine, and zip_path"
                };
            }

            GameUIAgentImportResult result = importService.Import(new GameUIAgentImportRequest
            {
                export_id = arguments.export_id,
                engine = arguments.engine,
                zip_path = arguments.zip_path,
                build_scene = true,
                build_snapshot = true
            });

            return new GameUIAgentToolResponse
            {
                tool_name = "import_package",
                status = "ok",
                payload_json = JsonUtility.ToJson(result)
            };
        }

        [System.Serializable]
        private sealed class ImportPackageArguments
        {
            public string export_id;
            public string engine;
            public string zip_path;
        }
    }
}
