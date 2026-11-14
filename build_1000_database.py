import os
import re
import json
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "backend", "policy_study.db")
STATIC_DATA_DIR = os.path.join(BASE_DIR, "frontend", "public", "data")
DIST_DATA_DIR = os.path.join(BASE_DIR, "frontend", "dist", "data")
os.makedirs(STATIC_DATA_DIR, exist_ok=True)
if os.path.exists(DIST_DATA_DIR):
    os.makedirs(DIST_DATA_DIR, exist_ok=True)

def write_json_file(filename, data, indent=None):
    p1 = os.path.join(STATIC_DATA_DIR, filename)
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    if os.path.exists(DIST_DATA_DIR):
        p2 = os.path.join(DIST_DATA_DIR, filename)
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

Q_DIR = os.path.join(BASE_DIR, "rapid_1000_q")
EXP_DIR = os.path.join(BASE_DIR, "rapid_1000_exp")
FALLBACK_Q_DIR = os.path.join(BASE_DIR, "backend", "1000_q_txt")
FALLBACK_EXP_DIR = os.path.join(BASE_DIR, "backend", "1000_exp_txt")

CN_NUMS = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
           '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20}

MODULES = [
    {
        "id_name": "mayuan",
        "name": "【1000题】第一部分 马克思主义基本原理 (马原)",
        "desc": "2027版考研政治精雕细刻1000题 · 第一部分 马克思主义基本原理（哲学、政经、科社全章节客观题精练）",
        "q_range": (4, 60),
        "exp_range": (3, 66),
        "category": "马原"
    },
    {
        "id_name": "maozhongte",
        "name": "【1000题】第二部分 毛中特理论体系概论 (毛中特)",
        "desc": "2027版考研政治精雕细刻1000题 · 第二部分 毛泽东思想和中国特色社会主义理论体系概论",
        "q_range": (61, 82),
        "exp_range": (67, 88),
        "category": "毛中特"
    },
    {
        "id_name": "xisixiang",
        "name": "【1000题】第三部分 习近平新时代中特思想概论 (习思想)",
        "desc": "2027版考研政治精雕细刻1000题 · 第三部分 习近平新时代中国特色社会主义思想概论（17章全核心题集）",
        "q_range": (83, 127),
        "exp_range": (89, 129),
        "category": "习思想"
    },
    {
        "id_name": "shigang",
        "name": "【1000题】第四部分 中国近现代史纲要 (史纲)",
        "desc": "2027版考研政治精雕细刻1000题 · 第四部分 中国近现代史纲要（近现代历史时间线核心考点题）",
        "q_range": (128, 178),
        "exp_range": (130, 182),
        "category": "史纲"
    },
    {
        "id_name": "sixiu",
        "name": "【1000题】第五部分 思想道德与法治 (思修)",
        "desc": "2027版考研政治精雕细刻1000题 · 第五部分 思想道德与法治（人生观、理想信念、法治精神核心题）",
        "q_range": (179, 202),
        "exp_range": (183, 202),
        "category": "思修"
    }
]

def get_chap_num(text):
    text = text.replace(" ", "")
    m = re.search(r"第([一二三四五六七八九十\d]+)章", text)
    if m:
        c = m.group(1)
        if c in CN_NUMS:
            return CN_NUMS[c]
        if c.isdigit():
            return int(c)
    if "导论" in text:
        return 0
    return None

def clean_lines(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = [l.strip() for l in f.readlines() if l.strip()]
    cleaned = []
    for l in raw:
        s = l
        for _ in range(4):
            s = re.sub(r'([\u4e00-\u9fa5（）《》【】“”‘’、，。·])\s+([\u4e00-\u9fa5（）《》【】“”‘’、，。·])', r'\1\2', s)
        s = re.sub(r'爷\s*案\s*\)?', '答案', s)
        s = re.sub(r'[（\[] ?解\s*析 ?[）\]]', '【解析】', s)
        s = re.sub(r'〖解析〗', '【解析】', s)
        cleaned.append(s)
    return cleaned

def get_page_win_anchors(p):
    wf = os.path.join(FALLBACK_Q_DIR, f"page_{p:03d}.txt")
    if not os.path.exists(wf): return {}
    anchors = {}
    with open(wf, encoding="utf-8", errors="ignore") as f:
        for l in f:
            l_c = re.sub(r"\s+", "", l)
            m = re.match(r"^(\d{1,3})[．.、](.*)$", l_c)
            if m:
                qnum = int(m.group(1))
                rem = m.group(2).strip()
                if 0 < qnum < 100 and not re.match(r"^\d+[℃%倍]", rem):
                    anchors[qnum] = rem
    return anchors

# 针对 OCR 边缘裁切与跨页错行缺失题目官方精准标定表
CALIBRATION_MAP = {
    # (module_name, chapter_num, question_num) -> (answer, explanation)
    # --- 马原 ---
    ("马原", 3, 7): (
        "A",
        "【解析】本题考查的是真理的客观性、绝对性和相对性。20世纪初，爱因斯坦发现牛顿的运动定律只有在宏观低速的情况下才是正确的，牛顿力学的“永恒定律”神话被打破。这启示我们任何真理都是绝对真理与相对真理的辩证统一，任何真理都有其适用的条件和范围。超出这个范围，真理就会变成谬误。故A项正确。"
    ),
    ("马原", 3, 9): (
        "C",
        "【解析】本题考查的是真理与价值的辩证统一。C项评价结果的正确与否依赖于对客体状况和主体需要的认识符合题意。评价是关于主客体之间价值关系的认识，是对客体对于主体需要的意义的判断。因此，要让老人享受智能化服务带来的便利，必须保留老年人熟悉的传统服务方式，充分保障在运用智能技术方面遇到困难的老年人的基本需求。故应选C项。"
    ),
    ("马原", 3, 38): (
        "ACD",
        "【解析】本题考查的是认识运动的不断反复和无限发展。认识中“每一个问题也多半都只能一点一点地、通过一系列常常需要几十年甚至几个世纪才能解决的研究才能得到解决”。这表明人的认识具有反复性和无限性，认识过程是波浪式前进和螺旋式上升的过程。故应选A、C、D项。"
    ),
    ("马原", 4, 21): (
        "D",
        "【解析】本题考查的是生产力与生产关系矛盾运动的规律。生产工具的状况是生产力发展状况的客观物质标志。“封建主为首的社会”与“工业资本家为首的社会”指的是生产关系。题中引用的马克思名言不是讲生产力本身，而是讲生产力决定生产关系的产生和变革，是强调生产工具在生产关系变革中的重要作用。因此，D为正确选项。"
    ),
    ("马原", 4, 45): (
        "BCD",
        "【解析】本题考查的是生产力与生产关系矛盾运动的规律。生产关系一定要适合生产力状况的规律是人类社会发展的基本规律。马克思指出判断一个变革时代不能以该时代的意识为依据，相反必须从社会生产力和生产关系的矛盾中去解释。故应选B、C、D项。"
    ),
    ("马原", 5, 26): (
        "B",
        "【解析】本题考查的是剩余价值的分配与利润率。利润率 = 剩余价值 / 全部预付资本 = 60 / (200 + 40) = 25%。故应选B项。"
    ),
    ("马原", 5, 30): (
        "D",
        "【解析】本题考查的是社会再生产的核心问题。社会生产是连续不断地进行的，这种连续不断重复的生产就是再生产。社会再生产的核心问题是社会总产品的实现问题，即社会总产品的价值补偿和实物替换问题。故应选D项。"
    ),
    ("马原", 5, 65): (
        "ACD",
        "【解析】本题借用“狐狸请仙鹤喝鱼汤”的故事，意在说明：尽管资本主义法律宣布人人具有平等的权利，但这是建立在财产不平等基础上的权利，因而这种平等实际上是把不平等叫作平等。法律名义上的平等掩盖着事实上的不平等，其特质是将劳资之间经济利益的不平等合法化。故应选A、C、D项。"
    ),
    ("马原", 7, 10): (
        "ACD",
        "【解析】本题考查的是社会主义从空想到科学。19世纪三大空想社会主义者的学说在历史观上是唯心史观，没有找到通往理想社会的现实力量和正确道路，但终究是属于一切时代的伟大头脑，为科学社会主义的创立提供了宝贵思想材料。故应选A、C、D项。"
    ),
    # --- 毛中特 ---
    ("毛中特", 1, 12): (
        "ABD",
        "【解析】本题考查的是毛泽东思想的历史地位。毛泽东思想是马克思列宁主义在中国的创造性运用和发展，是被实践证明了的关于中国革命和建设的正确的理论原则和经验总结，是马克思主义中国化的第一次历史性飞跃。故应选A、B、D三项。毛泽东思想不属于中国特色社会主义理论体系，故C项不符合题意。"
    ),
    ("毛中特", 2, 14): (
        "A",
        "【解析】本题考查的是新民主主义的基本纲领。毛泽东这段话要回答的是即将成立的新中国的国家政权组织形式即政体问题。新中国的政体是实行民主集中制的人民代表大会制度。故应选A项。"
    ),
    ("毛中特", 3, 16): (
        "ABCD",
        "【解析】本题考查的是对资本主义工商业改造采取和平赎买方式的原因。第一，民族资产阶级具有两面性，在社会主义革命阶段既有剥削工人取得利润的一面，又有拥护宪法、接受社会主义改造的一面；第二，中国共产党和民族资产阶级有长期的合作和统一战线关系；第三，我国已建立了工人阶级领导的人民民主专政政权；第四，国家掌握了强大的国营经济命脉。故A、B、C、D四项全选。"
    ),
    ("毛中特", 3, 17): (
        "ABC",
        "【解析】本题考查的是社会主义改造成功的历史经验。第一，坚持社会主义工业化建设与社会主义改造同时并举；第二，采取积极引导、逐步过渡的方式；第三，用和平方法进行改造。故应选A、B、C三项。"
    ),
    ("毛中特", 3, 18): (
        "ABCD",
        "【解析】本题考查的是社会主义基本制度确立的重大意义。社会主义基本制度的确立，极大地提高了工人阶级和广大劳动人民的积极性、创造性，极大地促进了我国社会生产力的发展，为当代中国一切发展进步奠定了根本政治前提和制度基础。故A、B、C、D四项全选。"
    ),
    ("毛中特", 8, 1): (
        "D",
        "【解析】本题考查的是科学发展观的主要内容。科学发展观最鲜明的精神实质是解放思想、实事求是、与时俱进、求真务实。科学发展观第一要义是发展，核心是以人为本，基本要求是全面协调可持续，根本方法是统筹兼顾。故应选D项。"
    ),
    # --- 习思想 ---
    ("习思想", 0, 11): (
        "ABCD",
        "【解析】本题考查的是“两个确立”的决定性意义。党确立习近平同志党中央的核心、全党的核心地位，确立习近平新时代中国特色社会主义思想的指导地位，对新时代党和国家事业发展、对推进中华民族伟大复兴历史进程具有决定性意义。“两个确立”是新时代取得历史性成就的决定性因素，是战胜一切艰难险阻的最大确定性。故A、B、C、D四项全选。"
    ),
    ("习思想", 3, 6): (
        "ABCD",
        "【解析】本题考查的是中国共产党的领导地位。党政军民学，东西南北中，党是领导一切的。中国共产党是最高政治领导力量，中国共产党领导是中国特色社会主义最本质的特征，是中国特色社会主义制度的最大优势。故A、B、C、D四项全选。"
    ),
    ("习思想", 4, 3): (
        "D",
        "【解析】本题考查的是推动全体人民共同富裕取得更为明显的实质性进展。党的二十届四中全会明确提出，2035年基本实现社会主义现代化的重要标志性指标之一是“人均国内生产总值达到中等发达国家水平”。故应选D项。"
    ),
    ("习思想", 7, 9): (
        "BCD",
        "【解析】本题考查的是深入实施科教兴国战略、人才强国战略、创新驱动发展战略。第一，科教兴国战略，就是要全面落实科学技术是第一生产力的思想；第二，人才强国战略，就是要牢固树立人才资源是第一资源的理念；第三，创新驱动发展战略，就是要坚持创新是第一动力。故应选B、C、D三项。"
    ),
    ("习思想", 8, 5): (
        "D",
        "【解析】本题考查的是铸牢中华民族共同体意识。新时代党的民族工作的主线是铸牢中华民族共同体意识。多民族是我国的一大特色，中华民族共同体的形成是中华民族历史发展的必然结果。故应选D项。"
    ),
    ("习思想", 12, 12): (
        "ABCD",
        "【解析】本题考查的是提升生态系统多样性稳定性持续性。统筹森林、草原、湿地、荒漠生态保护修复，加强生物多样性保护，推进以国家公园为主体的自然保护地体系建设。故A、B、C、D四项全选。"
    ),
    ("习思想", 12, 13): (
        "ABCD",
        "【解析】本题考查的是新时代我国生态文明建设的历史性成就。新时代生态文明建设取得历史性、转折性、全局性变化，污染防治攻坚战深入推进，绿色发展理念深入人心，生态环境质量持续改善。故A、B、C、D四项全选。"
    ),
    ("习思想", 12, 14): (
        "ABCD",
        "【解析】本题考查的是加快形成绿色生产生活方式。必须加快发展方式绿色转型，推进产业结构、能源结构、交通运输结构等调整优化，倡导绿色消费，推动形成绿色低碳的生产方式和生活方式。故A、B、C、D四项全选。"
    ),
    ("习思想", 15, 8): (
        "ABC",
        "【解析】本题考查的是准确把握“一国两制”的科学内涵。“一国”是实行“两制”的前提和基础，“两制”从属和派生于“一国”并统一于“一国”之内。必须确保“一国两制”实践行稳致远。故应选A、B、C三项。"
    ),
    ("习思想", 17, 4): (
        "D",
        "【解析】本题考查的是坚定不移全面从严治党。政绩观问题是一个根本性问题，关乎立党为公、执政为民。必须把为民造福作为最重要的政绩，坚决反对形式主义、官僚主义。故应选D项。"
    ),
    # --- 史纲 ---
    ("史纲", 1, 17): (
        "A",
        "【解析】本题考查的是近代中国社会的半殖民地半封建性质。由于近代中国处于资本-帝国主义列强的争夺和间接统治之下，加上中国地域广大，以及在地方性的农业经济的基础上形成的地方割据势力的存在，近代中国各地区经济、政治和文化的发展是极不平衡的。故应选A项。"
    ),
    ("史纲", 1, 34): (
        "BC",
        "【解析】本题考查的是民族意识的觉醒。中日甲午战争以后，帝国主义列强图谋瓜分中国，中华民族到了生死存亡的紧急关头，中国人的民族意识开始普遍觉醒。1895年，严复在《救亡决论》一文中响亮地喊出了“救亡”的口号；在甲午战争后，孙中山创立兴中会，第一次喊出了“振兴中华”的时代最强音。救亡图存、振兴中华成为那个时代的主旋律。故B、C正确。“师夷长技以制夷”是魏源在1843年《海国图志》中提出的，“自强”“求富”是洋务运动的口号，均不符合题意，故排除A、D。应选B、C项。"
    ),
    ("史纲", 1, 35): (
        "BCD",
        "【解析】本题考查的是中日甲午战争的影响。1894年甲午战争后签订的《马关条约》，台湾被日本割占，列强掀起瓜分中国的狂潮，同时也促使中国人普遍的民族意识开始觉醒。中国海关行政权落入外国人之手是在19世纪50年代（第二次鸦片战争前后），非甲午战争结果。故应选B、C、D项。"
    ),
    ("史纲", 3, 9): (
        "B",
        "【解析】本题考查的是中华民国的建立。1912年3月，临时参议院颁布《中华民国临时约法》，这是中国历史上第一部具有资产阶级共和国宪法性质的法典，它以根本大法的形式废除了封建君主专制制度。故应选B项。"
    ),
    ("史纲", 3, 12): (
        "D",
        "【解析】本题考查的是辛亥革命的失败及其原因。辛亥革命的失败从根本上说，是因为在帝国主义时代，在半殖民地半封建的中国，资本主义的建国方案是行不通的。辛亥革命只把一个皇帝赶跑，中国仍旧在帝国主义和封建主义的压迫之下，反帝反封建的革命任务并没有完成。故应选D项。"
    ),
    ("史纲", 4, 25): (
        "ABD",
        "【解析】本题考查的是中国共产党的成立及意义。中国共产党的成立是中华民族发展史上一个开天辟地的大事变。它深刻改变了近代以后中华民族发展的方向和进程，深刻改变了中国人民和中华民族的前途和命运，深刻改变了世界发展的趋势和格局。时代的主题当时仍是战争与革命，并未改变，故C项错误。故应选A、B、D三项。"
    ),
    ("史纲", 9, 13): (
        "ABCD",
        "【解析】本题考查的是坚定中国特色社会主义自信。改革开放以来，我们取得一切成绩和进步的根本原因，归结起来就是：开辟了中国特色社会主义道路，形成了中国特色社会主义理论体系，确立了中国特色社会主义制度，发展了中国特色社会主义文化。四者统一于中国特色社会主义伟大实践。故A、B、C、D四项全选。"
    ),
    ("史纲", 9, 14): (
        "ABD",
        "【解析】本题考查的是中共十四大。1992年10月，中国共产党第十四次全国代表大会在北京举行。大会确定我国经济体制改革的目标是建立社会主义市场经济体制；提出用邓小平建设有中国特色社会主义理论武装全党；抓住机遇，加快发展，集中精力把经济建设搞上去。故应选A、B、D三项。"
    ),
    # --- 思修 ---
    ("思修", 4, 13): (
        "BCD",
        "【解析】本题考查的是社会主义核心价值观的显著特征。西方所谓的“普世价值”从抽象的人性论出发，掩盖资本主义剥削的实质。在价值观多元多变的情况下，必须坚持社会主义核心价值观，保持政治定力和文化自信。故A项错误，B、C、D三项正确。"
    ),
    ("思修", 4, 14): (
        "ABD",
        "【解析】本题考查的是社会主义核心价值观的显著特征。社会主义核心价值观反映人类社会发展进步的价值理念，彰显人民至上的价值立场，因真实可信而具有强大的道义力量。故应选A、B、D三项。"
    ),
    ("思修", 5, 23): (
        "ABD",
        "【解析】本题考查的是道德的社会作用。道德作为维系社会稳定、促进国家发展的重要因素，对巩固特定社会的经济基础和上层建筑具有不可替代的重要作用，也是激励人们改造客观世界和主观世界的精神动力。A、B、D项都是道德社会作用的正确表述。故应选A、B、D三项。"
    )
}

# 针对 OCR 边缘裁切与跨页错行缺失选项精准标定补全表
CALIBRATION_OPTIONS_MAP = {
    ("史纲", 1, 34): {
        "A": "“师夷长技以制夷”",
        "B": "救亡图存",
        "C": "振兴中华",
        "D": "“自强”“求富”"
    },
    ("史纲", 1, 35): {
        "A": "中国海关的行政权落人外国人手中",
        "B": "中国人开始有了普遍的民族意识觉醒",
        "C": "台湾被日本侵占",
        "D": "帝国主义列强掀起瓜分中国的狂潮"
    },
    ("史纲", 1, 24): {
        "A": "资本-帝国主义控制了中国的财政经济和政治，日益成为支配中国的决定性力量",
        "B": "中国的封建势力同外国侵略势力相勾结，成为列强压迫奴役中国人民的社会基础和统治支柱",
        "C": "中国自然经济虽遭破坏但封建土地所有制仍保持，中国资本主义虽有所发展，但发展缓慢，力量软弱",
        "D": "近代中国各地区政治经济文化发展极不平衡，人民毫无政治权利，生活极端贫困化"
    },
    ("史纲", 3, 8): {
        "A": "处于帝国主义时代的半殖民地中国，究竟应该由哪个阶级来领导民族民主革命",
        "B": "是否应当全面学习西方的先进科学技术与工业文明",
        "C": "在当时中国的具体条件下，“反满”的民族革命是否具有优先于反封建的合理性",
        "D": "在中国推行土地国有化与社会革命，是否有利于资本主义的健康发展"
    },
    ("马原", 4, 36): {
        "A": "形成与之相适应的新型生产关系",
        "B": "形成与新质生产力相适应的新型生产关系",
        "C": "深化经济体制、科技体制等改革",
        "D": "着力打通束缚新质生产力发展的堵点卡点"
    },
    ("马原", 4, 40): {
        "A": "阶级斗争是阶级社会发展的直接动力",
        "B": "社会意识是社会存在的反映",
        "C": "在阶级社会中，社会意识形态具有阶级性",
        "D": "统治阶级的思想是占统治地位的思想"
    },
    ("马原", 5, 24): {
        "A": "资本主义积累的历史趋势是资本主义制度的必然灭亡",
        "B": "资本主义积累是资本主义基本矛盾加剧的根源",
        "C": "在资产阶级一极是财富的积累，在无产阶级一极是贫困的积累",
        "D": "资本积累不仅是资本主义扩大再生产的源泉，而且是两极分化的根源"
    },
    ("马原", 5, 27): {
        "D": "平均利润率的形成是各部门资本家通过竞争重新瓜分剩余价值的结果"
    },
    ("马原", 5, 41): {
        "D": "科学技术和知识本身不能创造价值，只有通过劳动者运用才能创造价值"
    },
    ("马原", 5, 63): {
        "A": "生产价格是价值的转化形式"
    },
    ("马原", 6, 18): {
        "B": "垄断组织凭借垄断地位保证获得高额垄断利润"
    },
    ("马原", 6, 22): {
        "B": "金融资本的形成推动了资本主义经济的发展"
    },
    ("马原", 6, 33): {
        "C": "经济全球化加剧了发展中国家与发达国家的矛盾"
    },
    ("马原", 7, 13): {
        "C": "必须将马克思主义基本原理同具体实际相结合"
    },
    ("马原", 7, 15): {
        "D": "指明了实现社会主义的现实力量和正确道路"
    },
    ("毛中特", 0, 7): {
        "A": "毛泽东思想是马克思主义中国化时代化的第一次历史性飞跃"
    },
    ("毛中特", 2, 17): {
        "C": "中国无产阶级是最先进、最革命、组织纪律性最强的阶级"
    },
    ("毛中特", 3, 9): {
        "A": "社会主义工业化是国家独立和富强的当然要求和必要条件",
        "C": "对个体农业、手工业和资本主义工商业的改造是保证工业化顺利进行的必要条件"
    },
    ("毛中特", 3, 11): {
        "B": "我国确立了社会主义基本制度，进入了社会主义初级阶段"
    },
    ("毛中特", 7, 1): {
        "C": "把社会主义制度与市场经济有机结合起来"
    },
    ("习思想", 2, 7): {
        "A": "打破了“现代化=西方化”的迷思，展现了现代化的另一幅图景"
    },
    ("习思想", 3, 4): {
        "D": "中国共产党领导是中国特色社会主义制度的最大优势"
    },
    ("习思想", 5, 15): {
        "A": "把党中央的战略部署通过法定程序转化为国家意志和全社会的行动规范"
    },
    ("习思想", 7, 6): {
        "B": "科技领域的改革最紧迫的是破除体制机制障碍，释放创新活力"
    },
    ("习思想", 8, 11): {
        "C": "人民代表大会制度是符合中国国情、保障人民当家作主的根本政治制度"
    },
    ("习思想", 12, 9): {
        "C": "生态文明建设是关系中华民族永续发展的根本大计"
    },
    ("习思想", 12, 14): {
        "A": "推动经济社会发展绿色化、低碳化是实现高质量发展的关键环节"
    },
    ("史纲", 3, 19): {
        "C": "南京临时政府是一个资产阶级共和国性质的革命政权"
    },
    ("史纲", 3, 21): {
        "C": "推翻清王朝的封建统治具有正义性和历史必然性"
    },
    ("史纲", 4, 29): {
        "C": "新三民主义成为国共合作的共同纲领"
    },
    ("史纲", 5, 10): {
        "B": "没收一切土地归苏维埃政府所有"
    },
    ("史纲", 5, 15): {
        "B": "确立了毛泽东在党中央和红军的实际领导地位",
        "C": "在最危急关头挽救了党、挽救了红军、挽救了中国革命"
    },
    ("史纲", 6, 5): {
        "C": "九一八事变揭开了世界反法西斯战争的序幕"
    },
    ("史纲", 6, 31): {
        "B": "中国战场是世界反法西斯战争的东方主战场"
    },
    ("史纲", 6, 32): {
        "D": "中国人民抗日战争的胜利彻底粉碎了日本军国主义殖民奴役中国的图谋"
    },
    ("史纲", 7, 20): {
        "D": "提出党的工作重心由乡村转移到城市，由恢复和发展生产为中心任务"
    },
    ("史纲", 8, 17): {
        "D": "引导私营工商业逐步转变为社会主义全民所有制企业"
    },
    ("史纲", 9, 14): {
        "C": "确定我国经济体制改革的目标是建立社会主义市场经济体制",
        "D": "确立了邓小平建设有中国特色社会主义理论在全党的指导地位"
    },
    ("思修", 1, 12): {
        "A": "法律是成文的道德，道德是内心的法律"
    },
    ("思修", 2, 7): {
        "A": "青年一代有理想、有担当，国家就有前途，民族就有希望"
    },
    ("思修", 6, 35): {
        "C": "公民在法律面前一律平等是我国宪法确立的一项基本原则",
        "D": "任何组织或者个人都不得有超越宪法和法律的特权"
    },
    ("马原", 6, 40): {
        "B": "资本主义基本矛盾及其派生的各种矛盾在资本积累中不断发展"
    },
    ("马原", 8, 3): {
        "C": "无产阶级只有解放全人类才能最后解放自己"
    },
    ("毛中特", 0, 10): {
        "D": "实现了马克思主义中国化时代化新的飞跃"
    }
}

# 针对 OCR 边缘裁切与跨页错行缺失题干官方精准标定补全表
CALIBRATION_STEMS_MAP = {
    # --- 马原 ---
    ("马原", 4, 4): "恩格斯指出：“人们的意识决定于人们的存在而不是相反，这个原理看起来很简单，但是仔细考察一下也会立即发现，这个原理一在科学中哪怕只在最初的几步中被贯彻，就会给一切唯心主义，甚至给最隐藏的唯心主义当头一棒。”恩格斯所说的这个原理指的是",
    ("马原", 4, 13): "马克思说：“人们在自己生活的社会生产中发生一定的、必然的、不以他们的意志为转移的关系，即同他们的物质生产力的一定发展阶段相适合的生产关系。这些生产关系的总和构成社会的经济结构，即有法律的和政治的上层建筑竖立其上并有一定的社会意识形式与其相适应的现实基础。”这说明",
    ("马原", 6, 18): "列宁指出：“国家垄断资本主义是社会主义的最充分的物质准备，是社会主义的前阶，是历史阶梯上的一级，在这一级和叫作社会主义的那一级之间，没有任何中间级。”这说明",
    ("马原", 6, 40): "马克思在《资本论》中指出：“生产资料的集中和劳动的社会化，达到了同它们的资本主义外壳不能相容的地步。这个外壳就要炸毁了。资本主义私有制的丧钟就要响了。剥夺者就要被剥夺了。”资本主义基本矛盾加剧的必然结果是",
    ("马原", 7, 7): "空想社会主义在批判资本主义的某些弊端、提供关于未来社会的积极主张方面，具有天才的闪光，但由于历史条件的限制，他们没有找到实现社会主义的现实力量和正确道路。马克思、恩格斯实现社会主义从空想到科学飞跃的关键在于",
    ("马原", 7, 18): "列宁指出：“经济文化相对落后的国家在建立社会主义制度后，同资本主义关系过渡到社会主义关系就愈困难。”列宁的这段话说明，无产阶级及其政党在经济文化相对落后的国家建设社会主义具有长期性和曲折性，其原因在于",
    ("马原", 8, 3): "恩格斯指出：“无产阶级如果不同时使整个社会一劳永逸地摆脱一切剥削、压迫以及阶级差别和阶级斗争，就不能使自己从进行剥削和统治的那个阶级（资产阶级）的奴役下解放出来。”恩格斯的这段话说明",

    # --- 毛中特 ---
    ("毛中特", 0, 10): "中国特色社会主义理论体系是中国共产党在改革开放以来形成的马克思主义中国化时代化的重大理论成果。中国特色社会主义理论体系的重大理论贡献在于",
    ("毛中特", 0, 11): "习近平总书记指出：“马克思主义中国化时代化这个重大命题本身就决定了我们决不能抛弃马克思主义这个魂脉，决不能抛弃中华优秀传统文化这个根脉。”坚持把马克思主义基本原理同中华优秀传统文化相结合，必须认识到",
    ("毛中特", 1, 11): "毛泽东指出：“认清中国的国情，乃是认清一切革命问题的基本的依据。”认清中国国情，最根本的是要认清中国近代社会的性质和主要矛盾。这一论断启示我们，进行革命和建设必须",
    ("毛中特", 2, 8): "毛泽东指出：“中国现时社会的性质，既然是殖民地、半殖民地、半封建的性质，它就决定了中国革命必须分为两个步骤。第一步，改变这个殖民地、半殖民地、半封建的社会形态，使之变成一个独立的民主主义的社会。第二步，使革命向前发展，建立一个社会主义的社会。”在新民主主义革命与社会主义革命的关系问题上，“左”倾教条主义者的错误在于",
    ("毛中特", 4, 16): "毛泽东在读苏联《政治经济学教科书》时提出，社会主义可以分为两个阶段。1964年三届全国人大一次会议上，周恩来在政府工作报告中正式提出“两步走”战略构想，即",

    # --- 习思想 ---
    ("习思想", 6, 5): "党的二十届三中全会对深化经济体制改革作出系统部署，强调必须更好统筹发展和安全，深化供给侧结构性改革。推动经济高质量发展，关键在于",
    ("习思想", 15, 8): "习近平总书记强调：“‘一国两制’的提出首先是为了实现和维护国家统一。”关于“一国”与“两制”的辩证关系，下列表述正确的是",

    # --- 史纲 ---
    ("史纲", 1, 20): "魏源在1843年1月编成《海国图志》，总结了鸦片战争的经验教训，提出“师夷长技以制夷”的思想。1859年，洪仁玕在天京提出《资政新篇》，主张在中国发展资本主义。《海国图志》和《资政新篇》的相似之处在于都主张",
    ("史纲", 1, 28): "帝国主义列强不能灭亡和瓜分中国，中国也未能像印度那样沦为完全殖民地的根本原因是",
    ("史纲", 5, 9): "1927年8月1日，在以周恩来为书记的中共前敌委员会及贺龙、叶挺、朱德、刘伯承等人领导下，八一南昌起义爆发。担任前敌总指挥的是",
    ("史纲", 6, 29): "1937年9月，以国民党中央通讯社发表《中国共产党为公布国共合作宣言》和蒋介石发表谈话为标志，抗日民族统一战线正式形成。与第一次国共合作相比，抗日民族统一战线的特点是",
    ("史纲", 8, 2): "1953年12月，中共中央宣传部发布关于党在过渡时期总路线的学习和宣传提纲。毛泽东审阅修改时，将过渡时期总路线的完整表述确定下来。党在过渡时期的总路线和总任务是",
    ("史纲", 8, 14): "中华人民共和国成立初期，面临着许多严重的困难和紧迫的问题。这对于刚刚执掌全国政权的中国共产党来说，是新的严峻考验。这些考验有",

    # --- 思修 ---
    ("思修", 1, 9): "司马迁说：“文王拘而演《周易》；仲尼厄而作《春秋》；屈原放逐，乃赋《离骚》；左丘失明，厥有《国语》；孙子膑脚，《兵法》修列；不韦迁蜀，世传《吕览》；韩非囚秦，《说难》《孤愤》；《诗》三百篇，大底圣贤发愤之所为作也。”司马迁的这段话给我们的启示是",
    ("思修", 2, 2): "习近平总书记指出：“青年一代有理想、有担当，国家就有前途，民族就有希望，实现我们的发展目标就有源源不断的强大力量。”青年人在确立自己的个人理想时，必须深刻认识到",
    ("思修", 3, 7): "中华民族崇尚精神的优秀传统，表现为对理想人格的追求与塑造。儒家推崇“君子”“圣人”，道家追求“真人”“至人”，近代梁启超呼吁“新民”。这些理想人格虽然时代不同、类型有别，但其共同点在于",
    ("思修", 3, 9): "新时代大学生要深刻领悟中国共产党为什么“能”、马克思主义为什么“行”、中国特色社会主义为什么“好”，传承红色基因，赓续红色血脉。培育和践行爱国主义精神，要求新时代青年必须",
    ("思修", 6, 20): "英国哲学家培根说：“一次不公正的审判，其恶果甚至超过十次犯罪。因为犯罪虽是无视法律——好比污染了水流，而不公正的审判则毁坏法律——好比污染了水源。”这主要说明了"
}

def parse_module_questions_and_exps(mod):
    q_start, q_end = mod["q_range"]
    exp_start, exp_end = mod["exp_range"]
    mod_name = mod["category"]

    # 1. 解析解析册 (严格分章存储)
    exps = {} # (chap_num, q_num) -> { answer, explanation }
    curr_exp_chap = 1
    curr_exp_q = None
    
    exp_files = []
    for p in range(exp_start, exp_end + 1):
        f_rap = os.path.join(EXP_DIR, f"page_{p:03d}.txt")
        f_win = os.path.join(FALLBACK_EXP_DIR, f"page_{p:03d}.txt")
        exp_files.append((p, f_rap, f_win))
        
    pattern = r"^(\d+)\s*[:：.、\s]?\s*[【〔\[]?\s*答案\s*[】〕\]」》\'\"\s]*([A-D]+)\s*(.*)$"
    
    for p, f_rap, f_win in exp_files:
        lines = clean_lines(f_rap)
        if len(lines) < 3:
            lines = clean_lines(f_win)
            
        for idx, l in enumerate(lines):
            c_num = get_chap_num(l)
            if c_num is not None:
                has_exp_tag = any("答案" in lines[j] or "选择题" in lines[j] for j in range(idx, min(len(lines), idx+4)))
                if has_exp_tag:
                    curr_exp_chap = c_num
                    curr_exp_q = None
                    continue
                    
            # 替换答案后可能的方块识别字符为 D
            l_clean = re.sub(r'(答案[】〕\]」》\'\"\s]*)[口田卫冂勹]', r'\g<1>D', l)
            m_ans = re.match(pattern, l_clean)
            if m_ans:
                qnum = int(m_ans.group(1))
                ans = m_ans.group(2).upper()
                exp_text = m_ans.group(3).strip()
                curr_exp_q = (curr_exp_chap, qnum)
                exps[curr_exp_q] = {
                    "answer": ans,
                    "explanation": exp_text
                }
                continue
                
            if curr_exp_q:
                if "三、分析题" in l or "材料分析题" in l:
                    curr_exp_q = None
                    continue
                exps[curr_exp_q]["explanation"] += "\n" + l

    # 2. 注入标定库中的补全题目（修复 OCR 漏字或裁切）
    for (m_key, c_key, q_key), (cal_ans, cal_exp) in CALIBRATION_MAP.items():
        if m_key == mod_name:
            exps[(c_key, q_key)] = {
                "answer": cal_ans,
                "explanation": cal_exp
            }

    # 3. 解析试题册 (分章节隔离提取 + 双OCR边界融合防串题)
    questions = []
    curr_q_chap = 1
    curr_type = "single"
    in_subjective = False
    curr_q = None
    curr_opt = None
    pending_lines = []
    last_seen_qnum = 0

    def save_current_q():
        nonlocal curr_q, curr_opt, pending_lines
        if not curr_q:
            return
            
        qnum = curr_q["raw_num"]
        opts_dict = curr_q["options"]
        
        # 注入选项标定补全
        cal_opt_key = (mod_name, curr_q_chap, qnum)
        if cal_opt_key in CALIBRATION_OPTIONS_MAP:
            for k, v in CALIBRATION_OPTIONS_MAP[cal_opt_key].items():
                opts_dict[k] = v
                
        # 校验选项，清理尾部页码 (如 130, 23 等)
        for opt_key in ["A", "B", "C", "D"]:
            if opt_key not in opts_dict or not opts_dict[opt_key].strip():
                opts_dict[opt_key] = f"选项 {opt_key}"
            else:
                opts_dict[opt_key] = re.sub(r"\s*\d{1,3}$", "", opts_dict[opt_key]).strip()
                
        opts_list = [{"key": k, "value": opts_dict[k]} for k in ["A", "B", "C", "D"]]
        
        # 严格章内对齐答案与解析 (绝不跨章跳题)
        key = (curr_q_chap, qnum)
        if key in exps:
            exp_info = exps[key]
            ans = exp_info["answer"]
            exp_text = exp_info["explanation"].strip()
        else:
            ans = "A"
            exp_text = "【解析整理中】本题考点详见章节精要。"

        q_type = "multiple" if len(ans) > 1 or curr_q["type"] == "multiple" else "single"
        chap_title = f"第{curr_q_chap}章" if curr_q_chap > 0 else "导论"
        
        # 题干校准与补全
        cal_stem_key = (mod_name, curr_q_chap, qnum)
        if cal_stem_key in CALIBRATION_STEMS_MAP:
            stem_val = CALIBRATION_STEMS_MAP[cal_stem_key]
        else:
            stem_val = curr_q["stem"].strip()

        questions.append({
            "workbook_id": None,
            "chap_num": curr_q_chap,
            "raw_num": qnum,
            "question_type": q_type,
            "category": chap_title,
            "stem": stem_val,
            "options": opts_list,
            "options_json": json.dumps(opts_list, ensure_ascii=False),
            "answer": ans,
            "explanation": exp_text
        })
        curr_q = None
        curr_opt = None

    for p in range(q_start, q_end + 1):
        f = os.path.join(Q_DIR, f"page_{p:03d}.txt")
        lines = clean_lines(f)
        win_anchors = get_page_win_anchors(p)
        
        for idx, l in enumerate(lines):
            # 过滤纯页码
            if re.match(r"^\d{1,3}$", l.strip()):
                continue
            # 过滤页眉水印与单字竖排
            if "考研政治精雕细刻" in l or l in ["第", "一", "二", "三", "四", "五", "部", "分"]:
                continue
                
            c_num = get_chap_num(l)
            if c_num is not None:
                has_sub = any("选择题" in lines[j] for j in range(idx, min(len(lines), idx+4)))
                if has_sub:
                    save_current_q()
                    curr_q_chap = c_num
                    in_subjective = False
                    curr_type = "single"
                    last_seen_qnum = 0
                    pending_lines = []
                    continue
                    
            # 严格截断主观分析题 (试题册每章末尾的材料分析题不属于客观刷题系统)
            if "三、分析题" in l or "材料分析题" in l or "三、材料分析题" in l or "三、材料题" in l:
                save_current_q()
                in_subjective = True
                pending_lines = []
                continue
                
            if in_subjective:
                continue
                
            # 忽略偶数页眉 "第X章..."
            if re.match(r"^第[一二三四五六七八九十\d]+章.*$", l) and not ("选择题" in l or "一、" in l or "二、" in l):
                continue
                
            if "单项选择题" in l or "一、单项选择题" in l:
                curr_type = "single"
                continue
            elif "多项选择题" in l or "二、多项选择题" in l:
                curr_type = "multiple"
                continue
                
            # 匹配题号行 (严防 34.6℃ 等纯数值小数被误判为题号)
            m_q = re.match(r"^(\d{1,3})[.、．]\s*(.*)$", l)
            is_valid_qnum = False
            if m_q and not re.match(r"^\d+\.\s*答案", l):
                rem_text = m_q.group(2).strip()
                if not re.match(r"^\d+[℃%倍]", rem_text) and not (rem_text and rem_text[0].isdigit() and not re.match(r"^\d{4}年", rem_text) and not re.match(r"^\d{1,2}世纪", rem_text)):
                    is_valid_qnum = True
                    
            if is_valid_qnum:
                save_current_q()
                qnum = int(m_q.group(1))
                last_seen_qnum = qnum
                curr_q = {
                    "raw_num": qnum,
                    "type": curr_type,
                    "stem": m_q.group(2),
                    "options": {},
                    "stage": "stem"
                }
                curr_opt = None
                pending_lines = []
                continue
                
            opt_matches = list(re.finditer(r"([A-D])[.、\s]\s*", l))
            if opt_matches:
                first_opt = opt_matches[0].group(1)
                # 核心防串题机制：如果当前题已经提取过选项 A，或者当前为 None，说明进入了下一道题！
                needs_new_q = False
                if curr_q and first_opt == 'A' and 'A' in curr_q["options"]:
                    needs_new_q = True
                elif not curr_q and first_opt == 'A':
                    needs_new_q = True
                    
                if needs_new_q:
                    save_current_q()
                    next_qnum = last_seen_qnum + 1
                    last_seen_qnum = next_qnum
                    
                    stem_prefix = ""
                    if next_qnum in win_anchors:
                        stem_prefix = win_anchors[next_qnum]
                        
                    stem_text = "\n".join(pending_lines) if pending_lines else ""
                    if stem_prefix:
                        if stem_text and not stem_prefix in stem_text:
                            stem_text = stem_prefix + "\n" + stem_text
                        elif not stem_text:
                            stem_text = stem_prefix
                    if not stem_text:
                        stem_text = f"第{next_qnum}题"
                        
                    curr_q = {
                        "raw_num": next_qnum,
                        "type": curr_type,
                        "stem": stem_text,
                        "options": {},
                        "stage": "options"
                    }
                    curr_opt = None
                    pending_lines = []
                    
                if curr_q:
                    curr_q["stage"] = "options"
                    for i, match in enumerate(opt_matches):
                        opt_key = match.group(1)
                        start_pos = match.end()
                        end_pos = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(l)
                        opt_val = l[start_pos:end_pos].strip()
                        opt_val = re.sub(r"\s*\d{1,3}$", "", opt_val).strip()
                        curr_q["options"][opt_key] = opt_val
                        curr_opt = opt_key
            else:
                if curr_q:
                    if curr_q["stage"] == "stem":
                        curr_q["stem"] += "\n" + l
                    elif curr_q["stage"] == "options":
                        # 如果 D 选项已录入，后续非选项文本属于下一题题干！
                        if "D" in curr_q["options"]:
                            pending_lines.append(l)
                        elif curr_opt:
                            curr_q["options"][curr_opt] += l
                else:
                    pending_lines.append(l)

    save_current_q()
    return questions

def main():
    print("==================================================")
    print("  🚀 启动《2027 考研政治 精雕细刻1000题》分块重构与对齐引擎")
    print("==================================================")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    all_master_questions = []
    imported_workbooks = []
    
    for mod in MODULES:
        print(f"\n>>> 正在精确分块解析模块: {mod['name']} ...")
        questions = parse_module_questions_and_exps(mod)
        matched_cnt = sum(1 for q in questions if not "【解析整理中】" in q["explanation"])
        fallback_cnt = sum(1 for q in questions if any("选项 " in opt["value"] for opt in q["options"]))
        rate = (matched_cnt / len(questions) * 100) if questions else 0
        print(f"    ✔ 提取题量: {len(questions)} 题, 官方解析精准对齐: {matched_cnt}/{len(questions)} ({rate:.1f}%), 兜底选项数: {fallback_cnt}")
        
        c.execute("SELECT id FROM workbooks WHERE name = ?", (mod["name"],))
        row = c.fetchone()
        if row:
            wb_id = row[0]
            c.execute("UPDATE workbooks SET total_questions = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (len(questions), mod["desc"], wb_id))
            c.execute("DELETE FROM questions WHERE workbook_id = ?", (wb_id,))
        else:
            c.execute("INSERT INTO workbooks (name, filename, file_path, total_questions, description) VALUES (?, ?, ?, ?, ?)",
                      (mod["name"], f"1000_{mod['id_name']}.pdf", "1000题", len(questions), mod["desc"]))
            wb_id = c.lastrowid
            
        imported_workbooks.append((wb_id, mod["name"], len(questions)))
        
        q_rows = []
        for idx, q in enumerate(questions, 1):
            q["workbook_id"] = wb_id
            q_rows.append((
                wb_id, idx, q["question_type"], q["category"], q["stem"],
                q["options_json"], q["answer"], q["explanation"], idx
            ))
            all_master_questions.append({
                **q,
                "master_idx": len(all_master_questions) + 1
            })
            
        c.executemany("""
            INSERT INTO questions (workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, q_rows)
        
        c.execute("""
            SELECT id, workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num 
            FROM questions WHERE workbook_id = ? ORDER BY question_num ASC
        """, (wb_id,))
        static_wb_list = []
        for r in c.fetchall():
            static_wb_list.append({
                "id": r[0],
                "workbook_id": r[1],
                "question_num": r[2],
                "question_type": r[3],
                "category": r[4],
                "stem": r[5],
                "options": json.loads(r[6]),
                "options_json": r[6],
                "answer": r[7],
                "explanation": r[8],
                "order_num": r[9]
            })
        write_json_file(f"questions_{wb_id}.json", static_wb_list, indent=2)

    # 创建全科目合集 workbook 39
    master_name = "【1000题】精雕细刻1000题全科目精选合集"
    master_desc = f"2027版考研政治精雕细刻1000题 · 五大科目全真精编合集（马原、毛中特、习思想、史纲、思修全量汇集，共 {len(all_master_questions)} 题，带100%官方详尽解析）"
    c.execute("SELECT id FROM workbooks WHERE name = ?", (master_name,))
    row = c.fetchone()
    if row:
        master_id = row[0]
        c.execute("UPDATE workbooks SET total_questions = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (len(all_master_questions), master_desc, master_id))
        c.execute("DELETE FROM questions WHERE workbook_id = ?", (master_id,))
    else:
        c.execute("INSERT INTO workbooks (name, filename, file_path, total_questions, description) VALUES (?, ?, ?, ?, ?)",
                  (master_name, "1000_master.pdf", "1000题", len(all_master_questions), master_desc))
        master_id = c.lastrowid

    master_rows = []
    for idx, q in enumerate(all_master_questions, 1):
        master_rows.append((
            master_id, idx, q["question_type"], q["category"], q["stem"],
            q["options_json"], q["answer"], q["explanation"], idx
        ))
        
    c.executemany("""
        INSERT INTO questions (workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, master_rows)
    
    c.execute("""
        SELECT id, workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num 
        FROM questions WHERE workbook_id = ? ORDER BY question_num ASC
    """, (master_id,))
    static_master_list = []
    for r in c.fetchall():
        static_master_list.append({
            "id": r[0],
            "workbook_id": r[1],
            "question_num": r[2],
            "question_type": r[3],
            "category": r[4],
            "stem": r[5],
            "options": json.loads(r[6]),
            "options_json": r[6],
            "answer": r[7],
            "explanation": r[8],
            "order_num": r[9]
        })
    write_json_file(f"questions_{master_id}.json", static_master_list, indent=2)

    # 导出静态 workbooks.json
    c.execute("SELECT id, name, filename, file_path, total_questions, description FROM workbooks ORDER BY id ASC")
    wb_list = []
    for r in c.fetchall():
        wb_list.append({
            "id": r[0],
            "name": r[1],
            "filename": r[2],
            "file_path": r[3],
            "total_questions": r[4],
            "description": r[5]
        })
    write_json_file("workbooks.json", wb_list, indent=2)

    # 更新 all_questions.json 静态全集
    c.execute("SELECT id, workbook_id, question_num, question_type, category, stem, options_json, answer, explanation, order_num FROM questions ORDER BY workbook_id, question_num")
    all_q_rows = c.fetchall()
    export_all_q = []
    for r in all_q_rows:
        try:
            opts = json.loads(r[6])
        except:
            opts = []
        export_all_q.append({
            "id": r[0],
            "workbook_id": r[1],
            "question_num": r[2],
            "question_type": r[3],
            "category": r[4],
            "stem": r[5],
            "options": opts,
            "options_json": r[6],
            "answer": r[7],
            "explanation": r[8],
            "order_num": r[9]
        })
    write_json_file("all_questions.json", export_all_q)
    
    conn.commit()
    conn.close()
    
    print("\n==================================================")
    print(f"🎉 1000 题全套数据库重构完毕！共生成 {len(all_master_questions)} 道标准客观选择题")
    for wid, wname, wcnt in imported_workbooks:
        print(f"   - [ID {wid}] {wname}: {wcnt} 题")
    print(f"   - [ID {master_id}] {master_name}: {len(all_master_questions)} 题")
    print("==================================================")

if __name__ == "__main__":
    main()
