import io
import base64
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from PIL import Image

app = FastAPI()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sprite Merger</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white">
    <div class="max-w-7xl mx-auto space-y-6 p-8 pt-20">
        <header class="border-b border-slate-700 pb-2">
            <h1 class="text-xl font-bold">🧩 Merger</h1>
            <p class="text-slate-400 text-sm mt-2">將來源圖片 merge 進主圖的指定 tile 座標</p>
        </header>

        <form id="mergeForm" class="space-y-4">
            <div>
                <label class="text-sm text-slate-300 block mb-1">主圖 (Main Sprite Sheet)</label>
                <input type="file" name="main_image" accept="image/*" required
                    class="w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer" />
            </div>
            <div>
                <label class="text-sm text-slate-300 block mb-1">來源圖 (Source Sprite)</label>
                <input type="file" name="source_image" accept="image/*" required
                    class="w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-green-600 file:text-white hover:file:bg-green-700 cursor-pointer" />
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-sm text-slate-300 block mb-1">主圖 Columns 數量</label>
                    <input type="number" name="main_cols" min="1" required placeholder="e.g. 8"
                        class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="text-sm text-slate-300 block mb-1">主圖 Rows 數量</label>
                    <input type="number" name="main_rows" min="1" required placeholder="e.g. 4"
                        class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-sm text-slate-300 block mb-1">目標 Column（從 0 開始）</label>
                    <input type="number" name="target_col" min="0" required placeholder="e.g. 4"
                        class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                    <label class="text-sm text-slate-300 block mb-1">目標 Row（從 0 開始）</label>
                    <input type="number" name="target_row" min="0" required placeholder="e.g. 5"
                        class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                </div>
            </div>
            <div>
                <label class="text-sm text-slate-300 block mb-1">輸出檔名</label>
                <input type="text" name="output_name" placeholder="output.png" value="output.png"
                    class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
            </div>
            <button type="submit"
                class="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition">
                Merge & Download
            </button>
        </form>

        <div id="preview" class="hidden space-y-3">
            <p class="text-green-400 text-sm font-semibold">✅ Merge 完成，預覽如下：</p>
            <img id="previewImg" class="border border-slate-600 rounded max-w-full" style="image-rendering: pixelated;" />
            <a id="downloadBtn" class="block text-center py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition cursor-pointer">
                ⬇ 下載結果
            </a>
        </div>

        <div id="errorMsg" class="hidden text-red-400 text-sm"></div>
    </div>

    <script>
        document.getElementById('mergeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);
            document.getElementById('preview').classList.add('hidden');
            document.getElementById('errorMsg').classList.add('hidden');

            const outputName = formData.get('output_name') || 'output.png';

            const res = await fetch('/merger/merge', { method: 'POST', body: formData });
            if (!res.ok) {
                const text = await res.text();
                document.getElementById('errorMsg').textContent = '❌ 錯誤：' + text;
                document.getElementById('errorMsg').classList.remove('hidden');
                return;
            }

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const img = document.getElementById('previewImg');
            img.src = url;

            const dlBtn = document.getElementById('downloadBtn');
            dlBtn.onclick = () => {
                const a = document.createElement('a');
                a.href = url;
                a.download = outputName;
                a.click();
            };
            document.getElementById('preview').classList.remove('hidden');
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.post("/merge")
async def merge_sprites(
    main_image: UploadFile = File(...),
    source_image: UploadFile = File(...),
    main_cols: int = Form(...),
    main_rows: int = Form(...),
    target_col: int = Form(...),
    target_row: int = Form(...),
    output_name: str = Form("output.png"),
):
    main_data = await main_image.read()
    source_data = await source_image.read()

    main_img = Image.open(io.BytesIO(main_data)).convert("RGBA")
    source_img = Image.open(io.BytesIO(source_data)).convert("RGBA")

    main_w, main_h = main_img.size
    tile_w = main_w // main_cols
    tile_h = main_h // main_rows

    # 將來源圖縮放至 tile 尺寸
    source_resized = source_img.resize((tile_w, tile_h), Image.NEAREST)

    paste_x = target_col * tile_w
    paste_y = target_row * tile_h

    result = main_img.copy()
    result.paste(source_resized, (paste_x, paste_y), source_resized)

    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{output_name}"'},
    )
