using System;

namespace GameUIAgent.Editor
{
    [Serializable]
    public sealed class GameUIAgentSnapshot
    {
        public string source;
        public GameUIAgentLayout layout;
        public GameUIAgentSprite[] sprites;
    }

    [Serializable]
    public sealed class GameUIAgentLayout
    {
        public string screen;
        public GameUIAgentRect canvas;
        public GameUIAgentNode[] nodes;
    }

    [Serializable]
    public sealed class GameUIAgentNode
    {
        public string id;
        public string parent_id;
        public string name;
        public string type;
        public GameUIAgentRect rect;
    }

    [Serializable]
    public sealed class GameUIAgentRect
    {
        public int x;
        public int y;
        public int width;
        public int height;
    }

    [Serializable]
    public sealed class GameUIAgentSprite
    {
        public string id;
        public string name;
        public string path;
    }
}
