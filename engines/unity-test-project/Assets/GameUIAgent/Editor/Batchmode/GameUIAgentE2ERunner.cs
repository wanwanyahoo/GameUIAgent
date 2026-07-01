using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public static class GameUIAgentE2ERunner
    {
        private static readonly GameUIAgentImportService importService = new GameUIAgentImportService();

        public static void Run()
        {
            try
            {
                GameUIAgentImportRequest request = new GameUIAgentImportRequest
                {
                    package_json = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_PACKAGE_JSON"),
                    manifest_json = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_MANIFEST_JSON"),
                    zip_path = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_ZIP_PATH"),
                    export_id = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_EXPORT_ID") ?? "unknown-export",
                    engine = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_ENGINE") ?? "unity",
                    build_scene = true,
                    build_snapshot = true
                };

                GameUIAgentImportResult imported = importService.Import(request);
                WriteResult(imported);
                EditorApplication.Exit(0);
            }
            catch (Exception ex)
            {
                GameUIAgentImportResult failed = new GameUIAgentImportResult
                {
                    status = "failed",
                    engine_version = Application.unityVersion,
                    plugin_version = "0.3.0",
                    duration_ms = 0,
                    summary = new GameUIAgentImportSummary { errors = 1, warnings = 0 },
                    logs = new[] { new GameUIAgentLogEntry { level = "error", message = ex.Message } }
                };
                WriteResult(failed);
                EditorApplication.Exit(1);
            }
        }

        private static void WriteResult(GameUIAgentImportResult result)
        {
            string json = JsonUtility.ToJson(result);
            string resultPath = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_RESULT_PATH");
            if (!string.IsNullOrWhiteSpace(resultPath))
            {
                string directory = Path.GetDirectoryName(resultPath);
                if (!string.IsNullOrEmpty(directory))
                {
                    Directory.CreateDirectory(directory);
                }
                File.WriteAllText(resultPath, json);
            }
            Console.Out.WriteLine(json);
        }
    }
}
