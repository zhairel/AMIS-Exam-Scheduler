#!/usr/bin/env python3
"""
AMIS Examination Calendar Maker - Teacher-Subject Assignment Tracking Generator
Extracts all teacher examination assignments, subjects taught, grades, sections, dates, and workloads.
"""

import os
import csv
import json

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"
DATA_PATH = os.path.join(BASE_DIR, "exam_data.json")

if not os.path.exists(DATA_PATH):
    print("Error: exam_data.json not found.")
    exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    records = json.load(f)

# Group records by Teacher
teacher_map = {}
for r in records:
    tchr = r.get("teacher") or "Unassigned / To Confirm"
    if tchr not in teacher_map:
        teacher_map[tchr] = {
            "teacher": tchr,
            "total_exams": 0,
            "subjects": set(),
            "grades": set(),
            "sections": set(),
            "modalities": set(),
            "shifts": set(),
            "exams": []
        }
    teacher_map[tchr]["total_exams"] += 1
    if r.get("subject"):
        teacher_map[tchr]["subjects"].add(r.get("subject"))
    if r.get("grade"):
        teacher_map[tchr]["grades"].add(r.get("grade"))
    if r.get("section"):
        teacher_map[tchr]["sections"].add(f"{r.get('grade')} — {r.get('section')}")
    if r.get("modality"):
        teacher_map[tchr]["modalities"].add(r.get("modality"))
    if r.get("shift"):
        teacher_map[tchr]["shifts"].add(r.get("shift"))
    teacher_map[tchr]["exams"].append(r)

# Convert sets to sorted lists for serialization
teacher_summary = []
for tchr, data in sorted(teacher_map.items(), key=lambda x: x[0].lower()):
    teacher_summary.append({
        "teacher": tchr,
        "total_exams": data["total_exams"],
        "subjects": sorted(list(data["subjects"])),
        "grades": sorted(list(data["grades"])),
        "sections_count": len(data["sections"]),
        "sections": sorted(list(data["sections"])),
        "modalities": sorted(list(data["modalities"])),
        "shifts": sorted(list(data["shifts"])),
        "exams": sorted(data["exams"], key=lambda e: (e.get("date", ""), e.get("time", "")))
    })

# Save JSON
with open(os.path.join(BASE_DIR, "teacher_subject_tracking.json"), "w", encoding="utf-8") as f:
    json.dump(teacher_summary, f, indent=2)

# Write Detailed CSV
csv_paths = [
    os.path.join(BASE_DIR, "AMIS_Teacher_Exam_Subject_Assignments.csv"),
    "/home/tatsuya/Downloads/AMIS_Teacher_Exam_Subject_Assignments.csv"
]

for p in csv_paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Teacher Name",
            "Total Exam Load",
            "Assigned Subject",
            "Grade Level",
            "Section",
            "Gender",
            "Modality",
            "Shift",
            "Examination Date",
            "Examination Time",
            "Room",
            "Status"
        ])
        
        for t in teacher_summary:
            for ex in t["exams"]:
                writer.writerow([
                    t["teacher"],
                    t["total_exams"],
                    ex.get("subject", ""),
                    ex.get("grade", ""),
                    ex.get("section", ""),
                    ex.get("gender", ""),
                    ex.get("modality", ""),
                    ex.get("shift", ""),
                    ex.get("date", ""),
                    ex.get("time", ""),
                    ex.get("room", ""),
                    ex.get("status", "OK")
                ])

print(f"Generated Teacher-Subject Tracking for {len(teacher_summary)} teachers across {len(records)} exams.")
print(f"Saved CSV to: {csv_paths[1]}")
