import fitz
import sys

doc = fitz.open("test/test.pdf")
page = doc[0]
raw_dict = page.get_text("dict")

with open("debug.txt", "w") as f:
    f.write(f"Total blocks: {len(raw_dict.get('blocks', []))}\n")
    for i, b in enumerate(raw_dict.get('blocks', [])):
        if b['type'] == 0:
            f.write(f"BLOCK {i}\n")
            prev_y1 = None
            for l in b['lines']:
                y0 = l['bbox'][1]
                y1 = l['bbox'][3]
                text = ''.join(s['text'] for s in l['spans'])[:40]
                if prev_y1 is not None:
                    gap = y0 - prev_y1
                    f.write(f"  Gap: {gap:.2f} | text: {text}\n")
                else:
                    f.write(f"  START       | text: {text}\n")
                prev_y1 = y1
