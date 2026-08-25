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

from teacher_registry import TEACHER_REGISTRY, resolve_teacher


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAM_JSON = os.path.join(BASE_DIR, "exam_data.json")
CLASS_JSON = os.path.join(BASE_DIR, "class_schedules_data.json")
TEACHER_WEEKLY_JSON = os.path.join(BASE_DIR, "teacher_weekly_schedules.json")
AUDIT_JSON = os.path.join(BASE_DIR, "exam_schedule_corrections_audit_20260824.json")
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
]

TEACHER_LATEST_END_M = {
    "tchr_saliha": 990,
    "tchr_mamonas": 990,
    "tchr_silfah": 1050,
}
TEACHER_DAY_LATEST_END_M = {
    ("tchr_sophia", 4): 990,
}
HAINUR_DAY4_FIXED_POSITIONS = {
    "exam_436": (4, 760),
    "exam_427": (4, 880),
    "exam_428": (4, 950),
    "exam_495": (4, 1050),
}
HAINUR_GRADE5_TRANSFER_IDS = {"exam_62", "exam_354"}
INACTIVE_TEACHER_IDS = {"tchr_normylah"}
AUTO_COVERAGE_MAX_ASSIGNMENTS_PER_TEACHER = 2
NORMYLAH_MANUAL_PROCTOR_OVERRIDES = {
    "exam_30": "tchr_zuhora",
    "exam_33": "tchr_franchette",
    "exam_81": "tchr_wendy",
    "exam_226": "tchr_ethel",
    "exam_229": "tchr_wendy",
    "exam_316": "tchr_wardah",
    "exam_325": "tchr_shirehan",
    "exam_364": "tchr_zuhora",
    "exam_511": "tchr_shirehan",
    "exam_513": "tchr_mohaymen",
    "exam_516": "tchr_mohaymen",
}
NORMYLAH_AUTO_PROCTOR_EXCLUDED_IDS = {"tchr_ayah", "tchr_angeleni"}
TEACHER_IDENTITY_CANONICAL_IDS = {"tchr_zara": "tchr_franchette"}
IDENTITY_CONFLICT_PROCTOR_OVERRIDES = {
}
ACCOMMODATION_PROCTOR_OVERRIDES = {
    "exam_575": "tchr_keychell",
    # Teacher Wendelyn took over this Filipino subject, but confirmed that
    # Teacher Ethel will cover its Grade 3 Zayd examination.
    "exam_323": "tchr_ethel",
    # Transfer Teacher Ethel's overlapping 120-minute Grade 7 Anas Math
    # proctor duty to the only fully available Academic Teacher.
    "exam_398": "tchr_nof",
}
ACCOMMODATION_PROCTOR_REASONS = {
    "exam_575": "SOPHIA_ANAS_DAY1_EARLY_RELEASE",
    "exam_323": "ETHEL_ZAYD_FILIPINO_REQUEST",
    "exam_398": "ETHEL_ZAYD_FILIPINO_CONFLICT_COVERAGE",
}
FRANCHETTE_VACANT_PROCTOR_OVERRIDES = {}
REQUESTED_NO_PROCTOR_EXAM_IDS = {
    # Keep K1 Husain Qur'an in the section schedule, but do not assign it to
    # Ustadha Hainur or add it as a proctor duty to any faculty timetable.
    "exam_4",
}
ABDUL_KARIM_EXPLICIT_PROCTOR_LABEL_EXAM_IDS = {
    # These six Sep 2–3 ISAL assignments were explicitly confirmed as Alim
    # Abdul Karim proctor duties. Keep their subject ownership unchanged, but
    # show the PROCTOR chip in his faculty timetable.
    "exam_13", "exam_24", "exam_160", "exam_208", "exam_309", "exam_315",
}
SUPPRESSED_NON_NORMYLAH_MAPEH_PROCTOR_IDS = {
    "exam_594",  # Grade 6 F2F
    "exam_595",  # Grade 6 Abdullah
    "exam_596",  # Grade 6 Abbas
    "exam_597",  # Grade 6 Khaleed
    "exam_549",  # Grade 9 Abu Dharr
}
ALL_SUPPRESSED_PROCTOR_IDS = (
    REQUESTED_NO_PROCTOR_EXAM_IDS | SUPPRESSED_NON_NORMYLAH_MAPEH_PROCTOR_IDS
)
NORMYLAH_INACTIVE_WARNING = (
    "Teacher Normylah is inactive/resigned. Please assign a replacement teacher."
)
FRANCHETTE_SCOPE_WARNING = (
    "Teacher Franchette confirmed this is not her assigned subject. "
    "Please assign the correct subject teacher."
)
HAINUR_K1_QURAN_WARNING = (
    "Ustadha Hainur confirmed that K1 Husain Qur'an is not her assigned subject. "
    "Please assign the correct subject teacher."
)

# The official three-period ODL grids cannot hold every Hainur/Silfah duty
# without double-booking them. These seven same-subject faculty assignments provide
# qualified exam coverage; all former Raslina loads remain with Ustadha Hainur.
EXAM_TEACHER_OVERRIDES = {
    "exam_3": "Ustadh Jaisam",          # Qur'an
    "exam_394": "Ustadha Hainur",       # Arabic transferred from Raslina
    "exam_298": "Alim Mamonas",         # Arabic exam coverage
    "exam_427": "Alim Abdulwahab",     # Qur'an
    "exam_428": "Alim Dipatuan",       # Qur'an
    "exam_86": "Teacher Zuhora",        # GMRC
    "exam_285": "Alim Mamonas",        # Arabic
    "exam_287": "Alim Abdul Karim",    # Arabic
    "exam_290": "Teacher Sitti Kauzar", # Oral & Written Exam
    # Teacher Wendelyn officially took over Filipino for Grade 3 Zayd after
    # the former teacher resigned. This is subject ownership, not proctoring.
    "exam_323": "Teacher Wendelyn",
    # Teacher Franchette Zarah officially owns these Grade 3 Makabansa
    # classes. They are regular subject assignments, not proctor-only duties.
    "exam_173": "Teacher Franchette Zarah M. Ranain",
    "exam_314": "Teacher Franchette Zarah M. Ranain",
    "exam_464": "Teacher Franchette Zarah M. Ranain",
    "exam_466": "Teacher Franchette Zarah M. Ranain",
}

# Grade 3 Makabansa is restored to Teacher Franchette above. These Grade 6
# MAPEH exams remain vacant until an admin selects the correct subject teacher.
FRANCHETTE_VACANT_SUBJECT_EXAM_IDS = {
    "exam_594", "exam_595", "exam_596", "exam_597",
}
FRANCHETTE_GRADE3_MAKABANSA_EXAM_IDS = {
    "exam_173", "exam_314", "exam_464", "exam_466",
}
HAINUR_VACANT_SUBJECT_EXAM_IDS = {"exam_4"}
VACANT_SUBJECT_TEACHER_EXAM_IDS = (
    FRANCHETTE_VACANT_SUBJECT_EXAM_IDS | HAINUR_VACANT_SUBJECT_EXAM_IDS
)
FRANCHETTE_GRADE6_MAPEH_SECTION_IDS = {
    "sec_grade_6_face_to_face",
    "sec_grade_6_abdullah_ibn_salaam_1st_shift",
    "sec_grade_6_abbas_ibn_abd_al_muttalib_1st_shift",
    "sec_grade_6_khaleed_ibn_waleed_2nd_shift",
}
MOHAYMEN_MAPEH_SECTION_IDS = {
    "sec_grade_10_utbah_ibn_ghazwan_1st_shift_girls",
    "sec_grade_10_abu_ayyub_al_ansari_2nd_shift_boys",
    "sec_grade_9_abu_jandal_ibn_suhayl_2nd_shift_girls",
    "sec_grade_9_abu_dharr_al_ghifarri_2nd_shift_boys",
    "sec_grade_9_abu_hurayrah_1st_shift_girls",
    "sec_grade_9_10_boys_face_to_face",
    "sec_grade_9_10_girls_face_to_face",
}
MOHAYMEN_PE12_SECTION_IDS = {
    "sec_grade_12_abu_musa_al_ashari",  # ODL
    "sec_grade_12_suhayb_ar_rumi",      # F2F
}


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
        # Collapse legacy duplicate identities (for example Teacher Zara) at
        # the source so subject ownership and faculty timetables use one ID.
        teacher_id = TEACHER_IDENTITY_CANONICAL_IDS.get(resolved["id"], resolved["id"])
        teacher_by_id = {teacher["id"]: teacher for teacher in TEACHER_REGISTRY}
        canonical_name = teacher_by_id.get(teacher_id, resolved)["canonical_name"]
        return canonical_name, teacher_id
    fallback = clean(value) or "Assigned Faculty"
    return fallback, "tchr_" + re.sub(r"[^a-z0-9]+", "_", fallback.lower()).strip("_")


def parse_clock_minutes(value, fallback_meridiem=None):
    text = clean(value).upper().replace(".", "")
    match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3) or fallback_meridiem
    if minute > 59 or hour > 23:
        return None
    if meridiem:
        if not 1 <= hour <= 12:
            return None
        hour %= 12
        if meridiem == "PM":
            hour += 12
    return hour * 60 + minute


def parse_time_range_minutes(value):
    parts = re.split(r"\s*(?:–|—|-)\s*", clean(value))
    if len(parts) != 2:
        return None
    start_meridiem_match = re.search(r"\b(AM|PM)\b", parts[0].upper())
    end_meridiem_match = re.search(r"\b(AM|PM)\b", parts[1].upper())
    start_meridiem = start_meridiem_match.group(1) if start_meridiem_match else None
    end_meridiem = end_meridiem_match.group(1) if end_meridiem_match else None
    start_m = parse_clock_minutes(parts[0], end_meridiem)
    end_m = parse_clock_minutes(parts[1], start_meridiem)
    if start_m is None or end_m is None:
        return None
    if end_m <= start_m and not start_meridiem and end_meridiem and start_m >= 12 * 60:
        start_m -= 12 * 60
    if end_m <= start_m:
        return None
    return start_m, end_m


def intervals_overlap(left_start, left_end, right_start, right_end):
    return left_start < right_end and right_start < left_end


def canonical_teacher_identity_id(teacher_id):
    teacher_id = clean(teacher_id)
    return TEACHER_IDENTITY_CANONICAL_IDS.get(teacher_id, teacher_id)


def effective_proctor_id(record):
    if record.get("id") in ALL_SUPPRESSED_PROCTOR_IDS:
        return ""
    return canonical_teacher_identity_id(record.get("proctor_id") or record.get("teacher_id"))


def suppress_non_normylah_mapeh_proctors(records):
    """Keep the MAPEH exams but remove extra proctor-only assignments."""
    suppressed = []
    for record in records:
        if record.get("id") not in SUPPRESSED_NON_NORMYLAH_MAPEH_PROCTOR_IDS:
            continue
        suppressed.append({
            "exam_id": record["id"],
            "subject": record["subject"],
            "section": record["section_name"],
            "former_proctor": clean(record.get("proctor")),
            "former_proctor_id": clean(record.get("proctor_id")),
        })
        record["proctor"] = ""
        record["proctor_id"] = ""
        record["proctor_status"] = "NOT_ASSIGNED"
        record["proctor_department"] = ""
        record["proctor_pool"] = "NONE"
        record["proctor_assignment_source"] = "ADMIN_REMOVED_NON_NORMYLAH_MAPEH"
        record["proctor_conflict_status"] = "NOT_ASSIGNED"
        record["proctor_coverage_reason"] = "NON_NORMYLAH_MAPEH_PROCTOR_REMOVED"
    return suppressed


def suppress_requested_no_proctor_assignments(records):
    """Keep requested exams visible without creating any faculty duty."""
    suppressed = []
    for record in records:
        if record.get("id") not in REQUESTED_NO_PROCTOR_EXAM_IDS:
            continue
        suppressed.append({
            "exam_id": record["id"],
            "subject": record["subject"],
            "section": record["section_name"],
            "former_proctor": clean(record.get("proctor")),
            "former_proctor_id": clean(record.get("proctor_id")),
        })
        record["proctor"] = ""
        record["proctor_id"] = ""
        record["proctor_status"] = "NOT_ASSIGNED"
        record["proctor_department"] = ""
        record["proctor_pool"] = "NONE"
        record["proctor_assignment_source"] = "ADMIN_NO_PROCTOR_REQUEST"
        record["proctor_conflict_status"] = "CLEAR"
        record["proctor_coverage_reason"] = "NO_PROCTOR_REQUESTED"
    return suppressed


def apply_subject_teacher_status(records):
    """Separate historical subject ownership from the active exam proctor role."""
    teacher_by_id = {teacher["id"]: teacher for teacher in TEACHER_REGISTRY}
    for record in records:
        subject_teacher = clean(record.get("teacher"))
        subject_teacher_id = clean(record.get("teacher_id"))
        is_scope_vacancy = record.get("id") in VACANT_SUBJECT_TEACHER_EXAM_IDS
        if is_scope_vacancy:
            record["former_subject_teacher"] = (
                clean(record.get("former_subject_teacher")) or subject_teacher
                or (
                    "Teacher Franchette Zarah M. Ranain"
                    if record.get("id") in FRANCHETTE_VACANT_SUBJECT_EXAM_IDS
                    else "Ustadha Hainur"
                )
            )
            record["former_subject_teacher_id"] = (
                clean(record.get("former_subject_teacher_id")) or subject_teacher_id
                or (
                    "tchr_franchette"
                    if record.get("id") in FRANCHETTE_VACANT_SUBJECT_EXAM_IDS
                    else "tchr_hainur"
                )
            )
            record["teacher"] = ""
            record["teacher_id"] = ""
            record["teacher_status"] = "VACANT_REPLACEMENT_REQUIRED"
            record["subject_teacher"] = "Unassigned"
            record["subject_teacher_id"] = ""
            record["subject_teacher_active"] = False
            record["replacement_teacher_required"] = True
            record["subject_teacher_status"] = "VACANT_REPLACEMENT_REQUIRED"
            record["active_subject_teacher"] = ""
            record["active_subject_teacher_id"] = ""
            record["inactive_teacher_warning"] = (
                HAINUR_K1_QURAN_WARNING
                if record.get("id") in HAINUR_VACANT_SUBJECT_EXAM_IDS
                else FRANCHETTE_SCOPE_WARNING
            )
            record["proctor"] = ""
            record["proctor_id"] = ""
            record["proctor_status"] = "PENDING_ASSIGNMENT"
            record["proctor_assignment_source"] = "AUTO_ACADEMIC_COVERAGE"
            continue
        canonical_identity_id = canonical_teacher_identity_id(subject_teacher_id)
        if canonical_identity_id != subject_teacher_id:
            subject_teacher = teacher_by_id[canonical_identity_id]["canonical_name"]
            record["teacher"] = subject_teacher
        is_inactive = subject_teacher_id in INACTIVE_TEACHER_IDS

        record["subject_teacher"] = subject_teacher
        record["subject_teacher_id"] = subject_teacher_id
        record["subject_teacher_active"] = not is_inactive
        record["replacement_teacher_required"] = is_inactive

        if is_inactive:
            record["teacher_status"] = "RESIGNED_INACTIVE"
            record["subject_teacher_status"] = "RESIGNED_INACTIVE"
            record["active_subject_teacher"] = ""
            record["active_subject_teacher_id"] = ""
            record["inactive_teacher_warning"] = NORMYLAH_INACTIVE_WARNING
            record["proctor"] = ""
            record["proctor_id"] = ""
            record["proctor_status"] = "PENDING_ASSIGNMENT"
            record["proctor_assignment_source"] = "AUTO_ACADEMIC_COVERAGE"
        else:
            if record.get("id") in ABDUL_KARIM_EXPLICIT_PROCTOR_LABEL_EXAM_IDS:
                record["display_as_proctor_duty"] = True
            else:
                record.pop("display_as_proctor_duty", None)
            if record.get("id") in FRANCHETTE_GRADE3_MAKABANSA_EXAM_IDS:
                # This is restored subject ownership, not historical or
                # substitute-proctor coverage. Remove stale vacancy metadata.
                record.pop("former_subject_teacher", None)
                record.pop("former_subject_teacher_id", None)
                record.pop("proctor_coverage_reason", None)
            record["subject_teacher_status"] = "ACTIVE_VERIFIED"
            record["active_subject_teacher"] = subject_teacher
            record["active_subject_teacher_id"] = subject_teacher_id
            record["inactive_teacher_warning"] = ""
            record["proctor"] = teacher_by_id.get(canonical_identity_id, {}).get("canonical_name", subject_teacher)
            record["proctor_id"] = canonical_identity_id
            record["proctor_status"] = "ACTIVE_ASSIGNED"
            record["proctor_pool"] = "SUBJECT_TEACHER"
            record["proctor_assignment_source"] = "SUBJECT_TEACHER"
            record["proctor_department"] = teacher_by_id.get(subject_teacher_id, {}).get(
                "department", record.get("department", "Faculty")
            )
            record["proctor_conflict_status"] = "CLEAR"


def apply_identity_conflict_proctor_overrides(records):
    """Apply explicit conflict-free coverage for identity and accommodation clashes."""
    teacher_by_id = {teacher["id"]: teacher for teacher in TEACHER_REGISTRY}
    assignments = []
    for record in records:
        proctor_id = (
            IDENTITY_CONFLICT_PROCTOR_OVERRIDES.get(record["id"])
            or ACCOMMODATION_PROCTOR_OVERRIDES.get(record["id"])
        )
        if not proctor_id:
            continue
        proctor = teacher_by_id[proctor_id]
        record["proctor"] = proctor["canonical_name"]
        record["proctor_id"] = proctor_id
        record["proctor_status"] = "ACTIVE_ASSIGNED"
        record["proctor_department"] = proctor.get("department", "Academic Faculty")
        record["proctor_pool"] = "ACADEMIC_TEACHER_ONLY"
        is_accommodation = record["id"] in ACCOMMODATION_PROCTOR_OVERRIDES
        record["proctor_assignment_source"] = (
            "TEACHER_ACCOMMODATION_COVERAGE"
            if is_accommodation
            else "SUBJECT_TEACHER_CONFLICT_COVERAGE"
        )
        record["proctor_conflict_status"] = "CLEAR"
        record["proctor_coverage_reason"] = (
            ACCOMMODATION_PROCTOR_REASONS[record["id"]]
            if is_accommodation
            else "MOHAYMEN_EXISTING_PROCTOR_DUTY_CONFLICT"
        )
        assignments.append({
            "exam_id": record["id"],
            "subject_teacher": record["subject_teacher"],
            "proctor": record["proctor"],
            "section": record["section_name"],
            "subject": record["subject"],
            "day_number": record["day_number"],
            "time": record["time"],
        })
    return assignments


def weekly_blocks_by_teacher(teacher_weekly):
    blocks = defaultdict(list)
    for teacher_id, teacher in (teacher_weekly or {}).items():
        source_teacher_id = teacher.get("teacher_id") or teacher.get("id") or teacher_id
        resolved_id = canonical_teacher_identity_id(
            source_teacher_id
        )
        # tchr_zara is the duplicate identity formerly merged into Franchette.
        # Its Grade 3 Makabansa and Grade 6 MAPEH rows are outside Franchette's
        # confirmed official scope (MAPEH Grades 7–8 only), so they must not
        # create false availability conflicts for her exam-proctor duties.
        if source_teacher_id == "tchr_zara" and resolved_id == "tchr_franchette":
            continue
        for period in teacher.get("periods") or []:
            day_name = clean(period.get("day"))
            parsed_range = parse_time_range_minutes(period.get("time"))
            if day_name and parsed_range:
                blocks[(resolved_id, day_name)].append(parsed_range)
        for blocked in teacher.get("blocked_periods") or teacher.get("unavailable") or []:
            day_name = clean(blocked.get("day"))
            parsed_range = parse_time_range_minutes(blocked.get("time"))
            if day_name and parsed_range:
                blocks[(resolved_id, day_name)].append(parsed_range)
    return blocks


def is_active_academic_teacher(teacher):
    """Allow active academic faculty only; ISAL/Ustadh/Ustadha/Alim are excluded."""
    title = clean(teacher.get("title")).lower()
    department = clean(teacher.get("department")).lower()
    canonical_name = clean(teacher.get("canonical_name")).lower()
    is_isal_identity = (
        "isal" in department
        or re.search(r"\b(?:ustadh|ustadha|alim)\b", canonical_name) is not None
    )
    return (
        title == "faculty member"
        and "faculty" in department
        and not is_isal_identity
        and teacher.get("status", "active") != "inactive"
        and teacher.get("employment_status", "active") != "resigned"
        and teacher.get("is_active", True)
        and teacher.get("automatic_proctor_eligible", True)
        and not clean(teacher.get("leadership_role"))
        and teacher["id"] not in INACTIVE_TEACHER_IDS
    )


def assign_inactive_teacher_proctors(records, teacher_weekly):
    """Assign active Academic Teachers without changing the former subject teacher."""
    teacher_by_id = {teacher["id"]: teacher for teacher in TEACHER_REGISTRY}
    manual_proctor_overrides = {
        **NORMYLAH_MANUAL_PROCTOR_OVERRIDES,
        **FRANCHETTE_VACANT_PROCTOR_OVERRIDES,
    }
    reserved_manual_counts = Counter(manual_proctor_overrides.values())
    academic_teachers = [
        teacher for teacher in TEACHER_REGISTRY
        if is_active_academic_teacher(teacher)
        and teacher["id"] not in NORMYLAH_AUTO_PROCTOR_EXCLUDED_IDS
    ]
    weekly_blocks = weekly_blocks_by_teacher(teacher_weekly)
    busy = defaultdict(list)
    proctor_load_minutes = Counter()
    proctor_day_load_minutes = Counter()
    proctor_assignment_count = Counter()
    automatic_coverage_count = Counter()

    inactive_records = []
    for record in records:
        if record.get("replacement_teacher_required"):
            if record.get("id") in ALL_SUPPRESSED_PROCTOR_IDS:
                continue
            inactive_records.append(record)
            continue
        proctor_id = effective_proctor_id(record)
        if not proctor_id:
            continue
        day_number = int(record.get("_original_day") or record.get("day_number"))
        start_m = int(record.get("_original_start_m") or record.get("start_m"))
        end_m = int(record.get("end_m") or (start_m + int(record.get("duration_minutes") or 60)))
        busy[(proctor_id, day_number)].append((start_m, end_m, record["id"]))
        duration_minutes = end_m - start_m
        proctor_load_minutes[proctor_id] += duration_minutes
        proctor_day_load_minutes[(proctor_id, day_number)] += duration_minutes
        proctor_assignment_count[proctor_id] += 1

    assignments = []
    for record in sorted(inactive_records, key=lambda item: (
        int(item.get("_original_day") or item.get("day_number")),
        int(item.get("_original_start_m") or item.get("start_m")),
        clean(item.get("section_name")),
    )):
        day_number = int(record.get("_original_day") or record.get("day_number"))
        day_name = EXAM_DAYS[day_number]["name"]
        start_m = int(record.get("_original_start_m") or record.get("start_m"))
        end_m = int(record.get("end_m") or (start_m + int(record.get("duration_minutes") or 60)))
        department = clean(record.get("department"))
        candidates = []

        manual_proctor_id = manual_proctor_overrides.get(record["id"])
        is_manual_override = bool(manual_proctor_id)
        candidate_teachers = [teacher_by_id[manual_proctor_id]] if manual_proctor_id else academic_teachers

        for teacher in candidate_teachers:
            teacher_id = teacher["id"]
            reserved_count = 0 if manual_proctor_id else reserved_manual_counts[teacher_id]
            coverage_limit = (
                4 if record.get("id") in VACANT_SUBJECT_TEACHER_EXAM_IDS
                else AUTO_COVERAGE_MAX_ASSIGNMENTS_PER_TEACHER
            )
            if not manual_proctor_id and (
                automatic_coverage_count[teacher_id] + reserved_count
                >= coverage_limit
            ):
                continue
            latest_end_m = TEACHER_DAY_LATEST_END_M.get(
                (teacher_id, day_number), TEACHER_LATEST_END_M.get(teacher_id)
            )
            if latest_end_m is not None and end_m > latest_end_m:
                continue
            if any(
                intervals_overlap(start_m, end_m, blocked_start, blocked_end)
                for blocked_start, blocked_end, *_ in busy[(teacher_id, day_number)]
            ):
                continue
            if any(
                intervals_overlap(start_m, end_m, blocked_start, blocked_end)
                for blocked_start, blocked_end in weekly_blocks.get((teacher_id, day_name), [])
            ):
                continue

            teacher_department = clean(teacher.get("department"))
            department_penalty = 0 if (
                (department == "Elementary" and "Elementary" in teacher_department)
                or (department in {"Junior High School", "Senior High School"} and "High School" in teacher_department)
            ) else 1
            candidates.append((
                0 if automatic_coverage_count[teacher_id] == 1 else 1,
                proctor_load_minutes[teacher_id],
                proctor_day_load_minutes[(teacher_id, day_number)],
                proctor_assignment_count[teacher_id],
                department_penalty,
                teacher["canonical_name"].lower(),
                teacher,
            ))

        if not candidates:
            raise RuntimeError(
                f"No active Academic Teacher is available to proctor {record['section_name']} / "
                f"{record['subject']} on {day_name} at {record.get('time_slot')}"
            )

        selected = min(candidates)[-1]
        record["proctor"] = selected["canonical_name"]
        record["proctor_id"] = selected["id"]
        record["proctor_status"] = "ACTIVE_ASSIGNED"
        record["proctor_department"] = selected.get("department", "Academic Faculty")
        record["proctor_pool"] = "MANUAL_ADMIN_OVERRIDE" if is_manual_override else "ACADEMIC_TEACHER_ONLY"
        record["proctor_assignment_source"] = "MANUAL_ADMIN_COVERAGE" if is_manual_override else "AUTO_ACADEMIC_COVERAGE"
        record["proctor_conflict_status"] = "CLEAR"
        busy[(selected["id"], day_number)].append((start_m, end_m, record["id"]))
        duration_minutes = end_m - start_m
        proctor_load_minutes[selected["id"]] += duration_minutes
        proctor_day_load_minutes[(selected["id"], day_number)] += duration_minutes
        proctor_assignment_count[selected["id"]] += 1
        automatic_coverage_count[selected["id"]] += 1
        assignments.append({
            "exam_id": record["id"],
            "section": record["section_name"],
            "subject": record["subject"],
            "former_subject_teacher": record["subject_teacher"],
            "former_teacher_status": record["subject_teacher_status"],
            "proctor": record["proctor"],
            "proctor_id": record["proctor_id"],
            "day_number": day_number,
            "time_slot": record.get("time_slot"),
        })

    return assignments


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


def is_compact_g1_g2_f2f(record):
    section = clean(record.get("section_name") or record.get("section")).upper()
    return section in {"GRADE 1 (FACE TO FACE)", "GRADE 2 (FACE TO FACE)"}


def is_compact_g3_f2f(record):
    section = clean(record.get("section_name") or record.get("section")).upper()
    return section == "GRADE 3 (FACE TO FACE)"


def is_daily_kinder_section(record):
    grade = clean(record.get("grade_level") or record.get("grade"))
    section = clean(record.get("section_name") or record.get("section")).upper()
    return grade == "Kinder 2" or section == "K1 - HUSAIN IBN ALI (2ND SHIFT)"


def section_contains(record, *tokens):
    name = clean(record.get("section_name") or record.get("section")).upper()
    return all(token.upper() in name for token in tokens)


def infer_gender(record):
    """Return the cohort gender encoded by the official section identity."""
    section = clean(record.get("section_name") or record.get("section")).upper()
    if re.search(r"\bGIRLS?\b|\bFEMALES?\b", section):
        return "FEMALE"
    if re.search(r"\bBOYS?\b|\bMALES?\b", section):
        return "MALE"
    if re.search(r"\bMIX(?:ED)?\b|\bCO[ -]?ED\b", section):
        return "MIXED"
    if clean(record.get("modality")).upper() == "F2F" or clean(record.get("shift")).upper() == "F2F":
        return "MIXED"
    return ""


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
    if record.get("id") in VACANT_SUBJECT_TEACHER_EXAM_IDS:
        return None
    if record.get("id") in EXAM_TEACHER_OVERRIDES:
        return canonical_teacher(EXAM_TEACHER_OVERRIDES[record["id"]])
    # Personnel override: the former Raslina SHAF loads for Grade 5 Hamza and
    # Muhammad now belong to Ustadha Hainur. Keep this after source imports so
    # the resigned teacher cannot be restored by stale class-schedule data.
    if record.get("id") in HAINUR_GRADE5_TRANSFER_IDS and key == "shaf":
        return canonical_teacher("Ustadha Hainur")
    if key == "mabisang_komunikasyon":
        return canonical_teacher("Teacher Nadzra")
    if key == "mapeh" and record.get("section_id") in MOHAYMEN_MAPEH_SECTION_IDS:
        return canonical_teacher("Sir Mohaymen")
    if key == "pe_12" and record.get("section_id") in MOHAYMEN_PE12_SECTION_IDS:
        return canonical_teacher("Sir Mohaymen")
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

        # Normalize legacy Fil/Fil3/Fil4/Fil5 labels to the official display name.
        if key == "filipino" and clean(record.get("subject")) != "Filipino":
            renamed.append({"section": record["section_name"], "from": record["subject"], "to": "Filipino"})
            record["subject"] = "Filipino"
            record["subject_id"] = "subj_filipino"

        if key in {"research_consultation", "aral_math"}:
            removed.append({"reason": "non-exam subject removed", "record": source})
            continue
        if section_contains(record, "GRADE 11", "2ND SHIFT") and clean(record.get("subject")).lower().startswith("lcs 11"):
            removed.append({"reason": "duplicate LCS 11 first entry removed", "record": source})
            continue

        # These JHS rows were generated from MAPEH but mislabeled Social Science.
        if (
            is_jhs(record)
            and clean(record.get("subject")).lower() == "social science"
            and record.get("teacher_id") != "tchr_sophia"
        ):
            renamed.append({"section": record["section_name"], "from": record["subject"], "to": "MAPEH"})
            record["subject"] = "MAPEH"
            record["subject_id"] = "subj_mapeh"

        # The Grade 8 Science rows assigned to Shirehan are the missing Social Studies load.
        if is_grade8(record) and subject_key(record.get("subject")) == "science" and record.get("teacher_id") == "tchr_shirehan":
            renamed.append({"section": record["section_name"], "from": record["subject"], "to": "Social Studies"})
            record["subject"] = "Social Studies"
            record["subject_id"] = "subj_social_studies"

        records.append(record)

    # The Grade 3 As'ad Filipino concern refers to a duplicate examination entry,
    # not a requirement for two exams. Keep the earlier Thursday assignment and
    # remove the later Sunday duplicate so future regeneration cannot restore it.
    asad_filipino = [
        r for r in records
        if section_contains(r, "GRADE 3", "AS'AD") and subject_key(r.get("subject")) == "filipino"
    ]
    if len(asad_filipino) > 1:
        keep = next(
            (record for record in asad_filipino if record.get("id") == "exam_182"),
            min(asad_filipino, key=lambda record: (record.get("day_number", 99), record.get("start_m", 9999))),
        )
        duplicate_ids = {
            record["id"] for record in asad_filipino
            if record is not keep
        }
        for duplicate in asad_filipino:
            if duplicate["id"] in duplicate_ids:
                removed.append({
                    "reason": "duplicate Grade 3 As'ad Filipino exam removed",
                    "record": deepcopy(duplicate),
                })
        records = [record for record in records if record.get("id") not in duplicate_ids]
        asad_filipino = [keep]
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

    # Clarified items 22, 25, and 26: these five Grade 5 sections need
    # MAPEH under the exact teacher assigned in the official class schedule.
    requested_grade5_mapeh = {
        "sec_grade_5_face_to_face": "Teacher Keychelle",
        "sec_grade_5_hamza_ibn_abdul_1st_shift": "Teacher Keychelle",
        "sec_grade_5_muhammad_ibn_maslamah_1st_shift": "Teacher Keychelle",
        "sec_grade_5_mus_ab_ibn_abdul_mutalib_2nd_shift": "Teacher Norhydie",
        "sec_grade_5_al_harith_bin_awf_2nd_shift": "Teacher Norhydie",
    }
    for section in class_sections:
        teacher = requested_grade5_mapeh.get(section.get("section_id"))
        if not teacher:
            continue
        if ensure_subject(records, section["section_id"], "MAPEH", teacher):
            additions.append({"section": section["section_name"], "subject": "MAPEH"})

    # Grade 9, Grade 10, and combined Grade 9 & 10 MAPEH loads belong to
    # Sir Mohaymen according to the official weekly class schedule.
    for section in class_sections:
        if section.get("section_id") not in MOHAYMEN_MAPEH_SECTION_IDS:
            continue
        if ensure_subject(records, section["section_id"], "MAPEH", "Sir Mohaymen"):
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
        record["gender"] = infer_gender(record)

    # IDs for additions follow the existing sequence; original IDs never change.
    next_id = max(int(re.search(r"(\d+)$", r["id"]).group(1)) for r in source_records if r.get("id")) + 1
    for record in records:
        if record.get("id") is None:
            record["id"] = f"exam_{next_id}"
            next_id += 1

    apply_subject_teacher_status(records)

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
    if record.get("replacement_teacher_required"):
        return int(record["_original_day"]), int(record["_original_start_m"])
    if record.get("id") in HAINUR_DAY4_FIXED_POSITIONS:
        return HAINUR_DAY4_FIXED_POSITIONS[record["id"]]
    # Grade 12 Abu Musa correction: the published exam day begins at 12:40 PM.
    # Keep the single official MIL and Practical Research 2 entries at 03:10 PM;
    # the old 04:20 PM placement was displayed as a misleading duplicate row.
    if record.get("id") == "exam_280":
        return 2, 910
    if record.get("id") == "exam_420":
        return 3, 910
    # Elementary GMRC confirmations: Ayyash must begin after the online
    # general assembly, while Saeed and Aasim retain their already-separated
    # Ustadha Saliha schedules.
    if record.get("id") == "exam_68":
        return 1, 760
    if record.get("id") == "exam_450":
        return 3, 910
    if record.get("id") == "exam_310":
        return 4, 910
    # Grade 11 Girls: place Mabisang Komunikasyon in Sunday's first period so
    # the section does not carry four examinations on Wednesday.
    if record.get("id") == "exam_582":
        return 3, 760
    # Grade 3 Zayd Makabansa is Teacher Franchette's own subject and remains on
    # Wednesday's 04:20 PM period.
    if record.get("id") == "exam_464":
        return 1, 980
    # Ammar Makabansa is also Teacher Franchette's own subject. Move it from
    # Thursday 01:50 PM, where it overlaps her Grade 8 Sa'ad MAPEH exam, into
    # the section's open Wednesday 03:10 PM period.
    if record.get("id") == "exam_173":
        return 1, 910
    # Keep Suhayb Biology on its requested Wednesday slot. Grade 11 F2F Biology
    # may move when needed so the shared official teacher is never double-booked.
    if is_fixed_suhayb_biology(record):
        return 1, 625
    if section_contains(record, "GRADE 12", "SUHAYB") and subject_key(record["subject"]) == "pe_12":
        return 2, 480
    # Teacher Aniah's final correction keeps Anas Science at Day 1 03:10 PM.
    # Teacher Sophia's transport accommodation moves Anas Filipino forward to
    # 04:20 PM; Social Studies uses the 05:30 PM period with an active proctor.
    if section_contains(record, "GRADE 7", "USAMA") and subject_key(record["subject"]) == "science":
        return 2, 910
    if section_contains(record, "GRADE 7", "ANAS"):
        if subject_key(record["subject"]) == "science":
            return 1, 910
        if subject_key(record["subject"]) == "social_studies":
            return 1, 1050
        if subject_key(record["subject"]) == "filipino":
            return 1, 980
    # Teacher Sophia accommodations: preserve the already-corrected Sep 2/Sep 3
    # placements and move her final Sep 7 duty to Sep 6. Swapping Mu'adh's
    # Filipino and MAPEH exams keeps the section complete without opening a gap.
    if section_contains(record, "GRADE 7", "ABU SUFYAN") and subject_key(record["subject"]) == "filipino":
        return 1, 830
    if section_contains(record, "GRADE 10", "UTBAH") and subject_key(record["subject"]) == "social_studies":
        return 1, 760
    if section_contains(record, "GRADE 9", "ABU DHARR") and subject_key(record["subject"]) == "social_studies":
        return 2, 910
    if section_contains(record, "GRADE 8", "MU'ADH", "2ND SHIFT"):
        if subject_key(record["subject"]) == "filipino":
            return 3, 980
        if subject_key(record["subject"]) == "mapeh":
            return 4, 980
    return None


def candidate_positions(record):
    slots = slots_for(record)
    span = 2 if int(record.get("duration_minutes") or 60) == 120 else 1
    candidates = []
    for day_number in EXAM_DAYS:
        for start_index in range(len(slots) - span + 1):
            start_m = slots[start_index][0]
            end_m = slots[start_index + span - 1][1]
            # Grade 1 and Grade 2 F2F each have eight exams. Keep exactly two
            # compact exams per day in the first two periods so no class waits
            # through an early vacancy or returns for the 10:25 third period.
            if is_compact_g1_g2_f2f(record) and start_index >= 2:
                continue
            # Grade 3 F2F has nine exams, so Day 1 necessarily keeps three.
            # Days 2–4 use only the first two periods to fill Sunday and avoid
            # an empty early slot before a later examination.
            if is_compact_g3_f2f(record) and day_number != 1 and start_index >= 2:
                continue
            proctor_id = effective_proctor_id(record)
            latest_end_m = TEACHER_DAY_LATEST_END_M.get(
                (proctor_id, day_number),
                TEACHER_LATEST_END_M.get(proctor_id),
            )
            if latest_end_m is not None and end_m > latest_end_m:
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
    cohort_slot_vars = defaultdict(list)
    kinder_section_day_vars = defaultdict(list)
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
                cohort_identity = (
                    clean(record.get("grade_level") or record.get("grade")),
                    clean(record.get("modality")),
                    clean(record.get("section_name") or record.get("section")),
                    infer_gender(record) or "NONE",
                )
                cohort_slot_vars[(cohort_identity, candidate["day"], occupied_slot)].append(var)

            if is_daily_kinder_section(record):
                kinder_section_day_vars[(record["section_id"], candidate["day"])].append(var)

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
    for vars_at_slot in cohort_slot_vars.values():
        model.AddAtMostOne(vars_at_slot)

    # Kinder 2 (all modalities/shifts) and the single Kinder 1 second-shift
    # section each carry four underlying schedules. Spread them evenly so
    # every class has exactly one supervised subject on each exam day.
    kinder_section_ids = {
        record["section_id"] for record in records if is_daily_kinder_section(record)
    }
    for section_id in kinder_section_ids:
        for day_number in EXAM_DAYS:
            model.AddExactlyOne(kinder_section_day_vars[(section_id, day_number)])

    # Absolute anti-conflict rule: a teacher can cover only one exam at a time.
    # There are no same-grade, same-subject, shared-cohort, modality, or gender
    # exceptions. Parallel exams remain valid only when they have different
    # assigned teachers and different section/cohort identities.
    records_by_teacher = defaultdict(list)
    for index, record in enumerate(records):
        proctor_id = effective_proctor_id(record)
        if proctor_id:
            records_by_teacher[proctor_id].append(index)

    for teacher_records in records_by_teacher.values():
        for left_pos, left_index in enumerate(teacher_records):
            left_record = records[left_index]
            for right_index in teacher_records[left_pos + 1:]:
                right_record = records[right_index]
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
        teacher = clean(record.get("proctor") or record.get("teacher"))
        if not teacher:
            continue
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
            "role": "Active Exam Proctor",
        })
    return output


def merge_previous_audit(audit, previous_audit, source_count):
    """Keep the original correction trail when rerunning against corrected output."""
    if not previous_audit or source_count != previous_audit.get("final_exam_count"):
        return audit

    for key in ("removed", "renamed", "added", "teacher_relinks"):
        previous_items = deepcopy(previous_audit.get(key, []))
        seen_items = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in previous_items}
        audit[key] = previous_items + [
            item for item in audit.get(key, [])
            if json.dumps(item, sort_keys=True, ensure_ascii=False) not in seen_items
        ]

    previous_moves = previous_audit.get("moved", [])
    new_moves = audit.get("moved", [])
    accommodation_moves = [
        {
            "id": "exam_399",
            "section": "GRADE 8 - MU'ADH IBN JABAL (2ND SHIFT) - BOYS",
            "subject": "MAPEH",
            "from_day": 3,
            "from_start_m": 980,
            "to_day": 4,
            "to_start_m": 980,
        },
        {
            "id": "exam_260",
            "section": "GRADE 8 - MU'ADH IBN JABAL (2ND SHIFT) - BOYS",
            "subject": "Filipino",
            "from_day": 4,
            "from_start_m": 980,
            "to_day": 3,
            "to_start_m": 980,
        },
    ]
    seen_moves = {
        (move.get("id"), move.get("to_day"), move.get("to_start_m"))
        for move in previous_moves
    }
    audit["moved"] = deepcopy(previous_moves) + [
        move for move in new_moves + accommodation_moves
        if (move.get("id"), move.get("to_day"), move.get("to_start_m")) not in seen_moves
    ]
    audit["source_exam_count"] = previous_audit.get("source_exam_count", audit["source_exam_count"])
    audit["source_duration_counts"] = previous_audit.get(
        "source_duration_counts", audit["source_duration_counts"]
    )
    audit["teacher_accommodations"] = [
        {
            "teacher": "Teacher Sophia",
            "request": "Remove Sep 2 overlap between Grade 7 Abu Sufyan and Grade 10 Utbah",
            "result": "Abu Sufyan retained at 01:50 PM – 02:50 PM; Utbah retained at 12:40 PM – 01:40 PM",
        },
        {
            "teacher": "Teacher Sophia",
            "request": "Avoid a 06:30 PM Grade 9 Abu Dharr dismissal duty",
            "result": "Abu Dharr retained at 03:10 PM – 04:10 PM on Sep 3",
        },
        {
            "teacher": "Teacher Sophia",
            "request": "Do not exceed 04:30 PM on Sep 7",
            "result": "Grade 8 Mu'adh Filipino moved to Sep 6 at 04:20 PM – 05:20 PM; Sep 7 duties now end at 04:10 PM",
        },
        {
            "teacher": "Teacher Sophia",
            "request": "Remove the weekday 05:30 PM – 06:30 PM Anas Filipino duty on Sep 2",
            "result": "Anas Filipino moved to 04:20 PM – 05:20 PM; Social Studies moved to 05:30 PM with Teacher Keychelle as the clear active proctor",
        },
        {
            "teacher": "Ustadha Hainur",
            "request": "Resolve the reported conflicts under the official 12:40 PM first-shift start",
            "result": "Grade 2 Amr Arabic is Sep 3 and Talha Arabic is Sep 7, both at 01:50 PM – 02:50 PM; Hainur has zero overlapping duties",
        },
        {
            "teacher": "Ustadha Hainur",
            "request": "Correct honorific from Ustadh to Ustadha",
            "result": "Canonical teacher name corrected to Ustadha Hainur across exam outputs",
        },
        {
            "teacher": "Ustadha Hainur",
            "request": "Transfer the Grade 5 Muhammad and Hamza SHAF exams from resigned Ustadha Raslina",
            "result": "Hamza is Sep 2 and Muhammad is Sep 6, both at 01:50 PM – 02:50 PM; both remain assigned to Hainur with no conflict",
        },
        {
            "teacher": "Grade 11 and Grade 12",
            "request": "Remove visually duplicated SHS subjects and make Grade 12 Abu Musa begin at 12:40 PM",
            "result": "SHS cells now render only at their authoritative time; Abu Musa MIL and Practical Research 2 moved from 04:20 PM to 03:10 PM while its 12:40 PM and 120-minute exams remain intact",
        },
        {
            "teacher": "Teacher Keychelle",
            "request": "Correct the displayed name from Keychell to Keychelle",
            "result": "Canonical display name corrected across class schedules, exam schedules, faculty views, and exports while preserving tchr_keychell and the former spelling as an import alias",
        },
        {
            "teacher": "Teacher Aniah",
            "request": "Keep Grade 7 Usama Science on Day 2 and reserve Day 1 03:10 PM for Grade 7 Anas Science only",
            "result": "Usama Science retained on Sep 3 at 03:10 PM; Anas Science is Sep 2 at 03:10 PM; Anas Social Studies moved to Sep 2 at 04:20 PM",
        },
        {
            "teacher": "Grade 1 and Grade 2 F2F",
            "request": "Fill Sunday and remove vacant early periods before later exams",
            "result": "Both sections now have exactly two exams per day at 08:00 AM and 09:00 AM, with no 10:25 AM third-period exam",
        },
        {
            "teacher": "Ustadha Saliha",
            "request": "Move Grade 5 Ayyash GMRC after the online general assembly and verify Grade 2 Saeed/Aasim GMRC",
            "result": "Ayyash GMRC is Sep 2 at 12:40 PM; Saeed is Sep 6 and Aasim is Sep 7 at 03:10 PM, all with no overlap",
        },
        {
            "teacher": "Grade 3 F2F",
            "request": "Fill Sunday and remove vacant early periods before later exams",
            "result": "All nine exams are compacted: three on Day 1 and two each on Days 2–4, with Sunday filled at 08:00 AM and 09:00 AM",
        },
        {
            "teacher": "Kindergarten",
            "request": "Provide one supervised subject on every exam day for Kinder 2 and Kinder 1 second shift",
            "result": "Each affected Kindergarten section now has exactly one schedule on each of Days 1–4; the public view shows the subject, assigned teacher, and duration",
        },
        {
            "teacher": "All ODL sections",
            "request": "Use the official shift time allocation and remove premature examination periods",
            "result": "ODL 1st Shift now uses 12:40, 01:50, and 03:10; ODL 2nd Shift uses 03:10, 04:20, and 05:30; F2F and Kinder 2 special grids are unchanged",
        },
        {
            "teacher": "Grade 11 (1st Shift Girls)",
            "request": "Move Mabisang Komunikasyon to Sunday at 12:40 PM to reduce the Wednesday exam load",
            "result": "Mabisang Komunikasyon is fixed on Sep 6 at 12:40 PM with Teacher Nadzra; the section and teacher remain conflict-free",
        },
        {
            "teacher": "Qualified exam coverage",
            "request": "Preserve zero conflicts after reducing both ODL grids to three official periods",
            "result": "Seven overloaded Hainur/Silfah duties received same-subject faculty coverage; all former Raslina duties remain with Ustadha Hainur",
        },
        {
            "teacher": "Ustadha Hainur",
            "request": "Transfer Grade 9 Abu Hurayrah Arabic from resigned Ustadh Raslina",
            "result": "Grade 9 Abu Hurayrah Arabic remains on Sep 6 at 12:40 PM under Ustadha Hainur; Alim Mamonas covers a parallel Arabic duty so no teacher or section conflict is created",
        },
        {
            "teacher": "Teacher Sitti Kauzar",
            "request": "Transfer Kinder 2 Khabaab Oral & Written Exam from Teacher Keychelle",
            "result": "The Sep 2 04:20 PM Oral & Written Exam remains in place under Teacher Sitti Kauzar with no overlapping duty",
        },
        {
            "teacher": "Teacher Normylah",
            "request": "Mark the resigned teacher inactive without deleting her former subjects or exam schedules",
            "result": "All 12 former exam assignments remain visible as Resigned / Inactive and Replacement Required; active Academic Teacher proctors are assigned separately with zero overlaps and no subject-teacher replacement",
        },
    ]
    return audit


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
            "Subject Teacher (Reference)", "Subject Teacher Status", "Replacement Required",
            "Assigned Proctor", "Proctor ID", "Proctor Load", "Proctor Status",
            "Assigned Subject", "Grade Level", "Section", "Gender", "Modality", "Shift",
            "Examination Date", "Examination Time", "Room", "Schedule Status", "Warning",
        ])
        loads = Counter(record["proctor"] for record in clean_records)
        for record in sorted(clean_records, key=lambda r: (r["proctor"].lower(), r["day_number"], r["start_m"])):
            writer.writerow([
                record.get("subject_teacher", record["teacher"]), record.get("subject_teacher_status", "ACTIVE_VERIFIED"),
                "YES" if record.get("replacement_teacher_required") else "NO",
                record["proctor"], record["proctor_id"], loads[record["proctor"]], record["proctor_status"],
                record["subject"], record["grade"], record["section"], record.get("gender", ""),
                record["modality"], record["shift"], record["date"], record["time"],
                record.get("room", ""), record.get("status", "OK"), record.get("inactive_teacher_warning", ""),
            ])

    export_headers = [
        "Day Number", "Date", "Slot Number", "Time Slot", "Section ID", "Section Name",
        "Department", "Grade Level", "Shift", "Subject ID", "Subject",
        "Subject Teacher ID", "Subject Teacher (Reference)", "Subject Teacher Status",
        "Replacement Required", "Proctor ID", "Assigned Proctor", "Proctor Status", "Duration (Mins)",
    ]
    export_rows = [[
        record["day_number"], record["date"], record["slot_number"], record["time_slot"],
        record["section_id"], record["section_name"], record["department"], record["grade_level"],
        record["shift"], record["subject_id"], record["subject"],
        record.get("subject_teacher_id", record["teacher_id"]),
        record.get("subject_teacher", record["teacher"]),
        record.get("subject_teacher_status", "ACTIVE_VERIFIED"),
        "YES" if record.get("replacement_teacher_required") else "NO",
        record["proctor_id"], record["proctor"], record["proctor_status"], record["duration_minutes"],
    ] for record in clean_records]

    proctor_assignments = [{
        "exam_id": record["id"],
        "day_number": record["day_number"],
        "date": record["date"],
        "day_name": record["day_name"],
        "time_slot": record["time_slot"],
        "start_m": record["start_m"],
        "end_m": record["end_m"],
        "grade_level": record["grade_level"],
        "section_id": record["section_id"],
        "section_name": record["section_name"],
        "department": record["department"],
        "shift": record["shift"],
        "subject": record["subject"],
        "subject_teacher": record.get("subject_teacher", record["teacher"]),
        "subject_teacher_id": record.get("subject_teacher_id", record["teacher_id"]),
        "subject_teacher_status": record.get("subject_teacher_status", "ACTIVE_VERIFIED"),
        "replacement_teacher_required": bool(record.get("replacement_teacher_required")),
        "warning": record.get("inactive_teacher_warning", ""),
        "proctor": record["proctor"],
        "proctor_id": record["proctor_id"],
        "proctor_status": record["proctor_status"],
        "proctor_department": record.get("proctor_department", ""),
        "proctor_pool": record.get("proctor_pool", "SUBJECT_TEACHER"),
        "proctor_assignment_source": record.get("proctor_assignment_source", "SUBJECT_TEACHER"),
        "conflict_status": record.get("proctor_conflict_status", "CLEAR"),
    } for record in clean_records]
    with open(os.path.join(BASE_DIR, "proctor_assignments.json"), "w", encoding="utf-8") as handle:
        json.dump(proctor_assignments, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

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
    with open(AUDIT_JSON, "w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main():
    previous_audit = None
    if os.path.exists(AUDIT_JSON):
        with open(AUDIT_JSON, "r", encoding="utf-8") as handle:
            previous_audit = json.load(handle)

    with open(SOURCE_EXAM_JSON, "r", encoding="utf-8") as handle:
        source_records = json.load(handle)
    with open(CLASS_JSON, "r", encoding="utf-8") as handle:
        class_sections = json.load(handle)
    with open(TEACHER_WEEKLY_JSON, "r", encoding="utf-8") as handle:
        teacher_weekly = json.load(handle)

    original_duration_counts = Counter(record["duration_minutes"] for record in source_records)
    official_lookup = build_official_teacher_lookup(class_sections)
    records, audit = apply_content_corrections(source_records, class_sections, official_lookup)
    audit["identity_merge_proctor_overrides"] = apply_identity_conflict_proctor_overrides(records)
    audit["inactive_teacher_proctor_assignments"] = assign_inactive_teacher_proctors(
        records, teacher_weekly
    )
    audit["source_exam_count"] = len(source_records)
    audit["source_duration_counts"] = dict(sorted(original_duration_counts.items()))
    audit["moved"] = solve_minimal_changes(records)
    audit["suppressed_non_normylah_mapeh_proctors"] = suppress_non_normylah_mapeh_proctors(records)
    audit["requested_no_proctor_assignments"] = suppress_requested_no_proctor_assignments(records)
    audit = merge_previous_audit(audit, previous_audit, len(source_records))
    write_outputs(records, audit)

    print(f"Source exams: {len(source_records)}")
    print(f"Removed only explicit non-exam/duplicates: {len(audit['removed'])}")
    print(f"Added requested missing exams: {len(audit['added'])}")
    print(f"Official teacher relinks: {len(audit['teacher_relinks'])}")
    print(f"Unresolved official teacher links: {len(audit['unresolved_official_teacher_links'])}")
    print(f"Final exams: {audit['final_exam_count']} ({audit['duration_counts']})")


if __name__ == "__main__":
    main()
