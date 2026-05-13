# SpriteTool - Game Developer Tool Suite

[English Version](./README_EN.md) | [中文版](./README.md)

一個功能強大的遊戲開發工具套件，提供 Sprite 和圖片編輯的完整解決方案。

## 🎯 功能概述

SpriteTool 是一個整合式的 Web 應用程式，集合了四個專業級工具於一身：

### 📏 Grid Tool（網格工具）
用於在圖片上定義規則的網格區域並進行批量選取。

**功能特性：**
- 根據行列數自動生成網格（如 64×95 格子）
- 支援拖拽平移和滾輪縮放
- Cmd+點擊選取任意矩形區域
- 實時計算選中的總格數
- 以 JSON 格式導出或編輯區域定義
- 支援撤銷和清除操作
- 批量導出為單張 PNG 圖片

**使用場景：** Tilemap 製作、Sprite Sheet 分割、地圖編輯

---

### 🎯 Sprite Picker（精靈選取器）
從複雜的 Sprite Sheet 中快速選取和提取個別 Sprite。

**功能特性：**
- 自由繪製選取框（支援任意大小和位置）
- 統一設定 Sprite 尺寸（寬高設定）
- 設定導出時的列數，自動排列
- 即時預覽已選取的 Sprite
- 點擊預覽圖移除不需要的 Sprite
- 導出為優化的 PNG 圖片

**使用場景：** 角色動畫分解、道具提取、UI 圖片整理

---

### ✨ Shiny Monster Maker（色違製作工具）
使用 HSV 色彩空間進行專業級色違調整。

**功能特性：**
- **Hue Shift（色調）** - 0~180° 旋轉色盤
- **Saturation（飽和度）** - 0~2 倍率調整
- **Brightness（亮度）** - 0~2 倍率調整
- **Saturation Mask（飽和度過濾）** - 保護灰色/黑色像素
- 實時預覽效果
- 支援多格式圖片輸入
- 一鍵下載成品

**使用場景：** 色違製作、角色皮膚調整、主題變色

---

### 🔄 Sprite Flipper（精靈翻轉工具）
快速對 Sprite Sheet 中的每個動作格進行水平翻轉（左右鏡像）。

**功能特性：**
- 根據設定的行列數精確分割格子
- 批量水平翻轉所有 Cell
- 支援即時原圖與結果預覽
- 保持 Alpha 透明頻道
- 一鍵下載翻轉後的完整 Sprite Sheet

**使用場景：** 動畫鏡像製作、Tilemap 對稱變體生成、角色動作調整

---

### 🧩 Sprite Merger（精靈合併工具）
將來源 Sprite 精確合併到主 Sprite Sheet 的指定格位。

**功能特性：**
- 上傳主圖和來源圖片
- 設定主圖的行列數，自動計算格子尺寸
- 指定目標格位座標（Column / Row）
- 自動對齊並合併來源圖到目標位置
- 保留透明度和色彩資訊
- 即時預覽合併結果
- 一鍵下載完成的圖片

**使用場景：** 角色變體組裝、Tilemap 元素組合、Sprite Sheet 內容更新

---

### ✂️ Inset Crop Tool（內縮裁切工具）
去除 Chroma Key 底色後，對 Sprite Sheet 進行內縮裁切及放大處理。

**功能特性：**
- **色彩去除** - 自訂底色（預設 #ff00ff 粉紅色）及去除閾值
- **即時預覽** - 調整 threshold 時實時顯示去底色效果
- **預覽底色檢查** - 可修改預覽背景顏色以檢查邊界精度（純檢查用，不影響導出）
- **內縮虛線框** - 在預覽上顯示每個格子的內縮邊界（粉紅色虛線框），視覺化檢查內縮效果
- **智慧裁切** - 根據行列數和內縮距離精確分割每格
- **縮放還原** - 內縮後自動放大回原格尺寸
- **批量輸出** - 導出個別格子 PNG + 組合完整圖
- 支援 ZIP 壓縮打包下載

**使用場景：** Sprite Sheet 去底色處理、像素藝術格式標準化、動畫幀序列優化

---

## 🚀 快速開始

### 環境需求
- Python 3.8+
- FastAPI
- Pillow (PIL)
- OpenCV (cv2)
- Uvicorn
- Starlette

### 安裝依賴

```bash
pip install fastapi uvicorn pillow opencv-python starlette
```

### 運行應用

```bash
python tool.py
```

應用將啟動在 `http://localhost:8000`

訪問首頁查看所有可用工具，或直接訪問：
- **Grid Tool**: `http://localhost:8000/grid/`
- **Sprite Picker**: `http://localhost:8000/picker/`
- **Shiny Maker**: `http://localhost:8000/shiny/`
- **Sprite Flipper**: `http://localhost:8000/flipper/`
- **Sprite Merger**: `http://localhost:8000/merger/`
- **Inset Crop Tool**: `http://localhost:8000/inset/`

---

## 📂 項目結構

```
SpriteTool/
├── tool.py                          # 主應用入口（FastAPI 聚合）
├── sprite_tool_fullstack.py         # Grid Tool 子應用
├── sprite_webtool.py                # Sprite Picker 子應用
├── shiny_maker.py                   # Shiny Monster Maker 子應用
├── rotate_webtool.py                # Sprite Flipper 子應用
├── rotate.py                        # Flipper 核心處理邏輯
├── sprite_merger.py                 # Sprite Merger 子應用
├── inset_crop_tool.py               # Inset Crop Tool 子應用
├── remove_pink_background.py        # 色彩去除工具（獨立使用）
├── output/                          # Grid Tool 導出目錄
├── shiny_output/                    # Shiny Maker 導出目錄
└── README.md                        # 本文件
```

---

## 🎮 使用指南

### Grid Tool 工作流

1. **上傳圖片** - 選擇要切割的 Sprite Sheet
2. **設定網格** - 輸入行列數（如 64×95）
3. **選取區域**
   - 拖拽平移圖片
   - Cmd+點擊選取矩形區域
   - 或在下方 JSON 編輯器直接修改座標
4. **導出** - 設定輸出的列數、名稱後點擊 Export

### Sprite Picker 工作流

1. **上傳 Sheet** - 選擇包含多個 Sprite 的圖片
2. **調整設定**
   - 設定 Sprite 的統一寬高
   - 設定導出時每行的列數
3. **選取 Sprite** - 在畫布上繪製框選要提取的 Sprite
4. **檢查預覽** - 查看左側的縮略圖預覽
5. **移除錯誤** - 點擊預覽圖移除不需要的 Sprite
6. **導出** - 輸入檔名後點擊 Export Image

### Shiny Maker 工作流

1. **上傳原始圖片** - 選擇要變色的圖片
2. **調整參數**
   - 拖動 **Hue Shift** 滑桿改變色調
   - 調整 **Saturation** 改變飽和度
   - 調整 **Brightness** 改變亮度
   - 設定 **Saturation Mask** 保護中性色
3. **實時預覽** - 右側即時顯示效果
4. **下載** - 滿意後點擊「下載」按鈕

### Sprite Flipper 工作流

1. **上傳圖片** - 選擇要翻轉的 Sprite Sheet
2. **設定分割** - 輸入圖片對應的行列數（Cols/Rows）
3. **執行翻轉** - 點擊執行按鈕，系統將自動處理每個格子
4. **檢查結果** - 下方會顯示翻轉後的預覽圖
5. **下載** - 點擊下載按鈕取得成品

### Sprite Merger 工作流

1. **上傳圖片** - 選擇主 Sprite Sheet 和來源圖片
2. **設定主圖網格** - 輸入主圖的行列數
3. **指定目標位置** - 輸入目標 Column 和 Row 編號（從 0 開始）
4. **檢查預覽** - 查看合併後的預覽結果
5. **下載** - 點擊下載按鈕取得合併後的圖片

### Inset Crop Tool 工作流

1. **上傳 Sprite Sheet** - 選擇含有底色的圖片
2. **調整去底色設定**
   - 選擇或輸入底色（如 #ff00ff）
   - 調整 Threshold 閾值，觀察右側實時預覽
   - 確認去底色效果滿意
3. **設定裁切參數**
   - 輸入圖片的行列數（Cols/Rows）
   - 設定四邊內縮距離（px）
   - 查看計算的格子尺寸及輸出數量
4. **確認並下載**
   - 點擊「確認並下載 ZIP」按鈕
   - 系統執行去底色 → 內縮裁切 → 放大還原
   - 下載包含所有格子 PNG + 完整組合圖的 ZIP 檔

---

## 🛠️ 技術架構

### 核心技術棧
- **後端框架**: FastAPI（高性能異步 Web 框架）
- **前端框架**: Tailwind CSS（無頭 CSS 框架）
- **圖像處理**: Pillow + OpenCV
- **顏色空間**: HSV 色彩轉換和処理

### 系統設計

**工具入口（tool.py）**
- 統一的導覽欄中間件
- 子應用挂載機制
- 首頁信息展示

**圖像處理管線**
- 前端拖拽/點擊交互 → 座標發送
- 後端 Python 圖像運算 → 二進制輸出
- 實時預覽 + 批量導出

---

## 📝 API 端點

### Grid Tool
- `GET /grid/` - 首頁
- `POST /grid/upload` - 上傳圖片並生成預覽

### Sprite Picker  
- `GET /picker/` - 首頁
- `POST /picker/upload` - 上傳圖片
- `POST /picker/export` - 導出選中的 Sprite

### Shiny Maker
- `GET /shiny/` - 首頁
- `POST /shiny/process` - 處理色違調整
- `GET /shiny/download` - 下載成品

### Sprite Flipper
- `GET /flipper/` - 首頁
- `POST /flipper/flip` - 執行精靈翻轉處理

### Sprite Merger
- `GET /merger/` - 首頁
- `POST /merger/merge` - 執行精靈合併處理

### Inset Crop Tool
- `GET /inset/` - 首頁
- `POST /inset/preview` - 即時預覽去底色效果
- `POST /inset/process` - 執行去底色 + 裁切 + 打包

---

## 🎨 UI/UX 特性

- **深色主題** - 護眼的深灰配色
- **統一導覽體驗** - 透過 FastAPI 中間件在所有工具頁面自動注入導覽列
- **標準化佈局** - 所有工具採用一致的寬螢幕佈局（Max-width 7xl）與標題樣式
- **響應式設計** - 適配桌面和平板
- **即時預覽** - 無延遲的視覺反饋
- **拖拽交互** - 直觀的圖像操作
- **觸控友善** - 精確的像素級選取

---

## 📊 常見用途

### 獨立遊戲開發
- Sprite Sheet 的切割和優化
- 怪物/角色的色違製作
- 動畫幀序列的組織

### 美術工作流
- Tilemap 素材準備
- UI 圖集組織
- 角色皮膚變體製作

### 資源優化
- Sprite 批量提取
- 統一尺寸規範化
- 減少資源檔案數量

---

## 🔧 故障排除

**問題：圖片無法上傳**
- 檢查圖片格式（支援 PNG, JPG, GIF）
- 確認檔案大小合理

**問題：導出後圖片模糊**
- 確認原始圖片是像素藝術格式
- 檢查瀏覽器縮放比例

**問題：顏色調整效果不理想**
- 調整飽和度過濾值
- 嘗試不同的 Hue Shift 角度

---

## 📄 許可證

開源項目，自由使用和修改。

---

## 👤 貢獻

歡迎提交 Issue 和 Pull Request！

---

**最後更新**: 2026 年 5 月  
**版本**: 1.2.0
