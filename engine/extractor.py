import fitz  # PyMuPDF
import os
from typing import List, Dict, Any

class PDFExtractor:
    """
    Handles the raw extraction of text, font metadata, and images from a PDF.
    We use PyMuPDF because it allows us to extract text with its visual formatting
    (like font size and style). This is the foundation for figuring out what text
    is a heading and what text is a paragraph.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        # fitz.open loads the PDF document into memory.
        self.doc = fitz.open(pdf_path)
        
    def extract_all_pages(self) -> List[Dict[str, Any]]:
        """
        Extracts structured data from all pages.
        Returns a list where each element represents a page.
        """
        pages_data = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            pages_data.append(self.extract_page_data(page))
        return pages_data

    def extract_page_data(self, page: fitz.Page) -> Dict[str, Any]:
        """
        Extracts raw building blocks from a single page.
        
        Under the hood, PyMuPDF's `get_text("dict")` returns a deeply nested dictionary:
        - A Page has 'blocks' (rough physical groupings of text/images).
        - A text block has 'lines' (physical lines on the page).
        - A line has 'spans' (fragments of text that share the exact same font/size/color).
        
        If a sentence starts normal but ends in *bold*, it will be on the same
        'line', but split into two 'spans'.
        """
        # get_text("dict") gives us the exact coordinates, font names, and sizes.
        raw_dict = page.get_text("dict")
        
        # We will parse this raw dictionary into a slightly cleaner format
        # separating text blocks from image blocks.
        page_structure = {
            "width": raw_dict["width"],
            "height": raw_dict["height"],
            "text_blocks": [],
            "image_blocks": []
        }
        
        for block in raw_dict.get("blocks", []):
            # block["type"] == 0 means it is a text block.
            if block["type"] == 0:
                page_structure["text_blocks"].append(self._parse_text_block(block))
            # block["type"] == 1 means it is an image block.
            elif block["type"] == 1:
                page_structure["image_blocks"].append(self._parse_image_block(block, page))

        # === PHASE 3: OCR FALLBACK OVERRIDE ===
        # Import dynamically to avoid circular dependencies
        from engine.ocr import OCREngine
        
        if OCREngine.is_page_scanned(page_structure):
            print(f"Scanned page detected (Page {page.number}). Engaging OCR Fallback...")
            ocr_text_blocks = OCREngine.process_page(page)
            if ocr_text_blocks:
                page_structure["text_blocks"] = ocr_text_blocks
                
        return page_structure

    def _parse_image_block(self, block: Dict[str, Any], page: fitz.Page) -> Dict[str, Any]:
        """
        Extracts information about an image.
        For now, we just save the image bounding box and raw bytes.
        We can save it to an assets folder later during assembly.
        """
        # Usually, an image block has 'image' raw bytes or an XREF we can use.
        bbox = block.get("bbox", (0,0,0,0))
        image_bytes = block.get("image", None)
        
        return {
            "bbox": bbox,
            "ext": block.get("ext", "png"), # the image extension
            "image_bytes": image_bytes
        }

    def _parse_text_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleans up a single raw text block.
        We iterate through every span to collect text and save the largest font size
        used in this block. This helps us later decide if the block is a Heading.
        """
        combined_text = ""
        max_font_size = 0
        bbox = block.get("bbox", (0,0,0,0))
        
        # We need to compute an average line gap to distinguish wrapped lines from new paragraphs
        prev_y1 = None
        prev_line_bbox = None
        
        # Regex to detect list items (bullets or numbers)
        import re
        list_pattern = r'^\s*(?:[-*•·◦➢➣✔]\s*|\d+\.\s+)'
        
        for line in block.get("lines", []):
            line_bbox = line.get("bbox", (0,0,0,0))
            
            # Combine all text spans for this line to check if it looks like a list
            line_text = "".join([span.get("text", "") for span in line.get("spans", [])]).strip()
            looks_like_list = bool(re.match(list_pattern, line_text))
            
            # If there is a noticeable vertical gap or previous line ended early, it's a paragraph break!
            if prev_y1 is not None and prev_line_bbox is not None:
                gap = line_bbox[1] - prev_y1
                
                # Check if previous line ended early
                # bbox[2] is the absolute right margin of the block.
                # If the previous line ended more than 2 font sizes away from the right margin,
                # it's highly likely to be the end of a paragraph.
                ended_early = max_font_size > 0 and prev_line_bbox[2] < (bbox[2] - max_font_size * 2)
                
                # Paragraph Break triggers:
                # 1. Large graphical gap
                # 2. Line explicitly starts with a list bullet/number
                # 3. The previous line ended early (did not hit the right margin)
                if (max_font_size > 0 and gap > (max_font_size * 0.2)) or looks_like_list or ended_early:
                    combined_text += "\n" # Insert an extra newline to create a \n\n split
            
            for span in line.get("spans", []):
                text = span.get("text", "")
                font_size = span.get("size", 0)
                font_name = span.get("font", "").lower()
                flags = span.get("flags", 0)
                
                # Check formatting flags 
                # PyMuPDF Bitmask: 1: superscript, 2: italic, 8: monospaced, 16: bold
                is_bold = "bold" in font_name or (flags & 16)
                is_italic = "italic" in font_name or "oblique" in font_name or (flags & 2)
                is_mono = "mono" in font_name or "courier" in font_name or "console" in font_name or (flags & 8)
                is_super = flags & 1
                
                # Apply inline formatting cleanly (keep spaces outside the asterisks so MD renders it properly)
                if text.strip() and (is_bold or is_italic or is_mono or is_super):
                    leading = text[:len(text) - len(text.lstrip())]
                    trailing = text[len(text.rstrip()):]
                    core = text.strip()
                    
                    if is_bold and is_italic:
                        core = f"***{core}***"
                    elif is_bold:
                        core = f"**{core}**"
                    elif is_italic:
                        core = f"*{core}*"
                        
                    if is_mono:
                        core = f"`{core}`"
                    if is_super:
                        core = f"<sup>{core}</sup>"
                        
                    text = f"{leading}{core}{trailing}"
                
                # Append the text fragment
                combined_text += text
                
                # Keep track of the largest font size in this block
                if font_size > max_font_size:
                    max_font_size = font_size
            
            # Reconstruct physical lines by adding newlines
            combined_text += "\n"
            prev_y1 = line_bbox[3] # bottom y-coordinate of the current line
            prev_line_bbox = line_bbox
                
        return {
            "text": combined_text.strip(),
            "max_font_size": round(max_font_size, 2), # Round to avoid float precision issues
            "bbox": bbox
        }

    def close(self):
        """Always close the document to free up memory."""
        self.doc.close()
