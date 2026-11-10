"""
Cell Picker — Picker Tool 的第二種用法（格子選取）

以固定大小的正方形格子（預設 10x10）切分圖片，
點選物件的「起始格」與「結束格」，可連續選取多個物件，
每個物件各自輸出一張擷取後的圖（PNG 或 WebP）與一份同名 JSON。

格子座標為 0-based，起始格與結束格都「包含」在擷取範圍內：
    cols = x2 - x1 + 1
    rows = y2 - y1 + 1
"""

import io
import json
import os
import zipfile
from urllib.parse import quote

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from PIL import Image

router = APIRouter()

HTML = r'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="utf-8">
    <title>Cell Picker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .pixelated { image-rendering: pixelated; }
        .checker {
            background-color: #888;
            background-image:
                linear-gradient(45deg, #aaa 25%, transparent 25%),
                linear-gradient(-45deg, #aaa 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #aaa 75%),
                linear-gradient(-45deg, transparent 75%, #aaa 75%);
            background-size: 12px 12px;
            background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
        }
    </style>
</head>
<body class="bg-slate-900 text-white">
<div class="max-w-7xl mx-auto p-4 pt-20 space-y-6">
    <header class="border-b border-slate-700 pb-2 flex items-end justify-between gap-4">
        <div>
            <h1 class="text-xl font-bold">🧱 Cell Picker</h1>
            <p class="text-slate-400 text-sm mt-2">以固定格子大小點選物件的起始格與結束格（可多個物件），輸出擷取圖與 JSON</p>
        </div>
        <div class="flex gap-2 text-sm">
            <a href="../" class="px-3 py-1 rounded-lg border border-slate-600 text-slate-300 hover:border-blue-500">🎯 自由選取</a>
            <span class="px-3 py-1 rounded-lg bg-blue-600 font-bold">🧱 格子選取</span>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
    <div class="lg:col-span-1 bg-slate-800 p-4 rounded-2xl space-y-4">
        <input id="file" type="file" accept="image/*" class="w-full text-xs">

        <div class="space-y-1">
            <label class="text-xs text-slate-400">格子大小 (px，正方形)</label>
            <input id="cell" type="number" value="10" min="1" class="w-full p-2 rounded bg-slate-700 border border-slate-600">
            <p id="gridInfo" class="text-xs text-slate-500"></p>
        </div>

        <div class="space-y-1">
            <label class="text-xs text-slate-400">輸出名稱（ZIP 檔名、物件預設名稱前綴）</label>
            <input id="name" value="object" class="w-full p-2 rounded bg-slate-700 border border-slate-600">
        </div>

        <div class="space-y-2">
            <label class="flex items-center gap-2 text-sm cursor-pointer">
                <input id="webp" type="checkbox" class="w-4 h-4 accent-blue-500">
                輸出 WebP
            </label>
            <div id="qualityRow" class="flex items-center gap-2 text-xs text-slate-400">
                <span>品質 -q</span>
                <input id="quality" type="number" value="50" min="0" max="100" class="w-20 p-1 rounded bg-slate-700 border border-slate-600 text-white">
                <span>(0–100)</span>
            </div>
        </div>

        <div class="bg-blue-900/30 p-3 rounded-lg border border-blue-700/50 text-sm space-y-2">
            <p id="stepHint" class="text-blue-200 text-xs"></p>
            <div class="grid grid-cols-4 gap-1">
                <label class="text-xs text-slate-400">x1<input id="x1" type="number" min="0" class="w-full p-1 rounded bg-slate-700 border border-slate-600"></label>
                <label class="text-xs text-slate-400">y1<input id="y1" type="number" min="0" class="w-full p-1 rounded bg-slate-700 border border-slate-600"></label>
                <label class="text-xs text-slate-400">x2<input id="x2" type="number" min="0" class="w-full p-1 rounded bg-slate-700 border border-slate-600"></label>
                <label class="text-xs text-slate-400">y2<input id="y2" type="number" min="0" class="w-full p-1 rounded bg-slate-700 border border-slate-600"></label>
            </div>
            <button onclick="addManual()" class="w-full py-1 text-xs bg-slate-600 hover:bg-slate-500 rounded">＋ 以座標加入</button>
        </div>

        <div class="space-y-2">
            <div class="flex items-center justify-between">
                <label class="text-xs text-slate-400">已選物件 <span id="count" class="text-white font-bold">0</span></label>
                <button onclick="clearAll()" class="text-xs text-slate-400 hover:text-red-400">全部清除</button>
            </div>
            <div id="list" class="space-y-2 max-h-96 overflow-y-auto"></div>
        </div>

        <button onclick="exportFile()" class="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold transition"><span id="exportLabel">Export (PNG + JSON)</span></button>

        <details class="text-xs">
            <summary class="text-slate-400 cursor-pointer">JSON 預覽</summary>
            <pre id="jsonPreview" class="mt-1 bg-black/30 p-2 rounded font-mono whitespace-pre-wrap break-all"></pre>
        </details>

        <p class="text-xs text-slate-500">拖曳平移、滾輪縮放；Cmd/Ctrl + 點擊選格（起始 → 結束，選完自動加入清單）；Esc 取消未完成的選取</p>
    </div>

    <div class="lg:col-span-3 bg-slate-800 p-4 rounded-2xl overflow-hidden relative min-h-[700px]">
        <canvas id="cv" class="border border-slate-700 w-full"></canvas>
        <div id="hover" class="empty:hidden absolute top-6 right-6 bg-black/60 text-xs font-mono px-2 py-1 rounded"></div>
    </div>
    </div>
</div>

<script>
let img = null, fileBlob = null, scale = 1, offX = 0, offY = 0;
let isPanning = false, lastX = 0, lastY = 0;
let hoverCell = null;
let start = null;          // 尚未完成的起始格 {x, y}
let items = [];            // [{name, x1, y1, x2, y2}]
let seq = 0;               // 預設名稱流水號（刪除後不回收，避免名稱跳動）
let highlight = -1;        // 清單 hover 中的物件

const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const $ = id => document.getElementById(id);
const cellSize = () => Math.max(1, parseInt($('cell').value) || 10);
const gridW = () => img ? Math.ceil(img.width / cellSize()) : 0;
const gridH = () => img ? Math.ceil(img.height / cellSize()) : 0;
const baseName = () => ($('name').value.trim() || 'object').replace(/\.(png|webp|json|zip)$/i, '');
const imgExt = () => $('webp').checked ? 'webp' : 'png';
const stemOf = n => n.replace(/\.(png|webp)$/i, '');
const quality = () => Math.max(0, Math.min(100, parseInt($('quality').value) || 0));
const imgName = it => `${stemOf(it.name)}.${imgExt()}`;

function makeItem(a, b) {
    return { name: `${baseName()}_${++seq}`,
             x1: Math.min(a.x, b.x), y1: Math.min(a.y, b.y),
             x2: Math.max(a.x, b.x), y2: Math.max(a.y, b.y) };
}

function toJson(it) {
    return { file: imgName(it), cols: it.x2 - it.x1 + 1, rows: it.y2 - it.y1 + 1, cell: cellSize(),
             x1: it.x1, y1: it.y1, x2: it.x2, y2: it.y2 };
}

function draw() {
    cv.width = cv.parentElement.clientWidth - 32;
    cv.height = 750;
    ctx.clearRect(0, 0, cv.width, cv.height);
    if (!img) return;
    const c = cellSize();
    ctx.save();
    ctx.translate(offX, offY);
    ctx.scale(scale, scale);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(img, 0, 0);

    // 格線（縮太小時不畫，避免整片糊掉）
    if (c * scale >= 4) {
        ctx.strokeStyle = 'rgba(255,255,255,0.15)';
        ctx.lineWidth = 1 / scale;
        ctx.beginPath();
        for (let x = 0; x <= gridW(); x++) { ctx.moveTo(x * c, 0); ctx.lineTo(x * c, gridH() * c); }
        for (let y = 0; y <= gridH(); y++) { ctx.moveTo(0, y * c); ctx.lineTo(gridW() * c, y * c); }
        ctx.stroke();
    }

    // 已選物件
    items.forEach((it, i) => {
        const x = it.x1 * c, y = it.y1 * c, w = (it.x2 - it.x1 + 1) * c, h = (it.y2 - it.y1 + 1) * c;
        const hi = i === highlight;
        ctx.fillStyle = hi ? 'rgba(250,204,21,0.35)' : 'rgba(59,130,246,0.25)';
        ctx.fillRect(x, y, w, h);
        ctx.strokeStyle = hi ? '#facc15' : '#3b82f6';
        ctx.lineWidth = 2 / scale;
        ctx.strokeRect(x, y, w, h);
        // 編號標籤
        const fs = 12 / scale, label = String(i + 1);
        ctx.font = `bold ${fs}px sans-serif`;
        const tw = ctx.measureText(label).width + 6 / scale;
        ctx.fillStyle = hi ? '#facc15' : '#3b82f6';
        ctx.fillRect(x, y, tw, fs + 4 / scale);
        ctx.fillStyle = hi ? '#000' : '#fff';
        ctx.fillText(label, x + 3 / scale, y + fs);
    });

    // 進行中的選取
    if (start) {
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 2 / scale;
        ctx.strokeRect(start.x * c, start.y * c, c, c);
        if (hoverCell) {
            const x1 = Math.min(start.x, hoverCell.x), y1 = Math.min(start.y, hoverCell.y);
            const w = Math.abs(start.x - hoverCell.x) + 1, h = Math.abs(start.y - hoverCell.y) + 1;
            ctx.setLineDash([6 / scale, 4 / scale]);
            ctx.strokeStyle = '#ffffff';
            ctx.strokeRect(x1 * c, y1 * c, w * c, h * c);
            ctx.setLineDash([]);
        }
    }

    if (hoverCell) {
        ctx.strokeStyle = window.isCmdPressed ? '#ff1111' : 'rgba(255,255,255,0.8)';
        ctx.lineWidth = 1.5 / scale;
        ctx.strokeRect(hoverCell.x * c, hoverCell.y * c, c, c);
    }
    ctx.restore();
}

function thumb(it) {
    const c = cellSize();
    const w = (it.x2 - it.x1 + 1) * c, h = (it.y2 - it.y1 + 1) * c;
    const t = document.createElement('canvas');
    t.width = w; t.height = h;
    t.getContext('2d').drawImage(img, it.x1 * c, it.y1 * c, w, h, 0, 0, w, h);
    t.className = 'pixelated max-w-full max-h-full';
    return t;
}

function renderList() {
    const list = $('list');
    list.innerHTML = '';
    $('count').innerText = items.length;
    items.forEach((it, i) => {
        const cols = it.x2 - it.x1 + 1, rows = it.y2 - it.y1 + 1;
        const row = document.createElement('div');
        row.className = 'flex gap-2 items-center bg-black/20 rounded p-2 border border-transparent hover:border-yellow-400';
        row.onmouseenter = () => { highlight = i; draw(); };
        row.onmouseleave = () => { highlight = -1; draw(); };

        const box = document.createElement('div');
        box.className = 'checker w-12 h-12 flex-none flex items-center justify-center rounded overflow-hidden';
        box.appendChild(thumb(it));

        const mid = document.createElement('div');
        mid.className = 'flex-1 min-w-0 space-y-1';
        const nameIn = document.createElement('input');
        nameIn.value = it.name;
        nameIn.className = 'w-full p-1 text-xs rounded bg-slate-700 border border-slate-600';
        nameIn.oninput = () => { it.name = nameIn.value.trim() || `${baseName()}_${i + 1}`; updateJson(); };
        const info = document.createElement('p');
        info.className = 'text-[11px] text-slate-400 font-mono';
        info.innerText = `#${i + 1} (${it.x1},${it.y1})→(${it.x2},${it.y2}) ${cols}×${rows}`;
        mid.append(nameIn, info);

        const del = document.createElement('button');
        del.className = 'flex-none text-slate-400 hover:text-red-400 px-1';
        del.innerText = '✕';
        del.title = '移除';
        del.onclick = () => { items.splice(i, 1); highlight = -1; renderList(); draw(); };

        row.append(box, mid, del);
        list.appendChild(row);
    });
    updateJson();
}

function updateJson() {
    // 每個物件各自一份 JSON
    $('jsonPreview').innerText = items.map(it =>
        `// ${stemOf(it.name)}.json\n` + JSON.stringify(toJson(it), null, 2)).join('\n\n');
}

function updateHint() {
    $('gridInfo').innerText = img ? `圖片 ${img.width}×${img.height} px → ${gridW()}×${gridH()} 格` : '';
    $('stepHint').innerText = !img ? '請先上傳圖片'
        : !start ? 'Cmd/Ctrl + 點擊：選起始格'
        : `起始格 (${start.x}, ${start.y})，Cmd/Ctrl + 點擊：選結束格`;
}

function cellAt(e) {
    const rect = cv.getBoundingClientRect();
    const lx = (e.clientX - rect.left - offX) / scale;
    const ly = (e.clientY - rect.top - offY) / scale;
    const c = cellSize();
    const x = Math.floor(lx / c), y = Math.floor(ly / c);
    if (x < 0 || y < 0 || x >= gridW() || y >= gridH()) return null;
    return { x, y };
}

window.isCmdPressed = false;
window.onkeydown = e => {
    if (e.metaKey || e.ctrlKey) { window.isCmdPressed = true; draw(); }
    if (e.key === 'Escape' && start) { start = null; updateHint(); draw(); }
};
window.onkeyup = () => { window.isCmdPressed = false; draw(); };

cv.onmousemove = e => {
    if (!img) return;
    hoverCell = cellAt(e);
    $('hover').innerText = hoverCell ? `x ${hoverCell.x}, y ${hoverCell.y}` : '';
    if (isPanning) {
        offX += e.clientX - lastX; offY += e.clientY - lastY;
        lastX = e.clientX; lastY = e.clientY;
    }
    draw();
};
cv.onmouseleave = () => { hoverCell = null; $('hover').innerText = ''; draw(); };

cv.onmousedown = e => {
    if (!img) return;
    if (e.metaKey || e.ctrlKey) {
        const cell = cellAt(e);
        if (!cell) return;
        if (!start) { start = cell; }
        else { items.push(makeItem(start, cell)); start = null; renderList(); }
        updateHint();
    } else {
        isPanning = true; lastX = e.clientX; lastY = e.clientY;
    }
    draw();
};
window.onmouseup = () => isPanning = false;

cv.onwheel = e => {
    e.preventDefault();
    const oldS = scale;
    scale = Math.max(0.1, Math.min(40, scale * (e.deltaY < 0 ? 1.1 : 0.9)));
    const rect = cv.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    offX = mx - (mx - offX) * (scale / oldS);
    offY = my - (my - offY) * (scale / oldS);
    draw();
};

function addManual() {
    if (!img) return alert('請先上傳圖片');
    const v = ['x1', 'y1', 'x2', 'y2'].map(k => parseInt($(k).value));
    if (v.some(isNaN)) return alert('請填完 x1, y1, x2, y2');
    if (v.some(n => n < 0) || Math.max(v[0], v[2]) >= gridW() || Math.max(v[1], v[3]) >= gridH())
        return alert(`座標超出範圍（x: 0~${gridW() - 1}, y: 0~${gridH() - 1}）`);
    items.push(makeItem({ x: v[0], y: v[1] }, { x: v[2], y: v[3] }));
    ['x1', 'y1', 'x2', 'y2'].forEach(k => $(k).value = '');
    renderList(); draw();
}

function clearAll() {
    if (items.length && !confirm(`確定清除全部 ${items.length} 個物件？`)) return;
    items = []; start = null; seq = 0; renderList(); updateHint(); draw();
}

// 改格子大小：既有座標意義已不同，必須清除
let lastCell = 10;
$('cell').addEventListener('change', () => {
    if (items.length && !confirm('變更格子大小會清除目前所有選取，確定？')) {
        $('cell').value = lastCell; return;
    }
    lastCell = cellSize();
    items = []; start = null; seq = 0; renderList(); updateHint(); draw();
});

// ── 設定記憶：重新整理後沿用上次的值（存在這個瀏覽器的 localStorage）
const SETTINGS_KEY = 'cellPicker.settings';
function saveSettings() {
    try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify({
            cell: cellSize(), webp: $('webp').checked, quality: quality() }));
    } catch (e) {}
}
function loadSettings() {
    try {
        const s = JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}');
        if (s.cell) { $('cell').value = s.cell; lastCell = s.cell; }
        if (typeof s.webp === 'boolean') $('webp').checked = s.webp;
        if (s.quality !== undefined) $('quality').value = s.quality;
    } catch (e) {}
}
function updateFormatUI() {
    const on = $('webp').checked;
    $('qualityRow').style.opacity = on ? 1 : 0.4;
    $('quality').disabled = !on;
    $('exportLabel').innerText = `Export (${on ? 'WebP' : 'PNG'} + JSON)`;
}
$('webp').addEventListener('change', () => { updateFormatUI(); updateJson(); saveSettings(); });
$('quality').addEventListener('change', () => { $('quality').value = quality(); saveSettings(); });
$('cell').addEventListener('change', saveSettings);

$('file').onchange = e => {
    fileBlob = e.target.files[0];
    if (!fileBlob) return;
    img = new Image();
    img.onload = () => {
        offX = 0; offY = 0; scale = 1; start = null; items = []; seq = 0;
        $('name').value = fileBlob.name.replace(/\.[^.]+$/, '');
        renderList(); updateHint(); draw();
    };
    img.src = URL.createObjectURL(fileBlob);
};

window.onresize = draw;

async function exportFile() {
    if (!img || !items.length) return alert('請先選取至少一個物件');
    const fd = new FormData();
    fd.append('file', fileBlob);
    fd.append('cell', cellSize());
    fd.append('name', baseName());
    fd.append('fmt', imgExt());
    fd.append('quality', quality());
    fd.append('items', JSON.stringify(items.map(it => ({ name: it.name, x1: it.x1, y1: it.y1, x2: it.x2, y2: it.y2 }))));

    const res = await fetch('export', { method: 'POST', body: fd });
    if (!res.ok) return alert(await res.text());
    const a = document.createElement('a');
    a.href = URL.createObjectURL(await res.blob());
    a.download = baseName() + '.zip';
    a.click();
}

loadSettings(); updateFormatUI();
renderList(); updateHint(); draw();
</script>
</body></html>'''


@router.get('/', response_class=HTMLResponse)
def cell_picker_home():
    return HTML


def crop_region(img: Image.Image, cell: int, x1: int, y1: int, x2: int, y2: int):
    """依格子座標（含起訖格）裁切，回傳 (圖片, 正規化後的座標 dict)。"""
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    box = (x1 * cell, y1 * cell, (x2 + 1) * cell, (y2 + 1) * cell)
    # 超出圖片邊界的部分 PIL 會補透明，確保輸出尺寸恆為 cols*cell x rows*cell
    return img.crop(box), {'cols': x2 - x1 + 1, 'rows': y2 - y1 + 1, 'cell': cell,
                           'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}


def safe_stem(name: str, fallback: str) -> str:
    stem = os.path.basename(str(name).strip())
    root, ext = os.path.splitext(stem)
    if ext.lower() in ('.png', '.webp'):
        stem = root
    return stem or fallback


@router.post('/export')
async def cell_picker_export(
    file: UploadFile = File(...),
    cell: int = Form(10),
    name: str = Form('object'),
    items: str = Form(...),
    fmt: str = Form('png'),
    quality: int = Form(50),
):
    if cell < 1:
        return PlainTextResponse('格子大小必須 >= 1', status_code=400)
    fmt = fmt.lower()
    if fmt not in ('png', 'webp'):
        return PlainTextResponse('fmt 只支援 png / webp', status_code=400)
    if not 0 <= quality <= 100:
        return PlainTextResponse('quality 必須在 0~100', status_code=400)
    try:
        item_list = json.loads(items)
        assert isinstance(item_list, list) and item_list
        coords = [[int(it[k]) for k in ('x1', 'y1', 'x2', 'y2')] for it in item_list]
    except Exception:
        return PlainTextResponse('items 格式錯誤', status_code=400)

    img = Image.open(io.BytesIO(await file.read())).convert('RGBA')
    max_x, max_y = -(-img.width // cell) - 1, -(-img.height // cell) - 1
    base = safe_stem(name, 'object')

    used = set()
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, (it, (x1, y1, x2, y2)) in enumerate(zip(item_list, coords), start=1):
            if min(x1, y1, x2, y2) < 0 or max(x1, x2) > max_x or max(y1, y2) > max_y:
                return PlainTextResponse(
                    f'第 {i} 個物件座標超出圖片範圍（x: 0~{max_x}, y: 0~{max_y}）', status_code=400)

            # 檔名重複時自動加後綴，避免 ZIP 內互相覆蓋
            stem = safe_stem(it.get('name', ''), f'{base}_{i}')
            unique, n = stem, 2
            while unique.lower() in used:
                unique, n = f'{stem}_{n}', n + 1
            used.add(unique.lower())

            # 每個物件各自一張圖 + 一份同名 JSON
            crop, meta = crop_region(img, cell, x1, y1, x2, y2)
            buf = io.BytesIO()
            if fmt == 'webp':
                # 等同 cwebp -q <quality>（有損壓縮，alpha 維持無損）
                crop.save(buf, 'WEBP', quality=quality)
            else:
                crop.save(buf, 'PNG')
            zf.writestr(f'{unique}.{fmt}', buf.getvalue())
            zf.writestr(f'{unique}.json',
                        json.dumps({'file': f'{unique}.{fmt}', **meta}, ensure_ascii=False, indent=2))
    zip_buf.seek(0)

    return StreamingResponse(
        zip_buf, media_type='application/zip',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(base)}.zip"},
    )
