using System;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentMcpDispatcher
    {
        private readonly GameUIAgentMcpToolRegistry registry = new GameUIAgentMcpToolRegistry();

        public GameUIAgentToolResponse Dispatch(GameUIAgentToolRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.tool_name))
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = string.Empty,
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = "tool_name is required"
                };
            }

            try
            {
                object tool = registry.Resolve(request.tool_name);
                if (tool == null)
                {
                    return new GameUIAgentToolResponse
                    {
                        tool_name = request.tool_name,
                        status = "error",
                        error_code = "UNKNOWN_TOOL",
                        error_message = "Unknown tool: " + request.tool_name
                    };
                }

                if (tool is GameUIAgentImportPackageTool importTool)
                {
                    return importTool.Execute(request);
                }

                if (tool is GameUIAgentBuildSnapshotTool snapshotTool)
                {
                    return snapshotTool.Execute(request);
                }

                return new GameUIAgentToolResponse
                {
                    tool_name = request.tool_name,
                    status = "error",
                    error_code = "INTERNAL_ERROR",
                    error_message = "Resolved tool does not support execution"
                };
            }
            catch (ArgumentException ex)
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = request.tool_name,
                    status = "error",
                    error_code = "INVALID_ARGUMENTS",
                    error_message = ex.Message
                };
            }
            catch (Exception ex)
            {
                return new GameUIAgentToolResponse
                {
                    tool_name = request.tool_name,
                    status = "error",
                    error_code = "INTERNAL_ERROR",
                    error_message = ex.Message
                };
            }
        }
    }
}
