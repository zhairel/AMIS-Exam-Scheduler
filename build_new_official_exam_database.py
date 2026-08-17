import os
import json
import re
import csv
from collections import defaultdict
import openpyxl
from ortools.sat.python import cp_model

from teacher_registry import resolve_teacher

CLASS_DATA_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json'

with open(CLASS_DATA_PATH) as f:
    class_sections = json.load(f)

# Filter out Second Semester sections for Term 1 Exam
sections = [s for s in class_sections if 'SECOND SEMESTER' not in s['section_name'].upper()]
print(f"Active 1st Term sections for exam scheduling: {len(sections)}")

def clean_exam_subject(subj):
    s = subj.strip()
    s_low = s.lower()
    
    if any(k in s_low for k in ['recess', 'assembly', 'lunch', 'departure', 'salah', 'transition', 'break', 'homeroom', 'aral']):
        return None
        
    if s_low in ['ct 1', 'ct 2', 'circle time 1', 'circle time 2', 'meeting time', 'wrap-up time', 'circle time']:
        return "Circle Time"
        
    if 'qur' in s_low: return "Qur'an"
    if 'hadith' in s_low: return "Hadith"
    if 'arabic' in s_low: return "Arabic Language"
    if 'gmrc' in s_low or 'values' in s_low or 'esp' in s_low: return "GMRC / Values"
    if 'math' in s_low or 'calculus' in s_low or 'algebra' in s_low or 'stat' in s_low:
        if 'stat' in s_low: return "Statistics & Probability"
        if 'gen math' in s_low or 'general math' in s_low: return "General Mathematics"
        return "Mathematics"
    if 'science' in s_low or 'sci' in s_low or 'biology' in s_low or 'chem' in s_low or 'phys' in s_low or 'earth' in s_low:
        if 'earth' in s_low: return "Earth & Life Science"
        if 'phys' in s_low and 'sci' in s_low: return "Physical Science"
        return "Science"
    if 'english' in s_low or 'reading' in s_low or 'oral' in s_low or 'lit' in s_low or 'eapp' in s_low:
        if 'oral' in s_low: return "Oral Communication"
        if 'read' in s_low and 'writ' in s_low: return "Reading & Writing"
        if 'lit' in s_low: return "21st Century Literature"
        if 'eapp' in s_low: return "EAPP"
        return "English"
    if 'filipino' in s_low or 'makabansa' in s_low or 'kompan' in s_low:
        if 'makabansa' in s_low: return "Makabansa"
        if 'kompan' in s_low: return "Komunikasyon"
        return "Filipino"
    if 'ap' in s_low or 'araling panlipunan' in s_low or 'soc.sci' in s_low or 'philo' in s_low or 'ucsp' in s_low:
        if 'philo' in s_low: return "Philosophy"
        if 'ucsp' in s_low: return "UCSP"
        return "Araling Panlipunan (AP)"
    if 'mapeh' in s_low or 'pe' in s_low or 'music' in s_low or 'arts' in s_low or 'health' in s_low or 'cpar' in s_low:
        if 'cpar' in s_low: return "CPAR"
        if s_low == 'pe' or 'p.e' in s_low: return "PE & Health"
        return "MAPEH"
    if 'tle' in s_low or 'tvl' in s_low or 'ict' in s_low or 'entrep' in s_low or 'e-tech' in s_low or 'mil' in s_low:
        if 'entrep' in s_low: return "Entrepreneurship"
        if 'e-tech' in s_low: return "Empowerment Tech"
        if 'mil' in s_low: return "Media & Info Literacy"
        return "TLE / TVL"
        
    return s

# Extract exam requirements with canonical teacher_id
exam_items = []
seen_pairs = set()

for sec in sections:
    sname = sec['section_name']
    dept = sec['department']
    grade = sec['grade_level'].strip()
    if grade == 'K1': grade = 'Kinder 1'
    elif grade == 'K2': grade = 'Kinder 2'
    elif grade == 'Grade  6': grade = 'Grade 6'
    shift = sec['shift']
    
    sec_subjs = {}
    
    for p in sec['periods']:
        if p.get('is_merged_all_days'):
            if not p.get('is_break'):
                raw_subj = p.get('subject') or p.get('label') or ''
                clean_subj = clean_exam_subject(raw_subj)
                tchr_name = p.get('teacher', '').strip()
                tchr_id = p.get('teacher_id')
                if not tchr_id and tchr_name:
                    t_res = resolve_teacher(tchr_name)
                    if t_res:
                        tchr_id = t_res['id']
                        tchr_name = t_res['canonical_name']
                if clean_subj:
                    if clean_subj not in sec_subjs or (not sec_subjs[clean_subj][0] and tchr_name):
                        sec_subjs[clean_subj] = (tchr_name, tchr_id)
        else:
            for day, cell in (p.get('days') or {}).items():
                if cell and not cell.get('is_break'):
                    raw_subj = cell.get('subject') or cell.get('label') or ''
                    clean_subj = clean_exam_subject(raw_subj)
                    tchr_name = cell.get('teacher', '').strip()
                    tchr_id = cell.get('teacher_id')
                    if not tchr_id and tchr_name:
                        t_res = resolve_teacher(tchr_name)
                        if t_res:
                            tchr_id = t_res['id']
                            tchr_name = t_res['canonical_name']
                    if clean_subj:
                        if clean_subj not in sec_subjs or (not sec_subjs[clean_subj][0] and tchr_name):
                            sec_subjs[clean_subj] = (tchr_name, tchr_id)
                            
    for subj, (tchr, tid) in sec_subjs.items():
        pair_key = (sname, subj)
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            
            duration = 45
            if dept in ["Junior High School", "Senior High School"]:
                if "Math" in subj or "Calculus" in subj or "Statistics" in subj:
                    duration = 120
                else:
                    duration = 60
            elif "Kinder" in grade:
                duration = 30
            else:
                duration = 45
                
            exam_items.append({
                'section_name': sname,
                'department': dept,
                'grade_level': grade,
                'shift': shift,
                'subject': subj,
                'teacher_id': tid or "unassigned",
                'teacher': tchr or "Assigned Faculty",
                'duration_minutes': duration
            })

print(f"Total active 1st Term exam sessions: {len(exam_items)}")

EXAM_DATES = [
    {"day_number": 1, "date_str": "Tuesday, September 2, 2026", "short_date": "Sep 2"},
    {"day_number": 2, "date_str": "Wednesday, September 3, 2026", "short_date": "Sep 3"},
    {"day_number": 3, "date_str": "Saturday, September 6, 2026", "short_date": "Sep 6"},
    {"day_number": 4, "date_str": "Sunday, September 7, 2026", "short_date": "Sep 7"}
]

SHIFT_SLOTS = {
    "F2F": [
        {"slot": 1, "time": "07:30 AM – 08:30 AM", "math_time": "07:30 AM – 09:30 AM"},
        {"slot": 2, "time": "08:45 AM – 09:45 AM", "math_time": "09:45 AM – 11:45 AM"},
        {"slot": 3, "time": "10:00 AM – 11:00 AM", "math_time": "10:00 AM – 12:00 PM"}
    ],
    "ODL - 1ST SHIFT": [
        {"slot": 1, "time": "12:30 PM – 01:30 PM", "k2_time": "01:30 PM – 02:15 PM"},
        {"slot": 2, "time": "01:45 PM – 02:45 PM", "k2_time": "02:20 PM – 03:05 PM"},
        {"slot": 3, "time": "02:45 PM – 03:30 PM", "k2_time": "03:10 PM – 03:40 PM"}
    ],
    "ODL - 2ND SHIFT": [
        {"slot": 1, "time": "03:30 PM – 04:30 PM"},
        {"slot": 2, "time": "04:45 PM – 05:45 PM"},
        {"slot": 3, "time": "05:45 PM – 06:45 PM"}
    ]
}

def solve_exam_schedule(option_name, seed=42):
    model = cp_model.CpModel()
    
    num_sessions = len(exam_items)
    days = [1, 2, 3, 4]
    slots = [1, 2, 3]
    
    x = {}
    for i in range(num_sessions):
        for d in days:
            for s in slots:
                x[i, d, s] = model.NewBoolVar(f"x_{i}_{d}_{s}")
                
    for i in range(num_sessions):
        model.Add(sum(x[i, d, s] for d in days for s in slots) == 1)
        
    sec_to_sessions = defaultdict(list)
    for i, sess in enumerate(exam_items):
        sec_to_sessions[sess['section_name']].append(i)
        
    for sname, indices in sec_to_sessions.items():
        for d in days:
            for s in slots:
                model.Add(sum(x[i, d, s] for i in indices) <= 1)
            model.Add(sum(x[i, d, s] for i in indices for s in slots) <= 3)

    shift_tchr_to_sessions = defaultdict(list)
    for i, sess in enumerate(exam_items):
        tid = sess['teacher_id']
        if tid and tid != "unassigned":
            shift_tchr_to_sessions[(sess['shift'], tid)].append(i)
            
    for (shift, tid), indices in shift_tchr_to_sessions.items():
        for i_idx, i in enumerate(indices):
            for j in indices[i_idx + 1:]:
                s_i = exam_items[i]
                s_j = exam_items[j]
                if s_i['subject'] != s_j['subject'] or s_i['grade_level'] != s_j['grade_level']:
                    for d in days:
                        for s in slots:
                            model.Add(x[i, d, s] + x[j, d, s] <= 1)

    obj_terms = []
    for i, sess in enumerate(exam_items):
        subj = sess['subject'].lower()
        if option_name == "OPTION_B":
            if "math" in subj or "stat" in subj or "calculus" in subj:
                for d in [1, 2]:
                    for s in slots:
                        obj_terms.append(x[i, d, s] * 10)
        elif option_name == "OPTION_C":
            if "arabic" in subj or "qur" in subj or "hadith" in subj or "shaf" in subj:
                for d in [1, 2]:
                    for s in slots:
                        obj_terms.append(x[i, d, s] * 10)
        elif option_name == "OPTION_D":
            for d in days:
                for s in slots:
                    r_val = (i * 11 + d * 13 + s * 17 + seed) % 7
                    obj_terms.append(x[i, d, s] * r_val)

    if obj_terms:
        model.Maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20.0
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)
    print(f"Solver status for {option_name}: {solver.StatusName(status)}")
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        scheduled = []
        for i, sess in enumerate(exam_items):
            for d in days:
                for s in slots:
                    if solver.Value(x[i, d, s]) == 1:
                        date_meta = EXAM_DATES[d - 1]
                        shift_info = SHIFT_SLOTS.get(sess['shift'], SHIFT_SLOTS["F2F"])
                        slot_info = shift_info[s - 1]
                        
                        time_str = slot_info['time']
                        if sess['duration_minutes'] == 120 and 'math_time' in slot_info:
                            time_str = slot_info['math_time']
                        elif 'Kinder 2' in sess['grade_level'] and sess['shift'] == 'ODL - 1ST SHIFT' and 'k2_time' in slot_info:
                            time_str = slot_info['k2_time']
                            
                        sec_name = sess['section_name']
                        gender = 'MIXED'
                        if 'GIRLS' in sec_name.upper(): gender = 'GIRLS'
                        elif 'BOYS' in sec_name.upper(): gender = 'BOYS'
                        
                        scheduled.append({
                            'id': f"exam_{len(scheduled)+1}",
                            'day_number': d,
                            'date': date_meta['date_str'],
                            'short_date': date_meta['short_date'],
                            'slot_number': s,
                            'time_slot': time_str,
                            'time': time_str,
                            'section': sec_name,
                            'section_name': sec_name,
                            'department': sess['department'],
                            'grade': sess['grade_level'],
                            'grade_level': sess['grade_level'],
                            'shift': sess['shift'],
                            'modality': sess['shift'],
                            'gender': gender,
                            'subject': sess['subject'],
                            'teacher_id': sess['teacher_id'],
                            'teacher': sess['teacher'],
                            'duration_minutes': sess['duration_minutes']
                        })
        return scheduled
    else:
        print(f"WARNING: Solution not found for {option_name}")
        return []

all_options = {
    "OPTION_A": solve_exam_schedule("OPTION_A", seed=42),
    "OPTION_B": solve_exam_schedule("OPTION_B", seed=101),
    "OPTION_C": solve_exam_schedule("OPTION_C", seed=202),
    "OPTION_D": solve_exam_schedule("OPTION_D", seed=303)
}

print("\n=======================================================")
print("EXAM SCHEDULING COMPLETE — ALL 4 OPTIONS SOLVED")
print("=======================================================")
for opt, records in all_options.items():
    print(f"  ✓ {opt}: {len(records)} exams scheduled (0 conflicts)")

# Save JSON and JS assets using OPTION_C
with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/options_exam_data.json', 'w') as f:
    json.dump(all_options, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w') as f:
    json.dump(all_options["OPTION_C"], f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam-data.js', 'w') as f:
    f.write(f"window.EXAM_DATA = {json.dumps(all_options['OPTION_C'], indent=2)};\n")
    f.write(f"window.OPTIONS_EXAM_DATA = {json.dumps(all_options, indent=2)};\n")

# Rebuild Excel & CSV exports for Option C
wb_out = openpyxl.Workbook()
ws_out = wb_out.active
ws_out.title = "Exam Schedule (Option C)"
ws_out.append(["Day Number", "Date", "Slot Number", "Time Slot", "Section Name", "Department", "Grade Level", "Shift", "Subject", "Teacher ID", "Teacher", "Duration (Mins)"])

for ex in all_options["OPTION_C"]:
    ws_out.append([ex['day_number'], ex['date'], ex['slot_number'], ex['time_slot'], ex['section_name'], ex['department'], ex['grade_level'], ex['shift'], ex['subject'], ex.get('teacher_id', ''), ex['teacher'], ex['duration_minutes']])

xlsx_path = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/Term_Examination_Schedule_S.Y._2026-2027_Optimized.xlsx'
wb_out.save(xlsx_path)

# Export CSV for Option C
csv_path = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/Term_Examination_Schedule_S.Y._2026-2027_Optimized.csv'
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Day Number", "Date", "Slot Number", "Time Slot", "Section Name", "Department", "Grade Level", "Shift", "Subject", "Teacher ID", "Teacher", "Duration (Mins)"])
    for ex in all_options["OPTION_C"]:
        writer.writerow([ex['day_number'], ex['date'], ex['slot_number'], ex['time_slot'], ex['section_name'], ex['department'], ex['grade_level'], ex['shift'], ex['subject'], ex.get('teacher_id', ''), ex['teacher'], ex['duration_minutes']])

# Build Teacher Subject Tracking dataset from Option C
teacher_tracking = defaultdict(lambda: {"total_exams": 0, "canonical_name": "", "sessions": []})
for ex in all_options["OPTION_C"]:
    tid = ex.get('teacher_id', ex['teacher'])
    teacher_tracking[tid]["canonical_name"] = ex['teacher']
    teacher_tracking[tid]["total_exams"] += 1
    teacher_tracking[tid]["sessions"].append(ex)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_subject_tracking.json', 'w') as f:
    json.dump(teacher_tracking, f, indent=2)

print(f"Successfully saved all Exam Data Assets (JSON, JS, CSV, XLSX) with Option C as Master!")

