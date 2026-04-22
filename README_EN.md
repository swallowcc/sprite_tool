# SpriteTool - Game Developer Tool Suite

A powerful suite of game development tools providing a complete solution for Sprite and image editing.

## 🎯 Feature Overview

SpriteTool is an integrated web application that combines three professional-grade tools into one:

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

---

## 📂 Project Structure

```
SpriteTool/
├── tool.py                          # Main entry point (FastAPI aggregation)
├── sprite_tool_fullstack.py         # Grid Tool sub-app
├── sprite_webtool.py                # Sprite Picker sub-app
├── shiny_maker.py                   # Shiny Monster Maker sub-app
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

**Last Updated**: April 2026  
**Version**: 1.0.0
