# Unity Importer MCP Package Design

## Goal

Evolve the current Unity zip importer from a batchmode-only implementation into the final shared architecture for:

- automated Unity batchmode E2E
- Unity-side MCP tool execution
- future Unity Editor plugin UI

The target end state is:

- `GameUIAgentE2ERunner` becomes a thin batchmode adapter
- Unity import logic moves into reusable importer services
- Unity exposes MCP-style tool facades that call the same importer core
- batchmode E2E and future production plugin flows stop drifting apart

## Why This Change

The current implementation in `GameUIAgentE2ERunner.cs` already proves the realistic flow:

- platform produces a real export zip
- Unity Editor consumes the zip
- Unity creates texture, prefab, scene, manifest copy, snapshot, and result JSON

However, the current file mixes too many responsibilities:

- environment variable parsing
- batchmode process exit behavior
- manifest parsing
- file extraction
- asset creation
- prefab creation
- scene creation
- snapshot construction
- result DTO definition

That structure is acceptable for the first realism milestone, but not for the final architecture that must support MCP-driven Unity operations similar to the target product direction.

## Scope

Included in this design:

- extract Unity import logic from `GameUIAgentE2ERunner.cs`
- create reusable importer service and editor-side contracts
- define Unity-side MCP facade layer for import and snapshot operations
- keep existing backend and environment contract compatible
- preserve real Unity batchmode verification path

Excluded in this design:

- final Unity EditorWindow UX
- full remote MCP transport/session stack inside Unity
- production binary asset packing beyond current placeholder/import reconstruction strategy
- live bidirectional scene edit sync from Unity back to Studio

## Final Architecture

### High-Level Shape

The Unity-side architecture is split into four layers:

1. `Contracts`
2. `Importer Core`
3. `MCP Facade`
4. `Batchmode Adapter`

Each outer layer depends inward. The importer core is the only place that owns real import behavior.

### Layer 1: Contracts

Create editor-side contract models under:

- `Assets/GameUIAgent/Editor/Contracts/GameUIAgentImportRequest.cs`
- `Assets/GameUIAgent/Editor/Contracts/GameUIAgentImportResult.cs`
- `Assets/GameUIAgent/Editor/Contracts/UnityPackageManifest.cs`
- `Assets/GameUIAgent/Editor/Contracts/GameUIAgentSnapshot.cs`

Responsibilities:

- define stable request/response models for Unity import execution
- separate transport-specific input from import-domain models
- allow batchmode and MCP facade to share the same result payload structure

Key requirement:

- current E2E result fields remain representable without breaking backend ingestion

Recommended model shape:

```csharp
public sealed class GameUIAgentImportRequest
{
    public string ExportId;
    public string Engine;
    public string ZipPath;
    public string ManifestJson;
    public string PackageJson;
    public bool BuildScene;
    public bool BuildSnapshot;
}
```

```csharp
public sealed class GameUIAgentImportResult
{
    public string Status;
    public string EngineVersion;
    public string PluginVersion;
    public int DurationMs;
    public GameUIAgentImportSummary Summary;
    public GameUIAgentLogEntry[] Logs;
    public GameUIAgentSnapshot Snapshot;
    public string PrefabPath;
    public string ScenePath;
    public string ManifestAssetPath;
}
```

### Layer 2: Importer Core

Create reusable importer services under:

- `Assets/GameUIAgent/Editor/Importer/GameUIAgentImportService.cs`
- `Assets/GameUIAgent/Editor/Importer/GameUIAgentAssetMaterializer.cs`
- `Assets/GameUIAgent/Editor/Importer/GameUIAgentPrefabBuilder.cs`
- `Assets/GameUIAgent/Editor/Importer/GameUIAgentSceneBuilder.cs`
- `Assets/GameUIAgent/Editor/Importer/GameUIAgentSnapshotBuilder.cs`
- `Assets/GameUIAgent/Editor/Importer/GameUIAgentPathUtility.cs`

Responsibilities by component:

- `GameUIAgentImportService`
  - orchestration entrypoint
  - validates request
  - parses manifest
  - coordinates extraction, asset import, prefab build, scene build, snapshot build
  - returns `GameUIAgentImportResult`

- `GameUIAgentAssetMaterializer`
  - extracts zip contents into temp area
  - creates or imports Unity assets
  - owns placeholder texture materialization for current phase
  - configures `TextureImporterType.Sprite`

- `GameUIAgentPrefabBuilder`
  - creates or updates prefab from manifest intent
  - owns runtime marker binding and base canvas/button creation

- `GameUIAgentSceneBuilder`
  - creates or updates scene from prefab
  - owns `EditorSceneManager` interactions

- `GameUIAgentSnapshotBuilder`
  - converts imported Unity state into snapshot DTO
  - isolates snapshot generation from import orchestration

- `GameUIAgentPathUtility`
  - normalizes Unity asset paths
  - guards against invalid non-`Assets/` paths
  - centralizes project-root path mapping
  - explicitly prevents regressions like the earlier `Path.Combine(projectRoot, normalized)` bug class

Key rule:

- no batchmode exit handling, no environment-variable parsing, and no stdout/file result writing inside importer core

### Layer 3: MCP Facade

Create Unity-side MCP-style tool facades under:

- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentMcpToolRegistry.cs`
- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentImportPackageTool.cs`
- `Assets/GameUIAgent/Editor/Mcp/GameUIAgentBuildSnapshotTool.cs`

This layer does not need to implement the final external MCP transport yet. Its job in this phase is to define the internal tool boundary that the future production plugin or EditorWindow can call.

Tool responsibilities:

- `import_package`
  - accepts zip path and import options
  - builds `GameUIAgentImportRequest`
  - calls `GameUIAgentImportService`
  - returns `GameUIAgentImportResult`

- `build_snapshot`
  - accepts prefab/scene path or current import result
  - calls `GameUIAgentSnapshotBuilder`
  - returns snapshot payload

Key requirement:

- MCP facade must never fork import logic from batchmode flow
- all real import behavior must still go through `GameUIAgentImportService`

### Layer 4: Batchmode Adapter

Keep batchmode entrypoint at:

- `Assets/GameUIAgent/Editor/Batchmode/GameUIAgentE2ERunner.cs`

Responsibilities:

- read `GAMEUIAGENT_E2E_*` environment variables
- assemble `GameUIAgentImportRequest`
- call `GameUIAgentImportService`
- serialize compatible result JSON
- write result file when `GAMEUIAGENT_E2E_RESULT_PATH` exists
- control `EditorApplication.Exit(0/1)`

Key requirement:

- the batchmode adapter should become intentionally boring
- it must not directly contain zip extraction, prefab creation, scene save, or snapshot construction logic

## Directory Structure

Target Unity editor layout:

```text
Assets/GameUIAgent/Editor/
  Batchmode/
    GameUIAgentE2ERunner.cs
  Contracts/
    GameUIAgentImportRequest.cs
    GameUIAgentImportResult.cs
    UnityPackageManifest.cs
    GameUIAgentSnapshot.cs
  Importer/
    GameUIAgentImportService.cs
    GameUIAgentAssetMaterializer.cs
    GameUIAgentPrefabBuilder.cs
    GameUIAgentSceneBuilder.cs
    GameUIAgentSnapshotBuilder.cs
    GameUIAgentPathUtility.cs
  Mcp/
    GameUIAgentMcpToolRegistry.cs
    GameUIAgentImportPackageTool.cs
    GameUIAgentBuildSnapshotTool.cs
```

This directory structure is intentionally aligned to future plugin growth without introducing UI code yet.

## Data Flow

### Batchmode E2E Flow

1. backend writes export zip
2. backend passes `GAMEUIAGENT_E2E_ZIP_PATH`
3. `GameUIAgentE2ERunner.Run()` reads env vars
4. runner builds `GameUIAgentImportRequest`
5. runner calls `GameUIAgentImportService`
6. service produces `GameUIAgentImportResult`
7. runner writes JSON and exits

### MCP Tool Flow

1. Unity-side MCP facade receives tool invocation
2. tool facade validates arguments
3. tool facade builds `GameUIAgentImportRequest`
4. tool facade calls `GameUIAgentImportService`
5. tool facade returns `GameUIAgentImportResult`

### Future EditorWindow Flow

1. editor UI gathers user action and selected export
2. UI calls MCP facade or directly calls importer service
3. shared importer logic performs the same import steps
4. UI renders progress/state from shared result object

The central invariant across all three flows is:

- one importer core
- many thin adapters

## Compatibility Requirements

The following existing contracts must remain compatible during this refactor:

- backend endpoint `/api/system/engine-e2e/exports/{export_id}/run`
- Unity shell script `run-gameuiagent-e2e.sh`
- environment variables:
  - `GAMEUIAGENT_E2E_ZIP_PATH`
  - `GAMEUIAGENT_E2E_RESULT_PATH`
  - `GAMEUIAGENT_E2E_EXPORT_ID`
  - `GAMEUIAGENT_E2E_ENGINE`
  - `GAMEUIAGENT_E2E_MANIFEST_JSON`
  - `GAMEUIAGENT_E2E_PACKAGE_JSON`
- backend noisy stdout parsing
- backend test expectations around:
  - `snapshot.source`
  - import log summary
  - IR generation from snapshot

Internal DTO naming may evolve from E2E-centric names to import-centric names, but the outer JSON written by batchmode must stay backward compatible for current backend ingestion.

## Error Handling

Importer core must return structured failures for:

- missing or unreadable zip path
- missing `manifest.json`
- invalid Unity manifest
- invalid asset path outside `Assets/`
- missing prefab after save
- scene creation failure
- texture import failure

Batchmode adapter behavior:

- serializes a compatible failed result payload
- exits with non-zero code

MCP facade behavior:

- returns structured tool error with stage and reason
- does not convert failures into fake success

## Testing Strategy

This refactor must follow TDD.

### RED Tests First

Add or update tests that fail before refactor:

- runner source no longer contains direct zip extraction or scene-save implementation details
- importer service source contains zip extraction, prefab creation, scene creation, snapshot construction responsibilities
- MCP facade source exists and calls importer service
- path utility owns Unity project path mapping

### GREEN Implementation

Minimal implementation to satisfy:

- current backend zip handoff test still passes
- current stdout noise tolerance test still passes
- Unity project contract test now validates the new file layout and responsibility split

### Regression Verification

Run:

```bash
python3 -m pytest backend/tests/test_product_flow.py -q -k "engine_e2e_runner_passes_real_zip_export_to_unity_importer or engine_e2e_runner_extracts_json_from_unity_stdout_noise or unity_test_project_contains_real_plugin"
python3 -m pytest backend/tests -q
git diff --check
```

### Real Unity Validation

After refactor, rerun the same real Unity flow:

- export through platform API
- invoke engine E2E endpoint
- confirm real files exist:
  - texture
  - prefab
  - scene
  - manifest
- confirm result still reports:
  - `status = succeeded`
  - `snapshot.source = unity_zip_importer`

## Implementation Order

Recommended order:

1. move DTOs to `Contracts`
2. introduce `GameUIAgentPathUtility`
3. extract `GameUIAgentSnapshotBuilder`
4. extract `GameUIAgentAssetMaterializer`
5. extract `GameUIAgentPrefabBuilder`
6. extract `GameUIAgentSceneBuilder`
7. introduce `GameUIAgentImportService`
8. shrink `GameUIAgentE2ERunner` to thin adapter
9. add `Mcp` facade classes
10. update tests and rerun real Unity validation

This order reduces breakage by peeling stable helpers first before shrinking the runner.

## Risks

- refactor may accidentally break current JSON compatibility expected by backend
- splitting files may miss Unity `.meta` tracking if not committed carefully
- MCP facade may become a duplicate abstraction if it bypasses importer service
- future plugin UI may still drift if it directly reimplements import logic

Mitigations:

- keep batchmode output schema backward compatible
- route all import behavior through importer service only
- keep facade intentionally thin
- retain real Unity validation after refactor, not only static source assertions

## Success Criteria

This design is considered complete when all of the following are true:

- `GameUIAgentE2ERunner` is a thin adapter
- Unity import behavior is implemented in reusable importer services
- Unity-side MCP tool facade exists and uses the same importer core
- backend integration tests remain green
- real Unity zip import validation still succeeds
- the resulting structure is suitable for future EditorWindow plugin UI without another large refactor
