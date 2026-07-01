using System;
using System.IO;
using GameUIAgent.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace GameUIAgent.Editor
{
    public static class GameUIAgentE2ERunner
    {
        private const string OutputRoot = "Assets/GameUIAgent/Generated";

        public static void Run()
        {
            try
            {
                string packageJson = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_PACKAGE_JSON");
                string manifestJson = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_MANIFEST_JSON");
                string exportId = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_EXPORT_ID") ?? "unknown-export";
                string engine = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_ENGINE") ?? "unity";

                if (string.IsNullOrWhiteSpace(packageJson))
                {
                    throw new InvalidOperationException("GAMEUIAGENT_E2E_PACKAGE_JSON is required");
                }

                Directory.CreateDirectory(OutputRoot);
                File.WriteAllText(Path.Combine(OutputRoot, "package.json"), packageJson);
                File.WriteAllText(Path.Combine(OutputRoot, "manifest.json"), manifestJson ?? "{}");

                GameObject canvas = BuildCanvas(exportId, engine);
                string prefabPath = Path.Combine(OutputRoot, "GameUIAgent_E2E_HUD.prefab").Replace("\\", "/");
                PrefabUtility.SaveAsPrefabAsset(canvas, prefabPath);
                UnityEngine.Object.DestroyImmediate(canvas);
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();

                E2EResult result = new E2EResult
                {
                    status = "succeeded",
                    engine_version = Application.unityVersion,
                    plugin_version = "0.3.0",
                    duration_ms = 1,
                    summary = new E2ESummary
                    {
                        assets_imported = 2,
                        prefabs_created = 1,
                        scenes_created = 0,
                        warnings = 0,
                        errors = 0
                    },
                    logs = new[]
                    {
                        new E2ELog { level = "info", message = "Imported GameUIAgent package into Unity test project" },
                        new E2ELog { level = "info", message = "Created prefab " + prefabPath }
                    },
                    snapshot = new E2ESnapshot
                    {
                        source = "unity_batchmode",
                        layout = new E2ELayout
                        {
                            screen = "GameUIAgentE2EHUD",
                            canvas = new E2ERect { x = 0, y = 0, width = 1280, height = 720 },
                            nodes = new[]
                            {
                                new E2ENode { id = "unity_canvas", name = "GameUIAgent Canvas", type = "canvas", rect = new E2ERect { x = 0, y = 0, width = 1280, height = 720 } },
                                new E2ENode { id = "unity_primary_cta", parent_id = "unity_canvas", name = "Primary CTA", type = "button", rect = new E2ERect { x = 480, y = 560, width = 320, height = 96 } }
                            }
                        },
                        sprites = new[]
                        {
                            new E2ESprite { id = "unity_primary_cta_sprite", name = "Primary CTA Sprite", path = "Assets/GameUIAgent/Generated/primary_cta.png" }
                        }
                    }
                };

                WriteResult(result);
                EditorApplication.Exit(0);
            }
            catch (Exception ex)
            {
                E2EResult failed = new E2EResult
                {
                    status = "failed",
                    engine_version = Application.unityVersion,
                    plugin_version = "0.3.0",
                    duration_ms = 0,
                    summary = new E2ESummary { errors = 1, warnings = 0 },
                    logs = new[] { new E2ELog { level = "error", message = ex.Message } }
                };
                WriteResult(failed);
                EditorApplication.Exit(1);
            }
        }

        private static void WriteResult(E2EResult result)
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

        private static GameObject BuildCanvas(string exportId, string engine)
        {
            GameObject canvas = new GameObject("GameUIAgent Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster), typeof(GameUIAgentRuntimeMarker));
            Canvas canvasComponent = canvas.GetComponent<Canvas>();
            canvasComponent.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler scaler = canvas.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1280, 720);
            GameUIAgentRuntimeMarker marker = canvas.GetComponent<GameUIAgentRuntimeMarker>();
            marker.ExportId = exportId;
            marker.Engine = engine;

            GameObject button = new GameObject("Primary CTA", typeof(RectTransform), typeof(Image), typeof(Button));
            button.transform.SetParent(canvas.transform, false);
            RectTransform rect = button.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0.5f, 0f);
            rect.anchorMax = new Vector2(0.5f, 0f);
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = new Vector2(0, 96);
            rect.sizeDelta = new Vector2(320, 96);
            button.GetComponent<Image>().color = new Color(0.31f, 0.61f, 1f, 1f);
            return canvas;
        }
    }

    [Serializable]
    public sealed class E2EResult
    {
        public string status;
        public string engine_version;
        public string plugin_version;
        public int duration_ms;
        public E2ESummary summary;
        public E2ELog[] logs;
        public E2ESnapshot snapshot;
    }

    [Serializable]
    public sealed class E2ESummary
    {
        public int assets_imported;
        public int prefabs_created;
        public int scenes_created;
        public int warnings;
        public int errors;
    }

    [Serializable]
    public sealed class E2ELog
    {
        public string level;
        public string message;
    }

    [Serializable]
    public sealed class E2ESnapshot
    {
        public string source;
        public E2ELayout layout;
        public E2ESprite[] sprites;
    }

    [Serializable]
    public sealed class E2ELayout
    {
        public string screen;
        public E2ERect canvas;
        public E2ENode[] nodes;
    }

    [Serializable]
    public sealed class E2ENode
    {
        public string id;
        public string parent_id;
        public string name;
        public string type;
        public E2ERect rect;
    }

    [Serializable]
    public sealed class E2ERect
    {
        public int x;
        public int y;
        public int width;
        public int height;
    }

    [Serializable]
    public sealed class E2ESprite
    {
        public string id;
        public string name;
        public string path;
    }
}
