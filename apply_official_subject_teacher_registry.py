import json
import random
from collections import defaultdict

OFFICIAL_CURRICULUM_TEACHERS = {
    "Kinder 1": {
        "F2F": [
            ("Circle Time 1", ["Teacher Wendy"]),
            ("Circle Time 2", ["Teacher Wendy"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("Arabic", ["Ustadha Saliha"]),
            ("Hadith", ["Ustadha Saliha"])
        ],
        "ODL_1": [],
        "ODL_2": []
    },
    "Kinder 2": {
        "F2F": [
            ("Circle Time 1", ["Teacher Keychell"]),
            ("Circle Time 2", ["Teacher Keychell"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("Arabic", ["Ustadha Saliha"]),
            ("Hadith", ["Ustadha Saliha"])
        ],
        "ODL_1": [
            ("Circle Time 1", ["Teacher Joanna", "Teacher Ayah"]),
            ("Circle Time 2", ["Teacher Joanna", "Teacher Ayah"]),
            ("Qur'an", ["Teacher Hainur"]),
            ("Arabic", ["Ustadha Silfah"]),
            ("Hadith", ["Ustadha Saliha"])
        ],
        "ODL_2": [
            ("Circle Time 1", ["Teacher Keychell"]),
            ("Circle Time 2", ["Teacher Keychell"]),
            ("Qur'an", ["Ustadh Faidh"]),
            ("Arabic", ["Ustadha Silfah"]),
            ("Hadith", ["Ustadh Faidh"])
        ]
    },
    "Grade 1": {
        "F2F": [
            ("GMRC", ["Ustadha Saliha"]),
            ("Language", ["Teacher Sahdia"]),
            ("Reading and Literacy", ["Teacher Katrina"]),
            ("Math", ["Teacher Wendy"]),
            ("SHAF", ["Ustadh Abdiraheem"]),
            ("Makabansa", ["Teacher Norhydie"]),
            ("Arabic", ["Teacher Sahdia"]),
            ("Qur'an", ["Ustadh Obaydah"])
        ],
        "ODL_1": [
            ("GMRC", ["Teacher Sahdia", "Ustadha Saliha"]),
            ("Language", ["Teacher Sahdia"]),
            ("Reading and Literacy", ["Teacher Katrina"]),
            ("Math", ["Teacher Joanna"]),
            ("SHAF", ["Alim Abdul Karim"]),
            ("Makabansa", ["Teacher Norhydie"]),
            ("Arabic", ["Teacher Hainur"]),
            ("Qur'an", ["Teacher Hainur"])
        ],
        "ODL_2": [
            ("GMRC", ["Teacher Sahdia"]),
            ("Language", ["Teacher Sahdia"]),
            ("Reading and Literacy", ["Teacher Katrina"]),
            ("Math", ["Teacher Joanna"]),
            ("SHAF", ["Alim Abdul Karim"]),
            ("Makabansa", ["Teacher Norhydie"]),
            ("Arabic", ["Teacher Hainur"]),
            ("Qur'an", ["Teacher Hainur"])
        ]
    },
    "Grade 2": {
        "F2F": [
            ("GMRC", ["Ustadha Saliha"]),
            ("English", ["Teacher Marham"]),
            ("Filipino", ["Teacher Sitti Kauzar"]),
            ("Math", ["Teacher Sitti Kauzar"]),
            ("Arabic", ["Ustadh Obaydah"]),
            ("SHAF", ["Ustadh Ersahad"]),
            ("Makabansa", ["Teacher Monisa"]),
            ("Qur'an", ["Ustadh Obaydah"])
        ],
        "ODL_1": [
            ("GMRC", ["Ustadha Saliha"]),
            ("English", ["Teacher Marham"]),
            ("Filipino", ["Teacher Sitti Kauzar"]),
            ("Math", ["Teacher Sitti Kauzar"]),
            ("Arabic", ["Teacher Hainur"]),
            ("SHAF", ["Alim Abdul Karim"]),
            ("Makabansa", ["Teacher Zuhora", "Teacher Monisa"]),
            ("Qur'an", ["Ustadh Obaydah"])
        ],
        "ODL_2": [
            ("GMRC", ["Ustadha Saliha"]),
            ("English", ["Teacher Marham"]),
            ("Filipino", ["Teacher Zuhora", "Teacher Sitti Kauzar"]),
            ("Math", ["Teacher Sitti Kauzar"]),
            ("Arabic", ["Teacher Hainur"]),
            ("SHAF", ["Alim Abdul Karim"]),
            ("Makabansa", ["Teacher Monisa"]),
            ("Qur'an", ["Ustadh Obaydah"])
        ]
    },
    "Grade 3": {
        "F2F": [
            ("Science", ["Teacher Jerlyn"]),
            ("Math", ["Teacher Jerlyn"]),
            ("GMRC", ["Ustadha Saliha"]),
            ("Arabic", ["Ustadha Silfah"]),
            ("English", ["Teacher Marham"]),
            ("Makabansa", ["Teacher Wendy"]),
            ("Qur'an", ["Ustadh Obaydah"]),
            ("SHAF", ["Ustadh Ersahad"]),
            ("Filipino", ["Teacher Normylah"])
        ],
        "ODL_1": [
            ("Science", ["Teacher Jerlyn", "Teacher Saimonah"]),
            ("Math", ["Teacher Jerlyn"]),
            ("GMRC", ["Ustadha Silfah", "Teacher Zuhora"]),
            ("Arabic", ["Ustadha Silfah", "Ustadh Faidh"]),
            ("English", ["Teacher Marham", "Teacher Jenny"]),
            ("Makabansa", ["Teacher Zara", "Teacher Jenny"]),
            ("Qur'an", ["Ustadh Obaydah"]),
            ("SHAF", ["Alim Abdul Karim", "Ustadh Ersahad", "Ustadh Faidh"]),
            ("Filipino", ["Teacher Normylah", "Teacher Jenny"])
        ],
        "ODL_2": [
            ("Science", ["Teacher Jerlyn", "Teacher Saimonah"]),
            ("Math", ["Teacher Jerlyn"]),
            ("GMRC", ["Ustadha Silfah", "Ustadha Saliha"]),
            ("Arabic", ["Ustadha Silfah", "Ustadh Faidh"]),
            ("English", ["Teacher Marham", "Teacher Jenny"]),
            ("Makabansa", ["Teacher Zara", "Teacher Jenny"]),
            ("Qur'an", ["Ustadh Obaydah"]),
            ("SHAF", ["Ustadh Ersahad", "Ustadh Faidh"]),
            ("Filipino", ["Teacher Normylah", "Teacher Jenny"])
        ]
    },
    "Grade 4": {
        "F2F": [
            ("AP", ["Teacher Monisa"]),
            ("Math", ["Teacher Arvin"]),
            ("TLE", ["Teacher Monisa"]),
            ("GMRC", ["Teacher Sahdia"]),
            ("SHAF", ["Ustadh Abdiraheem"]),
            ("Arabic", ["Ustadh Ali"]),
            ("Qur'an", ["Ustadh Obaydah"]),
            ("MAPEH", ["Teacher Halnaisa"]),
            ("English", ["Teacher Norhydie"]),
            ("Science", ["Teacher Junaisah"]),
            ("Filipino", ["Teacher Norhydie"])
        ],
        "ODL_1": [
            ("AP", ["Teacher Monisa"]),
            ("Math", ["Teacher Saimonah", "Teacher Arvin"]),
            ("TLE", ["Teacher Jenny", "Teacher Monisa"]),
            ("GMRC", ["Teacher Sahdia"]),
            ("SHAF", ["Ustadh Abdiraheem"]),
            ("Arabic", ["Ustadh Ali"]),
            ("Qur'an", ["Ustadh Faidh", "Ustadh Obaydah"]),
            ("MAPEH", ["Teacher Zuhora", "Teacher Halnaisa"]),
            ("English", ["Teacher Jenny", "Teacher Arvin"]),
            ("Science", ["Teacher Saimonah", "Teacher Anna"]),
            ("Filipino", ["Teacher Zuhora", "Teacher Monisa"])
        ],
        "ODL_2": [
            ("AP", ["Teacher Monisa"]),
            ("Math", ["Teacher Arvin", "Teacher Saimonah"]),
            ("TLE", ["Teacher Monisa", "Teacher Jenny"]),
            ("GMRC", ["Teacher Sahdia"]),
            ("SHAF", ["Ustadh Abdiraheem"]),
            ("Arabic", ["Ustadh Ali"]),
            ("Qur'an", ["Ustadh Obaydah", "Ustadh Faidh"]),
            ("MAPEH", ["Teacher Halnaisa", "Teacher Zuhora"]),
            ("English", ["Teacher Arvin"]),
            ("Science", ["Teacher Anna", "Teacher Saimonah"]),
            ("Filipino", ["Teacher Norhydie", "Teacher Zuhora"])
        ]
    },
    "Grade 5": {
        "F2F": [
            ("SHAF", ["Ustadh Ersahad"]),
            ("AP", ["Teacher Norhydie"]),
            ("Filipino", ["Teacher Jessa"]),
            ("GMRC", ["Teacher Jayra"]),
            ("English", ["Teacher Jessa"]),
            ("Qur'an", ["Ustadh Obaydah"]),
            ("MAPEH", ["Teacher Keychell"]),
            ("Arabic", ["Ustadh Ersahad"]),
            ("Science", ["Teacher Junaisah"]),
            ("Math", ["Teacher Fhairudz"]),
            ("TLE", ["Teacher Halnaisa"])
        ],
        "ODL_1": [
            ("SHAF", ["Ustadh Raslina", "Ustadh Faidh"]),
            ("AP", ["Teacher Monisa", "Teacher Keychell", "Teacher Saimonah"]),
            ("Filipino", ["Teacher Joanna", "Teacher Jenny"]),
            ("GMRC", ["Teacher Jayra", "Ustadha Saliha"]),
            ("English", ["Teacher Jessa"]),
            ("Qur'an", ["Ustadh Jaisam", "Ustadh Obaydah"]),
            ("MAPEH", ["Teacher Keychell", "Teacher Saimonah"]),
            ("Arabic", ["Alim Abdul Karim", "Ustadh Faidh"]),
            ("Science", ["Teacher Anna", "Teacher Saimonah"]),
            ("Math", ["Teacher Hannah", "Teacher Saimonah"]),
            ("TLE", ["Teacher Anna", "Teacher Jenny"])
        ],
        "ODL_2": [
            ("SHAF", ["Teacher Hainur", "Ustadh Ersahad", "Ustadh Faidh"]),
            ("AP", ["Teacher Monisa", "Teacher Saimonah"]),
            ("Filipino", ["Teacher Joanna", "Teacher Jenny"]),
            ("GMRC", ["Teacher Jayra", "Ustadha Saliha"]),
            ("English", ["Teacher Jessa"]),
            ("Qur'an", ["Ustadh Jaisam", "Ustadh Obaydah"]),
            ("MAPEH", ["Teacher Norhydie", "Teacher Saimonah"]),
            ("Arabic", ["Ustadh Ersahad", "Ustadh Faidh"]),
            ("Science", ["Teacher Anna", "Teacher Saimonah"]),
            ("Math", ["Teacher Fhairudz", "Teacher Hannah", "Teacher Saimonah"]),
            ("TLE", ["Teacher Anna", "Teacher Jenny"])
        ]
    },
    "Grade 6": {
        "F2F": [
            ("AP", ["Teacher Zuhora"]),
            ("English", ["Teacher Jessa"]),
            ("Science", ["Teacher Wendy"]),
            ("Math", ["Ustadh Ersahad"]),
            ("GMRC", ["Ustadha Silfah"]),
            ("MAPEH", ["Teacher Zara"]),
            ("SHAF", ["Ustadh Abdiraheem"]),
            ("Qur'an", ["Ustadh Faidh"]),
            ("TLE", ["Teacher Arvin"]),
            ("Arabic", ["Ustadh Ali"]),
            ("Filipino", ["Teacher Normylah"])
        ],
        "ODL_1": [
            ("AP", ["Teacher Normylah"]),
            ("English", ["Teacher Jessa"]),
            ("Science", ["Teacher Anna"]),
            ("Math", ["Teacher Katrina"]),
            ("GMRC", ["Ustadha Silfah"]),
            ("MAPEH", ["Teacher Zara"]),
            ("SHAF", ["Ustadh Abdiraheem"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("TLE", ["Teacher Arvin"]),
            ("Arabic", ["Ustadh Ali"]),
            ("Filipino", ["Teacher Zuhora"])
        ],
        "ODL_2": [
            ("AP", ["Teacher Normylah"]),
            ("English", ["Teacher Jessa"]),
            ("Science", ["Teacher Anna", "Teacher Fhairudz"]),
            ("Math", ["Teacher Katrina", "Teacher Saimonah"]),
            ("GMRC", ["Ustadha Silfah"]),
            ("MAPEH", ["Teacher Zara", "Teacher Zuhora"]),
            ("SHAF", ["Ustadh Abdiraheem", "Ustadh Faidh"]),
            ("Qur'an", ["Ustadh Jaisam", "Ustadh Obaydah"]),
            ("TLE", ["Teacher Arvin"]),
            ("Arabic", ["Ustadh Ali", "Ustadh Ersahad"]),
            ("Filipino", ["Teacher Normylah"])
        ]
    },
    "Grade 7": {
        "F2F": [
            ("GMRC", ["Ustadha Silfah"]),
            ("Science", ["Teacher Radzmia"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("Arabic", ["Ustadh Muh Ali"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Math", ["Teacher Hannah"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("Filipino", ["Teacher Sophia"])
        ],
        "ODL_1": [
            ("GMRC", ["Ustadha Silfah"]),
            ("Science", ["Teacher Aniah"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("Arabic", ["Ustadh Ali"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Math", ["Teacher Ethel"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("Filipino", ["Teacher Sophia"])
        ],
        "ODL_2": [
            ("GMRC", ["Ustadha Silfah"]),
            ("Science", ["Teacher Aniah"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("Arabic", ["Ustadh Ali"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Math", ["Teacher Ethel"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("Filipino", ["Teacher Sophia"])
        ]
    },
    "Grade 7 & 8": {
        "F2F": [
            ("GMRC", ["Ustadha Silfah"]),
            ("Science", ["Teacher Radzmia"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("Arabic", ["Ustadh Muh Ali"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Math", ["Teacher Hannah"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("Filipino", ["Teacher Sophia"])
        ],
        "ODL_1": [],
        "ODL_2": []
    },
    "Grade 8": {
        "F2F": [
            ("GMRC", ["Ustadha Silfah"]),
            ("Science", ["Teacher Radzmia"]),
            ("Math", ["Teacher Hannah"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("Filipino", ["Teacher Sophia"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("Arabic", ["Ustadh Muh Ali"])
        ],
        "ODL_1": [
            ("Values Education", ["Teacher Wardah"]),
            ("Science", ["Teacher Radzmia"]),
            ("Math", ["Teacher Hannah"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("Filipino", ["Teacher Sophia"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("Arabic", ["Ustadh Ali"])
        ],
        "ODL_2": [
            ("Values Education", ["Teacher Wardah"]),
            ("Science", ["Teacher Radzmia"]),
            ("Math", ["Teacher Hannah"]),
            ("Social Science", ["Teacher Shirehan"]),
            ("MAPEH", ["Teacher Franchette"]),
            ("English", ["Teacher Jayra"]),
            ("Filipino", ["Teacher Sophia"]),
            ("TLE", ["Teacher Halnaisa"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Ustadh Jaisam"]),
            ("Arabic", ["Ustadh Ali"])
        ]
    },
    "Grade 9": {
        "F2F": [
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Alim Abdulwahab"]),
            ("Math", ["Teacher Jhelyn"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Arabic", ["Alim Mamonas"]),
            ("English", ["Teacher Norhaima"]),
            ("MAPEH", ["Sir Mohaymen"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"]),
            ("Filipino", ["Teacher Nadzra"])
        ],
        "ODL_1": [
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Alim Abdulwahab"]),
            ("Math", ["Teacher Jhelyn"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Arabic", ["Ustadh Raslina"]),
            ("English", ["Teacher Norhaima"]),
            ("MAPEH", ["Sir Mohaymen"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"]),
            ("Filipino", ["Teacher Nadzra"])
        ],
        "ODL_2": [
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Alim Abdulwahab"]),
            ("Math", ["Teacher Jhelyn"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Arabic", ["Ustadh Ali"]),
            ("English", ["Teacher Norhaima"]),
            ("MAPEH", ["Teacher Angeleni", "Sir Mohaymen"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"]),
            ("Filipino", ["Teacher Nadzra"])
        ]
    },
    "Grade 9 & 10": {
        "F2F": [
            ("SHAF", ["Alim Samsuddin"]),
            ("Qur'an", ["Alim Abdulwahab"]),
            ("Math", ["Teacher Jhelyn"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Arabic", ["Alim Mamonas"]),
            ("English", ["Teacher Norhaima"]),
            ("MAPEH", ["Sir Mohaymen"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"]),
            ("Filipino", ["Teacher Nadzra"])
        ],
        "ODL_1": [],
        "ODL_2": []
    },
    "Grade 10": {
        "F2F": [
            ("Qur'an", ["Alim Abdulwahab"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Arabic", ["Alim Mamonas"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("MAPEH", ["Sir Mohaymen"]),
            ("English", ["Teacher Norhaima"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Math", ["Teacher Jhelyn"]),
            ("Filipino", ["Teacher Nadzra"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"])
        ],
        "ODL_1": [
            ("Qur'an", ["Alim Abdulwahab"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Arabic", ["Alim Mamonas"]),
            ("SHAF", ["Alim Bustamante"]),
            ("MAPEH", ["Sir Mohaymen"]),
            ("English", ["Teacher Norhaima"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Math", ["Teacher Jhelyn"]),
            ("Filipino", ["Teacher Nadzra"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"])
        ],
        "ODL_2": [
            ("Qur'an", ["Alim Abdulwahab"]),
            ("TLE", ["Teacher Angeleni"]),
            ("Arabic", ["Alim Mamonas"]),
            ("SHAF", ["Alim Bustamante"]),
            ("MAPEH", ["Sir Mohaymen"]),
            ("English", ["Teacher Norhaima"]),
            ("Social Science", ["Teacher Sophia"]),
            ("Math", ["Teacher Jhelyn"]),
            ("Filipino", ["Teacher Nadzra"]),
            ("Science", ["Teacher Rowena"]),
            ("ESP", ["Teacher Nof"])
        ]
    },
    "Grade 11": {
        "F2F": [
            ("Arabic", ["Alim Mamonas"]),
            ("General Biology 1", ["Teacher Radzmia"]),
            ("Qur'an", ["Alim Dipatuan"]),
            ("General Mathematics", ["Teacher Jhelyn"]),
            ("EC", ["Teacher Nadzra"]),
            ("PSKP", ["Teacher Shirehan"]),
            ("LCS", ["Teacher Norhaima"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("General Science", ["Teacher Rowena"])
        ],
        "ODL_1": [
            ("Arabic", ["Alim Mamonas"]),
            ("General Biology 1", ["Teacher Rowena"]),
            ("Qur'an", ["Alim Abdulwahab"]),
            ("General Mathematics", ["Teacher Jhelyn"]),
            ("EC", ["Teacher Nadzra"]),
            ("PSKP", ["Teacher Shirehan"]),
            ("LCS", ["Teacher Norhaima"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("General Science", ["Teacher Rowena"])
        ],
        "ODL_2": [
            ("Arabic", ["Alim Mamonas"]),
            ("General Biology 1", ["Teacher Radzmia"]),
            ("Qur'an", ["Alim Abdulwahab"]),
            ("General Mathematics", ["Teacher Jhelyn"]),
            ("EC", ["Teacher Nadzra"]),
            ("PSKP", ["Teacher Shirehan"]),
            ("LCS", ["Teacher Norhaima"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("General Science", ["Teacher Rowena"])
        ]
    },
    "Grade 12": {
        "F2F": [
            ("General Physics 1", ["Teacher Aniah"]),
            ("General Biology 1", ["Teacher Radzmia"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Arabic", ["Alim Mamonas"]),
            ("Qur'an", ["Alim Dipatuan"]),
            ("21st Century Literature", ["Teacher Nof"]),
            ("Practical Research 2", ["Teacher Aniah"]),
            ("MIL", ["Teacher Ethel"]),
            ("PE 12", ["Sir Mohaymen"])
        ],
        "ODL_1": [
            ("General Physics 1", ["Teacher Aniah"]),
            ("General Biology 1", ["Teacher Radzmia"]),
            ("SHAF", ["Alim Samsuddin"]),
            ("Arabic", ["Alim Mamonas"]),
            ("Qur'an", ["Alim Dipatuan"]),
            ("21st Century Literature", ["Teacher Nof"]),
            ("Practical Research 2", ["Teacher Aniah"]),
            ("MIL", ["Teacher Ethel"]),
            ("PE 12", ["Sir Mohaymen"])
        ],
        "ODL_2": []
    }
}

def run_schedule_solver():
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
    print(f"Total Sections to Schedule: {len(sections)}")

    EXAM_DAYS = [
        {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "1st Day"},
        {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "2nd Day"},
        {"dayNo": 3, "date": "2026-09-09", "dayName": "Wednesday", "examDay": "3rd Day"},
        {"dayNo": 4, "date": "2026-09-10", "dayName": "Thursday", "examDay": "4th Day"}
    ]

    ALL_DAY_SLOTS = [
        "7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM",
        "12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM",
        "3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"
    ]

    TIME_SLOTS = {
        "F2F": ["7:40-8:25 AM", "8:25-9:05 AM", "9:05-9:45 AM"],
        "ODL_1": ["12:40-1:20 PM", "1:30-2:10 PM", "2:20-3:00 PM"],
        "ODL_2": ["3:40-4:20 PM", "4:30-5:10 PM", "5:20-6:00 PM"]
    }

    best_records = None
    best_consecutives = 999

    for seed in range(1000):
        random.seed(seed)
        final_records = []
        teacher_busy = defaultdict(set)
        teacher_day_slots = defaultdict(set)
        teacher_workload = defaultdict(int)
        section_last_teacher = {}
        consec_count = 0
        success = True

        sec_day_subjects = {}
        for s_idx, sec in enumerate(sections):
            sec_key = f"{sec['grade']}_{sec['section']}_{sec['modality']}_{sec['shift']}"
            m_key = "F2F" if sec['modality'] == 'F2F' else ("ODL_2" if '2nd' in sec['shift'] else "ODL_1")
            
            grade_dict = OFFICIAL_CURRICULUM_TEACHERS.get(sec['grade'], {})
            official_list = list(grade_dict.get(m_key, []))

            if not official_list:
                # If no schedule encoded for this shift (e.g. Kinder 1 ODL)
                sec_day_subjects[sec_key] = [[], [], [], []]
                continue

            # Rotate curriculum slightly across sections for balanced scheduling
            offset = (s_idx * 5 + seed * 2) % len(official_list)
            rotated_req = official_list[offset:] + official_list[:offset]

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
                        sec_key = f"{sec['grade']}_{sec['section']}_{sec['modality']}_{sec['shift']}"
                        day_subs = sec_day_subjects[sec_key][day_idx]
                        if slot_idx < len(day_subs):
                            sub_name, cands = day_subs[slot_idx]
                            active_secs.append((sec, sub_name, cands))

                    used_in_slot = set(teacher_busy[(d_date, slot_time)])
                    
                    # Sort by MRV (fewest candidate teachers first)
                    active_secs.sort(key=lambda x: len(x[2]))

                    for sec, sub, cands in active_secs:
                        sec_key = f"{sec['grade']}_{sec['section']}_{sec['modality']}_{sec['shift']}"
                        prev_sec_t = section_last_teacher.get((sec_key, d_date))

                        available = [t for t in cands if t not in used_in_slot]
                        if not available:
                            success = False
                            break

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

                    if not success: break
                if not success: break
            if not success: break

        if success and len(final_records) > 0:
            if consec_count < best_consecutives:
                best_consecutives = consec_count
                best_records = final_records
                print(f"Seed {seed}: Schedule Generated ({len(final_records)} exams) with {best_consecutives} consecutive teacher slots.")
                if best_consecutives == 0:
                    print("Found 100% PERFECT ZERO-CONSECUTIVE SCHEDULE with EXACT OFFICIAL TEACHERS!")
                    break

    print(f"\nFinal Schedule Result: {len(best_records)} exams, {best_consecutives} consecutive slots.")
    
    with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json', 'w', encoding='utf-8') as f:
        json.dump(best_records, f, indent=2, ensure_ascii=False)

    print("Master schedule saved to exam_data.json successfully!")

if __name__ == '__main__':
    run_schedule_solver()
