# Unity Build IR Local Bridge Design

## Goal

Add the next Unity-side capability that is directly required for the AI Studio UI closed loop:

- local Unity MCP tool `build_ir`
- local bridge from Unity to the existing backend `build-ir` endpoint
- no unrelated website features

This round extends the current Unity local MCP layer from:

- `import_package`
- `build_snapshot`

to:

- `import_package`
- `build_snapshot`
- `build_ir`

The specific target loop is:

1. AI Studio creates export output
2. Unity imports package
3. Unity builds snapshot
4. Unity locally invokes `build_ir`
5. backend builds IR from engine snapshot
6. IR is available again for AI Studio-side workflows

## Why This Scope

The project already has:

- backend endpoint for engine snapshot IR construction
- Unity importer core
- Unity local MCP contracts, registry, dispatcher, and menu validation entrypoints

What is still missing is the Unity-side bridge that turns a locally available snapshot into a real `build-ir` backend call.

That bridge is directly related to the AI Studio UI closed loop because it is the path that returns Unity-side state back into Studio-editable IR.

Anything beyond that in this round would dilute focus away from the AI Studio loop.

## Scope

Included:

- Unity local MCP tool `build_ir`
- Unity local backend bridge for the existing backend build-ir flow
- tool request and response shape for `build_ir`
- registry and dispatcher support for `build_ir`
- local validation entrypoint in Unity Editor
- tests covering registry exposure, dispatch, argument validation, and bridge usage

Excluded:

- website features unrelated to AI Studio UI
- `restyle`
- full plugin networking layer
- EditorWindow plugin panel
- remote MCP transport
- generalized bridge for unrelated backend APIs
- marketing, docs, billing, auth, and other non-AI-Studio site work

## Existing Backend Contract

The backend already exposes the relevant endpoint:

- `POST /api/plugin/engine-snapshots/{snapshot_id}/build-ir`

and already implements snapshot-to-IR construction in backend logic.

This round must reuse that existing backend capability rather than inventing a parallel IR-building implementation inside Unity.

## Desired Closed Loop

This round only targets the following AI Studio-related loop:

1. Unity already has a project context and imported package
2. Unity produces or receives a snapshot payload
3. Unity `build_ir` tool sends snapshot context to backend
4. backend builds IR from the engine snapshot
5. Unity receives a structured result payload that references the created IR

This round does not attempt to solve the final Studio UI presentation layer. It only establishes the Unity-to-backend bridge required for that loop.

## Architecture

### Existing Base

The current Unity-side structure already contains:

- `Contracts`
- `Importer`
- `Mcp`
- `Batchmode`

This round adds one more local MCP tool and one backend bridge class.

### New Components

Add the following Unity-side components:

- `Assets/GameUIAgent/Editor/Contracts/GameUIAgentBuildIrRequest.cs`
- `Assets/GameUIAgent/Editor/Contracts/GameUIAgentBuildIrResult.cs`
- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentBuildIrTool.cs`
- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentBackendBridge.cs`

Also update:

- `GameUIAgentMcpToolRegistry`
- `GameUIAgentMcpDispatcher`
- `GameUIAgentMcpMenu`

## Contracts

### Build IR Request

Add `GameUIAgentBuildIrRequest.cs`.

Purpose:

- define the Unity-side request model for the bridge
- keep tool transport concerns separate from bridge concerns

Recommended fields:

```csharp
public sealed class GameUIAgentBuildIrRequest
{
    public string project_id;
    public string engine;
    public string source;
    public string snapshot_json;
    public string snapshot_id;
}
```

Rules:

- at least one of `snapshot_json` or `snapshot_id` must be present
- `project_id` is required
- `engine` is required and should remain `unity` in this round

### Build IR Result

Add `GameUIAgentBuildIrResult.cs`.

Purpose:

- capture the backend response relevant to Studio roundtrip
- give the Unity tool a stable result model

Recommended fields:

```csharp
public sealed class GameUIAgentBuildIrResult
{
    public string project_id;
    public string snapshot_id;
    public string ir_id;
    public string version_id;
    public string status;
    public string payload_json;
}
```

This model can stay intentionally thin as long as it preserves the created IR identity and backend payload.

## Backend Bridge

Add:

- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentBackendBridge.cs`

Responsibilities:

- accept `GameUIAgentBuildIrRequest`
- send the request to the existing backend build-ir flow
- normalize the backend response into `GameUIAgentBuildIrResult`
- convert transport and server errors into structured tool-level failures

Key rules:

- do not rebuild IR inside Unity
- do not invent a separate IR schema inside the bridge
- do not couple the bridge to unrelated website APIs

### Bridge Scope

This round allows the bridge to be narrow and single-purpose:

- only support the backend build-ir path needed for AI Studio roundtrip
- only support Unity engine context

It must not become a generic catch-all backend client in this round.

## Local MCP Tool

Add:

- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentBuildIrTool.cs`

Responsibilities:

- accept `GameUIAgentToolRequest`
- parse `arguments_json`
- validate required arguments
- invoke `GameUIAgentBackendBridge`
- wrap success or failure into `GameUIAgentToolResponse`

Input shape for `build_ir`:

- `project_id`
- `engine`
- either:
  - `snapshot_json`
  - or `snapshot_id`

Output shape:

- `GameUIAgentToolResponse`
- `tool_name = build_ir`
- `payload_json` contains serialized `GameUIAgentBuildIrResult`

## Registry and Dispatcher Changes

### Registry

Update `GameUIAgentMcpToolRegistry` so it exposes exactly:

- `import_package`
- `build_snapshot`
- `build_ir`

Still excluded:

- `restyle`
- unrelated speculative tools

### Dispatcher

Update `GameUIAgentMcpDispatcher` to:

- resolve `build_ir`
- dispatch to `GameUIAgentBuildIrTool`
- keep structured error handling consistent with the existing local MCP tools

Recommended error codes for this round:

- `UNKNOWN_TOOL`
- `INVALID_ARGUMENTS`
- `BRIDGE_FAILED`
- `INTERNAL_ERROR`

## Local Validation Entrypoints

Add one more Unity menu command:

- `GameUIAgent/MCP/Run Build IR`

Purpose:

- validate the local Unity-to-backend bridge
- allow manual testing without building a full plugin panel

This menu command must stay minimal and validation-focused.

## Data Flow

### Snapshot JSON Path

1. Unity tool caller creates `GameUIAgentToolRequest` with `tool_name = build_ir`
2. request contains `project_id`, `engine`, and `snapshot_json`
3. dispatcher resolves `GameUIAgentBuildIrTool`
4. tool validates request
5. tool calls `GameUIAgentBackendBridge`
6. bridge calls backend `build-ir`
7. backend returns IR identity and payload
8. tool wraps result into `GameUIAgentToolResponse`

### Snapshot ID Path

1. Unity tool caller creates `GameUIAgentToolRequest` with `snapshot_id`
2. dispatcher resolves `GameUIAgentBuildIrTool`
3. tool validates request
4. tool calls backend through bridge
5. backend builds IR from the referenced snapshot
6. tool returns structured result

## Error Handling

The `build_ir` local bridge must return structured failures for:

- missing `project_id`
- missing `engine`
- missing both `snapshot_json` and `snapshot_id`
- backend request failure
- backend returns non-success status
- malformed backend response

Recommended normalization:

- `INVALID_ARGUMENTS`
- `BRIDGE_FAILED`
- `INTERNAL_ERROR`

Key rule:

- backend bridge failures must not look like local Unity import failures

## Testing Strategy

This round must follow TDD.

### RED Tests First

Add failing tests for:

- registry exposes `build_ir`
- dispatcher resolves and executes `build_ir`
- `build_ir` tool requires `project_id`
- `build_ir` tool requires `engine`
- `build_ir` tool requires `snapshot_json` or `snapshot_id`
- `build_ir` tool source calls `GameUIAgentBackendBridge`
- menu source contains `GameUIAgent/MCP/Run Build IR`

### GREEN Implementation

Minimal code required:

- add build-ir request/result contracts
- add backend bridge
- add build-ir tool
- update registry
- update dispatcher
- update menu

### Regression Verification

Run:

```bash
python3 -m pytest backend/tests/test_product_flow.py -q -k "unity_test_project_contains_real_plugin_and_batchmode_runner or real_engine_e2e_runner_executes_editor"
python3 -m pytest backend/tests -q
git diff --check
```

### Unity Validation

Validation must confirm:

- Unity still imports packages successfully
- Unity local MCP layer lists `build_ir`
- Unity local `build_ir` returns structured response
- existing `import_package` and `build_snapshot` remain green

## Compatibility Requirements

This round must preserve:

- current batchmode runner behavior
- current importer behavior
- current local MCP dispatcher behavior
- current backend engine E2E behavior

This round must not require unrelated backend or frontend website changes.

## Risks

- backend bridge may become too broad
- `build_ir` may accidentally bypass the existing backend snapshot flow
- local tool contract may become overcomplicated

Mitigations:

- keep the bridge single-purpose
- always reuse existing backend build-ir semantics
- keep the request model minimal

## Success Criteria

This design is successful when:

- Unity local MCP layer exposes `build_ir`
- `build_ir` executes through dispatcher
- `build_ir` uses a backend bridge, not a Unity-local IR implementation
- the AI Studio-related Unity roundtrip is extended toward Studio IR recovery
- current importer, snapshot, and batchmode flows remain green
- no unrelated website features are added
