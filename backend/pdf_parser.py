import re
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional

def clean_text(text: str) -> str:
    """清理多余空白与控制字符，规范化标点"""
    if not text:
        return ""
    # 将全角字符或非标字符做标准化
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\u3000', ' ')  # 全角空格
    text = text.replace('\xa0', ' ')    # 不间断空格
    return text

def extract_pdf_blocks(file_path: str) -> List[str]:
    """
    智能提取PDF文本：
    自动识别页面分栏（如考研习题集常见的双栏排版），按栏目顺序和纵向坐标自然排序，
    避免跨栏左右错乱串行。
    """
    doc = fitz.open(file_path)
    page_texts = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        rect = page.rect
        width = rect.width
        mid_x = width / 2.0

        # 获取带坐标的文本块
        blocks = page.get_text("blocks")
        
        # 判断当前页面是否大致为双栏排版
        left_blocks = [b for b in blocks if b[2] <= mid_x + 30 and len(b[4].strip()) > 0]
        right_blocks = [b for b in blocks if b[0] >= mid_x - 30 and len(b[4].strip()) > 0]
        is_two_columns = len(left_blocks) >= 2 and len(right_blocks) >= 2

        if is_two_columns:
            # 排序：先排左栏（按y0），再排右栏（按y0），跨越中线的块插入合适位置
            def sort_key(b):
                x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
                column = 0 if x1 <= mid_x + 20 else (1 if x0 >= mid_x - 20 else 0)
                return (column, y0)
            sorted_blocks = sorted(blocks, key=sort_key)
        else:
            # 单栏：直接按垂直位置排序
            sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

        page_content = "\n".join([b[4] for b in sorted_blocks if b[4].strip()])
        page_texts.append(page_content)

    doc.close()
    return page_texts

def split_options(options_text: str) -> List[Dict[str, str]]:
    """
    智能切分选项 A, B, C, D (及 E)
    兼容同一行多个选项或分行选项、中文全角标点等
    """
    options = []
    # 正则匹配形如 A. A、 A． (A) [A]
    opt_pattern = re.compile(
        r'(?:^|[\s\n\t]+)([A-Ea-e])[\.、．\s\)\:\：\]]+', 
        re.MULTILINE
    )
    
    matches = list(opt_pattern.finditer(options_text))
    if not matches:
        return options

    for i, match in enumerate(matches):
        key = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(options_text)
        val = options_text[start:end].strip()
        # 清除结尾可能多出的换行或标点
        val = re.sub(r'[\s\n]+', ' ', val).strip()
        options.append({"key": key, "value": val})

    return options

def detect_category(text: str, default: str = "综合") -> str:
    """根据章节或题干关键词识别所属政治学科"""
    if any(k in text for k in ["马克思", "唯物", "辩证", "认识论", "剩余价值", "唯物史观", "资本主义", "商品经济", "马原"]):
        return "马原"
    if any(k in text for k in ["毛泽东", "习近平", "中国特色社会主义", "新时代", "新质生产力", "高质量发展", "共同富裕", "毛中特", "习思想"]):
        return "毛中特"
    if any(k in text for k in ["鸦片战争", "辛亥革命", "五四运动", "中国共产党成立", "抗日战争", "长征", "新民主主义革命", "史纲", "近代史"]):
        return "史纲"
    if any(k in text for k in ["思想道德", "法治", "宪法", "社会主义核心价值观", "人生观", "理想信念", "道德", "思修"]):
        return "思修"
    if any(k in text for k in ["二十大", "二十届", "一带一路", "中美元首", "上合组织", "时事", "时政", "金砖", "形势与政策"]):
        return "时政"
    return default

def parse_politics_pdf(file_path: str) -> Dict[str, Any]:
    """
    主解析函数：
    1. 解析单选/多选题干、选项
    2. 匹配答案与解析（支持题后紧跟解析、或书末/章末统一答案）
    """
    page_texts = extract_pdf_blocks(file_path)
    full_text = "\n".join(page_texts)
    full_text = clean_text(full_text)

    # 尝试判断是否存在单独的“参考答案”或“答案与解析”区域
    answer_section_pattern = re.search(
        r'\n\s*(?:【?(?:参考答案|答案与解析|答案及解析|答案速查|参考解析)】?|二、参考答案|第二部分\s*答案)\s*\n', 
        full_text
    )

    questions = []
    
    # 策略 1：如果全文属于题目与答案一体（题后直接跟答案解析，最常见格式）
    # 或者分开解析并合并
    if answer_section_pattern:
        split_pos = answer_section_pattern.start()
        questions_part = full_text[:split_pos]
        answers_part = full_text[split_pos:]
        questions = _parse_questions_and_separate_answers(questions_part, answers_part)
    else:
        questions = _parse_inline_questions(full_text)

    # 如果解析出的题目数量较少（可能分隔符不典型），尝试更宽松的一体化模式解析
    if len(questions) == 0:
        questions = _parse_inline_questions_relaxed(full_text)

    return {
        "success": True,
        "total_parsed": len(questions),
        "questions": questions
    }

def _parse_inline_questions(text: str) -> List[Dict[str, Any]]:
    """
    题、选项、答案、解析一体的模式解析
    """
    questions = []
    lines = text.split('\n')
    
    current_q = None
    current_category = "综合"
    current_type = "single" # 默认单选

    # 题号匹配正则，如：1. 1、 1． 【1】 (1)
    q_start_re = re.compile(r'^\s*(?:【?(?:单选|多选)?】?\s*)?(\d+)[\.、．\s\:\：](.*)$')
    # 题型大题标题正则
    section_single_re = re.compile(r'单项选择题|单选题|（单选）|【单选】|每题\s*1\s*分')
    section_multi_re = re.compile(r'多项选择题|多选题|（多选）|【多选】|每题\s*2\s*分')

    buffer = []
    mode = "stem" # stem, options, answer, explanation

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 检查是否切换了章节或题型大标题
        if section_multi_re.search(stripped):
            current_type = "multiple"
            continue
        elif section_single_re.search(stripped):
            current_type = "single"
            continue

        cat = detect_category(stripped, "")
        if cat:
            current_category = cat

        q_match = q_start_re.match(stripped)
        if q_match:
            # 遇到新题目，保存上一题
            if current_q:
                _finalize_question(current_q)
                questions.append(current_q)

            q_num = int(q_match.group(1))
            stem_init = q_match.group(2).strip()

            # 判断题干中是否标注了多选，例如 "1. (多选) 唯物辩证法..."
            q_type = current_type
            if "多选" in stem_init or "多项选择" in stem_init:
                q_type = "multiple"
            elif "单选" in stem_init or "单项选择" in stem_init:
                q_type = "single"

            current_q = {
                "question_num": q_num,
                "question_type": q_type,
                "category": current_category,
                "stem": stem_init,
                "options_raw": "",
                "options": [],
                "answer": "",
                "explanation": "",
                "_current_part": "stem"
            }
            continue

        if not current_q:
            continue

        # 检查是否出现【答案】/ 答案：
        ans_match = re.search(r'(?:【?\s*参考答案\s*】?|【?\s*答案\s*】?|答案\s*[:：])\s*([A-Ea-e]+)', stripped)
        if ans_match:
            current_q["answer"] = ans_match.group(1).upper()
            if len(current_q["answer"]) > 1:
                current_q["question_type"] = "multiple"
            current_q["_current_part"] = "answer"
            
            # 检查同一行是否紧跟解析
            exp_match = re.search(r'(?:【?\s*解析\s*】?|解析\s*[:：])\s*(.*)', stripped)
            if exp_match:
                current_q["explanation"] = exp_match.group(1).strip()
                current_q["_current_part"] = "explanation"
            continue

        # 检查是否出现【解析】/ 解析：
        exp_start = re.search(r'(?:【?\s*参考解析\s*】?|【?\s*解析\s*】?|解析\s*[:：])\s*(.*)', stripped)
        if exp_start:
            current_q["explanation"] += " " + exp_start.group(1).strip()
            current_q["_current_part"] = "explanation"
            continue

        # 检查是否出现选项 A. B. C. D.
        is_option_line = bool(re.search(r'(?:^|[\s]+)[A-Ea-e][\.、．\s\)\:\：]', stripped))
        if is_option_line and current_q["_current_part"] in ["stem", "options"]:
            current_q["_current_part"] = "options"
            current_q["options_raw"] += "\n" + stripped
            continue

        # 正在录入各个部分
        if current_q["_current_part"] == "stem":
            current_q["stem"] += " " + stripped
        elif current_q["_current_part"] == "options":
            current_q["options_raw"] += " " + stripped
        elif current_q["_current_part"] in ["answer", "explanation"]:
            current_q["explanation"] += "\n" + stripped

    if current_q:
        _finalize_question(current_q)
        questions.append(current_q)

    return questions

def _finalize_question(q: Dict[str, Any]):
    """整理题目的选项和解析格式"""
    q["stem"] = re.sub(r'\s+', ' ', q["stem"]).strip()
    # 切分选项
    if q.get("options_raw"):
        q["options"] = split_options(q["options_raw"])
    
    # 如果选项为空，尝试从题干中切分
    if not q["options"]:
        # 看看题干末尾是否有 A. B. C. D.
        opt_start = re.search(r'(?:^|[\s]+)[A-Ea-e][\.、．\s\)\:\：]', q["stem"])
        if opt_start:
            stem_text = q["stem"][:opt_start.start()].strip()
            opts_text = q["stem"][opt_start.start():].strip()
            q["stem"] = stem_text
            q["options"] = split_options(opts_text)

    # 如果答案多于1个字母，确认为多选题
    if len(q.get("answer", "")) > 1:
        q["question_type"] = "multiple"

    q["explanation"] = q["explanation"].strip()
    q.pop("options_raw", None)
    q.pop("_current_part", None)

def _parse_inline_questions_relaxed(text: str) -> List[Dict[str, Any]]:
    """宽松模式解析：使用全局正则查找题目块"""
    questions = []
    # 查找所有数字题号块
    pattern = re.compile(
        r'(?:^|\n)\s*(\d+)[\.、．\s]([\s\S]+?)(?=(?:\n\s*\d+[\.、．\s])|\Z)',
        re.MULTILINE
    )

    for match in pattern.finditer(text):
        q_num = int(match.group(1))
        content = match.group(2).strip()

        # 拆分 题干/选项/答案/解析
        ans_search = re.search(r'(?:【?\s*答案\s*】?|答案\s*[:：])\s*([A-Ea-e]+)', content)
        answer = ans_search.group(1).upper() if ans_search else ""
        
        exp_search = re.search(r'(?:【?\s*解析\s*】?|解析\s*[:：])\s*([\s\S]*)', content)
        explanation = exp_search.group(1).strip() if exp_search else ""

        # 排除答案和解析后的纯题干+选项
        body_end = len(content)
        if ans_search:
            body_end = min(body_end, ans_search.start())
        if exp_search:
            body_end = min(body_end, exp_search.start())

        body = content[:body_end].strip()

        # 分离选项
        first_opt = re.search(r'(?:^|[\s\n]+)[Aa][\.、．\s\)\:\：]', body)
        if first_opt:
            stem = body[:first_opt.start()].strip()
            opts_text = body[first_opt.start():].strip()
            options = split_options(opts_text)
        else:
            stem = body
            options = []

        q_type = "multiple" if len(answer) > 1 or "多选" in stem else "single"
        category = detect_category(stem + " " + explanation)

        questions.append({
            "question_num": q_num,
            "question_type": q_type,
            "category": category,
            "stem": stem,
            "options": options,
            "answer": answer,
            "explanation": explanation
        })

    return questions

def _parse_questions_and_separate_answers(q_text: str, a_text: str) -> List[Dict[str, Any]]:
    """处理题目在前、答案解析在后（分开编排）的格式"""
    # 1. 先解析前半部分的题目与选项
    questions = _parse_inline_questions_relaxed(q_text)
    
    # 2. 从后半部分提取答案和解析字典：{题号: {"answer": ..., "explanation": ...}}
    ans_map = {}

    # 匹配后半部分 "1. 【答案】A 【解析】..." 或者 "1-5: A B C D A"
    ans_item_pattern = re.compile(
        r'(?:^|\n)\s*(\d+)[\.、．\s]([\s\S]+?)(?=(?:\n\s*\d+[\.、．\s])|\Z)',
        re.MULTILINE
    )
    for m in ans_item_pattern.finditer(a_text):
        q_num = int(m.group(1))
        content = m.group(2).strip()

        ans_match = re.search(r'(?:【?\s*答案\s*】?|答案\s*[:：]|\s*)([A-Ea-e]+)', content)
        answer = ans_match.group(1).upper() if ans_match else ""

        exp_match = re.search(r'(?:【?\s*解析\s*】?|解析\s*[:：])\s*([\s\S]*)', content)
        explanation = exp_match.group(1).strip() if exp_match else ""

        ans_map[q_num] = {
            "answer": answer,
            "explanation": explanation
        }

    # 合并
    for q in questions:
        q_num = q["question_num"]
        if q_num in ans_map:
            if not q.get("answer"):
                q["answer"] = ans_map[q_num]["answer"]
            if not q.get("explanation"):
                q["explanation"] = ans_map[q_num]["explanation"]
            if len(q["answer"]) > 1:
                q["question_type"] = "multiple"

    return questions
