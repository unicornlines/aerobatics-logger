// Render the board views with headless Chromium: node shoot.js <dir with render.html, scene.json, board.glb, textures> <out dir>
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const [dir, out] = process.argv.slice(2);
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".png": "image/png", ".glb": "model/gltf-binary" };
const srv = http.createServer((req, res) => {
  const p = path.join(dir, decodeURIComponent(req.url.split("?")[0]));
  if (!p.startsWith(path.resolve(dir)) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": types[path.extname(p)] || "application/octet-stream" }); fs.createReadStream(p).pipe(res);
}).listen(0, async () => {
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  for (const view of (process.env.VIEWS || "hero,top,bottom").split(",")) {
    const page = await browser.newPage({ viewport: { width: 2400, height: 1600 } });
    page.on("console", m => console.log(view, ">", m.text()));
    page.on("pageerror", e => console.log(view, "ERR", e.message));
    await page.goto(`http://127.0.0.1:${port}/render.html?view=${view}&w=${process.env.RW || 2400}&h=${process.env.RH || 1600}`);
    await page.waitForFunction("window.done === true", null, { timeout: +(process.env.TMO || 600000) });
    await page.locator("canvas").screenshot({ path: path.join(out, `board-${view}.png`) });
    console.log("wrote", view);
    await page.close();
  }
  await browser.close(); srv.close();
});
