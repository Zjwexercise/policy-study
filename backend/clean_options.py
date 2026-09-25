import sqlite3
import json
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def clean_single_option_value(val: str) -> str:
    if not val:
        return ""
    # 移除开头的冗余选项字母（如被误识别到选项值内部的 "B. " 或 "D. "）
    val = re.sub(r'^[A-Da-dＡ-Ｄａ-ｄ①②③④\(\)]\s*[\.、．，,·:\s]\s*', '', val)
    # 移除页码渗漏
    val = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', val)
    # 移除诸如 〖 答案 〗 或 【解析】
    val = re.sub(r'(?:〖?\s*答案\s*〗?|【?\s*答案\s*】?|〖?\s*解析\s*〗?|【?\s*解析\s*】?)[\s\S]*$', '', val)
    # 移除下一题题干混入（例如：3 毛泽东强调... 或 4 · 恩格斯... 或 12. 题干...）
    val = re.sub(r'\s*\d{1,3}\s*[\.、．，,·:\s]\s*[\u4e00-\u9fa5“\"\'《].*$', '', val)
    # 移除尾部 OCR 杂符与乱码
    val = re.sub(r'[\?v\'\‘\’\@\?·孑]+$', '', val)
    # 移除做题解析注解（例如：表述错误...、不合题意、不符合题意...）
    val = re.sub(r'[\s,，、](?:表述错误|不合题意|不符合题意|与题意不符|与题目无关|基础知识表达错误|说法错误|说法绝对|不选|故不选|属于.*的内容).*$', '', val)
    val = re.sub(r'(?:表述错误|不合题意|不符合题意|与题意不符|与题目无关|基础知识表达错误|说法错误|说法绝对)$', '', val)
    # 压缩多余空格
    val = re.sub(r'[\s\n]+', ' ', val).strip()
    return val

def recover_from_explanation(opts_dict, explanation):
    """从解析文本开头找回遗漏的 B/C/D 选项"""
    if not explanation:
        return opts_dict, explanation
    
    # 查找如：B ． 选项内容 D ． 选项内容
    pat = re.compile(r'(?:^|[。\s@·\d])([B-Db-dＢ-Ｄｂ-ｄ])\s*[\.、．，,:\s]\s*([\u4e00-\u9fa5A-Za-z0-9\s（）《》“”]+?)(?=(?:[B-Db-dＢ-Ｄｂ-ｄ]\s*[\.、．，,:\s])|〖|【|ABD|不合题意|与题目无关|$)')
    matches = list(pat.finditer(explanation[:180]))
    for m in matches:
        k = m.group(1).upper()
        if k in ['Ｂ']: k = 'B'
        elif k in ['Ｃ']: k = 'C'
        elif k in ['Ｄ']: k = 'D'
        v = clean_single_option_value(m.group(2))
        if k not in opts_dict or len(opts_dict[k]) < 3:
            if len(v) >= 2 and not any(neg in v for neg in ['不选', '错误', '不符']):
                opts_dict[k] = v

    return opts_dict, explanation

def clean_and_split_options(raw_stem, raw_options, raw_answer, raw_explanation):
    """
    智能修复选项混乱、选项粘连、选项中混入解析与页码等问题
    """
    # 规范化原 options
    merged_chunks = []
    for o in raw_options:
        k = o.get('key', '').upper()
        v = o.get('value', '')
        # 如果内部含有形如 "0 物理世界..." 或 "I). 一个..." 或 "c ．"
        v = re.sub(r'(?:^|\s+)[0oO○]\s*[\.、．，,:\s]\s*([\u4e00-\u9fa5])', r' C. \1', v)
        v = re.sub(r'(?:^|\s+)(?:[I|1]|\(?1\)?)\s*[\)）\.、．，,:\s]\s*([\u4e00-\u9fa5])', r' D. \1', v)
        merged_chunks.append(f"{k}. {v}")

    merged_str = " ".join(merged_chunks)

    # 选项匹配切分正则
    opt_pat = re.compile(
        r'(?:^|\s+|[，。；\n])([A-Da-dＡ-Ｄａ-ｄ]|[①②③④]|\([A-Da-d]\))\s*[\.、．，,:\s]\s*'
    )

    matches = list(opt_pat.finditer(merged_str))
    extracted = {}
    if len(matches) >= 2:
        for i, m in enumerate(matches):
            raw_key = m.group(1).upper()
            if raw_key in ['①', '1']: raw_key = 'A'
            elif raw_key in ['②', '2']: raw_key = 'B'
            elif raw_key in ['③', '3']: raw_key = 'C'
            elif raw_key in ['④', '4']: raw_key = 'D'
            raw_key = raw_key.replace('(', '').replace(')', '').strip()
            if raw_key in ['Ａ']: raw_key = 'A'
            elif raw_key in ['Ｂ']: raw_key = 'B'
            elif raw_key in ['Ｃ']: raw_key = 'C'
            elif raw_key in ['Ｄ']: raw_key = 'D'

            start = m.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(merged_str)
            val = merged_str[start:end].strip()
            val = clean_single_option_value(val)
            if val and raw_key in ['A', 'B', 'C', 'D']:
                if raw_key not in extracted or len(val) > len(extracted[raw_key]):
                    extracted[raw_key] = val
    else:
        for o in raw_options:
            k = o.get('key', '').upper()
            v = clean_single_option_value(o.get('value', ''))
            if k in ['A', 'B', 'C', 'D'] and v:
                extracted[k] = v

    # 如果依然缺失选项，尝试从解析首部回收
    if len(extracted) < 4 and raw_explanation:
        extracted, _ = recover_from_explanation(extracted, raw_explanation)

    # 保证顺序 A, B, C, D
    ordered = []
    for k in ['A', 'B', 'C', 'D']:
        if k in extracted:
            ordered.append({'key': k, 'value': extracted[k]})
        else:
            # 如果依然找不到（极少数残缺），给一个占位或原选项
            pass

    # 清理 stem
    clean_stem = re.sub(r'=== Page \d+ ===[\s\S]*?(?=[A-Za-z\u4e00-\u9fa5]|$)', '', raw_stem)
    clean_stem = re.sub(r'[\s\n]+', ' ', clean_stem).strip()

    return clean_stem, ordered

if __name__ == "__main__":
    conn = sqlite3.connect('backend/policy_study.db')
    c = conn.cursor()
    c.execute('SELECT id, stem, options_json, answer, explanation FROM questions')
    rows = c.fetchall()

    fixed_count = 0
    for qid, stem, opts_json, ans, exp in rows:
        opts = json.loads(opts_json)
        new_stem, new_opts = clean_and_split_options(stem, opts, ans, exp)
        if new_opts != opts or new_stem != stem:
            fixed_count += 1
            c.execute('UPDATE questions SET stem = ?, options_json = ? WHERE id = ?', 
                      (new_stem, json.dumps(new_opts, ensure_ascii=False), qid))

    conn.commit()
    conn.close()
    print(f"深度清洗并重构了 {fixed_count} / {len(rows)} 道题目！")
