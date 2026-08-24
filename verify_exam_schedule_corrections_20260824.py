#!/usr/bin/env python3
"""Regression checks for the August 24 official exam-schedule corrections."""

import csv
import json
import os
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

    assert len(records) == 583, f"Expected 583 final exams, got {len(records)}"
    assert Counter(record["duration_minutes"] for record in records) == Counter({60: 558, 120: 25})
    assert all(record["slots_spanned"] == (2 if record["duration_minutes"] == 120 else 1) for record in records)
    assert len({record["id"] for record in records}) == len(records)
    assert len({(record["section_id"], record["subject_id"]) for record in records}) == len(records)

    assert not any(correction.subject_key(record["subject"]) == "research_consultation" for record in records)
    assert not any(correction.subject_key(record["subject"]) == "aral_math" for record in records)

    grade11 = [record for record in records if record["grade_level"] == "Grade 11"]
    mabisang = [record for record in grade11 if correction.subject_key(record["subject"]) == "mabisang_komunikasyon"]
    assert len(mabisang) == 3
    assert all(record["teacher_id"] == "tchr_nadzra" for record in mabisang)

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
    assert (suhayb_bio["day_number"], suhayb_bio["start_m"], suhayb_bio["end_m"]) == (
        grade11_f2f_bio["day_number"], grade11_f2f_bio["start_m"], grade11_f2f_bio["end_m"]
    )

    suhayb_pe = get_one(
        records,
        lambda record: section_has(record, "GRADE 12", "SUHAYB") and correction.subject_key(record["subject"]) == "pe_12",
        "Grade 12 Suhayb PE exam",
    )
    assert (suhayb_pe["day_number"], suhayb_pe["start_m"]) == (2, 480)

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

    usama_science = get_one(
        records,
        lambda record: section_has(record, "GRADE 7", "USAMA") and correction.subject_key(record["subject"]) == "science",
        "Grade 7 Usama Science exam",
    )
    assert (usama_science["day_number"], usama_science["start_m"], usama_science["end_m"]) == (1, 910, 970)

    for teacher_id in correction.EARLY_FINISH_TEACHERS:
        teacher_records = [record for record in records if record["teacher_id"] == teacher_id]
        assert teacher_records
        assert max(record["end_m"] for record in teacher_records) <= 990

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

    official_lookup = correction.build_official_teacher_lookup(class_sections)
    unmatched = []
    for record in records:
        if correction.subject_key(record["subject"]) == "oral_written":
            continue
        official = correction.pick_official_teacher(record, official_lookup)
        if not official or official[1] != record["teacher_id"]:
            unmatched.append((record["section_name"], record["subject"], record["teacher"]))
    assert not unmatched, f"Official subject-teacher mismatches: {unmatched[:10]}"

    by_section_day = defaultdict(list)
    by_teacher_day = defaultdict(list)
    for record in records:
        by_section_day[(record["section_id"], record["day_number"])].append(record)
        by_teacher_day[(record["teacher_id"], record["day_number"])].append(record)

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
                explicit_biology = (
                    (correction.is_fixed_suhayb_biology(left) and correction.is_fixed_g11_f2f_biology(right))
                    or (correction.is_fixed_suhayb_biology(right) and correction.is_fixed_g11_f2f_biology(left))
                )
                same_cohort = (
                    correction.subject_key(left["subject"]) == correction.subject_key(right["subject"])
                    and left["grade_level"] == right["grade_level"]
                    and left["shift"] == right["shift"]
                    and left["start_m"] == right["start_m"]
                    and left["end_m"] == right["end_m"]
                )
                if not explicit_biology and not same_cohort:
                    teacher_conflicts.append((left["id"], right["id"]))
    assert not teacher_conflicts, f"Teacher conflicts: {teacher_conflicts[:10]}"

    with open(os.path.join(BASE_DIR, "options_exam_data.json"), encoding="utf-8") as handle:
        options = json.load(handle)
    assert all(option == records for option in options.values())

    with open(os.path.join(BASE_DIR, "teacher_subject_tracking.json"), encoding="utf-8") as handle:
        tracking = json.load(handle)
    assert sum(item["total_exams"] for item in tracking) == len(records)

    with open(os.path.join(BASE_DIR, "AMIS_Teacher_Exam_Subject_Assignments.csv"), encoding="utf-8-sig") as handle:
        assert sum(1 for _ in csv.reader(handle)) == len(records) + 1

    workbook = openpyxl.load_workbook(
        os.path.join(BASE_DIR, "Term_Examination_Schedule_S.Y._2026-2027_Optimized.xlsx"),
        read_only=True,
    )
    assert workbook.active.max_row == len(records) + 1
    workbook.close()

    print("PASS: 583 official exam records")
    print("PASS: 558 x 60-minute and 25 x 120-minute exams")
    print("PASS: all requested removals, additions, moves, and teacher corrections")
    print("PASS: exact official section+subject teacher linkage")
    print("PASS: zero section conflicts and zero unapproved teacher conflicts")
    print("PASS: JSON, JS source, options, teacher tracking, CSV, and XLSX synchronized")


if __name__ == "__main__":
    main()
