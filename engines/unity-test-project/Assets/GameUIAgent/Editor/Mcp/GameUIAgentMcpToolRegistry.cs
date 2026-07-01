namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentMcpToolRegistry
    {
        private readonly GameUIAgentImportPackageTool importPackageTool = new GameUIAgentImportPackageTool();
        private readonly GameUIAgentBuildSnapshotTool buildSnapshotTool = new GameUIAgentBuildSnapshotTool();

        public GameUIAgentToolDescriptor[] ListTools()
        {
            return new[]
            {
                importPackageTool.Descriptor,
                buildSnapshotTool.Descriptor
            };
        }

        public object Resolve(string toolName)
        {
            if (toolName == "import_package")
            {
                return importPackageTool;
            }
            if (toolName == "build_snapshot")
            {
                return buildSnapshotTool;
            }
            return null;
        }
    }
}
