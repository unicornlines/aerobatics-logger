// Sailplane cockpit renders for social media:
//   NODE_PATH=$(npm root -g) node cockpit.js <out dir> [shot=WxH,...]   (default portrait=1080x1350,square=1080x1080)
// Renders at 2x and lets the caller downscale (supersampling).
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const dir = __dirname;
const out = path.resolve(process.argv[2] || path.join(dir, "..", "..", "renders"));
const shots = (process.argv[3] || "portrait=1080x1350,square=1080x1080").split(",").map(s => { const [n, wh] = s.split("="); const [w, h] = wh.split("x").map(Number); return { n, w: w * 2, h: h * 2 }; });
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".stl": "model/stl", ".png": "image/png" };
const srv = http.createServer((req, res) => {
  const p = path.join(dir, decodeURIComponent(req.url.split("?")[0]));
  if (!p.startsWith(dir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": types[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
}).listen(0, async () => {
  const port = srv.address().port;
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  for (const s of shots) {
    const page = await browser.newPage({ viewport: { width: s.w, height: s.h } });
    page.on("pageerror", e => console.log(s.n, "ERR", e.message));
    page.on("console", m => { if (m.type() === "error") console.log(s.n, "console", m.text()); });
    await page.goto(`http://127.0.0.1:${port}/cockpit.html?shot=${s.n}&w=${s.w}&h=${s.h}${process.env.Q || ""}`);
    await page.waitForFunction("window.done === true", null, { timeout: 900000 });
    const f = path.join(out, `cockpit-${s.n}@2x.png`);
    await page.locator("canvas").screenshot({ path: f });
    console.log("wrote", f);
    await page.close();
  }
  await browser.close(); srv.close();
});
