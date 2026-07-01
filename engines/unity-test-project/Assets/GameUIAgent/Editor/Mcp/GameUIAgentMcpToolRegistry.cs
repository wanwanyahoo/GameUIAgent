namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentMcpToolRegistry
    {
        private readonly GameUIAgentImportPackageTool importPackageTool = new GameUIAgentImportPackageTool();
        private readonly GameUIAgentBuildSnapshotTool buildSnapshotTool = new GameUIAgentBuildSnapshotTool();

        public object[] GetTools()
        {
            return new object[]
            {
                importPackageTool,
                buildSnapshotTool
            };
        }
    }
}
