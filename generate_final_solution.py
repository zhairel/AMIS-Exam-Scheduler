import json
import re
from ortools.sat.python import cp_model

print("Starting full generation and optimization of AMIS 2nd Term Exam Schedule...")

# 1. Load existing exams and HTML
with open('exam_data_2nd_term.json') as f:
    exams = json.load(f)

with open('exam-schedule-2nd-term.html') as f:
    html_content = f.read()

m = re.search(r'const FACULTY_ROSTER_DATA = (\[.*?\]);', html_content, re.DOTALL)
if not m:
    raise ValueError("FACULTY_ROSTER_DATA not found in HTML!")
roster = json.loads(m.group(1))

# 2. Refine Grade 11 and Grade 2 assignments in roster
for t in roster:
    for a in t['assignments']:
        raw = a.get('raw', '')
        if 'Grade 11 2nd Shift' in raw or ('2nd Shift' in raw and '11' in raw):
            a['section'] = 'GRADE 11 (2ND SHIFT BOYS)'
            a['shift'] = 'ODL'
        elif 'ODL' in raw and '11' in raw:
            a['section'] = 'GRADE 11 (1ST SHIFT GIRLS)'
            a['shift'] = 'ODL'
        elif 'Aral Math 2 (F2F)' in raw:
            a['section'] = 'GRADE 2 (FACE TO FACE)'
            a['shift'] = 'F2F'
        elif 'Aral Reading 2 (F2F)' in raw:
            a['section'] = 'GRADE 2 (FACE TO FACE)'
            a['shift'] = 'F2F'

# 3. Refine exam metadata in exams
for e in exams:
    eid = e['id']
    if eid == 'exam_248':
        e['section_name'] = 'GRADE 11 (2ND SHIFT BOYS)'
        e['section'] = 'GRADE 11 (2ND SHIFT BOYS)'
        e['section_id'] = 'sec_grade_11_2nd_shift_boys'
        e['shift'] = 'ODL'
        e['modality'] = 'ODL'
        e['gender'] = 'MALE'
    elif eid in ['exam_281', 'exam_331', 'exam_356', 'exam_381', 'exam_412', 'exam_415', 'exam_474', 'exam_520']:
        e['section_name'] = 'GRADE 11 (1ST SHIFT GIRLS)'
        e['section'] = 'GRADE 11 (1ST SHIFT GIRLS)'
        e['section_id'] = 'sec_grade_11_1st_shift_girls'
        e['shift'] = 'ODL'
        e['modality'] = 'ODL'
        e['gender'] = 'FEMALE'
    elif eid in ['exam_283', 'exam_335', 'exam_359', 'exam_382', 'exam_417', 'exam_479', 'exam_518']:
        e['section_name'] = 'GRADE 11 (2ND SHIFT BOYS)'
        e['section'] = 'GRADE 11 (2ND SHIFT BOYS)'
        e['section_id'] = 'sec_grade_11_2nd_shift_boys'
        e['shift'] = 'ODL'
        e['modality'] = 'ODL'
        e['gender'] = 'MALE'
    elif eid in ['exam_103', 'exam_128']:
        e['section_name'] = 'GRADE 2 (FACE TO FACE)'
        e['section'] = 'GRADE 2 (FACE TO FACE)'
        e['section_id'] = 'sec_grade_2_face_to_face'
        e['grade'] = 'Grade 2'
        e['grade_level'] = 'Grade 2'
        e['shift'] = 'F2F'
        e['modality'] = 'F2F'
    elif eid == 'exam_466':
        e['shift'] = 'F2F'
        e['modality'] = 'F2F'

# 4. Discrete Time Periods definition
# 4 days * 8 periods = 32 slots
slots = [(d, p) for d in range(1, 5) for p in range(8)]
slot_metadata = [
    {'time_slot': '08:00 AM – 09:00 AM', 'start_m': 480, 'end_m': 540, 'slot_num': 1},
    {'time_slot': '09:00 AM – 10:00 AM', 'start_m': 540, 'end_m': 600, 'slot_num': 2},
    {'time_slot': '10:25 AM – 11:25 AM', 'start_m': 625, 'end_m': 685, 'slot_num': 3},
    {'time_slot': '12:40 PM – 01:40 PM', 'start_m': 760, 'end_m': 820, 'slot_num': 1},
    {'time_slot': '01:50 PM – 02:50 PM', 'start_m': 830, 'end_m': 890, 'slot_num': 2},
    {'time_slot': '03:10 PM – 04:10 PM', 'start_m': 910, 'end_m': 970, 'slot_num': 3},
    {'time_slot': '04:20 PM – 05:20 PM', 'start_m': 980, 'end_m': 1040, 'slot_num': 2},
    {'time_slot': '05:30 PM – 06:30 PM', 'start_m': 1050, 'end_m': 1110, 'slot_num': 3},
]

day_names = {
    1: ('Tuesday, December 1, 2026', 'Dec 1', 'Tuesday'),
    2: ('Wednesday, December 2, 2026', 'Dec 2', 'Wednesday'),
    3: ('Thursday, December 3, 2026', 'Dec 3', 'Thursday'),
    4: ('Sunday, December 6, 2026', 'Dec 6', 'Sunday'),
}

# 5. Build CP-SAT Model
model = cp_model.CpModel()
x = {}

for i in range(len(exams)):
    for s_idx in range(len(slots)):
        x[i, s_idx] = model.NewBoolVar(f'x_{i}_{s_idx}')
    model.AddExactlyOne([x[i, s_idx] for s_idx in range(len(slots))])

# Teacher no-overlap constraint
teachers = {}
for i, e in enumerate(exams):
    t = e.get('teacher_id') or e.get('subject_teacher_id') or e.get('proctor_id')
    if t:
        teachers.setdefault(t, []).append(i)

for t, exam_indices in teachers.items():
    for s_idx in range(len(slots)):
        model.Add(sum(x[i, s_idx] for i in exam_indices) <= 1)

# Cohort no-overlap constraint
cohorts = {}
for i, e in enumerate(exams):
    ckey = (
        e.get('grade_level'),
        e.get('modality'),
        e.get('section_id') or e.get('section_name'),
        str(e.get('gender') or 'NONE')
    )
    cohorts.setdefault(ckey, []).append(i)

for ckey, exam_indices in cohorts.items():
    for s_idx in range(len(slots)):
        model.Add(sum(x[i, s_idx] for i in exam_indices) <= 1)

# Pinned exams from user requests
pinned = {
    'exam_506': (1, 5), # Ustadha Saliha Saeed GMRC: Day 1, 03:10 PM – 04:10 PM
    'exam_505': (4, 5), # Ustadha Saliha Aasim GMRC: Day 4, 03:10 PM – 04:10 PM
    'exam_498': (4, 3), # Ustadha Saliha Talha GMRC: Day 4, 12:40 PM – 01:40 PM
    'exam_360': (1, 4), # Teacher Nadzra Abu Jandal: Day 1, 01:50 PM – 02:50 PM
    'exam_361': (4, 5), # Teacher Nadzra Abu Ayyub: Day 4, 03:10 PM – 04:10 PM
    'exam_362': (2, 5), # Teacher Nadzra Abu Dharr: Day 2, 03:10 PM – 04:10 PM
    'exam_357': (2, 4), # Teacher Nadzra Utbah: Day 2, 01:50 PM – 02:50 PM
    'exam_358': (4, 4), # Teacher Nadzra Abu Hurayrah: Day 4, 01:50 PM – 02:50 PM
    'exam_352': (3, 0), # Teacher Nadzra Homeroom: Day 3, 08:00 AM – 09:00 AM
    'exam_355': (1, 2), # Teacher Nadzra EC 11 F2F: Day 1, 10:25 AM – 11:25 AM
    'exam_354': (1, 1), # Teacher Nadzra Filipino 9&10 Girls: Day 1, 09:00 AM – 10:00 AM
    'exam_353': (4, 0), # Teacher Nadzra Filipino 9&10 Boys: Day 4, 08:00 AM – 09:00 AM
    'exam_405': (4, 5), # Sir Mohaymen PE 12: Day 4, 03:10 PM – 04:10 PM
}

for i, e in enumerate(exams):
    eid = e['id']
    if eid in pinned:
        target_d, target_p = pinned[eid]
        s_idx = (target_d - 1) * 8 + target_p
        model.Add(x[i, s_idx] == 1)

# Objective terms:
# 1. Heavily reward proper shift placement:
#    - F2F in morning (periods 0, 1, 2)
#    - 1st Shift in afternoon (periods 3, 4, 5)
#    - 2nd Shift in afternoon (periods 5, 6, 7)
#    - Kinder 1 F2F in periods 3, 4
# 2. Heavily penalize cross-shift violations (e.g. F2F at 5:30pm or 2nd shift at 8am)
# 3. Reward preserving current slot if already valid
obj_terms = []
slot_sms = [480, 540, 625, 760, 830, 910, 980, 1050]

for i, e in enumerate(exams):
    sec = e.get('section_name', '')
    shift = e.get('shift', '')
    glevel = e.get('grade_level', '')
    is_k1_f2f = 'kinder 1' in glevel.lower() and ('f2f' in sec.lower() or shift == 'F2F')
    is_f2f = ('f2f' in shift.upper() or 'face' in sec.lower()) and not is_k1_f2f
    is_2nd = '2nd' in sec.lower() or 'second' in sec.lower()
    is_1st = '1st' in sec.lower() or 'first' in sec.lower()

    curr_d = int(e.get('day_number', 0))
    curr_sm = int(e.get('start_m', 0))

    for s_idx, (d, p) in enumerate(slots):
        score = 0
        if is_k1_f2f:
            if p in {3, 4}: score += 100
            elif p in {0, 1, 2}: score -= 200
            else: score -= 300
        elif is_f2f:
            if p in {0, 1, 2}: score += 100
            elif p in {3, 4}: score += 20
            else: score -= 300
        elif is_2nd:
            if p in {5, 6, 7}: score += 100
            elif p in {3, 4}: score += 10
            else: score -= 300
        elif is_1st:
            if p in {3, 4, 5}: score += 100
            elif p in {6, 7}: score += 10
            else: score -= 300
        else:
            if p in {3, 4, 5, 6, 7}: score += 50

        if curr_d == d and slot_sms[p] == curr_sm:
            score += 15

        obj_terms.append(score * x[i, s_idx])

model.Maximize(sum(obj_terms))

# 6. Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
status = solver.Solve(model)

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    raise RuntimeError(f"Solver failed with status: {solver.StatusName(status)}")

print(f"Solver succeeded! Status: {solver.StatusName(status)}, Objective: {solver.ObjectiveValue()}")

# 7. Apply solution to all exam records
solved_exams = []
for i, e in enumerate(exams):
    rec = dict(e)
    for s_idx, (d, p) in enumerate(slots):
        if solver.Value(x[i, s_idx]) == 1:
            rec['day_number'] = d
            rec['date'] = day_names[d][0]
            rec['short_date'] = day_names[d][1]
            rec['day_name'] = day_names[d][2]
            meta = slot_metadata[p]
            rec['time_slot'] = meta['time_slot']
            rec['time'] = meta['time_slot']
            rec['start_m'] = meta['start_m']
            rec['end_m'] = meta['end_m']
            rec['duration_minutes'] = 60
            rec['slot_number'] = meta['slot_num']
            rec['slots_spanned'] = 1
            rec['start_slot_index'] = meta['slot_num'] - 1
            rec['end_slot_index'] = meta['slot_num'] - 1
            break
    solved_exams.append(rec)

# 8. Strict Verification
def active_teacher(e):
    return e.get('proctor_id') or e.get('teacher_id') or e.get('subject_teacher_id') or ''

def overlaps(l, r):
    return (int(l.get('day_number', 0)) == int(r.get('day_number', 0)) and
            int(l.get('start_m', 0)) < int(r.get('end_m', 0)) and
            int(r.get('start_m', 0)) < int(l.get('end_m', 0)))

conflicts = []
for i in range(len(solved_exams)):
    l = solved_exams[i]
    for j in range(i + 1, len(solved_exams)):
        r = solved_exams[j]
        if not overlaps(l, r): continue
        lt = active_teacher(l)
        rt = active_teacher(r)
        st = bool(lt and lt == rt)
        sc = (l.get('grade_level') == r.get('grade_level') and
              l.get('modality') == r.get('modality') and
              (l.get('section_id') or l.get('section_name')) == (r.get('section_id') or r.get('section_name')) and
              str(l.get('gender') or 'NONE') == str(r.get('gender') or 'NONE'))
        if st or sc:
            conflicts.append((l, r, st, sc))

print(f"VERIFICATION: Strict Conflicts Count = {len(conflicts)}")
if len(conflicts) > 0:
    for c in conflicts[:10]:
        print("  Conflict:", c[0]['id'], c[0]['teacher'], "vs", c[1]['id'], c[1]['teacher'])
    raise RuntimeError("Non-zero conflicts detected!")

# 9. Verify Teacher Load Audits
def clean_tokens(sec):
    if not sec: return []
    s = re.sub(r'\(.*?\)', ' ', sec.lower())
    s = re.sub(r'[^a-z0-9]', ' ', s)
    stop = set(['grade', 'class', 'schedule', 'shift', 'first', 'second', '1st', '2nd', 'f2f', 'face', 'to', 'mix', 'mixed', 'girls', 'boys', 'abu', 'ibn', 'bin', 'al', 'as', 'ar', 'ad', 'an', 'at', 'az', 'the', 'and'])
    return [w for w in s.split() if w not in stop and len(w) > 1]

def norm_sub(sub):
    if not sub: return ''
    s = sub.lower().strip()
    if 'panlipunan' in s or s == 'ap' or 'social science' in s or 'social studies' in s or 'kasaysayan' in s: return 'ap'
    if 'makabansa' in s: return 'makabansa'
    if 'aral math' in s: return 'aral_math'
    if 'aral reading' in s: return 'aral_reading'
    if 'aral science' in s: return 'aral_science'
    if 'aral program' in s or s == 'aral': return 'aral'
    if 'reading & literacy' in s or 'reading and literacy' in s or 'r & l' in s: return 'english'
    if 'english' in s: return 'english'
    if 'math' in s or 'gen math' in s: return 'math'
    if 'physics' in s: return 'physics'
    if 'bio' in s: return 'biology'
    if 'science' in s: return 'science'
    if 'filipino' in s or 'pagsulat' in s or 'pfpl' in s: return 'filipino'
    if 'pananaliksik' in s or 'pskp' in s: return 'pskp'
    if 'effective communication' in s or 'ec' in s or 'komunikasyon' in s: return 'ec'
    if 'cpar' in s: return 'cpar'
    if 'ucsp' in s: return 'ucsp'
    if 'lcs' in s or 'literature' in s: return 'lcs'
    if 'mapeh' in s or 'pe' in s or 'physical education' in s: return 'mapeh'
    if 'tle' in s or 'tvl' in s or 'entrepreneurship' in s: return 'tle'
    if 'gmrc' in s or 'values' in s or 'esp' in s: return 'gmrc'
    if 'arabic' in s: return 'arabic'
    if 'qur' in s: return 'quran'
    if 'hadith' in s: return 'hadith'
    if any(x in s for x in ['shaf', 'seerah', 'sirah', 'aqeedah', 'fiqh', 'tawheed']): return 'shaf'
    if 'circle time' in s or 'ct' in s or 'meeting time' in s or 'wrap' in s: return 'circle_time'
    if 'language' in s: return 'language'
    return s

missing_total = 0
for t in roster:
    t_exams = [e for e in solved_exams if (e.get('teacher_id') or e.get('subject_teacher_id')) == t['id']]
    assignments = t.get('assignments', [])
    for a in assignments:
        a_sub = norm_sub(a.get('subject') or a.get('raw'))
        a_tok = clean_tokens(a.get('section'))
        is_f2f = 'face' in (a.get('section') or '').lower() or (a.get('shift') or '').upper() == 'F2F' or 'f2f' in (a.get('raw') or '').lower()
        mg = re.search(r'\b(12|11|10|9|8|7|6|5|4|3|2|1)\b', a.get('section') or a.get('raw') or '')
        a_g = mg.group(1) if mg else ''
        a_b = 'boy' in (a.get('section') or a.get('raw') or '').lower()
        a_gi = 'girl' in (a.get('section') or a.get('raw') or '').lower()

        matched = None
        for e in t_exams:
            e_sub = norm_sub(e.get('subject'))
            e_tok = clean_tokens(e.get('section_name'))
            is_ef2f = 'face' in (e.get('section_name') or '').lower()
            emg = re.search(r'\b(12|11|10|9|8|7|6|5|4|3|2|1)\b', e.get('section_name') or '')
            e_g = emg.group(1) if emg else ''
            e_b = 'boy' in (e.get('section_name') or '').lower()
            e_gi = 'girl' in (e.get('section_name') or '').lower()
            gender_match = (not a_b and not a_gi) or (a_b and e_b) or (a_gi and e_gi)

            if a_sub == e_sub:
                if a.get('section') and e.get('section_name') and a['section'].strip().lower() == e['section_name'].strip().lower():
                    matched = e; break
                if is_f2f and is_ef2f and a_g and e_g and a_g == e_g and gender_match:
                    matched = e; break
                if a_tok and any(tok in e_tok for tok in a_tok) and gender_match:
                    matched = e; break
        if not matched:
            print(f"AUDIT ERROR: {t['name']} missing assignment: {a}")
            missing_total += 1

print(f"VERIFICATION: Missing loads across all 48 faculty = {missing_total}")
if missing_total > 0:
    raise RuntimeError("Missing loads detected!")

# 10. Write to exam_data_2nd_term.json and exam_data_2nd_term.js
with open('exam_data_2nd_term.json', 'w') as f:
    json.dump(solved_exams, f, indent=2)
print("Saved exam_data_2nd_term.json successfully.")

with open('exam_data_2nd_term.js', 'w') as f:
    f.write('const ALL_EXAM_RECORDS = ')
    json.dump(solved_exams, f, indent=2)
    f.write(';\n\nwindow.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n')
print("Saved exam_data_2nd_term.js successfully.")

# 11. Update FACULTY_ROSTER_DATA in exam-schedule-2nd-term.html
roster_json_str = json.dumps(roster, indent=2)
new_roster_decl = f"const FACULTY_ROSTER_DATA = {roster_json_str};"
pattern = r'const FACULTY_ROSTER_DATA = \[.*?\];'
html_content = re.sub(pattern, lambda m: new_roster_decl, html_content, flags=re.DOTALL)

with open('exam-schedule-2nd-term.html', 'w') as f:
    f.write(html_content)
print("Saved exam-schedule-2nd-term.html with updated FACULTY_ROSTER_DATA successfully.")
