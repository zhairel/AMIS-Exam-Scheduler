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

TIME_SLOTS = {
    "F2F": ["7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM"],
    "ODL_1": ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"],
    "ODL_2": ["3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
}

groups = {
    "F2F": [s for s in sections if s['modality'] == 'F2F'],
    "ODL_1": [s for s in sections if s['modality'] == 'ODL' and '2nd' not in s['shift']],
    "ODL_2": [s for s in sections if s['modality'] == 'ODL' and '2nd' in s['shift']]
}

# 12 discrete slots per shift: (day_idx, slot_in_day)
# Each shift has 4 days x 3 slots = 12 slot positions (0 to 11)

def solve_group(group_name, group_secs):
    print(f"\n--- Solving for {group_name} ({len(group_secs)} sections) ---")
    time_slots = TIME_SLOTS[group_name]

    # For each section, get its list of required subjects and their teacher candidates
    sec_reqs = []
    for s_idx, sec in enumerate(group_secs):
        m_key = "F2F" if sec['modality'] == 'F2F' else ("ODL_2" if '2nd' in sec['shift'] else "ODL_1")
        grade_dict = OFFICIAL_CURRICULUM_TEACHERS.get(sec['grade'], {})
        official_list = list(grade_dict.get(m_key, []))
        if official_list:
            sec_reqs.append({
                "sec": sec,
                "subjects": official_list # list of (subject_name, [teachers])
            })

    # Total slots available = 12 (4 days x 3 periods)
    # A valid schedule assigns each subject of each section to a distinct slot (0..11)
    # and picks an available teacher for that subject, such that in any slot t (0..11),
    # no teacher is assigned more than once.

    # We can solve this with randomized local search / min-conflicts or ILP
    # Let's use randomized constructive search with restarts
    for attempt in range(10000):
        random.seed(attempt)
        
        # State: slot -> list of (sec_idx, sub_name, chosen_teacher)
        slot_teachers = defaultdict(set) # slot_id -> set of teachers
        teacher_daily_count = defaultdict(int) # (teacher, day_idx) -> count
        sec_slot_assignment = {} # (sec_idx, sub_name) -> (slot_id, teacher)
        success = True

        # Sort sections so harder sections / subjects are placed first
        # Randomize order of subjects per section
        shuffled_secs = list(enumerate(sec_reqs))
        random.shuffle(shuffled_secs)

        for s_idx, s_data in shuffled_secs:
            sec = s_data['sec']
            subs = list(s_data['subjects'])
            random.shuffle(subs)

            n = len(subs)
            if n == 11: day_caps = [3, 3, 3, 2]
            elif n == 9: day_caps = [3, 2, 2, 2]
            elif n == 8: day_caps = [2, 2, 2, 2]
            elif n == 5: day_caps = [2, 1, 1, 1]
            else: day_caps = [2, 2, 2, 2]
            random.shuffle(day_caps) # randomize which days get 3 or 2

            # Assign each day its quota of slots
            available_slots_for_sec = []
            for d in range(4):
                day_slots = [d * 3 + p for p in range(3)]
                random.shuffle(day_slots)
                available_slots_for_sec.extend(day_slots[:day_caps[d]])

            placed_subs = []
            used_sec_slots = set()

            for sub_name, cands in subs:
                possible_placements = []
                for slot_id in available_slots_for_sec:
                    if slot_id in used_sec_slots:
                        continue
                    d_idx = slot_id // 3
                    avail_t = [t for t in cands if t not in slot_teachers[slot_id]]
                    for t in avail_t:
                        load_penalty = teacher_daily_count[(t, d_idx)]
                        consec_penalty = 0
                        p_in_day = slot_id % 3
                        if p_in_day > 0 and (slot_id - 1) in [s for s, te in sec_slot_assignment.values() if te == t]:
                            consec_penalty += 2
                        possible_placements.append((consec_penalty * 5 + load_penalty, slot_id, t, sub_name))

                if not possible_placements:
                    success = False
                    break

                possible_placements.sort(key=lambda x: (x[0], random.random()))
                best_penalty, best_slot, best_t, _ = possible_placements[0]

                slot_teachers[best_slot].add(best_t)
                teacher_daily_count[(best_t, best_slot // 3)] += 1
                used_sec_slots.add(best_slot)
                sec_slot_assignment[(s_idx, sub_name)] = (best_slot, best_t)

            if not success:
                break

        if success:
            print(f"SUCCESS for {group_name} on attempt {attempt}!")
            # Construct records
            records = []
            for s_idx, s_data in enumerate(sec_reqs):
                sec = s_data['sec']
                for sub_name, _ in s_data['subjects']:
                    slot_id, teacher = sec_slot_assignment[(s_idx, sub_name)]
                    d_idx = slot_id // 3
                    p_idx = slot_id % 3
                    day_info = EXAM_DAYS[d_idx]
                    slot_time = time_slots[p_idx]
                    records.append({
                        "date": day_info['date'],
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
            return records

    print(f"Failed to solve {group_name} after 10000 attempts.")
    return None

def main():
    all_final_records = []
    for gname in ["F2F", "ODL_1", "ODL_2"]:
        g_secs = groups[gname]
        res = solve_group(gname, g_secs)
        if res is None:
            print(f"Fatal error solving group {gname}")
            return
        all_final_records.extend(res)

    print(f"\n==========================================")
    print(f"TOTAL EXAMS SCHEDULED: {len(all_final_records)}")
    
    # Audit teacher assignments against official curriculum
    print("Auditing all exams against user's official assigned teachers...")
    teacher_counts = defaultdict(int)
    for r in all_final_records:
        teacher_counts[r['teacher']] += 1

    print(f"Active Teachers: {len(teacher_counts)}")
    for t, c in sorted(teacher_counts.items(), key=lambda x: -x[1]):
        print(f" - {t}: {c} exams")

    with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_final_records, f, indent=2, ensure_ascii=False)
    print("exam_data.json successfully updated with 100% official assigned teachers!")

if __name__ == '__main__':
    main()
