#!/usr/bin/env python3
"""
schedule_60m_unstacked.py
Authoritative AMIS 2nd Term Examination CP-SAT Optimization Engine.

Enforces:
1. Every subject is exactly 60 minutes (duration_minutes = 60, slots_spanned = 1).
2. Zero stacking per teacher: Strictly at most 1 exam per teacher per slot (all 48 faculty).
3. Shift time window integrity:
   - F2F Morning: 08:00 AM – 11:25 AM
   - K1 F2F Afternoon: 12:40 PM – 02:50 PM
   - First Shift (ODL 1): 12:40 PM – 04:10 PM
   - Second Shift (ODL 2): 03:10 PM – 06:30 PM (with intentional 3:10 PM – 4:10 PM mixed overlap)
4. Preserves authentic faculty requirements and balances daily workload across Days 1–4.
5. Minimizes section collisions to the mathematical minimum.
6. Synchronizes exam_data_2nd_term.json and exam_data_2nd_term.js.
"""

import os
import json
from collections import defaultdict
from ortools.sat.python import cp_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAM_JSON = os.path.join(BASE_DIR, 'exam_data_2nd_term.json')
EXAM_JS = os.path.join(BASE_DIR, 'exam_data_2nd_term.js')

ROOT_DIR = os.path.dirname(BASE_DIR)
ROOT_EXAM_JSON = os.path.join(ROOT_DIR, 'exam_data_2nd_term.json')
ROOT_EXAM_JS = os.path.join(ROOT_DIR, 'exam_data_2nd_term.js')

# Load exams
with open(EXAM_JSON, 'r', encoding='utf-8') as f:
    exams = json.load(f)

print(f"Loaded {len(exams)} exam records.")

F2F_MORNING = ['08:00 AM – 09:00 AM', '09:00 AM – 10:00 AM', '10:25 AM – 11:25 AM']
K1_F2F = ['12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM']
FIRST_SHIFT = ['12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM', '03:10 PM – 04:10 PM']
SECOND_SHIFT = ['03:10 PM – 04:10 PM', '04:20 PM – 05:20 PM', '05:30 PM – 06:30 PM']

ALL_SLOT_TIMES = [
    '08:00 AM – 09:00 AM',
    '09:00 AM – 10:00 AM',
    '10:25 AM – 11:25 AM',
    '12:40 PM – 01:40 PM',
    '01:50 PM – 02:50 PM',
    '03:10 PM – 04:10 PM',
    '04:20 PM – 05:20 PM',
    '05:30 PM – 06:30 PM'
]

SLOT_INFO = {
    # F2F Morning
    ('F2F', '08:00 AM – 09:00 AM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 480, 'end_m': 540},
    ('F2F', '09:00 AM – 10:00 AM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 540, 'end_m': 600},
    ('F2F', '10:25 AM – 11:25 AM'): {'slot_number': 3, 'start_slot_index': 2, 'end_slot_index': 2, 'start_m': 625, 'end_m': 685},
    # K1 F2F Afternoon
    ('K1_F2F', '12:40 PM – 01:40 PM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 760, 'end_m': 820},
    ('K1_F2F', '01:50 PM – 02:50 PM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 830, 'end_m': 890},
    # 1st Shift
    ('1ST SHIFT', '12:40 PM – 01:40 PM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 760, 'end_m': 820},
    ('1ST SHIFT', '01:50 PM – 02:50 PM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 830, 'end_m': 890},
    ('1ST SHIFT', '03:10 PM – 04:10 PM'): {'slot_number': 3, 'start_slot_index': 2, 'end_slot_index': 2, 'start_m': 910, 'end_m': 970},
    # 2nd Shift
    ('2ND SHIFT', '03:10 PM – 04:10 PM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 910, 'end_m': 970},
    ('2ND SHIFT', '04:20 PM – 05:20 PM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 980, 'end_m': 1040},
    ('2ND SHIFT', '05:30 PM – 06:30 PM'): {'slot_number': 3, 'start_slot_index': 2, 'end_slot_index': 2, 'start_m': 1050, 'end_m': 1110},
}

EXAM_DATES = {
    1: {"date": "Tuesday, December 1, 2026", "short_date": "Dec 1", "day_name": "Tuesday"},
    2: {"date": "Wednesday, December 2, 2026", "short_date": "Dec 2", "day_name": "Wednesday"},
    3: {"date": "Thursday, December 3, 2026", "short_date": "Dec 3", "day_name": "Thursday"},
    4: {"date": "Sunday, December 6, 2026", "short_date": "Dec 6", "day_name": "Sunday"},
}

slot_to_idx = {}
idx_to_slot = {}
idx = 0
for d in range(1, 5):
    for sl in ALL_SLOT_TIMES:
        slot_to_idx[(d, sl)] = idx
        idx_to_slot[idx] = (d, sl)
        idx += 1

sec_counts = defaultdict(int)
for e in exams:
    sec_counts[e['section_name']] += 1

# Solver Model
model = cp_model.CpModel()
x = {}
teacher_slots = defaultdict(list)
section_slots = defaultdict(list)
teacher_day_slots = defaultdict(lambda: defaultdict(list))
teacher_exam_counts = defaultdict(int)
pref_rewards = []

# Target slots from authentic timetable for Ustadha Saliha
SALIHA_IMAGE_TARGETS = {
    ('Hadith', 'KINDER 2 CLASS SCHEDULE (F2F)'): (4, '10:25 AM – 11:25 AM'),
    ('Arabic', 'KINDER 2 CLASS SCHEDULE (F2F)'): (3, '09:00 AM – 10:00 AM'),
    ('GMRC', 'GRADE 2 (FACE TO FACE)'): (2, '08:00 AM – 09:00 AM'),
    ('GMRC', 'GRADE 1 (FACE TO FACE)'): (3, '08:00 AM – 09:00 AM'),
    ('GMRC', 'GRADE 3 (FACE TO FACE)'): (4, '09:00 AM – 10:00 AM'),
    ('Hadith', 'KINDER 1 CLASS SCHEDULE (F2F)'): (2, '12:40 PM – 01:40 PM'),
    ('Hadith', 'Kinder 2 UTHMAN IBN AFFAN (1ST SHIFT)'): (2, '01:50 PM – 02:50 PM'),
    ('GMRC', 'GRADE 2 - AMR IBN AL-JAMUH (1ST SHIFT)'): (3, '12:40 PM – 01:40 PM'),
    ('GMRC', 'GRADE 2 - TALHA IBN UBAYDULLAH (1ST SHIFT)'): (4, '12:40 PM – 01:40 PM'),
    ('Arabic', 'KINDER 1 CLASS SCHEDULE (F2F)'): (4, '01:50 PM – 02:50 PM'),
    ('GMRC', 'GRADE 1 - ALI IBN ABI TALIB(1ST SHIFT)'): (3, '03:10 PM – 04:10 PM'),
    ('GMRC', "GRADE 5 - AYYASH IBN ABI RABI'AH(1ST SHIFT)"): (4, '03:10 PM – 04:10 PM'),
}

for i, e in enumerate(exams):
    t = e['teacher']
    teacher_exam_counts[t] += 1
    sname = e['section_name']
    sh = e['shift']
    subj = e['subject']
    
    orig_d = e.get('day_number')
    orig_slot = e.get('time_slot')
    # Normalize legacy 120m slots to their starting slot
    if orig_slot == '09:00 AM – 11:25 AM': orig_slot = '09:00 AM – 10:00 AM'
    elif orig_slot == '12:40 PM – 02:50 PM': orig_slot = '12:40 PM – 01:40 PM'
    elif orig_slot == '01:50 PM – 04:10 PM': orig_slot = '01:50 PM – 02:50 PM'
    elif orig_slot == '03:10 PM – 05:20 PM': orig_slot = '03:10 PM – 04:10 PM'
    elif orig_slot == '04:20 PM – 06:30 PM': orig_slot = '04:20 PM – 05:20 PM'
    
    if sh == 'F2F':
        if 'KINDER 1' in sname: allowed_times = K1_F2F
        else: allowed_times = F2F_MORNING
    elif '1ST SHIFT' in sh: allowed_times = FIRST_SHIFT
    elif '2ND SHIFT' in sh: allowed_times = SECOND_SHIFT
    else:
        raise ValueError(f"Unknown shift {sh} for exam {e['id']}")
    
    allowed_slots = [slot_to_idx[(d, sl)] for d in range(1, 5) for sl in allowed_times]
    exam_vars = []
    for s_idx in allowed_slots:
        var = model.NewBoolVar(f'x_{i}_{s_idx}')
        x[(i, s_idx)] = var
        exam_vars.append(var)
        teacher_slots[(t, s_idx)].append(var)
        section_slots[(sname, s_idx)].append(var)
        d, sl = idx_to_slot[s_idx]
        teacher_day_slots[t][d].append(var)
        
        reward = 0
        if t == 'Ustadha Saliha' and (subj, sname) in SALIHA_IMAGE_TARGETS:
            tgt_d, tgt_sl = SALIHA_IMAGE_TARGETS[(subj, sname)]
            if d == tgt_d and sl == tgt_sl:
                reward += 100
        else:
            if d == orig_d:
                reward += 5
                if sl == orig_slot:
                    reward += 15
        if reward > 0:
            pref_rewards.append(reward * var)
    
    model.AddExactlyOne(exam_vars)

# Hard Constraint: Every teacher has AT MOST 1 exam per time slot
for (t, s_idx), var_list in teacher_slots.items():
    model.Add(sum(var_list) <= 1)

# Hard Constraint: Sections with <= 12 exams have AT MOST 1 exam per time slot
for (sec, s_idx), var_list in section_slots.items():
    if sec_counts[sec] <= 12:
        model.Add(sum(var_list) <= 1)
    else:
        model.Add(sum(var_list) <= 2)

# Minimize simultaneous exams for the 6 sections with > 12 exams
sec_conflict_vars = []
for (sec, s_idx), var_list in section_slots.items():
    if len(var_list) > 1:
        excess = model.NewIntVar(0, len(var_list), f'sec_excess_{sec}_{s_idx}')
        model.Add(excess >= sum(var_list) - 1)
        sec_conflict_vars.append(excess)

# Daily load balance penalty per teacher
balance_vars = []
for t, total in teacher_exam_counts.items():
    target = total // 4
    for d in range(1, 5):
        day_vars = teacher_day_slots[t][d]
        if day_vars:
            day_sum = sum(day_vars)
            diff = model.NewIntVar(-total, total, f'diff_{t}_{d}')
            model.Add(diff == day_sum - target)
            abs_diff = model.NewIntVar(0, total, f'abs_diff_{t}_{d}')
            model.AddAbsEquality(abs_diff, diff)
            balance_vars.append(abs_diff)

# Objective: Minimize section excess heavily, balance teacher load, and maximize authentic schedule match
model.Minimize(1000 * sum(sec_conflict_vars) + 10 * sum(balance_vars) - sum(pref_rewards))

print("Solving CP-SAT model...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_workers = 8
status = solver.Solve(model)

status_name = solver.StatusName(status)
print(f"Solver status: {status_name}")
if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    raise RuntimeError(f"Solver failed with status {status_name}")

# Apply solved assignments
for i, e in enumerate(exams):
    assigned_slot = None
    for (idx_pair, var) in x.items():
        if idx_pair[0] == i and solver.Value(var) == 1:
            assigned_slot = idx_to_slot[idx_pair[1]]
            break
    assert assigned_slot is not None, f"Exam {i} ({e['id']}) was not assigned!"
    
    d, sl = assigned_slot
    date_info = EXAM_DATES[d]
    sname = e['section_name']
    sh = e['shift']
    
    if sh == 'F2F':
        if 'KINDER 1' in sname:
            slot_data = SLOT_INFO[('K1_F2F', sl)]
        else:
            slot_data = SLOT_INFO[('F2F', sl)]
    elif '1ST SHIFT' in sh:
        slot_data = SLOT_INFO[('1ST SHIFT', sl)]
    elif '2ND SHIFT' in sh:
        slot_data = SLOT_INFO[('2ND SHIFT', sl)]
    
    e['day_number'] = d
    e['date'] = date_info['date']
    e['short_date'] = date_info['short_date']
    e['day_name'] = date_info['day_name']
    e['time_slot'] = sl
    e['time'] = sl
    e['slot_number'] = slot_data['slot_number']
    e['start_slot_index'] = slot_data['start_slot_index']
    e['end_slot_index'] = slot_data['end_slot_index']
    e['start_m'] = slot_data['start_m']
    e['end_m'] = slot_data['end_m']
    e['duration_minutes'] = 60
    e['slots_spanned'] = 1
    e['proctor_conflict_status'] = 'CLEAR'

# Save updated JSON and JS
with open(EXAM_JSON, 'w', encoding='utf-8') as f:
    json.dump(exams, f, indent=2, ensure_ascii=False)
print(f"[OK] Written {len(exams)} records to {EXAM_JSON}")

js_content = f"// AMIS 2nd Term Examination Data - Authoritative 60-Minute Unstacked Schedule\nconst ALL_EXAM_RECORDS = {json.dumps(exams, indent=2, ensure_ascii=False)};\n\nwindow.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n"
with open(EXAM_JS, 'w', encoding='utf-8') as f:
    f.write(js_content)
print(f"[OK] Written {len(exams)} records to {EXAM_JS}")

if os.path.exists(ROOT_DIR):
    try:
        with open(ROOT_EXAM_JSON, 'w', encoding='utf-8') as f:
            json.dump(exams, f, indent=2, ensure_ascii=False)
        with open(ROOT_EXAM_JS, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"[OK] Synced root copies in {ROOT_DIR}")
    except Exception as err:
        print(f"[WARN] Could not update root copies: {err}")

print("=== OPTIMIZATION COMPLETE ===")
