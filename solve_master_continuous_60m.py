import json
import random
import sys
from collections import defaultdict
sys.path.append("/home/tatsuya/Projects/AMIS/amis_exam_calendar")
from apply_official_subject_teacher_registry import OFFICIAL_CURRICULUM_TEACHERS

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

def get_slots_for_section(sec, count, opt=0):
    g = sec['grade']
    m = sec['modality']
    sh = sec['shift']

    if m == 'F2F':
        if g == 'Kinder 1':
            if count == 1: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}]
            else: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}, {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM"}]
        elif g == 'Kinder 2':
            if count == 1: return [{"start": "7:40 AM", "end": "8:40 AM", "time": "7:40 AM – 8:40 AM"}]
            else: return [{"start": "7:40 AM", "end": "8:40 AM", "time": "7:40 AM – 8:40 AM"}, {"start": "9:10 AM", "end": "10:10 AM", "time": "9:10 AM – 10:10 AM"}]
        else: # Grades 1-12 F2F
            if count == 1: return [{"start": "7:40 AM", "end": "8:40 AM", "time": "7:40 AM – 8:40 AM"}]
            elif count == 2: return [{"start": "7:40 AM", "end": "8:40 AM", "time": "7:40 AM – 8:40 AM"}, {"start": "8:40 AM", "end": "9:40 AM", "time": "8:40 AM – 9:40 AM"}]
            else: return [{"start": "7:40 AM", "end": "8:40 AM", "time": "7:40 AM – 8:40 AM"}, {"start": "8:40 AM", "end": "9:40 AM", "time": "8:40 AM – 9:40 AM"}, {"start": "10:00 AM", "end": "11:00 AM", "time": "10:00 AM – 11:00 AM"}]
    else: # ODL
        if '2nd' in sh: # ODL 2nd Shift
            if g == 'Grade 11':
                if count == 1: return [{"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}]
                elif count == 2: return [{"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}, {"start": "4:50 PM", "end": "5:50 PM", "time": "4:50 PM – 5:50 PM"}]
                else: return [{"start": "2:20 PM", "end": "3:20 PM", "time": "2:20 PM – 3:20 PM"}, {"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}, {"start": "4:50 PM", "end": "5:50 PM", "time": "4:50 PM – 5:50 PM"}]
            elif g == 'Kinder 2':
                all_s = [{"start": "2:30 PM", "end": "3:30 PM", "time": "2:30 PM – 3:30 PM"}, {"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}, {"start": "4:50 PM", "end": "5:50 PM", "time": "4:50 PM – 5:50 PM"}]
                if count == 1: return [all_s[opt % 3]]
                else: return all_s[1:]
            else: # Grades 1-10
                if count == 1: return [{"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}]
                elif count == 2:
                    if opt % 2 == 0:
                        return [{"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}, {"start": "4:50 PM", "end": "5:50 PM", "time": "4:50 PM – 5:50 PM"}]
                    else:
                        return [{"start": "2:30 PM", "end": "3:30 PM", "time": "2:30 PM – 3:30 PM"}, {"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}]
                else: # 3 exams
                    return [{"start": "2:30 PM", "end": "3:30 PM", "time": "2:30 PM – 3:30 PM"}, {"start": "3:40 PM", "end": "4:40 PM", "time": "3:40 PM – 4:40 PM"}, {"start": "4:50 PM", "end": "5:50 PM", "time": "4:50 PM – 5:50 PM"}]
        else: # ODL 1st Shift
            if g in ['Grade 11', 'Grade 12']:
                if count == 1: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}]
                elif count == 2: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}, {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM"}]
                else: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}, {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM"}, {"start": "3:00 PM", "end": "4:00 PM", "time": "3:00 PM – 4:00 PM"}]
            elif g == 'Kinder 2':
                if count == 1:
                    sl = ["12:40 PM – 1:40 PM", "1:50 PM – 2:50 PM"][opt % 2]
                    st, et = sl.split(" – ")
                    return [{"start": st, "end": et, "time": sl}]
                else:
                    return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}, {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM"}]
            else: # Grades 1-10
                if count == 1: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}]
                elif count == 2: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}, {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM"}]
                else: return [{"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM"}, {"start": "1:45 PM", "end": "2:45 PM", "time": "1:45 PM – 2:45 PM"}, {"start": "2:50 PM", "end": "3:50 PM", "time": "2:50 PM – 3:50 PM"}]

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

print(f"Total Sections to Schedule: {len(sec_reqs)}")

# Master Solver
def solve_all_sections():
    # Order sections by shift and grade
    grade_buckets = defaultdict(list)
    for s in sec_reqs:
        grade_buckets[(s['sec']['grade'], s['m_key'])].append(s)

    items = []
    for (g_name, m_key), s_list in grade_buckets.items():
        for i, s_data in enumerate(s_list):
            items.append((s_data, i))

    for attempt in range(100000):
        random.seed(attempt)
        teacher_busy = defaultdict(list)
        teacher_workload = defaultdict(int)
        sec_assignments = {}
        success = True

        # Randomize section processing order
        shuffled_items = list(items)
        random.shuffle(shuffled_items)
        shuffled_items.sort(key=lambda x: -len(x[0]['subjects']))

        for s_data, sec_order in shuffled_items:
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
                day_slots = get_slots_for_section(sec, cap, opt=d_idx + sec_order)
                for sl in day_slots:
                    target_slots.append((d_idx, day_info, sl))

            shuffled_subs = list(subs)
            offset = (sec_order * 4 + attempt * 3) % len(shuffled_subs)
            shuffled_subs = shuffled_subs[offset:] + shuffled_subs[:offset]

            sorted_subs = sorted(shuffled_subs, key=lambda x: (len(x[1]), random.random()))
            used_target_slots = set()

            placed_all = True

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
                        for (t_st, t_et) in teacher_busy[(t, d_date)]:
                            if max(st_m, t_st) < min(et_m, t_et):
                                has_overlap = True
                                break
                        if not has_overlap:
                            load = teacher_workload[t]
                            day_load = len(teacher_busy[(t, d_date)])
                            score = load * 2 + day_load * 5
                            valid_options.append((score, ts_idx, d_date, day_info, sl, t, st_m, et_m))

                if not valid_options:
                    placed_all = False
                    break

                valid_options.sort(key=lambda x: (x[0], random.random()))
                _, best_ts_idx, best_date, best_day_info, best_sl, best_t, st_m, et_m = valid_options[0]

                used_target_slots.add(best_ts_idx)
                teacher_busy[(best_t, best_date)].append((st_m, et_m))
                teacher_workload[best_t] += 1
                sec_assignments[(s_idx, sub_name)] = (best_date, best_day_info, best_sl, best_t)

            if not placed_all:
                success = False
                break

        if success:
            print(f"SUCCESS on attempt {attempt}!")
            records = []
            for s_data in sec_reqs:
                s_idx = s_data['s_idx']
                sec = s_data['sec']
                for sub_name, _ in s_data['subjects']:
                    d_date, day_info, slot_dict, teacher = sec_assignments[(s_idx, sub_name)]
                    records.append({
                        "date": d_date,
                        "dayName": day_info['dayName'],
                        "examDay": day_info['examDay'],
                        "startTime": slot_dict['start'],
                        "endTime": slot_dict['end'],
                        "time": slot_dict['time'],
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
            return records

    print("FAILED after 100000 attempts.")
    return None

if __name__ == '__main__':
    recs = solve_all_sections()
    if recs:
        print(f"Total Master Exams Generated: {len(recs)}")
        with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
            json.dump(recs, f, indent=2, ensure_ascii=False)
        print("Master exam_data.json saved successfully!")
