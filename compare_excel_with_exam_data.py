import json
import re

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/extracted_raw_tables.json') as f:
    tables = json.load(f)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json') as f:
    exam_data = json.load(f)

# Normalize teacher names
from parse_all_authoritative_schedules import normalize_teacher_name

# Collect all section subject-teacher mappings from Excel
excel_assignments = {} # (grade, section, subject) -> teacher

def parse_cell(text):
    if not text:
        return None, None
    s = text.strip()
    if any(k in s.upper() for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'DEPARTURE', 'TRANSITION', 'SALAH', 'HOMEROOM GUIDANCE']):
        return None, None
    m = re.match(r'^(.*?)\s*[-–—]\s*(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)?\s*([A-Za-z\s\.\'\`]+?)(\s*\(.*?\))?$', s, flags=re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        t_raw = (m.group(2) or '') + ' ' + m.group(3).strip()
        return subj, normalize_teacher_name(t_raw)
    return s, None

# Let's inspect sections from ELEM, HS SCHED (NEW), SHS
section_tables = [t for t in tables if any(k in t['title'].upper() for k in ['GRADE', 'KINDER', 'SECTION', 'FACE TO FACE', '1ST SHIFT', '2ND SHIFT'])]

print(f"Total section tables found: {len(section_tables)}")
for st in section_tables[:10]:
    print(f"Sheet: {st['sheet']:<15} | Title: {st['title']}")

