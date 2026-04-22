# SpriteTool - Game Developer Tool Suite

[English Version](./README_EN.md) | [中文版](./README.md)

一個功能強大的遊戲開發工具套件，提供 Sprite 和圖片編輯的完整解決方案。

## 🎯 功能概述

SpriteTool 是一個整合式的 Web 應用程式，集合了三個專業級工具於一身：

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

---

## 📂 項目結構

```
SpriteTool/
├── tool.py                          # 主應用入口（FastAPI 聚合）
├── sprite_tool_fullstack.py         # Grid Tool 子應用
├── sprite_webtool.py                # Sprite Picker 子應用
├── shiny_maker.py                   # Shiny Monster Maker 子應用
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

---

## 🎨 UI/UX 特性

- **深色主題** - 護眼的深灰配色
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

**最後更新**: 2026 年 4 月  
**版本**: 1.0.0
