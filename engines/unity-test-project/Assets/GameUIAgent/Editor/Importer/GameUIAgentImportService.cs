using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentImportService
    {
        private const string OutputRoot = "Assets/GameUIAgent/Generated";

        private readonly GameUIAgentAssetMaterializer assetMaterializer = new GameUIAgentAssetMaterializer();
        private readonly GameUIAgentPrefabBuilder prefabBuilder = new GameUIAgentPrefabBuilder();
        private readonly GameUIAgentSceneBuilder sceneBuilder = new GameUIAgentSceneBuilder();
        private readonly GameUIAgentSnapshotBuilder snapshotBuilder = new GameUIAgentSnapshotBuilder();

        public GameUIAgentImportResult Import(GameUIAgentImportRequest request)
        {
            if (!string.IsNullOrWhiteSpace(request.zip_path) && File.Exists(request.zip_path))
            {
                return ImportZipPackage(request);
            }
            return ImportPackageJson(request);
        }

        private GameUIAgentImportResult ImportZipPackage(GameUIAgentImportRequest request)
        {
            string projectRoot = Path.GetDirectoryName(Application.dataPath);
            string extractRoot = assetMaterializer.ExtractZipPackage(projectRoot, request.zip_path, OutputRoot);
            string extractedManifestPath = Path.Combine(extractRoot, "manifest.json");
            UnityPackageManifest manifest = assetMaterializer.ReadManifest(extractedManifestPath);

            string manifestAssetPath = assetMaterializer.WriteManifestAsset(projectRoot, manifest, extractedManifestPath);
            string textureAssetPath = assetMaterializer.ResolveTextureAssetPath(manifest);
            Sprite sprite = assetMaterializer.MaterializePrimarySprite(projectRoot, textureAssetPath);

            string prefabPath = GameUIAgentPathUtility.NormalizeAssetPath(manifest.entry.path);
            prefabBuilder.SavePrefab(projectRoot, prefabPath, request.export_id, request.engine, sprite, "GameUIAgent Canvas", "Primary CTA");

            string scenePath = assetMaterializer.ResolveSceneAssetPath(manifest);
            sceneBuilder.SaveSceneFromPrefab(projectRoot, prefabPath, GameUIAgentPathUtility.NormalizeAssetPath(scenePath));

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            return new GameUIAgentImportResult
            {
                status = "succeeded",
                engine_version = Application.unityVersion,
                plugin_version = "0.3.0",
                duration_ms = 1,
                summary = new GameUIAgentImportSummary
                {
                    assets_imported = manifest.assets != null ? manifest.assets.Length : 0,
                    prefabs_created = 1,
                    scenes_created = 1,
                    warnings = 0,
                    errors = 0
                },
                logs = new[]
                {
                    new GameUIAgentLogEntry { level = "info", message = "Imported GameUIAgent zip package " + request.zip_path },
                    new GameUIAgentLogEntry { level = "info", message = "Created prefab " + prefabPath },
                    new GameUIAgentLogEntry { level = "info", message = "Created scene " + scenePath }
                },
                snapshot = request.build_snapshot ? snapshotBuilder.BuildImportedSnapshot(textureAssetPath) : null,
                prefab_path = prefabPath,
                scene_path = scenePath,
                manifest_asset_path = manifestAssetPath
            };
        }

        private GameUIAgentImportResult ImportPackageJson(GameUIAgentImportRequest request)
        {
            if (string.IsNullOrWhiteSpace(request.package_json))
            {
                throw new InvalidOperationException("GAMEUIAGENT_E2E_PACKAGE_JSON is required");
            }

            Directory.CreateDirectory(OutputRoot);
            File.WriteAllText(Path.Combine(OutputRoot, "package.json"), request.package_json);
            File.WriteAllText(Path.Combine(OutputRoot, "manifest.json"), request.manifest_json ?? "{}");

            string prefabPath = Path.Combine(OutputRoot, "GameUIAgent_E2E_HUD.prefab").Replace("\\", "/");
            prefabBuilder.SavePrefab(null, prefabPath, request.export_id, request.engine, null, "GameUIAgent Canvas", "Primary CTA");
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            return new GameUIAgentImportResult
            {
                status = "succeeded",
                engine_version = Application.unityVersion,
                plugin_version = "0.3.0",
                duration_ms = 1,
                summary = new GameUIAgentImportSummary
                {
                    assets_imported = 2,
                    prefabs_created = 1,
                    scenes_created = 0,
                    warnings = 0,
                    errors = 0
                },
                logs = new[]
                {
                    new GameUIAgentLogEntry { level = "info", message = "Imported GameUIAgent package into Unity test project" },
                    new GameUIAgentLogEntry { level = "info", message = "Created prefab " + prefabPath }
                },
                snapshot = request.build_snapshot ? snapshotBuilder.BuildBatchmodeSnapshot("Assets/GameUIAgent/Generated/primary_cta.png") : null,
                prefab_path = prefabPath
            };
        }
    }
}
