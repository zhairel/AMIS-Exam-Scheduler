#!/usr/bin/env python3
"""
generate_official_exam_schedule_2026.py
Generates the Official 1st Quarter Examination Schedule for AMIS.
- Time allocation & scheduling structure strictly based on:
  1st Quarter Exam Schedule (S.Y. 2025-2026).xlsx
- Academic data (subjects, sections, teachers, shifts) strictly from:
  Current AMIS System Database (class_schedules_data.json / Canonical V4)
- High School & SHS Math exams are 120 minutes (2 consecutive slots)
- Zero teacher & section conflicts with CP-SAT solver across 100% of time intervals
"""

import os
import json
import re
import csv
from collections import defaultdict
from ortools.sat.python import cp_model
from schedule_optimization import (
    PlacementChoice,
    add_vacancy_gap_indicators,
    minimize_early_compact_schedule,
)
from teacher_registry import resolve_teacher

BASE_DIR = os.environ.get("AMIS_BASE_DIR", os.path.dirname(os.path.abspath(__file__)))
CLASS_DATA_PATH = os.path.join(BASE_DIR, "class_schedules_data.json")
EXAM_DATA_JSON = os.path.join(BASE_DIR, "exam_data.json")
EXAM_DATA_JS = os.path.join(BASE_DIR, "exam_data.js")
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
            ('Qur\'an', list(sec_subjs.get('Qur\'an', ['Ustadha Hainur']))[0]),
            ('Arabic', list(sec_subjs.get('Arabic', ['Ustadha Silfah']))[0]),
            ('Hadith', list(sec_subjs.get('Hadith', ['Ustadha Hainur']))[0]),
        ]
        for subj_name, tchr_name in kinder_exams:
            if 'KHABAAB' in sec_name.upper() and subj_name == 'Arabic':
                tchr_name = 'Ustadh Faidh'

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
                'duration_minutes': 60,
                'slots_needed': 1
            })
    else:
        for subj_name, tchrs in sec_subjs.items():
            valid_tchrs = [t for t in tchrs if t]
            tchr_name = valid_tchrs[0] if valid_tchrs else 'Assigned Faculty'

            # Explicit Teacher Corrections
            if 'AS\'AD' in sec_name.upper() or 'AS`AD' in sec_name.upper() or 'ASAD' in sec_name.upper():
                if subj_name == 'GMRC': tchr_name = 'Ustadha Saliha'
                if subj_name == 'Arabic': tchr_name = 'Ustadh Faidh'
            if 'DIHYA' in sec_name.upper():
                if subj_name == 'Math': tchr_name = 'Teacher Saimona'
                if subj_name == 'SHAF': tchr_name = 'Ustadh Faidh'
            if 'USAYD' in sec_name.upper():
                if subj_name == 'English': tchr_name = 'Teacher Jenny'

            t_res = resolve_teacher(tchr_name)
            tchr_canonical = t_res['canonical_name'] if t_res else tchr_name
            tchr_id = t_res['id'] if t_res else 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', tchr_name).strip('_').lower()
            
            item_key = (sec_id, subj_name.upper())
            if item_key in seen_items:
                continue
            seen_items.add(item_key)
            
            # High School & SHS Math = 2 hours (120 min, 2 slots)
            is_hs_or_shs = 'High School' in dept or 'Senior High' in dept or any(g in grade for g in ['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'])
            is_math = any(m in subj_name.lower() for m in ['math', 'mathematics', 'calculus', 'statistics'])
            duration_mins = 120 if (is_hs_or_shs and is_math) else 60
            slots_needed = 2 if duration_mins == 120 else 1

            all_exam_items.append({
                'section_id': sec_id,
                'section_name': sec_name,
                'department': dept,
                'grade_level': grade,
                'shift': shift,
                'subject': subj_name,
                'teacher': tchr_canonical,
                'teacher_id': tchr_id,
                'duration_minutes': duration_mins,
                'slots_needed': slots_needed
            })

print(f"Loaded {len(all_exam_items)} curricular exam items ({sum(1 for i in all_exam_items if i['slots_needed'] == 2)} 120min HS Math items) across {len(sections)} sections.")

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

K2_1ST_SLOTS = [
    {'slot_num': 1, 'time_slot': '01:30 PM – 02:30 PM', 'start_m': 810, 'end_m': 870},
    {'slot_num': 2, 'time_slot': '02:40 PM – 03:40 PM', 'start_m': 880, 'end_m': 940},
    {'slot_num': 3, 'time_slot': '03:50 PM – 04:50 PM', 'start_m': 950, 'end_m': 1010}
]

SHS_1ST_SLOTS = [
    {'slot_num': 1, 'time_slot': '12:40 PM – 01:40 PM', 'start_m': 760, 'end_m': 820},
    {'slot_num': 2, 'time_slot': '01:50 PM – 02:50 PM', 'start_m': 830, 'end_m': 890},
    {'slot_num': 3, 'time_slot': '03:10 PM – 04:10 PM', 'start_m': 910, 'end_m': 970},
    {'slot_num': 4, 'time_slot': '04:20 PM – 05:20 PM', 'start_m': 980, 'end_m': 1040}
]

def get_slots_for_item(item):
    if 'Kinder' in item['grade_level'] and '1ST' in item['shift']:
        return K2_1ST_SLOTS
    if 'Senior High' in item['department'] and item['shift'] == 'ODL - 1ST SHIFT':
        return SHS_1ST_SLOTS
    return SHIFT_SLOTS[item['shift']]

EXAM_DAYS = [
    {'day_num': 1, 'date_str': 'Wednesday, September 2, 2026', 'short_date': 'Sep 2', 'day_name': 'Wednesday', 'header': 'Day 1 • Wed, Sep 2'},
    {'day_num': 2, 'date_str': 'Thursday, September 3, 2026', 'short_date': 'Sep 3', 'day_name': 'Thursday', 'header': 'Day 2 • Thu, Sep 3'},
    {'day_num': 3, 'date_str': 'Sunday, September 6, 2026', 'short_date': 'Sep 6', 'day_name': 'Sunday', 'header': 'Day 3 • Sun, Sep 6'},
    {'day_num': 4, 'date_str': 'Monday, September 7, 2026', 'short_date': 'Sep 7', 'day_name': 'Monday', 'header': 'Day 4 • Mon, Sep 7'}
]

DAYS = [1, 2, 3, 4]

model = cp_model.CpModel()

# Decision variable: start_slot s_idx for item i on day d
x = {}
for i, item in enumerate(all_exam_items):
    slots = get_slots_for_item(item)
    k = item['slots_needed']
    for d in DAYS:
        for s_idx in range(len(slots) - k + 1):
            x[i, d, s_idx] = model.NewBoolVar(f'x_{i}_{d}_{s_idx}')

# Constraint 1: Exactly one assignment per exam item
for i, item in enumerate(all_exam_items):
    slots = get_slots_for_item(item)
    k = item['slots_needed']
    model.AddExactlyOne(x[i, d, s_idx] for d in DAYS for s_idx in range(len(slots) - k + 1))

# Constraint 2: Section constraint (at most 1 exam occupying any slot, max daily units <= 3 or 4)
by_sec = defaultdict(list)
section_day_occupancy = {}
for i, item in enumerate(all_exam_items):
    by_sec[item['section_id']].append(i)

for sec_id, items in by_sec.items():
    slots = get_slots_for_item(all_exam_items[items[0]])
    num_slots = len(slots)
    for d in DAYS:
        for s in range(num_slots):
            occupying = []
            for i in items:
                k = all_exam_items[i]['slots_needed']
                for s_start in range(max(0, s - k + 1), min(s + 1, num_slots - k + 1)):
                    occupying.append(x[i, d, s_start])
            model.Add(sum(occupying) <= 1)
            occupied = model.NewBoolVar(f"section_{sec_id}_{d}_{s}_occupied")
            model.Add(occupied == sum(occupying))
            section_day_occupancy.setdefault((sec_id, d), []).append(occupied)
            
        max_daily_units = 4 if 'Senior High' in all_exam_items[items[0]]['department'] else 3
        daily_units = []
        for i in items:
            k = all_exam_items[i]['slots_needed']
            for s_start in range(num_slots - k + 1):
                daily_units.append(x[i, d, s_start] * k)
        model.Add(sum(daily_units) <= max_daily_units)

# Constraint 3: Strict 0 Teacher Overlaps across all time windows & all teachers
by_teacher = defaultdict(list)
for i, item in enumerate(all_exam_items):
    tid = item['teacher_id']
    if tid and tid != 'tchr_assigned_faculty':
        by_teacher[tid].append(i)

for tid, items in by_teacher.items():
    for d in DAYS:
        for idx1 in range(len(items)):
            i1 = items[idx1]
            slots1 = get_slots_for_item(all_exam_items[i1])
            k1 = all_exam_items[i1]['slots_needed']
            for idx2 in range(idx1 + 1, len(items)):
                i2 = items[idx2]
                slots2 = get_slots_for_item(all_exam_items[i2])
                k2 = all_exam_items[i2]['slots_needed']
                
                # Check if i1 and i2 are co-taught synchronous ISAL sessions
                is_merged = (all_exam_items[i1]['shift'] == all_exam_items[i2]['shift'] and
                             'ODL' in all_exam_items[i1]['shift'] and
                             all_exam_items[i1]['subject'] == all_exam_items[i2]['subject'] and
                             any(k in all_exam_items[i1]['subject'].upper() for k in ['QUR', 'ARABIC', 'HADITH', 'SHAF']))
                
                for s1 in range(len(slots1) - k1 + 1):
                    start1 = slots1[s1]['start_m']
                    end1 = slots1[s1 + k1 - 1]['end_m']
                    for s2 in range(len(slots2) - k2 + 1):
                        start2 = slots2[s2]['start_m']
                        end2 = slots2[s2 + k2 - 1]['end_m']
                        
                        if not (end1 <= start2 or start1 >= end2):
                            if is_merged and start1 == start2 and end1 == end2:
                                continue
                            model.Add(x[i1, d, s1] + x[i2, d, s2] <= 1)

# Track chronological teacher occupancy separately from conflict prevention.
# A shared/cohort exam may contain multiple assignment variables at the same
# time, so AddMaxEquality turns them into one occupied time block.
teacher_day_time_vars = defaultdict(lambda: defaultdict(list))
for tid, items in by_teacher.items():
    for i in items:
        slots = get_slots_for_item(all_exam_items[i])
        slots_needed = all_exam_items[i]['slots_needed']
        for d in DAYS:
            for start_index in range(len(slots) - slots_needed + 1):
                placement = x[i, d, start_index]
                for occupied_index in range(start_index, start_index + slots_needed):
                    teacher_day_time_vars[(tid, d)][slots[occupied_index]['start_m']].append(placement)

teacher_day_occupancy = {}
for resource_day, variables_by_time in teacher_day_time_vars.items():
    chronological = []
    for time_index, start_minute in enumerate(sorted(variables_by_time)):
        variables_at_time = variables_by_time[start_minute]
        if len(variables_at_time) == 1:
            chronological.append(variables_at_time[0])
        else:
            occupied = model.NewBoolVar(
                f"teacher_{resource_day[0]}_{resource_day[1]}_{time_index}_occupied"
            )
            model.AddMaxEquality(occupied, variables_at_time)
            chronological.append(occupied)
    teacher_day_occupancy[resource_day] = chronological

# Hard rules above remain absolute. This objective only ranks the legal choices:
# Day 1 -> Day 2 -> Day 3 -> Day 4, earliest slot, then fewest section/teacher gaps.
gap_variables = []
gap_variables.extend(
    add_vacancy_gap_indicators(model, section_day_occupancy, "section")
)
gap_variables.extend(
    add_vacancy_gap_indicators(model, teacher_day_occupancy, "teacher")
)
placement_choices = []
for i, item in enumerate(all_exam_items):
    slots = get_slots_for_item(item)
    for d in DAYS:
        for start_index in range(len(slots) - item['slots_needed'] + 1):
            placement_choices.append(
                PlacementChoice(
                    variable=x[i, d, start_index],
                    day_rank=d - 1,
                    start_rank=start_index,
                )
            )

objective_weights = minimize_early_compact_schedule(
    model,
    placement_choices,
    assignment_count=len(all_exam_items),
    gap_variables=gap_variables,
)

print("Solving Official Examination CP-SAT model with zero conflicts...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 0
status = solver.Solve(model)

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Error: Could not find feasible exam schedule!")
    exit(1)

print(
    f"✓ Solver status {solver.StatusName(status)} with 0 conflicts using chronological compaction "
    f"(objective bound {objective_weights.maximum_cost})."
)

# Build Final Exam Records
final_exam_records = []
csv_export_rows = []
exam_id_counter = 1

for d_idx, day_info in enumerate(EXAM_DAYS):
    day_num = day_info['day_num']
    for i, item in enumerate(all_exam_items):
        slots = get_slots_for_item(item)
        k = item['slots_needed']
        for s_idx in range(len(slots) - k + 1):
            if solver.Value(x[i, day_num, s_idx]) == 1:
                rec_id = f"exam_{exam_id_counter}"
                exam_id_counter += 1
                
                # Full continuous time slot string for 120min (2-slot) exams
                start_slot_time = slots[s_idx]['time_slot']
                start_time_part = start_slot_time.split('–')[0].strip()
                end_slot_time = slots[s_idx + k - 1]['time_slot']
                end_time_part = end_slot_time.split('–')[1].strip()
                full_time_slot = f"{start_time_part} – {end_time_part}"
                
                rec = {
                    "id": rec_id,
                    "exam_term": "1st Term",
                    "day_number": day_num,
                    "date": day_info['date_str'],
                    "short_date": day_info['short_date'],
                    "day_name": day_info['day_name'],
                    "slot_number": slots[s_idx]['slot_num'],
                    "slots_spanned": k,
                    "start_slot_index": s_idx,
                    "end_slot_index": s_idx + k - 1,
                    "start_m": slots[s_idx]['start_m'],
                    "end_m": slots[s_idx + k - 1]['end_m'],
                    "time_slot": full_time_slot,
                    "time": full_time_slot,
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
                    "Time_Slot": full_time_slot,
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
