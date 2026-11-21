import sqlite3
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

TARGET_QUESTIONS = [
    # (wb_id, q_num, prompt_suffix)
    (43, 7, "关于中国式现代化，以下说法正确的是（ ）"),
    (44, 5, "马克思主义中国化时代化的理论成果是一脉相承又与时俱进的关系。它们都是（ ）"),
    (45, 11, "大会明确规定共产党员加入国民党时，党必须在（ ）"),
    (46, 11, "其中，秋收起义不同于南昌起义的特点有（ ）"),
    (47, 7, "新质生产力的显著特点是创新，这种创新包括（ ）"),
    (48, 11, "古田会议创造性地解决了在农村环境中、在党组织和军队以农民为主要成分的条件下（ ）"),
    
    # 1000题
    (34, 65, None),
    (35, 5, None),
]

def format_stem(stem, custom_prompt_split=None):
    # Remove stray headers if any
    stem = stem.replace("导论马克思主义中国化时代化的历史进程与理论成果", "").strip()
    
    parts = stem.split('①', 1)
    prefix = parts[0].strip()
    rest = '①' + parts[1]
    
    if custom_prompt_split:
        # replace prefix ending with custom prompt
        # Check if prefix already contains it or needs completion
        if not (prefix.endswith('（）') or prefix.endswith('（ ）') or prefix.endswith('？') or prefix.endswith('?')):
            prefix += '（ ）'
    else:
        if not (prefix.endswith('（）') or prefix.endswith('（ ）') or prefix.endswith('：') or prefix.endswith(':') or prefix.endswith('？') or prefix.endswith('?')):
            if prefix.endswith('体现了') or prefix.endswith('说明') or prefix.endswith('表明') or prefix.endswith('正确的是') or prefix.endswith('有'):
                prefix += '（ ）'
            else:
                prefix += '（ ）'
                
    items = re.split(r'([①②③④⑤⑥])', rest)
    formatted_items = []
    for i in range(1, len(items), 2):
        num = items[i]
        val = items[i+1].strip() if i+1 < len(items) else ""
        formatted_items.append(f"{num} {val}")
        
    return prefix + "\n" + "\n".join(formatted_items)

# Process target questions
updated_count = 0
for wb_id, q_num, custom_prompt in TARGET_QUESTIONS:
    c.execute("SELECT id, stem FROM questions WHERE workbook_id = ? AND question_num = ?", (wb_id, q_num))
    row = c.fetchone()
    if row:
        qid, stem = row
        new_stem = format_stem(stem, custom_prompt)
        c.execute("UPDATE questions SET stem = ? WHERE id = ?", (new_stem, qid))
        print(f"Updated WB{wb_id} Q{q_num}:\n{new_stem}\n")
        updated_count += 1
        
        # Also update corresponding master workbook questions
        if wb_id in range(41, 49):
            master_q_num = (wb_id - 41) * 33 + q_num
            c.execute("SELECT id, stem FROM questions WHERE workbook_id = 49 AND question_num = ?", (master_q_num,))
            m_row = c.fetchone()
            if m_row:
                m_qid, m_stem = m_row
                # WB49 might have prefix like "【卷四·第5题】"
                m_prefix = ""
                if m_stem.startswith("【"):
                    tag_end = m_stem.find("】")
                    if tag_end != -1:
                        m_prefix = m_stem[:tag_end+1]
                m_new_stem = (m_prefix + new_stem) if m_prefix else new_stem
                c.execute("UPDATE questions SET stem = ? WHERE id = ?", (m_new_stem, m_qid))
                print(f"Updated Master WB49 Q{master_q_num} counterpart.")
                updated_count += 1
                
        elif wb_id in [34, 35]:
            # WB39 is 1000题 master
            c.execute("SELECT id, stem FROM questions WHERE workbook_id = 39 AND stem LIKE ?", (f"%{stem[:30]}%",))
            for m_row in c.fetchall():
                c.execute("UPDATE questions SET stem = ? WHERE id = ?", (new_stem, m_row[0]))
                print(f"Updated 1000-master WB39 counterpart (id={m_row[0]}).")
                updated_count += 1

conn.commit()
conn.close()
print(f"\n🎉 成功更新并格式化 {updated_count} 条题目的题干排版！")
