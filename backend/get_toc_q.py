import fitz, subprocess, os, sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

temp_img = 'backend/temp_toc.png'
ocr_script = 'backend/ocr_test.ps1'
pdf_path = os.path.join('pdf', '27《优题库》 - 压缩版', '27《优题库》 - 压缩版', '（已压缩）27《优题库-试题拔高篇》.pdf')
doc = fitz.open(pdf_path)

for p in [1, 2, 3, 4, 5]:
    pix = doc[p].get_pixmap(dpi=140)
    pix.save(temp_img)
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ocr_script, '-ImagePath', temp_img]
    res = subprocess.run(cmd, capture_output=True)
    out = res.stdout.decode('utf-8', errors='ignore')
    print(f'=== Page {p+1} ===')
    for line in out.splitlines():
        if line.strip():
            print('  ', line.strip())

if os.path.exists(temp_img):
    os.remove(temp_img)
