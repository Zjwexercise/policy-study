import fitz
import re
import os
import sys

doc = fitz.open('pdf/27《优题库》 - 压缩版/27《优题库》 - 压缩版/（已压缩）27《优题库-试题拔高篇》.pdf')
print("Pages in 试题拔高篇:", len(doc))

# Let's check how many questions on Page 6 are found with the old regex vs new regex
from import_youtiku_all import ocr_page

temp_img = "backend/sample_page.png"
p6_text = ocr_page(doc, 5, temp_img) # Page 6
if os.path.exists(temp_img):
    os.remove(temp_img)

print("=== Page 6 Old Regex ===")
old_pat = re.compile(r'\n(?=\s*\d{1,2}\s*[\.、．]\s*[\u4e00-\u9fa5“\"\'《])')
old_chunks = old_pat.split(p6_text)
print("Old chunks count:", len(old_chunks))
for c in old_chunks:
    m = re.match(r'^\s*(\d{1,2})\s*[\.、．]\s*([\s\S]+)', c.strip())
    if m:
        print("  Found Q", m.group(1))

print("\n=== Page 6 New Regex (allowing · and spaces and other separators) ===")
new_pat = re.compile(r'\n(?=\s*\d{1,2}\s*[·\.、．，,:\s]\s*[\u4e00-\u9fa5“\"\'《])')
new_chunks = new_pat.split(p6_text)
print("New chunks count:", len(new_chunks))
for c in new_chunks:
    m = re.match(r'^\s*(\d{1,2})\s*[·\.、．，,:\s]\s*([\s\S]+)', c.strip())
    if m:
        print("  Found Q", m.group(1))
