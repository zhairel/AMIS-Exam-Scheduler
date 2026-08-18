#!/usr/bin/env python3
"""
Canonical V4 AMIS Class & Exam Dataset Builder
Sources of Truth:
  1. ELEM: Kinder to Grade 6 (all rows)
  2. HS SCHED (NEW): Grade 7 to Grade 10 ONLY (Regions: F2F B1:H68, 1st Shift K1:Q62, 2nd Shift S1:Y75)
  3. SHS: Grade 11 to Grade 12 FIRST TERM ONLY (Rows 1:46)
"""

import json, re, os, datetime
import openpyxl

EXCEL_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/SCHEDULE SY 2026-2027 TW.xlsx'
OUTPUT_V4_JSON = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/AMIS_CLASS_DATASET_CANONICAL_LATEST_V4.json'
CLASS_DATA_JSON = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json'
CLASS_DATA_JS = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.js'
EXAM_DATA_JSON = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json'
EXAM_DATA_JS = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.js'
TEACHER_WEEKLY_JSON = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.json'
TEACHER_WEEKLY_JS = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.js'
AUDIT_LOG_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/canonical_v4_teacher_audit.txt'

wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

# Build Raw V4 JSON representation
v4_meta = {
    "type": "AMIS_CLASS_DATASET_CANONICAL_LATEST_V4",
    "schema_version": 4,
    "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "source_file": "SCHEDULE SY 2026-2027 TW.xlsx",
    "purpose": "Canonical AMIS class dataset with G11-12 overlap removed from HS SCHED (NEW)."
}

# Define Section Bounds
SECTION_DEFINITIONS = [
    # --- ELEM (Kinder to Grade 6) ---
    # Kinder 2 F2F
    {"sheet": "ELEM", "header_cell": "B3", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 5, "end_row": 12, "shift": "F2F", "grade": "Kinder 2", "dept": "Elementary"},
    # Kinder 2 Abu Bakr (1st Shift)
    {"sheet": "ELEM", "header_cell": "J3", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 5, "end_row": 11, "shift": "ODL - 1ST SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    # Kinder 2 Uthman (1st Shift)
    {"sheet": "ELEM", "header_cell": "R3", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 5, "end_row": 11, "shift": "ODL - 1ST SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    # K2 - Abdullah Ibn Mas'ud (2nd Shift)
    {"sheet": "ELEM", "header_cell": "Z3", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 5, "end_row": 11, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    # K2 - Umar Ibn Al-Khattab (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AH3", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 5, "end_row": 11, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    # K2 - Khabaab Ibn Arat (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AH13", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 15, "end_row": 21, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    # K1 - Husain Ibn Ali (2nd Shift)
    {"sheet": "ELEM", "header_cell": "Z13", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 15, "end_row": 21, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 1", "dept": "Elementary"},
    # Kinder 1 F2F
    {"sheet": "ELEM", "header_cell": "B14", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 16, "end_row": 21, "shift": "F2F", "grade": "Kinder 1", "dept": "Elementary"},
    # Kinder 1 Hasan Ibn Ali (1st Shift)
    {"sheet": "ELEM", "header_cell": "J14", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 16, "end_row": 21, "shift": "ODL - 1ST SHIFT", "grade": "Kinder 1", "dept": "Elementary"},

    # Grade 1 F2F
    {"sheet": "ELEM", "header_cell": "B24", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 26, "end_row": 37, "shift": "F2F", "grade": "Grade 1", "dept": "Elementary"},
    # Grade 1 Hudhayfah (1st Shift)
    {"sheet": "ELEM", "header_cell": "J24", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 26, "end_row": 32, "shift": "ODL - 1ST SHIFT", "grade": "Grade 1", "dept": "Elementary"},
    # Grade 1 Ali Ibn Abi Talib (1st Shift)
    {"sheet": "ELEM", "header_cell": "R24", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 26, "end_row": 32, "shift": "ODL - 1ST SHIFT", "grade": "Grade 1", "dept": "Elementary"},
    # Grade 1 Suhayb Ar-Rumi (2nd Shift)
    {"sheet": "ELEM", "header_cell": "Z24", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 26, "end_row": 32, "shift": "ODL - 2ND SHIFT", "grade": "Grade 1", "dept": "Elementary"},
    # Grade 1 Sa'ad Ibn Abi Waqqaas (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AH24", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 26, "end_row": 32, "shift": "ODL - 2ND SHIFT", "grade": "Grade 1", "dept": "Elementary"},

    # Grade 2 F2F
    {"sheet": "ELEM", "header_cell": "B39", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 41, "end_row": 52, "shift": "F2F", "grade": "Grade 2", "dept": "Elementary"},
    # Grade 2 Talha (1st Shift)
    {"sheet": "ELEM", "header_cell": "J39", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 41, "end_row": 47, "shift": "ODL - 1ST SHIFT", "grade": "Grade 2", "dept": "Elementary"},
    # Grade 2 Amr Ibn Al-Jamuh (1st Shift)
    {"sheet": "ELEM", "header_cell": "R39", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 41, "end_row": 47, "shift": "ODL - 1ST SHIFT", "grade": "Grade 2", "dept": "Elementary"},
    # Grade 2 Saeed Ibn Zayd (2nd Shift)
    {"sheet": "ELEM", "header_cell": "Z39", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 41, "end_row": 47, "shift": "ODL - 2ND SHIFT", "grade": "Grade 2", "dept": "Elementary"},
    # Grade 2 Aasim Ibn Thabit (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AH39", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 41, "end_row": 47, "shift": "ODL - 2ND SHIFT", "grade": "Grade 2", "dept": "Elementary"},

    # Grade 3 F2F
    {"sheet": "ELEM", "header_cell": "B54", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 56, "end_row": 67, "shift": "F2F", "grade": "Grade 3", "dept": "Elementary"},
    # Grade 3 Habib (1st Shift Girls)
    {"sheet": "ELEM", "header_cell": "J54", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 56, "end_row": 62, "shift": "ODL - 1ST SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    # Grade 3 Ammar (1st Shift Boys)
    {"sheet": "ELEM", "header_cell": "R54", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 56, "end_row": 62, "shift": "ODL - 1ST SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    # Grade 3 Salman Al Farsi (1st Shift Mix)
    {"sheet": "ELEM", "header_cell": "R64", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 66, "end_row": 72, "shift": "ODL - 1ST SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    # Grade 3 Zayd Ibn Haritha (2nd Shift Girls)
    {"sheet": "ELEM", "header_cell": "Z54", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 56, "end_row": 62, "shift": "ODL - 2ND SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    # Grade 3 Thabit Ibn Qays (2nd Shift Boys)
    {"sheet": "ELEM", "header_cell": "AH54", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 56, "end_row": 62, "shift": "ODL - 2ND SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    # Grade 3 As'ad Ibn Zurarah (2nd Shift Mix)
    {"sheet": "ELEM", "header_cell": "AH64", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 66, "end_row": 72, "shift": "ODL - 2ND SHIFT", "grade": "Grade 3", "dept": "Elementary"},

    # Grade 4 F2F
    {"sheet": "ELEM", "header_cell": "B74", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 76, "end_row": 87, "shift": "F2F", "grade": "Grade 4", "dept": "Elementary"},
    # Grade 4 Abdur Rahman (1st Shift)
    {"sheet": "ELEM", "header_cell": "J74", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 76, "end_row": 82, "shift": "ODL - 1ST SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    # Grade 4 Hakim Ibn Hazm (1st Shift)
    {"sheet": "ELEM", "header_cell": "R74", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 76, "end_row": 82, "shift": "ODL - 1ST SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    # Grade 4 Usayd Ibn Hudhayr (1st Shift Mix)
    {"sheet": "ELEM", "header_cell": "J64", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 66, "end_row": 72, "shift": "ODL - 1ST SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    # Grade 4 Az Zubair (2nd Shift)
    {"sheet": "ELEM", "header_cell": "Z74", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 76, "end_row": 82, "shift": "ODL - 2ND SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    # Grade 4 Ikrimah (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AH74", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 76, "end_row": 82, "shift": "ODL - 2ND SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    # Grade 4 Hassan Ibn Thabit (2nd Shift Mix)
    {"sheet": "ELEM", "header_cell": "AP74", "time_col": 42, "min_col": 43, "day_cols": [44,45,46,47,48], "start_row": 76, "end_row": 82, "shift": "ODL - 2ND SHIFT", "grade": "Grade 4", "dept": "Elementary"},

    # Grade 5 F2F
    {"sheet": "ELEM", "header_cell": "B89", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 91, "end_row": 102, "shift": "F2F", "grade": "Grade 5", "dept": "Elementary"},
    # Grade 5 Hamza (1st Shift)
    {"sheet": "ELEM", "header_cell": "J89", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 91, "end_row": 97, "shift": "ODL - 1ST SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    # Grade 5 Muhammad Ibn Maslamah (1st Shift)
    {"sheet": "ELEM", "header_cell": "R89", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 91, "end_row": 97, "shift": "ODL - 1ST SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    # Grade 5 Ayyash (1st Shift)
    {"sheet": "ELEM", "header_cell": "Z89", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 91, "end_row": 97, "shift": "ODL - 1ST SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    # Grade 5 Mus'ab (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AH89", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 91, "end_row": 97, "shift": "ODL - 2ND SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    # Grade 5 Al Harith (2nd Shift)
    {"sheet": "ELEM", "header_cell": "AP89", "time_col": 42, "min_col": 43, "day_cols": [44,45,46,47,48], "start_row": 91, "end_row": 97, "shift": "ODL - 2ND SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    # Grade 5 Ja'far (2nd Shift Mix)
    {"sheet": "ELEM", "header_cell": "AX89", "time_col": 50, "min_col": 51, "day_cols": [52,53,54,55,56], "start_row": 91, "end_row": 97, "shift": "ODL - 2ND SHIFT", "grade": "Grade 5", "dept": "Elementary"},

    # Grade 6 F2F
    {"sheet": "ELEM", "header_cell": "B104", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 106, "end_row": 117, "shift": "F2F", "grade": "Grade 6", "dept": "Elementary"},
    # Grade 6 Abdullah Ibn Salaam (1st Shift)
    {"sheet": "ELEM", "header_cell": "J104", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 106, "end_row": 112, "shift": "ODL - 1ST SHIFT", "grade": "Grade 6", "dept": "Elementary"},
    # Grade 6 Abbas (1st Shift)
    {"sheet": "ELEM", "header_cell": "R104", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 106, "end_row": 112, "shift": "ODL - 1ST SHIFT", "grade": "Grade 6", "dept": "Elementary"},
    # Grade 6 Khaleed Ibn Waleed (2nd Shift)
    {"sheet": "ELEM", "header_cell": "Z104", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 106, "end_row": 112, "shift": "ODL - 2ND SHIFT", "grade": "Grade 6", "dept": "Elementary"},
    # Grade 6 Dihya (2nd Shift Girls)
    {"sheet": "ELEM", "header_cell": "AH104", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 106, "end_row": 112, "shift": "ODL - 2ND SHIFT", "grade": "Grade 6", "dept": "Elementary"},

    # --- HS SCHED (NEW) (Grade 7 to Grade 10 ONLY) ---
    # Grade 7 & 8 Girls F2F
    {"sheet": "HS SCHED (NEW)", "header_cell": "B5", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 7, "end_row": 18, "shift": "F2F", "grade": "Grade 7 & 8", "dept": "Junior High School"},
    # Grade 7 & 8 Boys F2F
    {"sheet": "HS SCHED (NEW)", "header_cell": "B21", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 23, "end_row": 34, "shift": "F2F", "grade": "Grade 7 & 8", "dept": "Junior High School"},
    # Grade 9 & 10 Girls F2F
    {"sheet": "HS SCHED (NEW)", "header_cell": "B37", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 39, "end_row": 50, "shift": "F2F", "grade": "Grade 9 & 10", "dept": "Junior High School"},
    # Grade 9 & 10 Boys F2F
    {"sheet": "HS SCHED (NEW)", "header_cell": "B53", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 55, "end_row": 66, "shift": "F2F", "grade": "Grade 9 & 10", "dept": "Junior High School"},

    # Grade 7 Usama (1st Shift Girls)
    {"sheet": "HS SCHED (NEW)", "header_cell": "K5", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 7, "end_row": 13, "shift": "ODL - 1ST SHIFT", "grade": "Grade 7", "dept": "Junior High School"},
    # Grade 7 Abu Sufyan (1st Shift Boys)
    {"sheet": "HS SCHED (NEW)", "header_cell": "K16", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 18, "end_row": 24, "shift": "ODL - 1ST SHIFT", "grade": "Grade 7", "dept": "Junior High School"},
    # Grade 8 Sa'ad (1st Shift Girls)
    {"sheet": "HS SCHED (NEW)", "header_cell": "K28", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 30, "end_row": 36, "shift": "ODL - 1ST SHIFT", "grade": "Grade 8", "dept": "Junior High School"},
    # Grade 9 Abu Hurayrah (1st Shift Girls)
    {"sheet": "HS SCHED (NEW)", "header_cell": "K40", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 42, "end_row": 48, "shift": "ODL - 1ST SHIFT", "grade": "Grade 9", "dept": "Junior High School"},
    # Grade 10 Utbah (1st Shift Girls)
    {"sheet": "HS SCHED (NEW)", "header_cell": "K52", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 54, "end_row": 60, "shift": "ODL - 1ST SHIFT", "grade": "Grade 10", "dept": "Junior High School"},

    # Grade 7 Anas (2nd Shift Mix)
    {"sheet": "HS SCHED (NEW)", "header_cell": "S5", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 7, "end_row": 13, "shift": "ODL - 2ND SHIFT", "grade": "Grade 7", "dept": "Junior High School"},
    # Grade 8 Mu'adh (2nd Shift Boys)
    {"sheet": "HS SCHED (NEW)", "header_cell": "S16", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 18, "end_row": 24, "shift": "ODL - 2ND SHIFT", "grade": "Grade 8", "dept": "Junior High School"},
    # Grade 8 Nuaym (2nd Shift Mix)
    {"sheet": "HS SCHED (NEW)", "header_cell": "S28", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 30, "end_row": 36, "shift": "ODL - 2ND SHIFT", "grade": "Grade 8", "dept": "Junior High School"},
    # Grade 9 Abu Dharr (2nd Shift Boys)
    {"sheet": "HS SCHED (NEW)", "header_cell": "S40", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 42, "end_row": 48, "shift": "ODL - 2ND SHIFT", "grade": "Grade 9", "dept": "Junior High School"},
    # Grade 9 Abu Jandal (2nd Shift Girls)
    {"sheet": "HS SCHED (NEW)", "header_cell": "S51", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 53, "end_row": 59, "shift": "ODL - 2ND SHIFT", "grade": "Grade 9", "dept": "Junior High School"},
    # Grade 10 Abu Ayyub (2nd Shift Boys)
    {"sheet": "HS SCHED (NEW)", "header_cell": "S62", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 64, "end_row": 70, "shift": "ODL - 2ND SHIFT", "grade": "Grade 10", "dept": "Junior High School"},

    # --- SHS (Grade 11 & Grade 12 FIRST TERM ONLY, Rows 1:46) ---
    # Grade 11 F2F
    {"sheet": "SHS", "header_cell": "B4", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 6, "end_row": 17, "shift": "F2F", "grade": "Grade 11", "dept": "Senior High School"},
    # Grade 12 Suhayb Ar-Rumi (F2F)
    {"sheet": "SHS", "header_cell": "K4", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 6, "end_row": 17, "shift": "F2F", "grade": "Grade 12", "dept": "Senior High School"},
    # Grade 11 (1st Shift Girls)
    {"sheet": "SHS", "header_cell": "B20", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 22, "end_row": 30, "shift": "ODL - 1ST SHIFT", "grade": "Grade 11", "dept": "Senior High School"},
    # Grade 12 Abu Musa (1st Shift)
    {"sheet": "SHS", "header_cell": "K20", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 22, "end_row": 30, "shift": "ODL - 1ST SHIFT", "grade": "Grade 12", "dept": "Senior High School"},
    # Grade 11 (2nd Shift Boys)
    {"sheet": "SHS", "header_cell": "B33", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 35, "end_row": 42, "shift": "ODL - 2ND SHIFT", "grade": "Grade 11", "dept": "Senior High School"}
]

print(f"Total Canonical Section Definitions: {len(SECTION_DEFINITIONS)}")
