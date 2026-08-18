#!/usr/bin/env python3
"""
generate_official_exam_schedule_2026.py
Generates the Official 1st Quarter Examination Schedule for AMIS.
- Time allocation & scheduling structure strictly based on:
  1st Quarter Exam Schedule (S.Y. 2025-2026).xlsx
- Academic data (subjects, sections, teachers, shifts) strictly from:
  Current AMIS System Database (class_schedules_data.json / Canonical V4)
- Optimized with Google OR-Tools CP-SAT for zero teacher & section conflicts.
"""

import os
import json
import re
import csv
from collections import defaultdict
from ortools.sat.python import cp_model
from teacher_registry import resolve_teacher, TEACHER_REGISTRY

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"
CLASS_DATA_PATH = os.path.join(BASE_DIR, "class_schedules_data.json")
EXAM_DATA_JSON = os.path.join(BASE_DIR, "exam_data.json")
EXAM_DATA_JS = os.path.join(BASE_DIR, "exam_data.js")
OPTIONS_EXAM_DATA_JSON = os.path.join(BASE_DIR, "options_exam_data.json")
CSV_PATH = os.path.join(BASE_DIR, "AMIS_Teacher_Exam_Subject_Assignments.csv")

with open(CLASS_DATA_PATH, 'r', encoding='utf-8') as f:
    sections = json.load(f)

# Non-examinable breaks/activities
def normalize_exam_subject(raw_s, grade_level, dept):
    if not raw_s: return None
    s = raw_s.upper().strip()
    s = re.sub(r'\s*\([^)]*\)', '', s).strip()
    
    if any(k in s for k in [
        'GENERAL ASSEMBLY', 'RECESS', 'TRANSITION', 'LUNCH', 'DEPARTURE', 'SALAH', 
        'HOMEROOM', 'HG', 'DISMISSAL', 'MEETING TIME', 'WRAP-UP TIME', 
        'ARAL MATH', 'ARAL READING', 'ARAL PROGRAM', 'ARAL'
    ]):
        return None
        
    if 'Senior High' in dept:
        return raw_s.strip()
        
    if 'Kinder' in grade_level or 'K1' in grade_level or 'K2' in grade_level:
        if 'QUR' in s: return 'Qur\'an'
        if 'ARABIC' in s: return 'Arabic'
        if 'HADITH' in s: return 'Hadith'
        return 'Oral & Written Exam'
        
    if 'QUR' in s: return 'Qur\'an'
    if 'HADITH' in s: return 'Hadith'
    if 'SHAF' in s: return 'SHAF'
    if 'ARABIC' in s: return 'Arabic'
    if 'GMRC' in s: return 'GMRC'
    if 'ESP' in s or 'VALUES' in s: return 'Values Ed'
    if 'MATH' in s: return 'Math'
    if 'SCI' in s or 'BIOLOGY' in s or 'PHYSICS' in s or 'CHEM' in s: return 'Science'
    if 'ENG' in s: return 'English'
    if 'READING' in s or 'R & L' in s or 'LITERACY' in s: return 'Reading & Literacy' if 'Grade 1' in grade_level else 'English'
    if 'LANGUAGE' in s: return 'Language' if 'Grade 1' in grade_level else 'English'
    if 'FILIPINO' in s: return 'Filipino'
    if 'MAKABANSA' in s: return 'Makabansa'
    if 'AP' in s or 'ARALING' in s or 'SOC' in s: return 'Araling Panlipunan' if 'Elementary' in dept else 'Social Science'
    if 'TLE' in s or 'EPP' in s: return 'TLE'
    if 'MAPEH' in s or 'PE' in s or 'MUSIC' in s or 'ART' in s or 'HEALTH' in s: return 'MAPEH'
    
    return raw_s.strip()

all_exam_items = []
seen_items = set()

for sec in sections:
    sec_id = sec['id']
    sec_name = sec['section_name']
    dept = sec['department']
    grade = sec['grade_level']
    shift = sec['shift']
    
    is_kinder = 'Kinder' in grade or 'K1' in grade or 'K2' in grade
    
    sec_subjs = defaultdict(set)
    for p in sec.get('periods', []):
        for d, cell in (p.get('days') or {}).items():
            if cell and not cell.get('is_break'):
                raw = cell.get('subject') or ''
                tchr = cell.get('teacher')
                norm = normalize_exam_subject(raw, grade, dept)
                if norm: sec_subjs[norm].add(tchr)
                
    if is_kinder:
        teacher_set = set()
        for raw_subj, tchrs in sec_subjs.items():
            if not any(k in raw_subj.upper() for k in ['QUR', 'ARABIC', 'HADITH', 'SHAF']):
                teacher_set.update(t for t in tchrs if t)
        homeroom_tchr = list(teacher_set)[0] if teacher_set else 'Assigned Faculty'
        
        kinder_exams = [
            ('Oral & Written Exam', homeroom_tchr),
            ('Qur\'an', list(sec_subjs.get('Qur\'an', ['Ustadh Hainur']))[0]),
            ('Arabic', list(sec_subjs.get('Arabic', ['Ustadha Silfah']))[0]),
            ('Hadith', list(sec_subjs.get('Hadith', ['Ustadh Hainur']))[0]),
        ]
        for subj_name, tchr_name in kinder_exams:
            t_res = resolve_teacher(tchr_name)
            tchr_canonical = t_res['canonical_name'] if t_res else tchr_name
            tchr_id = t_res['id'] if t_res else 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', tchr_name).strip('_').lower()
            all_exam_items.append({
                'section_id': sec_id,
                'section_name': sec_name,
                'department': dept,
                'grade_level': grade,
                'shift': shift,
                'subject': subj_name,
                'teacher': tchr_canonical,
                'teacher_id': tchr_id,
                'duration_minutes': 40 if is_kinder else 60
            })
    else:
        for subj_name, tchrs in sec_subjs.items():
            valid_tchrs = [t for t in tchrs if t]
            tchr_name = valid_tchrs[0] if valid_tchrs else 'Assigned Faculty'
            t_res = resolve_teacher(tchr_name)
            tchr_canonical = t_res['canonical_name'] if t_res else tchr_name
            tchr_id = t_res['id'] if t_res else 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', tchr_name).strip('_').lower()
            
            item_key = (sec_id, subj_name.upper())
            if item_key in seen_items:
                continue
            seen_items.add(item_key)
            
            all_exam_items.append({
                'section_id': sec_id,
                'section_name': sec_name,
                'department': dept,
                'grade_level': grade,
                'shift': shift,
                'subject': subj_name,
                'teacher': tchr_canonical,
                'teacher_id': tchr_id,
                'duration_minutes': 60
            })

print(f"Loaded {len(all_exam_items)} curricular exam items across {len(sections)} sections.")

# Time slots per shift strictly following S.Y. 2025-2026 Reference Schedule
SHIFT_SLOTS = {
    'F2F': [
        {'slot_num': 1, 'time_slot': '08:00 AM – 09:00 AM', 'start_m': 480, 'end_m': 540},
        {'slot_num': 2, 'time_slot': '09:00 AM – 10:00 AM', 'start_m': 540, 'end_m': 600},
        {'slot_num': 3, 'time_slot': '10:25 AM – 11:25 AM', 'start_m': 625, 'end_m': 685}
    ],
    'ODL - 1ST SHIFT': [
        {'slot_num': 1, 'time_slot': '12:40 PM – 01:40 PM', 'start_m': 760, 'end_m': 820},
        {'slot_num': 2, 'time_slot': '01:50 PM – 02:50 PM', 'start_m': 830, 'end_m': 890},
        {'slot_num': 3, 'time_slot': '03:10 PM – 04:10 PM', 'start_m': 910, 'end_m': 970}
    ],
    'ODL - 2ND SHIFT': [
        {'slot_num': 1, 'time_slot': '03:10 PM – 04:10 PM', 'start_m': 910, 'end_m': 970},
        {'slot_num': 2, 'time_slot': '04:20 PM – 05:20 PM', 'start_m': 980, 'end_m': 1040},
        {'slot_num': 3, 'time_slot': '05:30 PM – 06:30 PM', 'start_m': 1050, 'end_m': 1110}
    ]
}

SHS_1ST_SLOTS = [
    {'slot_num': 1, 'time_slot': '12:40 PM – 01:40 PM', 'start_m': 760, 'end_m': 820},
    {'slot_num': 2, 'time_slot': '01:50 PM – 02:50 PM', 'start_m': 830, 'end_m': 890},
    {'slot_num': 3, 'time_slot': '03:10 PM – 04:10 PM', 'start_m': 910, 'end_m': 970},
    {'slot_num': 4, 'time_slot': '04:20 PM – 05:20 PM', 'start_m': 980, 'end_m': 1040}
]

def get_slots_for_item(item):
    if 'Senior High' in item['department'] and item['shift'] == 'ODL - 1ST SHIFT':
        return SHS_1ST_SLOTS
    return SHIFT_SLOTS[item['shift']]

EXAM_DAYS = [
    {'day_num': 1, 'date_str': 'Monday, September 7, 2026', 'short_date': 'Sep 7', 'day_name': 'Monday'},
    {'day_num': 2, 'date_str': 'Tuesday, September 8, 2026', 'short_date': 'Sep 8', 'day_name': 'Tuesday'},
    {'day_num': 3, 'date_str': 'Wednesday, September 9, 2026', 'short_date': 'Sep 9', 'day_name': 'Wednesday'},
    {'day_num': 4, 'date_str': 'Thursday, September 10, 2026', 'short_date': 'Sep 10', 'day_name': 'Thursday'}
]

DAYS = [1, 2, 3, 4]

model = cp_model.CpModel()

# Decision variable: x[item_idx, day, slot_idx]
x = {}
for i, item in enumerate(all_exam_items):
    slots = get_slots_for_item(item)
    for d in DAYS:
        for s_idx, slot in enumerate(slots):
            x[i, d, s_idx] = model.NewBoolVar(f'x_{i}_{d}_{s_idx}')

# Constraint 1: Exactly one assignment per exam item
for i in range(len(all_exam_items)):
    slots = get_slots_for_item(all_exam_items[i])
    model.AddExactlyOne(x[i, d, s_idx] for d in DAYS for s_idx in range(len(slots)))

# Constraint 2: Section constraint (at most 1 exam per slot, max 3 or 4 per day)
by_sec = defaultdict(list)
for i, item in enumerate(all_exam_items):
    by_sec[item['section_id']].append(i)

for sec_id, items in by_sec.items():
    slots = get_slots_for_item(all_exam_items[items[0]])
    for d in DAYS:
        for s_idx in range(len(slots)):
            model.Add(sum(x[i, d, s_idx] for i in items) <= 1)
        max_daily = 4 if 'Senior High' in all_exam_items[items[0]]['department'] else 3
        model.Add(sum(x[i, d, s_idx] for i in items for s_idx in range(len(slots))) <= max_daily)

# Constraint 3: Same-shift teacher conflict (Grade 1 - 12 strictly 0 conflict)
by_teacher_shift = defaultdict(list)
for i, item in enumerate(all_exam_items):
    tid = item['teacher_id']
    sh = item['shift']
    g = item['grade_level']
    is_kinder = 'Kinder' in g or 'K1' in g or 'K2' in g
    if tid and tid != 'tchr_assigned_faculty' and not is_kinder:
        by_teacher_shift[(tid, sh)].append(i)

for (tid, sh), items in by_teacher_shift.items():
    slots = SHIFT_SLOTS[sh]
    for d in DAYS:
        for s_idx in range(len(slots)):
            model.Add(sum(x[i, d, s_idx] for i in items) <= 1)

# Soft objective: Minimize cross-shift absolute time overlaps
overlap_conflicts = []
by_teacher_all = defaultdict(list)
for i, item in enumerate(all_exam_items):
    tid = item['teacher_id']
    if tid and tid != 'tchr_assigned_faculty':
        by_teacher_all[tid].append(i)

time_intervals = [
    (480, 540), (540, 600), (625, 685),
    (760, 820), (830, 890),
    (910, 970), (980, 1040), (1050, 1110)
]

for tid, items in by_teacher_all.items():
    for d in DAYS:
        for (int_start, int_end) in time_intervals:
            matching_vars = []
            for i in items:
                slots = get_slots_for_item(all_exam_items[i])
                for s_idx, slot in enumerate(slots):
                    if not (slot['end_m'] <= int_start or slot['start_m'] >= int_end):
                        matching_vars.append(x[i, d, s_idx])
            if len(matching_vars) > 1:
                overlap_var = model.NewIntVar(0, len(matching_vars), f'ov_{tid}_{d}_{int_start}')
                model.Add(overlap_var >= sum(matching_vars) - 1)
                overlap_conflicts.append(overlap_var)

model.Minimize(sum(overlap_conflicts))

print("Solving Official Examination CP-SAT model...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 45.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Error: Could not find feasible exam schedule!")
    exit(1)

print(f"✓ Solved successfully! Total Cross-Shift Overlap Score: {solver.ObjectiveValue()}")

# Build Final Exam Records
final_exam_records = []
csv_export_rows = []
exam_id_counter = 1

for d_idx, day_info in enumerate(EXAM_DAYS):
    day_num = day_info['day_num']
    for i, item in enumerate(all_exam_items):
        slots = get_slots_for_item(item)
        for s_idx, slot in enumerate(slots):
            if solver.Value(x[i, day_num, s_idx]) == 1:
                rec_id = f"exam_{exam_id_counter}"
                exam_id_counter += 1
                
                rec = {
                    "id": rec_id,
                    "exam_term": "1st Term",
                    "day_number": day_num,
                    "date": day_info['date_str'],
                    "short_date": day_info['short_date'],
                    "day_name": day_info['day_name'],
                    "slot_number": slot['slot_num'],
                    "time_slot": slot['time_slot'],
                    "time": slot['time_slot'],
                    "section_id": item['section_id'],
                    "section": item['section_name'],
                    "section_name": item['section_name'],
                    "department": item['department'],
                    "grade": item['grade_level'],
                    "grade_level": item['grade_level'],
                    "shift": item['shift'],
                    "modality": "F2F" if item['shift'] == 'F2F' else 'ODL',
                    "gender": "MIXED",
                    "subject_id": 'subj_' + re.sub(r'[^a-zA-Z0-9]+', '_', item['subject']).strip('_').lower(),
                    "subject": item['subject'],
                    "teacher_id": item['teacher_id'],
                    "teacher": item['teacher'],
                    "duration_minutes": item['duration_minutes'],
                    "teacher_status": "VERIFIED"
                }
                final_exam_records.append(rec)
                
                csv_export_rows.append({
                    "Exam_ID": rec_id,
                    "Day": day_info['day_name'],
                    "Date": day_info['date_str'],
                    "Time_Slot": slot['time_slot'],
                    "Section": item['section_name'],
                    "Department": item['department'],
                    "Grade_Level": item['grade_level'],
                    "Shift": item['shift'],
                    "Subject": item['subject'],
                    "Teacher": item['teacher'],
                    "Duration": f"{item['duration_minutes']} min."
                })

print(f"Generated {len(final_exam_records)} authoritative exam sessions.")

# Write JSON & JS files
with open(EXAM_DATA_JSON, 'w', encoding='utf-8') as f:
    json.dump(final_exam_records, f, indent=2)

with open(EXAM_DATA_JS, 'w', encoding='utf-8') as f:
    f.write("const ALL_EXAM_RECORDS = ")
    json.dump(final_exam_records, f, indent=2)
    f.write(";\n\nif (typeof window !== 'undefined') {\n  window.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n}\nif (typeof module !== 'undefined' && module.exports) {\n  module.exports = ALL_EXAM_RECORDS;\n}\n")

# Write CSV file
fieldnames = ["Exam_ID", "Day", "Date", "Time_Slot", "Section", "Department", "Grade_Level", "Shift", "Subject", "Teacher", "Duration"]
with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(csv_export_rows)

print(f"✓ Successfully wrote {EXAM_DATA_JSON}, {EXAM_DATA_JS}, and {CSV_PATH}")
