import io
import math
import os
import re
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from PIL import Image

app = FastAPI()

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)


def natural_name_key(full_name: str) -> tuple[list[object], str]:
  normalized = (full_name or "").replace("\\", "/")
  base = os.path.basename(normalized)
  parts = re.split(r"(\d+)", base.lower())
  key: list[object] = [int(p) if p.isdigit() else p for p in parts]
  return key, normalized.lower()

HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8">
  <title>Folder Sprite Builder</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white">
<div class="max-w-6xl mx-auto p-6 pt-20 space-y-6">
  <header class="border-b border-slate-700 pb-2">
    <h1 class="text-xl font-bold">🗂️ Folder Sprite Builder</h1>
    <p class="text-slate-400 text-sm mt-2">選擇資料夾後，依 Columns 與總寬度自動縮放並合併為 Sprite 圖</p>
  </header>

  <div class="bg-slate-800 rounded-2xl p-5 space-y-4">
    <div>
      <label class="block text-xs text-slate-400 font-semibold mb-2">指定資料夾（會讀取該資料夾中的圖片）</label>
      <input id="folderInput" type="file" webkitdirectory directory multiple
             class="w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer" />
      <p class="text-xs text-slate-500 mt-2">支援 png/jpg/jpeg/webp/bmp/gif</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <label class="block text-xs text-slate-400 mb-2 font-semibold">Columns</label>
        <input id="colsInput" type="number" min="1" value="6"
               class="w-full p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
      </div>
      <div>
        <label class="block text-xs text-slate-400 mb-2 font-semibold">總寬度（px）</label>
        <input id="totalWidthInput" type="number" min="1" value="1200"
               class="w-full p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
      </div>
      <div>
        <label class="block text-xs text-slate-400 mb-2 font-semibold">輸出檔名</label>
        <input id="outputNameInput" type="text" value="folder_sprite.png"
               class="w-full p-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
      </div>
      <div class="flex items-end">
        <button id="exportBtn" onclick="doExport()"
                class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg font-semibold transition text-white">
          ⬇ 輸出並下載
        </button>
      </div>
    </div>

    <div id="summary" class="hidden bg-slate-700/40 rounded-lg p-3 text-sm text-slate-200"></div>
    <div id="status" class="hidden text-sm text-slate-300"></div>
  </div>

  <div class="bg-slate-800 rounded-2xl p-4">
    <p class="text-sm font-semibold text-slate-400 mb-2">目前資料夾中的圖片</p>
    <div id="filesList" class="text-sm text-slate-300 max-h-60 overflow-auto bg-slate-900/40 rounded-lg p-3"></div>
  </div>
</div>

<script>
const folderInput = document.getElementById('folderInput');
const colsInput = document.getElementById('colsInput');
const totalWidthInput = document.getElementById('totalWidthInput');
const outputNameInput = document.getElementById('outputNameInput');
const summary = document.getElementById('summary');
const statusDiv = document.getElementById('status');
const filesList = document.getElementById('filesList');
const exportBtn = document.getElementById('exportBtn');

let selectedImages = [];

function isImageFile(fileName) {
  const n = fileName.toLowerCase();
  return n.endsWith('.png') || n.endsWith('.jpg') || n.endsWith('.jpeg') || n.endsWith('.webp') || n.endsWith('.bmp') || n.endsWith('.gif');
}

function showStatus(text, kind = 'normal') {
  statusDiv.classList.remove('hidden');
  statusDiv.textContent = text;
  if (kind === 'error') {
    statusDiv.classList.remove('text-slate-300');
    statusDiv.classList.add('text-red-400');
  } else {
    statusDiv.classList.remove('text-red-400');
    statusDiv.classList.add('text-slate-300');
  }
}

function updateSummary() {
  const cols = parseInt(colsInput.value || '0', 10);
  const totalWidth = parseInt(totalWidthInput.value || '0', 10);

  if (selectedImages.length === 0) {
    summary.classList.add('hidden');
    filesList.innerHTML = '<p class="text-slate-500">尚未選擇資料夾</p>';
    return;
  }

  const rows = cols > 0 ? Math.ceil(selectedImages.length / cols) : 0;
  const tileWidth = cols > 0 ? Math.floor(totalWidth / cols) : 0;

  summary.innerHTML = `
    <p>圖片數量：<span class="font-semibold">${selectedImages.length}</span></p>
    <p>預估排版：<span class="font-semibold">${rows}</span> 行，每行最多 <span class="font-semibold">${cols}</span> 張</p>
    <p>每張目標寬度：<span class="font-semibold">${tileWidth}px</span>（由 ${totalWidth} / ${cols} 計算）</p>
  `;
  summary.classList.remove('hidden');

  const items = selectedImages
    .slice(0, 200)
    .map((f, idx) => `<div class="py-0.5"><span class="text-slate-500 mr-2">${idx + 1}.</span>${f.name}</div>`)
    .join('');

  filesList.innerHTML = items || '<p class="text-slate-500">沒有可用圖片</p>';
}

folderInput.addEventListener('change', () => {
  const allFiles = Array.from(folderInput.files || []);
  selectedImages = allFiles.filter((f) => isImageFile(f.name));

  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
  selectedImages.sort((a, b) => {
    const baseA = (a.name || '').toLowerCase();
    const baseB = (b.name || '').toLowerCase();
    const byBase = collator.compare(baseA, baseB);
    if (byBase !== 0) return byBase;

    const relA = (a.webkitRelativePath || a.name || '').toLowerCase();
    const relB = (b.webkitRelativePath || b.name || '').toLowerCase();
    return collator.compare(relA, relB);
  });

  updateSummary();
  if (selectedImages.length > 0) {
    showStatus(`已選擇 ${selectedImages.length} 張圖片`);
  } else {
    showStatus('資料夾中沒有可用圖片', 'error');
  }
});

colsInput.addEventListener('input', updateSummary);
totalWidthInput.addEventListener('input', updateSummary);

async function doExport() {
  if (selectedImages.length === 0) {
    showStatus('請先指定資料夾並確認內有圖片', 'error');
    return;
  }

  const cols = parseInt(colsInput.value || '0', 10);
  const totalWidth = parseInt(totalWidthInput.value || '0', 10);

  if (!Number.isInteger(cols) || cols <= 0) {
    showStatus('Columns 必須是大於 0 的整數', 'error');
    return;
  }

  if (!Number.isInteger(totalWidth) || totalWidth <= 0) {
    showStatus('總寬度必須是大於 0 的整數', 'error');
    return;
  }

  const outputName = (outputNameInput.value || 'folder_sprite.png').trim() || 'folder_sprite.png';

  const fd = new FormData();
  fd.append('cols', String(cols));
  fd.append('total_width', String(totalWidth));
  fd.append('output_name', outputName);

  selectedImages.forEach((f) => fd.append('files', f, f.webkitRelativePath || f.name));

  exportBtn.disabled = true;
  showStatus('處理中，請稍候...');

  try {
    const res = await fetch('/folder-builder/build', { method: 'POST', body: fd });
    if (!res.ok) {
      const text = await res.text();
      showStatus(`輸出失敗：${text}`, 'error');
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = outputName.toLowerCase().endsWith('.png') ? outputName : `${outputName}.png`;
    a.click();
    URL.revokeObjectURL(url);

    showStatus('輸出完成，已開始下載');
  } catch (err) {
    showStatus(`輸出失敗：${err}`, 'error');
  } finally {
    exportBtn.disabled = false;
  }
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.post("/build")
async def build_folder_sprite(
    files: list[UploadFile] = File(...),
    cols: int = Form(...),
    total_width: int = Form(...),
    output_name: str = Form("folder_sprite.png"),
):
    if cols <= 0:
        return PlainTextResponse("Columns 必須大於 0", status_code=400)
    if total_width <= 0:
        return PlainTextResponse("總寬度必須大於 0", status_code=400)

    tile_w = total_width // cols
    if tile_w <= 0:
        return PlainTextResponse("總寬度過小，請提高總寬度或降低 Columns", status_code=400)

    image_files: list[UploadFile] = []
    for f in files:
        _, ext = os.path.splitext((f.filename or "").lower())
        if ext in ALLOWED_EXTENSIONS:
            image_files.append(f)

    if not image_files:
        return PlainTextResponse("找不到可用圖片檔", status_code=400)

    image_files.sort(key=lambda f: natural_name_key(f.filename or ""))

    resized_images: list[Image.Image] = []
    resized_heights: list[int] = []

    for f in image_files:
        try:
            data = await f.read()
            img = Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            continue

        if img.width <= 0 or img.height <= 0:
            continue

        ratio = min(1.0, tile_w / float(img.width))
        new_w = max(1, int(round(img.width * ratio)))
        new_h = max(1, int(round(img.height * ratio)))
        resized = img.resize((new_w, new_h), RESAMPLE_LANCZOS)

        resized_images.append(resized)
        resized_heights.append(new_h)

    if not resized_images:
        return PlainTextResponse("圖片讀取失敗，請確認檔案格式", status_code=400)

    cell_h = max(resized_heights)
    rows = math.ceil(len(resized_images) / cols)
    out_h = rows * cell_h

    sheet = Image.new("RGBA", (total_width, out_h), (0, 0, 0, 0))

    for idx, img in enumerate(resized_images):
        row = idx // cols
        col = idx % cols

        x = col * tile_w + (tile_w - img.width) // 2
        y = row * cell_h + (cell_h - img.height) // 2
        sheet.paste(img, (x, y), img)

    final_name = output_name.strip() or "folder_sprite.png"
    if not final_name.lower().endswith(".png"):
        final_name += ".png"

    buf = io.BytesIO()
    sheet.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{final_name}"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("folder_sprite_builder:app", host="0.0.0.0", port=8005, reload=True)
