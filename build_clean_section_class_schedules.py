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

# Find all section headers across sheets
all_sections = []

sheet_configs = [
    ('ELEM', 120),
    ('HS SCHED (NEW)', 100),
    ('SHS', 50),
    ('HS SCHED', 140)
]

for sname, max_r in sheet_configs:
    ws = wb[sname]
    for r in range(1, min(ws.max_row + 1, max_r)):
        for c in range(1, min(ws.max_column + 1, 60)):
            v = ws.cell(row=r, column=c).value
            if v and isinstance(v, str):
                s = v.strip()
                s_up = s.upper()
                if any(k in s_up for k in ['GRADE', 'KINDER', 'SECTION', 'SCHEDULE', 'FACE TO FACE', '1ST SHIFT', '2ND SHIFT']):
                    if len(s) < 80 and not any(k in s_up for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH']):
                        # check if table starts at r+1 or r+2
                        time_row = None
                        if r + 1 <= ws.max_row and any('time' in str(ws.cell(row=r+1, column=cc).value).lower() for cc in range(c, min(ws.max_column+1, c+5))):
                            time_row = r + 1
                        elif r + 2 <= ws.max_row and any('time' in str(ws.cell(row=r+2, column=cc).value).lower() for cc in range(c, min(ws.max_column+1, c+5))):
                            time_row = r + 2
                            
                        if time_row:
                            # Extract periods
                            # Days are usually time_col+2 .. time_col+6
                            time_col = c
                            # find min_col
                            min_col = c + 1
                            
                            # check if time_col has time
                            periods = []
                            for pr in range(time_row + 1, time_row + 18):
                                t_val = clean_time(ws.cell(row=pr, column=time_col).value)
                                m_val = clean_min(ws.cell(row=pr, column=min_col).value)
                                
                                if not t_val and not m_val:
                                    continue
                                
                                row_days = {}
                                has_content = False
                                for didx, d in enumerate(DAYS):
                                    cell_val = ws.cell(row=pr, column=min_col + 1 + didx).value
                                    parsed = parse_cell(cell_val)
                                    row_days[d] = parsed
                                    if parsed:
                                        has_content = True
                                        
                                if has_content or t_val:
                                    periods.append({
                                        'time': t_val,
                                        'minutes': m_val,
                                        'days': row_days
                                    })
                                    
                            if periods:
                                # Determine Department, Grade Level, Modality, Shift
                                dept = "Elementary"
                                if any(k in s_up for k in ['GRADE 7', 'GRADE 8', 'GRADE 9', 'GRADE 10', '7 & 8', '9 & 10']):
                                    dept = "Junior High School"
                                elif any(k in s_up for k in ['GRADE 11', 'GRADE 12', '11 & 12', 'SHS', 'SEMESTER']):
                                    dept = "Senior High School"
                                    
                                grade = "Grade"
                                for g_num in range(12, 0, -1):
                                    if f"GRADE {g_num}" in s_up or f"G{g_num}" in s_up:
                                        grade = f"Grade {g_num}"
                                        break
                                    elif f"{g_num} &" in s_up or f"& {g_num}" in s_up:
                                        grade = f"Grade {g_num}"
                                        break
                                if 'KINDER 1' in s_up or 'K1' in s_up:
                                    grade = "Kindergarten 1"
                                elif 'KINDER 2' in s_up or 'K2' in s_up:
                                    grade = "Kindergarten 2"
                                    
                                shift = "Morning (F2F)"
                                if '1ST SHIFT' in s_up or 'FIRST SHIFT' in s_up:
                                    shift = "ODL 1st Shift"
                                elif '2ND SHIFT' in s_up or 'SECOND SHIFT' in s_up:
                                    shift = "ODL 2nd Shift"
                                    
                                all_sections.append({
                                    'id': f"sec_{len(all_sections)+1}",
                                    'sheet': sname,
                                    'section_name': s,
                                    'department': dept,
                                    'grade_level': grade,
                                    'shift': shift,
                                    'periods': periods
                                })

print(f"Extracted {len(all_sections)} clean section schedules.")

# De-duplicate by section_name if identical from multiple sheets, prefer newer sheets
unique_sections = []
seen_names = set()
for sec in all_sections:
    s_norm = sec['section_name'].strip().lower()
    if s_norm not in seen_names:
        seen_names.add(s_norm)
        unique_sections.append(sec)

print(f"Unique section schedules: {len(unique_sections)}")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json', 'w') as f:
    json.dump(unique_sections, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.js', 'w') as f:
    f.write(f"window.OFFICIAL_CLASS_SCHEDULES = {json.dumps(unique_sections, indent=2)};\n")
    f.write(f"const OFFICIAL_CLASS_SCHEDULES = window.OFFICIAL_CLASS_SCHEDULES;\n")

print("Saved class_schedules_data.json and class_schedules_data.js with window.OFFICIAL_CLASS_SCHEDULES!")

