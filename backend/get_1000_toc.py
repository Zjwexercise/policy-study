import fitz
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

for name in ['pdf/2027--1000题--试题册.pdf', 'pdf/2027--1000题--解析册.pdf']:
    if os.path.exists(name):
        doc = fitz.open(name)
        print(f"\n=== {name} (total pages: {len(doc)}) ===")
        toc = doc.get_toc()
        if toc:
            for item in toc:
                print(item)
        else:
            print("No bookmark outline found")
    else:
        print("Not found:", name)
