# Unity MCP Local AI Studio Design

## Goal

Add the next Unity-side layer that is directly relevant to the AI Studio UI closed loop:

- Unity local MCP-style tool execution
- tool coverage limited to `import_package` and `build_snapshot`
- shared execution on top of the existing importer package

This design intentionally excludes any website capabilities that are not directly required for the AI Studio UI closed loop.

## Why This Scope

The project already has:

- a real Unity importer core
- a thin batchmode runner
- Unity-side facade classes for import and snapshot

What is still missing is a real local execution layer that behaves like MCP tooling instead of a few ad hoc C# helper classes.

For the AI Studio UI closed loop, the minimum meaningful next step is:

1. AI Studio produces export output
2. Unity can execute a local `import_package` tool
3. Unity can execute a local `build_snapshot` tool
4. both tools return structured responses through a unified dispatcher

Anything beyond that in this round would dilute focus away from the AI Studio-related loop.

## Scope

Included:

- Unity local MCP-style request and response contracts
- Unity local tool registry
- Unity local dispatcher
- Unity local execution entrypoints for:
  - `import_package`
  - `build_snapshot`
- menu-based local validation entrypoints inside Unity Editor
- tests for local tool listing, dispatch, structured errors, and tool execution boundaries

Excluded:

- website features unrelated to AI Studio UI
- Unity EditorWindow plugin panel
- remote MCP transport/session layer
- `build_ir`
- `restyle`
- plugin networking
- account, billing, marketing, docs-center, and other non-AI-Studio site work

## Desired Closed Loop

This round only targets the following direct loop:

1. AI Studio UI prepares an export package
2. Unity local MCP layer runs `import_package`
3. importer core creates Unity-native outputs
4. Unity local MCP layer runs `build_snapshot`
5. Unity returns structured tool responses

This establishes the Unity-side tool execution boundary required for future AI Studio-to-Unity integration without dragging in unrelated product areas.

## Architecture

### Existing Base

The current Unity structure already contains:

- `Contracts`
- `Importer`
- `Mcp`
- `Batchmode`

This round extends the `Mcp` layer so it becomes a real local execution layer rather than a thin collection of helper wrappers.

### New Local MCP Layer

The Unity-side MCP local layer is split into:

1. tool contracts
2. tool registry
3. dispatcher
4. tool implementations
5. local validation entrypoints

All real business behavior must still flow through the existing importer core or snapshot builder.

### Contracts

Add under `Assets/GameUIAgent/Editor/Contracts/`:

- `GameUIAgentToolRequest.cs`
- `GameUIAgentToolResponse.cs`
- `GameUIAgentToolDescriptor.cs`

Responsibilities:

- define stable local tool invocation shape
- separate tool transport concerns from importer concerns
- provide structured success and error payloads

Recommended shape:

```csharp
public sealed class GameUIAgentToolRequest
{
    public string tool_name;
    public string arguments_json;
}
```

```csharp
public sealed class GameUIAgentToolResponse
{
    public string tool_name;
    public string status;
    public string error_code;
    public string error_message;
    public string payload_json;
}
```

```csharp
public sealed class GameUIAgentToolDescriptor
{
    public string name;
    public string description;
    public string input_schema_json;
}
```

These contracts are only for the Unity local MCP execution layer in this round.

### Registry

Upgrade `Assets/GameUIAgent/Editor/Mcp/GameUIAgentMcpToolRegistry.cs` into a real registry.

Required responsibilities:

- list all supported tool descriptors
- resolve a tool by name
- expose only tools that belong to the AI Studio UI closed loop for this round

For this round, the registry must expose exactly:

- `import_package`
- `build_snapshot`

It must not expose speculative future tools such as `build_ir` or `restyle`.

### Dispatcher

Add:

- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentMcpDispatcher.cs`

Responsibilities:

- accept `GameUIAgentToolRequest`
- resolve target tool through the registry
- validate arguments
- execute the tool
- catch exceptions and convert them into structured `GameUIAgentToolResponse`

Key rule:

- no tool-specific import logic inside dispatcher
- dispatcher only coordinates registry lookup, argument handling, execution, and error normalization

### Tool Implementations

Use and upgrade the existing tools:

- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentImportPackageTool.cs`
- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentBuildSnapshotTool.cs`

Required changes:

- align both tools to a unified request and response shape
- stop exposing ad hoc public methods as the primary interface
- make both tools invocable through dispatcher

#### `import_package`

Input:

- `export_id`
- `engine`
- `zip_path`

Behavior:

- build `GameUIAgentImportRequest`
- call `GameUIAgentImportService`
- wrap the result inside `GameUIAgentToolResponse`

Output payload:

- importer result JSON
- includes snapshot when importer produced one

#### `build_snapshot`

Input:

- current round keeps this intentionally local and minimal
- accepted input is a Unity-local asset context, initially `texture_asset_path`

Behavior:

- call `GameUIAgentSnapshotBuilder`
- wrap the snapshot inside `GameUIAgentToolResponse`

Output payload:

- snapshot JSON

This tool remains intentionally narrow in this round. It exists to complete the AI Studio-related Unity readback boundary, not to solve every future scene-inspection case yet.

### Local Validation Entrypoints

Add Unity menu commands under a new entrypoint class, for example:

- `GameUIAgent/MCP/List Tools`
- `GameUIAgent/MCP/Run Import Package`
- `GameUIAgent/MCP/Run Build Snapshot`

Purpose:

- validate that the local MCP execution layer is real and usable
- allow manual verification inside Unity Editor without building the full plugin panel

These menu commands are validation and developer tooling only. They are not the final plugin UX.

## Data Flow

### Import Flow

1. caller builds `GameUIAgentToolRequest` with `tool_name = import_package`
2. dispatcher resolves `GameUIAgentImportPackageTool`
3. tool validates arguments
4. tool builds `GameUIAgentImportRequest`
5. importer core executes import
6. tool wraps result as `GameUIAgentToolResponse`

### Snapshot Flow

1. caller builds `GameUIAgentToolRequest` with `tool_name = build_snapshot`
2. dispatcher resolves `GameUIAgentBuildSnapshotTool`
3. tool validates arguments
4. tool calls snapshot builder
5. tool wraps result as `GameUIAgentToolResponse`

## Error Handling

The local MCP layer must return structured errors for:

- unknown tool name
- malformed request arguments
- missing zip path
- invalid import inputs
- snapshot build failure
- internal execution exceptions

Recommended normalized error codes:

- `UNKNOWN_TOOL`
- `INVALID_ARGUMENTS`
- `IMPORT_FAILED`
- `SNAPSHOT_FAILED`
- `INTERNAL_ERROR`

Key rule:

- no fake success responses
- all failures must preserve stage-specific meaning

## Testing Strategy

This round must follow TDD.

### RED Tests First

Add failing tests for:

- registry returns descriptors rather than raw object arrays
- dispatcher resolves and executes `import_package`
- dispatcher resolves and executes `build_snapshot`
- unknown tool returns structured `UNKNOWN_TOOL`
- malformed arguments return structured `INVALID_ARGUMENTS`
- tool source remains thin and continues to call shared importer or snapshot builder

### GREEN Implementation

Minimal code required to satisfy the tests:

- add tool contracts
- add dispatcher
- upgrade registry
- upgrade `import_package`
- upgrade `build_snapshot`
- add local menu entrypoints

### Regression Verification

Run:

```bash
python3 -m pytest backend/tests/test_product_flow.py -q -k "unity_test_project_contains_real_plugin_and_batchmode_runner or real_engine_e2e_runner_executes_editor"
python3 -m pytest backend/tests -q
git diff --check
```

### Unity Validation

Manual or scripted Unity validation must confirm:

- `List Tools` shows only the two intended tools
- `import_package` still succeeds through shared importer core
- `build_snapshot` returns structured snapshot response
- batchmode import path still works unchanged

## Compatibility Requirements

This round must preserve:

- current batchmode runner behavior
- current importer core behavior
- current backend engine E2E endpoint
- current Unity zip importer success semantics

This round must not require backend changes for unrelated website areas.

## Risks

- dispatcher may accidentally duplicate business logic
- registry may drift into exposing tools outside the round scope
- local validation entrypoints may start turning into an accidental plugin UI

Mitigations:

- keep dispatcher orchestration-only
- hard-limit the registry to `import_package` and `build_snapshot`
- keep menu commands minimal and validation-focused

## Success Criteria

This design is successful when:

- Unity has a real local MCP execution layer, not just facade classes
- only AI Studio UI-related Unity tools are implemented in this round
- `import_package` and `build_snapshot` both execute through dispatcher
- responses are structured and normalized
- current importer and batchmode flows remain green
- no unrelated website features are added
