import os
import sys
import time

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import fitz
from concurrent.futures import ProcessPoolExecutor
from rapidocr_onnxruntime import RapidOCR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXP_PDF = r"D:\Users\zjw\Study\桌面考研与学习资料\政治1000题\2027--1000题--解析册.pdf"
EXP_OUT_DIR = os.path.join(BASE_DIR, "rapid_1000_exp")
os.makedirs(EXP_OUT_DIR, exist_ok=True)

_worker_ocr = None
_worker_docs = {}

def init_worker():
    global _worker_ocr
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    _worker_ocr = RapidOCR()

def ocr_single_page(args):
    global _worker_ocr, _worker_docs
    pdf_path, page_idx, out_path = args
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50:
        return page_idx, "skipped"
    
    try:
        if pdf_path not in _worker_docs:
            _worker_docs[pdf_path] = fitz.open(pdf_path)
        doc = _worker_docs[pdf_path]
        
        pix = doc[page_idx].get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        res, _ = _worker_ocr(img_bytes)
        
        lines = []
        if res:
            for item in res:
                line_text = item[1].strip()
                if line_text:
                    lines.append(line_text)
                    
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        return page_idx, f"done ({len(lines)} lines)"
    except Exception as e:
        return page_idx, f"error: {e}"

def main():
    cpu_cores = os.cpu_count() or 4
    max_workers = 8
    print(f"[EXP OCR] 启动解析册专用 OCR: 分配 {max_workers} 个并行 worker", flush=True)
    
    doc_exp = fitz.open(EXP_PDF)
    total_exp_pages = len(doc_exp)
    exp_tasks = []
    for p in range(2, total_exp_pages):
        out_f = os.path.join(EXP_OUT_DIR, f"page_{p+1:03d}.txt")
        exp_tasks.append((EXP_PDF, p, out_f))
        
    print(f"[EXP OCR] 解析任务总计 {len(exp_tasks)} 页", flush=True)
    
    t0 = time.time()
    completed = 0
    with ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker) as executor:
        for p_idx, status in executor.map(ocr_single_page, exp_tasks):
            completed += 1
            if completed % 10 == 0 or completed == len(exp_tasks):
                elapsed = time.time() - t0
                speed = completed / elapsed if elapsed > 0 else 0
                remaining = (len(exp_tasks) - completed) / speed if speed > 0 else 0
                print(f"[EXP OCR] [{completed}/{len(exp_tasks)}] 进度 {completed*100/len(exp_tasks):.1f}% | 速度: {speed:.1f}页/秒 | 预估剩余: {remaining:.0f}秒", flush=True)
                
    print(f"🎉 全部解析册 OCR 完成！总用时: {time.time()-t0:.1f}秒", flush=True)

if __name__ == "__main__":
    main()
