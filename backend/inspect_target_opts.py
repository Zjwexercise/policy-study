import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

gt = json.load(open('backend/parsed_ch0_ch1.json', encoding='utf-8'))
indices = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,27,29,30,32,41,46]
for idx in indices:
    q = gt[idx]
    print(f"=== Index {idx} Q{q['num']} [{q['ans']}] ===")
    print("Stem:", q['stem'][:60])
    for o in q['opts']:
        print(f"  {o['key']}: {o['value']}")
    print("Expl:", q['exp'][:60])
