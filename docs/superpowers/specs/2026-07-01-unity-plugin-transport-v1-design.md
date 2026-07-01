# Unity Plugin Transport V1 Design

## Goal

Add the first real Unity plugin transport layer that is directly relevant to the AI Studio closed loop.

This round upgrades the current Unity-side state from:

- local MCP-style tool execution
- local menu validation
- importer, snapshot, and build-ir business logic

to:

- real local transport host inside Unity
- HTTP command surface for tool invocation
- WebSocket event stream for status, progress, logs, and results
- local companion or agent bridge between AI Studio and Unity transport

The purpose is to make the Unity plugin behave like a real tool endpoint that AI Studio can talk to, rather than a collection of editor-local helper entrypoints.

## Why This Scope

The project already has:

- a real Unity importer core
- a thin batchmode runner
- Unity local MCP contracts, registry, dispatcher, and tools
- Unity local `build_ir` bridge to backend

What is still missing is the real communication layer between AI Studio and Unity.

Without transport, the current Unity logic can only be exercised through:

- local menu commands
- editor-local dispatcher calls
- batchmode scripts

That is enough for development validation, but not enough for a product-shaped AI Studio to Unity plugin flow.

This round fills that exact gap and nothing more.

## Scope

Included:

- Unity local transport host
- HTTP command endpoints for auth, health, tool listing, and invocation
- WebSocket event stream for connection and tool lifecycle events
- session and token-based access control for the local transport host
- transport-to-dispatcher execution bridge
- support for exactly these tools:
  - `import_package`
  - `build_snapshot`
  - `build_ir`
- tests for transport contracts, endpoint presence, tool routing, and event semantics

Excluded:

- website features unrelated to AI Studio
- EditorWindow panel
- `restyle`
- cross-machine discovery
- browser-direct complex local security model
- generic backend client platform
- unrelated billing, auth-center, docs, marketing, or site shell work

## Final Architecture

The final v1 architecture is:

1. AI Studio initiates a tool action
2. local companion or desktop bridge forwards the request to Unity over localhost
3. Unity HTTP host accepts the command
4. Unity WebSocket stream emits lifecycle events
5. Unity transport bridge forwards execution into the existing local MCP dispatcher
6. Unity returns structured result and status back through the event stream

### Key Design Rule

Transport does not implement business logic.

Business logic must stay in the existing Unity execution layer:

- importer core
- snapshot builder
- build-ir backend bridge
- local MCP registry and dispatcher

Transport only handles:

- connectivity
- authentication
- request correlation
- task lifecycle
- event delivery
- result wrapping

## Components

Add a new Unity-side transport layer under:

- `Assets/GameUIAgent/Editor/Transport/`

Recommended files:

- `GameUIAgentTransportHost.cs`
- `GameUIAgentTransportHttpServer.cs`
- `GameUIAgentTransportWebSocketServer.cs`
- `GameUIAgentTransportSessionStore.cs`
- `GameUIAgentTransportAuthService.cs`
- `GameUIAgentTransportInvokeBridge.cs`
- `GameUIAgentTransportContracts.cs`
- `GameUIAgentTransportEventBus.cs`

The current `Mcp` directory remains the execution surface for local tools.

The new `Transport` directory becomes the communication surface for the plugin.

## HTTP Command Surface

V1 should expose a minimal localhost HTTP API.

### `POST /authenticate`

Purpose:

- establish a local authorized session for AI Studio or its companion bridge

Input:

- `token`
- `project_id`
- `engine`
- `client_version`

Output:

- `session_id`
- `connection_id`
- `authorized_tools`
- `plugin_version`

Rules:

- only Unity engine is supported in this round
- failed authentication must not create a session

### `GET /healthz`

Purpose:

- report whether the transport host is available

Output:

- `status`
- `engine`
- `plugin_version`
- `transport_version`

### `GET /tools`

Purpose:

- expose tool descriptors after authentication

Output:

- descriptors for:
  - `import_package`
  - `build_snapshot`
  - `build_ir`

This endpoint must remain aligned with the existing Unity MCP registry.

### `POST /invoke`

Purpose:

- accept a real tool invocation request from AI Studio through the local bridge

Input:

- `session_id`
- `request_id`
- `tool_name`
- `arguments_json`

Immediate output:

- `status = accepted`
- `task_id`
- `request_id`

The final result is delivered through the WebSocket event stream.

## WebSocket Event Surface

V1 should expose one localhost WebSocket channel for transport events.

Recommended event types:

- `connected`
- `authenticated`
- `tool_started`
- `tool_progress`
- `tool_log`
- `tool_succeeded`
- `tool_failed`
- `heartbeat`

### Event Envelope

Every event should include:

- `type`
- `session_id`
- `request_id`
- `task_id`
- `timestamp`

Optional fields depending on event type:

- `tool_name`
- `status`
- `progress`
- `message`
- `payload_json`
- `error_code`
- `error_message`

### Event Rules

- `connected` is emitted when a WebSocket client attaches
- `authenticated` is emitted after successful HTTP auth for that logical session
- `tool_started` is emitted when invoke is accepted and execution begins
- `tool_progress` is optional but supported in v1 so tools can later report stages
- `tool_log` is for human-readable execution messages
- `tool_succeeded` carries the final structured payload
- `tool_failed` carries normalized structured error information
- `heartbeat` is periodic and used to keep the session alive

## Session and Auth Model

V1 uses a minimal local session model.

### Session Store

Add `GameUIAgentTransportSessionStore`.

Responsibilities:

- create session records after successful auth
- map `session_id` to project and allowed tools
- track connection state and heartbeat
- expire idle or disconnected sessions

Each session should track:

- `session_id`
- `connection_id`
- `project_id`
- `engine`
- `authorized_tools`
- `created_at`
- `last_seen_at`

### Auth Service

Add `GameUIAgentTransportAuthService`.

Responsibilities:

- validate plugin token or local transport token
- validate engine and project scope
- decide which tools are authorized

V1 keeps auth intentionally small:

- token-based
- project-scoped
- localhost only

This round must not introduce a full new account or identity subsystem.

## Transport Invoke Bridge

Add `GameUIAgentTransportInvokeBridge`.

Responsibilities:

- accept normalized invoke requests from the HTTP surface
- validate session and tool authorization
- translate transport request into `GameUIAgentToolRequest`
- call the existing `GameUIAgentMcpDispatcher`
- translate the final `GameUIAgentToolResponse` into WebSocket events

Key rules:

- transport invoke bridge must not duplicate tool logic
- transport invoke bridge must not know import internals, snapshot internals, or IR internals
- it only adapts transport contracts to dispatcher contracts

## Companion or Agent Bridge

V1 assumes AI Studio does not talk to Unity directly from the browser.

Instead, the supported flow is:

1. AI Studio initiates a local-plugin action
2. local companion or desktop bridge connects to Unity localhost transport
3. companion forwards Studio requests to Unity
4. companion receives WebSocket events and relays them to AI Studio

This keeps the browser side simpler and avoids overcommitting to a complex browser-to-localhost trust model in v1.

This round only defines the transport contract that the companion uses. It does not implement the whole desktop product layer.

## Supported Tools

The transport layer must only expose these tools:

- `import_package`
- `build_snapshot`
- `build_ir`

### `import_package`

Flow:

1. AI Studio requests import
2. transport accepts invoke
3. dispatcher routes to `GameUIAgentImportPackageTool`
4. importer core runs
5. `tool_succeeded` returns import result

### `build_snapshot`

Flow:

1. AI Studio requests snapshot build
2. transport accepts invoke
3. dispatcher routes to `GameUIAgentBuildSnapshotTool`
4. snapshot builder runs
5. `tool_succeeded` returns snapshot payload

### `build_ir`

Flow:

1. AI Studio requests IR build
2. transport accepts invoke
3. dispatcher routes to `GameUIAgentBuildIrTool`
4. Unity build-ir tool calls backend through the existing backend bridge
5. `tool_succeeded` returns snapshot and IR linkage result

## Data Flow

### Authentication Flow

1. companion opens WebSocket connection
2. Unity emits `connected`
3. companion calls `POST /authenticate`
4. Unity validates token and project scope
5. Unity creates `session_id`
6. Unity returns auth response
7. Unity emits `authenticated`

### Invoke Flow

1. companion calls `POST /invoke`
2. Unity validates session, tool, and payload
3. Unity creates `task_id`
4. HTTP returns `accepted`
5. Unity emits `tool_started`
6. Unity execution bridge calls dispatcher
7. dispatcher executes target tool
8. Unity emits logs and optional progress
9. Unity emits either `tool_succeeded` or `tool_failed`

## Error Handling

Transport v1 must normalize errors into a small stable set.

Recommended transport-level error codes:

- `AUTH_FAILED`
- `INVALID_SESSION`
- `UNKNOWN_TOOL`
- `TOOL_NOT_AUTHORIZED`
- `INVALID_ARGUMENTS`
- `TRANSPORT_FAILED`
- `TOOL_EXECUTION_FAILED`
- `INTERNAL_ERROR`

Rules:

- auth failures must be distinguishable from tool failures
- dispatcher or tool failures must not masquerade as transport failures
- tool execution details may be included in `tool_failed`
- HTTP and WebSocket event payloads must agree on final failure classification

## Testing Strategy

This round must follow TDD.

### RED Tests First

Add failing tests for:

- transport directory and core files exist
- source contains `POST /authenticate`
- source contains `GET /healthz`
- source contains `GET /tools`
- source contains `POST /invoke`
- source contains WebSocket event names:
  - `connected`
  - `authenticated`
  - `tool_started`
  - `tool_succeeded`
  - `tool_failed`
- transport invoke bridge references `GameUIAgentMcpDispatcher`
- transport scope remains limited to:
  - `import_package`
  - `build_snapshot`
  - `build_ir`
- transport source does not introduce `restyle` or unrelated tools

### GREEN Implementation

Minimal implementation required:

- add transport contracts
- add host, HTTP server, WebSocket server, auth service, session store, event bus, and invoke bridge
- connect invoke bridge to the existing dispatcher
- add the minimum source structure needed for future runtime wiring

This round does not require the full desktop companion implementation.

### Regression Verification

Run:

```bash
python3 -m pytest backend/tests/test_product_flow.py -q -k "unity_test_project_contains_real_plugin_and_batchmode_runner or real_engine_e2e_runner_executes_editor"
python3 -m pytest backend/tests -q
git diff --check
```

### Unity Validation

Validation must confirm:

- existing importer flows still compile and run
- local MCP tools still behave as before
- transport source compiles inside Unity
- transport-host code does not break batchmode execution

## Compatibility Requirements

This round must preserve:

- batchmode runner behavior
- importer core behavior
- local MCP tool behavior
- backend `build-ir` semantics

This round must not require unrelated site or product changes.

## Risks

- transport may accidentally absorb business logic
- HTTP and WebSocket contracts may drift apart
- v1 may overreach into desktop companion implementation
- auth may become heavier than needed for localhost v1

Mitigations:

- keep transport orchestration-only
- define one shared event envelope
- keep companion out of implementation scope and in contract scope only
- keep token auth minimal and project-scoped

## Success Criteria

This design is successful when:

- Unity has a real transport surface, not only local menu entrypoints
- AI Studio can target Unity through a localhost plugin contract
- transport bridges into the existing dispatcher rather than replacing it
- `import_package`, `build_snapshot`, and `build_ir` are the only exposed tools
- status and results have a real event-stream model
- no unrelated website features are added
