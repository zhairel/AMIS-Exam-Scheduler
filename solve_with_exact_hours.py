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

# Build section requirement objects
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
            "subjects": official_list
        })

print(f"Active Sections: {len(sec_reqs)}")

# Define slot options per grade/modality
def get_daily_slot_options(sec, count_for_day):
    g = sec['grade']
    m = sec['modality']
    sh = sec['shift']

    if m == 'F2F':
        if g == 'Kinder 1':
            # 12:40 PM – 2:55 PM
            slots = ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]
            return [slots[:count_for_day]]
        elif g == 'Kinder 2':
            # 7:40 AM – 10:30 AM
            slots = ["7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM"]
            return [slots[:count_for_day]]
        else:
            # Grades 1 to 12 F2F (7:40 AM – 3:00 PM)
            # Options for 3 subjects:
            # Option A: 2 in morning (7:40, 8:25) + 1 in afternoon (12:40)
            # Option B: 2 in morning (8:25, 9:05) + 1 in afternoon (1:30)
            # Option C: 1 in morning (7:40) + 2 in afternoon (12:40, 1:30)
            # Option D: 3 in morning (7:40, 8:25, 9:05)
            # Option E: 3 in afternoon (12:40, 1:30, 2:20)
            if count_for_day == 3:
                return [
                    ["7:40-8:25 AM", "8:25-9:05 AM", "12:40-1:20 PM"],
                    ["7:40-8:25 AM", "9:05-9:45 AM", "1:30-2:10 PM"],
                    ["8:25-9:05 AM", "12:40-1:20 PM", "1:30-2:10 PM"],
                    ["7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM"],
                    ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]
                ]
            else: # count_for_day == 2
                return [
                    ["7:40-8:25 AM", "12:40-1:20 PM"],
                    ["8:25-9:05 AM", "1:30-2:10 PM"],
                    ["7:40-8:25 AM", "8:25-9:05 AM"],
                    ["12:40-1:20 PM", "1:30-2:10 PM"]
                ]
    else: # ODL
        if '2nd' in sh: # ODL 2nd Shift
            if g == 'Grade 11':
                # 2:20 PM - 6:00 PM
                if count_for_day == 3:
                    return [["2:20-3:00 PM", "3:40-4:20 PM", "4:30-5:10 PM"], ["3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]]
                else:
                    return [["2:20-3:00 PM", "4:30-5:10 PM"], ["3:40-4:20 PM", "5:20-6:00 PM"]]
            else:
                # Grades 1-10 (3:40 PM - 6:00 PM)
                slots = ["3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
                return [slots[:count_for_day]]
        else: # ODL 1st Shift
            if g in ['Grade 11', 'Grade 12']:
                # 12:40 PM - 4:30 PM
                if count_for_day == 3:
                    return [["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"], ["1:30-2:10 PM", "2:20-3:00 PM", "3:40-4:20 PM"]]
                else:
                    return [["12:40-1:20 PM", "2:20-3:00 PM"], ["1:30-2:10 PM", "3:40-4:20 PM"]]
            elif g == 'Kinder 2':
                slots = ["1:30-2:10 PM", "2:20-3:00 PM"]
                return [slots[:count_for_day]]
            else:
                # Grades 1-10 (12:40 PM - 3:00 PM)
                slots = ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"]
                return [slots[:count_for_day]]

def solve():
    for seed in range(20000):
        random.seed(seed)
        final_records = []
        teacher_busy = defaultdict(set) # (date, time) -> set
        teacher_workload = defaultdict(int)
        success = True

        # For each day (0..3)
        for day_idx, day_info in enumerate(EXAM_DAYS):
            d_date = day_info['date']

            # Determine each section's subjects for this day
            day_sec_exams = []
            for s_data in sec_reqs:
                sec = s_data['sec']
                subs = list(s_data['subjects'])
                
                # Deterministic rotation per seed
                offset = (s_data['s_idx'] * 5 + seed * 3) % len(subs)
                rotated = subs[offset:] + subs[:offset]
                
                total = len(rotated)
                if total == 11: caps = [3, 3, 3, 2]
                elif total == 9: caps = [3, 2, 2, 2]
                elif total == 8: caps = [2, 2, 2, 2]
                elif total == 5: caps = [2, 1, 1, 1]
                else: caps = [2, 2, 2, 2]

                start_p = sum(caps[:day_idx])
                end_p = start_p + caps[day_idx]
                day_subs = rotated[start_p:end_p]
                
                if day_subs:
                    slot_options = get_daily_slot_options(sec, len(day_subs))
                    chosen_slots = random.choice(slot_options)
                    for i, (sub_name, cands) in enumerate(day_subs):
                        slot_time = chosen_slots[i]
                        day_sec_exams.append({
                            "sec": sec,
                            "sub": sub_name,
                            "cands": cands,
                            "slot_time": slot_time
                        })

            # Now assign teachers for this day
            # Group by slot_time
            exams_by_slot = defaultdict(list)
            for item in day_sec_exams:
                exams_by_slot[item['slot_time']].append(item)

            for slot_time, items in exams_by_slot.items():
                items.sort(key=lambda x: len(x['cands'])) # MRV
                used = set(teacher_busy[(d_date, slot_time)])

                for item in items:
                    avail = [t for t in item['cands'] if t not in used]
                    if not avail:
                        success = False
                        break
                    
                    # Sort by least overall workload
                    avail.sort(key=lambda t: teacher_workload[t])
                    best_t = avail[0]

                    used.add(best_t)
                    teacher_busy[(d_date, slot_time)].add(best_t)
                    teacher_workload[best_t] += 1

                    final_records.append({
                        "date": d_date,
                        "dayName": day_info['dayName'],
                        "examDay": day_info['examDay'],
                        "time": slot_time,
                        "grade": item['sec']['grade'],
                        "section": item['sec']['section'],
                        "gender": item['sec']['gender'],
                        "modality": item['sec']['modality'],
                        "shift": item['sec']['shift'],
                        "subject": item['sub'],
                        "teacher": best_t,
                        "room": item['sec'].get('room', ''),
                        "proctor": best_t,
                        "remarks": "Term Examination"
                    })

                if not success: break
            if not success: break

        if success and len(final_records) == 597:
            print(f"Seed {seed}: SUCCESS! Generated all {len(final_records)} exams with Official School Hours!")
            return final_records

    print("Failed to find schedule in 20000 seeds.")
    return None

if __name__ == '__main__':
    recs = solve()
    if recs:
        with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
            json.dump(recs, f, indent=2, ensure_ascii=False)
        print("Master schedule saved to exam_data.json successfully!")
