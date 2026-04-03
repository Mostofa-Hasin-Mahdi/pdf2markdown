from typing import List, Dict, Any
from collections import Counter
import re

class SemanticParser:
    """
    Takes the raw structurally-dumb text blocks from the Extractor
    and applies heuristics to figure out what they actually mean 
    (Headings, Paragraphs, Lists).
    """
    
    def __init__(self, pages_data: List[Dict[str, Any]]):
        self.pages_data = pages_data
        self.base_font_size = self._calculate_base_font_size()

    def _calculate_base_font_size(self) -> float:
        """
        Scans every text block across the entire document to find the most 
        frequently used font size. This is assumed to be the "body" text size.
        """
        all_sizes = []
        for page in self.pages_data:
            for block in page.get("text_blocks", []):
                # Ignore empty blocks
                if block.get("text", "").strip():
                    # We might have multiple blocks with the same size. 
                    # We weight the frequency by the length of the text.
                    # A massive paragraph of size 11 should count more than a tiny size 11 block.
                    weight = len(block.get("text", "")) // 10 + 1
                    all_sizes.extend([block.get("max_font_size", 12.0)] * weight)
                    
        if not all_sizes:
            return 12.0 # Standard fallback
            
        # The most common font size by text volume
        most_common_size = Counter(all_sizes).most_common(1)[0][0]
        print(f"Calculated Document Base Font Size: {most_common_size}pt")
        return most_common_size

    def parse(self) -> List[Dict[str, Any]]:
        """
        Runs the heuristic engine on every page.
        Returns the data with new 'semantic_type' labels attached to each block.
        """
        parsed_pages = []
        
        for page in self.pages_data:
            parsed_blocks = []
            
            for block in page.get("text_blocks", []):
                text = block.get("text", "").strip()
                if not text:
                    continue
                    
                font_size = block.get("max_font_size", 12.0)
                semantic_type = "paragraph" # default
                prefix = ""
                
                # HEURISTIC 1: Headings
                # If the font size is substantially larger than the body text
                if font_size >= self.base_font_size * 1.4:
                    semantic_type = "h1"
                    prefix = "# "
                elif font_size >= self.base_font_size * 1.15:
                    semantic_type = "h2"
                    prefix = "## "
                    
                # HEURISTIC 2: Lists
                # If the block wasn't a heading, check if it looks like a list
                elif self._is_list_item(text):
                    semantic_type = "list_item"
                    # We don't need a markdown prefix because it likely already has 
                    # its bullet point or number from the extraction.
                    # We might want to normalize bullets though.
                    text = self._normalize_bullet(text)
                
                parsed_blocks.append({
                    "semantic_type": semantic_type,
                    "text": text,
                    "prefix": prefix,
                    "bbox": block.get("bbox")
                })
                
            # Bring image blocks into the semantic stream so they can be sorted later!
            for img_block in page.get("image_blocks", []):
                parsed_blocks.append({
                    "semantic_type": "image",
                    "prefix": "",
                    "text": "", # Images natively have no text
                    "image_bytes": img_block.get("image_bytes"),
                    "ext": img_block.get("ext", "png"),
                    "bbox": img_block.get("bbox")
                })
                
            page["parsed_blocks"] = parsed_blocks
            parsed_pages.append(page)
            
        return parsed_pages

    def _is_list_item(self, text: str) -> bool:
        """
        Checks if the text string begins with standard list indicators.
        """
        # Matches expanded unicode bullets, hyphens, stars, or numbers
        list_pattern = r'^\s*(?:[-*•·◦➢➣✔]\s*|\d+\.\s+)'
        return bool(re.match(list_pattern, text))
        
    def _normalize_bullet(self, text: str) -> str:
        """
        Ensures weird PDF bullets (like • or  ) are converted to standard markdown (-).
        Leaves numbered lists alone.
        """
        return re.sub(r'^\s*[•·◦➢➣✔]\s*', '- ', text)
