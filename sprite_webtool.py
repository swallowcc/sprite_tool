import zipfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from PIL import Image
import io, math, json, os

app = FastAPI()
BASE = os.getcwd()
OUTPUT_DIR = os.path.join(BASE, 'output')
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
<div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-4">
    <div class="lg:col-span-1 bg-slate-800 p-4 rounded-2xl space-y-4">
        <h1 class="text-xl font-bold border-b border-slate-700 pb-2">Sprite Picker</h1>
        
        <div class="bg-blue-900/30 p-3 rounded-lg border border-blue-700/50">
            <p class="text-xs text-blue-200 mb-1">Total Selected</p>
            <span id="totalCount" class="text-2xl font-bold">0</span>
        </div>

        <div class="space-y-2">
            <div class="flex items-center gap-2">
                <span class="text-sm">WH:</span>
                <input id="wh" type="number" value="96" class="w-full p-2 rounded bg-slate-700 text-white border border-slate-600">
            </div>
            <div class="flex items-center gap-2">
                <span class="text-sm text-blue-300">Out WH:</span>
                <input id="outWH" type="number" value="96" class="w-full p-2 rounded bg-slate-700 text-white border border-blue-900">
            </div>
            <div class="flex items-center gap-2">
                <span class="text-sm">Cols:</span>
                <input id="outCols" type="number" value="10" class="w-full p-2 rounded bg-slate-700 text-white border border-slate-600">
            </div>
            <input id="name" value="sprites_export.png" class="w-full p-2 rounded bg-slate-700 text-white border border-slate-600">
        </div>

        <input id="file" type="file" accept="image/*" class="w-full text-xs">
        <button onclick="exportFile()" class="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold transition">Export Image</button>

        <div class="space-y-2">
            <label class="text-xs text-slate-400">Selected (Click image to remove)</label>
            <div id="previewList" class="grid grid-cols-4 gap-2 max-h-96 overflow-y-auto p-2 bg-black/20 rounded"></div>
        </div>
    </div>

    <div class="lg:col-span-3 bg-slate-800 p-4 rounded-2xl overflow-hidden relative min-h-[700px]">
        <canvas id="cv" class="border border-slate-700 w-full cursor-none"></canvas>
    </div>
</div>

<script>
let img=null, fileBlob=null, picks=[], scale=1, offX=0, offY=0;
let isPanning=false, lastMouseX=0, lastMouseY=0;
let mousePos = {lx:0, ly:0};

const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const previewList = document.getElementById('previewList');

function n(id){return parseInt(document.getElementById(id).value||0)}

function draw(){
    if(!img)return;
    cv.width = cv.parentElement.clientWidth;
    cv.height = 750;
    ctx.clearRect(0,0,cv.width,cv.height);
    ctx.save();
    ctx.translate(offX, offY);
    ctx.scale(scale, scale);
    ctx.drawImage(img,0,0);
    
    // 繪製標記
    picks.forEach((p, i)=>{
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2/scale;
        ctx.strokeRect(p.x, p.y, p.w, p.h);
        ctx.fillStyle = 'rgba(59,130,246,0.2)';
        ctx.fillRect(p.x, p.y, p.w, p.h);
    });

    // 繪製預覽框 (僅在按住 Cmd/Ctrl 時顯示為選取色)
    const wh = n('wh');
    const rectX = mousePos.lx - wh/2;
    const rectY = mousePos.ly - wh/2;

    // 1. 先畫一層半透明的黑色實線作為底色，確保在亮色背景下也能看見
    ctx.setLineDash([]); // 實線
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.lineWidth = 3 / scale; // 稍微粗一點
    ctx.strokeRect(rectX, rectY, wh, wh);

    // 2. 繪製主要的虛線層
    ctx.setLineDash([8 / scale, 4 / scale]); // 增加虛線間隔，使其更明顯
    // 按住 Cmd/Ctrl 時顯示亮紅色，否則顯示亮白色
    ctx.strokeStyle = window.isCmdPressed ? '#ff1111' : '#ffffff'; 
    ctx.lineWidth = 2 / scale;
    ctx.strokeRect(rectX, rectY, wh, wh);

    ctx.restore();    
    ctx.restore();
}

// 監測鍵盤
window.isCmdPressed = false;
window.onkeydown = e => { if(e.metaKey || e.ctrlKey) { window.isCmdPressed = true; draw(); } };
window.onkeyup = e => { window.isCmdPressed = false; draw(); };

cv.onmousemove = e => {
    const rect = cv.getBoundingClientRect();
    mousePos.lx = (e.clientX - rect.left - offX) / scale;
    mousePos.ly = (e.clientY - rect.top - offY) / scale;
    if(isPanning){
        offX += (e.clientX - lastMouseX);
        offY += (e.clientY - lastMouseY);
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    }
    draw();
};

cv.onmousedown = e => {
    if(!img) return;
    if(e.metaKey || e.ctrlKey){
        // 選取模式
        const wh = n('wh');
        const pick = { x: Math.round(mousePos.lx - wh/2), y: Math.round(mousePos.ly - wh/2), w: wh, h: wh };
        picks.push(pick);
        updateUI();
    } else {
        // 平移模式
        isPanning = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    }
    draw();
};

window.onmouseup = () => isPanning = false;

cv.onwheel = e => {
    e.preventDefault();
    const oldS = scale;
    
    // 每次滾動縮放 5%
    const factor = e.deltaY < 0 ? 1.05 : 0.95;
    scale = Math.max(0.1, Math.min(10, scale * factor));
    
    const rect = cv.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    offX = mx - (mx - offX) * (scale / oldS);
    offY = my - (my - offY) * (scale / oldS);
    
    draw();
};
function updateUI(){
    document.getElementById('totalCount').innerText = picks.length;
    previewList.innerHTML = '';
    picks.forEach((p, i) => {
        const pcv = document.createElement('canvas');
        pcv.width = p.w; pcv.height = p.h;
        pcv.getContext('2d').drawImage(img, p.x, p.y, p.w, p.h, 0, 0, p.w, p.h);
        
        const div = document.createElement('div');
        div.className = "relative group cursor-pointer border border-slate-600 rounded overflow-hidden hover:border-red-500";
        div.onclick = () => { picks.splice(i, 1); updateUI(); draw(); };
        div.innerHTML = `<img src="${pcv.toDataURL()}" class="w-full h-auto pixelated"><div class="absolute inset-0 bg-red-500/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-xs">Remove</div>`;
        previewList.appendChild(div);
    });
}

document.getElementById('file').onchange = e => {
    fileBlob = e.target.files[0];
    img = new Image();
    img.onload = () => { offX=0; offY=0; scale=1; draw(); };
    img.src = URL.createObjectURL(fileBlob);
};

async function exportFile(){
    if(picks.length === 0) return alert('No selections');
    const fd = new FormData();
    fd.append('file', fileBlob);
    fd.append('outCols', n('outCols'));
    fd.append('outWH', n('outWH')); // 新增這一行
    fd.append('name', document.getElementById('name').value);
    fd.append('picks', JSON.stringify(picks));

    const r = await fetch('export_picker', {method:'POST', body:fd});
    if(!r.ok) return alert(await r.text());

    const blob = await r.blob();
    const contentType = r.headers.get('Content-Type');
    const a = document.createElement('a');
    
    // 根據回傳類型決定副檔名
    let fileName = document.getElementById('name').value;
    if (contentType === 'application/zip') {
        fileName = fileName.replace('.png', '.zip');
    }
    
    a.href = URL.createObjectURL(blob);
    a.download = fileName;
    a.click();
}
</script>
<style>.pixelated { image-rendering: pixelated; }</style>
</body></html>'''


@app.get('/', response_class=HTMLResponse)
def home():
    return HTML

@app.post('/export_picker')
async def export_picker(
    file: UploadFile = File(...), 
    outCols: int = Form(...), 
    outWH: int = Form(...), # 新增參數
    name: str = Form(...), 
    picks: str = Form(...)
):
    data = await file.read()
    img = Image.open(io.BytesIO(data)).convert('RGBA')
    pick_list = json.loads(picks)
    
    if not pick_list:
        return HTMLResponse('None', status_code=400)
    
    # 輸出尺寸現在統一使用使用者設定的 outWH
    tw = th = outWH 
    base_name = os.path.splitext(name)[0]
    
    num_picks = len(pick_list)
    num_images = num_picks // outCols
    
    if num_images == 0:
        return HTMLResponse('選取數量不足以構成一列', status_code=400)

    generated_files = []

    for img_idx in range(num_images):
        # 建立畫布，寬度為 (OutWH * Cols)，高度為 OutWH
        out_img = Image.new('RGBA', (outCols * tw, th), (0, 0, 0, 0))
        
        for col_idx in range(outCols):
            p_idx = img_idx * outCols + col_idx
            p = pick_list[p_idx]
            box = (p['x'], p['y'], p['x'] + p['w'], p['y'] + p['h'])
            
            # 1. 裁切原始大小
            tile = img.crop(box)
            
            # 2. 強制縮放至目標 OutWH
            # 使用 Resampling.LANCZOS 保持像素品質，若要保留像素感可用 NEAREST
            tile = tile.resize((tw, th), Image.Resampling.LANCZOS)
            
            # 3. 貼上
            out_img.paste(tile, (col_idx * tw, 0))
        
        file_path = os.path.join(OUTPUT_DIR, f"{base_name}_{img_idx+1}.png")
        out_img.save(file_path)
        generated_files.append(file_path)

    # 如果只有一張圖，直接回傳圖片
    if len(generated_files) == 1:
        return FileResponse(generated_files[0], filename=f"{base_name}.png", media_type='image/png')
    
    # 如果有多張圖，打包成 ZIP
    zip_path = os.path.join(OUTPUT_DIR, f"{base_name}_batch.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in generated_files:
            zipf.write(f, os.path.basename(f))
            
    return FileResponse(zip_path, filename=f"{base_name}.zip", media_type='application/zip')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)