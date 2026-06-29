import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import { App } from "../App";

describe("App", () => {
  it("renders the replicated official site and studio entry points", () => {
    const html = renderToStaticMarkup(<App />);

    assert.match(html, /AI Game Asset Production/i);
    assert.match(html, /AI Studio/i);
    assert.match(html, /Unity-first/i);
    assert.match(html, /PSD \/ PSB \/ Figma/i);
  });

  it("shows the end-to-end production workflow", () => {
    const html = renderToStaticMarkup(<App />);

    assert.match(html, /Import or Generate/);
    assert.match(html, /Structure as Asset IR/);
    assert.match(html, /Import Through Plugin/);
  });

  it("renders professional import and AI pipeline sections", () => {
    const html = renderToStaticMarkup(<App />);

    assert.match(html, /Professional imports/);
    assert.match(html, /PSD layers/);
    assert.match(html, /Figma frames/);
    assert.match(html, /Developer API pipeline/);
    assert.match(html, /Webhook/);
    assert.match(html, /Cancel/);
  });
});
