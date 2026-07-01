using GameUIAgent.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentPrefabBuilder
    {
        public string SavePrefab(string projectRoot, string prefabPath, string exportId, string engine, Sprite sprite, string canvasName, string buttonName)
        {
            GameUIAgentPathUtility.EnsureAssetParent(projectRoot, prefabPath);
            GameObject canvas = BuildCanvas(exportId, engine, sprite, canvasName, buttonName);
            PrefabUtility.SaveAsPrefabAsset(canvas, prefabPath);
            Object.DestroyImmediate(canvas);
            return prefabPath;
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
    }
}
