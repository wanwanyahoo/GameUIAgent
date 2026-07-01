# Unity Zip Importer Design

## Goal

Close the remaining Unity realism gap by replacing the current `package JSON -> synthetic prefab` path with a real Unity importer flow:

- platform produces a real export zip file for engine E2E runs
- Unity Editor reads `GAMEUIAGENT_E2E_ZIP_PATH`
- Unity importer extracts the zip
- importer reads `manifest.json`
- importer creates/imports Unity-native assets under the manifest paths
- importer creates or updates prefab and scene
- importer emits import summary, snapshot, and result JSON back to the platform

## Scope

This change only targets the Unity path.

Included:

- real zip file generation for `/api/system/engine-e2e/exports/{export_id}/run`
- Unity Editor importer inside `unity-test-project`
- prefab and scene reconstruction from manifest
- regression tests for zip handoff and noisy Unity stdout handling
- documentation of a better long-term plugin architecture

Excluded:

- production-grade binary texture packing
- final Unity EditorWindow UX
- two-way live sync from Unity project edits back to Studio beyond existing snapshot/IR flow

## Recommended Architecture

### Platform Side

For engine E2E runs, the backend writes a temporary zip archive identical in structure to plugin download output and passes its path via:

- `GAMEUIAGENT_E2E_ZIP_PATH`
- `GAMEUIAGENT_E2E_MANIFEST_JSON`
- `GAMEUIAGENT_E2E_EXPORT_ID`

The backend still tolerates noisy Unity stdout and extracts the final JSON result object.

### Unity Side

`GameUIAgentE2ERunner.Run()` becomes a thin batch entrypoint that:

1. reads `GAMEUIAGENT_E2E_ZIP_PATH`
2. extracts the zip into a temp import folder
3. reads extracted `manifest.json`
4. materializes Unity-native assets:
   - writes/imports placeholder texture png assets for texture entries
   - sets texture importer to sprite
   - creates prefab at manifest entry path
   - creates scene at manifest scene path
   - stores manifest copy under `Assets/GameUIAgent/Manifests`
5. scans the imported result to produce snapshot nodes and sprite records
6. writes result JSON for platform ingestion

### Import Strategy

The importer reconstructs Unity-native assets from the manifest contract, not from placeholder zip file contents alone. This preserves a real plugin-import shape while staying deterministic in test automation.

## Better Long-Term Option

The recommended implementation above is the fastest complete solution for now, but the better long-term architecture for full VberAI/AI Studio parity is:

- extract importer logic from `GameUIAgentE2ERunner.cs` into a dedicated Unity Editor package, e.g. `Assets/GameUIAgent/Editor/Importer/*`
- keep the batch runner only as a thin CLI wrapper
- share the same importer code between:
  - automated batchmode E2E
  - future Unity EditorWindow plugin UI
  - production plugin download/import workflow

This gives one importer implementation for both QA and real user flows, reducing drift between "test mode" and "plugin mode".

## Testing Plan

### Backend Tests

- engine E2E passes a real zip path to the runner
- runner output with Unity noise still succeeds

### Unity Project Tests

- runner script requires and forwards `GAMEUIAGENT_E2E_ZIP_PATH`
- Unity importer source contains zip extraction, manifest parsing, texture import, prefab creation, and scene save behavior

### Real Validation

- launch local Unity 2022.3.x
- create export through platform API
- call engine E2E endpoint
- verify:
  - import log exists
  - prefab created
  - scene created
  - snapshot generated
  - IR built from snapshot

## Risks

- Unity sandbox and host environment may still write to user Library paths
- placeholder export files are not production textures, so importer must synthesize valid Unity assets from manifest intent
- Unity batchmode log noise must never break result parsing
