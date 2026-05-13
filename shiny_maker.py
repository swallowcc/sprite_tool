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
<body class="bg-slate-900 text-white">
    <div class="max-w-7xl mx-auto space-y-6 p-4 pt-20">
        <header class="border-b border-slate-700 pb-2">
            <h1 class="text-xl font-bold">✨ Shiny Maker</h1>
            <p class="text-slate-400 text-sm mt-2">全維度色違調整工具，支援 HSV 色相、飽和度、亮度變化</p>
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

                <div class="space-y-4">
                    <div class="flex justify-between text-sm">
                        <label class="font-medium text-slate-300">5. 染色強度 (Tint Strength)</label>
                        <span id="tintVal" class="text-blue-400 font-mono">0.0</span>
                    </div>
                    <input id="tintStrength" type="range" min="0" max="1" step="0.1" value="0.0" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-pink-500">
                    <p class="text-[10px] text-slate-500">專門處理灰色/單色怪物。0.0 為原本邏輯，1.0 為強行染色。</p>
                </div>

                <div class="space-y-2">
                    <label class="text-sm font-medium text-slate-300">6. 飽和度過濾 (Saturation Mask)</label>
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
        // 在 script 標籤開頭增加變數宣告
        const tintStrength = document.getElementById('tintStrength');
        const tintVal = document.getElementById('tintVal');

        let currentFile = null, timer = null;

        function g(id){ return document.getElementById(id); }

        // 事件綁定
        hueRange.oninput = () => { hueVal.innerText = hueRange.value; throttledProcess(); };
        satScale.oninput = () => { satScaleVal.innerText = satScale.value; throttledProcess(); };
        valScale.oninput = () => { valScaleVal.innerText = valScale.value; throttledProcess(); };
        satMin.oninput = () => { throttledProcess(); };
        
        // 增加監聽事件
        tintStrength.oninput = () => { 
            tintVal.innerText = tintStrength.value; 
            throttledProcess(); 
        };

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
            fd.append('hue_shift', document.getElementById('hueRange').value);
            fd.append('sat_min', document.getElementById('satMin').value);
            fd.append('sat_scale', document.getElementById('satScale').value);
            fd.append('val_scale', document.getElementById('valScale').value);
            
            // --- 新增這一行 ---
            fd.append('tint_strength', tintStrength.value); 

            try {
                // 請確保 fetch 的路徑是相對路徑 'process_shiny' (為了 main.py 整合)
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
    sat_scale: float = Form(...),
    val_scale: float = Form(...),
    # 新增參數：染色強度 (0.0 為原本邏輯, 1.0 為完全強制染色)
    tint_strength: float = Form(0.0) 
):
    try:
        data = await file.read()
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        # 頻道分離 (處理透明度)
        if img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha = img[:, :, 3]
        else:
            bgr = img
            alpha = None

        # --- 針對低飽和度怪物的優化處理 ---
        if tint_strength > 0:
            # 1. 將圖片轉為灰階獲取亮度資訊
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            
            # 2. 建立目標顏色 (根據 Hue 決定目標色)
            # 建立一個單一像素的 HSV，轉回 BGR 獲得目標色
            target_hsv = np.array([[[hue_shift, 200, 255]]], dtype=np.uint8)
            target_color = cv2.cvtColor(target_hsv, cv2.COLOR_HSV2BGR)[0][0]
            
            # 3. 線性混合：將亮度圖對應到目標顏色
            # 亮度越高的地方顏色越亮，亮度越低顏色越深
            tinted = np.zeros_like(bgr, dtype=np.float32)
            for i in range(3): # B, G, R
                tinted[:, :, i] = (gray / 255.0) * target_color[i]
            
            # 4. 根據強度與原圖混合
            bgr = cv2.addWeighted(bgr.astype(np.float32), 1 - tint_strength, tinted, tint_strength, 0)
            bgr = np.clip(bgr, 0, 255).astype(np.uint8)

        # --- 原始 HSV 調整 (對染色後的結果再做 S/V 微調) ---
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)
        
        # 僅在 tint_strength 為 0 時旋轉色相，避免衝突
        if tint_strength == 0:
            mask = s > (float(sat_min) * 2.55)
            h[mask] = (h[mask] + float(hue_shift)) % 180
            
        s = np.clip(s * sat_scale, 0, 255)
        v = np.clip(v * val_scale, 0, 255)
        
        hsv_new = cv2.merge([h, s, v]).astype(np.uint8)
        res_bgr = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)

        # 重組 Alpha 並回傳
        if alpha is not None:
            res = cv2.merge([res_bgr, alpha])
        else:
            res = res_bgr

        _, buffer = cv2.imencode('.png', res)
        return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type='image/png')
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)