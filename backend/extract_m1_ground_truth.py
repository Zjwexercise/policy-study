import fitz
import re
import json

doc = fitz.open('pdf/27《优题库》 - 压缩版/27《优题库》 - 压缩版/（已压缩）27《优题库-解析拔高篇》.pdf')

# Page 6 to 15 are 马原·综合测试一
# Page index 5 to 14
full_m1_text = ""
for p in range(5, 15):
    full_m1_text += f"\n=== Page {p+1} ===\n" + doc[p].get_text()

# 1. 提取 答案速查
# 题号 1 2 3 4 ... 答案 A C A A ...
# Page 6 包含完整的 答案速查 表格
p6_text = doc[5].get_text()
print("P6 Text:")
print(p6_text[:800])

# 2. 提取解析块
# 形如：
# 1. A\n9解题思路...
# 2. C\n...
# 3. A\n...
m1_exps = {}
pattern = re.compile(
    r'(?:^|\n)\s*(\d{1,2})\s*[\.、．]\s*([A-D]{1,4})\s*\n(?:9?解题思路|【?解题思路】?|【?解析】?)([\s\S]*?)(?=(?:\n\s*\d{1,2}\s*[\.、．]\s*[A-D]{1,4}\s*\n(?:9?解题思路|【?解题思路】?|【?解析】?))|=== Page 16|\Z)'
)

for m in pattern.finditer(full_m1_text):
    qn = int(m.group(1))
    ans = m.group(2).strip().upper()
    body = re.sub(r'=== Page \d+ ===[\s\S]*?(?=\n|$)', '', m.group(3))
    body = re.sub(r'[\s\n]+', ' ', body).strip()
    body = body.replace('9干扰选项', ' 【干扰选项】').replace('干扰选项', ' 【干扰选项】')
    body = body.replace('9解题思路', '【解题思路】')
    m1_exps[qn] = {
        'answer': ans,
        'explanation': f"【综合测试一 第 {qn} 题】{body}"
    }

print(f"提取到解析数量: {len(m1_exps)}")
for qn in sorted(m1_exps.keys()):
    print(f"Q{qn}: Ans={m1_exps[qn]['answer']} | Exp={m1_exps[qn]['explanation'][:60]}")
