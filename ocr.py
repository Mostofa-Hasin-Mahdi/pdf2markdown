import io
import fitz
from typing import Dict, Any, List

try:
    from PIL import Image
    import pytesseract
    # Note: On Windows, pytesseract might need the explicit path to the tesseract executable
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
except Exception:
    TESSERACT_AVAILABLE = False


class OCREngine:
    """
    Handles Optical Character Recognition (OCR) fallback for scanned pages.
    Instead of using pdf2image (which requires Poppler, a heavy C++ library),
    we use PyMuPDF to render the page to an image, and then pass it to PyTesseract.
    """
    
    @staticmethod
    def is_page_scanned(page_data: Dict[str, Any]) -> bool:
        """
        Heuristic to determine if a page needs OCR.
        If a page has 0 text blocks, but has an image covering most of the page,
        it is likely a scanned document.
        """
        text_blocks = page_data.get("text_blocks", [])
        if len(text_blocks) == 0:
            return True
            
        # Sometimes scanned PDFs have a tiny watermark text block but the rest is scanned
        # If total text length is abnormally small (e.g. < 20 chars), we might want to OCR.
        total_text_len = sum(len(b.get("text", "")) for b in text_blocks)
        if total_text_len < 20 and len(page_data.get("image_blocks", [])) > 0:
            return True
            
        return False

    @staticmethod
    def process_page(page: fitz.Page) -> List[Dict[str, Any]]:
        """
        Takes a PyMuPDF page, renders it to an image, runs OCR, 
        and formats the output to match our standard text_block structure.
        """
        if not TESSERACT_AVAILABLE:
            print("WARNING: PyTesseract or PIL is not installed/configured properly.")
            print("Cannot perform OCR on scanned page. Skipping.")
            return []

        try:
            # Render the PDF page to a high-resolution image (Matrix(2, 2) is ~144 DPI)
            zoom = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=zoom)
            
            # Convert PyMuPDF Pixmap to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Run pytesseract
            # Get verbose data including bounding boxes (x,y,w,h)
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            return OCREngine._parse_tesseract_data(ocr_data, zoom_scale=2.0)
        except pytesseract.TesseractNotFoundError:
            print("WARNING: Tesseract executable not found. OCR cannot run.")
            print("Please install Tesseract-OCR on your system for scanned PDFs.")
            return []
        except Exception as e:
            print(f"ERROR during OCR processing: {e}")
            return []

    @staticmethod
    def _parse_tesseract_data(ocr_data: Dict[str, list], zoom_scale: float) -> List[Dict[str, Any]]:
        """
        Converts Tesseract output into our standard `text_blocks` format.
        Since Tesseract doesn't give us font sizes reliably, we mock a default size.
        """
        text_blocks = []
        n_boxes = len(ocr_data['text'])
        
        current_block_text = []
        current_bbox = None
        
        # Tesseract outputs word by word. We group them into basic blocks based on 'block_num'
        current_block_num = -1
        
        for i in range(n_boxes):
            # level 5 = word. We only care about actual words with high confidence.
            if int(ocr_data['conf'][i]) > 30 and ocr_data['text'][i].strip():
                block_num = ocr_data['block_num'][i]
                text = ocr_data['text'][i]
                
                # Scale coordinates back down to match standard PDF dimensions
                x0 = ocr_data['left'][i] / zoom_scale
                y0 = ocr_data['top'][i] / zoom_scale
                w = ocr_data['width'][i] / zoom_scale
                h = ocr_data['height'][i] / zoom_scale
                bbox = (x0, y0, x0+w, y0+h)
                
                if block_num != current_block_num:
                    # Save old block
                    if current_block_text:
                        text_blocks.append({
                            "text": " ".join(current_block_text),
                            "max_font_size": 12.0, # Default body font size (we lack real data)
                            "bbox": current_bbox
                        })
                    
                    # Start new block
                    current_block_num = block_num
                    current_block_text = [text]
                    current_bbox = bbox
                else:
                    # Append to current block
                    current_block_text.append(text)
                    # Expand bounding box
                    old_x0, old_y0, old_x1, old_y1 = current_bbox
                    current_bbox = (
                        min(old_x0, bbox[0]),
                        min(old_y0, bbox[1]),
                        max(old_x1, bbox[2]),
                        max(old_y1, bbox[3])
                    )
        
        # Append the final block
        if current_block_text:
            text_blocks.append({
                "text": " ".join(current_block_text),
                "max_font_size": 12.0,
                "bbox": current_bbox
            })
            
        return text_blocks
