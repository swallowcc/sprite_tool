"""
Simple Sprite Splitter
上傳圖片 → 輸入 cols/rows → 下載分割後的 ZIP
"""

import io
import zipfile
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from PIL import Image

app = FastAPI()


HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8">
  <title>Sprite Splitter</title>
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
<div class="max-w-6xl mx-auto space-y-6 p-6 pt-20">

  <header class="border-b border-slate-700 pb-2">
    <h1 class="text-xl font-bold">📦 Sprite Splitter</h1>
    <p class="text-slate-400 text-sm mt-2">快速分割圖片為網格並打包為 ZIP</p>
  </header>

  <!-- ── Controls ── -->
  <div class="bg-slate-800 rounded-2xl p-5 space-y-4">
    
    <!-- 上傳區域 -->
    <div class="space-y-2">
      <label class="block text-xs text-slate-400 font-semibold">上傳圖片</label>
      <div class="border-2 border-dashed border-slate-600 rounded-xl p-6 text-center hover:border-blue-500 transition cursor-pointer"
           onclick="document.getElementById('fileInput').click()">
        <p id="uploadPH" class="text-slate-400">點擊上傳或拖拽圖片</p>
        <img id="previewImg" class="hidden max-h-40 mx-auto mt-3" style="image-rendering:pixelated">
      </div>
      <input id="fileInput" type="file" accept="image/*" class="hidden">
    </div>

    <!-- 設定區域 -->
    <div class="grid grid-cols-3 gap-4">
      <div>
        <label class="block text-xs text-slate-400 mb-2 font-semibold">Columns</label>
        <input id="colsInput" type="number" value="4" min="1"
               class="w-full p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
      </div>
      <div>
        <label class="block text-xs text-slate-400 mb-2 font-semibold">Rows</label>
        <input id="rowsInput" type="number" value="4" min="1"
               class="w-full p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
      </div>
      <div class="flex flex-col justify-end">
        <button id="downloadBtn" disabled onclick="doDownload()"
                class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600
                       disabled:cursor-not-allowed rounded-lg font-semibold transition text-white">
          ⬇ 下載 ZIP
        </button>
      </div>
    </div>

    <!-- 資訊顯示 -->
    <div id="info" class="hidden bg-slate-700/50 rounded-lg px-4 py-2 text-sm text-slate-300 space-y-1"></div>
    <div id="status" class="hidden text-sm text-slate-400"></div>
  </div>

  <!-- ── Preview ── -->
  <div class="bg-slate-800 rounded-2xl p-4">
    <p class="text-sm font-semibold text-slate-400 mb-3">預覽（分割線）</p>
    <div class="relative flex items-center justify-center rounded-lg bg-slate-700 min-h-64 overflow-auto">
      <img id="previewMainImg" class="hidden max-w-full object-contain" style="image-rendering:pixelated">
      <canvas id="gridCanvas" class="hidden absolute top-0 left-0" style="image-rendering:pixelated;"></canvas>
      <p id="previewPH" class="text-slate-500 text-sm">尚未上傳圖片</p>
    </div>
  </div>

</div>

<script>
let currentFile = null;

const fileInput = document.getElementById('fileInput');
const uploadPH = document.getElementById('uploadPH');
const previewImg = document.getElementById('previewImg');
const previewMainImg = document.getElementById('previewMainImg');
const gridCanvas = document.getElementById('gridCanvas');
const previewPH = document.getElementById('previewPH');
const infoDiv = document.getElementById('info');
const statusDiv = document.getElementById('status');
const downloadBtn = document.getElementById('downloadBtn');

// ── File upload ──
fileInput.addEventListener('change', () => {
  const f = fileInput.files[0];
  if (!f) return;
  currentFile = f;
  const url = URL.createObjectURL(f);
  previewImg.src = url;
  previewImg.classList.remove('hidden');
  uploadPH.classList.add('hidden');
  previewMainImg.src = url;
  previewMainImg.onload = () => {
    previewMainImg.classList.remove('hidden');
    previewPH.classList.add('hidden');
    updateInfo();
    drawGrid();
  };
  downloadBtn.disabled = false;
});

// ── Drag & drop ──
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => {
  e.preventDefault();
  const f = e.dataTransfer.files[0];
  if (f && f.type.startsWith('image/')) {
    fileInput.files = e.dataTransfer.files;
    fileInput.dispatchEvent(new Event('change'));
  }
});

// ── Update grid on input change ──
['colsInput', 'rowsInput'].forEach(id =>
  document.getElementById(id).addEventListener('input', () => {
    updateInfo();
    drawGrid();
  }));

// ── Draw grid lines ──
function drawGrid() {
  if (!previewMainImg.naturalWidth || previewMainImg.classList.contains('hidden')) return;
  
  const cols = +document.getElementById('colsInput').value || 1;
  const rows = +document.getElementById('rowsInput').value || 1;
  
  const imgW = previewMainImg.naturalWidth;
  const imgH = previewMainImg.naturalHeight;
  const tileW = imgW / cols;
  const tileH = imgH / rows;
  
  gridCanvas.width = imgW;
  gridCanvas.height = imgH;
  
  const displayW = previewMainImg.offsetWidth;
  const displayH = previewMainImg.offsetHeight;
  const offsetLeft = previewMainImg.offsetLeft;
  const offsetTop = previewMainImg.offsetTop;
  
  gridCanvas.style.width = displayW + 'px';
  gridCanvas.style.height = displayH + 'px';
  gridCanvas.style.left = offsetLeft + 'px';
  gridCanvas.style.top = offsetTop + 'px';
  
  const ctx = gridCanvas.getContext('2d');
  ctx.clearRect(0, 0, imgW, imgH);
  ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
  ctx.lineWidth = 1;
  
  // 縱線
  for (let c = 1; c < cols; c++) {
    const x = c * tileW;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, imgH);
    ctx.stroke();
  }
  
  // 橫線
  for (let r = 1; r < rows; r++) {
    const y = r * tileH;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(imgW, y);
    ctx.stroke();
  }
  
  gridCanvas.classList.remove('hidden');
}

// ── Update info ──
function updateInfo() {
  if (!currentFile || !previewMainImg.naturalWidth) return;
  const cols = +document.getElementById('colsInput').value || 1;
  const rows = +document.getElementById('rowsInput').value || 1;
  const tw = Math.floor(previewMainImg.naturalWidth / cols);
  const th = Math.floor(previewMainImg.naturalHeight / rows);
  
  infoDiv.innerHTML = `
    <span>圖片：<b>${previewMainImg.naturalWidth} × ${previewMainImg.naturalHeight}</b></span>
    <span>每格：<b>${tw} × ${th}</b>（共 ${cols * rows} 格）</span>
  `;
  infoDiv.classList.remove('hidden');
}

// ── Download ──
async function doDownload() {
  if (!currentFile) return;
  statusDiv.textContent = '處理中…';
  statusDiv.classList.remove('hidden');
  downloadBtn.disabled = true;
  
  const fd = new FormData();
  fd.append('file', currentFile);
  fd.append('cols', document.getElementById('colsInput').value);
  fd.append('rows', document.getElementById('rowsInput').value);
  
  try {
    const resp = await fetch('process', { method: 'POST', body: fd });
    if (!resp.ok) {
      statusDiv.textContent = '錯誤：' + await resp.text();
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sprite_split.zip';
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


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.post("/process")
async def process(
    file: UploadFile = File(...),
    cols: int = Form(...),
    rows: int = Form(...),
):
    """分割圖片並打包為 ZIP。"""
    raw = await file.read()
    try:
        src = Image.open(io.BytesIO(raw))
        src = src.convert("RGBA")
    except Exception as e:
        return PlainTextResponse(f"圖片載入失敗：{str(e)}", status_code=400)

    W, H = src.size
    tile_w = W // cols
    tile_h = H // rows

    tiles: list[Image.Image] = []
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * tile_w, r * tile_h
            cropped = src.crop((x0, y0, x0 + tile_w, y0 + tile_h))
            tiles.append(cropped)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, tile in enumerate(tiles):
            r, c = divmod(idx, cols)
            tb = io.BytesIO()
            tile.save(tb, format="PNG")
            zf.writestr(f"tile_r{r:02d}_c{c:02d}.png", tb.getvalue())

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=sprite_split.zip"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sprite_splitter:app", host="0.0.0.0", port=8004, reload=True)
