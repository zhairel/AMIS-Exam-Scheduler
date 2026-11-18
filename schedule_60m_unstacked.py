#!/usr/bin/env python3
"""
schedule_60m_unstacked.py
Authoritative AMIS 2nd Term Examination CP-SAT Optimization Engine.

Enforces:
1. Math (Grade 6 to 10 Math, General Math 11) restored to 120 minutes (slots_spanned = 2).
2. All other subjects strictly 60 minutes (duration_minutes = 60, slots_spanned = 1).
3. Zero stacking per teacher: Strictly at most 1 exam per teacher at ANY base time slot across all 48 faculty.
4. Shift time window integrity:
   - F2F Morning: 08:00 AM – 11:25 AM
   - K1 F2F Afternoon: 12:40 PM – 02:50 PM
   - First Shift (ODL 1): 12:40 PM – 04:10 PM
   - Second Shift (ODL 2): 03:10 PM – 06:30 PM (with intentional 3:10 PM – 4:10 PM mixed overlap)
5. Preserves authentic faculty requirements (e.g. Ustadha Saliha, Teacher Nadzra).
6. Minimizes section collisions to the mathematical minimum.
7. Synchronizes exam_data_2nd_term.json and exam_data_2nd_term.js.
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

# Identify Math Grade 6-10 and General Math 11 for 120-minute duration
MATH_120_IDS = set()
for e in exams:
    subj = e['subject']
    sec = e['section_name']
    if subj in ['Math', 'Mathematics', 'General Math 11', 'General Math', 'Gen Math']:
        if any(g in sec for g in ['GRADE 6', 'GRADE  6', 'Grade 6', 'GRADE 7', 'GRADE 8', 'GRADE 9', 'GRADE 10', 'GRADE 11', 'Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11']):
            MATH_120_IDS.add(e['id'])

print(f"Designated {len(MATH_120_IDS)} Math examinations for 120-minute duration.")

EXAM_DATES = {
    1: {"date": "Tuesday, December 1, 2026", "short_date": "Dec 1", "day_name": "Tuesday"},
    2: {"date": "Wednesday, December 2, 2026", "short_date": "Dec 2", "day_name": "Wednesday"},
    3: {"date": "Thursday, December 3, 2026", "short_date": "Dec 3", "day_name": "Thursday"},
    4: {"date": "Sunday, December 6, 2026", "short_date": "Dec 6", "day_name": "Sunday"},
}

SLOT_120_DATA = {
    # F2F
    ('F2F', '09:00 AM – 11:25 AM'): {
        'slot_number': 2,
        'start_slot_index': 1,
        'end_slot_index': 2,
        'start_m': 540,
        'end_m': 685,
        'duration_minutes': 120,
        'slots_spanned': 2,
        'base_slots': ['09:00 AM – 10:00 AM', '10:25 AM – 11:25 AM']
    },
    # 1st Shift
    ('1ST SHIFT', '12:40 PM – 02:50 PM'): {
        'slot_number': 1,
        'start_slot_index': 0,
        'end_slot_index': 1,
        'start_m': 760,
        'end_m': 890,
        'duration_minutes': 120,
        'slots_spanned': 2,
        'base_slots': ['12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM']
    },
    ('1ST SHIFT', '01:50 PM – 04:10 PM'): {
        'slot_number': 2,
        'start_slot_index': 1,
        'end_slot_index': 2,
        'start_m': 830,
        'end_m': 970,
        'duration_minutes': 120,
        'slots_spanned': 2,
        'base_slots': ['01:50 PM – 02:50 PM', '03:10 PM – 04:10 PM']
    },
    # 2nd Shift
    ('2ND SHIFT', '03:10 PM – 05:20 PM'): {
        'slot_number': 1,
        'start_slot_index': 0,
        'end_slot_index': 1,
        'start_m': 910,
        'end_m': 1040,
        'duration_minutes': 120,
        'slots_spanned': 2,
        'base_slots': ['03:10 PM – 04:10 PM', '04:20 PM – 05:20 PM']
    },
    ('2ND SHIFT', '04:20 PM – 06:30 PM'): {
        'slot_number': 2,
        'start_slot_index': 1,
        'end_slot_index': 2,
        'start_m': 980,
        'end_m': 1110,
        'duration_minutes': 120,
        'slots_spanned': 2,
        'base_slots': ['04:20 PM – 05:20 PM', '05:30 PM – 06:30 PM']
    },
}

SLOT_60_DATA = {
    # F2F Morning
    ('F2F', '08:00 AM – 09:00 AM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 480, 'end_m': 540, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['08:00 AM – 09:00 AM']},
    ('F2F', '09:00 AM – 10:00 AM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 540, 'end_m': 600, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['09:00 AM – 10:00 AM']},
    ('F2F', '10:25 AM – 11:25 AM'): {'slot_number': 3, 'start_slot_index': 2, 'end_slot_index': 2, 'start_m': 625, 'end_m': 685, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['10:25 AM – 11:25 AM']},
    # K1 F2F Afternoon
    ('K1_F2F', '12:40 PM – 01:40 PM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 760, 'end_m': 820, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['12:40 PM – 01:40 PM']},
    ('K1_F2F', '01:50 PM – 02:50 PM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 830, 'end_m': 890, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['01:50 PM – 02:50 PM']},
    # 1st Shift
    ('1ST SHIFT', '12:40 PM – 01:40 PM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 760, 'end_m': 820, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['12:40 PM – 01:40 PM']},
    ('1ST SHIFT', '01:50 PM – 02:50 PM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 830, 'end_m': 890, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['01:50 PM – 02:50 PM']},
    ('1ST SHIFT', '03:10 PM – 04:10 PM'): {'slot_number': 3, 'start_slot_index': 2, 'end_slot_index': 2, 'start_m': 910, 'end_m': 970, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['03:10 PM – 04:10 PM']},
    # 2nd Shift
    ('2ND SHIFT', '03:10 PM – 04:10 PM'): {'slot_number': 1, 'start_slot_index': 0, 'end_slot_index': 0, 'start_m': 910, 'end_m': 970, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['03:10 PM – 04:10 PM']},
    ('2ND SHIFT', '04:20 PM – 05:20 PM'): {'slot_number': 2, 'start_slot_index': 1, 'end_slot_index': 1, 'start_m': 980, 'end_m': 1040, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['04:20 PM – 05:20 PM']},
    ('2ND SHIFT', '05:30 PM – 06:30 PM'): {'slot_number': 3, 'start_slot_index': 2, 'end_slot_index': 2, 'start_m': 1050, 'end_m': 1110, 'duration_minutes': 60, 'slots_spanned': 1, 'base_slots': ['05:30 PM – 06:30 PM']},
}

model = cp_model.CpModel()
x = {}
exam_option_map = {}
teacher_base_slots = defaultdict(list)
section_base_slots = defaultdict(list)
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
    is_120 = e['id'] in MATH_120_IDS
    
    orig_d = e.get('day_number')
    orig_slot = e.get('time_slot')
    
    candidate_options = []
    for d in range(1, 5):
        if is_120:
            if sh == 'F2F':
                candidate_options.append(('09:00 AM – 11:25 AM', d, SLOT_120_DATA[('F2F', '09:00 AM – 11:25 AM')]))
            elif '1ST SHIFT' in sh:
                candidate_options.append(('12:40 PM – 02:50 PM', d, SLOT_120_DATA[('1ST SHIFT', '12:40 PM – 02:50 PM')]))
                candidate_options.append(('01:50 PM – 04:10 PM', d, SLOT_120_DATA[('1ST SHIFT', '01:50 PM – 04:10 PM')]))
            elif '2ND SHIFT' in sh:
                candidate_options.append(('03:10 PM – 05:20 PM', d, SLOT_120_DATA[('2ND SHIFT', '03:10 PM – 05:20 PM')]))
                candidate_options.append(('04:20 PM – 06:30 PM', d, SLOT_120_DATA[('2ND SHIFT', '04:20 PM – 06:30 PM')]))
        else:
            if sh == 'F2F':
                if 'KINDER 1' in sname:
                    sh_key = 'K1_F2F'
                    times = ['12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM']
                else:
                    sh_key = 'F2F'
                    times = ['08:00 AM – 09:00 AM', '09:00 AM – 10:00 AM', '10:25 AM – 11:25 AM']
            elif '1ST SHIFT' in sh:
                sh_key = '1ST SHIFT'
                times = ['12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM', '03:10 PM – 04:10 PM']
            elif '2ND SHIFT' in sh:
                sh_key = '2ND SHIFT'
                times = ['03:10 PM – 04:10 PM', '04:20 PM – 05:20 PM', '05:30 PM – 06:30 PM']
            for sl in times:
                candidate_options.append((sl, d, SLOT_60_DATA[(sh_key, sl)]))
    
    exam_vars = []
    for opt_idx, (slot_label, d, s_data) in enumerate(candidate_options):
        var = model.NewBoolVar(f'x_{i}_{d}_{opt_idx}')
        x[(i, d, slot_label)] = var
        exam_option_map[(i, d, slot_label)] = s_data
        exam_vars.append(var)
        teacher_day_slots[t][d].append(var)
        
        for b_slot in s_data['base_slots']:
            teacher_base_slots[(t, d, b_slot)].append(var)
            section_base_slots[(sname, d, b_slot)].append(var)
            
        reward = 0
        if t == 'Ustadha Saliha' and (subj, sname) in SALIHA_IMAGE_TARGETS:
            tgt_d, tgt_sl = SALIHA_IMAGE_TARGETS[(subj, sname)]
            if d == tgt_d and slot_label == tgt_sl:
                reward += 100
        else:
            if d == orig_d:
                reward += 5
                if slot_label == orig_slot:
                    reward += 15
        if reward > 0:
            pref_rewards.append(reward * var)
            
    model.AddExactlyOne(exam_vars)

# Hard constraint: Every teacher has AT MOST 1 exam at ANY base time slot
for (t, d, b_slot), var_list in teacher_base_slots.items():
    model.Add(sum(var_list) <= 1)

# Minimize section collisions across base time slots
sec_conflict_vars = []
for (sec, d, b_slot), var_list in section_base_slots.items():
    if len(var_list) > 1:
        excess = model.NewIntVar(0, len(var_list), f'sec_excess_{sec}_{d}_{b_slot}')
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

model.Minimize(1000 * sum(sec_conflict_vars) + 10 * sum(balance_vars) - sum(pref_rewards))

print("Solving CP-SAT optimization model...")
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
    assigned = None
    for (idx_triple, var) in x.items():
        if idx_triple[0] == i and solver.Value(var) == 1:
            assigned = idx_triple
            break
    assert assigned is not None, f"Exam {i} ({e['id']}) was not assigned!"
    
    _, d, slot_label = assigned
    s_data = exam_option_map[assigned]
    date_info = EXAM_DATES[d]
    
    e['day_number'] = d
    e['date'] = date_info['date']
    e['short_date'] = date_info['short_date']
    e['day_name'] = date_info['day_name']
    e['time_slot'] = slot_label
    e['time'] = slot_label
    e['slot_number'] = s_data['slot_number']
    e['start_slot_index'] = s_data['start_slot_index']
    e['end_slot_index'] = s_data['end_slot_index']
    e['start_m'] = s_data['start_m']
    e['end_m'] = s_data['end_m']
    e['duration_minutes'] = s_data['duration_minutes']
    e['slots_spanned'] = s_data['slots_spanned']
    e['proctor_conflict_status'] = 'CLEAR'

# Save updated JSON and JS
with open(EXAM_JSON, 'w', encoding='utf-8') as f:
    json.dump(exams, f, indent=2, ensure_ascii=False)
print(f"[OK] Written {len(exams)} records to {EXAM_JSON}")

js_content = f"// AMIS 2nd Term Examination Data - Authoritative Schedule\nconst ALL_EXAM_RECORDS = {json.dumps(exams, indent=2, ensure_ascii=False)};\n\nwindow.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n"
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
