import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "esbuild";

const repoRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const outDir = join(repoRoot, "dist", "frontend");
const assetsDir = join(outDir, "assets");

await rm(outDir, { recursive: true, force: true });
await mkdir(assetsDir, { recursive: true });

await build({
  entryPoints: [join(repoRoot, "frontend", "src", "main.tsx")],
  bundle: true,
  minify: true,
  sourcemap: false,
  target: ["es2022"],
  format: "esm",
  outfile: join(assetsDir, "index.js"),
  loader: {
    ".css": "css"
  }
});

const sourceHtml = await readFile(join(repoRoot, "frontend", "index.html"), "utf8");
const html = sourceHtml.replace(
  '<script type="module" src="/src/main.tsx"></script>',
  '<link rel="stylesheet" href="/assets/index.css" />\n    <script type="module" src="/assets/index.js"></script>'
);

await writeFile(join(outDir, "index.html"), html);
