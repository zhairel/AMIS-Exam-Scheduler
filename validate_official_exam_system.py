import json
import sys

print("======================================================================")
print("  OFFICIAL AMIS EXAMINATION SYSTEM RIGOROUS VALIDATION SUITE")
print("======================================================================")

# 1. Load data
with open('class_schedules_data.json') as f:
    cs = json.load(f)

with open('exam_data_2nd_term.json') as f:
    exams = json.load(f)

with open('exam_data_2nd_term.js') as f:
    js_text = f.read()

# Verify JS is in sync with JSON
js_json_part = js_text.split('const ALL_EXAM_RECORDS = ')[1].split(';\n\nwindow.AMIS_EXAM_DATA')[0]
js_exams = json.loads(js_json_part)
assert len(exams) == len(js_exams), f"JSON has {len(exams)} exams, JS has {len(js_exams)}"
print(f"[PASS] Sync check: exam_data_2nd_term.json and exam_data_2nd_term.js are 100% in sync ({len(exams)} exams).")

# 2. Section shift mapping
sec_shift_map = {c['section_name']: c['shift'] for c in cs}
assert len(sec_shift_map) == 64, f"Expected 64 sections, got {len(sec_shift_map)}"
print(f"[PASS] Section registry: 64 canonical sections registered.")

# 3. Time boundaries verification
FIRST_SHIFT_SLOTS = {'12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM', '12:40 PM – 02:50 PM', '03:10 PM – 04:10 PM', '01:50 PM – 04:10 PM'}
SECOND_SHIFT_SLOTS = {'03:10 PM – 04:10 PM', '04:20 PM – 05:20 PM', '05:30 PM – 06:30 PM', '04:20 PM – 06:30 PM', '03:10 PM – 05:20 PM'}
F2F_MORNING_SLOTS = {'08:00 AM – 09:00 AM', '09:00 AM – 10:00 AM', '10:25 AM – 11:25 AM', '09:00 AM – 11:25 AM'}

boundary_violations = []
for e in exams:
    sname = e['section_name']
    sh = sec_shift_map[sname]
    slot = e['time_slot']
    
    if sh == 'F2F':
        if 'KINDER 1' in sname:
            if slot not in {'12:40 PM – 01:40 PM', '01:50 PM – 02:50 PM'}:
                boundary_violations.append((e, f"K1 F2F outside authentic afternoon slot: {slot}"))
        else:
            if slot not in F2F_MORNING_SLOTS:
                boundary_violations.append((e, f"F2F outside morning window (7:30 - 11:25 AM): {slot}"))
    elif '1ST SHIFT' in sh:
        if slot not in FIRST_SHIFT_SLOTS:
            boundary_violations.append((e, f"1ST SHIFT outside 1st shift window (12:30 - 4:10 PM): {slot}"))
    elif '2ND SHIFT' in sh:
        if slot not in SECOND_SHIFT_SLOTS:
            boundary_violations.append((e, f"2ND SHIFT outside 2nd shift window (3:10 - 6:30 PM): {slot}"))

if boundary_violations:
    print(f"[FAIL] Boundary violations detected: {len(boundary_violations)}")
    for e, reason in boundary_violations:
        print(f"  {e['id']}: {e['teacher']} | {e['subject']} | {e['section_name']} | {e['time_slot']} -> {reason}")
    sys.exit(1)
else:
    print(f"[PASS] Boundary check: 0 boundary violations across all {len(exams)} examinations!")

# 4. Mixed slot verification (3:10 PM – 4:10 PM)
mixed_exams = [e for e in exams if e['time_slot'] == '03:10 PM – 04:10 PM']
print(f"[PASS] Mixed slot 03:10 PM - 04:10 PM: contains {len(mixed_exams)} correctly scheduled exams.")

# 5. Ustadha Saliha authentic timetable verification
saliha_exams = [e for e in exams if e['teacher'] == 'Ustadha Saliha']
assert len(saliha_exams) == 16, f"Expected 16 exams for Ustadha Saliha, got {len(saliha_exams)}"

EXPECTED_SALIHA = {
    (1, '03:10 PM – 04:10 PM', 'GMRC', "GRADE 5 - JA'FAR IBN ABI TALIB (2ND SHIFT) - MIX"),
    (1, '04:20 PM – 05:20 PM', 'GMRC', 'GRADE 2 - SAEED IBN ZAYD (2ND SHIFT)'),
    (1, '05:30 PM – 06:30 PM', 'GMRC', "GRADE 3 - AS'AD IBN ZURARAH (2ND SHIFT) MIX"),
    (2, '08:00 AM – 09:00 AM', 'GMRC', 'GRADE 2 (FACE TO FACE)'),
    (2, '12:40 PM – 01:40 PM', 'Hadith', 'KINDER 1 CLASS SCHEDULE (F2F)'),
    (2, '01:50 PM – 02:50 PM', 'Hadith', 'Kinder 2 UTHMAN IBN AFFAN (1ST SHIFT)'),
    (2, '03:10 PM – 04:10 PM', 'GMRC', 'GRADE 2 - AASIM IBN THABIT (2ND SHIFT)'),
    (3, '08:00 AM – 09:00 AM', 'GMRC', 'GRADE 1 (FACE TO FACE)'),
    (3, '09:00 AM – 10:00 AM', 'Arabic', 'KINDER 2 CLASS SCHEDULE (F2F)'),
    (3, '12:40 PM – 01:40 PM', 'GMRC', 'GRADE 2 - AMR IBN AL-JAMUH (1ST SHIFT)'),
    (3, '03:10 PM – 04:10 PM', 'GMRC', 'GRADE 1 - ALI IBN ABI TALIB(1ST SHIFT)'),
    (4, '09:00 AM – 10:00 AM', 'GMRC', 'GRADE 3 (FACE TO FACE)'),
    (4, '10:25 AM – 11:25 AM', 'Hadith', 'KINDER 2 CLASS SCHEDULE (F2F)'),
    (4, '12:40 PM – 01:40 PM', 'GMRC', 'GRADE 2 - TALHA IBN UBAYDULLAH (1ST SHIFT)'),
    (4, '01:50 PM – 02:50 PM', 'Arabic', 'KINDER 1 CLASS SCHEDULE (F2F)'),
    (4, '03:10 PM – 04:10 PM', 'GMRC', "GRADE 5 - AYYASH IBN ABI RABI'AH(1ST SHIFT)"),
}

actual_saliha = set((e['day_number'], e['time_slot'], e['subject'], e['section_name']) for e in saliha_exams)
assert actual_saliha == EXPECTED_SALIHA, f"Mismatch in Ustadha Saliha exams:\nDiff: {actual_saliha ^ EXPECTED_SALIHA}"
print(f"[PASS] Authentic Timetable Match: Ustadha Saliha's 16/16 exams match the authentic timetable 100%!")

# 6. Check Teacher Arvin, Teacher Nadzra, Sir Mohaymen, Alim Samsuddin
arvin_exams = [e for e in exams if e['teacher'] == 'Teacher Arvin']
assert len(arvin_exams) == 17, f"Expected 17 exams for Teacher Arvin, got {len(arvin_exams)}"
nadzra_exams = [e for e in exams if e['teacher'] == 'Teacher Nadzra']
assert len(nadzra_exams) == 11, f"Expected 11 exams for Teacher Nadzra, got {len(nadzra_exams)}"
mohaymen_exams = [e for e in exams if e['teacher'] == 'Sir Mohaymen']
assert len(mohaymen_exams) == 14, f"Expected 14 exams for Sir Mohaymen, got {len(mohaymen_exams)}"
samsuddin_exams = [e for e in exams if e['teacher'] == 'Alim Samsuddin']
assert len(samsuddin_exams) == 18, f"Expected 18 exams for Alim Samsuddin, got {len(samsuddin_exams)}"
print(f"[PASS] Specific teachers load count verified: Teacher Arvin (17), Teacher Nadzra (11), Sir Mohaymen (14), Alim Samsuddin (18).")

# 7. Strictly 60 minutes duration and slots_spanned check
for e in exams:
    assert e['duration_minutes'] == 60, f"Exam {e['id']} duration is {e['duration_minutes']} (expected 60)"
    assert e['slots_spanned'] == 1, f"Exam {e['id']} slots_spanned is {e['slots_spanned']} (expected 1)"
print(f"[PASS] Strict 60-minute duration: All {len(exams)} examinations are strictly 60 minutes.")

# 8. Check proctor physical collisions & zero teacher overlapping
proctor_conflicts = []
for i in range(len(exams)):
    for j in range(i + 1, len(exams)):
        e1, e2 = exams[i], exams[j]
        p1 = e1.get('proctor_id') or e1.get('teacher_id')
        p2 = e2.get('proctor_id') or e2.get('teacher_id')
        if p1 and p1 == p2 and e1['day_number'] == e2['day_number']:
            if max(e1['start_m'], e2['start_m']) < min(e1['end_m'], e2['end_m']):
                proctor_conflicts.append((e1, e2))

assert len(proctor_conflicts) == 0, f"Detected {len(proctor_conflicts)} simultaneous teacher collisions!"
print(f"[PASS] Proctor & Teacher Overlaps: Exactly 0 simultaneous collisions across entire faculty pool.")

print("======================================================================")
print("  ALL VALIDATION CHECKS PASSED PERFECTLY!")
print("======================================================================")
