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
<body class="bg-slate-900 text-white">
<div class="max-w-7xl mx-auto p-4 pt-20 space-y-6">
    <header class="border-b border-slate-700 pb-2">
        <h1 class="text-xl font-bold">📏 Grid Tool</h1>
        <p class="text-slate-400 text-sm mt-2">定義網格區域，批量選取多個 Tile 範圍</p>
    </header>
    
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <div class="bg-slate-800 p-4 rounded-2xl space-y-2">
        <div class="bg-blue-900/50 p-3 rounded-lg border border-blue-700/50">
            <p class="text-sm font-semibold text-blue-200">Total Tiles: <span id="totalCount" class="text-xl text-white">0</span></p>
        </div>
        <p class="text-xs text-slate-400">操作：直接拖拽平移。Cmd+點擊選取兩點定一區。</p>
        <input id="file" type="file" accept="image/*" class="w-full">
        <div class="grid grid-cols-2 gap-2">
            <input id="cols" type="number" value="64" class="p-2 rounded text-black">
            <input id="rows" type="number" value="95" class="p-2 rounded text-black">
            <input id="outCols" type="number" value="6" class="p-2 rounded text-black">
            <input id="outRows" type="number" value="6" class="p-2 rounded text-black">
        </div>
        <input id="name" value="output.png" class="w-full p-2 rounded text-black">
        <div class="flex gap-2">
            <button onclick="undo()" class="flex-1 py-2 bg-slate-600 rounded">Undo</button>
            <button onclick="clearAll()" class="flex-1 py-2 bg-slate-600 rounded">Clear</button>
            <button onclick="exportFile()" class="flex-1 py-2 bg-blue-600 rounded font-bold">Export</button>
        </div>
        <textarea id="log" class="w-full h-80 text-xs font-mono bg-black/50 p-2 rounded border border-slate-700 text-green-400" spellcheck="false"></textarea>
    </div>
    <div class="lg:col-span-2 bg-slate-800 p-4 rounded-2xl overflow-hidden relative">
        <canvas id="cv" class="border border-slate-600 w-full"></canvas>
    </div>
</div>

<script>
let img=null, fileBlob=null, regions=[], scale=1;
let offX=0, offY=0, isPanning=false, lastMouseX=0, lastMouseY=0;
let pendingPoint=null;

const cv=document.getElementById('cv'), ctx=cv.getContext('2d'), logArea=document.getElementById('log'), countDisplay=document.getElementById('totalCount');

function n(id){return parseInt(document.getElementById(id).value||0)}

// 計算總格數並更新 UI
function updateUI(){
    logArea.value = JSON.stringify(regions, null, 2);
    let total = 0;
    regions.forEach(r => {
        total += (r.x2 - r.x1 + 1) * (r.y2 - r.y1 + 1);
    });
    countDisplay.innerText = total;
}

logArea.oninput = () => {
    try {
        const val = JSON.parse(logArea.value);
        if(Array.isArray(val)) { regions = val; draw(); updateUI(); }
    } catch(e) {}
};

function draw(){
    if(!img)return;
    cv.width = cv.parentElement.clientWidth;
    cv.height = 700;
    ctx.clearRect(0,0,cv.width,cv.height);
    ctx.save();
    ctx.translate(offX, offY);
    ctx.scale(scale, scale);
    ctx.drawImage(img,0,0);
    const cols=n('cols'), rows=n('rows');
    if(cols && rows){
        const cw=img.width/cols, ch=img.height/rows;
        ctx.strokeStyle='rgba(255,255,255,0.1)';
        ctx.lineWidth = 1/scale;
        for(let x=0;x<=cols;x++){ctx.beginPath();ctx.moveTo(x*cw,0);ctx.lineTo(x*cw,img.height);ctx.stroke()}
        for(let y=0;y<=rows;y++){ctx.beginPath();ctx.moveTo(0,y*ch);ctx.lineTo(img.width,y*ch);ctx.stroke()}
        regions.forEach(r=>{
            ctx.fillStyle='rgba(59,130,246,0.3)';
            ctx.fillRect(r.x1*cw, r.y1*ch, (r.x2-r.x1+1)*cw, (r.y2-r.y1+1)*ch);
            ctx.strokeStyle='rgba(59,130,246,1)';
            ctx.strokeRect(r.x1*cw, r.y1*ch, (r.x2-r.x1+1)*cw, (r.y2-r.y1+1)*ch);
        });
        if(pendingPoint){
            ctx.fillStyle='rgba(16,185,129,0.5)';
            ctx.fillRect(pendingPoint.x*cw, pendingPoint.y*ch, cw, ch);
        }
    }
    ctx.restore();
}

function getCell(e){
    const rect=cv.getBoundingClientRect();
    const lx = (e.clientX - rect.left - offX) / scale;
    const ly = (e.clientY - rect.top - offY) / scale;
    const cw=img.width/n('cols'), ch=img.height/n('rows');
    return {
        x: Math.floor(Math.max(0, Math.min(img.width-1, lx)) / cw),
        y: Math.floor(Math.max(0, Math.min(img.height-1, ly)) / ch)
    };
}

cv.onmousedown = e => {
    if(!img) return;
    if(e.metaKey || e.ctrlKey) {
        const p = getCell(e);
        if(!pendingPoint) { pendingPoint = p; } 
        else {
            regions.push({
                x1: Math.min(pendingPoint.x, p.x), y1: Math.min(pendingPoint.y, p.y),
                x2: Math.max(pendingPoint.x, p.x), y2: Math.max(pendingPoint.y, p.y)
            });
            pendingPoint = null;
            updateUI();
        }
        draw();
    } else {
        isPanning = true; lastMouseX = e.clientX; lastMouseY = e.clientY;
        cv.style.cursor = 'grabbing';
    }
};

window.onmousemove = e => { if(isPanning){ offX += (e.clientX-lastMouseX); offY += (e.clientY-lastMouseY); lastMouseX=e.clientX; lastMouseY=e.clientY; draw(); }};
window.onmouseup = () => { isPanning = false; cv.style.cursor = 'default'; };
cv.onwheel = e => {
    e.preventDefault();
    const oldS = scale; scale = Math.max(0.1, Math.min(10, scale + (e.deltaY<0?0.1:-0.1)));
    const rect = cv.getBoundingClientRect();
    const mx = e.clientX-rect.left, my = e.clientY-rect.top;
    offX = mx - (mx-offX)*(scale/oldS); offY = my - (my-offY)*(scale/oldS);
    draw();
};

document.getElementById('file').onchange = e => {
    fileBlob = e.target.files[0];
    const url = URL.createObjectURL(fileBlob);
    img = new Image();
    img.onload = () => { offX=0; offY=0; scale=1; draw(); };
    img.src = url;
};

function undo(){ if(pendingPoint) pendingPoint=null; else regions.pop(); updateUI(); draw(); }
function clearAll(){ regions=[]; pendingPoint=null; updateUI(); draw(); }

async function exportFile(){
    if(!fileBlob || regions.length === 0) return alert('請先選擇檔案並選取區域');
    const fd=new FormData();
    ['file','cols','rows','outCols','outRows','name'].forEach(k=>fd.append(k, k==='file'?fileBlob:document.getElementById(k).value));
    fd.append('regions', JSON.stringify(regions));
    const r = await fetch('export', {method:'POST', body:fd});
    if(!r.ok) return alert(await r.text());
    const blob = await r.blob();
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = document.getElementById('name').value; a.click();
}
</script></body></html>'''

@app.get('/', response_class=HTMLResponse)
def home():
    return HTML

@app.post('/export')
async def export(file: UploadFile = File(...), cols: int = Form(...), rows: int = Form(...), outCols: int = Form(...), outRows: int = Form(...), name: str = Form('output.png'), regions: str = Form(...)):
    data = await file.read()
    img = Image.open(io.BytesIO(data)).convert('RGBA')
    cw, ch = img.width // cols, img.height // rows
    reg_list = json.loads(regions)
    tiles = []
    for r in reg_list:
        for y in range(r['y1'], r['y2'] + 1):
            for x in range(r['x1'], r['x2'] + 1):
                tiles.append((x, y))
    
    if not tiles: return HTMLResponse('No tiles selected', status_code=400)
    needed_rows = math.ceil(len(tiles) / outCols)
    out = Image.new('RGBA', (outCols * cw, needed_rows * ch), (0, 0, 0, 0))
    for i, (tx, ty) in enumerate(tiles):
        tile = img.crop((tx * cw, ty * ch, (tx + 1) * cw, (ty + 1) * ch))
        out.paste(tile, ((i % outCols) * cw, (i // outCols) * ch))
    
    path = os.path.join(OUTPUT_DIR, name)
    out.save(path)
    return FileResponse(path, filename=name, media_type='image/png')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)