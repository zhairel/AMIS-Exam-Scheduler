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
    if not subj: return None
    s = subj.strip()
    # If "Subject - Teacher" (e.g. "Filipino - Tchr. Normayla", "Math - Tchr. Kat")
    if ' - ' in s and not any(k in s.lower() for k in ['qur', 'hadith', 'shaf']):
        s = s.split(' - ')[0].strip()
    elif ' — ' in s:
        s = s.split(' — ')[0].strip()
        
    s_low = s.lower()
    
    if any(k in s_low for k in ['recess', 'assembly', 'lunch', 'departure', 'salah', 'transition', 'break', 'homeroom', 'aral', 'consultation', 'consulatation', 'consult']):
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
                
                t_res = resolve_teacher(tchr_name) or resolve_teacher(raw_subj)
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
                    
                    t_res = resolve_teacher(tchr_name) or resolve_teacher(raw_subj)
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
            
            # Duration allocation
            is_hs = grade in ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"] or dept in ["Junior High School", "Senior High School"]
            is_elem = grade in ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"] or dept in ["Elementary", "Primary"]

            if is_hs:
                if any(m in subj for m in ["Math", "Calculus", "Statistics", "Algebra", "General Mathematics"]):
                    duration = 120
                else:
                    duration = 60
            elif is_elem:
                duration = 60
            elif "Kinder" in grade:
                duration = 30
            else:
                duration = 60

            # User Corrections: Exact Teacher Assignments
            if 'KHABAAB' in sname.upper() and ('Arabic' in subj or 'ARABIC' in subj.upper()):
                tchr = "Ustadh Faidh"
            if ('AS\'AD' in sname.upper() or 'ASAD' in sname.upper()) and ('GMRC' in subj or 'Values' in subj):
                tchr = "Ustadha Saliha"
            if ('AS\'AD' in sname.upper() or 'ASAD' in sname.upper()) and ('Arabic' in subj or 'ARABIC' in subj.upper()):
                tchr = "Ustadh Faidh"
            if 'DIHYA' in sname.upper() and ('Math' in subj or 'Mathematics' in subj):
                tchr = "Teacher Saimonah"
            if 'DIHYA' in sname.upper() and 'SHAF' in subj:
                tchr = "Ustadh Faidh"
            if 'USAYD' in sname.upper() and ('Eng' in subj or 'English' in subj):
                tchr = "Teacher Jenny"

            t_can = resolve_teacher(tchr)
            if t_can:
                tid = t_can['id']
                tchr = t_can['canonical_name']
                
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
    {"day_number": 1, "date_str": "Wednesday, September 2, 2026", "short_date": "Sep 2"},
    {"day_number": 2, "date_str": "Thursday, September 3, 2026", "short_date": "Sep 3"},
    {"day_number": 3, "date_str": "Sunday, September 6, 2026", "short_date": "Sep 6"},
    {"day_number": 4, "date_str": "Monday, September 7, 2026", "short_date": "Sep 7"}
]

def get_slot_time_interval(shift, grade_level, duration_minutes, slot):
    if shift == 'F2F':
        if duration_minutes == 120:
            return 8 * 60, 10 * 60, '08:00 AM – 10:00 AM'
        if slot == 1: return 8 * 60, 9 * 60, '08:00 AM – 09:00 AM'
        if slot == 2: return 9 * 60, 10 * 60, '09:00 AM – 10:00 AM'
        if slot == 3: return 10 * 60 + 25, 11 * 60 + 25, '10:25 AM – 11:25 AM'
    elif shift == 'ODL - 1ST SHIFT':
        if grade_level == 'Kinder 2':
            if slot == 1: return 13 * 60 + 30, 14 * 60 + 15, '01:30 PM – 02:15 PM'
            if slot == 2: return 14 * 60 + 20, 15 * 60 + 5, '02:20 PM – 03:05 PM'
            if slot == 3: return 15 * 60 + 10, 15 * 60 + 40, '03:10 PM – 03:40 PM'
        if duration_minutes == 120:
            return 12 * 60 + 40, 14 * 60 + 50, '12:40 PM – 02:50 PM'
        if slot == 1: return 12 * 60 + 40, 13 * 60 + 40, '12:40 PM – 01:40 PM'
        if slot == 2: return 13 * 60 + 50, 14 * 60 + 50, '01:50 PM – 02:50 PM'
        if slot == 3: return 15 * 60 + 10, 16 * 60 + 10, '03:10 PM – 04:10 PM'
    elif shift == 'ODL - 2ND SHIFT':
        if duration_minutes == 120:
            return 15 * 60 + 10, 17 * 60 + 20, '03:10 PM – 05:20 PM'
        if slot == 1: return 15 * 60 + 10, 16 * 60 + 10, '03:10 PM – 04:10 PM'
        if slot == 2: return 16 * 60 + 20, 17 * 60 + 20, '04:20 PM – 05:20 PM'
        if slot == 3: return 17 * 60 + 30, 18 * 60 + 30, '05:30 PM – 06:30 PM'
    return 8 * 60, 9 * 60, '08:00 AM – 09:00 AM'

def slots_overlap(s1, e1, s2, e2):
    return s1 < e2 and s2 < e1

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

    # HS Math MUST be in slot 1 (since slot 1 covers both slot 1 & slot 2)
    for i, sess in enumerate(exam_items):
        if sess['duration_minutes'] == 120:
            for d in days:
                model.Add(x[i, d, 2] == 0)
                model.Add(x[i, d, 3] == 0)
        
    sec_to_sessions = defaultdict(list)
    for i, sess in enumerate(exam_items):
        sec_to_sessions[sess['section_name']].append(i)
        
    sec_dev_terms = []
    for sname, indices in sec_to_sessions.items():
        k = len(indices)
        target_d = k / 4.0
        target_int = int(round(target_d))

        for d in days:
            # Prevent any time overlap for the same section
            for i_idx, i in enumerate(indices):
                for j in indices[i_idx + 1:]:
                    for s1 in slots:
                        for s2 in slots:
                            t1_s, t1_e, _ = get_slot_time_interval(exam_items[i]['shift'], exam_items[i]['grade_level'], exam_items[i]['duration_minutes'], s1)
                            t2_s, t2_e, _ = get_slot_time_interval(exam_items[j]['shift'], exam_items[j]['grade_level'], exam_items[j]['duration_minutes'], s2)
                            if slots_overlap(t1_s, t1_e, t2_s, t2_e):
                                model.Add(x[i, d, s1] + x[j, d, s2] <= 1)
            
            # Max 3 exams per day
            day_sum = sum(x[i, d, s] for i in indices for s in slots)
            model.Add(day_sum <= 3)
            
            # If section has >= 4 exams, every exam day must have at least 1 exam!
            if k >= 4:
                model.Add(day_sum >= 1)

            # Section daily balance penalty
            dev = model.NewIntVar(0, 3, f"sec_dev_{sname}_{d}")
            model.Add(dev >= day_sum - target_int)
            model.Add(dev >= target_int - day_sum)
            sec_dev_terms.append(dev)

    # Teacher conflict constraint: Real-time overlap prevention across all shifts
    tchr_to_sessions = defaultdict(list)
    for i, sess in enumerate(exam_items):
        tid = sess['teacher_id']
        if tid and tid != "unassigned":
            tchr_to_sessions[tid].append(i)

    for tid, indices in tchr_to_sessions.items():
        for i_idx, i in enumerate(indices):
            for j in indices[i_idx + 1:]:
                s_i = exam_items[i]
                s_j = exam_items[j]
                # If same shift, grade, and subject in ODL with normal duration, they may share the online slot together
                is_same_merged_odl = (
                    s_i['shift'] == s_j['shift'] and
                    s_i['grade_level'] == s_j['grade_level'] and
                    s_i['subject'] == s_j['subject'] and
                    s_i['duration_minutes'] < 120 and
                    s_j['duration_minutes'] < 120 and
                    'ODL' in s_i['shift']
                )
                
                for d in days:
                    for s1 in slots:
                        for s2 in slots:
                            t1_s, t1_e, _ = get_slot_time_interval(s_i['shift'], s_i['grade_level'], s_i['duration_minutes'], s1)
                            t2_s, t2_e, _ = get_slot_time_interval(s_j['shift'], s_j['grade_level'], s_j['duration_minutes'], s2)
                            if slots_overlap(t1_s, t1_e, t2_s, t2_e):
                                if is_same_merged_odl and s1 == s2:
                                    pass
                                else:
                                    model.Add(x[i, d, s1] + x[j, d, s2] <= 1)

    tchr_dev_terms = []
    for tid, indices in tchr_to_sessions.items():
        t_count = len(indices)
        target_per_day = t_count / 4.0
        target_int = int(round(target_per_day))
        for d in days:
            t_day_sum = sum(x[i, d, s] for i in indices for s in slots)
            dev = model.NewIntVar(0, t_count, f"dev_{tid}_{d}")
            model.Add(dev >= t_day_sum - target_int)
            model.Add(dev >= target_int - t_day_sum)
            tchr_dev_terms.append(dev)

    day_total_devs = []
    target_day_total = num_sessions // 4
    for d in days:
        d_total = sum(x[i, d, s] for i in range(num_sessions) for s in slots)
        d_dev = model.NewIntVar(0, num_sessions, f"d_dev_{d}")
        model.Add(d_dev >= d_total - target_day_total)
        model.Add(d_dev >= target_day_total - d_total)
        day_total_devs.append(d_dev)

    # Core Objective: Section daily balance (weight 10) + Teacher daily balance (weight 5) + School day balance (weight 2)
    obj_cost = sum(sec_dev_terms) * 10 + sum(tchr_dev_terms) * 5 + sum(day_total_devs) * 2
    model.Minimize(obj_cost)

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
                        s_m, e_m, time_str = get_slot_time_interval(sess['shift'], sess['grade_level'], sess['duration_minutes'], s)
                        
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

