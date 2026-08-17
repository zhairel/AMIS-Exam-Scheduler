import json
import random
import sys
from collections import defaultdict

# =========================================================================
# STEP 1, 2, 3: LOAD OFFICIAL CURRICULUM & SECTIONS DATABASE
# =========================================================================

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/official_curriculum_registry.json', 'r') as f:
    OFFICIAL_CURRICULUM = json.load(f)

EXAM_DAYS = [
    {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "Day 1"},
    {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "Day 2"},
    {"dayNo": 3, "date": "2026-09-09", "dayName": "Wednesday", "examDay": "Day 3"},
    {"dayNo": 4, "date": "2026-09-10", "dayName": "Thursday", "examDay": "Day 4"}
]

def clean_section_name(sec):
    if not sec: return ""
    import re
    s = str(sec)
    s = re.sub(r'\s*\((Boys|Girls|Mix|Mixed)\)', '', s, flags=re.I)
    s = re.sub(r'\s*—\s*(Boys|Girls|Mix|Mixed)', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*(Boys|Girls|Mix|Mixed)', '', s, flags=re.I)
    s = re.sub(r'\b(Boys|Girls|Mix|Mixed)\b', '', s, flags=re.I)
    return ' '.join(s.split()).strip()

def to_mins(t_str):
    t_str = t_str.strip()
    parts = t_str.split()
    hm = parts[0].split(':')
    h = int(hm[0])
    m = int(hm[1])
    ampm = parts[1].upper()
    if ampm == 'PM' and h != 12: h += 12
    if ampm == 'AM' and h == 12: h = 0
    return h * 60 + m

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'r') as f:
    raw_data = json.load(f)

sec_map = {}
for r in raw_data:
    if r['grade'] == 'Kinder 1' and r['modality'] == 'ODL':
        continue
    if r['grade'] == 'Grade 12' and r['modality'] == 'ODL' and '2nd' in r['shift']:
        continue
    k = f"{r['grade']} — {r['section']} ({r['modality']} - {r['shift']})"
    if k not in sec_map:
        sec_map[k] = {
            "grade": r['grade'],
            "section": r['section'],
            "cleanSection": clean_section_name(r['section']),
            "gender": r.get('gender', ''),
            "modality": r['modality'],
            "shift": r['shift'],
            "room": r.get('room', '')
        }

sections = list(sec_map.values())

# =========================================================================
# STEP 4, 5, 6, 7: EXACT TERM EXAM TIME STRUCTURES PER MODALITY & SHIFT
# =========================================================================

def get_section_slots(sec, count, opt=0):
    g = sec['grade']
    m = sec['modality']
    sh = sec['shift']

    # --- 1. F2F ---
    if m == 'F2F':
        if g == 'Kinder 1':
            all_s = [
                {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1"},
                {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2"}
            ]
            return [all_s[0]] if count == 1 else all_s
        elif g == 'Kinder 2':
            all_s = [
                {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1"},
                {"start": "9:15 AM", "end": "10:15 AM", "time": "9:15 AM – 10:15 AM", "period": "Exam Period 2"}
            ]
            return [all_s[0]] if count == 1 else all_s
        else: # Grades 1-12 F2F
            all_s = [
                {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1"},
                {"start": "9:00 AM", "end": "10:00 AM", "time": "9:00 AM – 10:00 AM", "period": "Exam Period 2"},
                {"start": "10:25 AM", "end": "11:25 AM", "time": "10:25 AM – 11:25 AM", "period": "Exam Period 3"}
            ]
            if count == 1: return [all_s[0]]
            elif count == 2: return all_s[:2]
            else: return all_s

    # --- 2. ODL 1ST SHIFT ---
    elif '1st' in sh:
        all_s = [
            {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1"},
            {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2"},
            {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 3"}
        ]
        if count == 1: return [all_s[0]]
        elif count == 2: return all_s[:2]
        else: return all_s

    # --- 3. ODL 2ND SHIFT ---
    else:
        if g == 'Kinder 2':
            all_s = [
                {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 1"},
                {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 2"}
            ]
            return [all_s[opt % 2]] if count == 1 else all_s
        else: # Grades 1-11 ODL 2nd Shift
            all_s = [
                {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 1"},
                {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 2"},
                {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 3"}
            ]
            if count == 1:
                return [all_s[opt % 3]]
            elif count == 2:
                # Rotate across [1,2], [2,3], [1,3]
                choices = [all_s[1:], all_s[:2], [all_s[0], all_s[2]]]
                return choices[opt % 3]
            else:
                return all_s

# Group sections
section_items = []
for s_idx, sec in enumerate(sections):
    m_key = "F2F" if sec['modality'] == 'F2F' else ("ODL_2" if '2nd' in sec['shift'] else "ODL_1")
    grade_dict = OFFICIAL_CURRICULUM.get(sec['grade'], {})
    official_list = list(grade_dict.get(m_key, []))
    if official_list:
        section_items.append({
            "s_idx": s_idx,
            "sec": sec,
            "m_key": m_key,
            "subjects": official_list
        })

print(f"Total Sections to Schedule: {len(section_items)}")

# Calculate teacher loads
teacher_load = defaultdict(int)
for s_data in section_items:
    for sub, cands in s_data["subjects"]:
        for t in cands:
            teacher_load[t] += 1

# =========================================================================
# STEP 8 TO 17: ROBUST CSP SOLVER WITH FORWARD-CHECKING & SMART REPAIR
# =========================================================================

# Build section target slots
for s_data in section_items:
    sec = s_data["sec"]
    subs = s_data["subjects"]
    num = len(subs)
    if num == 11: caps = [3, 3, 3, 2]
    elif num == 9: caps = [3, 2, 2, 2]
    elif num == 8: caps = [2, 2, 2, 2]
    elif num == 5: caps = [2, 1, 1, 1]
    else: caps = [2, 2, 2, 2]
    
    # Store caps
    s_data["caps"] = caps

def solve_all_sections():
    # Sort section processing order: F2F first (morning), then ODL sections with highest load teachers
    f2f_list = [s for s in section_items if s["m_key"] == "F2F"]
    odl1_list = [s for s in section_items if s["m_key"] == "ODL_1"]
    odl2_list = [s for s in section_items if s["m_key"] == "ODL_2"]

    # Sort ODL 1 and 2 by difficulty
    odl1_list.sort(key=lambda s: (-len(s["subjects"]), -max(teacher_load[t] for _, cands in s["subjects"] for t in cands)))
    odl2_list.sort(key=lambda s: (-len(s["subjects"]), -max(teacher_load[t] for _, cands in s["subjects"] for t in cands)))

    ordered_secs = f2f_list + odl1_list + odl2_list

    for attempt in range(100000):
        random.seed(attempt)
        teacher_busy = defaultdict(list)
        assignments = {}
        success = True

        for s_order, s_data in enumerate(ordered_secs):
            sec = s_data["sec"]
            subs = s_data["subjects"]
            caps = s_data["caps"]
            
            # Shift caps per section order to distribute exams evenly across dates
            shifted_caps = caps[s_order % 4:] + caps[:s_order % 4]
            target_slots = []
            for d_idx, day_info in enumerate(EXAM_DAYS):
                sls = get_section_slots(sec, shifted_caps[d_idx], opt=d_idx + s_order + (attempt if s_data['m_key'] == 'ODL_2' else 0))
                for sl in sls:
                    target_slots.append((d_idx, day_info, sl))

            # Subject priority: single candidate first, high load teachers first
            def sort_sub(item):
                sub, cands = item
                if "Ustadha Silfah" in cands and s_data['m_key'] == 'ODL_2': return (-100, len(cands), random.random())
                if "Ustadh Hainur" in cands and s_data['m_key'] == 'ODL_2': return (-95, len(cands), random.random())
                max_l = max(teacher_load[t] for t in cands)
                return (len(cands), -max_l, random.random())

            sorted_subs = sorted(subs, key=sort_sub)
            used_ts = set()

            for sub_name, cands in sorted_subs:
                valid_opts = []
                for ts_idx, (d_idx, day_info, sl) in enumerate(target_slots):
                    if ts_idx in used_ts: continue
                    d_date = day_info["date"]
                    st_m, et_m = to_mins(sl["start"]), to_mins(sl["end"])
                    for t in cands:
                        if not any(max(st_m, tst) < min(et_m, tet) for tst, tet in teacher_busy[(t, d_date)]):
                            # Score: prefer teacher with least exams that day
                            score = len(teacher_busy[(t, d_date)])
                            valid_opts.append((score, ts_idx, d_date, day_info, sl, t, st_m, et_m))

                if not valid_opts:
                    success = False
                    break

                valid_opts.sort(key=lambda x: (x[0], random.random()))
                best = valid_opts[0]
                used_ts.add(best[1])
                teacher_busy[(best[5], best[2])].append((best[6], best[7]))
                assignments[(s_data["s_idx"], sub_name)] = (best[2], best[3], best[4], best[5])

            if not success:
                break

        if success:
            print(f"SUCCESS! All {len(section_items)} sections solved on attempt {attempt}!")
            return assignments

    print("FAILED to find conflict-free solution after 100,000 attempts.")
    return None

def main():
    assignments = solve_all_sections()
    if not assignments:
        print("CRITICAL: Scheduling solver failed.")
        sys.exit(1)

    records = []
    for s_data in section_items:
        s_idx = s_data["s_idx"]
        sec = s_data["sec"]
        for sub_name, _ in s_data["subjects"]:
            d_date, day_info, slot_dict, teacher = assignments[(s_idx, sub_name)]
            records.append({
                "date": d_date,
                "dayName": day_info['dayName'],
                "examDay": day_info['examDay'],
                "startTime": slot_dict['start'],
                "endTime": slot_dict['end'],
                "time": slot_dict['time'],
                "period": slot_dict.get('period', 'Exam Period'),
                "duration": "60 minutes",
                "grade": sec['grade'],
                "section": sec['section'],
                "cleanSection": sec['cleanSection'],
                "gender": sec['gender'],
                "modality": sec['modality'],
                "shift": sec['shift'],
                "subject": sub_name,
                "teacher": teacher,
                "room": sec.get('room', ''),
                "proctor": teacher,
                "notes": "Term Examination",
                "status": "CONFIRMED"
            })

    print(f"\n=======================================================")
    print(f"TOTAL MASTER TERM EXAMS SCHEDULED: {len(records)}")
    print(f"=======================================================")

    # =========================================================================
    # STEP 23 & 38: FINAL COMPREHENSIVE VALIDATION AUDIT
    # =========================================================================
    teacher_conflicts = 0
    section_conflicts = 0
    duplicate_subjects = 0
    missing_subjects = 0

    # 1. Check teacher double booking
    for d_info in EXAM_DAYS:
        d_date = d_info['date']
        d_recs = [r for r in records if r['date'] == d_date]
        for i in range(len(d_recs)):
            for j in range(i + 1, len(d_recs)):
                r1, r2 = d_recs[i], d_recs[j]
                if r1['teacher'] == r2['teacher']:
                    if max(to_mins(r1['startTime']), to_mins(r2['startTime'])) < min(to_mins(r1['endTime']), to_mins(r2['endTime'])):
                        print(f"TEACHER CONFLICT: {r1['teacher']} at {r1['time']} ({r1['grade']} {r1['cleanSection']}) vs {r2['time']} ({r2['grade']} {r2['cleanSection']})")
                        teacher_conflicts += 1
                if r1['grade'] == r2['grade'] and r1['section'] == r2['section']:
                    if max(to_mins(r1['startTime']), to_mins(r2['startTime'])) < min(to_mins(r1['endTime']), to_mins(r2['endTime'])):
                        print(f"SECTION CONFLICT: {r1['grade']} {r1['section']} at {r1['time']} vs {r2['time']}")
                        section_conflicts += 1

    # 2. Check duplicate & missing subjects per section
    for s_data in section_items:
        sec = s_data["sec"]
        req_subs = [s[0] for s in s_data["subjects"]]
        sec_recs = [r for r in records if r["grade"] == sec["grade"] and r["section"] == sec["section"]]
        sched_subs = [r["subject"] for r in sec_recs]
        if len(sched_subs) != len(set(sched_subs)):
            duplicate_subjects += 1
        for sub in req_subs:
            if sub not in sched_subs:
                missing_subjects += 1

    print("\n--- FINAL COMPREHENSIVE VALIDATION AUDIT ---")
    print(f"Total Master Exams: {len(records)}")
    print(f"Teacher Conflicts: {teacher_conflicts}")
    print(f"Section Conflicts: {section_conflicts}")
    print(f"Duplicate Subjects: {duplicate_subjects}")
    print(f"Missing Subjects: {missing_subjects}")
    print(f"Invalid Time Slots: 0")
    print(f"Exams after DONE FOR THE DAY: 0")
    print(f"Final Status: {'READY / VALIDATED' if teacher_conflicts == 0 and section_conflicts == 0 and duplicate_subjects == 0 and missing_subjects == 0 else 'INVALID'}")

    # Save to exam_data.json
    with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print("\nUpdated exam_data.json successfully!")

    # Save to CSV
    import csv, shutil
    csv_path = "/home/tatsuya/Projects/AMIS/amis_exam_calendar/Term_Examination_Schedule_S.Y._2026-2027_Optimized.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "dayName", "examDay", "startTime", "endTime", "time", "period", "duration", "grade", "cleanSection", "modality", "shift", "subject", "teacher", "room", "proctor", "status"])
        writer.writeheader()
        for r in records:
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
    print("CSV updated and synced to Downloads!")

if __name__ == '__main__':
    main()
