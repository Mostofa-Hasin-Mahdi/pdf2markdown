# PDF to Markdown Desktop Converter

![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Electron.js](https://img.shields.io/badge/Electron-191970?style=for-the-badge&logo=Electron&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![spaCy](https://img.shields.io/badge/spaCy-09A3D5.svg?style=for-the-badge&logo=spacy&logoColor=white)
![Tesseract OCR](https://img.shields.io/badge/Tesseract_OCR-black?style=for-the-badge)

A highly modular, robust, and 100% free **Desktop PDF to Markdown Conversion Engine** built with Electron, Next.js, and Python.

This tool is designed to accurately extract structural content from PDFs—including semantic headings, tables, bulleted lists, inline formatting, images, and raw text—and assemble it perfectly into GitHub-flavored Markdown. It intelligently bypasses the common pitfalls of PDF parsing (like randomly broken sentences and fractured tables) using a combination of geographic bounding box analysis and Natural Language Processing.

## ✨ Key Features

- **Beautiful Native UI:** A stunning, glassmorphic drag-and-drop Desktop Application built with Next.js and Framer Motion.
- **100% Offline Processing:** Completely self-contained. No internet connection, Python environments, or Node.js installations required for the end user.
- **Real-Time Telemetry:** Watch the Python engine crunch through your PDFs with a Matrix-style terminal log viewer built directly into the React UI.
- **Semantic Heading Detection:** Mathematically calculates the document's base font size and scales headers (`#`, `##`) dynamically based on mathematical ratios.
- **Flawless Tables:** Geometrically detects table grids using `pdfplumber`, extracts them via Pandas DataFrames, and prints them as perfectly aligned Markdown tables.
- **Spatial Deduplication & Sorting:** Tracks the exact `(x,y)` coordinates of every paragraph, table, and image. It actively prunes duplicate text hidden inside table bounds and chronologically sorts elements from top to bottom.
- **Image Extraction:** Physically drops embedded binary image files into an adjacent `/assets` directory and smoothly links them inline inside the `.md` stream.
- **Native OCR Fallback:** Detects scanned pages natively. Bypasses heavy dependencies like Poppler by using PyMuPDF to render raw high-res pixmaps directly in memory, feeding them into PyTesseract for Optical Character Recognition.
- **NLP Sentence Healing:** Implements lightweight spaCy Machine Learning Sentence Boundary Detection to intelligently repair the awkward, artificial line breaks caused by standard PDF right-margin wraparounds.

## ⚙️ How the Engine Works (The Pipeline)

The system is separated into a 5-part data mining pipeline that communicates seamlessly with the Electron/React frontend:

1. **Input & IPC Initialization (`desktop-app`):** The user drags a PDF into the React UI. The Electron backend safely extracts the native OS file path and spawns the compiled Python binary (`pdf2md.exe`) via `child_process.spawn()`, passing the input and output paths as arguments.
2. **Geographic Mining (`extractor.py` & `table_extractor.py`):** The Python engine drops into PyMuPDF to extract raw geometries, fonts, inline flags, span widths, and heuristic line-gaps. Simultaneously, `pdfplumber` scans the exact same coordinates to detect tabular grids. Any text detected inside a table's bounding box is aggressively pruned from the paragraph stream to prevent duplicates.
3. **Semantic Parsing (`parser.py`):** The engine analyzes document-wide font frequencies to isolate structural building blocks natively. It dynamically maps font sizes to determine `H1` and `H2` hierarchies without relying on hardcoded pixel thresholds.
4. **Optical Character Recognition (`ocr.py`):** If a page returns 0 text blocks, the engine assumes it is a scanned image. It bypasses heavy dependencies like Poppler by using PyMuPDF to render raw high-res pixmaps directly in memory, feeding them into PyTesseract for on-the-fly Optical Character Recognition.
5. **NLP Assembly (`assembler.py`):** The final stage sorts all data chronologically from top to bottom based on physical Y-coordinates. It applies `spaCy` NLP sentence healing to fix broken paragraph strings, writes extracted binary image data to disk, wraps everything in standard GitHub-flavored Markdown, and streams a success signal back to the React UI!

## 🚀 Installation & Setup

### For End Users
Simply download the **Portable Application** from the [GitHub Releases](../../releases) page!
1. Download the `PDF-to-Markdown-win32-x64.zip` file.
2. Extract the folder anywhere on your computer.
3. Double-click `PDF to Markdown.exe` to launch the app!

### For Developers

If you wish to modify the UI or the underlying Python engine, you will need Node.js and Python installed.

#### 1. Clone & Setup Python Engine
```bash
git clone https://github.com/Mostofa-Hasin-Mahdi/pdf2markdown.git
cd pdf2markdown

# Create and activate a Virtual Environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

# Install Python Dependencies and NLP Models
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

#### 2. Setup Desktop UI
```bash
cd desktop-app
npm install
```

#### 3. Run Development Server
This will start both the Next.js development server and the Electron shell simultaneously!
```bash
npm run electron:dev
```

#### 4. Package for Release
To generate the final standalone `.exe` folder (PyInstaller will first compile the python engine, then Electron-Builder will package the UI):
```bash
# Inside the root folder, freeze the Python script:
.\venv\Scripts\pyinstaller.exe -y --name pdf2md --onefile --collect-data en_core_web_sm --hidden-import spacy --hidden-import tabulate --copy-metadata tabulate pdf2md.py

# Inside the desktop-app folder, package the Desktop App:
cd desktop-app
npm run electron:build
```
Your final compiled application will be waiting inside `desktop-app/release/win-unpacked/`!

---

## 🧠 Project Architecture

For educational purposes, the engine is separated into a robust IPC-bridged architecture:
1. **Frontend (`desktop-app/src/app`):** A statically exported Next.js React application styled with TailwindCSS.
2. **IPC Bridge (`desktop-app/preload.js`):** Securely intercepts Next.js UI interactions and passes them to the Node.js backend.
3. **Electron Backend (`desktop-app/main.js`):** Manages native OS file dialogs and dynamically spawns the compiled Python `pdf2md.exe` binary.
4. **Python Engine (`engine/`):** The 5-part data mining pipeline that chronologically scrapes text, detects geographic tables, parses semantic fonts, runs PyTesseract OCR, and applies NLP sentence healing.
