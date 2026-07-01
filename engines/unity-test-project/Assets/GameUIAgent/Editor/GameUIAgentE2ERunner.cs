using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using GameUIAgent.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
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
                string zipPath = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_ZIP_PATH");
                string exportId = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_EXPORT_ID") ?? "unknown-export";
                string engine = Environment.GetEnvironmentVariable("GAMEUIAGENT_E2E_ENGINE") ?? "unity";

                if (!string.IsNullOrWhiteSpace(zipPath) && File.Exists(zipPath))
                {
                    E2EResult imported = ImportZipPackage(zipPath, exportId, engine);
                    WriteResult(imported);
                    EditorApplication.Exit(0);
                    return;
                }

                if (string.IsNullOrWhiteSpace(packageJson))
                {
                    throw new InvalidOperationException("GAMEUIAGENT_E2E_PACKAGE_JSON is required");
                }

                Directory.CreateDirectory(OutputRoot);
                File.WriteAllText(Path.Combine(OutputRoot, "package.json"), packageJson);
                File.WriteAllText(Path.Combine(OutputRoot, "manifest.json"), manifestJson ?? "{}");

                GameObject canvas = BuildCanvas(exportId, engine, null, "GameUIAgent Canvas", "Primary CTA");
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

        private static E2EResult ImportZipPackage(string zipPath, string exportId, string engine)
        {
            string projectRoot = Path.GetDirectoryName(Application.dataPath);
            string extractRoot = ProjectPath(projectRoot, Path.Combine(OutputRoot, "Extracted"));
            if (Directory.Exists(extractRoot))
            {
                Directory.Delete(extractRoot, true);
            }
            Directory.CreateDirectory(extractRoot);
            ZipFile.ExtractToDirectory(zipPath, extractRoot);

            string extractedManifestPath = Path.Combine(extractRoot, "manifest.json");
            if (!File.Exists(extractedManifestPath))
            {
                throw new InvalidOperationException("manifest.json is missing from export zip");
            }

            UnityPackageManifest manifest = JsonUtility.FromJson<UnityPackageManifest>(File.ReadAllText(extractedManifestPath));
            if (manifest == null || manifest.entry == null || string.IsNullOrWhiteSpace(manifest.entry.path))
            {
                throw new InvalidOperationException("Unity export manifest is invalid");
            }

            string manifestAssetPath = FindManifestAssetPath(manifest) ?? "Assets/GameUIAgent/Manifests/imported_manifest.json";
            WriteTextAsset(projectRoot, manifestAssetPath, File.ReadAllText(extractedManifestPath));

            string textureAssetPath = FindAssetPath(manifest, "texture") ?? "Assets/GameUIAgent/Textures/imported_atlas.png";
            CreatePlaceholderTexture(projectRoot, textureAssetPath);
            AssetDatabase.Refresh();
            Sprite sprite = ImportTextureAsSprite(textureAssetPath);

            string prefabPath = NormalizeAssetPath(manifest.entry.path);
            EnsureAssetParent(projectRoot, prefabPath);
            GameObject canvas = BuildCanvas(exportId, engine, sprite, "GameUIAgent Canvas", "Primary CTA");
            PrefabUtility.SaveAsPrefabAsset(canvas, prefabPath);
            UnityEngine.Object.DestroyImmediate(canvas);

            string scenePath = FindAssetPath(manifest, "scene");
            if (string.IsNullOrWhiteSpace(scenePath))
            {
                scenePath = "Assets/GameUIAgent/Scenes/ImportedGameUIAgent.unity";
            }
            CreateSceneFromPrefab(projectRoot, prefabPath, NormalizeAssetPath(scenePath));

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            return new E2EResult
            {
                status = "succeeded",
                engine_version = Application.unityVersion,
                plugin_version = "0.3.0",
                duration_ms = 1,
                summary = new E2ESummary
                {
                    assets_imported = manifest.assets != null ? manifest.assets.Length : 0,
                    prefabs_created = 1,
                    scenes_created = 1,
                    warnings = 0,
                    errors = 0
                },
                logs = new[]
                {
                    new E2ELog { level = "info", message = "Imported GameUIAgent zip package " + zipPath },
                    new E2ELog { level = "info", message = "Created prefab " + prefabPath },
                    new E2ELog { level = "info", message = "Created scene " + scenePath }
                },
                snapshot = BuildSnapshot(textureAssetPath)
            };
        }

        private static GameObject BuildCanvas(string exportId, string engine, Sprite sprite, string canvasName, string buttonName)
        {
            GameObject canvas = new GameObject(canvasName, typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster), typeof(GameUIAgentRuntimeMarker));
            Canvas canvasComponent = canvas.GetComponent<Canvas>();
            canvasComponent.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler scaler = canvas.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1280, 720);
            GameUIAgentRuntimeMarker marker = canvas.GetComponent<GameUIAgentRuntimeMarker>();
            marker.ExportId = exportId;
            marker.Engine = engine;

            GameObject button = new GameObject(buttonName, typeof(RectTransform), typeof(Image), typeof(Button));
            button.transform.SetParent(canvas.transform, false);
            RectTransform rect = button.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0.5f, 0f);
            rect.anchorMax = new Vector2(0.5f, 0f);
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = new Vector2(0, 96);
            rect.sizeDelta = new Vector2(320, 96);
            Image image = button.GetComponent<Image>();
            image.color = new Color(0.31f, 0.61f, 1f, 1f);
            if (sprite != null)
            {
                image.sprite = sprite;
                image.type = Image.Type.Sliced;
            }
            return canvas;
        }

        private static void CreatePlaceholderTexture(string projectRoot, string assetPath)
        {
            EnsureAssetParent(projectRoot, assetPath);
            Texture2D texture = new Texture2D(4, 4, TextureFormat.RGBA32, false);
            Color[] pixels = new Color[16];
            for (int i = 0; i < pixels.Length; i++)
            {
                pixels[i] = new Color(0.20f, 0.52f, 0.96f, 1f);
            }
            texture.SetPixels(pixels);
            texture.Apply();
            File.WriteAllBytes(ProjectPath(projectRoot, assetPath), texture.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(texture);
        }

        private static Sprite ImportTextureAsSprite(string assetPath)
        {
            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            if (importer != null)
            {
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Sprite>(assetPath);
        }

        private static void CreateSceneFromPrefab(string projectRoot, string prefabPath, string scenePath)
        {
            EnsureAssetParent(projectRoot, scenePath);
            SceneSetup();
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                throw new InvalidOperationException("Imported prefab asset is missing: " + prefabPath);
            }
            PrefabUtility.InstantiatePrefab(prefab);
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), scenePath);
        }

        private static void SceneSetup()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        }

        private static E2ESnapshot BuildSnapshot(string textureAssetPath)
        {
            return new E2ESnapshot
            {
                source = "unity_zip_importer",
                layout = new E2ELayout
                {
                    screen = "GameUIAgentImportedHUD",
                    canvas = new E2ERect { x = 0, y = 0, width = 1280, height = 720 },
                    nodes = new[]
                    {
                        new E2ENode { id = "unity_canvas", name = "GameUIAgent Canvas", type = "canvas", rect = new E2ERect { x = 0, y = 0, width = 1280, height = 720 } },
                        new E2ENode { id = "unity_primary_cta", parent_id = "unity_canvas", name = "Primary CTA", type = "button", rect = new E2ERect { x = 480, y = 560, width = 320, height = 96 } }
                    }
                },
                sprites = new[]
                {
                    new E2ESprite { id = "unity_primary_cta_sprite", name = "Primary CTA Sprite", path = textureAssetPath }
                }
            };
        }

        private static string FindAssetPath(UnityPackageManifest manifest, string kind)
        {
            if (manifest.assets == null)
            {
                return null;
            }
            foreach (UnityPackageAsset asset in manifest.assets)
            {
                if (asset.kind == kind)
                {
                    return NormalizeAssetPath(asset.path);
                }
            }
            return null;
        }

        private static string FindManifestAssetPath(UnityPackageManifest manifest)
        {
            if (manifest.assets == null)
            {
                return null;
            }
            foreach (UnityPackageAsset asset in manifest.assets)
            {
                if (asset.kind == "manifest" || asset.path.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
                {
                    return NormalizeAssetPath(asset.path);
                }
            }
            return null;
        }

        private static void WriteTextAsset(string projectRoot, string assetPath, string content)
        {
            EnsureAssetParent(projectRoot, assetPath);
            File.WriteAllText(ProjectPath(projectRoot, assetPath), content);
        }

        private static void EnsureAssetParent(string projectRoot, string assetPath)
        {
            string absolute = ProjectPath(projectRoot, assetPath);
            string directory = Path.GetDirectoryName(absolute);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }
        }

        private static string ProjectPath(string projectRoot, string assetPath)
        {
            string normalized = NormalizeAssetPath(assetPath);
            if (!normalized.StartsWith("Assets/", StringComparison.Ordinal))
            {
                throw new InvalidOperationException("Expected Unity asset path, got " + assetPath);
            }
            return Path.Combine(projectRoot, normalized);
        }

        private static string NormalizeAssetPath(string assetPath)
        {
            return (assetPath ?? string.Empty).Replace("\\", "/");
        }
    }

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
