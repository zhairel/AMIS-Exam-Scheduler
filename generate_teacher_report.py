#!/usr/bin/env python3
import json
import os
from collections import defaultdict

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"
with open(os.path.join(BASE_DIR, "options_exam_data.json"), "r", encoding="utf-8") as f:
    opts_data = json.load(f)

records = opts_data["OPTION_A"]
t_workload = defaultdict(lambda: {"total": 0, "F2F": 0, "ODL_1": 0, "ODL_2": 0, "subjects": set(), "sections": set()})

for r in records:
    t = r["teacher"]
    mod = r["modality"]
    sh = r["shift"]
    g = r["grade"]
    sec = r.get("section_name", r["section"])
    sub = r["subject"]
    
    t_workload[t]["total"] += 1
    if mod == "F2F":
        t_workload[t]["F2F"] += 1
    elif "2nd" in sh:
        t_workload[t]["ODL_2"] += 1
    else:
        t_workload[t]["ODL_1"] += 1
        
    t_workload[t]["subjects"].add(sub)
    t_workload[t]["sections"].add(f"{g} ({sec})")

out_lines = []
out_lines.append("=" * 90)
out_lines.append("AL MUNAWWARA ISLAMIC SCHOOL — CANONICAL FACULTY WORKLOAD REPORT")
out_lines.append(f"Total Canonical Faculty Members: {len(t_workload)}")
out_lines.append(f"Total Exam Proctored Sessions: {len(records)}")
out_lines.append("=" * 90)
out_lines.append(f"{'FACULTY NAME':<26} | {'TOTAL':<5} | {'F2F':<4} | {'ODL 1':<5} | {'ODL 2':<5} | {'PRIMARY SUBJECTS'}")
out_lines.append("-" * 90)

for t, d in sorted(t_workload.items(), key=lambda x: (-x[1]["total"], x[0])):
    subs_str = ", ".join(sorted(d["subjects"]))
    tot = d["total"]
    f2f = d["F2F"]
    odl1 = d["ODL_1"]
    odl2 = d["ODL_2"]
    out_lines.append(f"{t:<26} | {tot:>5} | {f2f:>4} | {odl1:>5} | {odl2:>5} | {subs_str}")

out_lines.append("=" * 90)
rep_text = "\n".join(out_lines)

with open(os.path.join(BASE_DIR, "teacher_canonical_recount_report.txt"), "w", encoding="utf-8") as f:
    f.write(rep_text)

with open("/home/tatsuya/Downloads/teacher_canonical_recount_report.txt", "w", encoding="utf-8") as f:
    f.write(rep_text)

print(rep_text)
