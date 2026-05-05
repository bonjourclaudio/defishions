"""
serve_animation.py
------------------
Place this file one level above your 'data' folder:

    project/
        serve_animation.py
        data/
            tracks_T3.csv
            delay_times.csv
            learning.csv
            social_parameters.csv

Run:
    python serve_animation.py

Then open:  http://localhost:8000
"""

import http.server
import json
import csv
import os
import webbrowser
from pathlib import Path

PORT = 8000
DATA_DIR = Path(__file__).parent / "data"
TRACKS_FILE = DATA_DIR / "tracks_T3.csv"

# ── Load and compact track data ───────────────────────────────────────────────

def load_tracks():
    frames = {}
    with open(TRACKS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fid = int(row["FRAME_IDX"])
            if fid not in frames:
                frames[fid] = []
            frames[fid].append([
                int(row["IDENTITY"]),
                round(float(row["X"]), 1),
                round(float(row["Y"]), 1),
            ])
    return [frames[k] for k in sorted(frames)]

print("Loading track data...", end=" ", flush=True)
TRACK_DATA = load_tracks()
TRACK_JSON = json.dumps(TRACK_DATA, separators=(",", ":"))
print(f"{len(TRACK_DATA)} frames, {len(TRACK_JSON)//1024} KB")

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Fish Tracks — A. burtoni Trial T3</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0d1117;
    color: #cdd9e5;
    font-family: ui-monospace, monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    min-height: 100vh;
  }}
  h1 {{
    font-size: 13px;
    font-weight: 400;
    color: #8b949e;
    margin-bottom: 12px;
    letter-spacing: 0.04em;
  }}
  canvas {{
    border: 1px solid #30363d;
    border-radius: 6px;
    display: block;
    max-width: 100%;
  }}
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: center;
    margin-top: 12px;
    font-size: 12px;
    color: #8b949e;
  }}
  button {{
    background: #21262d;
    border: 1px solid #30363d;
    color: #cdd9e5;
    padding: 4px 14px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 12px;
    font-family: inherit;
  }}
  button:hover {{ background: #30363d; }}
  .slider-group {{ display: flex; align-items: center; gap: 8px; }}
  input[type=range] {{ width: 120px; accent-color: #388bfd; }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 10px;
    font-size: 11px;
    color: #8b949e;
  }}
  .legend-item {{ display: flex; align-items: center; gap: 4px; }}
  .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  #info {{ font-size: 11px; color: #555; margin-top: 4px; }}
</style>
</head>
<body>

<h1>Astatotilapia burtoni — Trial T3 &nbsp;|&nbsp; {len(TRACK_DATA)} frames &nbsp;|&nbsp; 10 fish</h1>
<canvas id="c" width="1062" height="547"></canvas>

<div class="controls">
  <button id="btn">⏸ Pause</button>
  <div class="slider-group">
    <label for="speed">Speed</label>
    <input type="range" id="speed" min="1" max="20" value="5">
    <span id="speedVal">5</span>
  </div>
  <div class="slider-group">
    <label for="tail">Tail</label>
    <input type="range" id="tail" min="1" max="80" value="25">
    <span id="tailVal">25</span>
  </div>
  <div class="slider-group">
    <label for="scrub">Scrub</label>
    <input type="range" id="scrub" min="0" max="{len(TRACK_DATA)-1}" value="0" style="width:200px">
  </div>
  <span id="info">Frame 0 / {len(TRACK_DATA)-1}</span>
</div>

<div class="legend" id="legend"></div>

<script>
const TRACKS = {TRACK_JSON};

const COLOURS = [
  '#58a6ff','#ff7b72','#3fb950','#e3b341','#bc8cff',
  '#ff6bd6','#39d353','#f78166','#79c0ff','#ffa657'
];

const NAMES = TRACKS[0].map(([id]) => `Fish ${{id}}`);

// Build legend
const legendEl = document.getElementById('legend');
COLOURS.forEach((c, i) => {{
  const div = document.createElement('div');
  div.className = 'legend-item';
  div.innerHTML = `<span class="legend-dot" style="background:${{c}}"></span>Fish ${{i}}`;
  legendEl.appendChild(div);
}});

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

// Scale canvas to fit window on load and resize
function fitCanvas() {{
  const maxW = Math.min(window.innerWidth - 32, 1062);
  canvas.style.width  = maxW + 'px';
  canvas.style.height = (maxW * (547/1062)) + 'px';
}}
fitCanvas();
window.addEventListener('resize', fitCanvas);

// Coordinate space (pixel space from tracking)
const X_MIN = 160, X_MAX = 1280, Y_MIN = 40, Y_MAX = 690;
const CW = canvas.width, CH = canvas.height;

function tx(x) {{ return (x - X_MIN) / (X_MAX - X_MIN) * CW; }}
function ty(y) {{ return (y - Y_MIN) / (Y_MAX - Y_MIN) * CH; }}

// State
let frame   = 0;
let playing = true;
let lastT   = 0;
const history = {{}};

// Controls
const btn      = document.getElementById('btn');
const speedEl  = document.getElementById('speed');
const speedVal = document.getElementById('speedVal');
const tailEl   = document.getElementById('tail');
const tailVal  = document.getElementById('tailVal');
const scrubEl  = document.getElementById('scrub');
const infoEl   = document.getElementById('info');

btn.onclick = () => {{
  playing = !playing;
  btn.textContent = playing ? '⏸ Pause' : '▶ Play';
  if (playing) requestAnimationFrame(loop);
}};
speedEl.oninput = () => speedVal.textContent = speedEl.value;
tailEl.oninput  = () => tailVal.textContent  = tailEl.value;
scrubEl.oninput = () => {{
  frame = +scrubEl.value;
  Object.keys(history).forEach(k => history[k] = []);
  draw();
}};

// Draw one frame
function draw() {{
  const tailLen = +tailEl.value;
  ctx.fillStyle = '#0d1117';
  ctx.fillRect(0, 0, CW, CH);

  // Tank border
  ctx.strokeStyle = '#21262d';
  ctx.lineWidth = 2;
  ctx.strokeRect(tx(X_MIN), ty(Y_MIN), tx(X_MAX)-tx(X_MIN), ty(Y_MAX)-ty(Y_MIN));

  // Grid
  ctx.strokeStyle = 'rgba(48,54,61,0.6)';
  ctx.lineWidth = 0.5;
  for (let gx = 200; gx < X_MAX; gx += 100) {{
    ctx.beginPath(); ctx.moveTo(tx(gx), ty(Y_MIN)); ctx.lineTo(tx(gx), ty(Y_MAX)); ctx.stroke();
  }}
  for (let gy = 100; gy < Y_MAX; gy += 100) {{
    ctx.beginPath(); ctx.moveTo(tx(X_MIN), ty(gy)); ctx.lineTo(tx(X_MAX), ty(gy)); ctx.stroke();
  }}

  // Axis labels (pixel coords)
  ctx.fillStyle = '#3d444d';
  ctx.font = '9px monospace';
  ctx.textAlign = 'center';
  for (let gx = 200; gx < X_MAX; gx += 200) {{
    ctx.fillText(gx, tx(gx), ty(Y_MAX) + 12);
  }}
  ctx.textAlign = 'right';
  for (let gy = 100; gy < Y_MAX; gy += 100) {{
    ctx.fillText(gy, tx(X_MIN) - 4, ty(gy) + 3);
  }}

  // Update history
  const fdata = TRACKS[frame] || [];
  for (const [id, x, y] of fdata) {{
    if (!history[id]) history[id] = [];
    history[id].push({{x, y}});
    if (history[id].length > tailLen) history[id].shift();
  }}

  // Draw tails + fish
  for (const [id, x, y] of fdata) {{
    const col  = COLOURS[id % COLOURS.length];
    const hist = history[id] || [];

    // Tail
    for (let i = 1; i < hist.length; i++) {{
      const a = i / hist.length;
      ctx.beginPath();
      ctx.moveTo(tx(hist[i-1].x), ty(hist[i-1].y));
      ctx.lineTo(tx(hist[i].x),   ty(hist[i].y));
      ctx.strokeStyle = col;
      ctx.globalAlpha = a * 0.65;
      ctx.lineWidth   = 0.8 + a * 2.2;
      ctx.stroke();
    }}
    ctx.globalAlpha = 1;

    // Body — ellipse oriented by motion direction
    const cx = tx(x), cy = ty(y);
    let angle = 0;
    if (hist.length >= 2) {{
      const p = hist[hist.length - 2];
      angle = Math.atan2(ty(y) - ty(p.y), tx(x) - tx(p.x));
    }}

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(angle);
    ctx.shadowColor = col;
    ctx.shadowBlur  = 6;
    ctx.fillStyle   = col;
    ctx.beginPath();
    ctx.ellipse(0, 0, 9, 4.5, 0, 0, Math.PI * 2);
    ctx.fill();
    // Eye
    ctx.shadowBlur = 0;
    ctx.fillStyle  = '#0d1117';
    ctx.beginPath();
    ctx.arc(5, -1.5, 1.8, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // ID label
    ctx.fillStyle   = col;
    ctx.font        = '10px monospace';
    ctx.textAlign   = 'center';
    ctx.globalAlpha = 0.8;
    ctx.fillText(id, cx, cy - 13);
    ctx.globalAlpha = 1;
  }}

  // Progress bar
  const prog = frame / (TRACKS.length - 1);
  ctx.fillStyle = '#21262d';
  ctx.fillRect(tx(X_MIN), CH - 6, tx(X_MAX) - tx(X_MIN), 4);
  ctx.fillStyle = '#388bfd';
  ctx.fillRect(tx(X_MIN), CH - 6, (tx(X_MAX) - tx(X_MIN)) * prog, 4);

  // Sync scrubber
  scrubEl.value = frame;
  infoEl.textContent = `Frame ${{frame}} / ${{TRACKS.length - 1}}`;
}}

function loop(t) {{
  if (!playing) return;
  const fps = +speedEl.value;
  if (t - lastT >= 1000 / fps) {{
    frame  = (frame + 1) % TRACKS.length;
    lastT  = t;
    draw();
  }}
  requestAnimationFrame(loop);
}}

draw();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Suppress per-request logs; keep it clean
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    server = http.server.HTTPServer(("localhost", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Serving at  {url}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
