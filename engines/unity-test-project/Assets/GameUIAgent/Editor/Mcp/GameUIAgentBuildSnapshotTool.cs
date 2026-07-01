namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentBuildSnapshotTool
    {
        private readonly GameUIAgentSnapshotBuilder snapshotBuilder = new GameUIAgentSnapshotBuilder();

        public GameUIAgentSnapshot BuildSnapshot(string textureAssetPath)
        {
            return snapshotBuilder.BuildImportedSnapshot(textureAssetPath);
        }
    }
}
