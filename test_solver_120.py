import os
import json
import re
from collections import defaultdict
from ortools.sat.python import cp_model
from teacher_registry import resolve_teacher

BASE_DIR = '/home/tatsuya/Projects/AMIS/amis_exam_calendar'
with open(os.path.join(BASE_DIR, 'class_schedules_data.json'), 'r', encoding='utf-8') as f:
    sections = json.load(f)

def normalize_exam_subject(raw_s, grade_level, dept):
    if not raw_s: return None
    s = raw_s.upper().strip()
    s = re.sub(r'\s*\([^)]*\)', '', s).strip()
    if any(k in s for k in ['GENERAL ASSEMBLY', 'RECESS', 'TRANSITION', 'LUNCH', 'DEPARTURE', 'SALAH', 'HOMEROOM', 'HG', 'DISMISSAL', 'MEETING TIME', 'WRAP-UP TIME', 'ARAL']):
        return None
    if 'Senior High' in dept: return raw_s.strip()
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
            if 'KHABAAB' in sec_name.upper() and subj_name == 'Arabic': tchr_name = 'Ustadh Faidh'
            t_res = resolve_teacher(tchr_name)
            all_exam_items.append({
                'section_id': sec_id, 'section_name': sec_name, 'department': dept, 'grade_level': grade, 'shift': shift,
                'subject': subj_name, 'teacher': t_res['canonical_name'] if t_res else tchr_name,
                'teacher_id': t_res['id'] if t_res else 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', tchr_name).strip('_').lower(),
                'duration_minutes': 60, 'slots_needed': 1
            })
    else:
        for subj_name, tchrs in sec_subjs.items():
            valid_tchrs = [t for t in tchrs if t]
            tchr_name = valid_tchrs[0] if valid_tchrs else 'Assigned Faculty'
            if 'AS\'AD' in sec_name.upper() or 'AS`AD' in sec_name.upper() or 'ASAD' in sec_name.upper():
                if subj_name == 'GMRC': tchr_name = 'Ustadha Saliha'
                if subj_name == 'Arabic': tchr_name = 'Ustadh Faidh'
            if 'DIHYA' in sec_name.upper():
                if subj_name == 'Math': tchr_name = 'Teacher Saimona'
                if subj_name == 'SHAF': tchr_name = 'Ustadh Faidh'
            if 'USAYD' in sec_name.upper():
                if subj_name == 'English': tchr_name = 'Teacher Jenny'

            t_res = resolve_teacher(tchr_name)
            item_key = (sec_id, subj_name.upper())
            if item_key in seen_items: continue
            seen_items.add(item_key)
            
            is_hs_or_shs = 'High School' in dept or 'Senior High' in dept or any(g in grade for g in ['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'])
            is_math = any(m in subj_name.lower() for m in ['math', 'mathematics', 'calculus', 'statistics'])
            duration_mins = 120 if (is_hs_or_shs and is_math) else 60
            slots_needed = 2 if duration_mins == 120 else 1

            all_exam_items.append({
                'section_id': sec_id, 'section_name': sec_name, 'department': dept, 'grade_level': grade, 'shift': shift,
                'subject': subj_name, 'teacher': t_res['canonical_name'] if t_res else tchr_name,
                'teacher_id': t_res['id'] if t_res else 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', tchr_name).strip('_').lower(),
                'duration_minutes': duration_mins, 'slots_needed': slots_needed
            })

print(f'Total items: {len(all_exam_items)}, items needing 2 slots (120min Math): {sum(1 for i in all_exam_items if i["slots_needed"] == 2)}')

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

# Decision variable: start_slot for item i on day d
# If item i needs 2 slots, valid start_slot s_idx must satisfy s_idx + 1 < len(slots)
x = {}
for i, item in enumerate(all_exam_items):
    slots = get_slots_for_item(item)
    k = item['slots_needed']
    for d in DAYS:
        for s_idx in range(len(slots) - k + 1):
            x[i, d, s_idx] = model.NewBoolVar(f'x_{i}_{d}_{s_idx}')

# Constraint 1: Exactly one start assignment per exam item
for i, item in enumerate(all_exam_items):
    slots = get_slots_for_item(item)
    k = item['slots_needed']
    model.AddExactlyOne(x[i, d, s_idx] for d in DAYS for s_idx in range(len(slots) - k + 1))

# Constraint 2: Section constraint (at most 1 exam occupying any slot, max daily units <= 3 or 4)
by_sec = defaultdict(list)
for i, item in enumerate(all_exam_items):
    by_sec[item['section_id']].append(i)

for sec_id, items in by_sec.items():
    slots = get_slots_for_item(all_exam_items[items[0]])
    num_slots = len(slots)
    for d in DAYS:
        for s in range(num_slots):
            # Sum of all exams covering slot s
            occupying = []
            for i in items:
                k = all_exam_items[i]['slots_needed']
                # start slots that cover s: s_start <= s <= s_start + k - 1
                for s_start in range(max(0, s - k + 1), min(s + 1, num_slots - k + 1)):
                    occupying.append(x[i, d, s_start])
            model.Add(sum(occupying) <= 1)
            
        max_daily_units = 4 if 'Senior High' in all_exam_items[items[0]]['department'] else 3
        daily_units = []
        for i in items:
            k = all_exam_items[i]['slots_needed']
            for s_start in range(num_slots - k + 1):
                daily_units.append(x[i, d, s_start] * k)
        model.Add(sum(daily_units) <= max_daily_units)

# Constraint 3: Same-shift teacher conflict (Strictly 0 conflict)
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
    num_slots = len(slots)
    for d in DAYS:
        for s in range(num_slots):
            occupying = []
            for i in items:
                k = all_exam_items[i]['slots_needed']
                for s_start in range(max(0, s - k + 1), min(s + 1, num_slots - k + 1)):
                    occupying.append(x[i, d, s_start])
            model.Add(sum(occupying) <= 1)

print("Solving CP-SAT model with 120-minute 2-slot Math...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 45.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Error: Infeasible schedule!")
    exit(1)

print("✓ Feasible solution found!")

# Verify Grade 9 & 10 Boys Math
g910_items = [i for i, item in enumerate(all_exam_items) if 'Grade 9 & 10 Boys' in item['section_name'] or 'GRADE 9 & 10 BOYS' in item['section_name']]
for i in g910_items:
    item = all_exam_items[i]
    slots = get_slots_for_item(item)
    k = item['slots_needed']
    for d in DAYS:
        for s_start in range(len(slots) - k + 1):
            if solver.Value(x[i, d, s_start]) == 1:
                start_str = slots[s_start]['time_slot'].split('–')[0].trim() if hasattr(slots[s_start]['time_slot'], 'trim') else slots[s_start]['time_slot'].split('–')[0].strip()
                end_str = slots[s_start + k - 1]['time_slot'].split('–')[1].strip()
                print(f"Day {d} | {start_str} – {end_str} ({item['duration_minutes']} min.) | {item['subject']} | {item['teacher']}")
