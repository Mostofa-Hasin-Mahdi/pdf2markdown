import pdfplumber
import pandas as pd
from typing import List, Dict, Any

class TableExtractor:
    """
    Handles extracting tables from PDFs using pdfplumber, 
    and converting them into formatted Markdown tables via Pandas.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_tables(self) -> Dict[int, List[Dict[str, Any]]]:
        """
        Extracts tables from all pages.
        Returns a dictionary mapping page numbers (0-indexed) to a list of table blocks.
        """
        tables_by_page = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # find_tables gives us bounding box data
                # extract_tables gives us exactly the string rows
                found_tables = page.find_tables()
                if not found_tables:
                    continue
                    
                tables_by_page[page_num] = []
                
                for table in found_tables:
                    # Extract the actual text grid from the table object
                    grid = table.extract()
                    if not grid:
                        continue
                        
                    # We assume the first row is the header
                    # Clean out None values and replace newlines.
                    # CRITICAL: We MUST escape pipe characters (|) so Markdown doesn't think it's a new column!
                    cleaned_grid = [
                        ["" if cell is None else str(cell).replace('\n', ' ').replace('|', '&#124;') for cell in row] 
                        for row in grid
                    ]
                    
                    if len(cleaned_grid) > 1:
                        df = pd.DataFrame(cleaned_grid[1:], columns=cleaned_grid[0])
                    else:
                        # Table only has one row, dummy header
                        df = pd.DataFrame(cleaned_grid)
                        
                    # Convert to Markdown string using tabulate backend
                    md_table = df.to_markdown(index=False)
                    
                    # Store as a block mimicking our semantic blocks
                    tables_by_page[page_num].append({
                        "semantic_type": "table",
                        "text": md_table,
                        "prefix": "",
                        "bbox": table.bbox # (x0, top, x1, bottom)
                    })
                    
        return tables_by_page
