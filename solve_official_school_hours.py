import json
import random
from collections import defaultdict
from apply_official_subject_teacher_registry import OFFICIAL_CURRICULUM_TEACHERS

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'r') as f:
    existing_records = json.load(f)

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

def get_allowed_slots(sec):
    g = sec['grade']
    m = sec['modality']
    sh = sec['shift']

    if m == 'F2F':
        if g == 'Kinder 1':
            return ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]
        elif g == 'Kinder 2':
            return ["7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM"]
        else:
            # F2F Grades 1-12: 7:40 AM - 3:00 PM
            return [
                "7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM",
                "12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"
            ]
    else: # ODL
        if '2nd' in sh:
            if g == 'Grade 11':
                return ["2:20-3:00 PM", "3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
            else:
                return ["3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
        else:
            if g in ['Grade 11', 'Grade 12']:
                return ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM", "3:40-4:20 PM"]
            elif g == 'Kinder 2':
                return ["1:30-2:10 PM", "2:20-3:00 PM"]
            else:
                return ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]

sec_reqs = []
for s_idx, sec in enumerate(sections):
    m_key = "F2F" if sec['modality'] == 'F2F' else ("ODL_2" if '2nd' in sec['shift'] else "ODL_1")
    grade_dict = OFFICIAL_CURRICULUM_TEACHERS.get(sec['grade'], {})
    official_list = list(grade_dict.get(m_key, []))
    
    if official_list:
        sec_reqs.append({
            "s_idx": s_idx,
            "sec": sec,
            "m_key": m_key,
            "subjects": official_list,
            "allowed_slots": get_allowed_slots(sec)
        })

print(f"Active sections to schedule: {len(sec_reqs)}")

# Sequential backtracking search across sections
def solve_all():
    for seed in range(5000):
        random.seed(seed)
        
        # State: (date, slot_time) -> set of teachers
        slot_teachers = defaultdict(set)
        teacher_day_slots = defaultdict(set)
        teacher_workload = defaultdict(int)
        
        sec_assignments = {} # (s_idx, sub_name) -> (date, day_info, slot_time, teacher)
        success = True

        # Sort sections by most constrained first
        shuffled_secs = list(sec_reqs)
        # Random shuffle with seed
        random.shuffle(shuffled_secs)
        # Prioritize sections with few allowed slots
        shuffled_secs.sort(key=lambda s: len(s['allowed_slots']))

        for s_data in shuffled_secs:
            s_idx = s_data['s_idx']
            sec = s_data['sec']
            subs = list(s_data['subjects'])
            allowed_slots = s_data['allowed_slots']

            # Generate all possible (date, slot_time) available for this section across 4 days
            all_sec_slots = []
            for day_info in EXAM_DAYS:
                d_date = day_info['date']
                for st in allowed_slots:
                    all_sec_slots.append((d_date, day_info, st))

            # Distribute subjects across 4 days
            num_subs = len(subs)
            if num_subs == 11: day_caps = [3, 3, 3, 2]
            elif num_subs == 9: day_caps = [3, 2, 2, 2]
            elif num_subs == 8: day_caps = [2, 2, 2, 2]
            elif num_subs == 5: day_caps = [2, 1, 1, 1]
            else: day_caps = [2, 2, 2, 2]
            random.shuffle(day_caps)

            # Assign each subject of this section
            # Sort subjects by fewest candidate teachers
            sorted_subs = sorted(subs, key=lambda x: len(x[1]))
            used_slots_for_this_sec = set()
            sec_day_counts = defaultdict(int) # d_date -> count

            placed_all_subs_for_sec = True

            for sub_name, cands in sorted_subs:
                candidates_placements = []
                for d_date, day_info, st in all_sec_slots:
                    slot_key = (d_date, st)
                    if slot_key in used_slots_for_this_sec:
                        continue
                    
                    # Check day capacity
                    d_idx = [d['date'] for d in EXAM_DAYS].index(d_date)
                    if sec_day_counts[d_date] >= day_caps[d_idx]:
                        continue

                    avail_t = [t for t in cands if t not in slot_teachers[slot_key]]
                    for t in avail_t:
                        # Workload and consecutive penalty
                        tot_load = teacher_workload[t]
                        day_load = len(teacher_day_slots[(t, d_date)])
                        score = tot_load + day_load * 2
                        candidates_placements.append((score, d_date, day_info, st, t))

                if not candidates_placements:
                    placed_all_subs_for_sec = False
                    break

                candidates_placements.sort(key=lambda x: (x[0], random.random()))
                _, best_date, best_day_info, best_st, best_t = candidates_placements[0]

                slot_key = (best_date, best_st)
                used_slots_for_this_sec.add(slot_key)
                sec_day_counts[best_date] += 1
                slot_teachers[slot_key].add(best_t)
                teacher_day_slots[(best_t, best_date)].add(best_st)
                teacher_workload[best_t] += 1
                sec_assignments[(s_idx, sub_name)] = (best_date, best_day_info, best_st, best_t)

            if not placed_all_subs_for_sec:
                success = False
                break

        if success:
            print(f"Seed {seed}: SUCCESS! 100% Scheduled across exact school hours with zero conflicts!")
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
            return records

    print("Search ended without finding solution.")
    return None

if __name__ == '__main__':
    recs = solve_all()
    if recs:
        print(f"Total exams in schedule: {len(recs)}")
        with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
            json.dump(recs, f, indent=2, ensure_ascii=False)
        print("exam_data.json successfully written!")
