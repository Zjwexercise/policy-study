import json
import sqlite3
from database import get_db, init_db, DB_PATH

DEMO_QUESTIONS = [
    # 马克思主义基本原理 - 单选
    {
        "question_num": 1,
        "question_type": "single",
        "category": "马原",
        "stem": "马克思主义哲学认为，物质的唯一特性是（ ）。",
        "options": [
            {"key": "A", "value": "客观实在性"},
            {"key": "B", "value": "运动的绝对性"},
            {"key": "C", "value": "可知性"},
            {"key": "D", "value": "时空无限性"}
        ],
        "answer": "A",
        "explanation": "【解析】列宁对物质概念作了全面的科学的规定：“物质是标志客观实在的哲学范畴，这种客观实在是人通过感觉感知的，它不依赖于我们的感觉而存在，为我们的感觉所复写、摄影、反映。”物质的唯一特性是客观实在性，它存在于人的意识之外，可以为人的意识所反映。因此本题正确答案为A。"
    },
    {
        "question_num": 2,
        "question_type": "single",
        "category": "马原",
        "stem": "“沉舟侧畔千帆过，病树前头万木春。”辩证法认为发展的实质是（ ）。",
        "options": [
            {"key": "A", "value": "事物数量的增减和位置的移动"},
            {"key": "B", "value": "事物的质变"},
            {"key": "C", "value": "新事物的产生和旧事物的灭亡"},
            {"key": "D", "value": "事物内部矛盾的调和"}
        ],
        "answer": "C",
        "explanation": "【解析】唯物辩证法认为，发展是前进上升的运动，发展的实质是新事物的产生和旧事物的灭亡。新事物是指合乎历史前进方向、具有远大前途的东西；旧事物是指丧失历史必然性、日趋灭亡的东西。因此正确答案为C。"
    },
    {
        "question_num": 3,
        "question_type": "single",
        "category": "马原",
        "stem": "商品的二因素是使用价值和价值，决定商品二因素的是（ ）。",
        "options": [
            {"key": "A", "value": "具体劳动和抽象劳动"},
            {"key": "B", "value": "简单劳动和复杂劳动"},
            {"key": "C", "value": "私人劳动和社会劳动"},
            {"key": "D", "value": "体力劳动和脑力劳动"}
        ],
        "answer": "A",
        "explanation": "【解析】商品是由劳动创造的。生产商品的劳动具有二重性，即具体劳动和抽象劳动。具体劳动创造商品的使用价值，抽象劳动形成商品的价值。劳动的二重性决定了商品的二因素。因此正确答案为A。"
    },
    # 马克思主义基本原理 - 多选
    {
        "question_num": 4,
        "question_type": "multiple",
        "category": "马原",
        "stem": "实践是认识的基础，实践在认识活动中的决定作用表现在（ ）。",
        "options": [
            {"key": "A", "value": "实践是认识的来源"},
            {"key": "B", "value": "实践是认识发展的动力"},
            {"key": "C", "value": "实践是检验认识真理性的唯一标准"},
            {"key": "D", "value": "实践是认识的目的"}
        ],
        "answer": "ABCD",
        "explanation": "【解析】实践对认识的决定作用表现在：第一，实践是认识的来源；第二，实践是认识发展的动力；第三，实践是检验认识是否具有真理性的唯一标准；第四，实践是认识的目的。四个选项全符合题意，因此答案选ABCD。"
    },
    {
        "question_num": 5,
        "question_type": "multiple",
        "category": "马原",
        "stem": "在真理观上，真理与谬误是辩证统一的，二者的关系表现为（ ）。",
        "options": [
            {"key": "A", "value": "真理与谬误相互对立，有着确定的界限"},
            {"key": "B", "value": "真理与谬误相互依存、互为前提"},
            {"key": "C", "value": "真理与谬误在一定条件下可以相互转化"},
            {"key": "D", "value": "真理中包含着某种谬误的成分"}
        ],
        "answer": "ABC",
        "explanation": "【解析】真理与谬误是对立统一的。相互对立表现在两者在确定对象和范围内界限分明，不能混淆（A正确）；相互依存表现在真理同谬误相比较而存在，没有谬误就无所谓真理（B正确）；在一定条件下二者可以相互转化（C正确）。真理是对客观事物及其规律的正确反映，并不包含谬误成分，D错误。因此正确答案为ABC。"
    },
    # 毛中特与习近平新时代中国特色社会主义思想 - 单选
    {
        "question_num": 6,
        "question_type": "single",
        "category": "毛中特",
        "stem": "中国共产党思想路线的核心和实质是（ ）。",
        "options": [
            {"key": "A", "value": "一切从实际出发"},
            {"key": "B", "value": "理论联系实际"},
            {"key": "C", "value": "实事求是"},
            {"key": "D", "value": "在实践中检验真理和发展真理"}
        ],
        "answer": "C",
        "explanation": "【解析】中国共产党的思想路线是一切从实际出发，理论联系实际，实事求是，在实践中检验真理和发展真理。其实质和核心是实事求是。实事求是也是毛泽东思想的精髓。因此正确答案为C。"
    },
    {
        "question_num": 7,
        "question_type": "single",
        "category": "毛中特",
        "stem": "习近平新时代中国特色社会主义思想明确的新时代我国社会主要矛盾是（ ）。",
        "options": [
            {"key": "A", "value": "人民日益增长的物质文化需要同落后的社会生产之间的矛盾"},
            {"key": "B", "value": "人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾"},
            {"key": "C", "value": "经济发展与环境保护之间的矛盾"},
            {"key": "D", "value": "生产力与生产关系之间的矛盾"}
        ],
        "answer": "B",
        "explanation": "【解析】党的十九大明确指出，中国特色社会主义进入新时代，我国社会主要矛盾已经转化为人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾。因此正确答案为B。"
    },
    {
        "question_num": 8,
        "question_type": "multiple",
        "category": "毛中特",
        "stem": "新质生产力是创新起主导作用，具有高科技、高效能、高质量特征，符合新发展理念的先进生产力质态。发展新质生产力的核心要素和显著特征分别是（ ）。",
        "options": [
            {"key": "A", "value": "核心要素是科技创新"},
            {"key": "B", "value": "主要标志是全要素生产率大幅提升"},
            {"key": "C", "value": "关键在于引进外部资本"},
            {"key": "D", "value": "特点是创新，关键在质优，本质是先进生产力"}
        ],
        "answer": "ABD",
        "explanation": "【解析】习近平总书记指出，新质生产力特点是创新，关键在质优，本质是先进生产力（D正确）。科技创新是发展新质生产力的核心要素（A正确）。新质生产力以全要素生产率大幅提升为核心标志（B正确）。发展新质生产力强调自主创新和内生动力，而非关键在于引进外部资本（C错误）。故正确答案为ABD。"
    },
    # 中国近现代史纲要 - 单选与多选
    {
        "question_num": 9,
        "question_type": "single",
        "category": "史纲",
        "stem": "中国近代史的开端和中国旧民主主义革命的开端是（ ）。",
        "options": [
            {"key": "A", "value": "第一次鸦片战争"},
            {"key": "B", "value": "太平天国运动"},
            {"key": "C", "value": "甲午中日战争"},
            {"key": "D", "value": "辛亥革命"}
        ],
        "answer": "A",
        "explanation": "【解析】1840年第一次鸦片战争爆发，中国由封建社会逐渐沦为半殖民地半封建社会，标志着中国近代史的开端，也是中国旧民主主义革命的起点。因此正确答案为A。"
    },
    {
        "question_num": 10,
        "question_type": "single",
        "category": "史纲",
        "stem": "中国共产党历史上生死攸关的转折点是（ ）。",
        "options": [
            {"key": "A", "value": "八七会议"},
            {"key": "B", "value": "遵义会议"},
            {"key": "C", "value": "瓦窑堡会议"},
            {"key": "D", "value": "中共七大"}
        ],
        "answer": "B",
        "explanation": "【解析】1935年1月召开的遵义会议，结束了“左”倾教条主义在中央的统治，确立了毛泽东在红军和党中央的领导地位，在极其危急的关头挽救了党、挽救了红军、挽救了中国革命，是中国共产党历史上生死攸关的转折点。因此正确答案为B。"
    },
    {
        "question_num": 11,
        "question_type": "multiple",
        "category": "史纲",
        "stem": "中国共产党在中国革命中战胜敌人的三个主要法宝是（ ）。",
        "options": [
            {"key": "A", "value": "统一战线"},
            {"key": "B", "value": "武装斗争"},
            {"key": "C", "value": "党的建设"},
            {"key": "D", "value": "土地革命"}
        ],
        "answer": "ABC",
        "explanation": "【解析】毛泽东在《〈共产党人〉发刊词》中指出：“统一战线，武装斗争，党的建设，是中国共产党在中国革命中战胜敌人的三个法宝，三个主要的法宝。”土地革命是基本内容，但不属于“三大法宝”。因此正确答案为ABC。"
    },
    # 思想道德与法治 - 单选与多选
    {
        "question_num": 12,
        "question_type": "single",
        "category": "思修",
        "stem": "人生观的核心是（ ）。",
        "options": [
            {"key": "A", "value": "人生目的"},
            {"key": "B", "value": "人生态度"},
            {"key": "C", "value": "人生价值"},
            {"key": "D", "value": "人生信仰"}
        ],
        "answer": "A",
        "explanation": "【解析】人生观主要包括人生目的、人生态度和人生价值三个方面。其中，人生目的是人生观的核心，回答了人为什么活着的问题，决定了人生态度和人生价值取向。因此正确答案为A。"
    },
    {
        "question_num": 13,
        "question_type": "multiple",
        "category": "思修",
        "stem": "社会主义核心价值观在国家层面的价值要求是（ ）。",
        "options": [
            {"key": "A", "value": "富强"},
            {"key": "B", "value": "民主"},
            {"key": "C", "value": "文明"},
            {"key": "D", "value": "和谐"}
        ],
        "answer": "ABCD",
        "explanation": "【解析】社会主义核心价值观中：国家层面的价值目标是“富强、民主、文明、和谐”；社会层面的价值取向是“自由、平等、公正、法治”；公民个人层面的价值准则是“爱国、敬业、诚信、友善”。因此国家层面的要求选ABCD。"
    },
    # 形势与政策及当代世界经济与政治 - 单选与多选
    {
        "question_num": 14,
        "question_type": "single",
        "category": "时政",
        "stem": "中国外交政策的宗旨是（ ）。",
        "options": [
            {"key": "A", "value": "维护世界和平、促进共同发展"},
            {"key": "B", "value": "独立自主"},
            {"key": "C", "value": "和平共处五项原则"},
            {"key": "D", "value": "互利共赢"}
        ],
        "answer": "A",
        "explanation": "【解析】中国始终奉行独立自主的和平外交政策。独立自主是中国外交政策的基本立场；维护世界和平、促进共同发展是中国外交政策的宗旨；和平共处五项原则是中国对外关系的基本准则。因此正确答案为A。"
    },
    {
        "question_num": 15,
        "question_type": "multiple",
        "category": "时政",
        "stem": "构建人类命运共同体理念的丰富内涵包括建设一个（ ）的世界。",
        "options": [
            {"key": "A", "value": "持久和平、普遍安全"},
            {"key": "B", "value": "共同繁荣"},
            {"key": "C", "value": "开放包容"},
            {"key": "D", "value": "清洁美丽"}
        ],
        "answer": "ABCD",
        "explanation": "【解析】构建人类命运共同体，核心就是建设持久和平、普遍安全、共同繁荣、开放包容、清洁美丽的世界。本题全选，答案为ABCD。"
    }
]

def seed_default_workbook():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 仅当题库彻底为空时，才注入初始化示例，避免干扰用户真实导入的3本练习册
    cursor.execute("SELECT count(*) FROM workbooks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("""
        INSERT INTO workbooks (name, filename, file_path, total_questions, description)
        VALUES (?, ?, ?, ?, ?)
        """, (
            "考研政治核心高频题集（示范题库）",
            "demo_politics.pdf",
            "",
            len(DEMO_QUESTIONS),
            "涵盖马原、毛中特/习思想、史纲、思修法基、形策的经典单选与多选题，含详尽解析"
        ))
        workbook_id = cursor.lastrowid

        for idx, q in enumerate(DEMO_QUESTIONS):
            cursor.execute("""
            INSERT INTO questions (workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workbook_id,
                q["question_num"],
                q["question_type"],
                q["category"],
                q["stem"],
                json.dumps(q["options"], ensure_ascii=False),
                q["answer"],
                q["explanation"],
                idx + 1
            ))
        
        conn.commit()
        print(f"Seeded default workbook with {len(DEMO_QUESTIONS)} questions.")
    else:
        print("Default workbook already exists.")
        
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_default_workbook()
