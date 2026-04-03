import re
from typing import List, Dict, Any

try:
    import spacy
    # Load the small english model for sentence boundary detection
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    print("WARNING: spaCy or 'en_core_web_sm' model not found. Proceeding with basic regex cleanup.")
    print("To enable advanced NLP cleanup, run: python -m spacy download en_core_web_sm")

class MarkdownAssembler:
    """
    Takes the semantically parsed blocks and assembles them into the final
    Markdown document. It also performs NLP cleanup to fix arbitrary line breaks
    caused by PDF chunking.
    """
    
    def __init__(self, parsed_pages: List[Dict[str, Any]]):
        self.parsed_pages = parsed_pages
        
    def _cleanup_text(self, text: str, semantic_type: str) -> str:
        """
        Fixes the broken physical lines of a PDF into proper continuous sentences.
        """
        # Headings and lists usually don't need heavy sentence restructuring.
        if semantic_type in ["h1", "h2", "list_item"]:
            return text.replace('\n', ' ').strip()
            
        # Tables must be strictly preserved exactly as output by Pandas!
        if semantic_type == "table":
            return text
            
        # For paragraphs, we need to protect explicit paragraph breaks (\n\n) 
        # that we injected in the extractor.
        paragraphs = text.split('\n\n')
        clean_paragraphs = []
        
        for p in paragraphs:
            # 1. Remove hyphenated word breaks (e.g. "intelli-\ngent" -> "intelligent")
            p = re.sub(r'-\n\s*', '', p)
            
            if SPACY_AVAILABLE:
                # 2. Heuristically replace single newlines with spaces
                p = p.replace('\n', ' ')
                
                # 3. Let spaCy ensure the sentence boundaries make sense
                doc = nlp(p)
                sentences = [sent.text.strip() for sent in doc.sents]
                clean_paragraphs.append(" ".join(sentences))
            else:
                # Fallback if spaCy isn't installed
                p = re.sub(r'(?<![.\?!])\n', ' ', p)
                p = p.replace('\n', ' ')
                p = re.sub(r'\s+', ' ', p).strip()
                clean_paragraphs.append(p)

        # Rejoin the distinct paragraphs within the block using double newlines
        return "\n\n".join(clean_paragraphs)

    def assemble(self, output_path: str):
        """
        Assembles the text and writes it to the hard drive.
        """
        import os
        output_dir = os.path.dirname(os.path.abspath(output_path))
        assets_dir = os.path.join(output_dir, "assets")
        
        final_markdown = []
        img_counter = 1
        
        for page in self.parsed_pages:
            # We can optionally add a theoretical page break delimiter like "---" 
            # But standard markdown doesn't have pages. We'll just append continuously.
            
            for block in page.get("parsed_blocks", []):
                semantic_type = block.get("semantic_type")
                
                # --- NEW IMAGE LOGIC ---
                if semantic_type == "image":
                    if not os.path.exists(assets_dir):
                        os.makedirs(assets_dir)
                    
                    ext = block.get("ext", "png")
                    img_name = f"image_{img_counter}.{ext}"
                    img_path = os.path.join(assets_dir, img_name)
                    
                    # Physically write the binary image data to the assets folder
                    img_bytes = block.get("image_bytes")
                    if img_bytes:
                        with open(img_path, "wb") as f:
                            f.write(img_bytes)
                            
                    # Inject the Markdown Link into the layout stream
                    final_markdown.append(f"![Image](assets/{img_name})")
                    img_counter += 1
                    continue
                
                raw_text = block.get("text")
                prefix = block.get("prefix", "")
                
                # Clean up the arbitrary PDF line breaks
                clean_text = self._cleanup_text(raw_text, semantic_type)
                
                # Assemble the markdown chunk
                md_chunk = f"{prefix}{clean_text}"
                final_markdown.append(md_chunk)
            
        # Write to the file!
        with open(output_path, 'w', encoding='utf-8') as f:
            # Join everything with double newlines so markdown renders paragraphs properly
            f.write("\n\n".join(final_markdown))
        
        print(f"Successfully wrote Markdown output to: {output_path}")
