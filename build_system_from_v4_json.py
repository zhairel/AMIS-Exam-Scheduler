#!/usr/bin/env python3
"""
Complete System Rebuild Strictly from AMIS_CLASS_DATASET_CANONICAL_LATEST_V4.json
Zero dependence on old databases or stale registries.
"""

import json, re, os, datetime

BASE_DIR = '/home/tatsuya/Projects/AMIS/amis_exam_calendar'
V4_JSON_PATH = os.path.join(BASE_DIR, 'AMIS_CLASS_DATASET_CANONICAL_LATEST_V4.json')
CLASS_DATA_JSON = os.path.join(BASE_DIR, 'class_schedules_data.json')
CLASS_DATA_JS = os.path.join(BASE_DIR, 'class_schedules_data.js')
EXAM_DATA_JSON = os.path.join(BASE_DIR, 'exam_data.json')
EXAM_DATA_JS = os.path.join(BASE_DIR, 'exam_data.js')
OPTIONS_EXAM_DATA_JSON = os.path.join(BASE_DIR, 'options_exam_data.json')
TEACHER_WEEKLY_JSON = os.path.join(BASE_DIR, 'teacher_weekly_schedules.json')
TEACHER_WEEKLY_JS = os.path.join(BASE_DIR, 'teacher_weekly_schedules.js')
AUDIT_TXT = os.path.join(BASE_DIR, 'canonical_v4_teacher_audit.txt')

with open(V4_JSON_PATH, 'r', encoding='utf-8') as f:
    v4_data = json.load(f)

DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

def col2num(col):
    num = 0
    for c in col:
        num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num

def num2col(num):
    col = ""
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        col = chr(65 + remainder) + col
    return col

sheets_by_name = {s['sheet_name']: s for s in v4_data.get('sheets', [])}

def get_v4_cell(sheet_name, cell_ref):
    sheet = sheets_by_name.get(sheet_name)
    if not sheet: return ""
    cell = sheet.get('cells', {}).get(cell_ref)
    if not cell: return ""
    v = cell.get('value')
    return str(v).strip() if v is not None else ""

SECTION_DEFS = [
    # --- ELEM (Kinder to Grade 6) ---
    {"sheet": "ELEM", "header_cell": "B3", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 5, "end_row": 12, "shift": "F2F", "grade": "Kinder 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J3", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 5, "end_row": 11, "shift": "ODL - 1ST SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R3", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 5, "end_row": 11, "shift": "ODL - 1ST SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z3", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 5, "end_row": 11, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH3", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 5, "end_row": 11, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH13", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 15, "end_row": 21, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z13", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 15, "end_row": 21, "shift": "ODL - 2ND SHIFT", "grade": "Kinder 1", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "B14", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 16, "end_row": 21, "shift": "F2F", "grade": "Kinder 1", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J14", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 16, "end_row": 21, "shift": "ODL - 1ST SHIFT", "grade": "Kinder 1", "dept": "Elementary"},

    {"sheet": "ELEM", "header_cell": "B24", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 26, "end_row": 37, "shift": "F2F", "grade": "Grade 1", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J24", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 26, "end_row": 32, "shift": "ODL - 1ST SHIFT", "grade": "Grade 1", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R24", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 26, "end_row": 32, "shift": "ODL - 1ST SHIFT", "grade": "Grade 1", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z24", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 26, "end_row": 32, "shift": "ODL - 2ND SHIFT", "grade": "Grade 1", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH24", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 26, "end_row": 32, "shift": "ODL - 2ND SHIFT", "grade": "Grade 1", "dept": "Elementary"},

    {"sheet": "ELEM", "header_cell": "B39", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 41, "end_row": 52, "shift": "F2F", "grade": "Grade 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J39", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 41, "end_row": 47, "shift": "ODL - 1ST SHIFT", "grade": "Grade 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R39", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 41, "end_row": 47, "shift": "ODL - 1ST SHIFT", "grade": "Grade 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z39", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 41, "end_row": 47, "shift": "ODL - 2ND SHIFT", "grade": "Grade 2", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH39", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 41, "end_row": 47, "shift": "ODL - 2ND SHIFT", "grade": "Grade 2", "dept": "Elementary"},

    {"sheet": "ELEM", "header_cell": "B54", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 56, "end_row": 67, "shift": "F2F", "grade": "Grade 3", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J54", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 56, "end_row": 62, "shift": "ODL - 1ST SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R54", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 56, "end_row": 62, "shift": "ODL - 1ST SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R64", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 66, "end_row": 72, "shift": "ODL - 1ST SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z54", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 56, "end_row": 62, "shift": "ODL - 2ND SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH54", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 56, "end_row": 62, "shift": "ODL - 2ND SHIFT", "grade": "Grade 3", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH64", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 66, "end_row": 72, "shift": "ODL - 2ND SHIFT", "grade": "Grade 3", "dept": "Elementary"},

    {"sheet": "ELEM", "header_cell": "B74", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 76, "end_row": 87, "shift": "F2F", "grade": "Grade 4", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J74", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 76, "end_row": 82, "shift": "ODL - 1ST SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R74", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 76, "end_row": 82, "shift": "ODL - 1ST SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J64", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 66, "end_row": 72, "shift": "ODL - 1ST SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z74", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 76, "end_row": 82, "shift": "ODL - 2ND SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH74", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 76, "end_row": 82, "shift": "ODL - 2ND SHIFT", "grade": "Grade 4", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AP74", "time_col": 42, "min_col": 43, "day_cols": [44,45,46,47,48], "start_row": 76, "end_row": 82, "shift": "ODL - 2ND SHIFT", "grade": "Grade 4", "dept": "Elementary"},

    {"sheet": "ELEM", "header_cell": "B89", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 91, "end_row": 102, "shift": "F2F", "grade": "Grade 5", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J89", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 91, "end_row": 97, "shift": "ODL - 1ST SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R89", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 91, "end_row": 97, "shift": "ODL - 1ST SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z89", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 91, "end_row": 97, "shift": "ODL - 1ST SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH89", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 91, "end_row": 97, "shift": "ODL - 2ND SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AP89", "time_col": 42, "min_col": 43, "day_cols": [44,45,46,47,48], "start_row": 91, "end_row": 97, "shift": "ODL - 2ND SHIFT", "grade": "Grade 5", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AX89", "time_col": 50, "min_col": 51, "day_cols": [52,53,54,55,56], "start_row": 91, "end_row": 97, "shift": "ODL - 2ND SHIFT", "grade": "Grade 5", "dept": "Elementary"},

    {"sheet": "ELEM", "header_cell": "B104", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 106, "end_row": 117, "shift": "F2F", "grade": "Grade 6", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "J104", "time_col": 10, "min_col": 11, "day_cols": [12,13,14,15,16], "start_row": 106, "end_row": 112, "shift": "ODL - 1ST SHIFT", "grade": "Grade 6", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "R104", "time_col": 18, "min_col": 19, "day_cols": [20,21,22,23,24], "start_row": 106, "end_row": 112, "shift": "ODL - 1ST SHIFT", "grade": "Grade 6", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "Z104", "time_col": 26, "min_col": 27, "day_cols": [28,29,30,31,32], "start_row": 106, "end_row": 112, "shift": "ODL - 2ND SHIFT", "grade": "Grade 6", "dept": "Elementary"},
    {"sheet": "ELEM", "header_cell": "AH104", "time_col": 34, "min_col": 35, "day_cols": [36,37,38,39,40], "start_row": 106, "end_row": 112, "shift": "ODL - 2ND SHIFT", "grade": "Grade 6", "dept": "Elementary"},

    # --- HS SCHED (NEW) (Grade 7 to Grade 10 ONLY) ---
    {"sheet": "HS SCHED (NEW)", "header_cell": "B5", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 7, "end_row": 18, "shift": "F2F", "grade": "Grade 7 & 8", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "B21", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 23, "end_row": 34, "shift": "F2F", "grade": "Grade 7 & 8", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "B37", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 39, "end_row": 50, "shift": "F2F", "grade": "Grade 9 & 10", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "B53", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 55, "end_row": 66, "shift": "F2F", "grade": "Grade 9 & 10", "dept": "Junior High School"},

    {"sheet": "HS SCHED (NEW)", "header_cell": "K5", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 7, "end_row": 13, "shift": "ODL - 1ST SHIFT", "grade": "Grade 7", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "K16", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 18, "end_row": 24, "shift": "ODL - 1ST SHIFT", "grade": "Grade 7", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "K28", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 30, "end_row": 36, "shift": "ODL - 1ST SHIFT", "grade": "Grade 8", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "K40", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 42, "end_row": 48, "shift": "ODL - 1ST SHIFT", "grade": "Grade 9", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "K52", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 54, "end_row": 60, "shift": "ODL - 1ST SHIFT", "grade": "Grade 10", "dept": "Junior High School"},

    {"sheet": "HS SCHED (NEW)", "header_cell": "S5", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 7, "end_row": 13, "shift": "ODL - 2ND SHIFT", "grade": "Grade 7", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "S16", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 18, "end_row": 24, "shift": "ODL - 2ND SHIFT", "grade": "Grade 8", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "S28", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 30, "end_row": 36, "shift": "ODL - 2ND SHIFT", "grade": "Grade 8", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "S40", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 42, "end_row": 48, "shift": "ODL - 2ND SHIFT", "grade": "Grade 9", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "S51", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 53, "end_row": 59, "shift": "ODL - 2ND SHIFT", "grade": "Grade 9", "dept": "Junior High School"},
    {"sheet": "HS SCHED (NEW)", "header_cell": "S62", "time_col": 19, "min_col": 20, "day_cols": [21,22,23,24,25], "start_row": 64, "end_row": 70, "shift": "ODL - 2ND SHIFT", "grade": "Grade 10", "dept": "Junior High School"},

    # --- SHS (Grade 11 & Grade 12 FIRST TERM ONLY, Rows 1:46) ---
    {"sheet": "SHS", "header_cell": "B4", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 6, "end_row": 17, "shift": "F2F", "grade": "Grade 11", "dept": "Senior High School"},
    {"sheet": "SHS", "header_cell": "K4", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 6, "end_row": 17, "shift": "F2F", "grade": "Grade 12", "dept": "Senior High School"},
    {"sheet": "SHS", "header_cell": "B20", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 22, "end_row": 30, "shift": "ODL - 1ST SHIFT", "grade": "Grade 11", "dept": "Senior High School"},
    {"sheet": "SHS", "header_cell": "K20", "time_col": 11, "min_col": 12, "day_cols": [13,14,15,16,17], "start_row": 22, "end_row": 30, "shift": "ODL - 1ST SHIFT", "grade": "Grade 12", "dept": "Senior High School"},
    {"sheet": "SHS", "header_cell": "B33", "time_col": 2, "min_col": 3, "day_cols": [4,5,6,7,8], "start_row": 35, "end_row": 42, "shift": "ODL - 2ND SHIFT", "grade": "Grade 11", "dept": "Senior High School"}
]

BREAK_KEYWORDS = [
    'GENERAL ASSEMBLY', 'RECESS', 'TRANSITION', 'LUNCH AND SALAH', 
    'SALAH & DEPARTURE', 'DEPARTURE', 'SHORT BREAK', 'BREAK', 'SALAH', 
    'HOMEROOM GUIDANCE', 'HOMEROOM', 'DISMISSAL', 'HOMEROOM GUIDANCE/ARAL PROGRAM',
    'HOMEROOM GUIDANCE/ARAL MATH', 'QUR\'AN READING (GENERAL ASSEMBLY)'
]

def is_break_text(s):
    if not s: return True
    s_upper = s.strip().upper()
    return any(b in s_upper for b in BREAK_KEYWORDS)

def split_subject_teacher(cell_str):
    if not cell_str:
        return "", ""
    s = str(cell_str).strip()
    if is_break_text(s):
        return s, ""
    
    parts = s.split(' - ')
    if len(parts) >= 2:
        subj = parts[0].strip()
        tchr = ' - '.join(parts[1:]).strip()
        return subj, tchr
    
    if '-' in s:
        p = s.split('-')
        subj = p[0].strip()
        tchr = '-'.join(p[1:]).strip()
        return subj, tchr
        
    return s, ""

TEACHER_NAME_NORMALIZATION = {
    'FHAIRUDZ': 'Fhairudz',
    'FAIRUDZ': 'Fhairudz',
    'FAIRUZD': 'Fhairudz',
    'JUNAISA': 'Junaisa',
    'JUNAISAH': 'Junaisa',
    'KAT': 'Katrina',
    'KATRINA': 'Katrina',
    'NORMAYLA': 'Normylah',
    'NORMYLAH': 'Normylah',
    'WENDELYN': 'Wendy',
    'WENDY': 'Wendy',
    'SHI': 'Shirehan',
    'SHIREHAN': 'Shirehan',
    'RADZMIA+': 'Radzmia',
    'RADZMIA': 'Radzmia',
    'MAMONAS': 'Mamonas',
    'ALIM MAMONAS': 'Mamonas',
    'DIPATUAN': 'Dipatuan',
    'ALIM DIPATUAN': 'Dipatuan',
    'SAMSUDDIN': 'Samsuddin',
    'ALIM SAMSUDDIN': 'Samsuddin',
    'ABDULWAHAB': 'Abdulwahab',
    'ALIM ABDULWAHAB': 'Abdulwahab',
    'ABDUL KARIM': 'Abdul Karim',
    'ALIM ABDUL KARIM': 'Abdul Karim',
    'BUSTAMANTE': 'Bustamante',
    'ALIM BUSTAMANTE': 'Bustamante',
    'MOH': 'Moh',
    'SIR MOH': 'Moh',
    'ABDI': 'Abdiraheem',
    'UST. ABDI': 'Abdiraheem',
    'ABDIRAHEEM': 'Abdiraheem',
    'UST. ABDIRAHEEM': 'Abdiraheem',
    'ALI': 'Muh Ali',
    'UST. ALI': 'Muh Ali',
    'USTADH ALI': 'Muh Ali',
    'USTADH MUH ALI': 'Muh Ali',
    'UST ALI': 'Muh Ali',
    'FAIDH': 'Faidh',
    'UST. FAIDH': 'Faidh',
    'USTADH FAIDH': 'Faidh',
    'US. FAIDH': 'Faidh',
    'UST.FAIDH': 'Faidh',
    'HAINUR': 'Hainur',
    'UST. HAINUR': 'Hainur',
    'UST.HAINUR': 'Hainur',
    'JAISAM': 'Jaisam',
    'UST. JAISAM': 'Jaisam',
    'USTADH JAISAM': 'Jaisam',
    'OBAYDA': 'Obaydah',
    'OBAYDAH': 'Obaydah',
    'UST. OBAYDA': 'Obaydah',
    'UST. OBAYDAH': 'Obaydah',
    'UBAYDAH': 'Obaydah',
    'UST. UBAYDAH': 'Obaydah',
    'RASLINA': 'Raslina',
    'UST. RASLINA': 'Raslina',
    'SALIHA': 'Saliha',
    'UST. SALIHA': 'Saliha',
    'USTADHA SALIHA': 'Saliha',
    'A SALIHA': 'Saliha',
    'UST. A SALIHA': 'Saliha',
    'TEACHER A SALIHA': 'Saliha',
    'SILFA': 'Silfah',
    'SILFAH': 'Silfah',
    'UST. SILFAH': 'Silfah',
    'USTADHA SILFA': 'Silfah',
    'A SILFA': 'Silfah',
    'A SILFAH': 'Silfah',
    'UST. A SILFA': 'Silfah',
    'TEACHER A SILFA': 'Silfah',
    'ERSAHAD': 'Ersahad',
    'UST. ERSAHAD': 'Ersahad'
}

# Canonical display names: maps clean last-name → full title + name as it appears in original records
# Ustadh = male Islamic scholar, Ustadha = female Islamic scholar, Alim = Islamic scholar (senior)
# Sir = informal male title, Teacher = general/secular teacher
CANONICAL_DISPLAY_NAMES = {
    # Alim – senior Islamic scholars (HS / SHS Quran / Islamic Studies)
    'Abdul Karim': 'Alim Abdul Karim',
    'Abdulwahab':  'Alim Abdulwahab',
    'Samsuddin':   'Alim Samsuddin',
    'Mamonas':     'Alim Mamonas',
    'Dipatuan':    'Alim Dipatuan',
    'Bustamante':  'Alim Bustamante',
    # Sir
    'Moh':         'Sir Moh',
    # Ustadh (male)
    'Abdiraheem':  'Ustadh Abdiraheem',
    'Muh Ali':     'Ustadh Muh Ali',
    'Faidh':       'Ustadh Faidh',
    'Jaisam':      'Ustadh Jaisam',
    'Obaydah':     'Ustadh Obaydah',
    'Ersahad':     'Ustadh Ersahad',
    # Ustadha (female)
    'Hainur':      'Ustadha Hainur',
    'Saliha':      'Ustadha Saliha',
    'Silfah':      'Ustadha Silfah',
    'Raslina':     'Ustadha Raslina',
    # All other staff → Teacher prefix
}

def get_display_name(clean_t):
    """Return the proper title-prefixed display name for a canonical clean name."""
    if not clean_t:
        return ''
    return CANONICAL_DISPLAY_NAMES.get(clean_t, f'Teacher {clean_t}')


def clean_teacher_name(tname):
    if not tname: return ""
    t = str(tname).strip()
    t = re.sub(r'^(Tchr\.?|Teacher|Ustadh|Ustadha|Ust\.?|Alim|Sir|Tr\.)\s*', '', t, flags=re.IGNORECASE).strip()
    t_upper = t.upper()
    if t_upper in TEACHER_NAME_NORMALIZATION:
        return TEACHER_NAME_NORMALIZATION[t_upper]
    return t.title()

def clean_subject_code(s):
    if not s: return ""
    s = str(s).strip()
    s = re.sub(r'([a-zA-Z\']+)(\d+)$', r'\1', s).strip()
    return s.upper()

def format_time_label(t):
    if not t: return ""
    t = str(t).strip()
    t = t.replace('a.m.', 'AM').replace('p.m.', 'PM').replace('a.m', 'AM').replace('p.m', 'PM')
    t = re.sub(r'\s*-\s*', ' – ', t)
    return t

def parse_time_point(tp, default_meridiem='AM'):
    tp = tp.strip().upper().replace('.', '')
    m = re.search(r'(AM|PM)', tp)
    meridiem = m.group(1) if m else default_meridiem
    tp = re.sub(r'[^\d:]', '', tp)
    parts = tp.split(':')
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    if meridiem == 'PM' and h != 12:
        h += 12
    elif meridiem == 'AM' and h == 12:
        h = 0
    return h * 60 + m

def parse_time_range(tr):
    if not tr: return None
    tr = tr.replace('–', '-').replace('—', '-')
    parts = tr.split('-')
    if len(parts) != 2: return None
    
    end_mer = 'PM' if 'PM' in parts[1].upper() else ('AM' if 'AM' in parts[1].upper() else 'AM')
    start_mer = 'PM' if 'PM' in parts[0].upper() else ('AM' if 'AM' in parts[0].upper() else end_mer)
    
    if '11:' in parts[0] and '12:' in parts[1] and end_mer == 'PM':
        start_mer = 'AM'
        
    start_min = parse_time_point(parts[0], start_mer)
    end_min = parse_time_point(parts[1], end_mer)
    return (start_min, end_min)

def get_subj_color(sname):
    s = (sname or '').lower()
    if any(k in s for k in ['arabic', 'qur', 'hadith', 'shaf', 'islamic']):
        return {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#6b21a8'}
    if any(k in s for k in ['gmrc', 'values', 'esp']):
        return {'bg': '#dcfce7', 'border': '#86efac', 'text': '#166534'}
    if any(k in s for k in ['math', 'calculus', 'statistics']):
        return {'bg': '#e0f2fe', 'border': '#7dd3fc', 'text': '#0369a1'}
    if any(k in s for k in ['sci', 'physics', 'bio', 'chem']):
        return {'bg': '#ccfbf1', 'border': '#5eead4', 'text': '#0f766e'}
    if any(k in s for k in ['eng', 'language', 'reading', 'literacy', 'oral', '21st', 'lit']):
        return {'bg': '#fef3c7', 'border': '#fde047', 'text': '#854d0e'}
    if any(k in s for k in ['fil', 'ap', 'araling', 'makabansa', 'soc', 'pskp', 'pilosopiya']):
        return {'bg': '#ffedd5', 'border': '#fdba74', 'text': '#9a3412'}
    if any(k in s for k in ['mapeh', 'pe', 'tle', 'mil', 'prac', 'lcs']):
        return {'bg': '#fae8ff', 'border': '#f0abfc', 'text': '#86198f'}
    return {'bg': '#f1f5f9', 'border': '#cbd5e1', 'text': '#334155'}

print("Building Canonical V4 Class Schedules...")
sections_dataset = []
audit_records = []
canonical_lookup = {}
active_teachers = {}

for sdef in SECTION_DEFS:
    hdr_val = get_v4_cell(sdef['sheet'], sdef['header_cell'])
    if not hdr_val:
        continue
    sec_name = hdr_val.strip()
    sec_id = 'sec_' + re.sub(r'[^a-zA-Z0-9]+', '_', sec_name).strip('_').lower()
    
    periods_list = []
    p_num = 1
    
    for r in range(sdef['start_row'], sdef['end_row'] + 1):
        t_col_letter = num2col(sdef['time_col'])
        m_col_letter = num2col(sdef['min_col'])
        
        time_val = get_v4_cell(sdef['sheet'], f"{t_col_letter}{r}")
        min_val = get_v4_cell(sdef['sheet'], f"{m_col_letter}{r}")
        if not time_val:
            continue
            
        time_str = format_time_label(time_val)
        min_str = min_val
        if min_str and not min_str.endswith('min.') and not min_str.endswith('m'):
            try:
                min_str = f"{int(float(min_str))} min."
            except:
                pass
                
        day_cells = {}
        row_subjects = []
        row_teachers = []
        is_break_row = False
        
        for idx, c in enumerate(sdef['day_cols']):
            dname = DAYS_OF_WEEK[idx]
            col_letter = num2col(c)
            cell_ref = f"{col_letter}{r}"
            c_val = get_v4_cell(sdef['sheet'], cell_ref)
            
            subj, tchr = split_subject_teacher(c_val)
            is_break_cell = is_break_text(subj)
            
            clean_t = clean_teacher_name(tchr)
            t_id = 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', clean_t).strip('_').lower() if clean_t else None
            
            day_cells[dname] = {
                "raw": c_val,
                "subject": subj,
                "teacher": get_display_name(clean_t) if clean_t else (tchr if tchr else None),
                "teacher_id": t_id,
                "is_break": is_break_cell,
                "label": subj if is_break_cell else None,
                "source_sheet": sdef['sheet'],
                "source_cell": cell_ref
            }
            
            if is_break_cell:
                is_break_row = True
            elif subj:
                row_subjects.append(subj)
                if tchr:
                    row_teachers.append(tchr)
                    
            if tchr and subj and not is_break_cell:
                c_subj = clean_subject_code(subj)
                rec = {
                    "teacher": tchr,
                    "teacher_clean": clean_t,
                    "teacher_id": t_id,
                    "section": sec_name,
                    "section_id": sec_id,
                    "subject": subj,
                    "subject_code": c_subj,
                    "source_sheet": sdef['sheet'],
                    "source_cell": f"{sdef['sheet']}!{cell_ref}",
                    "day": dname,
                    "time": time_str
                }
                audit_records.append(rec)
                
                canonical_lookup[(sec_id, c_subj)] = rec
                canonical_lookup[(sec_name.upper(), c_subj)] = rec
                canonical_lookup[(sec_id, subj.upper())] = rec
                canonical_lookup[(sec_name.upper(), subj.upper())] = rec
                
                # Active teacher tracking
                if t_id not in active_teachers:
                    active_teachers[t_id] = {
                        "teacher_id": t_id,
                        "teacher_name": get_display_name(clean_t),
                        "canonical_name": get_display_name(clean_t),
                        "raw_names": set(),
                        "periods": [],
                        "subjects": set(),
                        "sections": set(),
                        "source_cells": []
                    }
                active_teachers[t_id]["raw_names"].add(tchr)
                active_teachers[t_id]["subjects"].add(subj)
                active_teachers[t_id]["sections"].add(sec_name)
                active_teachers[t_id]["source_cells"].append(f"{sdef['sheet']}!{cell_ref}")
                active_teachers[t_id]["periods"].append({
                    "section": sec_name,
                    "section_id": sec_id,
                    "subject": subj,
                    "day": dname,
                    "time": time_str,
                    "shift": sdef['shift'],
                    "source_cell": f"{sdef['sheet']}!{cell_ref}"
                })
                
        first_day_val = day_cells["Sunday"]["raw"] if "Sunday" in day_cells else ""
        all_same = all(day_cells[d]["raw"] == first_day_val for d in DAYS_OF_WEEK)
        
        main_subj = row_subjects[0] if row_subjects else (first_day_val if first_day_val else "BREAK / ASSEMBLY")
        main_tchr = row_teachers[0] if row_teachers else None
        clean_main_t = clean_teacher_name(main_tchr) if main_tchr else None
        
        period_obj = {
            "period_num": p_num,
            "time": time_str,
            "minutes": min_str,
            "is_merged_all_days": all_same,
            "label": main_subj if is_break_row else None,
            "subject": main_subj,
            "subject_id": 'subj_' + re.sub(r'[^a-zA-Z0-9]+', '_', main_subj).strip('_').lower(),
            "teacher": get_display_name(clean_main_t) if clean_main_t else main_tchr,
            "teacher_id": 'tchr_' + re.sub(r'[^a-zA-Z0-9]+', '_', clean_main_t).strip('_').lower() if clean_main_t else None,
            "is_break": is_break_row and all_same,
            "days": day_cells,
            "source_sheet": sdef['sheet'],
            "source_cell": sdef['header_cell']
        }
        periods_list.append(period_obj)
        p_num += 1
        
    sec_obj = {
        "id": sec_id,
        "section_id": sec_id,
        "section_name": sec_name,
        "shift": sdef['shift'],
        "department": sdef['dept'],
        "grade_level": sdef['grade'],
        "total_periods": len(periods_list),
        "source_sheet": sdef['sheet'],
        "source_cell": sdef['header_cell'],
        "periods": periods_list,
        "rows": periods_list
    }
    sections_dataset.append(sec_obj)

print(f"Total Canonical Sections: {len(sections_dataset)}")
print(f"Total Canonical Audit Records: {len(audit_records)}")
print(f"Total Active Faculty with >= 1 V4 Class: {len(active_teachers)}")

# Write class schedules
with open(CLASS_DATA_JSON, 'w') as f:
    json.dump(sections_dataset, f, indent=2)
with open(CLASS_DATA_JS, 'w') as f:
    f.write('const ALL_SECTIONS_DATA = ' + json.dumps(sections_dataset, indent=2) + ';\n')

# Comprehensive Master Time Slots spanning F2F, ODL1, ODL2
MASTER_TIME_SLOTS = [
    # F2F Morning
    {"time": "07:30 AM – 07:40 AM", "minutes": "10 min.", "is_break": True, "label": "GENERAL ASSEMBLY", "shift": "F2F"},
    {"time": "07:40 AM – 08:25 AM", "minutes": "45 min.", "is_break": False, "shift": "F2F"},
    {"time": "08:25 AM – 09:05 AM", "minutes": "40 min.", "is_break": False, "shift": "F2F"},
    {"time": "09:05 AM – 09:45 AM", "minutes": "40 min.", "is_break": False, "shift": "F2F"},
    {"time": "09:45 AM – 10:00 AM", "minutes": "15 min.", "is_break": True, "label": "RECESS", "shift": "F2F"},
    {"time": "10:00 AM – 10:45 AM", "minutes": "45 min.", "is_break": False, "shift": "F2F"},
    {"time": "10:45 AM – 11:30 AM", "minutes": "45 min.", "is_break": False, "shift": "F2F"},
    {"time": "11:30 AM – 12:40 PM", "minutes": "70 min.", "is_break": True, "label": "LUNCH AND SALAH", "shift": "F2F"},
    # F2F Afternoon
    {"time": "12:40 PM – 01:25 PM", "minutes": "45 min.", "is_break": False, "shift": "F2F"},
    {"time": "01:25 PM – 02:10 PM", "minutes": "45 min.", "is_break": False, "shift": "F2F"},
    {"time": "02:15 PM – 03:00 PM", "minutes": "45 min.", "is_break": False, "shift": "F2F"},
    {"time": "03:00 PM – 03:30 PM", "minutes": "30 min.", "is_break": True, "label": "SALAH & DEPARTURE", "shift": "F2F"},
    # ODL 1st Shift
    {"time": "12:30 PM – 12:40 PM", "minutes": "10 min.", "is_break": True, "label": "GENERAL ASSEMBLY", "shift": "ODL - 1ST SHIFT"},
    {"time": "12:40 PM – 01:20 PM", "minutes": "40 min.", "is_break": False, "shift": "ODL - 1ST SHIFT"},
    {"time": "01:20 PM – 01:30 PM", "minutes": "10 min.", "is_break": True, "label": "TRANSITION", "shift": "ODL - 1ST SHIFT"},
    {"time": "01:30 PM – 02:10 PM", "minutes": "40 min.", "is_break": False, "shift": "ODL - 1ST SHIFT"},
    {"time": "02:10 PM – 02:20 PM", "minutes": "10 min.", "is_break": True, "label": "TRANSITION", "shift": "ODL - 1ST SHIFT"},
    {"time": "02:20 PM – 03:00 PM", "minutes": "40 min.", "is_break": False, "shift": "ODL - 1ST SHIFT"},
    {"time": "03:00 PM – 03:30 PM", "minutes": "30 min.", "is_break": True, "label": "HOMEROOM GUIDANCE / ARAL", "shift": "ODL - 1ST SHIFT"},
    # ODL 2nd Shift
    {"time": "03:30 PM – 03:40 PM", "minutes": "10 min.", "is_break": True, "label": "GENERAL ASSEMBLY", "shift": "ODL - 2ND SHIFT"},
    {"time": "03:40 PM – 04:20 PM", "minutes": "40 min.", "is_break": False, "shift": "ODL - 2ND SHIFT"},
    {"time": "04:20 PM – 04:30 PM", "minutes": "10 min.", "is_break": True, "label": "TRANSITION", "shift": "ODL - 2ND SHIFT"},
    {"time": "04:30 PM – 05:10 PM", "minutes": "40 min.", "is_break": False, "shift": "ODL - 2ND SHIFT"},
    {"time": "05:10 PM – 05:20 PM", "minutes": "10 min.", "is_break": True, "label": "TRANSITION", "shift": "ODL - 2ND SHIFT"},
    {"time": "05:20 PM – 06:00 PM", "minutes": "40 min.", "is_break": False, "shift": "ODL - 2ND SHIFT"},
    {"time": "06:00 PM – 06:15 PM", "minutes": "15 min.", "is_break": True, "label": "SALAH & DISMISSAL", "shift": "ODL - 2ND SHIFT"}
]

teacher_weekly_dict = {}

for tid, tdata in active_teachers.items():
    t_periods = tdata["periods"]
    
    # Filter master slots to only those shifts where the teacher has classes
    t_shifts = set(p["shift"] for p in t_periods)
    relevant_slots = [s for s in MASTER_TIME_SLOTS if s.get("shift") in t_shifts or s.get("shift") is None]
    if not relevant_slots:
        relevant_slots = MASTER_TIME_SLOTS
        
    t_rows = []
    for slot in relevant_slots:
        s_rng = parse_time_range(slot["time"])
        
        if slot["is_break"]:
            t_rows.append({
                "time": slot["time"],
                "minutes": slot["minutes"],
                "is_break": True,
                "break_title": slot["label"],
                "days": {}
            })
        else:
            slot_days = {}
            for d in DAYS_OF_WEEK:
                matching_p = []
                for p in t_periods:
                    if p["day"] == d and (p["shift"] == slot.get("shift") or not slot.get("shift")):
                        p_rng = parse_time_range(p["time"])
                        if s_rng and p_rng and abs(s_rng[0] - p_rng[0]) <= 20 and abs(s_rng[1] - p_rng[1]) <= 20:
                            matching_p.append(p)
                            
                if len(matching_p) == 1:
                    p = matching_p[0]
                    slot_days[d] = {
                        "occupied": True,
                        "is_class": True,
                        "subject": p["subject"],
                        "section": p["section"],
                        "shift": p["shift"],
                        "color": get_subj_color(p["subject"]),
                        "has_conflict": False
                    }
                elif len(matching_p) > 1:
                    slot_days[d] = {
                        "occupied": True,
                        "is_class": True,
                        "subject": " / ".join([p["subject"] for p in matching_p]),
                        "section": " & ".join([p["section"] for p in matching_p]),
                        "shift": matching_p[0]["shift"],
                        "color": get_subj_color(matching_p[0]["subject"]),
                        "has_conflict": True
                    }
                else:
                    slot_days[d] = {"occupied": False, "is_class": False}
                    
            t_rows.append({
                "time": slot["time"],
                "minutes": slot["minutes"],
                "is_break": False,
                "days": slot_days
            })
            
    teacher_weekly_dict[tid] = {
        "teacher_id": tid,
        "teacher_name": tdata["teacher_name"],
        "canonical_name": tdata["canonical_name"],
        "total_classes": len(t_periods),
        "total_teaching_periods": len(t_periods),
        "subjects": sorted(list(tdata["subjects"])),
        "sections": sorted(list(tdata["sections"])),
        "periods": t_periods,
        "rows": t_rows
    }

with open(TEACHER_WEEKLY_JSON, 'w') as f:
    json.dump(teacher_weekly_dict, f, indent=2)
with open(TEACHER_WEEKLY_JS, 'w') as f:
    f.write('const ALL_TEACHERS_DATA = ' + json.dumps(teacher_weekly_dict, indent=2) + ';\n')

print(f"Teacher weekly schedules saved for {len(teacher_weekly_dict)} teachers.")

# Write Audit Log
with open(AUDIT_TXT, 'w') as f:
    f.write("=== CANONICAL V4 TEACHER AUDIT LOG ===\n")
    f.write(f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
    f.write(f"Total Verified Faculty: {len(active_teachers)}\n")
    f.write(f"Total Unique Class Periods: {len(audit_records)}\n\n")
    f.write(f"{'CANONICAL NAME':<25} | {'ACTIVE CLASSES':<15} | {'SECTIONS'}\n")
    f.write("-" * 120 + "\n")
    for tid, tdata in sorted(active_teachers.items(), key=lambda x: x[1]['canonical_name']):
        secs_str = ", ".join(sorted(list(tdata['sections'])))
        f.write(f"{tdata['canonical_name']:<25} | {len(tdata['periods']):<15} | {secs_str}\n")

print(f"Teacher audit written to {AUDIT_TXT}")

# Update Master Exam Records
with open(EXAM_DATA_JSON, 'r') as f:
    exam_records = json.load(f)

SUBJECT_CANONICAL_MAP = {
    'MATHEMATICS': ['MATH', 'MATH 5'],
    'GENERAL MATHEMATICS': ['GEN MATH', 'GEN. MATH', 'GENERAL MATH'],
    'ARAL MATH': ['ARAL MATH'],
    'ARABIC LANGUAGE': ['ARABIC'],
    'ARABIC': ['ARABIC'],
    'GMRC / VALUES': ['GMRC', 'VALUES ED.', 'ESP', 'VALUES'],
    'GMRC': ['GMRC'],
    'VALUES EDUCATION': ['VALUES ED.', 'ESP', 'VALUES'],
    'TECHNOLOGY AND LIVELIHOOD EDUCATION': ['TLE', 'TLE / TVL'],
    'TLE': ['TLE', 'TLE / TVL'],
    'MAPEH': ['MAPEH'],
    'PE': ['PE', 'PE 12'],
    'PHYSICAL EDUCATION': ['PE', 'PE 12'],
    'ARALING PANLIPUNAN (AP)': ['AP', 'SOC.SCI', 'SOC SCI', 'MAKABANSA'],
    'ARALING PANLIPUNAN': ['AP', 'SOC.SCI', 'SOC SCI'],
    'MAKABANSA': ['MAKABANSA'],
    'READING AND LITERACY': ['READING AND LITERACY', 'R & L', 'LANGUAGE'],
    'LANGUAGE': ['LANGUAGE'],
    'SCIENCE': ['SCIENCE', 'SCI', 'GEN SCIENCE'],
    'GENERAL SCIENCE': ['GEN SCIENCE', 'GEN. SCIENCE', 'GENERAL SCIENCE'],
    'GENERAL BIOLOGY 1': ['GEN BIO 1', 'GEN. BIO 1'],
    'GENERAL PHYSICS 1': ['GEN. PHYSICS 1', 'GEN PHYSICS 1'],
    'PRACTICAL RESEARCH 2': ['PRAC. RES. 2', 'PRAC RES 2'],
    'MEDIA AND INFORMATION LITERACY': ['MIL'],
    '21ST CENTURY LITERATURE': ['21ST LIT.', '21ST LIT', '21ST CENTURY LITERATURE'],
    'LIFE AND CAREER SKILLS': ['LCS', 'LCS 11 2ND SHIFT'],
    'PAGBASA AT PAGSUSURI NG IBA\'T IBANG TEKSTO': ['PSKP', 'PSKP 11'],
    'ENGLISH': ['ENGLISH', 'ENG', 'EC'],
    'FILIPINO': ['FILIPINO', 'FIL'],
    'QUR\'AN': ['QUR\'AN', 'QURAN'],
    'HADITH': ['HADITH'],
    'SHAF': ['SHAF'],
    'CIRCLE TIME': ['CIRCLE TIME 1', 'CIRCLE TIME 2', 'CT 1', 'CT 2', 'CIRCLE TIME', 'MEETING TIME']
}

verified_exams = 0
unverified_exams = 0

for exam in exam_records:
    sec_name = exam.get('section_name', '').strip()
    sec_id = exam.get('section_id', '')
    raw_subj = exam.get('subject', '').strip()
    subj_upper = raw_subj.upper()
    c_subj = clean_subject_code(raw_subj)
    
    # 120-min rule
    is_hs = any(g in exam.get('section_name', '').upper() for g in ['GRADE 7', 'GRADE 8', 'GRADE 9', 'GRADE 10'])
    is_reg_math = (c_subj == 'MATH' or raw_subj.upper() == 'MATHEMATICS') and not any(k in raw_subj.upper() for k in ['ARAL', 'GENERAL', 'CALCULUS', 'STATISTICS'])
    if is_hs and is_reg_math:
        exam['duration_minutes'] = 120
    elif exam.get('duration_minutes') == 120 and not (is_hs and is_reg_math):
        exam['duration_minutes'] = 60
        
    matched = None
    aliases = SUBJECT_CANONICAL_MAP.get(subj_upper, [subj_upper, c_subj])
    
    for a in aliases:
        if (sec_id, a) in canonical_lookup:
            matched = canonical_lookup[(sec_id, a)]
            break
        if (sec_name.upper(), a) in canonical_lookup:
            matched = canonical_lookup[(sec_name.upper(), a)]
            break
            
    if matched:
        exam['teacher'] = get_display_name(matched['teacher_clean'])
        exam['teacher_clean'] = matched['teacher_clean']
        exam['teacher_id'] = matched['teacher_id']
        exam['teacher_status'] = "VERIFIED"
        exam['source_cell'] = matched['source_cell']
        verified_exams += 1
    else:
        exam['teacher_status'] = "TEACHER NOT VERIFIED"
        unverified_exams += 1

print(f"Master Exam Records: {verified_exams} Verified, {unverified_exams} Unverified")

with open(EXAM_DATA_JSON, 'w') as f:
    json.dump(exam_records, f, indent=2)
with open(EXAM_DATA_JS, 'w') as f:
    f.write('const ALL_EXAM_RECORDS = ' + json.dumps(exam_records, indent=2) + ';\n')

print("✓ Successfully rebuilt system from AMIS_CLASS_DATASET_CANONICAL_LATEST_V4.json!")
