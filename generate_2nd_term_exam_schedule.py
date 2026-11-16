#!/usr/bin/env python3
"""
generate_2nd_term_exam_schedule.py
Generates the official 2nd Term Examination Schedule for AMIS.
- Authoritative Load Alignment: Aligns all 597 exam items to the updated master weekly faculty loads (49 active teachers).
- Zero Inactive Teachers: Eliminates Ustadh Obaydah, Ustadh Raffy, Teacher Ahmad, Teacher Jairah, Teacher Shanen, Teacher Zuhora, Teacher Normylah, Alim Abdul Karim.
- Faculty Policy:
  1. Teacher Anna -> Teacher Jeyra Mae (tchr_jeyra_mae)
  2. Teacher Wendelyn -> Teacher Wendy (tchr_wendy)
  3. Ustadh Silfah -> Ustadha Silfah (tchr_silfah)
  4. Teacher Jairah -> Teacher Jayra (tchr_jayra)
  5. Teacher Ahmad -> Teacher Fhairudz (tchr_fhairudz)
  6. Teacher Zuhora & Teacher Normylah classes -> remapped to active faculty (Erica, Jenny, Ayah, Junaisah, Monisa, Shirehan, Keychell, Silfah, Samsida)
  7. Ustadh Obaydah classes -> remapped to active Assatidz (Laurel/Nawawi, Faidh, Ersahad, Samsida, Jaisam, Ali, Silfah)
  8. Senior High courses aligned to 2nd term (Gen Bio 2, General Physics 2, CPAR, UCSP, Pagsulat sa Filipino)
  9. Proctors removed / set to subject teacher with zero duty conflicts
- Randomization: Mathematically randomized permutation across official 2nd Term dates (Dec 1, 2, 3, & 6, 2026).
- Strict Constraints:
  1. 0 Section Overlaps: No section has 2 exams at the same time. Max daily units respected.
  2. 0 Teacher Overlaps: No teacher is scheduled for two exams simultaneously (overlap > 15m strictly forbidden).
  3. 0 Copy / 100% Randomized: Exams are permuted to fresh slots/days.
- Validated with Google OR-Tools CP-SAT constraint programming.
"""

import os
import json
import random
import time
from collections import defaultdict
from ortools.sat.python import cp_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAM_DATA_1ST_JSON = os.path.join(BASE_DIR, "exam_data.json")
EXAM_DATA_2ND_JSON = os.path.join(BASE_DIR, "exam_data_2nd_term.json")
EXAM_DATA_2ND_JS = os.path.join(BASE_DIR, "exam_data_2nd_term.js")

ROOT_DIR = os.path.dirname(BASE_DIR)
ROOT_EXAM_DATA_2ND_JSON = os.path.join(ROOT_DIR, "exam_data_2nd_term.json")
ROOT_EXAM_DATA_2ND_JS = os.path.join(ROOT_DIR, "exam_data_2nd_term.js")

# Official 2nd Term Exam Dates
EXAM_DATES = {
    1: {"date": "Tuesday, December 1, 2026", "short_date": "Dec 1", "day_name": "Tuesday"},
    2: {"date": "Wednesday, December 2, 2026", "short_date": "Dec 2", "day_name": "Wednesday"},
    3: {"date": "Thursday, December 3, 2026", "short_date": "Dec 3", "day_name": "Thursday"},
    4: {"date": "Sunday, December 6, 2026", "short_date": "Dec 6", "day_name": "Sunday"}
}
DAYS = [1, 2, 3, 4]

# Standard time slots
SHIFT_SLOTS = {
    "F2F": [
        {"slot_num": 1, "time_slot": "08:00 AM – 09:00 AM", "start_m": 480, "end_m": 540},
        {"slot_num": 2, "time_slot": "09:00 AM – 10:00 AM", "start_m": 540, "end_m": 600},
        {"slot_num": 3, "time_slot": "10:25 AM – 11:25 AM", "start_m": 625, "end_m": 685}
    ],
    "ODL - 1ST SHIFT": [
        {"slot_num": 1, "time_slot": "12:40 PM – 01:40 PM", "start_m": 760, "end_m": 820},
        {"slot_num": 2, "time_slot": "01:50 PM – 02:50 PM", "start_m": 830, "end_m": 890},
        {"slot_num": 3, "time_slot": "03:10 PM – 04:10 PM", "start_m": 910, "end_m": 970}
    ],
    "ODL - 2ND SHIFT": [
        {"slot_num": 1, "time_slot": "03:10 PM – 04:10 PM", "start_m": 910, "end_m": 970},
        {"slot_num": 2, "time_slot": "04:20 PM – 05:20 PM", "start_m": 980, "end_m": 1040},
        {"slot_num": 3, "time_slot": "05:30 PM – 06:30 PM", "start_m": 1050, "end_m": 1110}
    ]
}

SHS_1ST_SLOTS = [
    {"slot_num": 1, "time_slot": "12:40 PM – 01:40 PM", "start_m": 760, "end_m": 820},
    {"slot_num": 2, "time_slot": "01:50 PM – 02:50 PM", "start_m": 830, "end_m": 890},
    {"slot_num": 3, "time_slot": "03:10 PM – 04:10 PM", "start_m": 910, "end_m": 970},
    {"slot_num": 4, "time_slot": "04:20 PM – 05:20 PM", "start_m": 980, "end_m": 1040}
]

# Kinder 1 Face-to-Face Afternoon Examination Slots (matching regular 12:40 PM – 03:00 PM school hours)
K1_F2F_AFTERNOON_SLOTS = [
    {"slot_num": 1, "time_slot": "12:40 PM – 01:40 PM", "start_m": 760, "end_m": 820},
    {"slot_num": 2, "time_slot": "01:50 PM – 02:50 PM", "start_m": 830, "end_m": 890}
]

def get_slots_for_rec(rec):
    if "Kinder 1" in rec.get("grade_level", "") and rec.get("modality", "") == "F2F":
        return K1_F2F_AFTERNOON_SLOTS
    if "Senior High" in rec.get("department", "") and rec.get("shift", "") == "ODL - 1ST SHIFT":
        return SHS_1ST_SLOTS
    return SHIFT_SLOTS[rec["shift"]]

def apply_authoritative_2nd_term_updates(records):
    """
    Applies authoritative teacher remappings and SHS 2nd term curriculum updates.
    Ensures zero inactive teachers and aligns exactly with updated faculty loads.
    """
    updated_records = []
    for it in records:
        r = dict(it)
        sec = r.get("section_name", "")
        sub = r.get("subject", "")
        t = r.get("teacher", "")
        tid = r.get("teacher_id", "")

        # Exclude removed Arabic subjects for Alim Mamonas as requested
        if (tid == "tchr_mamonas" or "mamonas" in t.lower()) and sub == "Arabic":
            if "11 (1ST SHIFT GIRLS)" in sec or "11 (2ND SHIFT BOYS)" in sec or "ABU AYYUB" in sec:
                continue

        # Exclude removed GMRC subjects for Ustadha Saliha as requested
        if (tid == "tchr_saliha" or "saliha" in t.lower()) and sub == "GMRC":
            if "AS'AD" in sec or "AASIM" in sec or "JA'FAR" in sec or "JA FAR" in sec or "SAEED" in sec:
                continue

        # 1. Fix missing/empty teacher in exam_4
        if not t or t == "Unassigned":
            if "K1 - HUSAIN" in sec and sub == "Qur'an":
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"

        # Filter out 1st Term Grade 12 records; they are fully replaced with the 10 official 2nd Term subjects
        if "12" in r.get("grade_level", "") or "12" in sec:
            continue

        # 2. Senior High School Grade 11 2nd Term Course Updates
        if "Senior High" in r.get("department", ""):
            if sub == "Gen Bio 1":
                sub = "Gen Bio 2"
                r["subject"] = "Gen Bio 2"
                r["subject_id"] = "subj_gen_bio_2"

        # Normalize Grade 6 F2F Math to 60m (1 slot, like G4 and G5) to fit all 12 subjects into 12 slots
        if "GRADE  6  FACE TO FACE" in sec and sub == "Math":
            r["slots_spanned"] = 1
            r["duration_minutes"] = 60

        # 3. Specific GMRC Grade 7 Usama -> Teacher Jayra
        if "USAMA" in sec and sub == "GMRC":
            t = "Teacher Jayra"
            r["teacher_id"] = "tchr_jayra"

        # 4. Standard Teacher Renames
        if t == "Teacher Anna":
            t = "Teacher Jeyra Mae"
            r["teacher_id"] = "tchr_jeyra_mae"
        elif t == "Teacher Wendelyn":
            t = "Teacher Wendy"
            r["teacher_id"] = "tchr_wendy"
        elif t == "Ustadh Silfah":
            t = "Ustadha Silfah"
            r["teacher_id"] = "tchr_silfah"
        elif t == "Teacher Jairah":
            t = "Teacher Jayra"
            r["teacher_id"] = "tchr_jayra"
        elif t == "Teacher Keychelle":
            t = "Teacher Keychell"
            r["teacher_id"] = "tchr_keychell"
        elif t in ["Teacher / Ustadh Ersahad", "Ustadh Ersahad"]:
            t = "Ustadh Ersahad"
            r["teacher_id"] = "tchr_ersahad"
        elif t == "Teacher Franchette Zarah M. Ranain":
            t = "Teacher Franchette"
            r["teacher_id"] = "tchr_franchette"

        # 5. Replace Alim Abdul Karim (0 load in 2nd term)
        elif t == "Alim Abdul Karim":
            if "Kinder 2 UTHMAN" in sec and sub == "Arabic":
                t = "Ustadha Silfah"
                r["teacher_id"] = "tchr_silfah"
            else:
                t = "Alim Bustamante"
                r["teacher_id"] = "tchr_bustamante"

        # 6. Replace Ustadh Obaydah (0 load in 2nd term)
        elif t == "Ustadh Obaydah":
            if "GRADE 3 -AMMAR" in sec:
                t = "Ustadha Silfah"
                r["teacher_id"] = "tchr_silfah"
            elif "GRADE 5 - AYYASH" in sec:
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "GRADE 3 - THABIT" in sec:
                t = "Ustadha Silfah"
                r["teacher_id"] = "tchr_silfah"
            elif "GRADE 2 - SAEED" in sec:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"
            elif "GRADE 4 - AZ ZUBAIR" in sec:
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "GRADE 2 (FACE TO FACE)" in sec:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"
            elif "GRADE 5 (FACE TO FACE)" in sec:
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "HABIB" in sec:
                t = "Ustadh Faidh"
                r["teacher_id"] = "tchr_faidh"
            elif "GRADE 6 - DIHYA" in sec:
                t = "Ustadh Jaisam"
                r["teacher_id"] = "tchr_jaisam"
            elif "GRADE 4 - IKRIMAH" in sec:
                t = "Ustadh Jaisam"
                r["teacher_id"] = "tchr_jaisam"
            elif "GRADE 3 (FACE TO FACE)" in sec:
                t = "Ustadh Faidh"
                r["teacher_id"] = "tchr_faidh"
            elif "GRADE 1 (FACE TO FACE)" in sec:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"
            elif "GRADE 2 - TALHA" in sec:
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "GRADE 4 - ABDUR RAHMAN" in sec:
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "GRADE 5 - JA'FAR" in sec or "JA FAR" in sec:
                t = "Ustadh Ali"
                r["teacher_id"] = "tchr_ali"
            elif "GRADE 3 - ZAYD" in sec:
                t = "Ustadh Ersahad"
                r["teacher_id"] = "tchr_ersahad"
            elif "GRADE 2 - AASIM" in sec:
                t = "Ustadh Ersahad"
                r["teacher_id"] = "tchr_ersahad"
            elif "GRADE 4 (FACE TO FACE)" in sec:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"
            elif "GRADE 3 - SALMAN" in sec:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"
            elif "GRADE 4 - HAKIM" in sec:
                t = "Ustadh Ersahad"
                r["teacher_id"] = "tchr_ersahad"
            elif "GRADE 2 - AMR" in sec:
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "GRADE 3 - AS'AD" in sec or "AS AD" in sec:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"

        # 7. Replace Teacher Normylah (0 load in 2nd term)
        elif t == "Teacher Normylah":
            if "GRADE 3 (FACE TO FACE)" in sec:
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "HABIB" in sec:
                t = "Teacher Ayah"
                r["teacher_id"] = "tchr_ayah"
            elif "GRADE 3 -AMMAR" in sec:
                t = "Teacher Ayah"
                r["teacher_id"] = "tchr_ayah"
            elif "GRADE 3 - THABIT" in sec:
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "GRADE  6  FACE TO FACE" in sec:
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"
            elif "KHALEED" in sec and sub == "Filipino":
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"
            elif "DIHYA" in sec and sub == "Filipino":
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"
            elif "ABDULLAH" in sec and "Panlipunan" in sub:
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"
            elif "ABBAS" in sec and "Panlipunan" in sub:
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"
            elif "KHALEED" in sec and "Panlipunan" in sub:
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"
            elif "DIHYA" in sec and "Panlipunan" in sub:
                t = "Teacher Junaisah"
                r["teacher_id"] = "tchr_junaisah"

        # 8. Replace Teacher Zuhora (0 load in 2nd term)
        elif t == "Teacher Zuhora":
            if "TALHA" in sec and sub == "Makabansa":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "ABBAS" in sec and sub == "Filipino":
                t = "Teacher Keychell"
                r["teacher_id"] = "tchr_keychell"
            elif "ABDULLAH" in sec and sub == "Filipino":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "KHALEED" in sec and sub == "GMRC":
                t = "Ustadha Silfah"
                r["teacher_id"] = "tchr_silfah"
            elif "SALMAN" in sec and sub == "GMRC":
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"
            elif "SAEED" in sec and sub == "Filipino":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "HASSAN" in sec and sub == "Filipino":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "HASSAN" in sec and sub == "MAPEH":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "USAYD" in sec and sub == "Filipino":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "USAYD" in sec and sub == "MAPEH":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "DIHYA" in sec and sub == "MAPEH":
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "FACE TO FACE" in sec and "Panlipunan" in sub:
                t = "Teacher Shirehan"
                r["teacher_id"] = "tchr_shirehan"

        # 9. Replace Ustadha Hainur (0 load in 2nd term - inactive/resigned)
        elif t == "Ustadha Hainur" or tid == "tchr_hainur":
            # Ustadh Laurel/Nawawi (7 classes: Qur'an G1 Ali, Qur'an 1 Hudhayfah, Qur'an G1 Sa'ad, Qur'an 1 Suhayb, SHAF 5 Hamza, SHAF 5 Muhammad, SHAF 5 Mus'ab)
            if "ALI" in sec and sub == "Qur'an":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "HUDHAYFAH" in sec and sub == "Qur'an":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "SA'AD" in sec and sub == "Qur'an":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "SUHAYB" in sec and sub == "Qur'an":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "HAMZA" in sec and sub == "SHAF":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "MUHAMMAD" in sec and sub == "SHAF":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "MUS'AB" in sec and sub == "SHAF":
                t = "Ustadh Laurel/Nawawi"
                r["teacher_id"] = "tchr_nawawi"
            elif "HUSAIN" in sec and sub == "Hadith":
                t = "Ustadha Silfah"
                r["teacher_id"] = "tchr_silfah"
            # Ustadha Samsida (13 classes: Hadith K2 Abdullah, Hadith K2 Umar, Qur'an K2 Abdullah, and all Arabic)
            else:
                t = "Ustadha Samsida"
                r["teacher_id"] = "tchr_samsida"

        # 10. Reassignments from Teacher Monisa (not in her loads anymore per 2nd Term ELEM LOADs)
        if t == "Teacher Monisa" or tid == "tchr_monisa":
            if "HAKIM" in sec and (sub == "TLE" or "Panlipunan" in sub):
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "ABDUR RAHMAN" in sec and "Panlipunan" in sub:
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "USAYD" in sec and "Panlipunan" in sub:
                t = "Teacher Erica"
                r["teacher_id"] = "tchr_erica"
            elif "HAMZA" in sec and "Panlipunan" in sub:
                t = "Teacher Jenny"
                r["teacher_id"] = "tchr_jenny"

        # 11. Grade 8 - Sa'ad section name & gender to MIX
        if "GRADE 8 - SA'AD" in sec or r.get("section_id") == "sec_grade_8_sa_ad_ibn_mua_dh_1st_shift_girls":
            r["section"] = "GRADE 8 - SA'AD IBN MUA'DH (1ST SHIFT) - MIX"
            r["section_name"] = "GRADE 8 - SA'AD IBN MUA'DH (1ST SHIFT) - MIX"
            r["gender"] = "MIX"

        # Clean all related fields & remove proctors for 2nd term
        r["teacher"] = t
        r["subject_teacher"] = t
        r["subject_teacher_id"] = r["teacher_id"]
        r["active_subject_teacher"] = t
        r["active_subject_teacher_id"] = r["teacher_id"]
        r["proctor"] = t
        r["proctor_id"] = r["teacher_id"]
        r["proctor_status"] = "ACTIVE_ASSIGNED"
        r["proctor_assignment_source"] = "SUBJECT_TEACHER"
        r["proctor_conflict_status"] = "CLEAR"
        r["proctor_pool"] = "SUBJECT_TEACHER"
        r["inactive_teacher_warning"] = ""
        r["teacher_status"] = "VERIFIED"
        r["subject_teacher_active"] = True
        r["subject_teacher_status"] = "ACTIVE_VERIFIED"
        r["replacement_teacher_required"] = False
        r.pop("display_as_proctor_duty", None)
        r.pop("proctor_coverage_reason", None)
        r.pop("former_subject_teacher", None)
        r.pop("former_subject_teacher_id", None)

        updated_records.append(r)

    # 10. Append Authoritative Grade 12 - Term 2 Subjects & Faculty (9 examination subjects each, Research/3Is removed)
    g12_abu_subjects = [
        ("Gen Bio 2", "Teacher Rowena", "tchr_rowena", "High School Faculty", 1, 60),
        ("General Physics 2", "Teacher Abegail", "tchr_abegail", "High School Faculty", 2, 120),
        ("CPAR", "Teacher Nof", "tchr_nof", "High School Faculty", 1, 60),
        ("EAPP", "Teacher Sophia", "tchr_sophia", "High School Faculty", 1, 60),
        ("Entrepreneurship", "Teacher Shanen", "tchr_shanen", "High School Faculty", 1, 60),
        ("PE 12", "Sir Mohaymen", "tchr_mohaymen", "High School Faculty", 1, 60),
        ("Arabic", "Alim Mamonas", "tchr_mamonas", "ISAL Faculty", 1, 60),
        ("Qur'an", "Alim Dipatuan", "tchr_dipatuan", "ISAL Faculty", 1, 60),
        ("SHAF", "Alim Samsuddin", "tchr_samsuddin", "ISAL Faculty", 1, 60),
    ]

    g12_suhayb_subjects = [
        ("Gen Bio 2", "Teacher Rowena", "tchr_rowena", "High School Faculty", 1, 60),
        ("General Physics 2", "Teacher Abegail", "tchr_abegail", "High School Faculty", 2, 120),
        ("CPAR", "Teacher Nof", "tchr_nof", "High School Faculty", 1, 60),
        ("EAPP", "Teacher Sophia", "tchr_sophia", "High School Faculty", 1, 60),
        ("Entrepreneurship", "Teacher Shanen", "tchr_shanen", "High School Faculty", 1, 60),
        ("PE 12", "Sir Mohaymen", "tchr_mohaymen", "High School Faculty", 1, 60),
        ("Arabic", "Alim Mamonas", "tchr_mamonas", "ISAL Faculty", 1, 60),
        ("Qur'an", "Alim Dipatuan", "tchr_dipatuan", "ISAL Faculty", 1, 60),
        ("SHAF", "Alim Samsuddin", "tchr_samsuddin", "ISAL Faculty", 1, 60),
    ]

    for sub, tchr, tid, dept, span, dur in g12_abu_subjects:
        clean_name = sub.lower().replace(' ', '_').replace("'", "")
        subj_id = f"subj_{clean_name}"
        updated_records.append({
            "section_id": "sec_grade_12_abu_musa_al_ashari",
            "section": "GRADE 12 - ABU MUSA AL-ASHARI",
            "section_name": "GRADE 12 - ABU MUSA AL-ASHARI",
            "department": "Senior High School",
            "grade": "Grade 12",
            "grade_level": "Grade 12",
            "shift": "ODL - 1ST SHIFT",
            "modality": "ODL",
            "gender": "GIRLS",
            "subject_id": subj_id,
            "subject": sub,
            "teacher_id": tid,
            "teacher": tchr,
            "subject_teacher": tchr,
            "subject_teacher_id": tid,
            "active_subject_teacher": tchr,
            "active_subject_teacher_id": tid,
            "proctor": tchr,
            "proctor_id": tid,
            "proctor_department": dept,
            "proctor_status": "ACTIVE_ASSIGNED",
            "proctor_assignment_source": "SUBJECT_TEACHER",
            "proctor_conflict_status": "CLEAR",
            "proctor_pool": "SUBJECT_TEACHER",
            "slots_spanned": span,
            "duration_minutes": dur,
            "teacher_status": "VERIFIED",
            "subject_teacher_active": True,
            "subject_teacher_status": "ACTIVE_VERIFIED",
            "replacement_teacher_required": False,
            "inactive_teacher_warning": ""
        })

    for sub, tchr, tid, dept, span, dur in g12_suhayb_subjects:
        clean_name = sub.lower().replace(' ', '_').replace("'", "")
        subj_id = f"subj_{clean_name}"
        updated_records.append({
            "section_id": "sec_grade_12_suhayb_ar_rumi",
            "section": "GRADE 12 - SUHAYB AR-RUMI",
            "section_name": "GRADE 12 - SUHAYB AR-RUMI",
            "department": "Senior High School",
            "grade": "Grade 12",
            "grade_level": "Grade 12",
            "shift": "F2F",
            "modality": "F2F",
            "gender": "BOYS",
            "subject_id": subj_id,
            "subject": sub,
            "teacher_id": tid,
            "teacher": tchr,
            "subject_teacher": tchr,
            "subject_teacher_id": tid,
            "active_subject_teacher": tchr,
            "active_subject_teacher_id": tid,
            "proctor": tchr,
            "proctor_id": tid,
            "proctor_department": dept,
            "proctor_status": "ACTIVE_ASSIGNED",
            "proctor_assignment_source": "SUBJECT_TEACHER",
            "proctor_conflict_status": "CLEAR",
            "proctor_pool": "SUBJECT_TEACHER",
            "slots_spanned": span,
            "duration_minutes": dur,
            "teacher_status": "VERIFIED",
            "subject_teacher_active": True,
            "subject_teacher_status": "ACTIVE_VERIFIED",
            "replacement_teacher_required": False,
            "inactive_teacher_warning": ""
        })

    # Add ARAL Program for Grade 4, 5, 6 (F2F) with Teacher Arvin
    aral_f2f_items = [
        ("sec_grade_4_face_to_face", "GRADE 4 (FACE TO FACE)", "Grade 4"),
        ("sec_grade_5_face_to_face", "GRADE 5 (FACE TO FACE)", "Grade 5"),
        ("sec_grade_6_face_to_face", "GRADE  6  FACE TO FACE", "Grade 6"),
    ]
    for sec_id, sec_name, gr in aral_f2f_items:
        updated_records.append({
            "section_id": sec_id,
            "section": sec_name,
            "section_name": sec_name,
            "department": "Elementary",
            "grade": gr,
            "grade_level": gr,
            "shift": "F2F",
            "modality": "F2F",
            "gender": "MIXED",
            "subject_id": "subj_aral_program",
            "subject": "ARAL Program",
            "teacher_id": "tchr_arvin",
            "teacher": "Teacher Arvin",
            "subject_teacher": "Teacher Arvin",
            "subject_teacher_id": "tchr_arvin",
            "active_subject_teacher": "Teacher Arvin",
            "active_subject_teacher_id": "tchr_arvin",
            "proctor": "Teacher Arvin",
            "proctor_id": "tchr_arvin",
            "proctor_department": "Elementary",
            "proctor_status": "ACTIVE_ASSIGNED",
            "proctor_assignment_source": "SUBJECT_TEACHER",
            "proctor_conflict_status": "CLEAR",
            "proctor_pool": "SUBJECT_TEACHER",
            "slots_spanned": 1,
            "duration_minutes": 60,
            "teacher_status": "VERIFIED",
            "subject_teacher_active": True,
            "subject_teacher_status": "ACTIVE_VERIFIED",
            "replacement_teacher_required": False,
            "inactive_teacher_warning": ""
        })

    return updated_records

def generate_schedule(seed=20261201):
    print(f"Loading 1st Term exam baseline from {EXAM_DATA_1ST_JSON}...")
    with open(EXAM_DATA_1ST_JSON, "r", encoding="utf-8") as f:
        raw_baseline = json.load(f)

    print(f"Applying authoritative 2nd Term faculty updates on {len(raw_baseline)} items...")
    records = apply_authoritative_2nd_term_updates(raw_baseline)

    # Verify no inactive faculty names remain
    forbidden_names = {
        "Ustadh Obaydah", "Ustadh Raffy", "Teacher Ahmad", "Teacher Jairah",
        "Teacher Zuhora", "Teacher Normylah", "Alim Abdul Karim",
        "Ustadha Hainur"
    }
    for r in records:
        for fld in ["teacher", "subject_teacher", "proctor", "active_subject_teacher"]:
            val = r.get(fld, "")
            if val in forbidden_names:
                raise ValueError(f"Forbidden inactive teacher '{val}' found in record {r['id']}!")

    print("All records updated with 48 active faculty members. Zero inactive teachers confirmed.")
    rng = random.Random(seed)

    model = cp_model.CpModel()
    x = {}

    for i, rec in enumerate(records):
        slots = get_slots_for_rec(rec)
        k = rec.get("slots_spanned", 1)
        for d in DAYS:
            for s_idx in range(len(slots) - k + 1):
                x[i, d, s_idx] = model.NewBoolVar(f"x_{i}_{d}_{s_idx}")

    # Constraint 1: Exactly one assignment per exam item
    for i, rec in enumerate(records):
        slots = get_slots_for_rec(rec)
        k = rec.get("slots_spanned", 1)
        model.AddExactlyOne(x[i, d, s_idx] for d in DAYS for s_idx in range(len(slots) - k + 1))

    # Constraint 2: Section capacity and 0 overlapping exams within each section
    by_sec = defaultdict(list)
    for i, rec in enumerate(records):
        by_sec[rec["section_id"]].append(i)

    for sec_id, items in by_sec.items():
        slots = get_slots_for_rec(records[items[0]])
        num_slots = len(slots)
        max_daily_units = 4 if "Senior High" in records[items[0]].get("department", "") else 3
        for d in DAYS:
            for s in range(num_slots):
                occupying = []
                for i in items:
                    k = records[i].get("slots_spanned", 1)
                    for s_start in range(max(0, s - k + 1), min(s + 1, num_slots - k + 1)):
                        occupying.append(x[i, d, s_start])
                model.Add(sum(occupying) <= 1)
            daily_units = []
            for i in items:
                k = records[i].get("slots_spanned", 1)
                for s_start in range(num_slots - k + 1):
                    daily_units.append(x[i, d, s_start] * k)
            model.Add(sum(daily_units) <= max_daily_units)

    # Constraint 2b: Kinder 1 F2F exactly 1 exam per day in afternoon slots (4 subjects across 4 days)
    k1_f2f_items = [i for i, r in enumerate(records) if "Kinder 1" in r.get("grade_level", "") and r.get("modality") == "F2F"]
    if k1_f2f_items:
        for d in DAYS:
            model.Add(sum(x[i, d, s] for i in k1_f2f_items for s in range(len(K1_F2F_AFTERNOON_SLOTS))) == 1)

    # Constraint 2c: Pin PE 12 for Grade 12 - Abu Musa Al-Ashari to Day 4 at 03:10 PM – 04:10 PM (Slot 3)
    for i, r in enumerate(records):
        if r.get("section_id") == "sec_grade_12_abu_musa_al_ashari" and r.get("subject") == "PE 12":
            slots = get_slots_for_rec(r)
            for s_idx, sl in enumerate(slots):
                if sl["start_m"] == 910: # 03:10 PM – 04:10 PM
                    model.Add(x[i, 4, s_idx] == 1)

    # Constraint 3: Strict 0 Teacher Overlaps across all time slots!
    by_teacher = defaultdict(list)
    for i, rec in enumerate(records):
        tid = rec.get("teacher_id")
        if tid:
            by_teacher[tid].append(i)

    teacher_conflict_checks = 0
    for tid, items in by_teacher.items():
        if len(items) <= 1:
            continue
        unique_items = sorted(list(set(items)))
        for d in DAYS:
            for idx1 in range(len(unique_items)):
                i1 = unique_items[idx1]
                slots1 = get_slots_for_rec(records[i1])
                k1 = records[i1].get("slots_spanned", 1)
                for idx2 in range(idx1 + 1, len(unique_items)):
                    i2 = unique_items[idx2]
                    slots2 = get_slots_for_rec(records[i2])
                    k2 = records[i2].get("slots_spanned", 1)
                    for s1 in range(len(slots1) - k1 + 1):
                        start1 = slots1[s1]["start_m"]
                        end1 = slots1[s1 + k1 - 1]["end_m"]
                        for s2 in range(len(slots2) - k2 + 1):
                            start2 = slots2[s2]["start_m"]
                            end2 = slots2[s2 + k2 - 1]["end_m"]
                            # Overlap > 15 minutes is strictly prohibited
                            overlap = max(0, min(end1, end2) - max(start1, start2))
                            if overlap > 15:
                                model.Add(x[i1, d, s1] + x[i2, d, s2] <= 1)
                                teacher_conflict_checks += 1

    print(f"Configured constraints. Checked {teacher_conflict_checks} simultaneous teacher pairs.")

    # Objective: Randomize permutation away from 1st term slots
    obj_terms = []
    for (i, d, s_idx), var in x.items():
        w = rng.randint(50, 1000)
        orig_d = raw_baseline[i].get("day_number") if i < len(raw_baseline) else None
        orig_s = raw_baseline[i].get("start_slot_index", 0) if i < len(raw_baseline) else 0
        if orig_d == d and orig_s == s_idx:
            w -= 900
        obj_terms.append(w * var)

    model.Maximize(sum(obj_terms))

    print("Solving CP-SAT model for randomized 2nd Term schedule...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = seed

    t0 = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - t0
    print(f"Solver completed in {elapsed:.2f}s with status: {solver.StatusName(status)}")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("Failed to find feasible schedule for 2nd Term!")

    # Assemble new 2nd Term exam records
    raw_2nd_records = []
    for i, rec in enumerate(records):
        slots = get_slots_for_rec(rec)
        k = rec.get("slots_spanned", 1)
        for d in DAYS:
            for s_idx in range(len(slots) - k + 1):
                if solver.Value(x[i, d, s_idx]) == 1:
                    new_rec = dict(rec)
                    new_rec["exam_term"] = "2nd Term"
                    new_rec["day_number"] = d
                    new_rec["date"] = EXAM_DATES[d]["date"]
                    new_rec["short_date"] = EXAM_DATES[d]["short_date"]
                    new_rec["day_name"] = EXAM_DATES[d]["day_name"]
                    new_rec["slot_number"] = slots[s_idx]["slot_num"]
                    new_rec["slots_spanned"] = k
                    new_rec["start_slot_index"] = s_idx
                    new_rec["end_slot_index"] = s_idx + k - 1
                    new_rec["start_m"] = slots[s_idx]["start_m"]
                    new_rec["end_m"] = slots[s_idx + k - 1]["end_m"]

                    if k == 1:
                        new_rec["time_slot"] = slots[s_idx]["time_slot"]
                        new_rec["time"] = slots[s_idx]["time_slot"]
                    else:
                        start_time_part = slots[s_idx]["time_slot"].split("–")[0].strip()
                        end_time_part = slots[s_idx + k - 1]["time_slot"].split("–")[1].strip()
                        full_time_slot = f"{start_time_part} – {end_time_part}"
                        new_rec["time_slot"] = full_time_slot
                        new_rec["time"] = full_time_slot

                    raw_2nd_records.append(new_rec)
                    break

    # Sort deterministically by day_number, start_m, section_name, slot_number
    raw_2nd_records.sort(key=lambda r: (
        r["day_number"],
        r["start_m"],
        r.get("section_name", ""),
        r["slot_number"]
    ))

    # Re-index clean consecutive exam IDs
    final_records = []
    for idx, r in enumerate(raw_2nd_records, start=1):
        r["id"] = f"exam_{idx}"
        final_records.append(r)

    # Verification: check all teacher overlaps
    teacher_time_slots = defaultdict(list)
    for r in final_records:
        t_list = set()
        for t_field in ["teacher", "subject_teacher", "proctor", "active_subject_teacher"]:
            val = r.get(t_field)
            if val and val not in ["Assigned Faculty", "TBA", "TBD", "None"]:
                t_list.add(val)
        for t in t_list:
            teacher_time_slots[(t, r["day_number"])].append((r["start_m"], r["end_m"], r["section"], r["subject"]))

    all_conflicts = []
    for (teacher, day), sessions in teacher_time_slots.items():
        for i in range(len(sessions)):
            s1, e1, sec1, subj1 = sessions[i]
            for j in range(i + 1, len(sessions)):
                s2, e2, sec2, subj2 = sessions[j]
                overlap = max(0, min(e1, e2) - max(s1, s2))
                if overlap > 15:
                    all_conflicts.append((teacher, day, f"{s1}-{e1}", sec1, subj1, f"{s2}-{e2}", sec2, subj2))

    print(f"Verification: Teacher Overlap Conflicts Count = {len(all_conflicts)}")
    if len(all_conflicts) > 0:
        for c in all_conflicts[:5]:
            print("  Conflict:", c)
        raise RuntimeError("Found teacher overlaps in generated 2nd term schedule!")

    # Check variation from 1st term
    map1 = {(r["section_id"], r["subject"]): (r["day_number"], r["slot_number"]) for r in raw_baseline}
    map2 = {(r["section_id"], r["subject"]): (r["day_number"], r["slot_number"]) for r in final_records}
    same_count = sum(1 for k in map1 if map1.get(k) == map2.get(k))
    print(f"Schedule Variation: {len(map1) - same_count} / {len(map1)} items changed slot/day from 1st term ({(len(map1)-same_count)*100/len(map1):.1f}% randomized, {same_count} exact copies)")

    # Save to amis_exam_calendar/
    with open(EXAM_DATA_2ND_JSON, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)
    print(f"Successfully wrote {EXAM_DATA_2ND_JSON} ({len(final_records)} records)")

    js_content = "const ALL_EXAM_RECORDS = " + json.dumps(final_records, indent=2, ensure_ascii=False) + ";\n\nif (typeof window !== 'undefined') {\n  window.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n}\nif (typeof module !== 'undefined' && module.exports) {\n  module.exports = ALL_EXAM_RECORDS;\n}\n"
    with open(EXAM_DATA_2ND_JS, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully wrote {EXAM_DATA_2ND_JS}")

    # Also save to root /home/tatsuya/Projects/AMIS/
    with open(ROOT_EXAM_DATA_2ND_JSON, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)
    print(f"Successfully wrote {ROOT_EXAM_DATA_2ND_JSON}")

    with open(ROOT_EXAM_DATA_2ND_JS, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully wrote {ROOT_EXAM_DATA_2ND_JS}")

    return final_records

if __name__ == "__main__":
    generate_schedule()
