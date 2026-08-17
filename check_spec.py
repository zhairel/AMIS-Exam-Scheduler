#!/usr/bin/env python3
import re

with open("/home/tatsuya/Projects/AMIS/amis_exam_calendar/apply_new_assignments_and_solve.py", "r", encoding="utf-8") as f:
    code = f.read()

m = re.search(r'RAW_SPEC = """(.*?)"""', code, re.DOTALL)
spec = m.group(1)

blocks = spec.strip().split("\n\n")
total_header = 0
total_parsed = 0

for b in blocks:
    lines = [l.strip() for l in b.strip().split("\n") if l.strip()]
    if not lines: continue
    m_h = re.match(r"^([A-Za-z\s\'\.\-]+)\s*—\s*TOTAL\s*(\d+)", lines[0])
    if not m_h: continue
    t_name = m_h.group(1).strip()
    expected_tot = int(m_h.group(2))
    total_header += expected_tot
    
    cnt = 0
    for l in lines[1:]:
        if ":" in l:
            items = l.split(":", 1)[1].split(";")
            cnt += len([it for it in items if it.strip()])
            
    total_parsed += cnt
    if cnt != expected_tot:
        print(f"DISCREPANCY for {t_name}: Header says {expected_tot}, items count = {cnt}")

print(f"\nSum of Headers: {total_header} | Sum of Parsed Items: {total_parsed}")
