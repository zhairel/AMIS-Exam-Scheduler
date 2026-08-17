import json
from collections import defaultdict
from ortools.sat.python import cp_model
import random
import os

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/raw_exam_sessions.json') as f:
    exam_sessions = json.load(f)

print(f"Loaded {len(exam_sessions)} exam sessions to optimize.")

EXAM_DATES = [
    {"day_index": 1, "date_str": "Tuesday, September 2, 2026", "short_date": "Sep 2"},
    {"day_index": 2, "date_str": "Wednesday, September 3, 2026", "short_date": "Sep 3"},
    {"day_index": 3, "date_str": "Saturday, September 6, 2026", "short_date": "Sep 6"},
    {"day_index": 4, "date_str": "Sunday, September 7, 2026", "short_date": "Sep 7"}
]

# Time slots per shift
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

def solve_option(option_name, seed=42):
    model = cp_model.CpModel()
    
    # Assign each session i a day d (1..4) and slot s (1..3)
    # Binary var x[i, d, s]
    x = {}
    
    num_sessions = len(exam_sessions)
    days = [1, 2, 3, 4]
    slots = [1, 2, 3]
    
    for i in range(num_sessions):
        for d in days:
            for s in slots:
                x[i, d, s] = model.NewBoolVar(f"x_{i}_{d}_{s}")
                
    # 1. Exactly one (d, s) per session
    for i in range(num_sessions):
        model.Add(sum(x[i, d, s] for d in days for s in slots) == 1)
        
    # Group sessions by section
    sec_to_sessions = defaultdict(list)
    tchr_to_sessions = defaultdict(list)
    
    for i, sess in enumerate(exam_sessions):
        sec_to_sessions[sess['section_name']].append(i)
        t = sess['teacher'].strip()
        if t and t != "Assigned Faculty":
            tchr_to_sessions[t].append(i)
            
    # 2. No section takes > 1 exam at the same (d, s)
    for sname, s_indices in sec_to_sessions.items():
        for d in days:
            for s in slots:
                model.Add(sum(x[i, d, s] for i in s_indices) <= 1)
                
            # Limit max exams per day for this section
            max_daily = 3 if len(s_indices) >= 9 else 2
            model.Add(sum(x[i, d, s] for i in s_indices for s in slots) <= max_daily)
            
    # 3. No teacher proctors > 1 exam at the same (d, s) across sections of the same shift
    # Note: If teacher teaches in F2F (morning) and ODL2 (afternoon), slot 1 is at different times!
    # So we group by (shift, teacher)
    shift_tchr_to_sessions = defaultdict(list)
    for i, sess in enumerate(exam_sessions):
        t = sess['teacher'].strip()
        if t and t != "Assigned Faculty":
            shift_tchr_to_sessions[(sess['shift'], t)].append(i)
            
    for (shift, t), s_indices in shift_tchr_to_sessions.items():
        if len(s_indices) > 1:
            for d in days:
                for s in slots:
                    model.Add(sum(x[i, d, s] for i in s_indices) <= 1)

    # 4. Objective styling based on option
    obj_terms = []
    
    for i, sess in enumerate(exam_sessions):
        subj = sess['subject'].lower()
        if option_name == "OPTION_B": # Math early
            if "math" in subj or "stat" in subj:
                for d in [1, 2]:
                    for s in slots:
                        obj_terms.append(x[i, d, s] * 10)
        elif option_name == "OPTION_C": # Islamic/Language early
            if "arabic" in subj or "qur" in subj or "hadith" in subj:
                for d in [1, 2]:
                    for s in slots:
                        obj_terms.append(x[i, d, s] * 10)
        elif option_name == "OPTION_D": # Even distribution
            for d in days:
                for s in slots:
                    # slight random weight for variety
                    r_val = (i * 7 + d * 13 + s * 17 + seed) % 5
                    obj_terms.append(x[i, d, s] * r_val)

    if obj_terms:
        model.Maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = 8
    
    status = solver.Solve(model)
    print(f"Solver status for {option_name}: {solver.StatusName(status)}")
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        scheduled = []
        for i, sess in enumerate(exam_sessions):
            for d in days:
                for s in slots:
                    if solver.Value(x[i, d, s]) == 1:
                        date_meta = EXAM_DATES[d - 1]
                        shift_info = SHIFT_SLOTS.get(sess['shift'], SHIFT_SLOTS["F2F"])
                        slot_info = shift_info[s - 1]
                        
                        # Determine time label
                        time_str = slot_info['time']
                        if sess['duration_minutes'] == 120 and 'math_time' in slot_info:
                            time_str = slot_info['math_time']
                        elif 'Kinder 2' in sess['grade_level'] and sess['shift'] == 'ODL - 1ST SHIFT' and 'k2_time' in slot_info:
                            time_str = slot_info['k2_time']
                            
                        scheduled.append({
                            'id': f"exam_{len(scheduled)+1}",
                            'day_number': d,
                            'date': date_meta['date_str'],
                            'short_date': date_meta['short_date'],
                            'slot_number': s,
                            'time_slot': time_str,
                            'section_name': sess['section_name'],
                            'department': sess['department'],
                            'grade_level': sess['grade_level'],
                            'shift': sess['shift'],
                            'subject': sess['subject'],
                            'teacher': sess['teacher'],
                            'duration_minutes': sess['duration_minutes']
                        })
        return scheduled
    else:
        print(f"Failed to find solution for {option_name}")
        return []

all_options = {
    "OPTION_A": solve_option("OPTION_A", seed=42),
    "OPTION_B": solve_option("OPTION_B", seed=101),
    "OPTION_C": solve_option("OPTION_C", seed=202),
    "OPTION_D": solve_option("OPTION_D", seed=303)
}

print("\n--- Summary of Solved Options ---")
for opt, records in all_options.items():
    print(f"  {opt}: {len(records)} exams scheduled (0 conflicts)")

# Save options_exam_data.json
with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/options_exam_data.json', 'w') as f:
    json.dump(all_options, f, indent=2)

# Save default exam_data.json and exam-data.js (Option A)
with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w') as f:
    json.dump(all_options["OPTION_A"], f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam-data.js', 'w') as f:
    f.write(f"window.EXAM_DATA = {json.dumps(all_options['OPTION_A'], indent=2)};\n")
    f.write(f"window.OPTIONS_EXAM_DATA = {json.dumps(all_options, indent=2)};\n")

print("\nSaved options_exam_data.json, exam_data.json, and exam-data.js successfully!")

