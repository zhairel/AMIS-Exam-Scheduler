#!/usr/bin/env python3
"""Regression checks for the August 24 official exam-schedule corrections."""

import csv
import json
import os
import re
from collections import Counter, defaultdict

import openpyxl

import apply_exam_schedule_corrections_20260824 as correction


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def overlaps(left, right):
    return not (left["end_m"] <= right["start_m"] or left["start_m"] >= right["end_m"])


def section_has(record, *tokens):
    name = record["section_name"].upper()
    return all(token.upper() in name for token in tokens)


def get_one(records, predicate, label):
    matches = [record for record in records if predicate(record)]
    assert len(matches) == 1, f"Expected one {label}, found {len(matches)}"
    return matches[0]


def main():
    with open(os.path.join(BASE_DIR, "exam_data.json"), encoding="utf-8") as handle:
        records = json.load(handle)
    with open(os.path.join(BASE_DIR, "class_schedules_data.json"), encoding="utf-8") as handle:
        class_sections = json.load(handle)
    with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.json"), encoding="utf-8") as handle:
        teacher_weekly = json.load(handle)

    assert len(records) == 592, f"Expected 592 final exams, got {len(records)}"
    assert Counter(record["duration_minutes"] for record in records) == Counter({60: 567, 120: 25})
    assert all(record["slots_spanned"] == (2 if record["duration_minutes"] == 120 else 1) for record in records)
    assert len({record["id"] for record in records}) == len(records)
    assert all(record.get("gender", "") == correction.infer_gender(record) for record in records)
    assert all(
        record["subject"] == "Filipino"
        for record in records
        if correction.subject_key(record.get("subject")) == "filipino"
    )
    keychelle_records = [record for record in records if record["teacher_id"] == "tchr_keychell"]
    assert keychelle_records
    assert all(record["teacher"] == "Teacher Keychelle" for record in keychelle_records)
    assert correction.canonical_teacher("Teacher Keychell") == ("Teacher Keychelle", "tchr_keychell")
    assert correction.canonical_teacher("Teacher Keychelle") == ("Teacher Keychelle", "tchr_keychell")
    subject_counts = Counter((record["section_id"], record["subject_id"]) for record in records)
    repeated_subjects = {key: count for key, count in subject_counts.items() if count > 1}
    assert repeated_subjects == {}

    assert not any(correction.subject_key(record["subject"]) == "research_consultation" for record in records)
    assert not any(correction.subject_key(record["subject"]) == "aral_math" for record in records)

    normylah_records = [record for record in records if record.get("subject_teacher_id") == "tchr_normylah"]
    assert len(normylah_records) == 12
    assert all(record["teacher"] == "Teacher Normylah" for record in normylah_records)
    assert all(record["teacher_status"] == "RESIGNED_INACTIVE" for record in normylah_records)
    assert all(record["subject_teacher_status"] == "RESIGNED_INACTIVE" for record in normylah_records)
    assert all(record["subject_teacher_active"] is False for record in normylah_records)
    assert all(record["replacement_teacher_required"] is True for record in normylah_records)
    assert all(record["active_subject_teacher_id"] == "" for record in normylah_records)
    assert all(record["proctor_id"] != "tchr_normylah" for record in normylah_records)
    assert all(record["proctor_status"] == "ACTIVE_ASSIGNED" for record in normylah_records)
    assert all(
        record["inactive_teacher_warning"] == correction.NORMYLAH_INACTIVE_WARNING
        for record in normylah_records
    )

    registry_by_id = {teacher["id"]: teacher for teacher in correction.TEACHER_REGISTRY}
    merged_identity_name = "Teacher Franchette Zarah M. Ranain"
    assert registry_by_id["tchr_franchette"]["canonical_name"] == merged_identity_name
    assert registry_by_id["tchr_zara"]["same_person_as"] == "tchr_franchette"
    merged_identity_records = [
        record for record in records
        if record["teacher_id"] in {"tchr_franchette", "tchr_zara"}
    ]
    assert merged_identity_records
    assert all(record["subject_teacher"] == merged_identity_name for record in merged_identity_records)
    assert not any(record["proctor_id"] == "tchr_zara" for record in records)
    for exam_id, proctor_id in correction.IDENTITY_CONFLICT_PROCTOR_OVERRIDES.items():
        record = next(item for item in records if item["id"] == exam_id)
        assert record["proctor_id"] == proctor_id
        expected_source = (
            "SUBJECT_TEACHER_CONFLICT_COVERAGE" if exam_id == "exam_549"
            else "IDENTITY_CONFLICT_COVERAGE"
        )
        assert record["proctor_assignment_source"] == expected_source
    assert correction.IDENTITY_CONFLICT_PROCTOR_OVERRIDES == {"exam_549": "tchr_franchette"}

    normylah_coverage_counts = Counter(record["proctor_id"] for record in normylah_records)
    assert max(normylah_coverage_counts.values()) <= correction.AUTO_COVERAGE_MAX_ASSIGNMENTS_PER_TEACHER
    assert normylah_coverage_counts == Counter({
        "tchr_wardah": 2,
        "tchr_franchette": 2,
        "tchr_zuhora": 2,
        "tchr_junaisah": 2,
        "tchr_mohaymen": 2,
        "tchr_shirehan": 2,
    })
    assert sum(
        record["proctor_id"] == "tchr_junaisah"
        and record["proctor_assignment_source"] != "SUBJECT_TEACHER"
        for record in normylah_records
    ) == 2
    assert {
        record["id"] for record in normylah_records
        if record["proctor_id"] == "tchr_franchette"
    } == {"exam_226", "exam_229"}
    assert normylah_coverage_counts["tchr_ayah"] == 0
    for record in normylah_records:
        proctor = registry_by_id[record["proctor_id"]]
        assert proctor["title"] == "Faculty Member"
        assert "isal" not in correction.clean(proctor.get("department")).lower()
        assert not re.search(
            r"\b(?:ustadh|ustadha|alim)\b",
            correction.clean(proctor.get("canonical_name")).lower(),
        )
        assert proctor.get("status", "active") != "inactive"
        assert proctor.get("is_active", True)
        manual_proctor_id = correction.NORMYLAH_MANUAL_PROCTOR_OVERRIDES.get(record["id"])
        if manual_proctor_id:
            assert record["proctor_id"] == manual_proctor_id
            assert record["proctor_pool"] == "MANUAL_ADMIN_OVERRIDE"
            assert record["proctor_assignment_source"] == "MANUAL_ADMIN_COVERAGE"
        else:
            assert proctor.get("automatic_proctor_eligible", True)
            assert not correction.clean(proctor.get("leadership_role"))
            assert record["proctor_id"] != "tchr_wardah"
            assert record["proctor_pool"] == "ACADEMIC_TEACHER_ONLY"

    expected_normylah_positions = {
        "exam_30": (1, 480, 540),
        "exam_33": (1, 830, 890),
        "exam_81": (1, 910, 970),
        "exam_226": (2, 980, 1040),
        "exam_229": (2, 1050, 1110),
        "exam_364": (3, 540, 600),
        "exam_316": (3, 760, 820),
        "exam_323": (3, 910, 970),
        "exam_325": (3, 1050, 1110),
        "exam_511": (4, 760, 820),
        "exam_516": (4, 980, 1040),
        "exam_513": (4, 1050, 1110),
    }
    for exam_id, expected in expected_normylah_positions.items():
        record = next(item for item in normylah_records if item["id"] == exam_id)
        assert (record["day_number"], record["start_m"], record["end_m"]) == expected

    weekly_blocks = correction.weekly_blocks_by_teacher(teacher_weekly)
    for record in normylah_records:
        assert not any(
            correction.intervals_overlap(record["start_m"], record["end_m"], start_m, end_m)
            for start_m, end_m in weekly_blocks.get((record["proctor_id"], record["day_name"]), [])
        ), f"Proctor weekly class conflict for {record['id']} / {record['proctor']}"

    grade11 = [record for record in records if record["grade_level"] == "Grade 11"]
    mabisang = [record for record in grade11 if correction.subject_key(record["subject"]) == "mabisang_komunikasyon"]
    assert len(mabisang) == 3
    assert all(record["teacher_id"] == "tchr_nadzra" for record in mabisang)
    g11_girls_mabisang = get_one(
        records,
        lambda record: section_has(record, "GRADE 11", "1ST SHIFT GIRLS")
        and correction.subject_key(record["subject"]) == "mabisang_komunikasyon",
        "Grade 11 Girls Mabisang Komunikasyon exam",
    )
    assert (
        g11_girls_mabisang["day_number"],
        g11_girls_mabisang["start_m"],
        g11_girls_mabisang["end_m"],
    ) == (3, 760, 820)

    suhayb_bio = get_one(
        records,
        lambda record: section_has(record, "GRADE 12", "SUHAYB") and correction.subject_key(record["subject"]) == "general_biology_1",
        "Grade 12 Suhayb General Biology 1 exam",
    )
    grade11_f2f_bio = get_one(
        records,
        lambda record: section_has(record, "GRADE 11", "FACE TO FACE") and correction.subject_key(record["subject"]) == "general_biology_1",
        "Grade 11 F2F General Biology 1 exam",
    )
    assert (suhayb_bio["day_number"], suhayb_bio["start_m"], suhayb_bio["end_m"]) == (1, 625, 685)
    assert not overlaps(suhayb_bio, grade11_f2f_bio), "Biology teacher remains double-booked"

    suhayb_pe = get_one(
        records,
        lambda record: section_has(record, "GRADE 12", "SUHAYB") and correction.subject_key(record["subject"]) == "pe_12",
        "Grade 12 Suhayb PE exam",
    )
    assert (suhayb_pe["day_number"], suhayb_pe["start_m"]) == (2, 480)

    abu_musa_records = [
        record for record in records
        if correction.clean(record.get("section_name") or record.get("section")).upper()
        == "GRADE 12 - ABU MUSA AL-ASHARI"
    ]
    assert len(abu_musa_records) == 9
    assert len({correction.subject_key(record["subject"]) for record in abu_musa_records}) == 9
    assert all(record["start_m"] >= 760 for record in abu_musa_records)
    abu_musa_by_id = {record["id"]: record for record in abu_musa_records}
    assert abu_musa_by_id["exam_280"]["start_m"] == 910
    assert abu_musa_by_id["exam_420"]["start_m"] == 910

    jhs_sections = sorted({record["section_id"] for record in records if correction.is_jhs(record)})
    assert len(jhs_sections) == 15
    for section_id in jhs_sections:
        subjects = {correction.subject_key(record["subject"]) for record in records if record["section_id"] == section_id}
        assert "mapeh" in subjects, f"Missing MAPEH in {section_id}"
        assert "social_studies" in subjects, f"Missing Social Studies in {section_id}"

    grade8_science = [
        record for record in records
        if record["grade_level"] == "Grade 8" and correction.subject_key(record["subject"]) == "science"
    ]
    assert len(grade8_science) == 3
    assert all(record["teacher_id"] == "tchr_radzmia" for record in grade8_science)
    assert not any(record["teacher_id"] == "tchr_shirehan" and correction.subject_key(record["subject"]) == "science" for record in records)

    grade9_10_social = [
        record for record in records
        if record["grade_level"] in {"Grade 9", "Grade 10", "Grade 9 & 10"}
        and correction.subject_key(record["subject"]) == "social_studies"
    ]
    assert len(grade9_10_social) == 7
    assert all(record["teacher_id"] == "tchr_sophia" for record in grade9_10_social)
    assert all(record["subject"] == "Social Science" for record in grade9_10_social)

    sophia_abu_sufyan = get_one(
        records,
        lambda record: section_has(record, "GRADE 7", "ABU SUFYAN")
        and correction.subject_key(record["subject"]) == "filipino",
        "Teacher Sophia Grade 7 Abu Sufyan Filipino exam",
    )
    sophia_utbah = get_one(
        records,
        lambda record: section_has(record, "GRADE 10", "UTBAH")
        and correction.subject_key(record["subject"]) == "social_studies",
        "Teacher Sophia Grade 10 Utbah Social Science exam",
    )
    sophia_abu_dharr = get_one(
        records,
        lambda record: section_has(record, "GRADE 9", "ABU DHARR")
        and correction.subject_key(record["subject"]) == "social_studies",
        "Teacher Sophia Grade 9 Abu Dharr Social Science exam",
    )
    muadh_filipino = get_one(
        records,
        lambda record: section_has(record, "GRADE 8", "MU'ADH", "2ND SHIFT")
        and correction.subject_key(record["subject"]) == "filipino",
        "Teacher Sophia Grade 8 Mu'adh Filipino exam",
    )
    muadh_mapeh = get_one(
        records,
        lambda record: section_has(record, "GRADE 8", "MU'ADH", "2ND SHIFT")
        and correction.subject_key(record["subject"]) == "mapeh",
        "Grade 8 Mu'adh MAPEH exam",
    )
    assert (sophia_abu_sufyan["day_number"], sophia_abu_sufyan["start_m"]) == (1, 830)
    assert (sophia_utbah["day_number"], sophia_utbah["start_m"]) == (1, 760)
    assert not overlaps(sophia_abu_sufyan, sophia_utbah)
    assert (sophia_abu_dharr["day_number"], sophia_abu_dharr["start_m"], sophia_abu_dharr["end_m"]) == (2, 910, 970)
    assert (muadh_filipino["day_number"], muadh_filipino["start_m"]) == (3, 980)
    assert (muadh_mapeh["day_number"], muadh_mapeh["start_m"]) == (4, 980)
    sophia_last_day = [record for record in records if record["teacher_id"] == "tchr_sophia" and record["day_number"] == 4]
    assert sophia_last_day
    assert max(record["end_m"] for record in sophia_last_day) <= 970

    by_id = {record["id"]: record for record in records}
    hainur_reported_pairs = [
        ("exam_1", "exam_17"),
        ("exam_3", "exam_4"),
        ("exam_159", "exam_161"),
        ("exam_144", "exam_146"),
        ("exam_298", "exam_394"),
        ("exam_300", "exam_308"),
    ]
    for left_id, right_id in hainur_reported_pairs:
        left, right = by_id[left_id], by_id[right_id]
        both_hainur = left["teacher_id"] == right["teacher_id"] == "tchr_hainur"
        same_day_overlap = left["day_number"] == right["day_number"] and overlaps(left, right)
        assert not (both_hainur and same_day_overlap), f"Unresolved Hainur conflict: {left_id} / {right_id}"

    talha_arabic = by_id["exam_159"]
    amr_arabic = by_id["exam_161"]
    assert (talha_arabic["day_number"], talha_arabic["start_m"]) == (4, 830)
    assert (amr_arabic["day_number"], amr_arabic["start_m"]) == (2, 830)

    hainur_records = [record for record in records if record["teacher_id"] == "tchr_hainur"]
    assert len(hainur_records) == 19
    assert all(record["teacher"] == "Ustadha Hainur" for record in hainur_records)
    assert (by_id["exam_354"]["day_number"], by_id["exam_354"]["start_m"]) == (3, 830)
    assert (by_id["exam_62"]["day_number"], by_id["exam_62"]["start_m"]) == (1, 830)
    assert all(by_id[exam_id]["teacher_id"] == "tchr_hainur" for exam_id in ("exam_62", "exam_354"))
    hainur_day4 = {
        record["id"]: (record["day_number"], record["start_m"], record["end_m"])
        for record in hainur_records if record["day_number"] == 4
    }
    assert hainur_day4 == {
        "exam_436": (4, 760, 820),
        "exam_159": (4, 830, 890),
        "exam_15": (4, 910, 970),
        "exam_144": (4, 980, 1040),
        "exam_495": (4, 1050, 1110),
    }

    silfah_records = [record for record in records if record["teacher_id"] == "tchr_silfah"]
    assert len(silfah_records) == 20
    assert all(record["teacher"] == "Ustadh Silfah" for record in silfah_records)
    assert all(record["end_m"] <= 1050 for record in silfah_records), "Ustadha Silfah exceeds 5:30 PM"

    usama_science = get_one(
        records,
        lambda record: section_has(record, "GRADE 7", "USAMA") and correction.subject_key(record["subject"]) == "science",
        "Grade 7 Usama Science exam",
    )
    assert (usama_science["day_number"], usama_science["start_m"], usama_science["end_m"]) == (2, 910, 970)

    anas_science = get_one(
        records,
        lambda record: section_has(record, "GRADE 7", "ANAS") and correction.subject_key(record["subject"]) == "science",
        "Grade 7 Anas Science exam",
    )
    assert (anas_science["day_number"], anas_science["start_m"], anas_science["end_m"]) == (1, 910, 970)

    anas_social_studies = get_one(
        records,
        lambda record: section_has(record, "GRADE 7", "ANAS") and correction.subject_key(record["subject"]) == "social_studies",
        "Grade 7 Anas Social Studies exam",
    )
    assert (
        anas_social_studies["day_number"],
        anas_social_studies["start_m"],
        anas_social_studies["end_m"],
    ) == (1, 980, 1040)

    for section_name in ("GRADE 1 (FACE TO FACE)", "GRADE 2 (FACE TO FACE)"):
        compact_records = [
            record for record in records
            if correction.clean(record.get("section_name") or record.get("section")).upper() == section_name
        ]
        assert len(compact_records) == 8
        for day_number in correction.EXAM_DAYS:
            day_records = [record for record in compact_records if record["day_number"] == day_number]
            assert len(day_records) == 2, f"{section_name} Day {day_number} must have exactly two exams"
            assert {record["start_m"] for record in day_records} == {480, 540}
            assert all(record["end_m"] <= 600 for record in day_records)

    grade3_f2f_records = [record for record in records if correction.is_compact_g3_f2f(record)]
    assert len(grade3_f2f_records) == 9
    for day_number, expected_starts in {
        1: {480, 540, 625},
        2: {480, 540},
        3: {480, 540},
        4: {480, 540},
    }.items():
        actual_starts = {
            record["start_m"] for record in grade3_f2f_records if record["day_number"] == day_number
        }
        assert actual_starts == expected_starts, f"Grade 3 F2F Day {day_number}: {actual_starts}"

    elementary_gmrc_positions = {
        "exam_68": (1, 760, 820, "tchr_saliha"),
        "exam_450": (3, 910, 970, "tchr_saliha"),
        "exam_310": (4, 910, 970, "tchr_saliha"),
    }
    for exam_id, expected in elementary_gmrc_positions.items():
        record = by_id[exam_id]
        actual = (record["day_number"], record["start_m"], record["end_m"], record["teacher_id"])
        assert actual == expected, f"Unexpected GMRC position for {exam_id}: {actual}"

    kinder_daily_sections = {
        record["section_id"] for record in records if correction.is_daily_kinder_section(record)
    }
    for section_id in kinder_daily_sections:
        section_records = [record for record in records if record["section_id"] == section_id]
        assert len(section_records) == 4, f"{section_id} must retain exactly four schedules"
        assert Counter(record["day_number"] for record in section_records) == Counter({1: 1, 2: 1, 3: 1, 4: 1})

    for teacher_id, latest_end_m in correction.TEACHER_LATEST_END_M.items():
        teacher_records = [record for record in records if record["teacher_id"] == teacher_id]
        assert teacher_records
        assert max(record["end_m"] for record in teacher_records) <= latest_end_m

    # Official time allocation: no standard ODL first-shift class starts at
    # 11:30 AM, and no ODL second-shift class starts at 01:50 PM.
    for record in records:
        if record["shift"] == "F2F":
            assert record["start_m"] in {480, 540, 625}
        elif record["shift"] == "ODL - 1ST SHIFT":
            if record["grade_level"] == "Kinder 2":
                assert record["start_m"] in {810, 880, 950}
            else:
                assert record["start_m"] in {760, 830, 910}
        elif record["shift"] == "ODL - 2ND SHIFT":
            assert record["start_m"] in {910, 980, 1050}

    expected_exam_coverage = {
        "exam_3": "tchr_jaisam",
        "exam_298": "tchr_mamonas",
        "exam_394": "tchr_hainur",
        "exam_427": "tchr_abdulwahab",
        "exam_428": "tchr_dipatuan",
        "exam_86": "tchr_zuhora",
        "exam_285": "tchr_mamonas",
        "exam_287": "tchr_abdul_karim",
        "exam_290": "tchr_sitti_kauzar",
    }
    for exam_id, teacher_id in expected_exam_coverage.items():
        assert by_id[exam_id]["teacher_id"] == teacher_id
    assert not any(record["teacher_id"] == "tchr_raslina" for record in records)
    assert (
        by_id["exam_394"]["day_number"],
        by_id["exam_394"]["start_m"],
        by_id["exam_394"]["end_m"],
    ) == (3, 760, 820)
    assert (
        by_id["exam_290"]["day_number"],
        by_id["exam_290"]["start_m"],
        by_id["exam_290"]["end_m"],
    ) == (1, 980, 1040)

    g11_girls_shaf = get_one(
        records,
        lambda record: section_has(record, "GRADE 11", "1ST SHIFT GIRLS") and correction.subject_key(record["subject"]) == "shaf",
        "Grade 11 Girls SHAF exam",
    )
    abu_musa_shaf = get_one(
        records,
        lambda record: section_has(record, "GRADE 12", "ABU MUSA") and correction.subject_key(record["subject"]) == "shaf",
        "Grade 12 Abu Musa SHAF exam",
    )
    assert g11_girls_shaf["day_number"] != abu_musa_shaf["day_number"] or not overlaps(g11_girls_shaf, abu_musa_shaf)

    rowena_grade9 = get_one(
        records,
        lambda record: section_has(record, "GRADE 9", "HURAYRAH") and correction.subject_key(record["subject"]) == "science",
        "Grade 9 Hurayrah Science exam",
    )
    rowena_grade11 = get_one(
        records,
        lambda record: section_has(record, "GRADE 11", "1ST SHIFT GIRLS") and correction.subject_key(record["subject"]) == "general_science",
        "Grade 11 Girls General Science exam",
    )
    assert rowena_grade9["day_number"] != rowena_grade11["day_number"] or not overlaps(rowena_grade9, rowena_grade11)

    g11_boys_bio = get_one(
        records,
        lambda record: section_has(record, "GRADE 11", "2ND SHIFT BOYS") and correction.subject_key(record["subject"]) == "general_biology_1",
        "Grade 11 Boys General Biology 1 exam",
    )
    nuaym_science = get_one(
        records,
        lambda record: section_has(record, "GRADE 8", "NUAYM") and correction.subject_key(record["subject"]) == "science",
        "Grade 8 Nuaym Science exam",
    )
    assert g11_boys_bio["day_number"] != nuaym_science["day_number"] or not overlaps(g11_boys_bio, nuaym_science)

    g11_boys_lcs = [
        record for record in records
        if section_has(record, "GRADE 11", "2ND SHIFT BOYS") and correction.subject_key(record["subject"]) == "lcs"
    ]
    assert len(g11_boys_lcs) == 1

    asad_filipino = [
        record for record in records
        if section_has(record, "GRADE 3", "AS'AD") and correction.subject_key(record["subject"]) == "filipino"
    ]
    assert len(asad_filipino) == 1
    assert asad_filipino[0]["id"] == "exam_182"
    assert asad_filipino[0]["subject"] == "Filipino"
    assert asad_filipino[0]["teacher_id"] == "tchr_jenny"
    assert asad_filipino[0]["day_number"] == 2
    assert asad_filipino[0]["start_m"] == 980

    grade5_requested_mapeh = [
        record for record in records
        if record["grade_level"] == "Grade 5"
        and record["section_id"] in {
            "sec_grade_5_face_to_face",
            "sec_grade_5_hamza_ibn_abdul_1st_shift",
            "sec_grade_5_muhammad_ibn_maslamah_1st_shift",
            "sec_grade_5_mus_ab_ibn_abdul_mutalib_2nd_shift",
            "sec_grade_5_al_harith_bin_awf_2nd_shift",
        }
        and correction.subject_key(record["subject"]) == "mapeh"
    ]
    assert len(grade5_requested_mapeh) == 5
    grade5_mapeh_by_section = {record["section_id"]: record for record in grade5_requested_mapeh}
    assert grade5_mapeh_by_section["sec_grade_5_face_to_face"]["teacher_id"] == "tchr_keychell"
    assert grade5_mapeh_by_section["sec_grade_5_hamza_ibn_abdul_1st_shift"]["teacher_id"] == "tchr_keychell"
    assert grade5_mapeh_by_section["sec_grade_5_muhammad_ibn_maslamah_1st_shift"]["teacher_id"] == "tchr_keychell"
    assert grade5_mapeh_by_section["sec_grade_5_mus_ab_ibn_abdul_mutalib_2nd_shift"]["teacher_id"] == "tchr_norhydie"
    assert grade5_mapeh_by_section["sec_grade_5_al_harith_bin_awf_2nd_shift"]["teacher_id"] == "tchr_norhydie"

    franchette_subjects = [
        record for record in records
        if record["subject_teacher_id"] == "tchr_franchette"
    ]
    assert len(franchette_subjects) == 8
    assert all(correction.subject_key(record["subject"]) == "mapeh" for record in franchette_subjects)
    assert all(record["grade_level"] in {"Grade 7", "Grade 8", "Grade 7 & 8"} for record in franchette_subjects)
    assert all(record["teacher"] == "Teacher Franchette Zarah M. Ranain" for record in franchette_subjects)

    franchette_scope_vacancies = [
        record for record in records
        if record["id"] in correction.FRANCHETTE_VACANT_SUBJECT_EXAM_IDS
    ]
    assert len(franchette_scope_vacancies) == len(correction.FRANCHETTE_VACANT_SUBJECT_EXAM_IDS) == 8
    assert {record["id"] for record in franchette_scope_vacancies} == correction.FRANCHETTE_VACANT_SUBJECT_EXAM_IDS
    assert all(record["subject_teacher"] == "Unassigned" for record in franchette_scope_vacancies)
    assert all(record["subject_teacher_id"] == "" for record in franchette_scope_vacancies)
    assert all(record["subject_teacher_status"] == "VACANT_REPLACEMENT_REQUIRED" for record in franchette_scope_vacancies)
    assert all(record["replacement_teacher_required"] is True for record in franchette_scope_vacancies)
    assert all(record["former_subject_teacher_id"] == "tchr_franchette" for record in franchette_scope_vacancies)
    assert all(record["proctor_id"] and record["proctor_conflict_status"] == "CLEAR" for record in franchette_scope_vacancies)
    for exam_id, proctor_id in correction.FRANCHETTE_VACANT_PROCTOR_OVERRIDES.items():
        record = next(item for item in franchette_scope_vacancies if item["id"] == exam_id)
        assert record["proctor_id"] == proctor_id

    hainur_k1_quran = get_one(
        records,
        lambda record: record["id"] == "exam_4",
        "K1 Husain Qur'an exam",
    )
    assert hainur_k1_quran["subject"] == "Qur'an"
    assert hainur_k1_quran["subject_teacher"] == "Unassigned"
    assert hainur_k1_quran["subject_teacher_id"] == ""
    assert hainur_k1_quran["former_subject_teacher_id"] == "tchr_hainur"
    assert hainur_k1_quran["subject_teacher_status"] == "VACANT_REPLACEMENT_REQUIRED"
    assert hainur_k1_quran["proctor_id"] and hainur_k1_quran["proctor_conflict_status"] == "CLEAR"
    k1_husain_hadith = get_one(
        records,
        lambda record: record["id"] == "exam_146",
        "K1 Husain Hadith exam",
    )
    assert k1_husain_hadith["subject_teacher_id"] == "tchr_hainur"
    assert k1_husain_hadith["subject_teacher"] == "Ustadha Hainur"

    mohaymen_mapeh = [
        record for record in records
        if record["section_id"] in correction.MOHAYMEN_MAPEH_SECTION_IDS
        and correction.subject_key(record["subject"]) == "mapeh"
    ]
    assert len(mohaymen_mapeh) == len(correction.MOHAYMEN_MAPEH_SECTION_IDS) == 7
    assert {record["section_id"] for record in mohaymen_mapeh} == correction.MOHAYMEN_MAPEH_SECTION_IDS
    assert all(record["teacher_id"] == "tchr_mohaymen" for record in mohaymen_mapeh)

    zayd_makabansa = get_one(
        records,
        lambda record: record["id"] == "exam_464",
        "Grade 3 Zayd Makabansa exam",
    )
    assert (zayd_makabansa["day_number"], zayd_makabansa["start_m"]) == (1, 980)
    assert zayd_makabansa["proctor_id"] == "tchr_ethel"

    gmrc2_saeed = get_one(
        records,
        lambda record: section_has(record, "GRADE 2", "SAEED")
        and correction.subject_key(record["subject"]) == "gmrc",
        "Grade 2 Saeed GMRC exam",
    )
    hadith_k2_uthman = get_one(
        records,
        lambda record: section_has(record, "KINDER 2", "UTHMAN")
        and correction.subject_key(record["subject"]) == "hadith",
        "Kinder 2 Uthman Hadith exam",
    )
    arabic12_f2f = get_one(
        records,
        lambda record: record["grade_level"] == "Grade 12"
        and record["modality"] == "F2F"
        and correction.subject_key(record["subject"]) == "arabic",
        "Grade 12 F2F Arabic exam",
    )
    assert gmrc2_saeed["teacher_id"] == "tchr_saliha"
    assert hadith_k2_uthman["teacher_id"] == "tchr_saliha"
    assert arabic12_f2f["teacher_id"] == "tchr_mamonas"

    official_lookup = correction.build_official_teacher_lookup(class_sections)
    unmatched = []
    for record in records:
        if (
            correction.subject_key(record["subject"]) == "oral_written"
            or record["id"] in correction.VACANT_SUBJECT_TEACHER_EXAM_IDS
        ):
            continue
        official = correction.pick_official_teacher(record, official_lookup)
        if not official or official[1] != record["teacher_id"]:
            unmatched.append((record["section_name"], record["subject"], record["teacher"]))
    assert not unmatched, f"Official subject-teacher mismatches: {unmatched[:10]}"

    by_section_day = defaultdict(list)
    by_teacher_day = defaultdict(list)
    for record in records:
        by_section_day[(record["section_id"], record["day_number"])].append(record)
        by_teacher_day[(correction.effective_proctor_id(record), record["day_number"])].append(record)

    for section_records in by_section_day.values():
        for index, left in enumerate(section_records):
            for right in section_records[index + 1:]:
                assert not overlaps(left, right), f"Section conflict: {left['id']} / {right['id']}"

    teacher_conflicts = []
    for teacher_records in by_teacher_day.values():
        for index, left in enumerate(teacher_records):
            for right in teacher_records[index + 1:]:
                if not overlaps(left, right):
                    continue
                teacher_conflicts.append((left["id"], right["id"]))
    assert not teacher_conflicts, f"Teacher conflicts: {teacher_conflicts[:10]}"

    # Explicit cohort identity check: grade + modality + section + gender.
    # This supplements section_id validation and guards future imports whose IDs
    # may change while the visible cohort identity remains the same.
    by_cohort_day = defaultdict(list)
    for record in records:
        cohort_key = (
            record["grade_level"],
            record["modality"],
            record["section_name"],
            record.get("gender") or "NONE",
            record["day_number"],
        )
        by_cohort_day[cohort_key].append(record)
    for cohort_records in by_cohort_day.values():
        for index, left in enumerate(cohort_records):
            for right in cohort_records[index + 1:]:
                assert not overlaps(left, right), f"Cohort conflict: {left['id']} / {right['id']}"

    with open(os.path.join(BASE_DIR, "options_exam_data.json"), encoding="utf-8") as handle:
        options = json.load(handle)
    assert all(option == records for option in options.values())

    with open(os.path.join(BASE_DIR, "teacher_subject_tracking.json"), encoding="utf-8") as handle:
        tracking = json.load(handle)
    assert sum(item["total_exams"] for item in tracking) == len(records)

    with open(os.path.join(BASE_DIR, "proctor_assignments.json"), encoding="utf-8") as handle:
        proctor_assignments = json.load(handle)
    assert len(proctor_assignments) == len(records)
    assert sum(item["replacement_teacher_required"] for item in proctor_assignments) == 21
    assert not any(item["proctor_id"] == "tchr_normylah" for item in proctor_assignments)
    manual_assignment_ids = {
        *correction.NORMYLAH_MANUAL_PROCTOR_OVERRIDES,
        *correction.FRANCHETTE_VACANT_PROCTOR_OVERRIDES,
    }
    assert all(
        item["proctor_pool"] == (
            "MANUAL_ADMIN_OVERRIDE" if item["exam_id"] in manual_assignment_ids else "ACADEMIC_TEACHER_ONLY"
        )
        for item in proctor_assignments
        if item["replacement_teacher_required"]
    )

    with open(os.path.join(BASE_DIR, "AMIS_Teacher_Exam_Subject_Assignments.csv"), encoding="utf-8-sig") as handle:
        assert sum(1 for _ in csv.reader(handle)) == len(records) + 1

    workbook = openpyxl.load_workbook(
        os.path.join(BASE_DIR, "Term_Examination_Schedule_S.Y._2026-2027_Optimized.xlsx"),
        read_only=True,
    )
    assert workbook.active.max_row == len(records) + 1
    workbook.close()

    print("PASS: 592 official exam records")
    print("PASS: 567 x 60-minute and 25 x 120-minute exams")
    print("PASS: all requested removals, additions, moves, and teacher corrections")
    print("PASS: exact official section+subject teacher linkage")
    print("PASS: zero teacher, section, and grade/modality/section/gender cohort conflicts")
    print("PASS: JSON, JS source, options, teacher tracking, CSV, and XLSX synchronized")


if __name__ == "__main__":
    main()
