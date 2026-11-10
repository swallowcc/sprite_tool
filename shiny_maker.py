import traceback
import json
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse
import cv2
import numpy as np
from PIL import Image
import io, os, base64
from typing import Optional, Tuple

app = FastAPI()
BASE = os.getcwd()
OUTPUT_DIR = os.path.join(BASE, 'shiny_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shiny_settings.sqlite3')


def initialize_settings_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS shiny_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                settings_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')


initialize_settings_database()

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .pixelated { image-rendering: pixelated; }
        #preview { cursor: crosshair; }
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

                <div class="space-y-4 border-t border-slate-700 pt-5">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-slate-300">7. 選色替換</label>
                        <p class="text-[11px] text-slate-400">在右側預覽點選來源顏色，再挑選替換色。</p>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div class="space-y-1">
                            <span class="text-xs text-slate-400">來源顏色</span>
                            <div class="flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 min-h-11">
                                <span id="sourceColorSwatch" class="w-5 h-5 rounded border border-slate-500 bg-slate-700"></span>
                                <span id="sourceColorHex" class="text-xs font-mono text-slate-400">尚未取色</span>
                            </div>
                        </div>
                        <label class="space-y-1">
                            <span class="text-xs text-slate-400">替換成</span>
                            <span class="flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 min-h-11">
                                <input id="replaceColor" type="color" value="#ff4d7d" aria-label="選擇替換顏色" class="w-8 h-7 rounded cursor-pointer bg-transparent border-0 p-0">
                                <span id="replaceColorHex" class="text-xs font-mono text-slate-300">#ff4d7d</span>
                            </span>
                        </label>
                    </div>

                    <label class="block space-y-1">
                        <span class="text-xs text-slate-400">替換範圍</span>
                        <select id="replaceMode" class="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="global">全圖相近顏色</option>
                            <option value="region">點選處的連通區域</option>
                        </select>
                    </label>

                    <div class="space-y-2">
                        <div class="flex justify-between text-xs">
                            <label for="replaceTolerance" class="text-slate-400">相近色範圍</label>
                            <span id="replaceToleranceVal" class="text-blue-400 font-mono">24</span>
                        </div>
                        <input id="replaceTolerance" type="range" min="4" max="80" step="1" value="24" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-fuchsia-500">
                    </div>

                    <div id="regionFeatherControl" class="space-y-2 hidden">
                        <div class="flex justify-between text-xs">
                            <label for="regionFeather" class="text-slate-400">區域邊緣柔化</label>
                            <span id="regionFeatherVal" class="text-blue-400 font-mono">2</span>
                        </div>
                        <input id="regionFeather" type="range" min="0" max="8" step="1" value="2" class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-fuchsia-500">
                    </div>
                    <p id="replaceModeHelp" class="text-[10px] text-slate-500">全圖模式會柔和影響所有相近顏色，並保留原有明暗與陰影。</p>
                </div>

                <div class="flex gap-2 pt-4">
                    <button type="button" onclick="processImage()" class="flex-1 py-4 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold shadow-lg transition-all active:scale-95">更新預覽</button>
                    <button type="button" onclick="restoreDefaults()" class="px-4 py-4 bg-slate-700 hover:bg-slate-600 rounded-xl text-sm transition-all active:scale-95">還原預設值</button>
                    <button type="button" onclick="downloadImage()" id="btnDownload" class="px-6 py-4 bg-slate-700 hover:bg-slate-600 rounded-xl text-sm hidden">下載</button>
                </div>

                <div class="space-y-2 border-t border-slate-700 pt-4">
                    <div class="flex gap-2">
                        <input id="settingsName" type="text" maxlength="48" placeholder="設定檔名稱，例如：火焰系" aria-label="設定檔名稱" class="min-w-0 flex-1 rounded-lg bg-slate-900 border border-slate-700 px-3 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <button type="button" onclick="saveSettings()" class="px-4 py-3 bg-indigo-700 hover:bg-indigo-600 rounded-xl text-sm font-semibold transition-all active:scale-95">儲存</button>
                    </div>
                    <div class="flex gap-2">
                        <select id="savedSettingsSelect" aria-label="選擇已儲存的設定檔" class="min-w-0 flex-1 rounded-lg bg-slate-900 border border-slate-700 px-3 py-3 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">選擇已儲存設定</option>
                        </select>
                        <button type="button" onclick="loadSettings()" id="btnLoadSettings" disabled class="px-4 py-3 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-sm transition-all active:scale-95">套用</button>
                    </div>
                    <p id="settingsStatus" aria-live="polite" class="text-[10px] text-slate-500">設定會儲存在這個瀏覽器；同名儲存會更新原設定。</p>
                </div>
            </div>

            <div class="bg-slate-800 p-6 rounded-2xl flex flex-col items-center justify-center border-2 border-dashed border-slate-700">
                <p id="placeholder" class="text-slate-500 text-sm font-mono italic">AWAITING IMAGE...</p>
                <img id="preview" title="點選圖片取樣來源顏色" alt="處理後的圖片預覽；點選可取樣顏色" class="max-w-full h-auto rounded shadow-2xl pixelated hidden">
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

        let currentFile = null, timer = null, processRequestId = 0;
        let replacementSample = null;
        let savedSettings = [];
        let settingsReady = Promise.resolve();
        const settingsStorageKey = 'shinyMakerSavedSettingsV1';

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

        const replaceColor = g('replaceColor');
        const replaceMode = g('replaceMode');
        const replaceTolerance = g('replaceTolerance');
        const regionFeather = g('regionFeather');

        function updateReplacementControls() {
            const isRegion = replaceMode.value === 'region';
            g('regionFeatherControl').classList.toggle('hidden', !isRegion);
            g('replaceModeHelp').textContent = isRegion
                ? '只替換與取樣點相連的相近色塊；邊緣柔化可減少生硬接縫。'
                : '全圖模式會柔和影響所有相近顏色，並保留原有明暗與陰影。';
        }

        function processReplacementSettings() {
            if (replacementSample) throttledProcess();
        }

        replaceColor.oninput = () => {
            g('replaceColorHex').textContent = replaceColor.value;
            processReplacementSettings();
        };
        replaceMode.onchange = () => {
            updateReplacementControls();
            processReplacementSettings();
        };
        replaceTolerance.oninput = () => {
            g('replaceToleranceVal').textContent = replaceTolerance.value;
            processReplacementSettings();
        };
        regionFeather.oninput = () => {
            g('regionFeatherVal').textContent = regionFeather.value;
            processReplacementSettings();
        };

        preview.addEventListener('click', (event) => {
            if (!preview.naturalWidth || !preview.naturalHeight) return;
            const rect = preview.getBoundingClientRect();
            const x = Math.max(0, Math.min(preview.naturalWidth - 1,
                Math.floor((event.clientX - rect.left) * preview.naturalWidth / rect.width)));
            const y = Math.max(0, Math.min(preview.naturalHeight - 1,
                Math.floor((event.clientY - rect.top) * preview.naturalHeight / rect.height)));

            const canvas = document.createElement('canvas');
            canvas.width = preview.naturalWidth;
            canvas.height = preview.naturalHeight;
            const context = canvas.getContext('2d', { willReadFrequently: true });
            context.drawImage(preview, 0, 0);
            const pixel = context.getImageData(x, y, 1, 1).data;
            const hex = '#' + Array.from(pixel.slice(0, 3), value => value.toString(16).padStart(2, '0')).join('');

            replacementSample = {
                x,
                y,
                xRatio: x / Math.max(1, preview.naturalWidth - 1),
                yRatio: y / Math.max(1, preview.naturalHeight - 1),
                hex,
                fromPreset: false
            };
            g('sourceColorSwatch').style.backgroundColor = hex;
            g('sourceColorHex').textContent = hex;
            processImage();
        });

        function restoreDefaults() {
            [hueRange, satMin, satScale, valScale, tintStrength].forEach(control => {
                control.value = control.defaultValue;
            });
            [replaceColor, replaceTolerance, regionFeather].forEach(control => {
                control.value = control.defaultValue;
            });
            replaceMode.selectedIndex = 0;
            hueVal.textContent = hueRange.value;
            satScaleVal.textContent = satScale.value;
            valScaleVal.textContent = valScale.value;
            tintVal.textContent = tintStrength.value;
            g('replaceColorHex').textContent = replaceColor.value;
            g('replaceToleranceVal').textContent = replaceTolerance.value;
            g('regionFeatherVal').textContent = regionFeather.value;
            replacementSample = null;
            g('sourceColorSwatch').style.backgroundColor = '';
            g('sourceColorHex').textContent = '尚未取色';
            updateReplacementControls();

            if (timer) clearTimeout(timer);
            processImage();
        }

        const settingControlIds = [
            'hueRange', 'satMin', 'satScale', 'valScale', 'tintStrength',
            'replaceColor', 'replaceMode', 'replaceTolerance', 'regionFeather'
        ];

        function readLegacySettings() {
            try {
                const raw = localStorage.getItem(settingsStorageKey);
                if (!raw) return [];
                const saved = JSON.parse(raw);
                if (saved.version === 2 && Array.isArray(saved.presets)) return saved.presets;
                if (saved.version === 1 && saved.values) {
                    return [{ name: '我的設定', values: saved.values, sourceSample: saved.sourceSample || null }];
                }
            } catch (e) {
                return [];
            }
            return [];
        }

        async function migrateLegacySettings() {
            let legacyPresets = readLegacySettings();
            if (!legacyPresets.length) return;

            try {
                const currentResponse = await fetch('settings');
                if (!currentResponse.ok) return;
                const remotePresets = await currentResponse.json();

                for (const legacy of legacyPresets) {
                    const baseName = String(legacy.name || '我的設定').trim() || '我的設定';
                    const valuesJson = JSON.stringify(legacy.values || {});
                    const sampleJson = JSON.stringify(legacy.sourceSample || null);
                    const equivalentExists = remotePresets.some(preset => {
                        const nameMatches = preset.name === baseName || preset.name.startsWith(`${baseName} (匯入`);
                        return nameMatches
                            && JSON.stringify(preset.values || {}) === valuesJson
                            && JSON.stringify(preset.sourceSample || null) === sampleJson;
                    });
                    if (equivalentExists) continue;

                    let name = baseName;
                    let suffix = 2;
                    while (remotePresets.some(preset => preset.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
                        name = `${baseName} (匯入 ${suffix++})`;
                    }
                    const response = await fetch('settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name,
                            values: legacy.values || {},
                            sourceSample: legacy.sourceSample || null
                        })
                    });
                    if (!response.ok) return;
                    remotePresets.push(await response.json());
                }
                localStorage.removeItem(settingsStorageKey);
            } catch (e) {
                console.warn('Could not migrate browser settings to SQLite.', e);
            }
        }

        function populateSettingsList(selectedId = '') {
            const select = g('savedSettingsSelect');
            const previousId = String(selectedId || select.value || '');
            select.replaceChildren(new Option('選擇已儲存設定', ''));
            savedSettings.forEach(preset => {
                select.add(new Option(preset.name, String(preset.id)));
            });
            select.value = savedSettings.some(preset => String(preset.id) === previousId) ? previousId : '';
            g('btnLoadSettings').disabled = !select.value;
        }

        async function refreshSettingsStatus(selectedId = '') {
            try {
                await migrateLegacySettings();
                const response = await fetch('settings');
                if (!response.ok) throw new Error('Could not load settings from SQLite');
                savedSettings = await response.json();
                populateSettingsList(selectedId);
                g('settingsStatus').textContent = savedSettings.length
                    ? `SQLite 中有 ${savedSettings.length} 組設定；選擇後可套用。`
                    : '設定會儲存在這台伺服器的 SQLite 資料庫。';
            } catch (e) {
                g('btnLoadSettings').disabled = true;
                g('settingsStatus').textContent = '無法讀取 SQLite 設定檔，請確認 Shiny Maker 伺服器可用。';
            }
        }

        async function saveSettings() {
            const name = g('settingsName').value.trim();
            if (!name) {
                g('settingsStatus').textContent = '請先輸入設定檔名稱。';
                g('settingsName').focus();
                return;
            }

            await settingsReady;
            const values = {};
            settingControlIds.forEach(id => { values[id] = g(id).value; });
            const existing = savedSettings.some(preset =>
                preset.name.trim().toLocaleLowerCase() === name.toLocaleLowerCase()
            );
            const payload = {
                name,
                values,
                sourceSample: replacementSample ? {
                    hex: replacementSample.hex,
                    xRatio: replacementSample.xRatio,
                    yRatio: replacementSample.yRatio
                } : null
            };

            try {
                const response = await fetch('settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message || 'Could not save settings');
                if (replacementSample) replacementSample.savedForReuse = true;
                await refreshSettingsStatus(result.id);
                g('settingsName').value = name;
                g('settingsStatus').textContent = `已${existing ? '更新' : '儲存'}「${name}」${replacementSample ? '，來源色也會沿用到後續圖片。' : '。'}`;
            } catch (e) {
                g('settingsStatus').textContent = '無法儲存設定至 SQLite，請確認 Shiny Maker 伺服器可用。';
            }
        }

        function loadSettings() {
            const preset = savedSettings.find(item => String(item.id) === g('savedSettingsSelect').value);
            if (!preset || !preset.values) {
                g('settingsStatus').textContent = '找不到可套用的已記錄設定。';
                g('btnLoadSettings').disabled = true;
                return;
            }

            settingControlIds.forEach(id => {
                if (preset.values[id] !== undefined) g(id).value = preset.values[id];
            });
            hueVal.textContent = hueRange.value;
            satScaleVal.textContent = satScale.value;
            valScaleVal.textContent = valScale.value;
            tintVal.textContent = tintStrength.value;
            g('replaceColorHex').textContent = replaceColor.value;
            g('replaceToleranceVal').textContent = replaceTolerance.value;
            g('regionFeatherVal').textContent = regionFeather.value;
            replaceMode.value = preset.values.replaceMode === 'region' ? 'region' : 'global';
            updateReplacementControls();

            const sample = preset.sourceSample;
            if (sample && /^#[0-9a-f]{6}$/i.test(sample.hex)
                && Number.isFinite(sample.xRatio) && Number.isFinite(sample.yRatio)) {
                replacementSample = {
                    x: null,
                    y: null,
                    xRatio: Math.max(0, Math.min(1, sample.xRatio)),
                    yRatio: Math.max(0, Math.min(1, sample.yRatio)),
                    hex: sample.hex,
                    fromPreset: true
                };
                g('sourceColorSwatch').style.backgroundColor = sample.hex;
                g('sourceColorHex').textContent = sample.hex;
            } else {
                replacementSample = null;
                g('sourceColorSwatch').style.backgroundColor = '';
                g('sourceColorHex').textContent = '尚未取色';
            }

            g('settingsName').value = preset.name;
            g('settingsStatus').textContent = `已套用「${preset.name}」${replacementSample ? '與來源色。' : '。'}`;
            if (timer) clearTimeout(timer);
            processImage();
        }

        g('savedSettingsSelect').onchange = () => {
            const preset = savedSettings.find(item => String(item.id) === g('savedSettingsSelect').value);
            g('btnLoadSettings').disabled = !preset;
            if (preset) g('settingsName').value = preset.name;
        };
        g('settingsName').onkeydown = (event) => {
            if (event.key === 'Enter') saveSettings();
        };

        document.getElementById('file').onchange = (e) => {
            currentFile = e.target.files[0];
            if (replacementSample && (replacementSample.fromPreset || replacementSample.savedForReuse)) {
                replacementSample.fromPreset = true;
                replacementSample.x = null;
                replacementSample.y = null;
            } else {
                replacementSample = null;
                g('sourceColorSwatch').style.backgroundColor = '';
                g('sourceColorHex').textContent = '尚未取色';
            }
            if (currentFile) processImage(); 
        };

        settingsReady = refreshSettingsStatus();

        function throttledProcess() {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => { processImage(); }, 50);
        }

        async function processImage() {
            if (!currentFile) return;
            const requestId = ++processRequestId;
            const fd = new FormData();
            fd.append('file', currentFile);
            fd.append('hue_shift', document.getElementById('hueRange').value);
            fd.append('sat_min', document.getElementById('satMin').value);
            fd.append('sat_scale', document.getElementById('satScale').value);
            fd.append('val_scale', document.getElementById('valScale').value);
            
            // --- 新增這一行 ---
            fd.append('tint_strength', tintStrength.value); 
            fd.append('replace_x', replacementSample && Number.isInteger(replacementSample.x) ? replacementSample.x : -1);
            fd.append('replace_y', replacementSample && Number.isInteger(replacementSample.y) ? replacementSample.y : -1);
            fd.append('replace_x_ratio', replacementSample ? replacementSample.xRatio : -1);
            fd.append('replace_y_ratio', replacementSample ? replacementSample.yRatio : -1);
            fd.append('replace_source_color', replacementSample && replacementSample.fromPreset ? replacementSample.hex : '');
            fd.append('replace_color', replaceColor.value);
            fd.append('replace_mode', replaceMode.value);
            fd.append('replace_tolerance', replaceTolerance.value);
            fd.append('region_feather', regionFeather.value);

            try {
                // 請確保 fetch 的路徑是相對路徑 'process_shiny' (為了 main.py 整合)
                const r = await fetch('process_shiny', { method: 'POST', body: fd });
                if (!r.ok) throw new Error('Backend process failed');
                const blob = await r.blob();
                if (requestId !== processRequestId) return;
                
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


@app.get('/settings')
def list_settings():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            'SELECT id, name, settings_json, updated_at FROM shiny_settings ORDER BY name COLLATE NOCASE'
        ).fetchall()
    settings = []
    for setting_id, name, settings_json, updated_at in rows:
        payload = json.loads(settings_json)
        settings.append({
            'id': str(setting_id),
            'name': name,
            'values': payload.get('values', {}),
            'sourceSample': payload.get('sourceSample'),
            'savedAt': updated_at
        })
    return settings


@app.post('/settings')
async def save_settings(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={'message': 'Invalid JSON body'})

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={'message': 'Settings must be an object'})
    name = body.get('name')
    values = body.get('values')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 48:
        return JSONResponse(status_code=400, content={'message': 'Name must be between 1 and 48 characters'})
    if not isinstance(values, dict):
        return JSONResponse(status_code=400, content={'message': 'Settings values are required'})

    name = name.strip()
    payload = json.dumps({
        'values': values,
        'sourceSample': body.get('sourceSample') if isinstance(body.get('sourceSample'), dict) else None
    }, ensure_ascii=False)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute('''
            INSERT INTO shiny_settings (name, settings_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                settings_json = excluded.settings_json,
                updated_at = CURRENT_TIMESTAMP
        ''', (name, payload))
        row = connection.execute(
            'SELECT id, name, settings_json, updated_at FROM shiny_settings WHERE name = ?',
            (name,)
        ).fetchone()

    saved = json.loads(row[2])
    return {
        'id': str(row[0]),
        'name': row[1],
        'values': saved.get('values', {}),
        'sourceSample': saved.get('sourceSample'),
        'savedAt': row[3]
    }

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


def apply_color_replacement(
    bgr: np.ndarray,
    x: int,
    y: int,
    target_hex: str,
    mode: str,
    tolerance: float,
    region_feather: float,
    source_hex: str = '',
    alpha: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Replace colors near the sampled pixel while retaining local shading."""
    height, width = bgr.shape[:2]
    has_seed = 0 <= x < width and 0 <= y < height
    if not source_hex and not has_seed:
        return bgr

    def parse_hex(hex_value: str) -> Optional[Tuple[int, int, int]]:
        value = hex_value.strip().lstrip('#')
        if len(value) != 6:
            return None
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None

    target_rgb = parse_hex(target_hex)
    source_rgb = parse_hex(source_hex) if source_hex else None
    if target_rgb is None or (source_hex and source_rgb is None):
        return bgr

    # Work in CIELAB so the selection radius tracks perceived color difference.
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    if source_rgb is not None:
        red, green, blue = source_rgb
        source_bgr = np.array([[[blue, green, red]]], dtype=np.float32) / 255.0
        source_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2Lab)[0, 0]
    else:
        source_lab = lab[y, x].copy()
    red, green, blue = target_rgb
    target_bgr = np.array([[[blue, green, red]]], dtype=np.float32) / 255.0
    target_lab = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2Lab)[0, 0]
    distance = np.linalg.norm(lab - source_lab, axis=2)
    tolerance = float(np.clip(tolerance, 1.0, 100.0))

    if mode == 'region':
        candidates = (distance <= tolerance).astype(np.uint8)
        if not has_seed or candidates[y, x] == 0:
            candidate_y, candidate_x = np.where(candidates > 0)
            if not len(candidate_x):
                return bgr
            seed_x = x if has_seed else width // 2
            seed_y = y if has_seed else height // 2
            nearest = np.argmin((candidate_x - seed_x) ** 2 + (candidate_y - seed_y) ** 2)
            x, y = int(candidate_x[nearest]), int(candidate_y[nearest])
        cv2.floodFill(candidates, None, (x, y), 2, flags=4)
        region = candidates == 2
        if not np.any(region):
            return bgr
        weights = region.astype(np.float32)
        feather = float(np.clip(region_feather, 0.0, 8.0))
        if feather > 0:
            softened = cv2.GaussianBlur(
                weights, (0, 0), sigmaX=max(0.5, feather / 2.0)
            )
            peak = float(softened[region].max())
            if peak > 0:
                weights[region] = np.clip(softened[region] / peak, 0.0, 1.0)
            weights[~region] = 0.0
    else:
        # Keep nearby colors at full strength, then smoothly fade the edge of
        # the match so the replacement does not create a hard color boundary.
        feather = max(1.0, tolerance * 0.25)
        low = max(0.0, tolerance - feather)
        high = tolerance + feather
        t = np.clip((distance - low) / (high - low), 0.0, 1.0)
        weights = 1.0 - (t * t * (3.0 - 2.0 * t))

    if alpha is not None:
        weights[alpha == 0] = 0.0

    active = weights > 0
    if not np.any(active):
        return bgr

    shifted_lab = lab + (target_lab - source_lab) * weights[:, :, None]
    shifted_bgr = np.clip(
        cv2.cvtColor(shifted_lab, cv2.COLOR_Lab2BGR) * 255.0, 0, 255
    ).astype(np.uint8)
    result = bgr.copy()
    result[active] = shifted_bgr[active]
    return result

@app.post('/process_shiny')
async def process_shiny(
    file: UploadFile = File(...),
    hue_shift: int = Form(...),
    sat_min: int = Form(...),
    sat_scale: float = Form(...),
    val_scale: float = Form(...),
    # 新增參數：染色強度 (0.0 為原本邏輯, 1.0 為完全強制染色)
    tint_strength: float = Form(0.0),
    replace_x: int = Form(-1),
    replace_y: int = Form(-1),
    replace_color: str = Form('#ff4d7d'),
    replace_mode: str = Form('global'),
    replace_tolerance: float = Form(24.0),
    region_feather: float = Form(2.0),
    replace_source_color: str = Form(''),
    replace_x_ratio: float = Form(-1.0),
    replace_y_ratio: float = Form(-1.0),
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

        if replace_x_ratio >= 0 and replace_y_ratio >= 0:
            replace_x = int(round(np.clip(replace_x_ratio, 0.0, 1.0) * (bgr.shape[1] - 1)))
            replace_y = int(round(np.clip(replace_y_ratio, 0.0, 1.0) * (bgr.shape[0] - 1)))

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

        if replace_source_color or (replace_x >= 0 and replace_y >= 0):
            res_bgr = apply_color_replacement(
                res_bgr,
                replace_x,
                replace_y,
                replace_color,
                replace_mode,
                replace_tolerance,
                region_feather,
                replace_source_color,
                alpha,
            )

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
