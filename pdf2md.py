import argparse
import os
import sys
from engine.extractor import PDFExtractor

def validate_pdf_path(path: str) -> str:
    """Validates that the provided path exists, is a file, and is a PDF."""
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist.")
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"Path '{path}' is not a file.")
    if not path.lower().endswith('.pdf'):
        raise argparse.ArgumentTypeError(f"File '{path}' is not a PDF (.pdf).")
    return path

def validate_output_path(path: str) -> str:
    """Validates the output path structure."""
    if not path.lower().endswith('.md'):
        raise argparse.ArgumentTypeError(f"Output file '{path}' must have a .md extension.")
    
    # Check if the output directory is valid
    output_dir = os.path.dirname(path)
    if output_dir and not os.path.exists(output_dir):
        raise argparse.ArgumentTypeError(f"Output directory '{output_dir}' does not exist.")
    return path

def setup_cli() -> argparse.ArgumentParser:
    """Creates and returns the argparse parser with our arguments."""
    parser = argparse.ArgumentParser(
        description="CPU-based PDF to Markdown Converter",
        epilog="Converts a PDF file into structured Markdown, extracting text, headings, and tables."
    )
    
    parser.add_argument(
        "input",
        type=validate_pdf_path,
        help="Path to the input PDF file."
    )
    
    parser.add_argument(
        "output",
        type=validate_output_path,
        help="Path where the output Markdown file will be saved. Needs to be a .md file."
    )
    
    return parser

def main():
    parser = setup_cli()
    args = parser.parse_args()
    
    print(f"Validated Input PDF: {args.input}")
    print(f"Validated Output Path: {args.output}")
    print("Beginning extraction phase...")
    
    # Initialize the extractor
    extractor = PDFExtractor(args.input)
    
    # Extract all the data (Phase 2 & 3)
    pages_data = extractor.extract_all_pages()
    extractor.close()
    
    print(f"Successfully extracted data from {len(pages_data)} pages!")
    
    # === PHASE 4: SEMANTIC PARSING ===
    from engine.parser import SemanticParser
    print("Beginning semantic parsing...")
    
    semantic_parser = SemanticParser(pages_data)
    parsed_pages = semantic_parser.parse()
    
    print("Successfully mapped blocks to Headings and Paragraphs!")
    
    # === PHASE 5: TABLE EXTRACTION ===
    from engine.table_extractor import TableExtractor
    print("Extracting tables using pdfplumber...")
    
    tb_extractor = TableExtractor(args.input)
    page_tables = tb_extractor.extract_tables()
    
    # Merge tables into the parsed pages and sort them chronologically
    for page_num, page in enumerate(parsed_pages):
        table_bboxes = []
        
        # Identify the physical tables for this page
        if page_num in page_tables:
            page["parsed_blocks"].extend(page_tables[page_num])
            table_bboxes = [t["bbox"] for t in page_tables[page_num]]
            
        # Pruning Pass: PyMuPDF extracts table text as raw text blocks.
        # We need to delete any text block that physically overlaps with a pdfplumber table
        # so that we don't print the contents of the table twice!
        filtered_blocks = []
        for b in page["parsed_blocks"]:
            if b.get("semantic_type") == "table":
                filtered_blocks.append(b)
                continue
                
            block_bbox = b.get("bbox")
            if not block_bbox or block_bbox == (0,0,0,0):
                filtered_blocks.append(b)
                continue
                
            x0, y0, x1, y1 = block_bbox
            # Use the center point of the text block to check if it's inside a table
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            
            is_inside_table = False
            for (tx0, ty0, tx1, ty1) in table_bboxes:
                if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                    is_inside_table = True
                    break
                    
            if not is_inside_table:
                filtered_blocks.append(b)
                
        page["parsed_blocks"] = filtered_blocks
            
        # Sort all elements Top-to-Bottom based on the Top Y-coordinate (bbox[1])
        # This guarantees that tables are printed exactly where they appeared physically relative to text
        page["parsed_blocks"].sort(key=lambda b: b.get("bbox", (0,0,0,0))[1])
        
    print(f"Successfully extracted tabular grids into DataFrames!")
    
    # === PHASE 6: ASSEMBLY AND OUTPUT ===
    # (Doing this slightly out of order so you can see the result!)
    from engine.assembler import MarkdownAssembler
    print("Assembling Markdown and cleaning up line breaks...")
    
    assembler = MarkdownAssembler(parsed_pages)
    assembler.assemble(args.output)
    
    print("Conversion Complete!")
    
if __name__ == "__main__":
    main()
