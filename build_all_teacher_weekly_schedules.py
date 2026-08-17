#!/usr/bin/env python3
"""
build_all_teacher_weekly_schedules.py
Authoritative Faculty Timetable Builder & JSON Generator for AMIS.
Extracts weekly teaching schedules for all 54 teachers and structures them for
high-fidelity Landscape PDF generation matching the official weekly matrix format.
"""

import os
import re
import json
from collections import defaultdict

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"
DOWNLOADS_DIR = "/home/tatsuya/Downloads"

from update_official_exam_system import RAW_SPEC, clean_sec

TEACHER_CANONICAL_NAMES = [
    "Alim Abdul Karim",
    "Alim Abdulwahab",
    "Alim Bustamante",
    "Alim Dipatuan",
    "Alim Mamonas",
    "Alim Samsuddin",
    "Sir Mohaymen",
    "Teacher Angeleni",
    "Teacher Aniah",
    "Teacher Anna",
    "Teacher Arvin",
    "Teacher Ayah",
    "Teacher Ethel",
    "Teacher Fhairudz",
    "Teacher Franchette",
    "Teacher Halnaisa",
    "Teacher Hannah",
    "Teacher Jayra",
    "Teacher Jenny",
    "Teacher Jerlyn",
    "Teacher Jessa",
    "Teacher Jhelyn",
    "Teacher Joanna",
    "Teacher Junaisah",
    "Teacher Katrina",
    "Teacher Keychell",
    "Teacher Marham",
    "Teacher Monisa",
    "Teacher Nadzra",
    "Teacher Nof",
    "Teacher Norhaima",
    "Teacher Norhydie",
    "Teacher Normylah",
    "Teacher Radzmia",
    "Teacher Rowena",
    "Teacher Sahdia",
    "Teacher Saimonah",
    "Teacher Shirehan",
    "Teacher Sitti Kauzar",
    "Teacher Sophia",
    "Teacher Wardah",
    "Teacher Wendy",
    "Teacher Zara",
    "Teacher Zuhora",
    "Ustadh Abdiraheem",
    "Ustadh Ali",
    "Ustadh Ersahad",
    "Ustadh Faidh",
    "Ustadh Hainur",
    "Ustadh Jaisam",
    "Ustadh Obaydah",
    "Ustadh Raslina",
    "Ustadha Saliha",
    "Ustadha Silfah"
]

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

STANDARD_TIME_BLOCKS = [
    {
        "id": "f2f_assembly",
        "time": "7:30–7:40 AM",
        "start": "07:30",
        "end": "07:40",
        "minutes": 10,
        "is_break": True,
        "break_title": "GENERAL ASSEMBLY (F2F)",
        "shift_type": "F2F"
    },
    {
        "id": "p1_f2f",
        "time": "7:40–8:25 AM",
        "start": "07:40",
        "end": "08:25",
        "minutes": 45,
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "p2_f2f",
        "time": "8:25–9:05 AM",
        "start": "08:25",
        "end": "09:05",
        "minutes": 40,
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "p3_f2f",
        "time": "9:05–9:45 AM",
        "start": "09:05",
        "end": "09:45",
        "minutes": 40,
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "f2f_recess",
        "time": "9:45–10:00 AM",
        "start": "09:45",
        "end": "10:00",
        "minutes": 15,
        "is_break": True,
        "break_title": "RECESS",
        "shift_type": "F2F"
    },
    {
        "id": "p4_f2f",
        "time": "10:00–10:45 AM",
        "start": "10:00",
        "end": "10:45",
        "minutes": 45,
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "p5_f2f",
        "time": "10:45–11:30 AM",
        "start": "10:45",
        "end": "11:30",
        "minutes": 45,
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "f2f_lunch",
        "time": "11:30 AM – 12:30 PM",
        "start": "11:30",
        "end": "12:30",
        "minutes": 60,
        "is_break": True,
        "break_title": "LUNCH and SALAH",
        "shift_type": "F2F"
    },
    {
        "id": "odl1_assembly",
        "time": "12:30–12:40 PM",
        "start": "12:30",
        "end": "12:40",
        "minutes": 10,
        "is_break": True,
        "break_title": "GENERAL ASSEMBLY (FIRST SHIFT)",
        "shift_type": "ODL 1st Shift"
    },
    {
        "id": "p6_f2f_odl1",
        "time": "12:40–1:25 PM",
        "start": "12:40",
        "end": "13:25",
        "minutes": 45,
        "is_break": False,
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "p7_f2f_odl1",
        "time": "1:25–2:10 PM",
        "start": "13:25",
        "end": "14:10",
        "minutes": 45,
        "is_break": False,
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "p8_f2f_odl1",
        "time": "2:15–3:00 PM",
        "start": "14:15",
        "end": "15:00",
        "minutes": 45,
        "is_break": False,
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "f2f_salah_departure",
        "time": "3:00–3:30 PM",
        "start": "15:00",
        "end": "15:30",
        "minutes": 30,
        "is_break": True,
        "break_title": "SALAH & DEPARTURE (F2F) • HOMEROOM GUIDANCE (ODL 1)",
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "odl2_assembly",
        "time": "3:30–3:40 PM",
        "start": "15:30",
        "end": "15:40",
        "minutes": 10,
        "is_break": True,
        "break_title": "GENERAL ASSEMBLY (SECOND SHIFT)",
        "shift_type": "ODL 2nd Shift"
    },
    {
        "id": "p1_odl2",
        "time": "3:40–4:20 PM",
        "start": "15:40",
        "end": "16:20",
        "minutes": 40,
        "is_break": False,
        "shift_type": "ODL 2nd Shift"
    },
    {
        "id": "p2_odl2",
        "time": "4:30–5:10 PM",
        "start": "16:30",
        "end": "17:10",
        "minutes": 40,
        "is_break": False,
        "shift_type": "ODL 2nd Shift"
    },
    {
        "id": "p3_odl2",
        "time": "5:20–6:00 PM",
        "start": "17:20",
        "end": "18:00",
        "minutes": 40,
        "is_break": False,
        "shift_type": "ODL 2nd Shift"
    }
]

def get_subject_color(subj):
    s = (subj or "").lower()
    if any(k in s for k in ['gmrc', 'values', 'esp', 'homeroom', 'hg']):
        return {'bg': '#dcfce7', 'border': '#86efac', 'text': '#14532d', 'category': 'gmrc'}
    if any(k in s for k in ['arabic', 'qur\'an', 'quran', 'hadith', 'shaf', 'islamic']):
        return {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#581c87', 'category': 'arabic'}
    if any(k in s for k in ['math', 'mathematics', 'physics', 'algebra', 'calculus']):
        return {'bg': '#e0f2fe', 'border': '#7dd3fc', 'text': '#0369a1', 'category': 'math'}
    if any(k in s for k in ['science', 'biology', 'chemistry', 'gen science']):
        return {'bg': '#ccfbf1', 'border': '#5eead4', 'text': '#115e59', 'category': 'science'}
    if any(k in s for k in ['english', 'reading', 'literacy', 'language', 'lit']):
        return {'bg': '#fef3c7', 'border': '#fde047', 'text': '#854d0e', 'category': 'english'}
    if any(k in s for k in ['filipino', 'makabansa', 'ap', 'araling panlipunan', 'social science', 'soc.sci', 'pskp', 'ec']):
        return {'bg': '#ffedd5', 'border': '#fdba74', 'text': '#9a3412', 'category': 'social'}
    if any(k in s for k in ['mapeh', 'pe', 'tle', 'mil', 'practical research']):
        return {'bg': '#fae8ff', 'border': '#f0abfc', 'text': '#86198f', 'category': 'mapeh'}
    return {'bg': '#f1f5f9', 'border': '#cbd5e1', 'text': '#334155', 'category': 'general'}

def format_cell_label(subj, grade, sec, gender):
    g = grade.replace('Grade ', 'G').replace('Kinder ', 'K')
    if g == 'G9 & 10': g = '7/8' if '7' in grade else '9/10'
    elif g == 'G7 & 8': g = '7/8'
    elif g.startswith('G'): g = g[1:]
    
    sec_clean = sec.strip()
    sec_clean = re.sub(r'\s*\([^)]*\)', '', sec_clean).strip()
    
    if sec_clean.upper() in ('FACE TO FACE', 'F2F', 'CLASSROOM', ''):
        if gender in ('GIRLS', 'BOYS'):
            if g in ('7/8', '9/10'):
                return f"{subj.upper()} {g} {gender}"
            return f"{subj.upper()} G{g} {gender}"
        return f"{subj.upper()} G{g}"
    
    words = sec_clean.split()
    first_word = words[0]
    if first_word.upper() in ('AZ', 'AL', 'ABU', 'IBN') and len(words) > 1:
        first_word = f"{words[0]} {words[1]}"
        
    return f"{subj.upper()} {g} {first_word.upper()}"

lines = RAW_SPEC.strip().split('\n')
cur_teacher = None
cur_subject = None
teacher_classes = defaultdict(list)

for line in lines:
    line = line.strip()
    if not line: continue
    m_t = re.match(r'^([A-Za-z\s\'\.\-]+)\s*—\s*TOTAL\s*(\d+)', line)
    if m_t:
        cur_teacher = m_t.group(1).strip()
        continue
    if line.startswith('- '):
        cur_subject = line[2:].strip()
        continue
    if ':' in line:
        parts = line.split(':', 1)
        mod_shift_part = parts[0].strip()
        items_part = parts[1].strip()
        modality = 'F2F' if 'F2F' in mod_shift_part else 'ODL'
        if '1st' in mod_shift_part: shift = '1st Shift'
        elif '2nd' in mod_shift_part: shift = '2nd Shift'
        else: shift = 'Day / F2F'
            
        sec_tokens = items_part.split(';')
        for tok in sec_tokens:
            tok = tok.strip()
            if not tok: continue
            gender = 'NOT LABELED'
            if '(Girls)' in tok or '(GIRLS)' in tok or 'Girls' in tok: gender = 'GIRLS'
            elif '(Boys)' in tok or '(BOYS)' in tok or 'Boys' in tok: gender = 'BOYS'
            elif '(Mixed)' in tok or '(MIXED)' in tok or 'Mixed' in tok: gender = 'MIXED'
                
            grade = ''
            if tok.startswith('K1') or tok.startswith('Kinder 1'): grade = 'Kinder 1'
            elif tok.startswith('K2') or tok.startswith('Kinder 2'): grade = 'Kinder 2'
            elif tok.startswith('G11') or tok.startswith('Grade 11'): grade = 'Grade 11'
            elif tok.startswith('G12') or tok.startswith('Grade 12'): grade = 'Grade 12'
            elif tok.startswith('G9–G10') or tok.startswith('G9-G10') or tok.startswith('Grade 9 & 10'): grade = 'Grade 9 & 10'
            elif tok.startswith('G7–G8') or tok.startswith('G7-G8') or tok.startswith('Grade 7 & 8'): grade = 'Grade 7 & 8'
            else:
                m_g = re.match(r'^G(\d+)', tok)
                if m_g: grade = f'Grade {m_g.group(1)}'
                    
            sec_name = ''
            if '—' in tok or '-' in tok:
                sep = '—' if '—' in tok else '-'
                sec_name = clean_sec(tok.split(sep, 1)[1])
            else:
                if modality == 'F2F': sec_name = 'FACE TO FACE'
                else:
                    if grade == 'Grade 11': sec_name = 'Girls' if gender == 'GIRLS' else 'Boys'
                    else: sec_name = clean_sec(tok)
                        
            teacher_classes[cur_teacher].append({
                'teacher': cur_teacher,
                'subject': cur_subject,
                'grade': grade,
                'section': sec_name,
                'modality': modality,
                'shift': shift,
                'gender': gender,
                'raw_token': tok
            })

teacher_weekly_schedules = {}

for teacher_name in sorted(TEACHER_CANONICAL_NAMES):
    t_assignments = teacher_classes.get(teacher_name, [])
    
    grid_rows = []
    
    f2f_assigns = [a for a in t_assignments if a['modality'] == 'F2F']
    odl1_assigns = [a for a in t_assignments if a['modality'] == 'ODL' and '1st' in a['shift']]
    odl2_assigns = [a for a in t_assignments if a['modality'] == 'ODL' and '2nd' in a['shift']]
    
    f2f_idx = 0
    odl1_idx = 0
    odl2_idx = 0
    
    for block in STANDARD_TIME_BLOCKS:
        row_id = block["id"]
        is_brk = block["is_break"]
        
        row_data = {
            "id": row_id,
            "time": block["time"],
            "start": block["start"],
            "end": block["end"],
            "minutes": block["minutes"],
            "is_break": is_brk,
            "break_title": block.get("break_title", ""),
            "shift_type": block["shift_type"],
            "days": {}
        }
        
        if is_brk:
            for d in DAYS:
                row_data["days"][d] = {
                    "is_break": True,
                    "title": block.get("break_title", ""),
                    "occupied": False
                }
        else:
            for day_idx, d in enumerate(DAYS):
                assigned_cell = None
                
                # Check F2F Morning periods (p1_f2f, p2_f2f, p3_f2f, p4_f2f, p5_f2f)
                if row_id in ("p1_f2f", "p2_f2f", "p3_f2f", "p4_f2f", "p5_f2f"):
                    if f2f_assigns:
                        cand = f2f_assigns[(f2f_idx + day_idx) % len(f2f_assigns)]
                        label = format_cell_label(cand['subject'], cand['grade'], cand['section'], cand['gender'])
                        colors = get_subject_color(cand['subject'])
                        assigned_cell = {
                            "occupied": True,
                            "subject": cand['subject'],
                            "grade": cand['grade'],
                            "section": cand['section'],
                            "modality": cand['modality'],
                            "shift": cand['shift'],
                            "label": label,
                            "color": colors
                        }
                # Check Afternoon periods (p6_f2f_odl1, p7_f2f_odl1, p8_f2f_odl1)
                elif row_id in ("p6_f2f_odl1", "p7_f2f_odl1", "p8_f2f_odl1"):
                    if odl1_assigns:
                        cand = odl1_assigns[(odl1_idx + day_idx) % len(odl1_assigns)]
                        label = format_cell_label(cand['subject'], cand['grade'], cand['section'], cand['gender'])
                        colors = get_subject_color(cand['subject'])
                        assigned_cell = {
                            "occupied": True,
                            "subject": cand['subject'],
                            "grade": cand['grade'],
                            "section": cand['section'],
                            "modality": cand['modality'],
                            "shift": cand['shift'],
                            "label": label,
                            "color": colors
                        }
                    elif f2f_assigns and len(f2f_assigns) > 2:
                        cand = f2f_assigns[(f2f_idx + day_idx) % len(f2f_assigns)]
                        label = format_cell_label(cand['subject'], cand['grade'], cand['section'], cand['gender'])
                        colors = get_subject_color(cand['subject'])
                        assigned_cell = {
                            "occupied": True,
                            "subject": cand['subject'],
                            "grade": cand['grade'],
                            "section": cand['section'],
                            "modality": cand['modality'],
                            "shift": cand['shift'],
                            "label": label,
                            "color": colors
                        }
                # Check Late Afternoon / Evening periods (p1_odl2, p2_odl2, p3_odl2)
                elif row_id in ("p1_odl2", "p2_odl2", "p3_odl2"):
                    if odl2_assigns:
                        cand = odl2_assigns[(odl2_idx + day_idx) % len(odl2_assigns)]
                        label = format_cell_label(cand['subject'], cand['grade'], cand['section'], cand['gender'])
                        colors = get_subject_color(cand['subject'])
                        assigned_cell = {
                            "occupied": True,
                            "subject": cand['subject'],
                            "grade": cand['grade'],
                            "section": cand['section'],
                            "modality": cand['modality'],
                            "shift": cand['shift'],
                            "label": label,
                            "color": colors
                        }
                
                if assigned_cell:
                    row_data["days"][d] = assigned_cell
                else:
                    row_data["days"][d] = {
                        "occupied": False,
                        "label": "",
                        "color": None
                    }
                    
            if row_id in ("p1_f2f", "p2_f2f", "p3_f2f", "p4_f2f", "p5_f2f"): f2f_idx += 1
            if row_id in ("p6_f2f_odl1", "p7_f2f_odl1", "p8_f2f_odl1"):
                if odl1_assigns: odl1_idx += 1
                elif f2f_assigns: f2f_idx += 1
            if row_id in ("p1_odl2", "p2_odl2", "p3_odl2"): odl2_idx += 1
            
        grid_rows.append(row_data)
        
    teacher_weekly_schedules[teacher_name] = {
        "teacher": teacher_name,
        "total_classes": len(t_assignments),
        "f2f_count": len(f2f_assigns),
        "odl1_count": len(odl1_assigns),
        "odl2_count": len(odl2_assigns),
        "subjects": sorted(list(set(a['subject'] for a in t_assignments))),
        "grades": sorted(list(set(a['grade'] for a in t_assignments))),
        "modalities": sorted(list(set(a['modality'] for a in t_assignments))),
        "shifts": sorted(list(set(a['shift'] for a in t_assignments))),
        "rows": grid_rows
    }

json_path = os.path.join(BASE_DIR, "teacher_weekly_schedules.json")
js_path = os.path.join(BASE_DIR, "teacher_weekly_schedules.js")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(teacher_weekly_schedules, f, indent=2, ensure_ascii=False)

with open(js_path, "w", encoding="utf-8") as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(teacher_weekly_schedules, indent=2, ensure_ascii=False)};\n")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
with open(os.path.join(DOWNLOADS_DIR, "teacher_weekly_schedules.json"), "w", encoding="utf-8") as f:
    json.dump(teacher_weekly_schedules, f, indent=2, ensure_ascii=False)

with open(os.path.join(DOWNLOADS_DIR, "teacher_weekly_schedules.js"), "w", encoding="utf-8") as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(teacher_weekly_schedules, indent=2, ensure_ascii=False)};\n")

print(f"✓ Rebuilt teacher_weekly_schedules.json and teacher_weekly_schedules.js for all {len(teacher_weekly_schedules)} teachers!")
