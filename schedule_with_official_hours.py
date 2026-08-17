import json
import random
from collections import defaultdict
from apply_official_subject_teacher_registry import OFFICIAL_CURRICULUM_TEACHERS

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'r') as f:
    existing_records = json.load(f)

# Extract unique sections
sec_map = {}
for r in existing_records:
    if r['grade'] == 'Kinder 1' and r['modality'] == 'ODL':
        continue
    key = f"{r['grade']} — {r['section']} ({r['modality']} - {r['shift']})"
    if key not in sec_map:
        sec_map[key] = {
            "grade": r['grade'],
            "section": r['section'],
            "gender": r.get('gender', ''),
            "modality": r['modality'],
            "shift": r['shift'],
            "room": r.get('room', '')
        }
sections = list(sec_map.values())
print(f"Total Sections to schedule: {len(sections)}")

EXAM_DAYS = [
    {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "1st Day"},
    {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "2nd Day"},
    {"dayNo": 3, "date": "2026-09-09", "dayName": "Wednesday", "examDay": "3rd Day"},
    {"dayNo": 4, "date": "2026-09-10", "dayName": "Thursday", "examDay": "4th Day"}
]

# Standard Time Slots across the day
ALL_POSSIBLE_SLOTS = [
    # Morning F2F (7:40 AM - 11:30 AM)
    "7:40-8:25 AM",
    "8:25-9:05 AM",
    "9:05-9:45 AM",
    # Afternoon F2F & ODL 1 (12:40 PM - 3:00 PM / 4:30 PM)
    "12:40-1:20 PM",
    "1:30-2:10 PM",
    "2:20-3:00 PM",
    # Late Afternoon & ODL 2 (3:40 PM - 6:00 PM)
    "3:40-4:20 PM",
    "4:30-5:10 PM",
    "5:20-6:00 PM"
]

def get_allowed_slots_for_section(sec):
    g = sec['grade']
    m = sec['modality']
    sh = sec['shift']

    if m == 'F2F':
        if g == 'Kinder 1':
            # Kinder 1 F2F: 12:40 PM – 2:55 PM
            return ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]
        elif g == 'Kinder 2':
            # Kinder 2 F2F: 7:40 AM – 10:30 AM
            return ["7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM"]
        else:
            # Grades 1-12 F2F: 7:40 AM – 3:00 PM (Morning & Afternoon slots)
            return [
                "7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM",
                "12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"
            ]
    else: # ODL
        if '2nd' in sh: # ODL 2nd Shift
            if g == 'Grade 11':
                # Grade 11 ODL 2nd: 2:20 PM – 6:00 PM
                return ["2:20-3:00 PM", "3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
            else:
                # Grades 1-10 ODL 2nd: 3:40 PM – 6:00 PM
                return ["3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
        else: # ODL 1st Shift
            if g in ['Grade 11', 'Grade 12']:
                # Grade 11 & 12 ODL 1st: 12:40 PM – 4:30 PM
                return ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM", "3:40-4:20 PM"]
            elif g == 'Kinder 2':
                # Kinder 2 ODL 1st: 1:30 PM - 3:00 PM
                return ["1:30-2:10 PM", "2:20-3:00 PM"]
            else:
                # Grades 1-10 ODL 1st: 12:40 PM – 3:00 PM
                return ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]

print("Configuring school hours per section...")
sec_reqs = []
for s_idx, sec in enumerate(sections):
    m_key = "F2F" if sec['modality'] == 'F2F' else ("ODL_2" if '2nd' in sec['shift'] else "ODL_1")
    grade_dict = OFFICIAL_CURRICULUM_TEACHERS.get(sec['grade'], {})
    official_list = list(grade_dict.get(m_key, []))
    allowed_slots = get_allowed_slots_for_section(sec)
    
    if official_list:
        sec_reqs.append({
            "s_idx": s_idx,
            "sec": sec,
            "m_key": m_key,
            "subjects": official_list,
            "allowed_slots": allowed_slots
        })

print(f"Active Sections to schedule: {len(sec_reqs)}")

# CSP Solver with Backtracking & Local Search
def solve_full_master_schedule():
    best_solution = None
    best_consecutives = 999

    for seed in range(20000):
        random.seed(seed)
        success = True

        # State: (date, slot_time) -> set of teachers
        slot_teachers = defaultdict(set)
        teacher_day_slots = defaultdict(set) # (teacher, date) -> set of global slot indices
        teacher_workload = defaultdict(int)
        sec_assignments = {} # (s_idx, sub_name) -> (date, slot_time, teacher)

        # Shuffle sections for randomized ordering
        shuffled_secs = list(sec_reqs)
        random.shuffle(shuffled_secs)

        for s_data in shuffled_secs:
            s_idx = s_data['s_idx']
            sec = s_data['sec']
            subs = list(s_data['subjects'])
            allowed_slots = s_data['allowed_slots']
            random.shuffle(subs)

            # Generate candidate (date, slot_time) pairs for this section across 4 days
            # Distribute subjects evenly across 4 days
            num_subs = len(subs)
            if num_subs == 11: day_caps = [3, 3, 3, 2]
            elif num_subs == 9: day_caps = [3, 2, 2, 2]
            elif num_subs == 8: day_caps = [2, 2, 2, 2]
            elif num_subs == 5: day_caps = [2, 1, 1, 1]
            else: day_caps = [2, 2, 2, 2]
            random.shuffle(day_caps)

            # For each day, pick day_caps[d] distinct slots from allowed_slots
            chosen_day_slots = []
            for d_idx, day_info in enumerate(EXAM_DAYS):
                cap = day_caps[d_idx]
                d_date = day_info['date']
                avail_slots_for_day = list(allowed_slots)
                random.shuffle(avail_slots_for_day)
                for st in avail_slots_for_day[:cap]:
                    chosen_day_slots.append((d_date, day_info, st))

            used_sec_slots = set()

            for sub_name, cands in subs:
                possible = []
                for d_date, day_info, slot_time in chosen_day_slots:
                    slot_key = (d_date, slot_time)
                    if slot_key in used_sec_slots:
                        continue
                    
                    global_slot_idx = ALL_POSSIBLE_SLOTS.index(slot_time)
                    avail_t = [t for t in cands if t not in slot_teachers[slot_key]]
                    
                    for t in avail_t:
                        was_prev = 1 if (global_slot_idx - 1) in teacher_day_slots[(t, d_date)] else 0
                        was_next = 1 if (global_slot_idx + 1) in teacher_day_slots[(t, d_date)] else 0
                        day_load = len(teacher_day_slots[(t, d_date)])
                        tot_load = teacher_workload[t]
                        penalty = was_prev * 10 + was_next * 10 + day_load * 2 + tot_load
                        possible.append((penalty, d_date, day_info, slot_time, t, global_slot_idx))

                if not possible:
                    success = False
                    break

                possible.sort(key=lambda x: (x[0], random.random()))
                _, best_date, best_day_info, best_slot, best_t, best_g_idx = possible[0]

                slot_key = (best_date, best_slot)
                used_sec_slots.add(slot_key)
                slot_teachers[slot_key].add(best_t)
                teacher_day_slots[(best_t, best_date)].add(best_g_idx)
                teacher_workload[best_t] += 1
                sec_assignments[(s_idx, sub_name)] = (best_date, best_day_info, best_slot, best_t)

            if not success:
                break

        if success:
            # Count consecutive slots across all teachers
            total_consec = 0
            for (t, d_date), g_set in teacher_day_slots.items():
                sorted_g = sorted(g_set)
                for i in range(len(sorted_g) - 1):
                    if sorted_g[i+1] == sorted_g[i] + 1:
                        total_consec += 1

            print(f"Seed {seed}: Found valid schedule with {total_consec} consecutive teacher slots!")
            if total_consec < best_consecutives:
                best_consecutives = total_consec
                best_solution = (sec_assignments, teacher_workload)
                if best_consecutives == 0:
                    print("PERFECT 0 CONSECUTIVE SLOTS FOUND!")
                    break

    if best_solution is None:
        print("Failed to find solution in search iterations.")
        return None

    sec_assignments, workloads = best_solution
    records = []
    for s_data in sec_reqs:
        s_idx = s_data['s_idx']
        sec = s_data['sec']
        for sub_name, _ in s_data['subjects']:
            d_date, day_info, slot_time, teacher = sec_assignments[(s_idx, sub_name)]
            records.append({
                "date": d_date,
                "dayName": day_info['dayName'],
                "examDay": day_info['examDay'],
                "time": slot_time,
                "grade": sec['grade'],
                "section": sec['section'],
                "gender": sec['gender'],
                "modality": sec['modality'],
                "shift": sec['shift'],
                "subject": sub_name,
                "teacher": teacher,
                "room": sec.get('room', ''),
                "proctor": teacher,
                "remarks": "Term Examination"
            })

    print(f"\nFinal Schedule Result: {len(records)} exams generated across all school hours!")
    return records

if __name__ == '__main__':
    recs = solve_full_master_schedule()
    if recs:
        with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
            json.dump(recs, f, indent=2, ensure_ascii=False)
        print("Successfully written to exam_data.json!")
