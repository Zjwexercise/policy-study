import sqlite3
import json
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 1. Load parsed ground truth for ch0 and ch1
with open('backend/parsed_ch0_ch1.json', encoding='utf-8') as f:
    ground_truth = json.load(f)

print(f"Loaded {len(ground_truth)} ground truth questions from ch0 and ch1.")

# Map each database ID to its exact corresponding question in ground_truth or manual exact text
# Let's inspect ground_truth indices first
for idx, q in enumerate(ground_truth):
    opt_keys = "".join([o['key'] for o in q['opts']])
    print(f"[{idx:2d}] Q{q['num']:2d} [{q['ans']:4s}] ({opt_keys}) | {q['stem'][:50]}")

