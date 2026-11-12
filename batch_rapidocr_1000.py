import os
import sys
import time

# 核心关键：必须在导入任何 numpy / onnxruntime / torch 前设置单线程环境变量，杜绝 128 线程争抢 CPU 缓存
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import fitz
from concurrent.futures import ProcessPoolExecutor
from rapidocr_onnxruntime import RapidOCR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
Q_PDF = r"D:\Users\zjw\Study\桌面考研与学习资料\政治1000题\2027--1000题--试题册.pdf"
EXP_PDF = r"D:\Users\zjw\Study\桌面考研与学习资料\政治1000题\2027--1000题--解析册.pdf"

Q_OUT_DIR = os.path.join(BASE_DIR, "rapid_1000_q")
EXP_OUT_DIR = os.path.join(BASE_DIR, "rapid_1000_exp")

os.makedirs(Q_OUT_DIR, exist_ok=True)
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
    max_workers = 8  # 8 个单线程 worker 跑在 16 核 CPU 上，兼顾极速与系统流畅
    print(f"检测到 {cpu_cores} 核心 CPU，分配 {max_workers} 个并行常驻 OCR 工作进程（已设 OMP_NUM_THREADS=1）！", flush=True)
    
    # 试题任务：第 3 页到最后一页（0-indexed：3对应Page 4）
    doc_q = fitz.open(Q_PDF)
    total_q_pages = len(doc_q)
    q_tasks = []
    for p in range(3, total_q_pages):
        out_f = os.path.join(Q_OUT_DIR, f"page_{p+1:03d}.txt")
        q_tasks.append((Q_PDF, p, out_f))
        
    # 解析任务：第 2 页到最后一页（0-indexed：2对应Page 3）
    doc_exp = fitz.open(EXP_PDF)
    total_exp_pages = len(doc_exp)
    exp_tasks = []
    for p in range(2, total_exp_pages):
        out_f = os.path.join(EXP_OUT_DIR, f"page_{p+1:03d}.txt")
        exp_tasks.append((EXP_PDF, p, out_f))
        
    all_tasks = q_tasks + exp_tasks
    print(f"总计任务: 试题 {len(q_tasks)} 页 + 解析 {len(exp_tasks)} 页 = 共 {len(all_tasks)} 页", flush=True)
    
    t0 = time.time()
    completed = 0
    with ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker) as executor:
        for p_idx, status in executor.map(ocr_single_page, all_tasks):
            completed += 1
            if completed % 10 == 0 or completed == len(all_tasks):
                elapsed = time.time() - t0
                speed = completed / elapsed if elapsed > 0 else 0
                remaining = (len(all_tasks) - completed) / speed if speed > 0 else 0
                print(f"[{completed}/{len(all_tasks)}] 进度 {completed*100/len(all_tasks):.1f}% | 速度: {speed:.1f}页/秒 | 预估剩余: {remaining:.0f}秒", flush=True)
                
    print(f"🎉 全部 1000 题页面 OCR 完成！总用时: {time.time()-t0:.1f}秒", flush=True)

if __name__ == "__main__":
    main()
