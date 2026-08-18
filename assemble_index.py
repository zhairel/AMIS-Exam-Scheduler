#!/usr/bin/env python3
import os
import subprocess

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

# Run generate_exam_schedule_page.py to assemble exam-schedule.html with unified design system
subprocess.run(["python3", os.path.join(BASE_DIR, "generate_exam_schedule_page.py")], check=True)

print("✓ Assembled official portals and exam-schedule.html successfully!")
