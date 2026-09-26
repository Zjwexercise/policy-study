import glob
import os
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def find_chapter_starts(folder):
    files = sorted(glob.glob(os.path.join(folder, '*.txt')))
    starts = []
    current_chap = None

    for f in files:
        pnum = int(os.path.basename(f).split('_')[1].split('.')[0])
        with open(f, 'r', encoding='utf-8-sig') as fp:
            lines = [l.strip() for l in fp if l.strip()]

        for l in lines[:10]:
            # 标准化
            l_clean = re.sub(r'\s+', '', l)
            m = re.search(r'(第[一二三四五六七八九十\d]+章|导论)(.*)', l_clean)
            if m:
                chap_name = m.group(1) + (m.group(2)[:15] if m.group(2) else '')
                if chap_name != current_chap:
                    starts.append((pnum, chap_name, l))
                    current_chap = chap_name
                break
    return starts

if __name__ == '__main__':
    print("=== Q Chapter Starts ===")
    for p, c, raw in find_chapter_starts('backend/1000_q_txt'):
        print(f"P{p:3d}: {c:25s} | Raw: {raw}")

    print("\n=== Exp Chapter Starts ===")
    for p, c, raw in find_chapter_starts('backend/1000_exp_txt'):
        print(f"P{p:3d}: {c:25s} | Raw: {raw}")
