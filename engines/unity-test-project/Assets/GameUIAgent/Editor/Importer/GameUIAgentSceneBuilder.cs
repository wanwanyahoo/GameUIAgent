using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentSceneBuilder
    {
        public string SaveSceneFromPrefab(string projectRoot, string prefabPath, string scenePath)
        {
            GameUIAgentPathUtility.EnsureAssetParent(projectRoot, scenePath);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                throw new InvalidOperationException("Imported prefab asset is missing: " + prefabPath);
            }

            PrefabUtility.InstantiatePrefab(prefab);
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), scenePath);
            return scenePath;
        }
    }
}
