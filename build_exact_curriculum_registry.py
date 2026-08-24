# Verify and construct the exact official curriculum dictionary from the user prompt

OFFICIAL_FACULTY_ASSIGNMENTS = {
    "Teacher Wendy": [
        ("Circle Time 1", ["Kinder 1 F2F", "Kinder 1 ODL_2"]),
        ("Circle Time 2", ["Kinder 1 F2F", "Kinder 1 ODL_2"]),
        ("Math", ["Grade 1 F2F"]),
        ("Makabansa", ["Grade 3 F2F"]),
        ("Science", ["Grade 6 F2F"]),
    ],
    "Teacher Katrina": [
        ("Reading and Literacy", ["Grade 1 F2F", "Grade 1 ODL_1", "Grade 1 ODL_2"]),
        ("Math", ["Grade 6 ODL_1", "Grade 6 ODL_2"]),
    ],
    "Teacher Norhydie": [
        ("Makabansa", ["Grade 1 F2F", "Grade 1 ODL_1", "Grade 1 ODL_2"]),
        ("Filipino", ["Grade 4 F2F", "Grade 4 ODL_2"]),
        ("English", ["Grade 4 F2F"]),
        ("AP", ["Grade 5 F2F"]),
        ("MAPEH", ["Grade 5 ODL_2"]),
    ],
    "Teacher Jerlyn": [
        ("Science", ["Grade 3 F2F", "Grade 3 ODL_1", "Grade 3 ODL_2"]),
        ("Math", ["Grade 3 F2F", "Grade 3 ODL_1", "Grade 3 ODL_2"]),
    ],
    "Teacher Sahdia": [
        ("Language", ["Grade 1 F2F", "Grade 1 ODL_1", "Grade 1 ODL_2"]),
        ("Arabic", ["Grade 1 F2F"]),
        ("GMRC", ["Grade 4 F2F", "Grade 1 ODL_1", "Grade 4 ODL_1", "Grade 1 ODL_2", "Grade 4 ODL_2"]),
    ],
    "Teacher Sitti Kauzar": [
        ("Math", ["Grade 2 F2F", "Grade 2 ODL_1", "Grade 2 ODL_2"]),
        ("Filipino", ["Grade 2 F2F", "Grade 2 ODL_1", "Grade 2 ODL_2"]),
    ],
    "Teacher Arvin": [
        ("Math", ["Grade 4 F2F", "Grade 4 ODL_1", "Grade 4 ODL_2"]),
        ("TLE", ["Grade 6 F2F", "Grade 6 ODL_1", "Grade 6 ODL_2"]),
        ("English", ["Grade 4 ODL_1", "Grade 4 ODL_2"]),
    ],
    "Teacher Ayah": [
        ("Circle Time 1", ["Kinder 2 ODL_1", "Kinder 2 ODL_2"]),
        ("Circle Time 2", ["Kinder 2 ODL_1", "Kinder 2 ODL_2"]),
    ],
    "Teacher Junaisah": [
        ("Science", ["Grade 4 F2F", "Grade 5 F2F"]),
    ],
    "Teacher Joanna": [
        ("Circle Time 1", ["Kinder 2 ODL_1", "Kinder 2 ODL_2"]),
        ("Circle Time 2", ["Kinder 2 ODL_1", "Kinder 2 ODL_2"]),
        ("Math", ["Grade 1 ODL_1", "Grade 1 ODL_2"]),
        ("Filipino", ["Grade 5 ODL_1", "Grade 5 ODL_2"]),
    ],
    "Teacher Marham": [
        ("English", ["Grade 2 F2F", "Grade 3 F2F", "Grade 2 ODL_1", "Grade 3 ODL_1", "Grade 2 ODL_2", "Grade 3 ODL_2"]),
    ],
    "Teacher Saimonah": [
        ("Science", ["Grade 3 ODL_1"]),
        ("Math", ["Grade 4 ODL_2", "Grade 5 ODL_2", "Grade 6 ODL_2"]),
        ("MAPEH", ["Grade 5 ODL_2"]),
        ("AP", ["Grade 5 ODL_2"]),
    ],
    "Teacher Jessa": [
        ("English", ["Grade 5 F2F", "Grade 6 F2F", "Grade 5 ODL_1", "Grade 6 ODL_1", "Grade 5 ODL_2", "Grade 6 ODL_2"]),
        ("Filipino", ["Grade 5 F2F"]),
    ],
    "Teacher Anna": [
        ("Science", ["Grade 4 ODL_1", "Grade 5 ODL_1", "Grade 6 ODL_1", "Grade 4 ODL_2", "Grade 5 ODL_2", "Grade 6 ODL_2"]),
        ("TLE", ["Grade 5 ODL_1", "Grade 5 ODL_2"]),
    ],
    "Teacher Zuhora": [
        ("AP", ["Grade 6 F2F"]),
        ("Makabansa", ["Grade 2 ODL_1"]),
        ("Filipino", ["Grade 6 ODL_1", "Grade 2 ODL_2", "Grade 4 ODL_2"]),
        ("GMRC", ["Grade 3 ODL_1"]),
        ("MAPEH", ["Grade 4 ODL_2", "Grade 6 ODL_2"]),
    ],
    "Teacher Monisa": [
        ("Makabansa", ["Grade 2 F2F", "Grade 2 ODL_1", "Grade 2 ODL_2"]),
        ("AP", ["Grade 4 F2F", "Grade 4 ODL_1", "Grade 5 ODL_1", "Grade 4 ODL_2", "Grade 5 ODL_2"]),
        ("TLE", ["Grade 4 F2F", "Grade 4 ODL_1", "Grade 4 ODL_2"]),
        ("Filipino", ["Grade 4 ODL_1"]),
    ],
    "Teacher Normylah": [
        ("Filipino", ["Grade 3 F2F", "Grade 6 F2F", "Grade 3 ODL_1", "Grade 3 ODL_2", "Grade 6 ODL_2"]),
        ("AP", ["Grade 6 ODL_1", "Grade 6 ODL_2"]),
    ],
    "Teacher Keychelle": [
        ("Circle Time 1", ["Kinder 2 F2F", "Kinder 2 ODL_2"]),
        ("Circle Time 2", ["Kinder 2 F2F", "Kinder 2 ODL_2"]),
        ("MAPEH", ["Grade 5 F2F", "Grade 5 ODL_1"]),
        ("AP", ["Grade 5 ODL_1"]),
    ],
    "Teacher Jenny": [
        ("English", ["Grade 3 ODL_1", "Grade 3 ODL_2"]),
        ("Filipino", ["Grade 3 ODL_1", "Grade 3 ODL_2", "Grade 5 ODL_2"]),
        ("Makabansa", ["Grade 3 ODL_1", "Grade 3 ODL_2"]),
        ("TLE", ["Grade 4 ODL_2", "Grade 5 ODL_2"]),
    ],
    "Teacher Hannah": [
        ("Math", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 5 ODL_1", "Grade 8 ODL_1", "Grade 5 ODL_2", "Grade 8 ODL_2"]),
    ],
    "Teacher Zara": [
        ("MAPEH", ["Grade 6 F2F", "Grade 6 ODL_1", "Grade 6 ODL_2"]),
        ("Makabansa", ["Grade 3 ODL_1", "Grade 3 ODL_2"]),
    ],
    "Teacher Fhairudz": [
        ("Math", ["Grade 5 F2F", "Grade 5 ODL_2"]),
        ("Science", ["Grade 6 ODL_2"]),
    ],
    "Teacher Radzmia": [
        ("Science", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 8 ODL_1", "Grade 8 ODL_2"]),
        ("General Biology 1", ["Grade 11 F2F", "Grade 12 F2F", "Grade 12 ODL_1", "Grade 11 ODL_2"]),
    ],
    "Teacher Halnaisa": [
        ("MAPEH", ["Grade 4 F2F", "Grade 4 ODL_1", "Grade 4 ODL_2"]),
        ("TLE", ["Grade 5 F2F", "Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 7 ODL_2", "Grade 8 ODL_2"]),
    ],
    "Teacher Shirehan": [
        ("Social Science", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 7 ODL_2", "Grade 8 ODL_2"]),
        ("PSKP", ["Grade 11 F2F", "Grade 11 ODL_1", "Grade 11 ODL_2"]),
    ],
    "Teacher Angeleni": [
        ("TLE", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("MAPEH", ["Grade 9 ODL_2"]),
    ],
    "Teacher Franchette": [
        ("MAPEH", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 7 ODL_2", "Grade 8 ODL_2"]),
    ],
    "Teacher Sophia": [
        ("Filipino", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 7 ODL_2", "Grade 8 ODL_2"]),
        ("Social Science", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
    ],
    "Teacher Jhelyn": [
        ("Math", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("General Mathematics", ["Grade 11 F2F", "Grade 11 ODL_1", "Grade 11 ODL_2"]),
    ],
    "Teacher Jayra": [
        ("GMRC", ["Grade 5 F2F", "Grade 5 ODL_1", "Grade 5 ODL_2"]),
        ("English", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 7 ODL_2", "Grade 8 ODL_2"]),
    ],
    "Teacher Nadzra": [
        ("Filipino", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("EC", ["Grade 11 F2F", "Grade 11 ODL_1", "Grade 11 ODL_2"]),
    ],
    "Teacher Ethel": [
        ("MIL", ["Grade 12 F2F", "Grade 12 ODL_1"]),
        ("Math", ["Grade 7 ODL_1", "Grade 7 ODL_2"]),
    ],
    "Teacher Aniah": [
        ("Practical Research 2", ["Grade 12 F2F", "Grade 12 ODL_1"]),
        ("General Physics 1", ["Grade 12 F2F", "Grade 12 ODL_1"]),
        ("Science", ["Grade 7 ODL_1", "Grade 7 ODL_2"]),
    ],
    "Teacher Norhaima": [
        ("English", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("LCS", ["Grade 11 F2F", "Grade 11 ODL_1", "Grade 11 ODL_2"]),
    ],
    "Teacher Nof": [
        ("ESP", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("21st Century Literature", ["Grade 12 F2F", "Grade 12 ODL_1"]),
    ],
    "Sir Mohaymen": [
        ("MAPEH", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("PE 12", ["Grade 12 F2F", "Grade 12 ODL_1"]),
    ],
    "Teacher Rowena": [
        ("Science", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2"]),
        ("General Science", ["Grade 11 F2F", "Grade 11 ODL_1", "Grade 11 ODL_2"]),
        ("General Biology 1", ["Grade 11 ODL_1"]),
    ],
    "Teacher Wardah": [
        ("Values Education", ["Grade 8 ODL_1", "Grade 8 ODL_2"]),
    ],
    "Alim Mamonas": [
        ("Arabic", ["Grade 9 F2F", "Grade 10 F2F", "Grade 11 F2F", "Grade 12 F2F", "Grade 9 & 10 F2F", "Grade 10 ODL_1", "Grade 11 ODL_1", "Grade 12 ODL_1", "Grade 10 ODL_2", "Grade 11 ODL_2"]),
    ],
    "Alim Bustamante": [
        ("Arabic", ["Kinder 1 ODL_2"]),
        ("SHAF", ["Grade 10 ODL_1", "Grade 10 ODL_2"]),
    ],
    "Ustadha Silfah": [
        ("Arabic", ["Grade 3 F2F", "Kinder 2 ODL_1", "Grade 3 ODL_1", "Kinder 2 ODL_2", "Grade 3 ODL_2"]),
        ("GMRC", ["Grade 6 F2F", "Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 3 ODL_1", "Grade 6 ODL_1", "Grade 7 ODL_1", "Grade 3 ODL_2", "Grade 6 ODL_2", "Grade 7 ODL_2"]),
    ],
    "Alim Dipatuan": [
        ("Qur'an", ["Grade 11 F2F", "Grade 12 F2F", "Grade 12 ODL_1"]),
    ],
    "Ustadh Abdiraheem": [
        ("SHAF", ["Grade 1 F2F", "Grade 4 F2F", "Grade 6 F2F", "Grade 4 ODL_1", "Grade 6 ODL_1", "Grade 4 ODL_2", "Grade 6 ODL_2"]),
    ],
    "Ustadha Saliha": [
        ("Hadith", ["Kinder 1 F2F", "Kinder 2 F2F", "Kinder 2 ODL_1"]),
        ("Arabic", ["Kinder 1 F2F", "Kinder 2 F2F"]),
        ("GMRC", ["Grade 1 F2F", "Grade 2 F2F", "Grade 3 F2F", "Grade 1 ODL_1", "Grade 2 ODL_1", "Grade 2 ODL_2", "Grade 5 ODL_2"]),
    ],
    "Alim Samsuddin": [
        ("SHAF", ["Grade 7 F2F", "Grade 8 F2F", "Grade 9 F2F", "Grade 10 F2F", "Grade 11 F2F", "Grade 12 F2F", "Grade 7 & 8 F2F", "Grade 9 & 10 F2F", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 9 ODL_1", "Grade 11 ODL_1", "Grade 12 ODL_1", "Grade 7 ODL_2", "Grade 8 ODL_2", "Grade 9 ODL_2", "Grade 11 ODL_2"]),
    ],
    "Ustadh Ali": [
        ("Arabic", ["Grade 4 F2F", "Grade 6 F2F", "Grade 4 ODL_1", "Grade 6 ODL_1", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 4 ODL_2", "Grade 6 ODL_2", "Grade 7 ODL_2", "Grade 8 ODL_2", "Grade 9 ODL_2"]),
    ],
    "Ustadha Hainur": [
        ("Qur'an", ["Kinder 2 ODL_1", "Grade 1 ODL_1", "Kinder 1 ODL_2", "Kinder 2 ODL_2", "Grade 1 ODL_2"]),
        ("Arabic", ["Grade 1 ODL_1", "Grade 2 ODL_1", "Grade 1 ODL_2", "Grade 2 ODL_2"]),
        ("Hadith", ["Kinder 1 ODL_2", "Kinder 2 ODL_2"]),
    ],
    "Ustadh Jaisam": [
        ("Qur'an", ["Kinder 1 F2F", "Kinder 2 F2F", "Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F", "Grade 5 ODL_1", "Grade 6 ODL_1", "Grade 7 ODL_1", "Grade 8 ODL_1", "Grade 5 ODL_2", "Grade 6 ODL_2", "Grade 7 ODL_2", "Grade 8 ODL_2"]),
    ],
    "Ustadh Obaydah": [
        ("Qur'an", ["Grade 1 F2F", "Grade 2 F2F", "Grade 3 F2F", "Grade 4 F2F", "Grade 5 F2F", "Grade 2 ODL_1", "Grade 3 ODL_1", "Grade 4 ODL_1", "Grade 2 ODL_2", "Grade 3 ODL_2", "Grade 4 ODL_2", "Grade 5 ODL_2", "Grade 6 ODL_2"]),
        ("Arabic", ["Grade 2 F2F"]),
    ],
    "Ustadh Faidh": [
        ("Qur'an", ["Grade 6 F2F", "Grade 4 ODL_2"]),
        ("SHAF", ["Grade 3 ODL_1", "Grade 3 ODL_2", "Grade 5 ODL_2", "Grade 6 ODL_2"]),
        ("Arabic", ["Grade 3 ODL_1", "Grade 5 ODL_2"]),
        ("Hadith", ["Kinder 2 ODL_2"]),
    ],
    "Ustadh Ersahad": [
        ("SHAF", ["Grade 2 F2F", "Grade 3 F2F", "Grade 5 F2F", "Grade 3 ODL_1", "Grade 3 ODL_2", "Grade 5 ODL_2"]),
        ("Arabic", ["Grade 5 F2F", "Grade 5 ODL_2", "Grade 6 ODL_2"]),
        ("Math", ["Grade 6 F2F"]),
    ],
    "Alim Abdul Karim": [
        ("SHAF", ["Grade 1 ODL_1", "Grade 2 ODL_1", "Grade 3 ODL_1", "Grade 1 ODL_2", "Grade 2 ODL_2"]),
        ("Arabic", ["Grade 5 ODL_1"]),
    ],
    "Alim Abdulwahab": [
        ("Qur'an", ["Grade 9 F2F", "Grade 10 F2F", "Grade 9 & 10 F2F", "Grade 9 ODL_1", "Grade 10 ODL_1", "Grade 11 ODL_1", "Grade 9 ODL_2", "Grade 10 ODL_2", "Grade 11 ODL_2"]),
    ],
    "Ustadh Raslina": [
        ("SHAF", ["Grade 5 ODL_1"]),
        ("Arabic", ["Grade 9 ODL_1"]),
    ],
    "Ustadh Muh Ali": [
        ("Arabic", ["Grade 7 F2F", "Grade 8 F2F", "Grade 7 & 8 F2F"]),
    ],
}

# Build curriculum map
from collections import defaultdict
CURRICULUM_TEACHERS = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

for teacher, subjects in OFFICIAL_FACULTY_ASSIGNMENTS.items():
    for sub, targets in subjects:
        for tgt in targets:
            parts = tgt.split(" ")
            # Check modality & shift
            if "ODL_2" in tgt:
                m_key = "ODL_2"
                grade = " ".join([p for p in parts if p not in ["ODL_2", "ODL", "2nd", "Shift"]])
            elif "ODL_1" in tgt:
                m_key = "ODL_1"
                grade = " ".join([p for p in parts if p not in ["ODL_1", "ODL", "1st", "Shift"]])
            else:
                m_key = "F2F"
                grade = " ".join([p for p in parts if p not in ["F2F"]])
            
            grade = grade.strip()
            if teacher not in CURRICULUM_TEACHERS[grade][m_key][sub]:
                CURRICULUM_TEACHERS[grade][m_key][sub].append(teacher)

# Convert to ordered list of (subject, candidates) per grade and modality
FINAL_REGISTRY = {}
for grade, m_dict in CURRICULUM_TEACHERS.items():
    FINAL_REGISTRY[grade] = {}
    for m_key, s_dict in m_dict.items():
        FINAL_REGISTRY[grade][m_key] = [(sub, cands) for sub, cands in s_dict.items()]

import pprint
print("Generated Curricula:")
for g in sorted(FINAL_REGISTRY.keys()):
    print(f"Grade: {g}")
    for m, subs in FINAL_REGISTRY[g].items():
        print(f"  {m}: {len(subs)} subjects -> {[s[0] for s in subs]}")

with open("/home/tatsuya/Projects/AMIS/amis_exam_calendar/official_curriculum_registry.json", "w") as f:
    import json
    json.dump(FINAL_REGISTRY, f, indent=2)
