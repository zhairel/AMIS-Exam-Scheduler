import json
import random
import sys
from collections import defaultdict

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
            "gender": r.get('gender', ''),
            "modality": r['modality'],
            "shift": r['shift'],
            "room": r.get('room', '')
        }

sections = list(sec_map.values())

# =========================================================================
# EXACT TERM EXAM TIME STRUCTURE (USER SPECIFICATION)
# =========================================================================

def get_f2f_slots(sec, count, opt=0):
    # F2F Term Exam Structure:
    # 7:30–7:45 GA, 7:45–8:00 Prep, 8:00–9:00 Exam 1, 9:00–10:00 Exam 2, 10:00–10:25 Recess, 10:25–11:25 Exam 3, 11:25 Dismissal
    all_3 = [
        {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1"},
        {"start": "9:00 AM", "end": "10:00 AM", "time": "9:00 AM – 10:00 AM", "period": "Exam Period 2"},
        {"start": "10:25 AM", "end": "11:25 AM", "time": "10:25 AM – 11:25 AM", "period": "Exam Period 3"}
    ]
    if count == 1:
        return [all_3[0]]
    elif count == 2:
        return all_3[:2]
    else:
        return all_3

def get_odl1_slots(sec, count, opt=0):
    # ODL 1st Shift Term Exam Structure:
    # 12:30–12:40 GA, 12:40–1:40 Exam 1, 1:40–1:50 Trans, 1:50–2:50 Exam 2, 2:50–3:10 Trans/Salah, 3:10–4:10 Exam 3, 4:10 Dismissal
    all_3 = [
        {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1"},
        {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2"},
        {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 3"}
    ]
    if count == 1:
        return [all_3[0]]
    elif count == 2:
        return all_3[:2]
    else:
        return all_3

def get_odl2_slots(sec, count, opt=0):
    # ODL 2nd Shift Term Exam Structure:
    # 2:50–3:10 Trans/Salah, 3:10–4:10 Exam 1, 4:10–4:20 Trans, 4:20–5:20 Exam 2, 5:20–5:30 Trans, 5:30–6:30 Exam 3, 6:30 Dismissal
    all_3 = [
        {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 1"},
        {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 2"},
        {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 3"}
    ]
    if count == 1:
        return [all_3[opt % 3]]
    elif count == 2:
        choices = [all_3[:2], all_3[1:], [all_3[0], all_3[2]]]
        return choices[opt % 3]
    else:
        return all_3

# Group sections
f2f_secs = []
odl1_secs = []
odl2_secs = []

for s_idx, sec in enumerate(sections):
    m_key = "F2F" if sec['modality'] == 'F2F' else ("ODL_2" if '2nd' in sec['shift'] else "ODL_1")
    grade_dict = OFFICIAL_CURRICULUM.get(sec['grade'], {})
    official_list = list(grade_dict.get(m_key, []))
    if official_list:
        item = {
            "s_idx": s_idx,
            "sec": sec,
            "m_key": m_key,
            "subjects": official_list
        }
        if m_key == 'F2F': f2f_secs.append(item)
        elif m_key == 'ODL_1': odl1_secs.append(item)
        else: odl2_secs.append(item)

print(f"Total Sections to Schedule: F2F={len(f2f_secs)}, ODL1={len(odl1_secs)}, ODL2={len(odl2_secs)}")

def solve_group_coordinated(group_name, group_secs, get_slots_fn, global_teacher_busy):
    print(f"\n--- Solving {group_name} ({len(group_secs)} sections) ---")

    teacher_total_load = defaultdict(int)
    for s in group_secs:
        for sub, cands in s["subjects"]:
            for t in cands:
                teacher_total_load[t] += 1

    grade_buckets = defaultdict(list)
    for s in group_secs:
        grade_buckets[s['sec']['grade']].append(s)

    grade_order = sorted(grade_buckets.keys(), key=lambda g: -len(grade_buckets[g]))
    
    items = []
    for g_name in grade_order:
        for i, s_data in enumerate(grade_buckets[g_name]):
            items.append((s_data, i))

    for attempt in range(50000):
        random.seed(attempt)
        local_teacher_busy = defaultdict(list)
        for k, v in global_teacher_busy.items():
            local_teacher_busy[k] = list(v)

        sec_assignments = {}
        success = True

        for s_data, sec_order in items:
            s_idx = s_data['s_idx']
            sec = s_data['sec']
            subs = list(s_data['subjects'])

            num_subs = len(subs)
            if num_subs == 11: day_caps = [3, 3, 3, 2]
            elif num_subs == 9: day_caps = [3, 2, 2, 2]
            elif num_subs == 8: day_caps = [2, 2, 2, 2]
            elif num_subs == 5: day_caps = [2, 1, 1, 1]
            else: day_caps = [2, 2, 2, 2]

            day_caps_shifted = day_caps[sec_order % 4:] + day_caps[:sec_order % 4]

            target_slots = []
            for d_idx, day_info in enumerate(EXAM_DAYS):
                cap = day_caps_shifted[d_idx]
                day_slots = get_slots_fn(sec, cap, opt=d_idx + sec_order)
                for sl in day_slots:
                    target_slots.append((d_idx, day_info, sl))

            if group_name == 'ODL_1':
                def sort_key(item):
                    sub, cands = item
                    max_l = max(teacher_total_load[t] for t in cands)
                    return (len(cands), -max_l, random.random())
                sorted_subs = sorted(subs, key=sort_key)
            else:
                sorted_subs = sorted(subs, key=lambda x: (len(x[1]), random.random()))
            
            used_target_slots = set()

            placed_all_subs = True

            for sub_name, cands in sorted_subs:
                valid_options = []
                for ts_idx, (d_idx, day_info, sl) in enumerate(target_slots):
                    if ts_idx in used_target_slots:
                        continue
                    
                    d_date = day_info['date']
                    st_m = to_mins(sl['start'])
                    et_m = to_mins(sl['end'])

                    for t in cands:
                        has_overlap = False
                        for (t_st, t_et) in local_teacher_busy[(t, d_date)]:
                            if max(st_m, t_st) < min(et_m, t_et):
                                has_overlap = True
                                break
                        if not has_overlap:
                            score = len(local_teacher_busy[(t, d_date)])
                            valid_options.append((score, ts_idx, d_date, day_info, sl, t, st_m, et_m))

                if not valid_options:
                    placed_all_subs = False
                    break

                valid_options.sort(key=lambda x: (x[0], random.random()))
                _, best_ts_idx, best_date, best_day_info, best_sl, best_t, st_m, et_m = valid_options[0]

                used_target_slots.add(best_ts_idx)
                local_teacher_busy[(best_t, best_date)].append((st_m, et_m))
                sec_assignments[(s_idx, sub_name)] = (best_date, best_day_info, best_sl, best_t)

            if not placed_all_subs:
                success = False
                break

        if success:
            print(f"SUCCESS solving {group_name} on attempt {attempt}!")
            for k, v in local_teacher_busy.items():
                global_teacher_busy[k] = list(v)
            return sec_assignments

    print(f"FAILED to solve {group_name}")
    return None

def main():
    global_teacher_busy = defaultdict(list)
    all_assignments = {}

    f2f_res = solve_group_coordinated("F2F", f2f_secs, get_f2f_slots, global_teacher_busy)
    if not f2f_res: return
    all_assignments.update(f2f_res)

    odl1_res = solve_group_coordinated("ODL_1", odl1_secs, get_odl1_slots, global_teacher_busy)
    if not odl1_res: return
    all_assignments.update(odl1_res)

    odl2_res = solve_group_coordinated("ODL_2", odl2_secs, get_odl2_slots, global_teacher_busy)
    if not odl2_res: return
    all_assignments.update(odl2_res)

    print(f"\n==========================================")
    print("ALL 3 SHIFTS (F2F, ODL 1, ODL 2) 100% CONFLICT-FREE SCHEDULED!")

    records = []
    for s_data in (f2f_secs + odl1_secs + odl2_secs):
        s_idx = s_data['s_idx']
        sec = s_data['sec']
        for sub_name, _ in s_data['subjects']:
            d_date, day_info, slot_dict, teacher = all_assignments[(s_idx, sub_name)]
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
                "cleanSection": clean_section_name(sec['section']),
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

    print(f"Total Master Exams Generated: {len(records)}")

    # Audit Validation
    print("\n--- FINAL MASTER VALIDATION ---")
    teacher_conflicts = 0
    section_conflicts = 0

    for d_info in EXAM_DAYS:
        d_date = d_info['date']
        d_recs = [r for r in records if r['date'] == d_date]
        for i in range(len(d_recs)):
            for j in range(i + 1, len(d_recs)):
                r1, r2 = d_recs[i], d_recs[j]
                if r1['teacher'] == r2['teacher']:
                    if max(to_mins(r1['startTime']), to_mins(r2['startTime'])) < min(to_mins(r1['endTime']), to_mins(r2['endTime'])):
                        print(f"TEACHER CONFLICT: {r1['teacher']} at {r1['time']} ({r1['grade']}) vs {r2['time']} ({r2['grade']})")
                        teacher_conflicts += 1
                if r1['grade'] == r2['grade'] and r1['section'] == r2['section']:
                    if max(to_mins(r1['startTime']), to_mins(r2['startTime'])) < min(to_mins(r1['endTime']), to_mins(r2['endTime'])):
                        print(f"SECTION CONFLICT: {r1['grade']} {r1['section']} at {r1['time']} vs {r2['time']}")
                        section_conflicts += 1

    print(f"Teacher Conflicts: {teacher_conflicts}")
    print(f"Section Conflicts: {section_conflicts}")
    print(f"Validation Status: {'READY / VALIDATED' if teacher_conflicts == 0 and section_conflicts == 0 else 'INVALID'}")

    with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print("Master exam_data.json updated successfully!")

    # Write Master CSV
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
    print("CSV updated and copied to Downloads!")

if __name__ == '__main__':
    main()
