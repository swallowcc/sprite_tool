import cv2
import io
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sprite Flipper</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .pixelated { image-rendering: pixelated; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1e293b; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
    </style>
</head>
<body class="bg-slate-900 text-white">
<div class="max-w-7xl mx-auto space-y-6 p-6 pt-20">
    <header class="border-b border-slate-700 pb-2">
        <h1 class="text-xl font-bold">🔄 Flipper</h1>
        <p class="text-slate-400 text-sm mt-2">將 Sprite Sheet 中每個格子水平翻轉（左右鏡像），並輸出新圖片</p>
    </header>

    <div class="bg-slate-800 p-6 rounded-2xl border border-slate-700">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
                <label class="block text-xs text-slate-400 mb-1">Columns（列數）</label>
                <input id="cols" type="number" value="10" min="1"
                    class="w-full p-2 rounded-lg bg-slate-700 text-white border border-slate-600 focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-slate-400 mb-1">Rows（行數）</label>
                <input id="rows" type="number" value="6" min="1"
                    class="w-full p-2 rounded-lg bg-slate-700 text-white border border-slate-600 focus:outline-none focus:border-blue-500">
            </div>
        </div>

        <div class="mb-6">
            <label class="block text-xs text-slate-400 mb-2">上傳 Sprite Sheet（PNG / GIF 等）</label>
            <div id="dropzone"
                class="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 transition"
                onclick="document.getElementById('fileInput').click()">
                <p id="dropLabel" class="text-slate-400 text-sm">點擊或拖曳圖片至此處</p>
            </div>
            <input id="fileInput" type="file" accept="image/*" class="hidden">
        </div>

        <div id="previewSection" class="hidden mb-6 space-y-2">
            <p class="text-xs text-slate-400">預覽（原圖）</p>
            <img id="preview" class="max-w-full rounded-lg border border-slate-700 pixelated">
        </div>

        <button id="flipBtn" onclick="doFlip()"
            class="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold transition disabled:opacity-50 disabled:cursor-not-allowed"
            disabled>
            🔄 執行翻轉並下載
        </button>

        <div id="status" class="mt-4 text-sm text-center text-slate-400 hidden"></div>
    </div>

    <div id="resultSection" class="hidden bg-slate-800 p-6 rounded-2xl border border-slate-700 space-y-3">
        <p class="text-sm text-slate-400">輸出結果預覽</p>
        <img id="resultImg" class="max-w-full rounded-lg border border-slate-700 pixelated">
        <a id="downloadLink" class="inline-block mt-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg font-bold transition text-sm">
            ⬇ 下載翻轉後圖片
        </a>
    </div>

</div>

<script>
let fileBlob = null;

const fileInput = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
const flipBtn  = document.getElementById('flipBtn');

function loadFile(file) {
    if (!file) return;
    fileBlob = file;
    document.getElementById('dropLabel').textContent = file.name;
    const url = URL.createObjectURL(file);
    document.getElementById('preview').src = url;
    document.getElementById('previewSection').classList.remove('hidden');
    flipBtn.disabled = false;
    document.getElementById('resultSection').classList.add('hidden');
}

fileInput.addEventListener('change', e => loadFile(e.target.files[0]));

dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('border-blue-500'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('border-blue-500'));
dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('border-blue-500');
    loadFile(e.dataTransfer.files[0]);
});

async function doFlip() {
    if (!fileBlob) return;
    const cols = parseInt(document.getElementById('cols').value) || 10;
    const rows = parseInt(document.getElementById('rows').value) || 6;

    flipBtn.disabled = true;
    const status = document.getElementById('status');
    status.textContent = '⏳ 處理中...';
    status.classList.remove('hidden');

    const fd = new FormData();
    fd.append('file', fileBlob);
    fd.append('cols', cols);
    fd.append('rows', rows);

    try {
        const r = await fetch('flip', { method: 'POST', body: fd });
        if (!r.ok) {
            status.textContent = '❌ 處理失敗：' + await r.text();
            flipBtn.disabled = false;
            return;
        }
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);

        document.getElementById('resultImg').src = url;
        const dl = document.getElementById('downloadLink');
        dl.href = url;
        const ext = fileBlob.name.split('.').pop();
        dl.download = fileBlob.name.replace(/\.[^.]+$/, '') + '_flipped.' + ext;
        document.getElementById('resultSection').classList.remove('hidden');
        status.textContent = '✅ 完成！';
    } catch(e) {
        status.textContent = '❌ 發生錯誤：' + e.message;
    }
    flipBtn.disabled = false;
}
</script>
</body>
</html>'''


def _flip_sprite_sheet(img_bytes: bytes, cols: int, rows: int) -> bytes:
    """核心翻轉邏輯（來自 rotate.py）：將每個 cell 水平翻轉。"""
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("無法解碼圖片")

    h, w = img.shape[:2]
    cell_w = w / cols
    cell_h = h / rows
    output = img.copy()

    for r in range(rows):
        for c in range(cols):
            x1 = int(c * cell_w)
            y1 = int(r * cell_h)
            x2 = int((c + 1) * cell_w)
            y2 = int((r + 1) * cell_h)

            cell = img[y1:y2, x1:x2]
            if cell.size == 0:
                continue

            output[y1:y2, x1:x2] = cv2.flip(cell, 1)

    success, buf = cv2.imencode(".png", output)
    if not success:
        raise ValueError("圖片編碼失敗")
    return buf.tobytes()


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.post("/flip")
async def flip(
    file: UploadFile = File(...),
    cols: int = Form(10),
    rows: int = Form(6),
):
    data = await file.read()
    try:
        result = _flip_sprite_sheet(data, cols, rows)
    except ValueError as e:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(str(e), status_code=400)

    return StreamingResponse(
        io.BytesIO(result),
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="flipped.png"'},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
