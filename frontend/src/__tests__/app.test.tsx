import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import { App as StudioApp } from "../StudioApp";
import { DeveloperPage } from "../components/DeveloperPage";

describe("StudioApp", () => {
  it("matches the VberAI homepage information architecture with GameUIAgent branding", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /GameUIAgent · AI 原生游戏生产力平台/);
    assert.match(html, /登录/);
    assert.match(html, /注册/);
    assert.match(html, /探索产品/);
    assert.match(html, /一站式 AI 游戏开发/);
    assert.match(html, /核心产品/);
    assert.match(html, /AI 超强抠图/);
    assert.match(html, /GAMEUIAGENT PRODUCTION STACK/);
    assert.match(html, /游戏原生设计平台/);
    assert.match(html, /让 AI 真正进入\s*游戏引擎/);
    assert.match(html, /让下一次迭代\s*直接进入引擎/);

    assert.ok(html.indexOf("一站式 AI 游戏开发") < html.indexOf("导入来源"));
    assert.ok(html.indexOf("导入来源") < html.indexOf("最佳 AI 工具"));
    assert.ok(html.indexOf("最佳 AI 工具") < html.indexOf("GAMEUIAGENT PRODUCTION STACK"));
    assert.ok(html.indexOf("GAMEUIAGENT PRODUCTION STACK") < html.indexOf("游戏原生设计平台"));
    assert.ok(html.indexOf("游戏原生设计平台") < html.indexOf("让 AI 真正进入"));
  });

  it("renders the replicated official site and studio entry points", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /一站式 AI 游戏开发/i);
    assert.match(html, /AI Studio/i);
    assert.match(html, /Unity-first/i);
    assert.match(html, /PSD \/ PSB \/ Figma/i);
  });

  it("shows the end-to-end production workflow", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Import or Generate/);
    assert.match(html, /Structure as Asset IR/);
    assert.match(html, /Import Through Plugin/);
  });

  it("renders professional import and AI pipeline sections", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Professional imports/);
    assert.match(html, /PSD layers/);
    assert.match(html, /Figma frames/);
    assert.match(html, /Developer API pipeline/);
    assert.match(html, /Webhook/);
    assert.match(html, /Cancel/);
  });

  it("renders the Unity plugin protocol and restyle chain", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Unity plugin protocol/);
    assert.match(html, /Manifest/);
    assert.match(html, /Download ZIP/);
    assert.match(html, /Import log/);
    assert.match(html, /Replacement manifest/);
    assert.match(html, /preserve RectTransform/);
  });

  it("renders the multi-engine export matrix", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Multi-engine export matrix/);
    assert.match(html, /Unity, Cocos, Godot and Unreal/);
    assert.match(html, /Unity 2022.3\+/);
    assert.match(html, /Cocos Creator 3.8.6\+/);
    assert.match(html, /Cocos Creator 2.4.x\+/);
    assert.match(html, /Godot 4.x/);
    assert.match(html, /Unreal Engine 5.3\+/);
    assert.match(html, /write_tscn_scene/);
    assert.match(html, /create_umg_widget_blueprint/);
  });

  it("renders the engine plugin connection sequence", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Engine plugin connection/);
    assert.match(html, /Plugin Auth/);
    assert.match(html, /Project Sync/);
    assert.match(html, /Export Query/);
    assert.match(html, /Package Download/);
  });

  it("renders billing credits and developer API limits", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Credits and billing/);
    assert.match(html, /Daily Free Credits/);
    assert.match(html, /Monthly Credits/);
    assert.match(html, /Purchased Credits/);
    assert.match(html, /PRO/);
    assert.match(html, /X-RateLimit-Limit/);
  });

  it("rebrands visible VberAI references to GameUIAgent", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.doesNotMatch(html, /VberAI/);
    assert.match(html, /GameUIAgent · AI 原生游戏生产力平台/);
    assert.match(html, /GameUIAgent-style marketing portal/);
  });

  it("renders the complete AI Studio interaction workspace", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Asset Library/);
    assert.match(html, /Task Timeline/);
    assert.match(html, /Layer Tree/);
    assert.match(html, /Inspector/);
    assert.match(html, /Slice Editor/);
    assert.match(html, /Nine-slice/);
  });

  it("renders actionable studio correction and export controls", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Action Dock/);
    assert.match(html, /Regenerate/);
    assert.match(html, /Segmentation Corrections/);
    assert.match(html, /Apply Correction/);
    assert.match(html, /Export Wizard/);
    assert.match(html, /Select Target Engine/);
    assert.match(html, /Synced via Studio API/);
  });

  it("renders Unreal plugin import log telemetry", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Plugin Import Telemetry/);
    assert.match(html, /Unreal 5.3\+ import summary/);
    assert.match(html, /Plugin import succeeded/);
    assert.match(html, /Warnings: 1/);
    assert.match(html, /umg_widgets_created/);
    assert.match(html, /slate_slots_bound/);
  });

  it("renders the verified PSD to Unity plugin core chain", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Core Chain Self-Test/);
    assert.match(html, /PSD layered import/);
    assert.match(html, /Unity package export/);
    assert.match(html, /Unity plugin import/);
    assert.match(html, /Studio timeline synced/);
  });

  it("renders completed account and docs center capabilities", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Completeness Status/);
    assert.match(html, /Core engine chain: verified/);
    assert.match(html, /Account and docs: covered/);
    assert.match(html, /Team Roles/);
    assert.match(html, /Owner/);
    assert.match(html, /Designer/);
    assert.match(html, /Developer/);
    assert.match(html, /Password Reset/);
    assert.match(html, /Reset token/);
    assert.match(html, /Docs Center/);
    assert.match(html, /Developer API/);
    assert.match(html, /Engine Plugins/);
  });

  it("renders the uploaded asset to slice production chain", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Upload-to-Slice Chain/);
    assert.match(html, /Uploaded Asset API/);
    assert.match(html, /Image-to-Image input asset/);
    assert.match(html, /Editable slices/);
    assert.match(html, /Professional source parser/);
    assert.match(html, /\/api\/projects\/\{project_id\}\/assets/);
    assert.match(html, /\/imports\/professional-sources/);
  });

  it("renders the asset library management operations", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Asset Library Operations/);
    assert.match(html, /Search and tags/);
    assert.match(html, /Rename and version/);
    assert.match(html, /Copy and delete/);
    assert.match(html, /\/assets\/\{asset_id\}\/versions/);
  });

  it("renders the production runtime foundation", () => {
    const html = renderToStaticMarkup(<StudioApp />);

    assert.match(html, /Production Runtime/);
    assert.match(html, /SQLite durable store/);
    assert.match(html, /Local object storage/);
    assert.match(html, /GAMEUIAGENT_OBJECT_STORE_DIR/);
    assert.match(html, /Binary upload and download/);
    assert.match(html, /AI worker queue/);
    assert.match(html, /\/api\/system\/ai-worker\/run-next/);
    assert.match(html, /GAMEUIAGENT_WORKER_TOKEN/);
    assert.match(html, /X-Worker-Token/);
    assert.match(html, /queued -&gt; running -&gt; succeeded/);
    assert.match(html, /Qwen inference provider/);
    assert.match(html, /GAMEUIAGENT_INFERENCE_PROVIDER=qwen/);
    assert.match(html, /QWEN_API_KEY/);
    assert.match(html, /inference_runs/);
    assert.match(html, /\/api\/system\/production-readiness/);
    assert.match(html, /No in-memory-only data loss/);
  });
});

describe("DeveloperPage", () => {
  it("documents real project-scoped AI, export and billing endpoints", () => {
    const html = renderToStaticMarkup(<DeveloperPage />);

    assert.match(html, /\/api\/projects\/\{project_id\}\/ai\/jobs/);
    assert.match(html, /\/api\/projects\/\{project_id\}\/exports/);
    assert.match(html, /\/api\/user\/billing\/orders/);
    assert.match(html, /\/api\/user\/billing\/orders\/\{id\}\/confirm/);
    assert.doesNotMatch(html, /\/api\/ai\/jobs/);
    assert.doesNotMatch(html, /\/api\/export\/\{engine\}/);
    assert.doesNotMatch(html, /\/api\/user\/billing\/recharge/);
  });
});
