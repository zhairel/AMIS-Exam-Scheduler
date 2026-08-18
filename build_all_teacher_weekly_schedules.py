#!/usr/bin/env python3
"""
build_all_teacher_weekly_schedules.py
Rebuilds teacher_weekly_schedules.json & .js directly from the canonical class dataset
class_schedules_data.json (ELEM + HS SCHED (NEW)).
"""

import os
import json
from collections import defaultdict
from teacher_registry import resolve_teacher, TEACHER_REGISTRY

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "class_schedules_data.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)

# Initialize all canonical teachers
teacher_data = {}
for t in TEACHER_REGISTRY:
    teacher_data[t['id']] = {
        'teacher_id': t['id'],
        'teacher_name': t['canonical_name'],
        'canonical_name': t['canonical_name'],
        'department': t.get('department', 'Faculty'),
        'periods': []
    }

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

for sec in sections:
    sname = sec['section_name']
    dept = sec['department']
    grade = sec['grade_level']
    shift = sec['shift']
    sec_id = sec['id']
    
    for p in sec.get('periods', []):
        time_str = p.get('time')
        mins_str = p.get('minutes')
        p_num = p.get('period_num')
        
        if p.get('is_merged_all_days'):
            if not p.get('is_break'):
                raw = p.get('label') or p.get('subject') or ''
                tchr = p.get('teacher')
                tid = p.get('teacher_id')
                t_res = resolve_teacher(tchr) or resolve_teacher(raw)
                if t_res:
                    tid = t_res['id']
                    tchr = t_res['canonical_name']
                if tid and tid in teacher_data:
                    for day in DAYS:
                        teacher_data[tid]['periods'].append({
                            'section_id': sec_id,
                            'section_name': sname,
                            'department': dept,
                            'grade_level': grade,
                            'shift': shift,
                            'period_num': p_num,
                            'time': time_str,
                            'minutes': mins_str,
                            'day': day,
                            'subject': p.get('subject') or raw,
                            'raw_label': raw
                        })
        else:
            for day, cell in (p.get('days') or {}).items():
                if cell and not cell.get('is_break'):
                    raw = cell.get('label') or cell.get('subject') or ''
                    tchr = cell.get('teacher')
                    tid = cell.get('teacher_id')
                    t_res = resolve_teacher(tchr) or resolve_teacher(raw)
                    if t_res:
                        tid = t_res['id']
                        tchr = t_res['canonical_name']
                    if tid and tid in teacher_data:
                        teacher_data[tid]['periods'].append({
                            'section_id': sec_id,
                            'section_name': sname,
                            'department': dept,
                            'grade_level': grade,
                            'shift': shift,
                            'period_num': p_num,
                            'time': time_str,
                            'minutes': mins_str,
                            'day': day,
                            'subject': cell.get('subject') or raw,
                            'raw_label': raw
                        })

# Save JSON and JS
with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.json"), "w", encoding="utf-8") as f:
    json.dump(teacher_data, f, indent=2, ensure_ascii=False)

with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.js"), "w", encoding="utf-8") as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(teacher_data, indent=2, ensure_ascii=False)};\n")

print(f"✓ Successfully built teacher_weekly_schedules.json and .js for {len(teacher_data)} teachers!")
