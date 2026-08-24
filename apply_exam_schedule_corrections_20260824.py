#!/usr/bin/env python3
"""Apply the August 24 official term-exam corrections without replacing the scheduler.

The existing exam records and their 60/120-minute durations are the baseline. Only
the explicitly removed duplicate/non-exam rows are deleted. Missing exams are added,
subject teachers are re-linked from class_schedules_data.json, and CP-SAT moves the
fewest possible existing exams needed to produce a conflict-free timetable.
"""

import csv
import json
import os
import re
from collections import Counter, defaultdict
from copy import deepcopy

import openpyxl
from ortools.sat.python import cp_model

from teacher_registry import resolve_teacher


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAM_JSON = os.path.join(BASE_DIR, "exam_data.json")
CLASS_JSON = os.path.join(BASE_DIR, "class_schedules_data.json")
SOURCE_EXAM_JSON = os.environ.get("AMIS_CORRECTION_SOURCE_EXAMS", EXAM_JSON)

EXAM_DAYS = {
    1: {"date": "Wednesday, September 2, 2026", "short": "Sep 2", "name": "Wednesday"},
    2: {"date": "Thursday, September 3, 2026", "short": "Sep 3", "name": "Thursday"},
    3: {"date": "Sunday, September 6, 2026", "short": "Sep 6", "name": "Sunday"},
    4: {"date": "Monday, September 7, 2026", "short": "Sep 7", "name": "Monday"},
}

STANDARD_SLOTS = {
    "F2F": [
        (480, 540, "08:00 AM", "09:00 AM"),
        (540, 600, "09:00 AM", "10:00 AM"),
        (625, 685, "10:25 AM", "11:25 AM"),
    ],
    "ODL_1": [
        (760, 820, "12:40 PM", "01:40 PM"),
        (830, 890, "01:50 PM", "02:50 PM"),
        (910, 970, "03:10 PM", "04:10 PM"),
    ],
    "ODL_2": [
        (910, 970, "03:10 PM", "04:10 PM"),
        (980, 1040, "04:20 PM", "05:20 PM"),
        (1050, 1110, "05:30 PM", "06:30 PM"),
    ],
}

K2_FIRST_SHIFT_SLOTS = [
    (810, 870, "01:30 PM", "02:30 PM"),
    (880, 940, "02:40 PM", "03:40 PM"),
    (950, 1010, "03:50 PM", "04:50 PM"),
]

SHS_FIRST_SHIFT_SLOTS = [
    (760, 820, "12:40 PM", "01:40 PM"),
    (830, 890, "01:50 PM", "02:50 PM"),
    (910, 970, "03:10 PM", "04:10 PM"),
    (980, 1040, "04:20 PM", "05:20 PM"),
]

EARLY_FINISH_TEACHERS = {"tchr_saliha", "tchr_mamonas"}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def subject_key(value):
    raw = clean(value)
    s = raw.lower().replace("’", "'")
    s = re.sub(r"[^a-z0-9']+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    if "research consultation" in s or "research consulatation" in s:
        return "research_consultation"
    if "oral" in s and "written" in s:
        return "oral_written"
    if "mabisang komunikasyon" in s:
        return "mabisang_komunikasyon"
    if s in {"ec", "early childhood"}:
        return "ec"
    if s.startswith("lcs") or "life and career" in s:
        return "lcs"
    if s.startswith("pskp") or "pilosopiya" in s:
        return "pskp"
    if "general physics 1" in s or "gen physics 1" in s:
        return "general_physics_1"
    if "general biology 1" in s or "gen bio 1" in s:
        return "general_biology_1"
    if "general science" in s or "gen science" in s:
        return "general_science"
    if "general mathematics" in s or "general math" in s or "gen math" in s:
        return "general_mathematics"
    if "practical research 2" in s or "prac res 2" in s:
        return "practical_research_2"
    if "21st" in s and ("lit" in s or "literature" in s):
        return "21st_literature"
    if s == "mil" or "media and information literacy" in s:
        return "mil"
    if s in {"pe", "pe 12", "p e", "pe health"}:
        return "pe_12"
    if "aral math" in s:
        return "aral_math"
    if "aral reading" in s:
        return "aral_reading"
    if "social studies" in s or s in {"soc sci", "socsci"}:
        return "social_studies"
    if "social science" in s:
        return "social_studies"
    if "mapeh" in s:
        return "mapeh"
    if re.fullmatch(r"sci\d*", s) or s == "science" or s.startswith("science "):
        return "science"
    if s in {"values ed", "values education", "esp"}:
        return "values_education"
    if s in {"ap", "ap4", "ap5", "araling panlipunan"}:
        return "araling_panlipunan"
    if re.fullmatch(r"fil\d*", s) or s == "filipino":
        return "filipino"
    if re.fullmatch(r"eng\d*", s) or s == "english" or s.startswith("english "):
        return "english"
    if re.fullmatch(r"math\s*\d*", s) or s == "mathematics":
        return "math"
    if re.fullmatch(r"gmrc\d*", s):
        return "gmrc"
    if re.fullmatch(r"tle\d*", s):
        return "tle"
    if s.startswith("shaf"):
        return "shaf"
    if "qur" in s:
        return "quran"
    if s.startswith("arabic"):
        return "arabic"
    if s == "hadith":
        return "hadith"
    if s.startswith("makabansa"):
        return "makabansa"
    if s in {"reading and literacy", "r l"}:
        return "reading_literacy"
    if s == "language":
        return "language"
    if s.startswith("circle time 1"):
        return "circle_time_1"
    if s.startswith("circle time 2"):
        return "circle_time_2"
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def canonical_teacher(value):
    resolved = resolve_teacher(value)
    if resolved:
        return resolved["canonical_name"], resolved["id"]
    fallback = clean(value) or "Assigned Faculty"
    return fallback, "tchr_" + re.sub(r"[^a-z0-9]+", "_", fallback.lower()).strip("_")


def slots_for(record):
    grade = clean(record.get("grade_level") or record.get("grade"))
    shift = clean(record.get("shift")).upper()
    department = clean(record.get("department"))
    if shift == "F2F":
        return STANDARD_SLOTS["F2F"]
    if "1ST" in shift:
        if grade == "Kinder 2":
            return K2_FIRST_SHIFT_SLOTS
        if department == "Senior High School":
            return SHS_FIRST_SHIFT_SLOTS
        return STANDARD_SLOTS["ODL_1"]
    return STANDARD_SLOTS["ODL_2"]


def is_jhs(record):
    return clean(record.get("department")) == "Junior High School"


def is_grade8(record):
    return clean(record.get("grade_level") or record.get("grade")) == "Grade 8"


def is_grade11(record):
    return clean(record.get("grade_level") or record.get("grade")) == "Grade 11"


def section_contains(record, *tokens):
    name = clean(record.get("section_name") or record.get("section")).upper()
    return all(token.upper() in name for token in tokens)


def build_official_teacher_lookup(class_sections):
    lookup = defaultdict(lambda: defaultdict(Counter))
    for section in class_sections:
        section_id = section["section_id"]
        for period in section.get("periods") or section.get("rows") or []:
            if period.get("is_break"):
                continue
            cells = []
            if period.get("subject") and period.get("teacher"):
                cells.append(period)
            cells.extend(cell for cell in (period.get("days") or {}).values() if cell)
            for cell in cells:
                if cell.get("is_break"):
                    continue
                key = subject_key(cell.get("subject") or cell.get("label"))
                teacher = cell.get("teacher")
                if not teacher:
                    embedded = resolve_teacher(cell.get("subject") or cell.get("label"))
                    teacher = embedded["canonical_name"] if embedded else None
                if not key or not teacher:
                    continue
                teacher_name, teacher_id = canonical_teacher(teacher)
                lookup[section_id][key][(teacher_name, teacher_id)] += 1
    return lookup


def pick_official_teacher(record, official_lookup):
    key = subject_key(record.get("subject"))
    if key == "mabisang_komunikasyon":
        return canonical_teacher("Teacher Nadzra")
    candidates = official_lookup.get(record["section_id"], {}).get(key)
    if not candidates:
        return None
    current_name, current_id = canonical_teacher(record.get("teacher"))
    if any(candidate_id == current_id for _, candidate_id in candidates):
        return current_name, current_id
    return candidates.most_common(1)[0][0]


def make_added_record(template, subject, teacher):
    record = deepcopy(template)
    record["id"] = None
    record["subject"] = subject
    record["subject_id"] = "subj_" + subject_key(subject)
    record["teacher"], record["teacher_id"] = canonical_teacher(teacher)
    record["teacher_status"] = "VERIFIED"
    record["duration_minutes"] = 60
    record["slots_spanned"] = 1
    record["_added"] = True
    record["_original_day"] = None
    record["_original_start_m"] = None
    return record


def ensure_subject(records, section_id, subject, teacher):
    key = subject_key(subject)
    if any(r["section_id"] == section_id and subject_key(r["subject"]) == key for r in records):
        return False
    template = next(r for r in records if r["section_id"] == section_id)
    records.append(make_added_record(template, subject, teacher))
    return True


def apply_content_corrections(source_records, class_sections, official_lookup):
    records = []
    removed = []
    renamed = []

    for source in source_records:
        record = deepcopy(source)
        record["_added"] = False
        record["_original_day"] = record["day_number"]
        record["_original_start_m"] = record["start_m"]
        key = subject_key(record.get("subject"))

        if key in {"research_consultation", "aral_math"}:
            removed.append({"reason": "non-exam subject removed", "record": source})
            continue
        if section_contains(record, "GRADE 11", "2ND SHIFT") and clean(record.get("subject")).lower().startswith("lcs 11"):
            removed.append({"reason": "duplicate LCS 11 first entry removed", "record": source})
            continue

        # These JHS rows were generated from MAPEH but mislabeled Social Science.
        if is_jhs(record) and clean(record.get("subject")).lower() == "social science":
            renamed.append({"section": record["section_name"], "from": record["subject"], "to": "MAPEH"})
            record["subject"] = "MAPEH"
            record["subject_id"] = "subj_mapeh"

        # The Grade 8 Science rows assigned to Shirehan are the missing Social Studies load.
        if is_grade8(record) and subject_key(record.get("subject")) == "science" and record.get("teacher_id") == "tchr_shirehan":
            renamed.append({"section": record["section_name"], "from": record["subject"], "to": "Social Studies"})
            record["subject"] = "Social Studies"
            record["subject_id"] = "subj_social_studies"

        records.append(record)

    # Clarified item 21 requires two Filipino examination schedules for Grade 3
    # As'ad, both handled by Teacher Jenny. Preserve both source records and only
    # normalize the older Fil3 display label.
    asad_filipino = [
        r for r in records
        if section_contains(r, "GRADE 3", "AS'AD") and subject_key(r.get("subject")) == "filipino"
    ]
    for record in asad_filipino:
        if clean(record.get("subject")) != "Filipino":
            renamed.append({"section": record["section_name"], "from": record["subject"], "to": "Filipino"})
            record["subject"] = "Filipino"
            record["subject_id"] = "subj_filipino"

    section_by_id = {section["section_id"]: section for section in class_sections}
    additions = []

    # Restore MAPEH and add the genuinely missing Social Studies exam for every JHS section.
    for section in class_sections:
        if section.get("department") != "Junior High School":
            continue
        section_id = section["section_id"]
        if ensure_subject(records, section_id, "MAPEH", "Assigned Faculty"):
            additions.append({"section": section["section_name"], "subject": "MAPEH"})
        social_label = "Social Science" if section.get("grade_level") in {"Grade 9", "Grade 10", "Grade 9 & 10"} else "Social Studies"
        if ensure_subject(records, section_id, social_label, "Assigned Faculty"):
            additions.append({"section": section["section_name"], "subject": social_label})
        if section.get("grade_level") == "Grade 8" and ensure_subject(records, section_id, "Science", "Teacher Radzmia"):
            additions.append({"section": section["section_name"], "subject": "Science"})

    # Add the requested Grade 11 Mabisang Komunikasyon examination to all Grade 11 sections.
    for section in class_sections:
        if section.get("grade_level") != "Grade 11":
            continue
        if ensure_subject(records, section["section_id"], "Mabisang Komunikasyon", "Teacher Nadzra"):
            additions.append({"section": section["section_name"], "subject": "Mabisang Komunikasyon"})

    # The concern named these five Grade 4 sections as missing MAPEH.
    grade4_mapeh_tokens = (
        "GRADE 4 (FACE TO FACE)",
        "ABDUR RAHMAN",
        "HAKIM IBN HAZM",
        "AZ ZUBAIR",
        "IKRIMAH",
    )
    for section in class_sections:
        if section.get("grade_level") != "Grade 4":
            continue
        upper_name = section["section_name"].upper()
        if not any(token in upper_name for token in grade4_mapeh_tokens):
            continue
        if ensure_subject(records, section["section_id"], "MAPEH", "Teacher Halnaisa"):
            additions.append({"section": section["section_name"], "subject": "MAPEH"})

    # Clarified item 22: Grade 5 Al Harith and Mus'ab need MAPEH under
    # their official subject teacher, Teacher Norhydie.
    for section in class_sections:
        if section.get("grade_level") != "Grade 5":
            continue
        upper_name = section["section_name"].upper()
        if not any(token in upper_name for token in ("AL HARITH", "MUS'AB")):
            continue
        if ensure_subject(records, section["section_id"], "MAPEH", "Teacher Norhydie"):
            additions.append({"section": section["section_name"], "subject": "MAPEH"})

    # Re-link every exam with an exact section+subject teacher from the official class schedule.
    relinked = []
    unresolved = []
    for record in records:
        official = pick_official_teacher(record, official_lookup)
        if official:
            old = (record.get("teacher"), record.get("teacher_id"))
            record["teacher"], record["teacher_id"] = official
            record["teacher_status"] = "VERIFIED"
            if old != official:
                relinked.append({
                    "section": record["section_name"],
                    "subject": record["subject"],
                    "from": old[0],
                    "to": official[0],
                })
        elif subject_key(record.get("subject")) == "oral_written":
            # Kinder oral/written examination is a combined homeroom assessment.
            record["teacher"], record["teacher_id"] = canonical_teacher(record.get("teacher"))
            record["teacher_status"] = "VERIFIED"
        else:
            unresolved.append({"section": record["section_name"], "subject": record["subject"]})

    # IDs for additions follow the existing sequence; original IDs never change.
    next_id = max(int(re.search(r"(\d+)$", r["id"]).group(1)) for r in source_records if r.get("id")) + 1
    for record in records:
        if record.get("id") is None:
            record["id"] = f"exam_{next_id}"
            next_id += 1

    return records, {
        "removed": removed,
        "renamed": renamed,
        "added": additions,
        "teacher_relinks": relinked,
        "unresolved_official_teacher_links": unresolved,
        "known_sections": len(section_by_id),
    }


def is_fixed_suhayb_biology(record):
    return section_contains(record, "GRADE 12", "SUHAYB") and subject_key(record["subject"]) == "general_biology_1"


def is_fixed_g11_f2f_biology(record):
    return section_contains(record, "GRADE 11", "FACE TO FACE") and subject_key(record["subject"]) == "general_biology_1"


def fixed_position(record):
    if is_fixed_suhayb_biology(record) or is_fixed_g11_f2f_biology(record):
        return 1, 625
    if section_contains(record, "GRADE 12", "SUHAYB") and subject_key(record["subject"]) == "pe_12":
        return 2, 480
    if section_contains(record, "GRADE 7", "USAMA") and subject_key(record["subject"]) == "science":
        return 1, 910
    return None


def candidate_positions(record):
    slots = slots_for(record)
    span = 2 if int(record.get("duration_minutes") or 60) == 120 else 1
    candidates = []
    for day_number in EXAM_DAYS:
        for start_index in range(len(slots) - span + 1):
            start_m = slots[start_index][0]
            end_m = slots[start_index + span - 1][1]
            if record.get("teacher_id") in EARLY_FINISH_TEACHERS and end_m > 990:
                continue
            fixed = fixed_position(record)
            if fixed and (day_number, start_m) != fixed:
                continue
            candidates.append({
                "day": day_number,
                "start_index": start_index,
                "end_index": start_index + span - 1,
                "start_m": start_m,
                "end_m": end_m,
                "start_text": slots[start_index][2],
                "end_text": slots[start_index + span - 1][3],
            })
    if not candidates:
        raise RuntimeError(f"No legal candidate positions for {record['section_name']} / {record['subject']}")
    return candidates


def solve_minimal_changes(records):
    model = cp_model.CpModel()
    variables = {}
    candidates_by_record = {}
    section_slot_vars = defaultdict(list)
    objective_terms = []

    for index, record in enumerate(records):
        candidates = candidate_positions(record)
        candidates_by_record[index] = candidates
        record_vars = []
        slots = slots_for(record)
        for candidate_index, candidate in enumerate(candidates):
            var = model.NewBoolVar(f"exam_{index}_{candidate_index}")
            variables[(index, candidate_index)] = var
            record_vars.append(var)

            for occupied_slot in range(candidate["start_index"], candidate["end_index"] + 1):
                section_slot_vars[(record["section_id"], candidate["day"], occupied_slot)].append(var)

            if record.get("_added"):
                cost = (candidate["day"] - 1) * 20 + candidate["start_index"] * 3
            else:
                same_day = candidate["day"] == record["_original_day"]
                same_time = candidate["start_m"] == record["_original_start_m"]
                if same_day and same_time:
                    cost = 0
                else:
                    cost = 100000
                    cost += abs(candidate["day"] - record["_original_day"]) * 1000
                    cost += abs(candidate["start_m"] - record["_original_start_m"])
            objective_terms.append(var * cost)
        model.AddExactlyOne(record_vars)

    for vars_at_slot in section_slot_vars.values():
        model.AddAtMostOne(vars_at_slot)

    # A teacher cannot cover overlapping exams. The sole general exception is a
    # synchronized cohort: same grade, subject, shift, and exact time. The Suhayb
    # Biology + Grade 11 F2F Biology pairing is also explicitly requested.
    records_by_teacher = defaultdict(list)
    for index, record in enumerate(records):
        records_by_teacher[record["teacher_id"]].append(index)

    for teacher_records in records_by_teacher.values():
        for left_pos, left_index in enumerate(teacher_records):
            left_record = records[left_index]
            for right_index in teacher_records[left_pos + 1:]:
                right_record = records[right_index]
                explicit_shared_biology = (
                    (is_fixed_suhayb_biology(left_record) and is_fixed_g11_f2f_biology(right_record))
                    or (is_fixed_suhayb_biology(right_record) and is_fixed_g11_f2f_biology(left_record))
                )
                same_cohort = (
                    subject_key(left_record["subject"]) == subject_key(right_record["subject"])
                    and clean(left_record.get("grade_level")) == clean(right_record.get("grade_level"))
                    and clean(left_record.get("shift")) == clean(right_record.get("shift"))
                )
                for left_candidate_index, left_candidate in enumerate(candidates_by_record[left_index]):
                    for right_candidate_index, right_candidate in enumerate(candidates_by_record[right_index]):
                        if left_candidate["day"] != right_candidate["day"]:
                            continue
                        overlaps = not (
                            left_candidate["end_m"] <= right_candidate["start_m"]
                            or left_candidate["start_m"] >= right_candidate["end_m"]
                        )
                        if not overlaps:
                            continue
                        exact_same_time = (
                            left_candidate["start_m"] == right_candidate["start_m"]
                            and left_candidate["end_m"] == right_candidate["end_m"]
                        )
                        if explicit_shared_biology or (same_cohort and exact_same_time):
                            continue
                        model.Add(
                            variables[(left_index, left_candidate_index)]
                            + variables[(right_index, right_candidate_index)]
                            <= 1
                        )

    model.Minimize(sum(objective_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 180.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Exam correction solver failed: {solver.StatusName(status)}")

    moved = []
    for index, record in enumerate(records):
        chosen = None
        for candidate_index, candidate in enumerate(candidates_by_record[index]):
            if solver.Value(variables[(index, candidate_index)]):
                chosen = candidate
                break
        if chosen is None:
            raise RuntimeError(f"Solver did not select a position for {record['id']}")

        if not record.get("_added") and (
            chosen["day"] != record["_original_day"] or chosen["start_m"] != record["_original_start_m"]
        ):
            moved.append({
                "id": record["id"],
                "section": record["section_name"],
                "subject": record["subject"],
                "from_day": record["_original_day"],
                "from_start_m": record["_original_start_m"],
                "to_day": chosen["day"],
                "to_start_m": chosen["start_m"],
            })

        day_info = EXAM_DAYS[chosen["day"]]
        record["day_number"] = chosen["day"]
        record["date"] = day_info["date"]
        record["short_date"] = day_info["short"]
        record["day_name"] = day_info["name"]
        record["slot_number"] = chosen["start_index"] + 1
        record["start_slot_index"] = chosen["start_index"]
        record["end_slot_index"] = chosen["end_index"]
        record["slots_spanned"] = chosen["end_index"] - chosen["start_index"] + 1
        record["start_m"] = chosen["start_m"]
        record["end_m"] = chosen["end_m"]
        record["time_slot"] = f"{chosen['start_text']} – {chosen['end_text']}"
        record["time"] = record["time_slot"]

    print(f"Solver status: {solver.StatusName(status)}; existing exams moved: {len(moved)}")
    return moved


def strip_internal(record):
    return {key: value for key, value in record.items() if not key.startswith("_")}


def build_teacher_tracking(records):
    grouped = {}
    for record in records:
        teacher = record["teacher"]
        if teacher not in grouped:
            grouped[teacher] = {
                "teacher": teacher,
                "total_exams": 0,
                "subjects": set(),
                "grades": set(),
                "sections": set(),
                "modalities": set(),
                "shifts": set(),
                "exams": [],
            }
        item = grouped[teacher]
        item["total_exams"] += 1
        item["subjects"].add(record["subject"])
        item["grades"].add(record["grade"])
        item["sections"].add(f"{record['grade']} — {record['section']}")
        item["modalities"].add(record["modality"])
        item["shifts"].add(record["shift"])
        item["exams"].append(record)

    output = []
    for teacher in sorted(grouped, key=str.lower):
        item = grouped[teacher]
        output.append({
            "teacher": teacher,
            "total_exams": item["total_exams"],
            "subjects": sorted(item["subjects"]),
            "grades": sorted(item["grades"]),
            "sections_count": len(item["sections"]),
            "sections": sorted(item["sections"]),
            "modalities": sorted(item["modalities"]),
            "shifts": sorted(item["shifts"]),
            "exams": sorted(item["exams"], key=lambda r: (r["day_number"], r["start_m"], r["section"])),
        })
    return output


def write_outputs(records, audit):
    records.sort(key=lambda r: (r["day_number"], r["start_m"], r["section"].lower(), r["subject"].lower()))
    clean_records = [strip_internal(record) for record in records]

    with open(EXAM_JSON, "w", encoding="utf-8") as handle:
        json.dump(clean_records, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    with open(os.path.join(BASE_DIR, "exam_data.js"), "w", encoding="utf-8") as handle:
        handle.write("const ALL_EXAM_RECORDS = ")
        json.dump(clean_records, handle, indent=2, ensure_ascii=False)
        handle.write(";\n\nif (typeof window !== 'undefined') {\n  window.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n}\n")
        handle.write("if (typeof module !== 'undefined' && module.exports) {\n  module.exports = ALL_EXAM_RECORDS;\n}\n")

    with open(os.path.join(BASE_DIR, "options_exam_data.json"), "w", encoding="utf-8") as handle:
        json.dump({name: clean_records for name in ("OPTION_A", "OPTION_B", "OPTION_C", "OPTION_D")}, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    tracking = build_teacher_tracking(clean_records)
    with open(os.path.join(BASE_DIR, "teacher_subject_tracking.json"), "w", encoding="utf-8") as handle:
        json.dump(tracking, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    csv_path = os.path.join(BASE_DIR, "AMIS_Teacher_Exam_Subject_Assignments.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "Teacher Name", "Total Exam Load", "Assigned Subject", "Grade Level", "Section",
            "Gender", "Modality", "Shift", "Examination Date", "Examination Time", "Room", "Status",
        ])
        loads = Counter(record["teacher"] for record in clean_records)
        for record in sorted(clean_records, key=lambda r: (r["teacher"].lower(), r["day_number"], r["start_m"])):
            writer.writerow([
                record["teacher"], loads[record["teacher"]], record["subject"], record["grade"],
                record["section"], record.get("gender", ""), record["modality"], record["shift"],
                record["date"], record["time"], record.get("room", ""), record.get("status", "OK"),
            ])

    export_headers = [
        "Day Number", "Date", "Slot Number", "Time Slot", "Section ID", "Section Name",
        "Department", "Grade Level", "Shift", "Subject ID", "Subject", "Teacher ID", "Teacher", "Duration (Mins)",
    ]
    export_rows = [[
        record["day_number"], record["date"], record["slot_number"], record["time_slot"],
        record["section_id"], record["section_name"], record["department"], record["grade_level"],
        record["shift"], record["subject_id"], record["subject"], record["teacher_id"],
        record["teacher"], record["duration_minutes"],
    ] for record in clean_records]

    with open(os.path.join(BASE_DIR, "Term_Examination_Schedule_S.Y._2026-2027_Optimized.csv"), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(export_headers)
        writer.writerows(export_rows)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Exam Schedule (Canonical)"
    worksheet.append(export_headers)
    for row in export_rows:
        worksheet.append(row)
    workbook.save(os.path.join(BASE_DIR, "Term_Examination_Schedule_S.Y._2026-2027_Optimized.xlsx"))

    audit["final_exam_count"] = len(clean_records)
    audit["duration_counts"] = dict(sorted(Counter(record["duration_minutes"] for record in clean_records).items()))
    audit["teacher_count"] = len(tracking)
    with open(os.path.join(BASE_DIR, "exam_schedule_corrections_audit_20260824.json"), "w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main():
    with open(SOURCE_EXAM_JSON, "r", encoding="utf-8") as handle:
        source_records = json.load(handle)
    with open(CLASS_JSON, "r", encoding="utf-8") as handle:
        class_sections = json.load(handle)

    original_duration_counts = Counter(record["duration_minutes"] for record in source_records)
    official_lookup = build_official_teacher_lookup(class_sections)
    records, audit = apply_content_corrections(source_records, class_sections, official_lookup)
    audit["source_exam_count"] = len(source_records)
    audit["source_duration_counts"] = dict(sorted(original_duration_counts.items()))
    audit["moved"] = solve_minimal_changes(records)
    write_outputs(records, audit)

    print(f"Source exams: {len(source_records)}")
    print(f"Removed only explicit non-exam/duplicates: {len(audit['removed'])}")
    print(f"Added requested missing exams: {len(audit['added'])}")
    print(f"Official teacher relinks: {len(audit['teacher_relinks'])}")
    print(f"Unresolved official teacher links: {len(audit['unresolved_official_teacher_links'])}")
    print(f"Final exams: {audit['final_exam_count']} ({audit['duration_counts']})")


if __name__ == "__main__":
    main()
