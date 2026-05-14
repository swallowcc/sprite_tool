import uvicorn
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 匯入原本的三個檔案
from sprite_tool_fullstack import app as grid_app
from sprite_webtool import app as picker_app
from shiny_maker import app as shiny_app
from rotate_webtool import app as flipper_app
from sprite_merger import app as merger_app
from inset_crop_tool import app as inset_app
from sprite_splitter import app as splitter_app

app = FastAPI(title="Game Dev Suite")

# --- 定義導覽列 HTML ---
NAVBAR_HTML = """
<nav class="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center gap-6 sticky top-0 z-50 shadow-lg font-sans">
    <span class="font-bold text-blue-400 mr-4">DEV SUITE</span>
    <a href="/" class="text-sm text-slate-300 hover:text-blue-400 transition">🏠 Home</a>
    <a href="/grid/" class="text-sm text-slate-300 hover:text-blue-400 transition">📏 Grid Tool</a>
    <a href="/picker/" class="text-sm text-slate-300 hover:text-blue-400 transition">🎯 Picker Tool</a>
    <a href="/shiny/" class="text-sm text-slate-300 hover:text-blue-400 transition">✨ Shiny Maker</a>
    <a href="/flipper/" class="text-sm text-slate-300 hover:text-blue-400 transition">🔄 Flipper</a>
    <a href="/merger/" class="text-sm text-slate-300 hover:text-blue-400 transition">🧩 Merger</a>
    <a href="/inset/" class="text-sm text-slate-300 hover:text-blue-400 transition">✂️ Inset Crop</a>
    <a href="/splitter/" class="text-sm text-slate-300 hover:text-blue-400 transition">📦 Splitter</a>
</nav>
"""

class NavbarMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 針對所有 HTML 回傳進行注入
        if "text/html" in response.headers.get("content-type", ""):
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            html_content = body.decode("utf-8")
            
            # 使用正則表達式匹配 <body> 標籤，不論它有沒有帶 class 或其他屬性
            # 這會匹配 <body ...> 並在其後方插入 Navbar
            new_content = re.sub(r'(<body[^>]*>)', r'\1' + NAVBAR_HTML, html_content, flags=re.IGNORECASE)
            
            return HTMLResponse(content=new_content, status_code=response.status_code)
            
        return response

app.add_middleware(NavbarMiddleware)

# --- 掛載子應用程式 ---
app.mount("/grid", grid_app)
app.mount("/picker", picker_app)
app.mount("/shiny", shiny_app)
app.mount("/flipper", flipper_app)
app.mount("/merger", merger_app)
app.mount("/inset", inset_app)
app.mount("/splitter", splitter_app)

# 首頁入口
@app.get("/", response_class=HTMLResponse)
async def index():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white">
        <div class="flex flex-col items-center justify-center min-h-[80vh] space-y-6 pt-20">
            <h1 class="text-4xl font-bold text-blue-400">Game Developer Tool Suite</h1>
            <p class="text-slate-400">請從上方導覽列選擇要使用的工具</p>
            <div class="grid grid-cols-4 gap-6 pt-10">
                <a href="/grid/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">📏 Grid Tool</a>
                <a href="/picker/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">🎯 Picker Tool</a>
                <a href="/shiny/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">✨ Shiny Maker</a>
                <a href="/flipper/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">🔄 Flipper</a>
                <a href="/merger/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">🧩 Merger</a>
                <a href="/inset/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">✂️ Inset Crop</a>
                <a href="/splitter/" class="p-6 bg-slate-800 rounded-2xl border border-slate-700 text-center hover:border-blue-500 transition block">📦 Splitter</a>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)