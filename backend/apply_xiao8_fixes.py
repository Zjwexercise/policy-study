import sqlite3
import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Applying targeted precision fixes for Xiao 8 questions...")

# 1. Paper 1 Q1 & Q2
# Fix Q1 Option D
cursor.execute("SELECT id, options_json FROM questions WHERE workbook_id = 41 AND question_num = 1")
r = cursor.fetchone()
if r:
    q_id, opt_json = r
    opts = json.loads(opt_json)
    for opt in opts:
        if opt["key"] == "D":
            opt["value"] = "多样的事物之间存在着普遍的、无条件的联系"
    cursor.execute("UPDATE questions SET options_json = ? WHERE id = ?", (json.dumps(opts, ensure_ascii=False), q_id))
    print("Fixed WB 41 Q1 Option D")

# Fix Q2 Stem
q2_stem = "夏日炎炎，海南三亚崖州湾，田间的南繁季已结束，而“数据田”里的育种仍在进行。走进海南大学南繁学院基因组与大数据育种实验室，不见培养血与种苗圃，只有运转不息的机房。人工智能（AI)生物信息科学家智能体与大模型，能在虚拟农田里“算”出作物长什么样，帮育种科研人员节省时间。田间南繁，须守农时。每年9月到次年5月，北方的育种科研人员如候鸟南下海南岛南部，利用充足光热资源开展种子加代繁育，压缩育种周期。选种、种植、收获，重复6到7轮、花上8到10年，才能找出性状稳定、表现优良的品种。而工作人员将积累的作物基因数据“喂”给AI，让它预测作物未来的样子，提前淘汰掉不合格品种，精准锁定最具潜力、最能适应环境变化的“种子选手”。在一定条件下，相关技术能帮育种人员节约近一半时间。从“数据田”育出“种子选手”表明"
cursor.execute("UPDATE questions SET stem = ? WHERE workbook_id = 41 AND question_num = 2", (q2_stem,))
print("Fixed WB 41 Q2 Stem")

# 2. Paper 3 Q6 & Q7
# Fix Q6 Option D and Stem
q6_stem = "1978年12月，邓小平在为党的十一届三中全会做准备的中央工作会议上发表了《解放思想，实事求是，团结一致向前看》的重要讲话。讲话强调：“一个党，一个国家，一个民族，如果一切从本本出发，思想僵化，迷信盛行，那它就不能前进，它的生机就停止了，就要亡党亡国。”这个讲话"
cursor.execute("SELECT id, options_json FROM questions WHERE workbook_id = 43 AND question_num = 6")
r = cursor.fetchone()
if r:
    q_id, opt_json = r
    opts = json.loads(opt_json)
    for opt in opts:
        if opt["key"] == "D":
            opt["value"] = "开启了我国改革开放和社会主义现代化建设新时期"
    cursor.execute("UPDATE questions SET stem = ?, options_json = ? WHERE id = ?", (q6_stem, json.dumps(opts, ensure_ascii=False), q_id))
    print("Fixed WB 43 Q6 Stem and Option D")

# Fix Q7 Stem
q7_stem = "习近平总书记指出：“中国式现代化，是中国共产党领导的社会主义现代化，既有各国现代化的共同特征，更有基于自己国情的中国特色。”党的二十大集中概括了中国式现代化五个方面的中国特色，深刻揭示了中国式现代化的科学内涵，这是理论概括，也是实践要求。关于中国式现代化，以下说法正确的是①人口规模巨大的现代化是中国式现代化的显著特征②全体人民共同富裕的现代化是中国式现代化的本质特征③既要物质富足、也要精神富有，是中国式现代化的崇高追求④促进人与自然和谐共生，是中国式现代化区别于西方现代化的显著标志"
cursor.execute("UPDATE questions SET stem = ? WHERE workbook_id = 43 AND question_num = 7", (q7_stem,))
print("Fixed WB 43 Q7 Stem")

# 3. Paper 6 Q3 Explanation
p6_q3_exp = "简析社会再生产的核心问题是社会总产品的实现问题，即社会总产品的价值补偿和实物补偿问题。社会总产品的价值补偿，是指社会总产品各个组成部分的价值，如何通过商品出售以货币形式收回，用以补偿生产中预付的不变资本和可变资本并获得剩余价值。社会总产品的实物补偿，是指社会总产品各个组成部分的价值转化为货币以后，如何再购买到生产所需要的生产资料和生活资料。B正确。"
cursor.execute("UPDATE questions SET explanation = ? WHERE workbook_id = 46 AND question_num = 3", (p6_q3_exp,))
print("Fixed WB 46 Q3 Explanation")

# 4. Paper 7 Q3 Stem
p7_q3_stem = "某资本家投资100万元，其预付资本的有机构成是4：1，每次投资的剩余价值率为150%，该资本家每次投资的利润为"
cursor.execute("UPDATE questions SET stem = ? WHERE workbook_id = 47 AND question_num = 3", (p7_q3_stem,))
print("Fixed WB 47 Q3 Stem")

# 5. Fix Master Workbook (WB 49)
# Master Q1
cursor.execute("SELECT id, options_json FROM questions WHERE workbook_id = 49 AND question_num = 1")
r = cursor.fetchone()
if r:
    q_id, opt_json = r
    opts = json.loads(opt_json)
    for opt in opts:
        if opt["key"] == "D":
            opt["value"] = "多样的事物之间存在着普遍的、无条件的联系"
    cursor.execute("UPDATE questions SET options_json = ? WHERE id = ?", (json.dumps(opts, ensure_ascii=False), q_id))
    print("Fixed WB 49 Q1 Option D")

# Master Q2
cursor.execute("UPDATE questions SET stem = ? WHERE workbook_id = 49 AND question_num = 2", ("【卷一·第2题】" + q2_stem,))
print("Fixed WB 49 Q2 Stem")

# Master Q72 (Paper 3 Q6)
cursor.execute("SELECT id, options_json FROM questions WHERE workbook_id = 49 AND question_num = 72")
r = cursor.fetchone()
if r:
    q_id, opt_json = r
    opts = json.loads(opt_json)
    for opt in opts:
        if opt["key"] == "D":
            opt["value"] = "开启了我国改革开放和社会主义现代化建设新时期"
    cursor.execute("UPDATE questions SET stem = ?, options_json = ? WHERE id = ?", ("【卷三·第6题】" + q6_stem, json.dumps(opts, ensure_ascii=False), q_id))
    print("Fixed WB 49 Q72 Stem and Option D")

# Master Q73 (Paper 3 Q7)
cursor.execute("UPDATE questions SET stem = ? WHERE workbook_id = 49 AND question_num = 73", ("【卷三·第7题】" + q7_stem,))
print("Fixed WB 49 Q73 Stem")

# Master Q168 (Paper 6 Q3)
cursor.execute("UPDATE questions SET explanation = ? WHERE workbook_id = 49 AND question_num = 168", (p6_q3_exp,))
print("Fixed WB 49 Q168 Explanation")

# Master Q201 (Paper 7 Q3)
cursor.execute("UPDATE questions SET stem = ? WHERE workbook_id = 49 AND question_num = 201", ("【卷七·第3题】" + p7_q3_stem,))
print("Fixed WB 49 Q201 Stem")

conn.commit()
conn.close()
print("All database updates committed successfully!")

# Export static data for frontend
export_script = os.path.join(BASE_DIR, "backend", "export_static_data.py")
subprocess.run([sys.executable, export_script], check=True)
print("Static JSON files exported for frontend successfully!")
