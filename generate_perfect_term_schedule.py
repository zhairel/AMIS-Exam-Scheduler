import json
import os
import random
from collections import defaultdict

# 1. Official Curriculum Requirements per Grade
CURRICULUM = {
    "Kinder 1": ["Circle Time 1", "Circle Time 2", "Qur'an", "Arabic", "Hadith"],
    "Kinder 2": ["Circle Time 1", "Circle Time 2", "Qur'an", "Arabic", "Hadith"],
    "Grade 1": ["GMRC", "Language", "Reading and Literacy", "Math", "SHAF", "Makabansa", "Arabic", "Qur'an"],
    "Grade 2": ["GMRC", "English", "Filipino", "Math", "Arabic", "SHAF", "Makabansa", "Qur'an"],
    "Grade 3": ["Science", "Math", "GMRC", "Arabic", "English", "Makabansa", "Qur'an", "SHAF", "Filipino"],
    "Grade 4": ["AP", "Math", "TLE", "GMRC", "SHAF", "Arabic", "Qur'an", "MAPEH", "English", "Science", "Filipino"],
    "Grade 5": ["SHAF", "AP", "Filipino", "GMRC", "English", "Qur'an", "MAPEH", "Arabic", "Science", "Math", "TLE"],
    "Grade 6": ["AP", "English", "Science", "Math", "GMRC", "MAPEH", "SHAF", "Qur'an", "TLE", "Arabic", "Filipino"],
    "Grade 7": ["GMRC", "Sci", "Qur'an", "MAPEH", "English", "TLE", "Arabic", "SHAF", "Math", "Soc.Sci", "Filipino"],
    "Grade 7 & 8": ["GMRC", "Sci", "Qur'an", "MAPEH", "English", "TLE", "Arabic", "SHAF", "Math", "Soc.Sci", "Filipino"],
    "Grade 8": ["Sci", "Math", "Values Ed.", "Soc.Sci", "MAPEH", "English", "Filipino", "TLE", "SHAF", "Qur'an", "Arabic"],
    "Grade 9": ["SHAF", "Qur'an", "Math", "TLE", "Soc.Sci", "Arabic", "English", "MAPEH", "Sci", "ESP", "Filipino"],
    "Grade 9 & 10": ["SHAF", "Qur'an", "Math", "TLE", "Soc.Sci", "Arabic", "English", "MAPEH", "Sci", "ESP", "Filipino"],
    "Grade 10": ["Qur'an", "TLE", "Arabic", "SHAF", "MAPEH", "English", "Soc.Sci", "Math", "Filipino", "Sci", "ESP"],
    "Grade 11": ["Arabic", "Gen Bio 1", "Qur'an", "Gen Math", "EC", "PSKP", "LCS", "SHAF", "Gen Science"],
    "Grade 12": ["Gen. Physics 1", "Gen Bio 1", "SHAF", "Arabic", "Qur'an", "21st Lit.", "Prac. Res. 2", "MIL", "PE 12"]
}

# 2. Official Faculty Capabilities
FACULTY_ELEMENTARY = {
    "Teacher Wendy": ["Circle Time 1", "Circle Time 2", "Math", "Makabansa", "Science"],
    "Teacher Katrina": ["Reading and Literacy", "Math", "Language", "R & L"],
    "Teacher Norhydie": ["Makabansa", "Filipino", "English", "AP", "MAPEH"],
    "Teacher Jerlyn": ["Science", "Math"],
    "Teacher Sahdia": ["GMRC", "Language", "Arabic"],
    "Teacher Sitti": ["Math", "Filipino"],
    "Teacher Arvin": ["Math", "English", "TLE"],
    "Teacher Ayah": ["Circle Time 1", "Circle Time 2"],
    "Teacher Junaisah": ["Science"],
    "Teacher Joanna": ["Circle Time 1", "Circle Time 2", "Math", "Filipino"],
    "Teacher Marham": ["English"],
    "Teacher Saimona": ["Math", "Science", "MAPEH", "AP"],
    "Teacher Jessa": ["English", "Filipino"],
    "Teacher Anna": ["Science", "TLE"],
    "Teacher Zuhora": ["Filipino", "Makabansa", "MAPEH", "GMRC", "AP"],
    "Teacher Monisa": ["Makabansa", "AP", "TLE", "Filipino"],
    "Teacher Normylah": ["Filipino", "AP"],
    "Teacher Keychelle": ["Circle Time 1", "Circle Time 2", "MAPEH", "AP"],
    "Teacher Jenny": ["English", "Filipino", "TLE", "Makabansa"],
    "Teacher Hannah": ["Math"],
    "Teacher Zara": ["Makabansa", "MAPEH"],
    "Teacher Fhairudz": ["Math", "Science"]
}

FACULTY_HS = {
    "Teacher Radzmia": ["Science", "General Biology 1", "General Biology 2", "Sci", "Gen Bio 1"],
    "Teacher Halnaisa": ["TLE", "MAPEH"],
    "Teacher Shirehan": ["Social Science", "PSKP", "Soc.Sci", "PSKP 11"],
    "Teacher Angeleni": ["TLE", "MAPEH"],
    "Teacher Franchette": ["MAPEH"],
    "Teacher Sophia": ["Filipino", "Social Science", "Soc.Sci"],
    "Teacher Jhelyn": ["Math", "General Mathematics", "Gen Math", "Gen Math/HR"],
    "Teacher Jayra": ["English", "GMRC", "ESP", "Values Ed."],
    "Teacher Nadzra": ["Filipino", "EC"],
    "Teacher Ethel": ["Math", "MIL", "UCSP", "CPAR", "Entrepreneurship"],
    "Teacher Aniah": ["Science", "General Physics 1", "General Physics 2", "Practical Research 2", "3 I's", "Research/Capstone", "Sci", "Gen. Physics 1", "Prac. Res. 2"],
    "Teacher Norhaima": ["English", "LCS"],
    "Teacher Nof": ["ESP", "21st Century Literature", "Pagsulat sa Filipino", "EAPP", "21st Lit.", "Filipino", "Values Ed."],
    "Sir Moh": ["MAPEH", "PE 12"],
    "Teacher Rowena": ["Science", "General Science", "General Biology 1", "General Biology 2", "Gen Science", "Sci", "Gen Bio 1"],
    "Teacher Wardah": ["Values Education", "Values Ed.", "ESP"]
}

FACULTY_ISAL = {
    "Alim Mamonas": ["Arabic"],
    "Alim Bustamante": ["Arabic", "SHAF"],
    "Ustadha Silfah": ["Arabic", "GMRC"],
    "Alim Dipatuan": ["Qur'an"],
    "Ustadh Abdiraheem": ["SHAF"],
    "Ustadha Saliha": ["Hadith", "Arabic", "GMRC"],
    "Alim Samsuddin": ["SHAF"],
    "Ustadh Ali": ["Arabic"],
    "Teacher Hainur": ["Qur'an", "Hadith", "Arabic", "SHAF"],
    "Ustadh Jaisam": ["Qur'an"],
    "Ustadh Obaydah": ["Qur'an", "Arabic"],
    "Ustadh Faidh": ["Qur'an", "SHAF", "Arabic", "Hadith"],
    "Ustadh Ersahad": ["SHAF", "Arabic", "Math"],
    "Alim Abdul Karim": ["SHAF", "Arabic"],
    "Alim Abdulwahab": ["Qur'an"],
    "Ustadh Raslina": ["SHAF", "Arabic"],
    "Ustadh Muh Ali": ["Arabic"]
}

def norm(s):
    return str(s or '').lower().replace('.', ' ').replace(',', ' ').replace('-', ' ').strip()

def get_candidates(subject, grade):
    n_sub = norm(subject)
    is_elem = any(k in grade.lower() for k in ["kinder", "grade 1", "grade 2", "grade 3", "grade 4", "grade 5", "grade 6"])
    
    candidates = []
    if any(k in n_sub for k in ["qur'an", "quran", "arabic", "hadith", "shaf", "gmrc"]):
        for t, subs in FACULTY_ISAL.items():
            if any(norm(s) == n_sub or n_sub in norm(s) or norm(s) in n_sub for s in subs):
                if t not in candidates: candidates.append(t)
                
    if is_elem:
        for t, subs in FACULTY_ELEMENTARY.items():
            if any(norm(s) == n_sub or n_sub in norm(s) or norm(s) in n_sub for s in subs):
                if t not in candidates: candidates.append(t)
    else:
        for t, subs in FACULTY_HS.items():
            if any(norm(s) == n_sub or n_sub in norm(s) or norm(s) in n_sub for s in subs):
                if t not in candidates: candidates.append(t)

    if not candidates:
        for fac in [FACULTY_ISAL, FACULTY_ELEMENTARY, FACULTY_HS]:
            for t, subs in fac.items():
                if any(norm(s) == n_sub or n_sub in norm(s) or norm(s) in n_sub for s in subs):
                    if t not in candidates: candidates.append(t)
                    
    return candidates

def generate_perfect_term_schedule():
    with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'r') as f:
        existing_records = json.load(f)

    sec_map = {}
    for r in existing_records:
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
    print(f"Scheduling {len(sections)} sections across Kinder 1 to Grade 12...")

    EXAM_DAYS = [
        {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "1st Day"},
        {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "2nd Day"},
        {"dayNo": 3, "date": "2026-09-09", "dayName": "Wednesday", "examDay": "3rd Day"},
        {"dayNo": 4, "date": "2026-09-10", "dayName": "Thursday", "examDay": "4th Day"}
    ]

    ALL_DAY_SLOTS = [
        "7:40-8:25 a.m.", "8:25-9:05 a.m.", "9:05-9:45 a.m.",
        "12:40-01:20 p.m.", "01:30-02:10 p.m.", "02:20-03:00 p.m.",
        "3:40-4:20 p.m.", "4:30-5:10 p.m.", "5:20-6:00 p.m."
    ]

    TIME_SLOTS = {
        "F2F": ["7:40-8:25 a.m.", "8:25-9:05 a.m.", "9:05-9:45 a.m."],
        "ODL_1": ["12:40-01:20 p.m.", "01:30-02:10 p.m.", "02:20-03:00 p.m."],
        "ODL_2": ["3:40-4:20 p.m.", "4:30-5:10 p.m.", "5:20-6:00 p.m."]
    }

    best_records = None
    best_consecutives = 999

    for seed in range(500):
        random.seed(seed)
        final_records = []
        teacher_busy = defaultdict(set) # (date, time) -> set
        teacher_day_slots = defaultdict(set) # (teacher, date) -> set of global slot indices
        teacher_workload = defaultdict(int)
        section_last_teacher = {}
        consec_count = 0
        success = True

        # Subject assignment partitioned across 4 days
        sec_day_subjects = {}
        for s_idx, sec in enumerate(sections):
            sec_key = f"{sec['grade']}_{sec['section']}"
            req = list(CURRICULUM.get(sec['grade'], CURRICULUM["Grade 1"]))
            
            # Shuffle slightly
            offset = (s_idx * 7 + seed * 3) % len(req)
            rotated_req = req[offset:] + req[:offset]

            total = len(rotated_req)
            if total == 11: counts = [3, 3, 3, 2]
            elif total == 9: counts = [3, 2, 2, 2]
            elif total == 8: counts = [2, 2, 2, 2]
            elif total == 5: counts = [2, 1, 1, 1]
            else: counts = [2, 2, 2, 2]

            chunks = []
            ptr = 0
            for c in counts:
                chunks.append(rotated_req[ptr:ptr+c])
                ptr += c
            sec_day_subjects[sec_key] = chunks

        for day_idx, day_info in enumerate(EXAM_DAYS):
            d_date = day_info['date']

            for group_name, time_slots in TIME_SLOTS.items():
                if group_name == "F2F":
                    group_secs = [s for s in sections if s['modality'] == 'F2F']
                elif group_name == "ODL_1":
                    group_secs = [s for s in sections if s['modality'] == 'ODL' and '2nd' not in s['shift']]
                else:
                    group_secs = [s for s in sections if s['modality'] == 'ODL' and '2nd' in s['shift']]

                for slot_idx, slot_time in enumerate(time_slots):
                    global_slot_idx = ALL_DAY_SLOTS.index(slot_time)

                    active_secs = []
                    for sec in group_secs:
                        sec_key = f"{sec['grade']}_{sec['section']}"
                        day_subs = sec_day_subjects[sec_key][day_idx]
                        if slot_idx < len(day_subs):
                            active_secs.append((sec, day_subs[slot_idx]))

                    # Greedy assignment with strict no-consecutive rule
                    used_in_slot = set(teacher_busy[(d_date, slot_time)])
                    
                    # Sort active secs by MRV
                    items = []
                    for sec, sub in active_secs:
                        cands = get_candidates(sub, sec['grade'])
                        items.append({"sec": sec, "sub": sub, "cands": cands})
                    items.sort(key=lambda x: len(x['cands']))

                    slot_assignment = {}

                    for item in items:
                        sec = item['sec']
                        sub = item['sub']
                        sec_key = f"{sec['grade']}_{sec['section']}"
                        prev_sec_t = section_last_teacher.get((sec_key, d_date))

                        available = [t for t in item['cands'] if t not in used_in_slot]
                        if not available:
                            success = False
                            break

                        # Score each candidate:
                        # Priority 0: NOT in global_slot_idx - 1 today (anti-consecutive!)
                        # Priority 1: NOT in prev_sec_t
                        # Priority 2: Daily load <= 2
                        # Priority 3: Lowest overall workload
                        def score(t):
                            was_prev = 1 if (global_slot_idx - 1) in teacher_day_slots[(t, d_date)] else 0
                            was_next = 1 if (global_slot_idx + 1) in teacher_day_slots[(t, d_date)] else 0
                            same_sec = 1 if t == prev_sec_t else 0
                            day_load = len(teacher_day_slots[(t, d_date)])
                            tot_load = teacher_workload[t]
                            return (was_prev, was_next, same_sec, day_load, tot_load)

                        available.sort(key=score)
                        best_t = available[0]

                        if (global_slot_idx - 1) in teacher_day_slots[(best_t, d_date)]:
                            consec_count += 1

                        used_in_slot.add(best_t)
                        slot_assignment[sec_key] = best_t
                        teacher_day_slots[(best_t, d_date)].add(global_slot_idx)
                        teacher_workload[best_t] += 1
                        section_last_teacher[(sec_key, d_date)] = best_t

                        final_records.append({
                            "date": d_date,
                            "dayName": day_info['dayName'],
                            "examDay": day_info['examDay'],
                            "time": slot_time,
                            "grade": sec['grade'],
                            "section": sec['section'],
                            "gender": sec['gender'],
                            "modality": sec['modality'],
                            "shift": sec['shift'],
                            "subject": sub,
                            "teacher": best_t,
                            "room": sec.get('room', ''),
                            "proctor": best_t,
                            "remarks": "Term Examination"
                        })

                    if not success:
                        break
                if not success:
                    break
            if not success:
                break

        if success and len(final_records) == 602:
            if consec_count < best_consecutives:
                best_consecutives = consec_count
                best_records = final_records
                print(f"Seed {seed}: Total Consecutive Teacher Slots across entire 4 days = {best_consecutives}")
                if best_consecutives == 0:
                    print("Found PERFECT 0 CONSECUTIVE TEACHER SLOTS!")
                    break

    print(f"\nFinal Schedule Result: {best_consecutives} consecutive slots.")
    
    with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
        json.dump(best_records, f, indent=2, ensure_ascii=False)

    print("Master schedule saved to exam_data.json successfully!")

if __name__ == '__main__':
    generate_perfect_term_schedule()
