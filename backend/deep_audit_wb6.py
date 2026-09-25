import sqlite3
import json
import re

conn = sqlite3.connect('backend/policy_study.db')
c = conn.cursor()

c.execute('SELECT id, question_num, stem, options_json, answer, explanation FROM questions WHERE workbook_id = 6')
rows = c.fetchall()

anomalies = []
for qid, num, stem, opts_json, ans, exp in rows:
    opts = json.loads(opts_json)
    
    # 1. 检查选项数量
    if len(opts) < 4:
        anomalies.append((qid, num, f"选项少于4个: 仅{len(opts)}个", stem[:40]))
        
    # 2. 检查解析与答案是否提及完全不相干的关键词
    # 例如：解析讲唯物唯心，选项里全是“形式与内容/共性与个性”
    # 检查解析中的关键词在题干和选项中的重合度
    exp_words = set(re.findall(r'[\u4e00-\u9fa5]{2,6}', exp))
    all_q_text = stem + " " + " ".join([o['value'] for o in opts])
    q_words = set(re.findall(r'[\u4e00-\u9fa5]{2,6}', all_q_text))
    overlap = exp_words.intersection(q_words)
    
    if len(overlap) < 3 and len(exp) > 50:
        anomalies.append((qid, num, "解析与题目关键词重合度极低(可能错位)", f"重合词:{overlap}", stem[:40], exp[:60]))

print(f"共发现异常项: {len(anomalies)} 处：")
for a in anomalies:
    print(a)

conn.close()
