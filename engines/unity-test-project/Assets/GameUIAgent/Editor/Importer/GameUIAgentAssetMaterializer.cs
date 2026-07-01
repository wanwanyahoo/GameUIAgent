using System;
using System.IO;
using System.IO.Compression;
using UnityEditor;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentAssetMaterializer
    {
        public string ExtractZipPackage(string projectRoot, string zipPath, string outputRoot)
        {
            string extractRoot = GameUIAgentPathUtility.ProjectPath(projectRoot, Path.Combine(outputRoot, "Extracted"));
            if (Directory.Exists(extractRoot))
            {
                Directory.Delete(extractRoot, true);
            }
            Directory.CreateDirectory(extractRoot);
            ZipFile.ExtractToDirectory(zipPath, extractRoot);
            return extractRoot;
        }

        public UnityPackageManifest ReadManifest(string manifestPath)
        {
            if (!File.Exists(manifestPath))
            {
                throw new InvalidOperationException("manifest.json is missing from export zip");
            }

            UnityPackageManifest manifest = JsonUtility.FromJson<UnityPackageManifest>(File.ReadAllText(manifestPath));
            if (manifest == null || manifest.entry == null || string.IsNullOrWhiteSpace(manifest.entry.path))
            {
                throw new InvalidOperationException("Unity export manifest is invalid");
            }
            return manifest;
        }

        public string WriteManifestAsset(string projectRoot, UnityPackageManifest manifest, string manifestPath)
        {
            string manifestAssetPath = FindManifestAssetPath(manifest);
            if (string.IsNullOrWhiteSpace(manifestAssetPath))
            {
                manifestAssetPath = "Assets/GameUIAgent/Manifests/imported_manifest.json";
            }

            GameUIAgentPathUtility.EnsureAssetParent(projectRoot, manifestAssetPath);
            File.WriteAllText(GameUIAgentPathUtility.ProjectPath(projectRoot, manifestAssetPath), File.ReadAllText(manifestPath));
            return manifestAssetPath;
        }

        public string ResolveTextureAssetPath(UnityPackageManifest manifest)
        {
            string textureAssetPath = FindAssetPath(manifest, "texture");
            if (string.IsNullOrWhiteSpace(textureAssetPath))
            {
                textureAssetPath = "Assets/GameUIAgent/Textures/imported_atlas.png";
            }
            return textureAssetPath;
        }

        public string ResolveSceneAssetPath(UnityPackageManifest manifest)
        {
            string sceneAssetPath = FindAssetPath(manifest, "scene");
            if (string.IsNullOrWhiteSpace(sceneAssetPath))
            {
                sceneAssetPath = "Assets/GameUIAgent/Scenes/ImportedGameUIAgent.unity";
            }
            return sceneAssetPath;
        }

        public Sprite MaterializePrimarySprite(string projectRoot, string assetPath)
        {
            CreatePlaceholderTexture(projectRoot, assetPath);
            AssetDatabase.Refresh();
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

        private static void CreatePlaceholderTexture(string projectRoot, string assetPath)
        {
            GameUIAgentPathUtility.EnsureAssetParent(projectRoot, assetPath);
            Texture2D texture = new Texture2D(4, 4, TextureFormat.RGBA32, false);
            Color[] pixels = new Color[16];
            for (int index = 0; index < pixels.Length; index++)
            {
                pixels[index] = new Color(0.20f, 0.52f, 0.96f, 1f);
            }
            texture.SetPixels(pixels);
            texture.Apply();
            File.WriteAllBytes(GameUIAgentPathUtility.ProjectPath(projectRoot, assetPath), texture.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(texture);
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
                    return GameUIAgentPathUtility.NormalizeAssetPath(asset.path);
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
                    return GameUIAgentPathUtility.NormalizeAssetPath(asset.path);
                }
            }
            return null;
        }
    }
}
