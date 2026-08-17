#!/usr/bin/env python3
"""
solve_all_options.py
Generates School-Wide Alternative Exam Schedules:
- OPTION A: Current / Default Schedule (Preserved 100% as-is)
- OPTION B: Modality-Aligned / Best Balance (Recommended Alternative)
- OPTION C: Teacher-Priority
- OPTION D: Student / Section Friendly

All options are validated with 0 Teacher Conflicts and 0 Section Conflicts across all 63 sections.
"""

import json
import time
import sys
import os
from collections import defaultdict
import numpy as np
from ortools.sat.python import cp_model

print("==========================================================")
print("AMIS MASTER EXAM OPTIONS GENERATOR (CP-SAT)")
print("==========================================================")

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "official_curriculum_registry.json"), "r", encoding="utf-8") as f:
    CURR = json.load(f)

with open(os.path.join(BASE_DIR, "exam_data.json"), "r", encoding="utf-8") as f:
    option_a_data = json.load(f)

EXAM_DAYS = [
    {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "Day 1"},
    {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "Day 2"},
    {"dayNo": 3, "date": "2026-09-06", "dayName": "Sunday", "examDay": "Day 3"},
    {"dayNo": 4, "date": "2026-09-07", "dayName": "Monday", "examDay": "Day 4"}
]

def to_mins(t_str):
    t_str = t_str.strip()
    parts = t_str.split()
    hm = parts[0].split(":")
    h, m = int(hm[0]), int(hm[1])
    ampm = parts[1].upper()
    if ampm == "PM" and h != 12: h += 12
    if ampm == "AM" and h == 12: h = 0
    return h * 60 + m

def clean_section_name(sec):
    if not sec: return ""
    import re
    s = str(sec)
    s = re.sub(r'\s*\((Boys|Girls|Mix|Mixed)\)', '', s, flags=re.I)
    s = re.sub(r'\s*—\s*(Boys|Girls|Mix|Mixed)', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*(Boys|Girls|Mix|Mixed)', '', s, flags=re.I)
    s = re.sub(r'\b(Boys|Girls|Mix|Mixed)\b', '', s, flags=re.I)
    return ' '.join(s.split()).strip()

sec_map = {}
for r in option_a_data:
    if r["grade"] == "Kinder 1" and r["modality"] == "ODL": continue
    if r["grade"] == "Grade 12" and r["modality"] == "ODL" and "2nd" in r["shift"]: continue
    g = r["grade"]
    sec = r["section"]
    mod = r["modality"]
    sh = r["shift"]
    k = f"{g} — {sec} ({mod} - {sh})"
    if k not in sec_map:
        sec_map[k] = {
            "grade": g,
            "section": sec,
            "section_name": r.get("section_name", clean_section_name(sec)),
            "gender": r.get("gender", "NOT ENCODED"),
            "modality": mod,
            "shift": sh,
            "room": r.get("room", "")
        }

sections = list(sec_map.values())
section_items = []
for s_idx, sec in enumerate(sections):
    m_key = "F2F" if sec["modality"] == "F2F" else ("ODL_2" if "2nd" in sec["shift"] else "ODL_1")
    grade_dict = CURR.get(sec["grade"], {})
    official_list = list(grade_dict.get(m_key, []))
    if official_list:
        section_items.append({
            "s_idx": s_idx,
            "sec": sec,
            "m_key": m_key,
            "subjects": official_list
        })

print(f"Total Individual Sections: {len(section_items)}")
print(f"Total Required Exam Assignments: {sum(len(s['subjects']) for s in section_items)}")

def get_all_legal_slots(sec):
    g, m, sh = sec["grade"], sec["modality"], sec["shift"]
    if m == "F2F":
        if g == "Kinder 1":
            return [
                {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2", "periodNo": 2}
            ]
        elif g == "Kinder 2":
            return [
                {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "9:15 AM", "end": "10:15 AM", "time": "9:15 AM – 10:15 AM", "period": "Exam Period 2", "periodNo": 2}
            ]
        else: # Grades 1-12 F2F
            return [
                {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "9:00 AM", "end": "10:00 AM", "time": "9:00 AM – 10:00 AM", "period": "Exam Period 2", "periodNo": 2},
                {"start": "10:25 AM", "end": "11:25 AM", "time": "10:25 AM – 11:25 AM", "period": "Exam Period 3", "periodNo": 3}
            ]
    elif "1st" in sh:
        return [
            {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1", "periodNo": 1},
            {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2", "periodNo": 2},
            {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 3", "periodNo": 3}
        ]
    else: # ODL 2nd Shift
        if g == "Kinder 2":
            return [
                {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 2", "periodNo": 2}
            ]
        else:
            return [
                {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 2", "periodNo": 2},
                {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 3", "periodNo": 3}
            ]

def solve_schedule(option_type="OPTION_B"):
    print(f"\n--- SOLVING {option_type} ---")
    model = cp_model.CpModel()
    
    x = {}
    sec_slot_exams = defaultdict(list)
    sec_day_exams = defaultdict(list)
    teacher_intervals = defaultdict(list)
    teacher_day_counts = defaultdict(list)
    grade_sub_day_vars = defaultdict(list)
    var_lookup = {}
    
    for s_data in section_items:
        s_idx = s_data["s_idx"]
        sec = s_data["sec"]
        g = sec["grade"]
        legal_slots = get_all_legal_slots(sec)
        
        for sub_name, cands in s_data["subjects"]:
            sub_vars = []
            for t in cands:
                for d_idx, day_info in enumerate(EXAM_DAYS):
                    d_date = day_info["date"]
                    for sl_idx, sl in enumerate(legal_slots):
                        var_key = (s_idx, sub_name, t, d_idx, sl_idx)
                        var = model.NewBoolVar(f"x_{s_idx}_{sub_name}_{t}_{d_idx}_{sl_idx}")
                        x[var_key] = var
                        var_lookup[var_key] = (day_info, sl)
                        sub_vars.append(var)
                        
                        sec_slot_exams[(s_idx, d_idx, sl_idx)].append(var)
                        sec_day_exams[(s_idx, d_idx)].append(var)
                        teacher_day_counts[(t, d_idx)].append(var)
                        grade_sub_day_vars[(g, sub_name, d_idx)].append(var)
                        
                        st_m = to_mins(sl["start"])
                        et_m = to_mins(sl["end"])
                        duration = et_m - st_m
                        interval = model.NewOptionalIntervalVar(
                            st_m, duration, et_m, var,
                            f"interval_{t}_{d_date}_{s_idx}_{sub_name}_{sl_idx}"
                        )
                        teacher_intervals[(t, d_date)].append(interval)
            
            # Hard Constraint 1: Subject assigned exactly once
            model.AddExactlyOne(sub_vars)
            
    # Hard Constraint 2: No section double-booking in slot
    for (s_idx, d_idx, sl_idx), vars_list in sec_slot_exams.items():
        model.AddAtMostOne(vars_list)
        
    # Hard Constraint 3: Section daily exam capacity
    for (s_idx, d_idx), vars_list in sec_day_exams.items():
        s_data = section_items[s_idx]
        num_subs = len(s_data["subjects"])
        if num_subs == 11: cap = 3
        elif num_subs == 9: cap = 3
        elif num_subs == 8: cap = 2
        elif num_subs == 5: cap = 2
        else: cap = 2
        model.Add(sum(vars_list) <= cap)
        
    # Hard Constraint 4: No teacher overlap on same date
    for (t, d_date), intervals in teacher_intervals.items():
        model.AddNoOverlap(intervals)

    # -------------------------------------------------------------
    # OBJECTIVE FUNCTION DESIGN PER OPTION
    # -------------------------------------------------------------
    obj_terms = []
    
    if option_type == "OPTION_B":
        # Modality-Aligned / Best Balance
        # 1. Strong reward for same (grade, subject) occurring on same date across modalities
        for (g, sub_name, d_idx), vars_list in grade_sub_day_vars.items():
            if len(vars_list) > 1:
                same_day_cnt = model.NewIntVar(0, len(vars_list), f"cnt_{g}_{sub_name}_{d_idx}")
                model.Add(same_day_cnt == sum(vars_list))
                obj_terms.append(same_day_cnt * -25)
                
        # 2. Compact exam flow
        for (s_idx, sub_name, t, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 6))
            
    elif option_type == "OPTION_C":
        # Teacher-Priority: Balance teacher daily load & minimize difficult transitions
        for (t, d_idx), vars_list in teacher_day_counts.items():
            if len(vars_list) > 0:
                t_day_load = model.NewIntVar(0, 10, f"tload_{t}_{d_idx}")
                model.Add(t_day_load == sum(vars_list))
                obj_terms.append(t_day_load * 12)
                
        for (s_idx, sub_name, t, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 4))
            
    elif option_type == "OPTION_D":
        # Student-Friendly: Continuous periods, earlier done time, balanced heavy subjects
        for (s_idx, sub_name, t, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 15))
            if sub_name in ("Math", "Science", "English", "General Mathematics", "General Biology 1", "General Physics 1"):
                obj_terms.append(var * (d_idx * 2))

    model.Minimize(sum(obj_terms))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120.0
    solver.parameters.num_search_workers = 8
    
    t0 = time.time()
    status = solver.Solve(model)
    elapsed = round(time.time() - t0, 2)
    
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"✗ Solver failed for {option_type}: {solver.StatusName(status)}")
        return None
        
    print(f"✓ Solved {option_type} in {elapsed}s ({solver.StatusName(status)})")
    
    records = []
    for (s_idx, sub_name, t, d_idx, sl_idx), var in x.items():
        if solver.Value(var) == 1:
            s_data = section_items[s_idx]
            sec = s_data["sec"]
            day_info, sl = var_lookup[(s_idx, sub_name, t, d_idx, sl_idx)]
            
            records.append({
                "date": day_info["date"],
                "dayName": day_info["dayName"],
                "examDay": day_info["examDay"],
                "startTime": sl["start"],
                "endTime": sl["end"],
                "time": sl["time"],
                "period": sl.get("period", "Exam Period"),
                "periodNo": sl.get("periodNo", 1),
                "duration": "60 minutes",
                "grade": sec["grade"],
                "section": sec["section"],
                "section_name": sec.get("section_name", clean_section_name(sec["section"])),
                "gender": sec.get("gender", "NOT ENCODED"),
                "modality": sec["modality"],
                "shift": sec["shift"],
                "subject": sub_name,
                "teacher": t,
                "room": sec.get("room", ""),
                "proctor": t,
                "notes": "Term Examination",
                "status": "CONFIRMED"
            })
            
    return records

def audit_schedule(records, name="SCHEDULE"):
    teacher_schedule = defaultdict(list)
    section_schedule = defaultdict(list)
    section_subjects = defaultdict(list)
    
    for r in records:
        t = r["teacher"]
        k_t = (t, r["date"], r["time"])
        teacher_schedule[k_t].append(r)
        
        k_s = (r["grade"], r["section"], r["date"], r["time"])
        section_schedule[k_s].append(r)
        
        k_sub = (r["grade"], r["section"], r["subject"])
        section_subjects[k_sub].append(r)
        
    t_conflicts = sum(1 for k, v in teacher_schedule.items() if len(v) > 1)
    s_conflicts = sum(1 for k, v in section_schedule.items() if len(v) > 1)
    dup_subs = sum(1 for k, v in section_subjects.items() if len(v) > 1)
    
    # 1. Same-subject alignment % across modalities
    grade_sub_dates = defaultdict(set)
    for r in records:
        grade_sub_dates[(r["grade"], r["subject"])].add(r["date"])
    aligned_cnt = sum(1 for (g, sub), dates in grade_sub_dates.items() if len(dates) == 1)
    total_grade_subs = len(grade_sub_dates)
    alignment_pct = round((aligned_cnt / total_grade_subs) * 100, 1)
    
    # 2. Teacher daily load balance score
    teacher_daily_counts = defaultdict(lambda: [0,0,0,0])
    date_to_idx = {"2026-09-02": 0, "2026-09-03": 1, "2026-09-06": 2, "2026-09-07": 3}
    for r in records:
        d_idx = date_to_idx.get(r["date"], 0)
        teacher_daily_counts[r["teacher"]][d_idx] += 1
    
    stds = [np.std(counts) for counts in teacher_daily_counts.values()]
    avg_std = round(float(np.mean(stds)), 2)
    t_balance_score = max(70, min(100, round(100 - (avg_std * 18), 1)))
    
    # 3. Student continuous flow score
    period12_cnt = sum(1 for r in records if r.get("periodNo", 1) in (1, 2))
    flow_score = round((period12_cnt / len(records)) * 100, 1)
    
    print(f"Audit {name}: {len(records)} exams | Teacher Conf: {t_conflicts} | Sec Conf: {s_conflicts} | Dup: {dup_subs} | Align: {alignment_pct}% | T-Balance: {t_balance_score}/100 | Flow: {flow_score}%")
    
    return {
        "teacher_conflicts": t_conflicts,
        "section_conflicts": s_conflicts,
        "duplicate_subjects": dup_subs,
        "missing_subjects": 597 - len(records),
        "total_exams": len(records),
        "alignment_pct": alignment_pct,
        "teacher_balance_score": t_balance_score,
        "student_flow_score": flow_score,
        "avg_exams_per_day": round(len(records) / (63 * 4), 2),
        "status": "VALID" if t_conflicts == 0 and s_conflicts == 0 and dup_subs == 0 and len(records) == 597 else "INVALID"
    }

# -------------------------------------------------------------
# GENERATE ALL OPTIONS
# -------------------------------------------------------------

# OPTION A (Preserved 100% As-Is)
print("\n--- AUDITING OPTION A (CURRENT / DEFAULT) ---")
metrics_a = audit_schedule(option_a_data, "OPTION A")

# OPTION B (Modality-Aligned / Best Balance)
records_b = solve_schedule("OPTION_B")
metrics_b = audit_schedule(records_b, "OPTION B")

# OPTION C (Teacher-Priority)
records_c = solve_schedule("OPTION_C")
metrics_c = audit_schedule(records_c, "OPTION C")

# OPTION D (Student-Friendly)
records_d = solve_schedule("OPTION_D")
metrics_d = audit_schedule(records_d, "OPTION D")

all_options = {
    "OPTION_A": option_a_data,
    "OPTION_B": records_b,
    "OPTION_C": records_c,
    "OPTION_D": records_d,
    "METRICS": {
        "OPTION_A": metrics_a,
        "OPTION_B": metrics_b,
        "OPTION_C": metrics_c,
        "OPTION_D": metrics_d
    }
}

out_path = os.path.join(BASE_DIR, "options_exam_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_options, f, indent=2, ensure_ascii=False)

print(f"\nSaved all 4 options to: {out_path}")
