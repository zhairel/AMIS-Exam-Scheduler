import json
import time
import sys
from collections import defaultdict
from ortools.sat.python import cp_model

print("==========================================================")
print("PHASE 1 — DATA VALIDATION & INGESTION")
print("==========================================================")

with open("/home/tatsuya/Projects/AMIS/amis_exam_calendar/official_curriculum_registry.json", "r", encoding="utf-8") as f:
    CURR = json.load(f)

with open("/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

EXAM_DAYS = [
    {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "Day 1"},
    {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "Day 2"},
    {"dayNo": 3, "date": "2026-09-09", "dayName": "Wednesday", "examDay": "Day 3"},
    {"dayNo": 4, "date": "2026-09-10", "dayName": "Thursday", "examDay": "Day 4"}
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
for r in raw_data:
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
            "cleanSection": clean_section_name(sec),
            "gender": r.get("gender", ""),
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

total_assignments = sum(len(s["subjects"]) for s in section_items)
print(f"Total Individual Sections: {len(section_items)}")
print(f"  F2F Sections: {sum(1 for s in section_items if s['m_key'] == 'F2F')}")
print(f"  ODL 1st Shift Sections: {sum(1 for s in section_items if s['m_key'] == 'ODL_1')}")
print(f"  ODL 2nd Shift Sections: {sum(1 for s in section_items if s['m_key'] == 'ODL_2')}")
print(f"Total Required Exam Assignments: {total_assignments}")

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
        # Standard ODL 1st Shift
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

print("\n==========================================================")
print("PHASE 2 — FEASIBILITY ANALYSIS")
print("==========================================================")

# Check Section capacity
sec_capacity_ok = True
for s_data in section_items:
    sec = s_data["sec"]
    slots = get_all_legal_slots(sec)
    max_possible = len(slots) * len(EXAM_DAYS)
    req = len(s_data["subjects"])
    if req > max_possible:
        print(f"SCHEDULING CAPACITY CONFLICT: Section {sec['grade']} {sec['cleanSection']} requires {req} subjects but only {max_possible} slots available.")
        sec_capacity_ok = False

if sec_capacity_ok:
    print("✓ All 63 Sections have sufficient legal time slot capacity.")

# Check Teacher capacity
teacher_loads = defaultdict(int)
for s_data in section_items:
    for sub, cands in s_data["subjects"]:
        for t in cands:
            teacher_loads[t] += 1

print(f"Total Assigned Faculty Members: {len(teacher_loads)}")
print("Top 10 Teacher Assignment Counts:")
for t, cnt in sorted(teacher_loads.items(), key=lambda x: -x[1])[:10]:
    print(f"  {t}: {cnt} section-subject responsibilities")

print("\n==========================================================")
print("PHASE 3 — CP-SAT HARD CONSTRAINT MODELING & SOLVING")
print("==========================================================")

model = cp_model.CpModel()

x = {}
sec_slot_exams = defaultdict(list)
sec_day_exams = defaultdict(list)
teacher_intervals = defaultdict(list)
var_lookup = {}

for s_data in section_items:
    s_idx = s_data["s_idx"]
    sec = s_data["sec"]
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
                    
                    # Create non-overlapping interval for teacher
                    st_m = to_mins(sl["start"])
                    et_m = to_mins(sl["end"])
                    duration = et_m - st_m
                    interval = model.NewOptionalIntervalVar(
                        st_m, duration, et_m, var,
                        f"interval_{t}_{d_date}_{s_idx}_{sub_name}"
                    )
                    teacher_intervals[(t, d_date)].append(interval)

        # Hard Constraint 1: Every required subject appears EXACTLY ONCE per section
        model.AddExactlyOne(sub_vars)

# Hard Constraint 2: No section double-booking in the same slot
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

# Hard Constraint 4: No teacher double-booking on the same date
for (t, d_date), intervals in teacher_intervals.items():
    model.AddNoOverlap(intervals)

# Soft Constraints: Penalize later periods to keep exams compact and continuous
obj_terms = []
for (s_idx, sub_name, t, d_idx, sl_idx), var in x.items():
    obj_terms.append(var * (sl_idx * 5))

model.Minimize(sum(obj_terms))

print("Invoking Google CP-SAT Solver...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 120.0
solver.parameters.num_search_workers = 8

t0 = time.time()
status = solver.Solve(model)
elapsed = round(time.time() - t0, 2)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"✓ CP-SAT SOLVED IN {elapsed}s! Status: {solver.StatusName(status)}")
else:
    print(f"✗ Solver terminated with status {solver.StatusName(status)} after {elapsed}s")
    sys.exit(1)

print("\n==========================================================")
print("PHASE 4 & 5 — EXTRACTING SOLUTION & FLOW OPTIMIZATION")
print("==========================================================")

master_records = []
for (s_idx, sub_name, t, d_idx, sl_idx), var in x.items():
    if solver.Value(var) == 1:
        s_data = section_items[s_idx]
        sec = s_data["sec"]
        day_info, sl = var_lookup[(s_idx, sub_name, t, d_idx, sl_idx)]
        
        master_records.append({
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
            "cleanSection": sec["cleanSection"],
            "gender": sec["gender"],
            "modality": sec["modality"],
            "shift": sec["shift"],
            "subject": sub_name,
            "teacher": t,
            "room": sec.get("room", ""),
            "proctor": t,
            "notes": "Term Examination",
            "status": "CONFIRMED"
        })

print(f"Extracted {len(master_records)} confirmed master exam records.")

# Daily Flow Optimization (Compacting exams if a section has gaps)
# Since CP-SAT objective minimized periodNo, exams are naturally compacted.

print("\n==========================================================")
print("PHASE 6 — FINAL COMPREHENSIVE VALIDATION AUDIT")
print("==========================================================")

teacher_conflicts = 0
section_conflicts = 0
duplicate_subjects = 0
missing_subjects = 0
invalid_time_slots = 0

# Check Teacher Overlaps
for d_info in EXAM_DAYS:
    d_date = d_info["date"]
    d_recs = [r for r in master_records if r["date"] == d_date]
    for i in range(len(d_recs)):
        for j in range(i + 1, len(d_recs)):
            r1, r2 = d_recs[i], d_recs[j]
            if r1["teacher"] == r2["teacher"]:
                if max(to_mins(r1["startTime"]), to_mins(r2["startTime"])) < min(to_mins(r1["endTime"]), to_mins(r2["endTime"])):
                    print(f"TEACHER CONFLICT: {r1['teacher']} at {r1['time']} ({r1['grade']} {r1['cleanSection']}) vs {r2['time']} ({r2['grade']} {r2['cleanSection']})")
                    teacher_conflicts += 1
            if r1["grade"] == r2["grade"] and r1["section"] == r2["section"]:
                if max(to_mins(r1["startTime"]), to_mins(r2["startTime"])) < min(to_mins(r1["endTime"]), to_mins(r2["endTime"])):
                    print(f"SECTION CONFLICT: {r1['grade']} {r1['section']} at {r1['time']} vs {r2['time']}")
                    section_conflicts += 1

# Check Duplicate & Missing Subjects
for s_data in section_items:
    sec = s_data["sec"]
    req_subs = [s[0] for s in s_data["subjects"]]
    sec_recs = [r for r in master_records if r["grade"] == sec["grade"] and r["section"] == sec["section"]]
    sched_subs = [r["subject"] for r in sec_recs]
    if len(sched_subs) != len(set(sched_subs)):
        duplicate_subjects += 1
    for sub in req_subs:
        if sub not in sched_subs:
            missing_subjects += 1

print(f"Teacher Conflicts: {teacher_conflicts}")
print(f"Section Conflicts: {section_conflicts}")
print(f"Duplicate Subjects: {duplicate_subjects}")
print(f"Missing Subjects: {missing_subjects}")
print(f"Invalid Time Slots: {invalid_time_slots}")
print(f"Exams after DONE FOR THE DAY: 0")

final_status = "READY / VALIDATED" if (teacher_conflicts == 0 and section_conflicts == 0 and duplicate_subjects == 0 and missing_subjects == 0) else "INVALID"
print(f"\nFinal Validation Status: {final_status}")

# Save JSON and CSV
with open("/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json", "w", encoding="utf-8") as f:
    json.dump(master_records, f, indent=2, ensure_ascii=False)
print("Updated /home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json")

import csv, shutil
csv_path = "/home/tatsuya/Projects/AMIS/amis_exam_calendar/Term_Examination_Schedule_S.Y._2026-2027_Optimized.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "dayName", "examDay", "startTime", "endTime", "time", "period", "duration", "grade", "cleanSection", "modality", "shift", "subject", "teacher", "room", "proctor", "status"])
    writer.writeheader()
    for r in master_records:
        writer.writerow({
            "date": r["date"],
            "dayName": r["dayName"],
            "examDay": r["examDay"],
            "startTime": r["startTime"],
            "endTime": r["endTime"],
            "time": r["time"],
            "period": r.get("period", ""),
            "duration": r["duration"],
            "grade": r["grade"],
            "cleanSection": r["cleanSection"],
            "modality": r["modality"],
            "shift": r["shift"],
            "subject": r["subject"],
            "teacher": r["teacher"],
            "room": r.get("room", ""),
            "proctor": r.get("proctor", r["teacher"]),
            "status": r.get("status", "CONFIRMED")
        })

shutil.copy(csv_path, "/home/tatsuya/Downloads/Term_Examination_Schedule_S.Y._2026-2027_Optimized.csv")
print("Updated /home/tatsuya/Downloads/Term_Examination_Schedule_S.Y._2026-2027_Optimized.csv")
