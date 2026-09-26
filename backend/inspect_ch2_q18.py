import sys
sys.stdout.reconfigure(encoding='utf-8')

from test_ch2_stitch import lines

for i, l in enumerate(lines[150:210]):
    print(f"{i+151:3d}: {repr(l)}")
