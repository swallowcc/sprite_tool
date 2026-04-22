import traceback
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse
import cv2
import numpy as np
from PIL import Image
import io, os, base64

app = FastAPI()
BASE = os.getcwd()
OUTPUT_DIR = os.path.join(BASE, 'shiny_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .pixelated { image-rendering: pixelated; }
        /* 統一捲軸樣式，避免 Webkit 預設樣式不一 */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1e293b; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
    </style>
</head>
<body class="bg-slate-900 text-white p-4">
    <div class="max-w-4xl mx-auto space-y-6">
        <header class="border-b border-slate-700 pb-4">
            <h1 class="text-3xl font-bold text-blue-400">Shiny Monster Maker Pro</h1>
            <p class="text-slate-400">全維度色違調整工具 (HSV 模式)</p>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="bg-slate-800 p-6 rounded-2xl space-y-6">
                <div class="space-y-2">
                    <label class="text-sm font-medium text-slate-300">1. 上傳原始圖片</label>
                    <input id="file" type="file" accept="image/*" class="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500">
                </div>

                <div class="space-y-4">
                    <div class="flex justify-between text-sm">
                        <label class="font-medium text-slate-300">2. 色調偏移 (Hue Shift)</label>
                        <span id="hueVal" class="text-blue-400 font-mono">0</span>
                    </div>
                    <input id="hueRange" type="range" min="0" max="180" value="0" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500">
                </div>

                <div class="space-y-4">
                    <div class="flex justify-between text-sm">
                        <label class="font-medium text-slate-300">3. 飽和度倍率 (Saturation)</label>
                        <span id="satScaleVal" class="text-blue-400 font-mono">1.0</span>
                    </div>
                    <input id="satScale" type="range" min="0" max="2" step="0.1" value="1.0" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500">
                </div>

                <div class="space-y-4">
                    <div class="flex justify-between text-sm">
                        <label class="font-medium text-slate-300">4. 亮度倍率 (Brightness)</label>
                        <span id="valScaleVal" class="text-blue-400 font-mono">1.0</span>
                    </div>
                    <input id="valScale" type="range" min="0" max="2" step="0.1" value="1.0" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500">
                </div>

                <div class="space-y-2">
                    <label class="text-sm font-medium text-slate-300">5. 飽和度過濾 (Saturation Mask)</label>
                    <input id="satMin" type="range" min="0" max="100" value="30" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-slate-500">
                    <p class="text-[10px] text-slate-500">避免影響灰色/黑色區塊</p>
                </div>

                <div class="flex gap-2 pt-4">
                    <button onclick="processImage()" class="flex-1 py-4 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold shadow-lg transition-all active:scale-95">更新預覽</button>
                    <button onclick="downloadImage()" id="btnDownload" class="px-6 py-4 bg-slate-700 hover:bg-slate-600 rounded-xl text-sm hidden">下載</button>
                </div>
            </div>

            <div class="bg-slate-800 p-6 rounded-2xl flex flex-col items-center justify-center border-2 border-dashed border-slate-700">
                <p id="placeholder" class="text-slate-500 text-sm font-mono italic">AWAITING IMAGE...</p>
                <img id="preview" class="max-w-full h-auto rounded shadow-2xl pixelated hidden">
            </div>
        </div>
    </div>

    <script>
        const hueRange = g('hueRange'), satMin = g('satMin'), satScale = g('satScale'), valScale = g('valScale');
        const hueVal = g('hueVal'), satScaleVal = g('satScaleVal'), valScaleVal = g('valScaleVal');
        const preview = g('preview'), placeholder = g('placeholder'), btnDownload = g('btnDownload');

        let currentFile = null, timer = null;

        function g(id){ return document.getElementById(id); }

        // 事件綁定
        hueRange.oninput = () => { hueVal.innerText = hueRange.value; throttledProcess(); };
        satScale.oninput = () => { satScaleVal.innerText = satScale.value; throttledProcess(); };
        valScale.oninput = () => { valScaleVal.innerText = valScale.value; throttledProcess(); };
        satMin.oninput = () => { throttledProcess(); };

        document.getElementById('file').onchange = (e) => {
            currentFile = e.target.files[0];
            if (currentFile) processImage(); 
        };

        function throttledProcess() {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => { processImage(); }, 50);
        }

        async function processImage() {
            if (!currentFile) return;
            const fd = new FormData();
            fd.append('file', currentFile);
            fd.append('hue_shift', hueRange.value);
            fd.append('sat_min', satMin.value);
            fd.append('sat_scale', satScale.value);
            fd.append('val_scale', valScale.value);

            try {
                const r = await fetch('process_shiny', { method: 'POST', body: fd });
                if (!r.ok) throw new Error('Backend process failed');
                const blob = await r.blob();
                if (preview.src) URL.revokeObjectURL(preview.src);
                preview.src = URL.createObjectURL(blob);
                preview.classList.remove('hidden');
                placeholder.classList.add('hidden');
                btnDownload.classList.remove('hidden');
            } catch (e) {
                console.error(e);
            }
        }

        function downloadImage() {
            const a = document.createElement('a');
            a.href = preview.src;
            a.download = `shiny_h${hueRange.value}_s${satScale.value}_v${valScale.value}.png`;
            a.click();
        }
    </script>
    <style>.pixelated { image-rendering: pixelated; }</style>
</body></html>'''

@app.get('/', response_class=HTMLResponse)
def home():
    return HTML

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # 在終端機印出完整的錯誤追蹤
        traceback.print_exc() 
        return JSONResponse(
            status_code=500,
            content={"message": str(e), "traceback": traceback.format_exc()}
        )

@app.post('/process_shiny')
async def process_shiny(
    file: UploadFile = File(...),
    hue_shift: int = Form(...),
    sat_min: int = Form(...),
    sat_scale: float = Form(...), # 新增：飽和度倍率
    val_scale: float = Form(...)  # 新增：亮度倍率
):
    try:
        data = await file.read()
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        if img is None: return JSONResponse(status_code=400, content={"message": "解碼失敗"})

        # 頻道判斷
        if img.ndim == 2:
            bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR); alpha = None
        elif img.shape[2] == 3:
            bgr = img; alpha = None
        else:
            bgr = img[:, :, :3]; alpha = img[:, :, 3]

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)

        # 遮罩邏輯
        mask = s > (float(sat_min) * 2.55)

        # --- 核心變色邏輯 ---
        # 1. 色相旋轉
        h[mask] = (h[mask] + float(hue_shift)) % 180
        
        # 2. 飽和度調整 (乘法運算並限制範圍 0-255)
        s[mask] = np.clip(s[mask] * sat_scale, 0, 255)
        
        # 3. 亮度調整 (乘法運算並限制範圍 0-255)
        v[mask] = np.clip(v[mask] * val_scale, 0, 255)

        # 合併與轉換回 BGR
        hsv_new = cv2.merge([h, s, v]).astype(np.uint8)
        bgr_new = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)

        if alpha is not None:
            res = cv2.merge([bgr_new, alpha])
        else:
            res = bgr_new

        _, buffer = cv2.imencode('.png', res)
        return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type='image/png')
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)