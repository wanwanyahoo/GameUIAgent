namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentSnapshotBuilder
    {
        public GameUIAgentSnapshot BuildImportedSnapshot(string textureAssetPath)
        {
            return new GameUIAgentSnapshot
            {
                source = "unity_zip_importer",
                layout = new GameUIAgentLayout
                {
                    screen = "GameUIAgentImportedHUD",
                    canvas = new GameUIAgentRect { x = 0, y = 0, width = 1280, height = 720 },
                    nodes = new[]
                    {
                        new GameUIAgentNode
                        {
                            id = "unity_canvas",
                            name = "GameUIAgent Canvas",
                            type = "canvas",
                            rect = new GameUIAgentRect { x = 0, y = 0, width = 1280, height = 720 }
                        },
                        new GameUIAgentNode
                        {
                            id = "unity_primary_cta",
                            parent_id = "unity_canvas",
                            name = "Primary CTA",
                            type = "button",
                            rect = new GameUIAgentRect { x = 480, y = 560, width = 320, height = 96 }
                        }
                    }
                },
                sprites = new[]
                {
                    new GameUIAgentSprite
                    {
                        id = "unity_primary_cta_sprite",
                        name = "Primary CTA Sprite",
                        path = textureAssetPath
                    }
                }
            };
        }

        public GameUIAgentSnapshot BuildBatchmodeSnapshot(string textureAssetPath)
        {
            return new GameUIAgentSnapshot
            {
                source = "unity_batchmode",
                layout = new GameUIAgentLayout
                {
                    screen = "GameUIAgentE2EHUD",
                    canvas = new GameUIAgentRect { x = 0, y = 0, width = 1280, height = 720 },
                    nodes = new[]
                    {
                        new GameUIAgentNode
                        {
                            id = "unity_canvas",
                            name = "GameUIAgent Canvas",
                            type = "canvas",
                            rect = new GameUIAgentRect { x = 0, y = 0, width = 1280, height = 720 }
                        },
                        new GameUIAgentNode
                        {
                            id = "unity_primary_cta",
                            parent_id = "unity_canvas",
                            name = "Primary CTA",
                            type = "button",
                            rect = new GameUIAgentRect { x = 480, y = 560, width = 320, height = 96 }
                        }
                    }
                },
                sprites = new[]
                {
                    new GameUIAgentSprite
                    {
                        id = "unity_primary_cta_sprite",
                        name = "Primary CTA Sprite",
                        path = textureAssetPath
                    }
                }
            };
        }
    }
}
