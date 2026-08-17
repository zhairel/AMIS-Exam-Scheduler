#!/usr/bin/env python3
"""
AMIS Examination Calendar Maker - Automated High-Resolution Grade Calendar JPG Generator
Generates clean, printable, visual JPG calendars for every Grade Level.
"""

import os
import json
import subprocess
import urllib.parse
from PIL import Image

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"
OUT_DIRS = [
    os.path.join(BASE_DIR, "calendars"),
    "/home/tatsuya/Downloads/AMIS_Grade_Calendars_JPG"
]

for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

data_path = os.path.join(BASE_DIR, "exam_data.json")
if not os.path.exists(data_path):
    print("Error: exam_data.json not found.")
    exit(1)

with open(data_path, "r", encoding="utf-8") as f:
    records = json.load(f)

# Extract unique grades
grades = sorted(list(set(r.get("grade") for r in records if r.get("grade"))), key=lambda x: (x.replace("Grade ", "").replace("Kinder ", "0"), x))

print(f"Generating JPG calendars for {len(grades)} Grade Levels...")

temp_dir = "/tmp/amis_cal_gen"
os.makedirs(temp_dir, exist_ok=True)
os.makedirs("/tmp/ff_profile", exist_ok=True)

generated_files = []

for grade in grades:
    safe_name = grade.replace(" ", "_").replace("&", "and")
    png_path = os.path.join(temp_dir, f"{safe_name}.png")
    jpg_name = f"AMIS_{safe_name}_Exam_Calendar.jpg"
    
    grade_exams = [r for r in records if r.get("grade") == grade]
    unique_times = set(r.get("time") for r in grade_exams)
    has_f2f = any(r.get("modality") == "F2F" for r in grade_exams)
    
    total_rows = len(unique_times) + (3 if has_f2f else 0)
    
    # Dynamic height: header (240px) + total rows * 115px + footer/padding (160px)
    win_height = max(920, min(3200, 260 + (total_rows * 118) + 120))
    
    url = f"http://localhost:3000/grade-calendar-view.html?grade={urllib.parse.quote(grade)}&nobar=1"
    
    cmd = [
        "firefox", "--headless",
        "--profile", "/tmp/ff_profile",
        "--screenshot", png_path,
        f"--window-size=1420,{win_height}",
        url
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(png_path):
            img = Image.open(png_path).convert("RGB")
            
            for d in OUT_DIRS:
                out_path = os.path.join(d, jpg_name)
                img.save(out_path, "JPEG", quality=95, optimize=True)
            
            file_size_kb = round(os.path.getsize(os.path.join(OUT_DIRS[0], jpg_name)) / 1024)
            print(f"Generated: {jpg_name} ({file_size_kb} KB, {img.size[0]}x{img.size[1]}px)")
            generated_files.append(jpg_name)
    except Exception as e:
        print(f"Error generating {grade}: {e}")

print(f"\nAll {len(generated_files)} Grade JPG Calendars successfully generated!")
print(f"Saved to:")
for d in OUT_DIRS:
    print(f" - {d}")
