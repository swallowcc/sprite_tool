# SpriteTool - Game Developer Tool Suite

A powerful suite of game development tools providing a complete solution for Sprite and image editing.

## 🎯 Feature Overview

SpriteTool is an integrated web application that combines four professional-grade tools into one:

### 📏 Grid Tool
Used to define regular grid areas on an image and perform batch selections.

**Key Features:**
- Automatically generate grids based on rows and columns (e.g., 64x95 cells).
- Supports drag-to-pan and scroll-to-zoom.
- Cmd+Click to select any rectangular area.
- Real-time calculation of total selected cells.
- Export or edit area definitions in JSON format.
- Supports undo and clear operations.
- Batch export as a single PNG image.

**Use Cases:** Tilemap creation, Sprite Sheet splitting, map editing.

---

### 🎯 Sprite Picker
Quickly select and extract individual sprites from complex Sprite Sheets.

**Key Features:**
- Free-hand selection box (supports any size and position).
- Unified Sprite dimension settings (width/height).
- Set column count for export with automatic layout.
- Real-time preview of selected Sprites.
- Click preview images to remove unwanted Sprites.
- Export as optimized PNG images.

**Use Cases:** Character animation decomposition, prop extraction, UI asset organization.

---

### ✨ Shiny Monster Maker
Professional-grade "shiny" variant adjustment using HSV color space.

**Key Features:**
- **Hue Shift** - 0~180° color wheel rotation.
- **Saturation** - 0~2x multiplier adjustment.
- **Brightness** - 0~2x multiplier adjustment.
- **Saturation Mask** - Protects gray/black pixels.
- Real-time effect preview.
- Supports multiple image input formats.
- One-click download of the result.

**Use Cases:** Shiny variant creation, character skin adjustment, thematic color swapping.

---

### 🔄 Sprite Flipper
Quickly perform horizontal flipping (mirroring) for each animation cell in a Sprite Sheet.

**Key Features:**
- Precisely split cells based on configured row and column counts.
- Batch horizontal flip for all cells.
- Real-time preview of both original and result images.
- Preserves Alpha transparency channel.
- One-click download of the complete flipped Sprite Sheet.

**Use Cases:** Creating mirrored animations, symmetrical Tilemap variants, character action adjustments.

---

### 🧩 Sprite Merger
Precisely merge source Sprite into the target cell of a main Sprite Sheet.

**Key Features:**
- Upload main image and source sprite.
- Set main image row/column counts with automatic cell size calculation.
- Specify target cell coordinates (Column / Row).
- Automatic alignment and merge of source sprite to target position.
- Preserves transparency and color information.
- Real-time preview of merge result.
- One-click download of completed image.

**Use Cases:** Character variant assembly, Tilemap element composition, Sprite Sheet content updates.

---

### ✂️ Inset Crop Tool
Remove Chroma Key background and perform intelligent inset cropping and enlargement on Sprite Sheets.

**Key Features:**
- **Color Removal** - Custom chroma key (default #ff00ff pink) and threshold adjustment.
- **Real-time Preview** - Instantly view background removal effects while adjusting threshold.
- **Smart Cropping** - Precisely divide cells based on rows/columns and inset distance.
- **Enlarge After Crop** - Automatically enlarge back to original cell size after inset cropping.
- **Batch Export** - Export individual cell PNGs + combined full image.
- **ZIP Archive** - Download all results in a single ZIP package.

**Use Cases:** Sprite Sheet background removal, pixel art standardization, animation frame sequence optimization.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FastAPI
- Pillow (PIL)
- OpenCV (cv2)
- Uvicorn
- Starlette

### Install Dependencies

```bash
pip install fastapi uvicorn pillow opencv-python starlette
```

### Run Application

```bash
python tool.py
```

The application will start at `http://localhost:8000`

Visit the home page to see all available tools, or access them directly:
- **Grid Tool**: `http://localhost:8000/grid/`
- **Sprite Picker**: `http://localhost:8000/picker/`
- **Shiny Maker**: `http://localhost:8000/shiny/`
- **Sprite Flipper**: `http://localhost:8000/flipper/`
- **Sprite Merger**: `http://localhost:8000/merger/`
- **Inset Crop Tool**: `http://localhost:8000/inset/`

## 📂 Project Structure

```
SpriteTool/
├── tool.py                          # Main entry point (FastAPI aggregation)
├── sprite_tool_fullstack.py         # Grid Tool sub-app
├── sprite_webtool.py                # Sprite Picker sub-app
├── shiny_maker.py                   # Shiny Monster Maker sub-app
├── rotate_webtool.py                # Sprite Flipper sub-app
├── rotate.py                        # Flipper core processing logic
├── sprite_merger.py                 # Sprite Merger sub-app
├── inset_crop_tool.py               # Inset Crop Tool sub-app
├── remove_pink_background.py        # Color removal tool (standalone use)
├── output/                          # Grid Tool export directory
├── shiny_output/                    # Shiny Maker export directory
└── README.md                        # This file
```

---

## 🎮 User Guide

### Grid Tool Workflow

1. **Upload Image** - Select the Sprite Sheet to cut.
2. **Set Grid** - Enter row and column counts (e.g., 64x95).
3. **Select Areas**
   - Drag to pan the image.
   - Cmd+Click to select rectangular areas.
   - Or modify coordinates directly in the JSON editor below.
4. **Export** - Set output columns and name, then click Export.

### Sprite Picker Workflow

1. **Upload Sheet** - Select an image containing multiple Sprites.
2. **Adjust Settings**
   - Set uniform Sprite width and height.
   - Set the number of columns for the exported row.
3. **Select Sprites** - Draw boxes on the canvas to select Sprites to extract.
4. **Check Preview** - View thumbnail previews on the left.
5. **Remove Errors** - Click a preview image to remove unwanted Sprites.
6. **Export** - Enter a filename and click Export Image.

### Shiny Maker Workflow

1. **Upload Original Image** - Select the image to recolor.
2. **Adjust Parameters**
   - Drag **Hue Shift** slider to change tone.
   - Adjust **Saturation** multiplier.
   - Adjust **Brightness** multiplier.
   - Set **Saturation Mask** to protect neutral colors.
3. **Real-time Preview** - View the effect instantly on the right.
4. **Download** - Click "Download" once satisfied.

### Sprite Flipper Workflow

1. **Upload Image** - Select the Sprite Sheet to flip.
2. **Set Partition** - Enter the row and column counts (Cols/Rows).
3. **Execute Flip** - Click the button to process each cell automatically.
4. **Check Result** - View the flipped preview image below.
5. **Download** - Click the download button to get the result.

### Sprite Merger Workflow

1. **Upload Images** - Select the main Sprite Sheet and source sprite.
2. **Set Main Grid** - Enter the row and column counts for the main image.
3. **Specify Target Position** - Enter the target column and row indices (starting from 0).
4. **Preview Merge** - View the merge result preview.
5. **Download** - Click the download button to get the merged image.

### Inset Crop Tool Workflow

1. **Upload Sprite Sheet** - Select an image with chroma key background.
2. **Adjust Background Removal Settings**
   - Choose or input the background color (e.g., #ff00ff).
   - Adjust Threshold slider and observe real-time preview on the right.
   - Confirm the background removal result.
3. **Configure Crop Parameters**
   - Enter grid row and column counts (Cols/Rows).
   - Set inset distance (px) for all edges.
   - View calculated cell size and output count.
4. **Confirm and Download**
   - Click "Confirm and Download ZIP" button.
   - System executes: Remove background → Inset crop → Enlarge back → Package.
   - Download ZIP containing all individual cell PNGs + combined image.

---

## 🛠️ Technical Architecture

### Core Tech Stack
- **Backend Framework**: FastAPI (High-performance asynchronous web framework)
- **Frontend Framework**: Tailwind CSS (Utility-first CSS framework)
- **Image Processing**: Pillow + OpenCV
- **Color Space**: HSV color conversion and processing

### System Design

**Tool Entry (tool.py)**
- Unified navigation bar middleware.
- Sub-app mounting mechanism.
- Home page information display.

**Image Processing Pipeline**
- Frontend drag/click interaction → Coordinate transmission.
- Backend Python image calculation → Binary output.
- Real-time preview + batch export.

---

## 📝 API Endpoints

### Grid Tool
- `GET /grid/` - Home page.
- `POST /grid/upload` - Upload image and generate preview.

### Sprite Picker  
- `GET /picker/` - Home page.
- `POST /picker/upload` - Upload image.
- `POST /picker/export` - Export selected Sprites.

### Shiny Maker
- `GET /shiny/` - Home page.
- `POST /shiny/process` - Process shiny adjustment.
- `GET /shiny/download` - Download result.

### Sprite Flipper
- `GET /flipper/` - Home page.
- `POST /flipper/flip` - Execute sprite flipping process.

### Sprite Merger
- `GET /merger/` - Home page.
- `POST /merger/merge` - Execute sprite merge process.

### Inset Crop Tool
- `GET /inset/` - Home page.
- `POST /inset/preview` - Real-time background removal preview.
- `POST /inset/process` - Execute background removal + cropping + packaging.
---

## 🎨 UI/UX Features

- **Dark Theme** - Eye-friendly dark gray color scheme.
- **Responsive Design** - Optimized for desktop and tablets.
- **Instant Preview** - Lag-free visual feedback.
- **Drag-and-Drop Interaction** - Intuitive image manipulation.
- **Touch-Friendly** - Precise pixel-level selection.

---

## 📊 Common Use Cases

### Indie Game Development
- Sprite Sheet cutting and optimization.
- Monster/character shiny variant creation.
- Animation frame sequence organization.

### Art Workflow
- Tilemap asset preparation.
- UI atlas organization.
- Character skin variant production.

### Resource Optimization
- Batch Sprite extraction.
- Unified size normalization.
- Reduction of resource file counts.

---

## 🔧 Troubleshooting

**Problem: Image fails to upload**
- Check image format (Supports PNG, JPG, GIF).
- Ensure file size is reasonable.

**Problem: Exported image is blurry**
- Confirm original image is in pixel art format.
- Check browser zoom level.

**Problem: Color adjustment effect is suboptimal**
- Adjust Saturation Mask value.
- Try different Hue Shift angles.

---

## 📄 License

Open-source project, free to use and modify.

---

## 👤 Contribution

Issues and Pull Requests are welcome!

---

**Last Updated**: May 2026  
**Version**: 1.1.0
