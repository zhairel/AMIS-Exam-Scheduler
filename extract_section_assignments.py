import json
import re
from parse_all_authoritative_schedules import normalize_teacher_name

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/extracted_raw_tables.json') as f:
    tables = json.load(f)

# Collect all section assignments: section_title -> dict of subject -> teacher
section_assignments = {}

def parse_cell(text):
    if not text:
        return None, None
    s = text.strip()
    # Skip breaks, assemblies, transitions
    if any(k in s.upper() for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'DEPARTURE', 'TRANSITION', 'SALAH', 'HOMEROOM GUIDANCE/ARAL PROGRAM', 'HOMEROOM GUIDANCE']):
        return None, None
    
    # Clean up
    s = re.sub(r'[\r\n]+', ' ', s)
    
    # Try pattern: "Subject - Teacher"
    m = re.match(r'^(.*?)\s*[-–—]\s*(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)?\s*([A-Za-z\s\.\'\`]+?)(\s*\(.*?\))?$', s, flags=re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        t_raw = (m.group(2) or '') + ' ' + m.group(3).strip()
        teacher = normalize_teacher_name(t_raw)
        return subj, teacher
        
    # Pattern: "Subject Teacher"
    m2 = re.match(r'^(.*?)\s+(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)\s+([A-Za-z\s\.\'\`]+)$', s, flags=re.IGNORECASE)
    if m2:
        subj = m2.group(1).strip()
        t_raw = m2.group(2) + ' ' + m2.group(3).strip()
        teacher = normalize_teacher_name(t_raw)
        return subj, teacher

    return s, None

# Filter to section tables
for t in tables:
    title = t['title']
    if not any(k in title.upper() for k in ['GRADE', 'KINDER', 'SECTION', 'FACE TO FACE', '1ST SHIFT', '2ND SHIFT']):
        continue
    
    subjs = {}
    for p in t['periods']:
        for d, cell in p['days'].items():
            if cell:
                subj, teacher = parse_cell(cell)
                if subj:
                    # Clean subject name
                    s_clean = re.sub(r'\s*\(.*?\)', '', subj).strip()
                    if s_clean and teacher:
                        subjs[s_clean] = teacher
    
    if subjs:
        section_assignments[f"{t['sheet']}: {title}"] = subjs

print(f"Parsed assignments for {len(section_assignments)} section schedules:")
for sec, subjs in sorted(section_assignments.items())[:15]:
    print(f"\n[{sec}]")
    for s, t in sorted(subjs.items()):
        print(f"  - {s:<25} -> {t}")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/parsed_section_assignments.json', 'w') as f:
    json.dump(section_assignments, f, indent=2)

