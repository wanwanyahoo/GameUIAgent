namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentMcpToolRegistry
    {
        private readonly GameUIAgentImportPackageTool importPackageTool = new GameUIAgentImportPackageTool();
        private readonly GameUIAgentBuildSnapshotTool buildSnapshotTool = new GameUIAgentBuildSnapshotTool();
        private readonly GameUIAgentBuildIrTool buildIrTool = new GameUIAgentBuildIrTool();

        public GameUIAgentToolDescriptor[] ListTools()
        {
            return new[]
            {
                importPackageTool.Descriptor,
                buildSnapshotTool.Descriptor,
                buildIrTool.Descriptor
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
            if (toolName == "build_ir")
            {
                return buildIrTool;
            }
            return null;
        }
    }
}
