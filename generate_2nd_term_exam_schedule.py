#!/usr/bin/env python3
"""
generate_2nd_term_exam_schedule.py
Generates the official 2nd Term Examination Schedule for AMIS.
- Baseline: Authoritative 1st Term exam items (sections, subjects, durations, teachers, proctors) from exam_data.json
- Randomization: Mathematically randomized permutation across official 2nd Term dates (Dec 1, 2, 3, & 6, 2026)
- Constraints: 0 teacher conflicts, 0 proctor conflicts, 0 cohort/section conflicts
- Validated with OR-Tools CP-SAT solver
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

K2_1ST_SLOTS = [
    {"slot_num": 1, "time_slot": "01:30 PM – 02:30 PM", "start_m": 810, "end_m": 870},
    {"slot_num": 2, "time_slot": "02:40 PM – 03:40 PM", "start_m": 880, "end_m": 940},
    {"slot_num": 3, "time_slot": "03:50 PM – 04:50 PM", "start_m": 950, "end_m": 1010}
]

SHS_1ST_SLOTS = [
    {"slot_num": 1, "time_slot": "12:40 PM – 01:40 PM", "start_m": 760, "end_m": 820},
    {"slot_num": 2, "time_slot": "01:50 PM – 02:50 PM", "start_m": 830, "end_m": 890},
    {"slot_num": 3, "time_slot": "03:10 PM – 04:10 PM", "start_m": 910, "end_m": 970},
    {"slot_num": 4, "time_slot": "04:20 PM – 05:20 PM", "start_m": 980, "end_m": 1040}
]

def get_slots_for_rec(rec):
    if "Kinder" in rec.get("grade_level", "") and "1ST" in rec.get("shift", ""):
        return K2_1ST_SLOTS
    if "Senior High" in rec.get("department", "") and rec.get("shift", "") == "ODL - 1ST SHIFT":
        return SHS_1ST_SLOTS
    return SHIFT_SLOTS[rec["shift"]]

def active_proctor(rec):
    if rec.get("proctor_status") == "NOT_ASSIGNED" or rec.get("proctor_pool") == "NONE":
        return ""
    return rec.get("proctor_id") or rec.get("teacher_id") or ""

def generate_schedule(seed=20261201):
    print(f"Loading 1st Term exam baseline from {EXAM_DATA_1ST_JSON}...")
    with open(EXAM_DATA_1ST_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} official exam items.")
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

    # Constraint 2: Section capacity and no overlapping exams within each section
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

    # Constraint 3: Strict 0 Proctor/Teacher overlaps across all time slots
    by_teacher = defaultdict(list)
    for i, rec in enumerate(records):
        pid = active_proctor(rec)
        if pid and pid != "tchr_assigned_faculty":
            by_teacher[pid].append(i)

    teacher_conflict_checks = 0
    for pid, items in by_teacher.items():
        if len(items) <= 1:
            continue
        for d in DAYS:
            for idx1 in range(len(items)):
                i1 = items[idx1]
                slots1 = get_slots_for_rec(records[i1])
                k1 = records[i1].get("slots_spanned", 1)
                for idx2 in range(idx1 + 1, len(items)):
                    i2 = items[idx2]
                    slots2 = get_slots_for_rec(records[i2])
                    k2 = records[i2].get("slots_spanned", 1)
                    for s1 in range(len(slots1) - k1 + 1):
                        start1 = slots1[s1]["start_m"]
                        end1 = slots1[s1 + k1 - 1]["end_m"]
                        for s2 in range(len(slots2) - k2 + 1):
                            start2 = slots2[s2]["start_m"]
                            end2 = slots2[s2 + k2 - 1]["end_m"]
                            if not (end1 <= start2 or start1 >= end2):
                                model.Add(x[i1, d, s1] + x[i2, d, s2] <= 1)
                                teacher_conflict_checks += 1

    print(f"Configured constraints. Checked {teacher_conflict_checks} simultaneous teacher/proctor pairs.")

    # Random objective: assign random weights and penalize staying in the exact 1st term day/slot
    obj_terms = []
    for (i, d, s_idx), var in x.items():
        w = rng.randint(50, 1000)
        orig_d = records[i].get("day_number")
        orig_s = records[i].get("start_slot_index", 0)
        if orig_d == d and orig_s == s_idx:
            w -= 900
        obj_terms.append(w * var)

    model.Maximize(sum(obj_terms))

    print("Solving CP-SAT model for randomized 2nd Term schedule...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 25.0
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

    # Verification: strict conflicts
    def strict_conflicts(recs):
        confs = []
        def overlaps(l, r):
            return (l["day_number"] == r["day_number"] and
                    l["start_m"] < r["end_m"] and
                    r["start_m"] < l["end_m"])
        for idx1 in range(len(recs)):
            l = recs[idx1]
            for idx2 in range(idx1 + 1, len(recs)):
                r = recs[idx2]
                if not overlaps(l, r): continue
                lp = active_proctor(l)
                rp = active_proctor(r)
                same_t = bool(lp and lp == rp)
                same_c = (l.get("grade_level") == r.get("grade_level") and
                          l.get("modality") == r.get("modality") and
                          (l.get("section_id") or l.get("section_name")) == (r.get("section_id") or r.get("section_name")) and
                          str(l.get("gender", "NONE")) == str(r.get("gender", "NONE")))
                if same_t or same_c:
                    confs.append((l["id"], r["id"], l.get("section"), l.get("subject"), r.get("section"), r.get("subject")))
        return confs

    conflicts = strict_conflicts(final_records)
    print(f"Verification: Strict Conflicts Count = {len(conflicts)}")
    if len(conflicts) > 0:
        for c in conflicts[:5]:
            print("  Conflict:", c)
        raise RuntimeError("Found conflicts in generated 2nd term schedule!")

    # Check variation from 1st term
    moved = sum(1 for nr, or_ in zip(final_records, records) if nr["day_number"] != or_["day_number"] or nr["start_slot_index"] != or_["start_slot_index"])
    print(f"Schedule Variation: {moved} / {len(final_records)} items changed slot/day from 1st term ({moved*100/len(final_records):.1f}% randomized)")

    # Save to JSON
    with open(EXAM_DATA_2ND_JSON, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)
    print(f"Successfully wrote {EXAM_DATA_2ND_JSON} ({len(final_records)} records)")

    # Save to JS
    with open(EXAM_DATA_2ND_JS, "w", encoding="utf-8") as f:
        f.write("const ALL_EXAM_RECORDS = ")
        json.dump(final_records, f, indent=2, ensure_ascii=False)
        f.write(";\n\nif (typeof window !== 'undefined') {\n  window.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n}\nif (typeof module !== 'undefined' && module.exports) {\n  module.exports = ALL_EXAM_RECORDS;\n}\n")
    print(f"Successfully wrote {EXAM_DATA_2ND_JS}")

    return final_records

if __name__ == "__main__":
    generate_schedule()
