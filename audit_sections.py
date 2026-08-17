#!/usr/bin/env python3
import json
import os
import re
from collections import defaultdict

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "check_spec.py"), "r") as f:
    pass

from apply_new_assignments_and_solve import assignments, sec_assignments

print(f"Total Sections: {len(sec_assignments)}")
print("\nSection Workload Breakdown (Subjects per section):")
for (g, sec, sec_name, mod, sh, gen), subs in sorted(sec_assignments.items(), key=lambda x: (x[0][0], x[0][3], x[0][4], x[0][1])):
    print(f"  • {g:12} | {sec:28} | {mod:3} | {sh:10} | {gen:7} | Count: {len(subs)}")
    sub_names = [s[0] for s in subs]
    # check for duplicates within section
    if len(sub_names) != len(set(sub_names)):
        dups = [s for s in sub_names if sub_names.count(s) > 1]
        print(f"    ⚠️ DUPLICATE SUBJECTS IN SECTION: {set(dups)}")
