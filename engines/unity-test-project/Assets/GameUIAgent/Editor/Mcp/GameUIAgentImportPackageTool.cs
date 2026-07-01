namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentImportPackageTool
    {
        private readonly GameUIAgentImportService importService = new GameUIAgentImportService();

        public GameUIAgentImportResult ImportPackage(string exportId, string engine, string zipPath)
        {
            return importService.Import(new GameUIAgentImportRequest
            {
                export_id = exportId,
                engine = engine,
                zip_path = zipPath,
                build_scene = true,
                build_snapshot = true
            });
        }
    }
}
