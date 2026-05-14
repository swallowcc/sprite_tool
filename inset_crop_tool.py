"""
Inset Crop Tool  +  Pink BG Remover
1. 上傳圖片，設定底色與 threshold → 即時預覽去底色效果
2. 確認後設定 cols / rows / inset → 下載 ZIP
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from PIL import Image

app = FastAPI()


# ──────────────────────────────────────────────
# BG Removal helper  (from remove_pink_background.py)
# ──────────────────────────────────────────────

def _parse_hex(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) != 6:
        raise ValueError("需要 6 位 hex 色碼，例如 #ff00ff")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def remove_background(img: Image.Image, bg_color: str, threshold: float) -> Image.Image:
    """將 img 中 RGB 距離 bg_color 在 threshold 內的像素設為透明。"""
    img = img.convert("RGBA")
    pixels = np.array(img, dtype=np.int32)
    key = np.array(_parse_hex(bg_color), dtype=np.int32)
    dist = np.sqrt(np.sum((pixels[..., :3] - key) ** 2, axis=-1))
    out = pixels.copy()
    out[..., 3] = np.where(dist <= threshold, 0, pixels[..., 3])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ──────────────────────────────────────────────
# HTML 前端
# ──────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8">
  <title>Inset Crop Tool</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .checker {
      background-color: #888;
      background-image:
        linear-gradient(45deg, #aaa 25%, transparent 25%),
        linear-gradient(-45deg, #aaa 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #aaa 75%),
        linear-gradient(-45deg, transparent 75%, #aaa 75%);
      background-size: 20px 20px;
      background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    }
  </style>
</head>
<body class="bg-slate-900 text-white">
<div class="max-w-7xl mx-auto space-y-6 p-6 pt-20">

  <header class="border-b border-slate-700 pb-2">
    <h1 class="text-xl font-bold">✂️ Inset Crop</h1>
    <p class="text-slate-400 text-sm mt-2">移除背景色並內縮邊界，自動切割 Sprite Sheet 為個別方塊</p>
  </header>

  <!-- ── Top: Controls ── -->
  <div class="bg-slate-800 rounded-2xl p-5">
    <div class="flex flex-wrap gap-6 items-end">

      <!-- 上傳 -->
      <div class="min-w-48">
        <label class="block text-xs text-slate-400 mb-1">上傳圖片</label>
        <input id="fileInput" type="file" accept="image/*"
               class="w-full text-sm file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0
                      file:bg-blue-600 file:text-white file:cursor-pointer hover:file:bg-blue-500">
      </div>

      <div class="w-px self-stretch bg-slate-600"></div>

      <!-- 去底色 -->
      <div class="space-y-1">
        <p class="text-xs font-semibold text-pink-300">去底色設定</p>
        <div class="flex gap-2 items-center">
          <input id="colorPicker" type="color" value="#ff00ff"
                 class="w-10 h-9 rounded cursor-pointer border-0 p-0 bg-transparent">
          <input id="colorHex" type="text" value="#ff00ff" maxlength="7"
                 class="w-24 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white font-mono text-sm">
          <div class="flex gap-2 items-center">
            <span class="text-xs text-slate-400 whitespace-nowrap">Threshold: <span id="threshLabel">100</span></span>
            <input id="threshRange" type="range" min="0" max="442" value="100"
                   class="w-32 accent-pink-500">
            <input id="threshNum" type="number" min="0" max="442" value="100"
                   class="w-16 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
          </div>
        </div>
      </div>

      <div class="w-px self-stretch bg-slate-600"></div>

      <!-- 預覽底色 -->
      <div class="space-y-1">
        <p class="text-xs font-semibold text-cyan-300">預覽底色（檢查用）</p>
        <div class="flex gap-2 items-center">
          <input id="previewColorPicker" type="color" value="#333333"
                 class="w-10 h-9 rounded cursor-pointer border-0 p-0 bg-transparent">
          <input id="previewColorHex" type="text" value="#333333" maxlength="7"
                 class="w-24 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white font-mono text-sm">
          <span class="text-xs text-slate-400">僅用於檢查，不影響匯出</span>
        </div>
      </div>

    </div>

    <!-- Info -->
    <div id="info" class="hidden mt-3 bg-slate-700/50 rounded-lg px-4 py-2 text-sm text-slate-300 flex flex-wrap gap-x-6 gap-y-1"></div>
  </div>

  <!-- ── Middle: Previews ── -->
  <div class="grid grid-cols-2 gap-4">

    <div class="bg-slate-800 rounded-2xl p-4 space-y-2">
      <p class="text-sm font-semibold text-slate-400">原始圖片</p>
      <div class="flex items-center justify-center rounded-lg bg-slate-700 min-h-80 overflow-auto">
        <img id="origImg" class="hidden max-w-full object-contain" style="image-rendering:pixelated">
        <p id="origPH" class="text-slate-500 text-sm">尚未上傳圖片</p>
      </div>
    </div>

    <div class="bg-slate-800 rounded-2xl p-4 space-y-2">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-cyan-300">去底色預覽（底色檢查用 + 內縮虛線）</p>
        <span id="previewLoading" class="hidden text-xs text-slate-400 animate-pulse">更新中…</span>
      </div>
      <div id="previewBg" class="relative flex items-center justify-center rounded-lg min-h-80 overflow-auto" style="background-color: #333333;">
        <img id="bgImg" class="hidden max-w-full object-contain" style="image-rendering:pixelated">
        <canvas id="insetCanvas" class="hidden absolute top-0 left-0" style="image-rendering:pixelated;"></canvas>
        <p id="bgPH" class="text-slate-500 text-sm">預覽將在此顯示</p>
      </div>
    </div>

  </div>

  <!-- ── Bottom: Crop Settings & Download ── -->
  <div class="bg-slate-800 rounded-2xl p-4">
    
    <!-- 左邊：裁切設定 -->
    <div class="flex flex-col items-center gap-2">
      <p class="text-xs font-semibold text-blue-300">裁切設定</p>
      <div class="flex flex-wrap gap-2 items-end">
        <div>
          <label class="block text-xs text-slate-400 mb-1">Columns</label>
          <input id="colsInput" type="number" value="4" min="1"
                 class="w-20 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">Rows</label>
          <input id="rowsInput" type="number" value="6" min="1"
                 class="w-20 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">內縮 (px)</label>
          <input id="insetInput" type="number" value="2" min="0"
                 class="w-20 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">X 偏移 (px)</label>
          <input id="offsetXInput" type="number" value="0"
                 class="w-20 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">Y 偏移 (px)</label>
          <input id="offsetYInput" type="number" value="0"
                 class="w-20 p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
        </div>
      </div>
    </div>

    <!-- 右邊：下載按鈕 -->
    <div class="flex flex-col items-center gap-2 mt-4">
      <button id="downloadBtn" disabled onclick="doProcess()"
              class="px-10 py-3 bg-blue-600 hover:bg-blue-500
                     disabled:bg-slate-600 disabled:cursor-not-allowed
                     rounded-xl font-bold transition text-white whitespace-nowrap">
        ⬇ 確認並下載 ZIP
      </button>
      <div id="status" class="hidden text-sm text-slate-400"></div>
    </div>
  </div>

</div>

<script>
let currentFile      = null;
let previewDebounce  = null;
let previewObjectUrl = null;

const fileInput      = document.getElementById('fileInput');
const origImg        = document.getElementById('origImg');
const origPH         = document.getElementById('origPH');
const bgImg          = document.getElementById('bgImg');
const bgPH           = document.getElementById('bgPH');
const insetCanvas    = document.getElementById('insetCanvas');
const previewBg      = document.getElementById('previewBg');
const colorPicker    = document.getElementById('colorPicker');
const colorHex       = document.getElementById('colorHex');
const previewColorPicker = document.getElementById('previewColorPicker');
const previewColorHex    = document.getElementById('previewColorHex');
const threshRange    = document.getElementById('threshRange');
const threshNum      = document.getElementById('threshNum');
const threshLabel    = document.getElementById('threshLabel');
const infoDiv        = document.getElementById('info');
const statusDiv      = document.getElementById('status');
const downloadBtn    = document.getElementById('downloadBtn');
const previewLoading = document.getElementById('previewLoading');

// ── Preview color picker <-> hex ─────────────
previewColorPicker.addEventListener('input', () => {
  previewColorHex.value = previewColorPicker.value;
  previewBg.style.backgroundColor = previewColorPicker.value;
});
previewColorHex.addEventListener('change', () => {
  const v = previewColorHex.value.trim();
  if (/^#[0-9a-fA-F]{6}$/.test(v)) {
    previewColorPicker.value = v;
    previewBg.style.backgroundColor = v;
  }
});

// ── Color picker <-> hex ─────────────────────
colorPicker.addEventListener('input', () => {
  colorHex.value = colorPicker.value;
  schedulePreview();
});
colorHex.addEventListener('change', () => {
  const v = colorHex.value.trim();
  if (/^#[0-9a-fA-F]{6}$/.test(v)) {
    colorPicker.value = v;
    schedulePreview();
  }
});

// ── Threshold slider <-> number ──────────────
threshRange.addEventListener('input', () => {
  threshNum.value         = threshRange.value;
  threshLabel.textContent = threshRange.value;
  schedulePreview();
});
threshNum.addEventListener('input', () => {
  threshRange.value       = threshNum.value;
  threshLabel.textContent = threshNum.value;
  schedulePreview();
});

// ── File upload ──────────────────────────────
fileInput.addEventListener('change', () => {
  const f = fileInput.files[0];
  if (!f) return;
  currentFile = f;
  origImg.src = URL.createObjectURL(f);
  origImg.classList.remove('hidden');
  origPH.classList.add('hidden');
  downloadBtn.disabled = false;
  schedulePreview();
});

origImg.addEventListener('load', updateInfo);
['colsInput','rowsInput','insetInput','offsetXInput','offsetYInput'].forEach(id =>
  document.getElementById(id).addEventListener('input', () => {
    updateInfo();
    drawInsetGrid();
  }));

// ── Draw inset grid on canvas ────────────────
function drawInsetGrid() {
  if (!bgImg.naturalWidth || bgImg.classList.contains('hidden')) return;
  
  const cols    = +document.getElementById('colsInput').value    || 1;
  const rows    = +document.getElementById('rowsInput').value    || 1;
  const inset   = +document.getElementById('insetInput').value   || 0;
  const offsetX = +document.getElementById('offsetXInput').value || 0;
  const offsetY = +document.getElementById('offsetYInput').value || 0;
  
  const imgW = bgImg.naturalWidth;
  const imgH = bgImg.naturalHeight;
  const tileW = Math.floor(imgW / cols);
  const tileH = Math.floor(imgH / rows);
  
  // 設置Canvas的繪製解析度（邏輯像素）
  insetCanvas.width = imgW;
  insetCanvas.height = imgH;
  
  // 計算bgImg的實際顯示大小
  const displayW = bgImg.offsetWidth;
  const displayH = bgImg.offsetHeight;
  const offsetLeft = bgImg.offsetLeft;
  const offsetTop = bgImg.offsetTop;
  
  // 設置Canvas的CSS顯示大小和位置以匹配bgImg
  insetCanvas.style.width = displayW + 'px';
  insetCanvas.style.height = displayH + 'px';
  insetCanvas.style.left = offsetLeft + 'px';
  insetCanvas.style.top = offsetTop + 'px';
  
  const ctx = insetCanvas.getContext('2d');
  ctx.clearRect(0, 0, imgW, imgH);
  ctx.strokeStyle = 'rgba(255, 100, 200, 0.7)'; // 粉紅色虛線
  ctx.setLineDash([4, 4]);
  ctx.lineWidth = 1.5;
  
  // 對每個格子繪製內縮邊界框
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x0 = c * tileW + offsetX;
      const y0 = r * tileH + offsetY;
      
      // 繪製內縮矩形框
      ctx.strokeRect(x0 + inset, y0 + inset, tileW - inset * 2, tileH - inset * 2);
    }
  }
  
  insetCanvas.classList.remove('hidden');
}

function updateInfo() {
  if (!currentFile || !origImg.naturalWidth) return;
  const cols  = +document.getElementById('colsInput').value  || 1;
  const rows  = +document.getElementById('rowsInput').value  || 1;
  const inset = +document.getElementById('insetInput').value || 0;
  const tw = Math.floor(origImg.naturalWidth  / cols);
  const th = Math.floor(origImg.naturalHeight / rows);
  const cw = tw - inset * 2;
  const ch = th - inset * 2;
  infoDiv.innerHTML =
    `<span>圖片：<b>${origImg.naturalWidth} × ${origImg.naturalHeight}</b></span>` +
    `<span>格子：<b>${tw} × ${th}</b>（共 ${cols * rows} 格）</span>` +
    `<span>裁切：<b>${cw} × ${ch}</b> → <b>${tw} × ${th}</b></span>` +
    `<span>輸出：<b>${cols * rows + 1}</b> 張</span>`;
  infoDiv.classList.remove('hidden');
}

// ── Preview BG removal (debounce 400 ms) ─────
function schedulePreview() {
  if (!currentFile) return;
  clearTimeout(previewDebounce);
  previewDebounce = setTimeout(doPreview, 400);
}

async function doPreview() {
  if (!currentFile) return;
  previewLoading.classList.remove('hidden');
  const fd = new FormData();
  fd.append('file',      currentFile);
  fd.append('bg_color',  colorHex.value);
  fd.append('threshold', threshNum.value);
  try {
    const resp = await fetch('preview', { method: 'POST', body: fd });
    if (!resp.ok) return;
    const blob = await resp.blob();
    if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = URL.createObjectURL(blob);
    bgImg.src = previewObjectUrl;
    bgImg.classList.remove('hidden');
    bgPH.classList.add('hidden');
    bgImg.onload = () => {
      drawInsetGrid();
    };
  } catch (e) {
    console.error(e);
  } finally {
    previewLoading.classList.add('hidden');
  }
}

// ── Process & Download ───────────────────────
async function doProcess() {
  if (!currentFile) return;
  statusDiv.textContent = '處理中…';
  statusDiv.classList.remove('hidden');
  downloadBtn.disabled = true;

  const fd = new FormData();
  fd.append('file',      currentFile);
  fd.append('bg_color',  colorHex.value);
  fd.append('threshold', threshNum.value);
  fd.append('cols',      document.getElementById('colsInput').value);
  fd.append('rows',      document.getElementById('rowsInput').value);
  fd.append('inset',     document.getElementById('insetInput').value);
  fd.append('offset_x',  document.getElementById('offsetXInput').value);
  fd.append('offset_y',  document.getElementById('offsetYInput').value);

  try {
    const resp = await fetch('process', { method: 'POST', body: fd });
    if (!resp.ok) {
      statusDiv.textContent = '錯誤：' + await resp.text();
      return;
    }
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'inset_crop_output.zip';
    a.click();
    URL.revokeObjectURL(url);
    statusDiv.textContent = '下載完成！';
  } catch (e) {
    statusDiv.textContent = '網路錯誤：' + e.message;
  } finally {
    downloadBtn.disabled = false;
  }
}
</script>
</body>
</html>
"""


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.post("/preview")
async def preview_bg(
    file: UploadFile = File(...),
    bg_color: str = Form("#ff00ff"),
    threshold: float = Form(100.0),
):
    """去底色後回傳 PNG，供前端即時預覽。"""
    raw = await file.read()
    try:
        src = Image.open(io.BytesIO(raw))
        result = remove_background(src, bg_color, threshold)
    except ValueError as e:
        return PlainTextResponse(str(e), status_code=400)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.post("/process")
async def process(
    file: UploadFile = File(...),
    bg_color: str = Form("#ff00ff"),
    threshold: float = Form(100.0),
    cols: int = Form(...),
    rows: int = Form(...),
    inset: int = Form(...),
    offset_x: int = Form(0),
    offset_y: int = Form(0),
):
    """去底色 → 內縮裁切 → 打包 ZIP 下載。"""
    raw = await file.read()
    try:
        src = Image.open(io.BytesIO(raw))
        src = remove_background(src, bg_color, threshold)
    except ValueError as e:
        return PlainTextResponse(str(e), status_code=400)

    W, H = src.size
    tile_w = W // cols
    tile_h = H // rows

    if inset * 2 >= tile_w or inset * 2 >= tile_h:
        return PlainTextResponse("內縮距離過大，超出格子尺寸", status_code=400)

    tiles: list[Image.Image] = []
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * tile_w, r * tile_h
            cropped = src.crop((x0 + offset_x + inset, y0 + offset_y + inset, x0 + offset_x + tile_w - inset, y0 + offset_y + tile_h - inset))
            resized = cropped.resize((tile_w, tile_h), Image.NEAREST)
            tiles.append(resized)

    combined = Image.new("RGBA", (cols * tile_w, rows * tile_h), (0, 0, 0, 0))
    for idx, tile in enumerate(tiles):
        r, c = divmod(idx, cols)
        combined.paste(tile, (c * tile_w, r * tile_h))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, tile in enumerate(tiles):
            r, c = divmod(idx, cols)
            tb = io.BytesIO()
            tile.save(tb, format="PNG")
            zf.writestr(f"tiles/tile_r{r:02d}_c{c:02d}.png", tb.getvalue())
        cb = io.BytesIO()
        combined.save(cb, format="PNG")
        zf.writestr("combined.png", cb.getvalue())

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=inset_crop_output.zip"},
    )


# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("inset_crop_tool:app", host="0.0.0.0", port=8003, reload=True)
