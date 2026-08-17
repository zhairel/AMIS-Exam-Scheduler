import openpyxl
import re
import json

EXCEL_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/SCHEDULE SY 2026-2027 TW.xlsx'
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

from parse_all_authoritative_schedules import normalize_teacher_name

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

def clean_time(t_str):
    if not t_str:
        return ""
    s = str(t_str).strip()
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def clean_min(m_val):
    if not m_val:
        return ""
    if isinstance(m_val, (int, float)):
        return f"{int(m_val)} min."
    s = str(m_val).strip()
    if 'min' not in s.lower() and s.isdigit():
        return f"{s} min."
    return s

def parse_cell(cell_str):
    if not cell_str:
        return None
    s = str(cell_str).strip()
    if not s:
        return None
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    
    s_up = s.upper()
    is_break = any(k in s_up for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'DEPARTURE', 'TRANSITION', 'SALAH'])
    if is_break:
        return {
            'is_break': True,
            'label': s,
            'subject': '',
            'teacher': ''
        }
    
    # Check "Subject - Teacher"
    m = re.match(r'^(.*?)\s*[-–—]\s*(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)?\s*([A-Za-z\s\.\'\`]+?)(\s*\(.*?\))?$', s, flags=re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        t_raw = (m.group(2) or '') + ' ' + m.group(3).strip()
        t_norm = normalize_teacher_name(t_raw)
        extra = m.group(4) or ''
        return {
            'is_break': False,
            'subject': subj,
            'teacher': t_norm,
            'extra': extra.strip()
        }
        
    m2 = re.match(r'^(.*?)\s+(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)\s+([A-Za-z\s\.\'\`]+)$', s, flags=re.IGNORECASE)
    if m2:
        subj = m2.group(1).strip()
        t_raw = m2.group(2) + ' ' + m2.group(3).strip()
        t_norm = normalize_teacher_name(t_raw)
        return {
            'is_break': False,
            'subject': subj,
            'teacher': t_norm,
            'extra': ''
        }
        
    return {
        'is_break': False,
        'subject': s,
        'teacher': '',
        'extra': ''
    }

# Parse ELEM sheet
elem_sheet = wb['ELEM']
with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/extracted_raw_tables.json') as f:
    raw_tables = json.load(f)

# Build a clean list of official class schedules
official_class_schedules = []

for t in raw_tables:
    sheet = t['sheet']
    title = t['title']
    
    # Filter out dedicated teacher load tables
    if sheet in ['ISAL UPDATED', 'HS LOADS'] or 'LOAD' in sheet.upper():
        continue
    
    # Clean section title
    t_clean = re.sub(r'[\r\n\t]+', ' ', title).strip()
    if not any(k in t_clean.upper() for k in ['GRADE', 'KINDER', 'SECTION', 'FACE TO FACE', '1ST SHIFT', '2ND SHIFT', 'SECOND SEMESTER']):
        continue
    
    # Determine Department, Grade Level, Modality, Shift
    dept = "Elementary"
    if any(k in t_clean.upper() for k in ['GRADE 7', 'GRADE 8', 'GRADE 9', 'GRADE 10', '7 & 8', '9 & 10']):
        dept = "Junior High School"
    elif any(k in t_clean.upper() for k in ['GRADE 11', 'GRADE 12', '11 & 12', 'SHS', 'SEMESTER']):
        dept = "Senior High School"
        
    grade = "Grade"
    for g_num in range(12, 0, -1):
        if f"GRADE {g_num}" in t_clean.upper() or f"G{g_num}" in t_clean.upper():
            grade = f"Grade {g_num}"
            break
        elif f"{g_num} &" in t_clean.upper() or f"& {g_num}" in t_clean.upper():
            grade = f"Grade {g_num}"
            break
    if 'KINDER 1' in t_clean.upper() or 'K1' in t_clean.upper():
        grade = "Kindergarten 1"
    elif 'KINDER 2' in t_clean.upper() or 'K2' in t_clean.upper():
        grade = "Kindergarten 2"
        
    modality = "Face to Face"
    shift = "Morning (F2F)"
    if '1ST SHIFT' in t_clean.upper() or 'FIRST SHIFT' in t_clean.upper():
        modality = "Online Distance Learning (ODL)"
        shift = "1st Shift"
    elif '2ND SHIFT' in t_clean.upper() or 'SECOND SHIFT' in t_clean.upper():
        modality = "Online Distance Learning (ODL)"
        shift = "2nd Shift"
        
    # Build schedule rows
    schedule_rows = []
    for p in t['periods']:
        t_str = clean_time(p.get('time', ''))
        m_str = clean_min(p.get('minutes', ''))
        
        row_days = {}
        for d in DAYS:
            c_val = p['days'].get(d)
            parsed = parse_cell(c_val)
            row_days[d] = parsed
            
        schedule_rows.append({
            'time': t_str,
            'minutes': m_str,
            'days': row_days
        })
        
    if schedule_rows and any(any(r['days'][d] for d in DAYS) for r in schedule_rows):
        official_class_schedules.append({
            'id': f"sec_{len(official_class_schedules)+1}",
            'sheet': sheet,
            'section_name': t_clean,
            'department': dept,
            'grade_level': grade,
            'modality': modality,
            'shift': shift,
            'periods': schedule_rows
        })

print(f"Compiled {len(official_class_schedules)} official section class schedules.")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json', 'w') as f:
    json.dump(official_class_schedules, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.js', 'w') as f:
    f.write(f"const OFFICIAL_CLASS_SCHEDULES = {json.dumps(official_class_schedules, indent=2)};\n")

print("Saved class_schedules_data.json and class_schedules_data.js successfully!")

