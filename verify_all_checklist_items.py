import json
from collections import defaultdict

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'r', encoding='utf-8') as f:
    exams = json.load(f)

print(f"=== Loaded {len(exams)} Official Exam Sessions ===")

# 1. Dates Verification
dates_set = set(e['date'] for e in exams)
expected_dates = {
    'Wednesday, September 2, 2026',
    'Thursday, September 3, 2026',
    'Sunday, September 6, 2026',
    'Monday, September 7, 2026'
}
assert dates_set == expected_dates, f"Unexpected dates: {dates_set}"
print("✓ Item 1: Exam dates exactly: Sep 2, Sep 3, Sep 6, Sep 7 (PASS)")

# 2. Kindergarten 2 1st Shift Start Time
k2_1st = [e for e in exams if 'Kinder 2' in e['section_name'] and '1ST' in e['shift']]
k2_start_times = set(e['time_slot'].split('–')[0].strip() for e in k2_1st)
print("  K2 1st Shift start times:", k2_start_times)
assert all(not st.startswith('12:40') for st in k2_start_times), "K2 1st shift should not start at 12:40 PM!"
assert any(st.startswith('01:30') or st.startswith('1:30') for st in k2_start_times), "K2 1st shift must start at 01:30 PM!"
print("✓ Item 2: Kindergarten 2 1st Shift starts at 01:30 PM (PASS)")

# 3. Arabic - K2 Khabaab -> Ustadh Faidh
k2_khabaab_arabic = [e for e in exams if 'KHABAAB' in e['section_name'].upper() and e['subject'] == 'Arabic']
assert len(k2_khabaab_arabic) > 0, "K2 Khabaab Arabic not found"
for e in k2_khabaab_arabic:
    assert 'Faidh' in e['teacher'], f"Expected Ustadh Faidh, got {e['teacher']}"
print(f"✓ Item 3: Arabic — K2 Khabaab -> {k2_khabaab_arabic[0]['teacher']} (PASS)")

# 4. GMRC - Grade 3 As'ad -> Ustadha Saliha
asad_gmrc = [e for e in exams if ('AS\'AD' in e['section_name'].upper() or 'ASAD' in e['section_name'].upper()) and e['subject'] == 'GMRC']
assert len(asad_gmrc) > 0, "Grade 3 As'ad GMRC not found"
for e in asad_gmrc:
    assert 'Saliha' in e['teacher'], f"Expected Ustadha Saliha, got {e['teacher']}"
print(f"✓ Item 4: GMRC — Grade 3 As'ad -> {asad_gmrc[0]['teacher']} (PASS)")

# 5. Arabic - Grade 3 As'ad -> Ustadh Faidh
asad_arabic = [e for e in exams if ('AS\'AD' in e['section_name'].upper() or 'ASAD' in e['section_name'].upper()) and e['subject'] == 'Arabic']
assert len(asad_arabic) > 0, "Grade 3 As'ad Arabic not found"
for e in asad_arabic:
    assert 'Faidh' in e['teacher'], f"Expected Ustadh Faidh, got {e['teacher']}"
print(f"✓ Item 5: Arabic — Grade 3 As'ad -> {asad_arabic[0]['teacher']} (PASS)")

# 6. Math - Grade 6 Dihya -> Teacher Saimona
dihya_math = [e for e in exams if 'DIHYA' in e['section_name'].upper() and e['subject'] == 'Math']
assert len(dihya_math) > 0, "Grade 6 Dihya Math not found"
for e in dihya_math:
    assert 'Saimon' in e['teacher'], f"Expected Teacher Saimona, got {e['teacher']}"
print(f"✓ Item 6: Math — Grade 6 Dihya -> {dihya_math[0]['teacher']} (PASS)")

# 7. English - Grade 4 Usayd -> Teacher Jenny
usayd_eng = [e for e in exams if 'USAYD' in e['section_name'].upper() and e['subject'] == 'English']
assert len(usayd_eng) > 0, "Grade 4 Usayd English not found"
for e in usayd_eng:
    assert 'Jenny' in e['teacher'], f"Expected Teacher Jenny, got {e['teacher']}"
print(f"✓ Item 7: English — Grade 4 Usayd -> {usayd_eng[0]['teacher']} (PASS)")

# 8. SHAF - Grade 6 Dihya -> Ustadh Faidh
dihya_shaf = [e for e in exams if 'DIHYA' in e['section_name'].upper() and e['subject'] == 'SHAF']
assert len(dihya_shaf) > 0, "Grade 6 Dihya SHAF not found"
for e in dihya_shaf:
    assert 'Faidh' in e['teacher'], f"Expected Ustadh Faidh, got {e['teacher']}"
print(f"✓ Item 8: SHAF — Grade 6 Dihya -> {dihya_shaf[0]['teacher']} (PASS)")

# 9. HS Math = 120 min / 2 hours
hs_math = [e for e in exams if any(g in e['grade_level'] for g in ['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12']) and 'math' in e['subject'].lower()]
assert len(hs_math) == 19, f"Expected 19 HS Math items, got {len(hs_math)}"
assert all(e['duration_minutes'] == 120 for e in hs_math), "All HS Math items must have duration_minutes == 120"
assert all(e['slots_spanned'] == 2 for e in hs_math), "All HS Math items must span 2 slots"
print(f"✓ Item 9: HS Math = 120 min / 2 hours across {len(hs_math)} sections (PASS)")

# 10. Conflict Checker (Interval-Based)
# Section conflicts:
sec_day_exams = defaultdict(list)
for e in exams:
    sec_day_exams[(e['section_id'], e['day_number'])].append(e)

sec_conflicts = 0
for (sec_id, d), s_exams in sec_day_exams.items():
    for i in range(len(s_exams)):
        for j in range(i + 1, len(s_exams)):
            e1, e2 = s_exams[i], s_exams[j]
            # Check overlap between (start_m, end_m)
            if not (e1['end_m'] <= e2['start_m'] or e1['start_m'] >= e2['end_m']):
                print(f"Section conflict: {e1['section']} on Day {d}: {e1['subject']} ({e1['time_slot']}) vs {e2['subject']} ({e2['time_slot']})")
                sec_conflicts += 1

assert sec_conflicts == 0, f"Found {sec_conflicts} section conflicts!"
print("✓ Item 10a: Section Conflicts = 0 (PASS)")

# Teacher conflicts:
tchr_day_exams = defaultdict(list)
for e in exams:
    tid = e['teacher_id']
    if tid and tid != 'tchr_assigned_faculty':
        tchr_day_exams[(tid, e['day_number'])].append(e)

tchr_conflicts = 0
for (tid, d), t_exams in tchr_day_exams.items():
    for i in range(len(t_exams)):
        for j in range(i + 1, len(t_exams)):
            e1, e2 = t_exams[i], t_exams[j]
            is_merged = (e1['shift'] == e2['shift'] and 'ODL' in e1['shift'] and e1['subject_id'] == e2['subject_id'])
            if not (e1['end_m'] <= e2['start_m'] or e1['start_m'] >= e2['end_m']):
                if is_merged and e1['start_m'] == e2['start_m'] and e1['end_m'] == e2['end_m']:
                    continue # Synchronous allowed
                print(f"Teacher conflict: {e1['teacher']} on Day {d}: {e1['section']} {e1['subject']} ({e1['time_slot']}) vs {e2['section']} {e2['subject']} ({e2['time_slot']})")
                tchr_conflicts += 1

assert tchr_conflicts == 0, f"Found {tchr_conflicts} teacher conflicts!"
print("✓ Item 10b: Teacher Conflicts = 0 (PASS)")
print("\n>>> ALL 10 CHECKLIST REQUIREMENTS 100% VERIFIED AND PASSING WITH ZERO CONFLICTS! <<<")
