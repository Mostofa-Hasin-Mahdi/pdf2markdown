# PDF to Markdown Converter

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![spaCy](https://img.shields.io/badge/spaCy-09A3D5.svg?style=for-the-badge&logo=spacy&logoColor=white)
![Tesseract OCR](https://img.shields.io/badge/Tesseract_OCR-black?style=for-the-badge)

A highly modular, robust, and 100% free **CPU-bound PDF to Markdown Conversion Engine** built in Python.

This tool is designed to accurately extract structural content from PDFs—including semantic headings, tables, bulleted lists, inline formatting, images, and raw text—and assemble it perfectly into GitHub-flavored Markdown. It intelligently bypasses the common pitfalls of PDF parsing (like randomly broken sentences and fractured tables) using a combination of geographic bounding box analysis and Natural Language Processing.

## ✨ Key Features

- **Semantic Heading Detection:** Mathematically calculates the document's base font size and scales headers (`#`, `##`) dynamically based on mathematical ratios.
- **Flawless Tables:** Geometrically detects table grids using `pdfplumber`, extracts them via Pandas DataFrames, and prints them as perfectly aligned Markdown tables.
- **Spatial Deduplication & Sorting:** Tracks the exact `(x,y)` coordinates of every paragraph, table, and image. It actively prunes duplicate text hidden inside table bounds and chronologically sorts elements from top to bottom.
- **Advanced List Parsing:** Utilizes "Early Termination" geometric heuristics to separate paragraphs and list items, bypassing the need to rely on invisible or unicode bullet characters.
- **Inline Formatting Support:** Dives into PyMuPDF span-level bitmask flags to wrap text in **Bold**, *Italic*, `Monospace`, and <sup>Superscript</sup> markers cleanly.
- **Image Extraction:** Physically drops embedded binary image files into an adjacent `/assets` directory and smoothly links them inline inside the `.md` stream.
- **Native OCR Fallback:** Detects scanned pages (0 text blocks) natively. Bypasses heavy dependencies like Poppler by using PyMuPDF to render raw high-res pixmaps directly in memory, feeding them into PyTesseract for on-the-fly optical character recognition.
- **NLP Sentence Healing:** Implements lightweight spaCy Sentence Boundary Detection to intelligently repair the awkward, artificial line breaks caused by standard PDF right-margin wraparounds.

## 🛠️ Technology Stack

100% Free and Open Source. No Paid APIs.
- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)** - Raw text extraction, geometric bounding boxes, and image bit rendering.
- **[pdfplumber](https://github.com/jsvine/pdfplumber)** - Robust tabular grid detection.
- **[Pandas](https://pandas.pydata.org/) & [Tabulate](https://pypi.org/project/tabulate/)** - DataFrame formatting into GitHub Markdown.
- **[spaCy](https://spacy.io/)** - Linguistic boundary detection for text cleanup.
- **[PyTesseract](https://pypi.org/project/pytesseract/)** - OCR Engine fallback.

---

## 🚀 Installation & Setup

### 1. Prerequisites
If you plan to use this on older, scanned PDFs (that are purely images), you must have the **Tesseract-OCR Engine** installed on your operating system.
- **Windows:** Download the installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
- **Mac:** `brew install tesseract`
- **Linux:** `sudo apt-get install tesseract-ocr`

### 2. Clone & Initialize
```bash
git clone https://github.com/Mostofa-Hasin-Mahdi/pdf2markdown.git
cd pdf2markdown

# Create and activate a Virtual Environment
python -m venv venv

# Windows Wait:
.\venv\Scripts\activate
# Mac/Linux Wait:
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Language Models
The assembler relies on spaCy's small english linguistic model to perfectly stitch broken physical lines into continuously flowing sentences.
```bash
python -m spacy download en_core_web_sm
```

---

## 💻 Usage

Run the program via the Command Line. It takes two positional arguments: the input `.pdf` and the desired output `.md` destination.

```bash
python pdf2md.py <path_to_input.pdf> <path_to_output.md>
```

**Example:**
```bash
python pdf2md.py report.pdf markdown_output/report.md
```

### Output Behavior:
- The script will dump `report.md` at the location specified.
- If it encounters images within the PDF, it will automatically generate a folder called `assets/` right next to your `report.md` file, dump the binary images there, and link them locally inside your document!

---

## 🧠 Project Architecture

For educational purposes, the engine is separated into a 5-part pipeline:
1. `pdf2md.py`: The Main Orchestrator. Handles chronological top-to-bottom geographic sorting and overlap prevention. 
2. `extractor.py`: The Data Miner. Drops into PyMuPDF to extract raw geometries, fonts, inline flags, span widths, and heuristic line-gaps.
3. `parser.py`: The Semantics Brain. Analyzes document-wide font frequencies to isolate structural building blocks natively.
4. `table_extractor.py`: The Grid Engine. Targets `pdfplumber` for strict vertical/horizontal line parsing.
5. `assembler.py`: The Output Engine. Applies spaCy NLP, controls I/O behavior, writes the raw image bits to disk, and injects clean markdown wrappers seamlessly.
