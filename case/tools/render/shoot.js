// Render the case views with headless Chromium:
//   NODE_PATH=$(npm root -g) node shoot.js <out dir> [view,view,...]
// Serves this folder (render.html, scene.json, scene/, node_modules/three) on a local port.
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const dir = __dirname;
const out = path.resolve(process.argv[2] || path.join(dir, "..", "..", "renders"));
const cfg = JSON.parse(fs.readFileSync(path.join(dir, "scene.json")));
const views = (process.argv[3] || Object.keys(cfg.views).join(",")).split(",");
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".stl": "model/stl" };

const srv = http.createServer((req, res) => {
  const p = path.join(dir, decodeURIComponent(req.url.split("?")[0]));
  if (!p.startsWith(dir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": types[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
}).listen(0, async () => {
  const port = srv.address().port;
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  for (const v of views) {
    const page = await browser.newPage({ viewport: { width: 2400, height: 1600 } });
    page.on("pageerror", e => console.log(v, "ERR", e.message));
    await page.goto(`http://127.0.0.1:${port}/render.html?view=${v}`);
    await page.waitForFunction("window.done === true", null, { timeout: 600000 });
    await page.locator("canvas").screenshot({ path: path.join(out, `case-${v}.png`) });
    console.log("wrote", path.join(out, `case-${v}.png`));
    await page.close();
  }
  await browser.close(); srv.close();
});
