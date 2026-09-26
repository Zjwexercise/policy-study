import os
import sys
import re
import json
import sqlite3

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")
Q_TXT_DIR = os.path.join(BASE_DIR, "backend", "1000_q_txt")
EXP_TXT_DIR = os.path.join(BASE_DIR, "backend", "1000_exp_txt")

# 1000题 5 大模块的页面范围
MODULES = [
    {"part": "马原", "q_range": (4, 67), "exp_range": (3, 69)},
    {"part": "毛中特", "q_range": (67, 89), "exp_range": (69, 93)},
    {"part": "习思想", "q_range": (89, 125), "exp_range": (93, 128)},
    {"part": "史纲", "q_range": (125, 176), "exp_range": (128, 181)},
    {"part": "思修", "q_range": (176, 205), "exp_range": (181, 204)},
]

def clean_ocr(text):
    text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    return text

def extract_module_explanations(start_p, end_p):
    """从解析册页面范围提取所有题目的答案与解析"""
    raw_text = ""
    for p in range(start_p, end_p + 1):
        f = os.path.join(EXP_TXT_DIR, f"page_{p:03d}.txt")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8-sig") as fp:
                raw_text += f"\n=== Page {p} ===\n" + fp.read()

    cleaned = clean_ocr(raw_text)

    # 识别解析块：以答案为核心
    # 模式形如： 
    # 1. 答案 B 〖解析〗...
    # 答案 B 〖解析〗...
    # 3 . 爷案 A 〖解析〗...
    # [A-D]+ 〖解析〗...
    blocks = re.split(r'\n(?=(?:\d{1,3}\s*[\.、．·:：]?\s*)?(?:答\s*案|答案|爷\s*案|[A-D]{1,4}\s*〖\s*解析))', cleaned)

    exps = []
    for b in blocks:
        b = b.strip()
        if not b or '解析' not in b:
            continue
        m_ans = re.search(r'(?:(\d{1,3})\s*[\.、．·:：\s]*)?(?:答\s*案|答案|爷\s*案|案|」)?\s*[:：\(<〖\s]*([A-Da-d]{1,4})[\)\]>〗\s]*(?:〖?\s*解析\s*〗?)([\s\S]*)', b)
        if m_ans:
            q_num_str = m_ans.group(1)
            ans = m_ans.group(2).upper()
            exp_body = m_ans.group(3).strip()
            # 清理
            exp_body = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', exp_body)
            exp_body = re.sub(r'[\s\n]+', ' ', exp_body).strip()
            if len(exp_body) > 10:
                exps.append({
                    "ans": ans,
                    "exp": f"【肖秀荣1000题名师精解】{exp_body}"
                })
    return exps

def extract_module_questions(start_p, end_p):
    """从试题册页面范围提取所有题目（题干与四个选项）"""
    raw_text = ""
    for p in range(start_p, end_p + 1):
        f = os.path.join(Q_TXT_DIR, f"page_{p:03d}.txt")
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8-sig") as fp:
                raw_text += f"\n=== Page {p} ===\n" + fp.read()

    cleaned = clean_ocr(raw_text)

    # 按照独立题号切分：换行 + 1..999 + 点/顿号/空格 + 汉字/书名号/引号
    pattern = re.compile(r'\n(?=\s*(\d{1,3})\s*[\.、．·:：]\s*(?:[\u4e00-\u9fa5“\"\'《A-Za-z]|\d{1,4}))')
    chunks = pattern.split("\n" + cleaned)

    questions = []
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        m_num = re.match(r'^\s*(\d{1,3})\s*[\.、．·:：]\s*([\s\S]+)', c)
        if not m_num:
            continue
        q_num = int(m_num.group(1))
        body = m_num.group(2).strip()

        # 标准化选项
        def normalize_opt_key(m):
            k = m.group(1).replace('(', '').replace(')', '').strip().upper()
            if k in ['①', '1', 'A']: return '\nA. '
            if k in ['②', '2', '8', '13', 'B']: return '\nB. '
            if k in ['③', '3', '0', 'O', 'C']: return '\nC. '
            if k in ['④', '4', 'L)', 'D']: return '\nD. '
            return f'\n{k}. '

        body = re.sub(r'(?:^|\s+)([A-Da-d①②③④80oO]|L\)|13|\([A-Da-d]\))\s*[\.、．，,·:：\s]\s*', normalize_opt_key, body)
        opt_pattern = re.compile(r'\n([A-D])\.\s*([\s\S]*?)(?=(?:\n[A-D]\.)|\Z)')
        opt_matches = list(opt_pattern.finditer(body))

        if len(opt_matches) >= 2:
            stem = body[:opt_matches[0].start()].strip()
            stem = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', stem)
            stem = re.sub(r'[\s\n]+', ' ', stem).strip()
            stem = re.sub(r'^\d{1,3}\s*[\.、．·:：]\s*', '', stem)

            opts = {}
            for om in opt_matches:
                k = om.group(1).upper()
                v = om.group(2).strip()
                v = re.sub(r'^[A-Da-d①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', v)
                v = re.sub(r'\s*\d{1,3}\s*[\.、．·:：]\s*[\u4e00-\u9fa5“\"\'《].*$', '', v)
                v = re.sub(r'=== Page \d+ ===[\s\S]*$', '', v)
                v = re.sub(r'[\s\n]+', ' ', v).strip()
                if k in ['A', 'B', 'C', 'D'] and v:
                    opts[k] = v

            final_opts = []
            for k in ['A', 'B', 'C', 'D']:
                if k in opts:
                    final_opts.append({'key': k, 'value': opts[k]})

            if len(stem) >= 6 and len(final_opts) >= 2:
                questions.append({
                    "q_num": q_num,
                    "stem": stem,
                    "options": final_opts
                })

    return questions

def run_audit():
    print("=" * 64)
    print("🚀 审核《肖秀荣 1000题》五大模块试题与解析匹配情况...")
    print("=" * 64)

    total_qs = 0
    total_exps = 0

    for m in MODULES:
        part = m["part"]
        qs = extract_module_questions(m["q_range"][0], m["q_range"][1])
        exps = extract_module_explanations(m["exp_range"][0], m["exp_range"][1])
        print(f"【{part}】试题提取: {len(qs)} 题 (P{m['q_range'][0]}~P{m['q_range'][1]}) | 解析提取: {len(exps)} 条 (P{m['exp_range'][0]}~P{m['exp_range'][1]})")
        total_qs += len(qs)
        total_exps += len(exps)

    print(f"\n全册汇总: 试题提取 {total_qs} 道，解析提取 {total_exps} 条")

if __name__ == "__main__":
    run_audit()
