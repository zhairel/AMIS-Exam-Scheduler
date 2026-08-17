import openpyxl
import json
import re
from collections import defaultdict
from teacher_registry import TEACHER_REGISTRY, resolve_teacher

EXCEL_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/SCHEDULE SY 2026-2027 TW.xlsx'
CLASS_DATA_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json'

wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

with open(CLASS_DATA_PATH) as f:
    sections = json.load(f)

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

STANDARD_TIME_BLOCKS = [
    {"id": "f2f_assembly", "time": "07:30 AM – 07:40 AM", "minutes": "10 min.", "is_break": True, "break_title": "GENERAL ASSEMBLY (F2F)", "shift_type": "F2F"},
    {"id": "p1_f2f", "time": "07:40 AM – 08:25 AM", "minutes": "45 min.", "is_break": False, "shift_type": "F2F"},
    {"id": "p2_f2f", "time": "08:25 AM – 09:05 AM", "minutes": "40 min.", "is_break": False, "shift_type": "F2F"},
    {"id": "p3_f2f", "time": "09:05 AM – 09:45 AM", "minutes": "40 min.", "is_break": False, "shift_type": "F2F"},
    {"id": "f2f_recess", "time": "09:45 AM – 10:00 AM", "minutes": "15 min.", "is_break": True, "break_title": "RECESS", "shift_type": "F2F"},
    {"id": "p4_f2f", "time": "10:00 AM – 10:45 AM", "minutes": "45 min.", "is_break": False, "shift_type": "F2F"},
    {"id": "p5_f2f", "time": "10:45 AM – 11:30 AM", "minutes": "45 min.", "is_break": False, "shift_type": "F2F"},
    {"id": "f2f_lunch", "time": "11:30 AM – 12:30 PM", "minutes": "60 min.", "is_break": True, "break_title": "LUNCH and SALAH", "shift_type": "F2F"},
    {"id": "odl1_assembly", "time": "12:30 PM – 12:40 PM", "minutes": "10 min.", "is_break": True, "break_title": "GENERAL ASSEMBLY (FIRST SHIFT)", "shift_type": "ODL 1st Shift"},
    {"id": "p6_f2f_odl1", "time": "12:40 PM – 01:25 PM (F2F)\n12:40 PM – 01:20 PM (ODL)", "minutes": "45/40 min.", "is_break": False, "shift_type": "F2F / ODL 1"},
    {"id": "p7_f2f_odl1", "time": "01:25 PM – 02:10 PM (F2F)\n01:30 PM – 02:10 PM (ODL)", "minutes": "45/40 min.", "is_break": False, "shift_type": "F2F / ODL 1"},
    {"id": "p8_f2f_odl1", "time": "02:15 PM – 03:00 PM (F2F)\n02:20 PM – 03:00 PM (ODL)", "minutes": "45/40 min.", "is_break": False, "shift_type": "F2F / ODL 1"},
    {"id": "f2f_salah_departure", "time": "03:00 PM – 03:30 PM", "minutes": "30 min.", "is_break": True, "break_title": "SALAH & DEPARTURE (F2F)", "shift_type": "F2F / ODL 1"},
    {"id": "odl2_assembly", "time": "03:30 PM – 03:40 PM", "minutes": "10 min.", "is_break": True, "break_title": "GENERAL ASSEMBLY (SECOND SHIFT)", "shift_type": "ODL 2nd Shift"},
    {"id": "p1_odl2", "time": "03:40 PM – 04:20 PM", "minutes": "40 min.", "is_break": False, "shift_type": "ODL 2nd Shift"},
    {"id": "p2_odl2", "time": "04:30 PM – 05:10 PM", "minutes": "40 min.", "is_break": False, "shift_type": "ODL 2nd Shift"},
    {"id": "p3_odl2", "time": "05:20 PM – 06:00 PM", "minutes": "40 min.", "is_break": False, "shift_type": "ODL 2nd Shift"}
]

def map_time_to_row_id(time_str, shift):
    if not time_str: return None
    t_clean = time_str.upper().replace(' ', '')
    if '7:30' in t_clean and '7:40' in t_clean: return 'f2f_assembly'
    if '7:40' in t_clean or '07:40' in t_clean: return 'p1_f2f'
    if '8:25' in t_clean or '08:25' in t_clean: return 'p2_f2f'
    if '9:05' in t_clean or '09:05' in t_clean: return 'p3_f2f'
    if '9:45' in t_clean and '10:00' in t_clean: return 'f2f_recess'
    if '10:00' in t_clean: return 'p4_f2f'
    if '10:45' in t_clean: return 'p5_f2f'
    if '11:30' in t_clean: return 'f2f_lunch'
    if '12:30' in t_clean and '12:40' in t_clean: return 'odl1_assembly'
    if '12:40' in t_clean: return 'p6_f2f_odl1'
    if '1:25' in t_clean or '1:30' in t_clean or '01:25' in t_clean or '01:30' in t_clean: return 'p7_f2f_odl1'
    if '2:15' in t_clean or '2:20' in t_clean or '02:15' in t_clean or '02:20' in t_clean: return 'p8_f2f_odl1'
    if '3:00' in t_clean and '3:30' in t_clean: return 'f2f_salah_departure'
    if '3:30' in t_clean and '3:40' in t_clean: return 'odl2_assembly'
    if '3:40' in t_clean or '03:40' in t_clean: return 'p1_odl2'
    if '4:30' in t_clean or '04:30' in t_clean: return 'p2_odl2'
    if '5:20' in t_clean or '05:20' in t_clean: return 'p3_odl2'
    return None

def get_subject_color(subj):
    s = (subj or "").lower()
    if any(k in s for k in ['gmrc', 'values', 'esp', 'homeroom', 'hg', 'val ed']):
        return {'bg': '#dcfce7', 'border': '#86efac', 'text': '#14532d'}
    if any(k in s for k in ['arabic', "qur'an", 'quran', 'hadith', 'shaf', 'islamic']):
        return {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#581c87'}
    if any(k in s for k in ['math', 'mathematics', 'physics', 'algebra', 'calculus']):
        return {'bg': '#e0f2fe', 'border': '#7dd3fc', 'text': '#0369a1'}
    if any(k in s for k in ['science', 'sci', 'biology', 'chemistry', 'gen science']):
        return {'bg': '#ccfbf1', 'border': '#5eead4', 'text': '#115e59'}
    if any(k in s for k in ['english', 'reading', 'literacy', 'language', 'lit', 'circle', 'meeting', 'wrap-up']):
        return {'bg': '#fef3c7', 'border': '#fde047', 'text': '#854d0e'}
    if any(k in s for k in ['filipino', 'makabansa', 'ap', 'araling panlipunan', 'social science', 'soc.sci', 'soc sci']):
        return {'bg': '#ffedd5', 'border': '#fdba74', 'text': '#9a3412'}
    if any(k in s for k in ['mapeh', 'pe', 'tle', 'mil', 'practical research', 'entrep', 'entrepreneurship']):
        return {'bg': '#fae8ff', 'border': '#f0abfc', 'text': '#86198f'}
    return {'bg': '#f1f5f9', 'border': '#cbd5e1', 'text': '#334155'}

def format_clean_short_label(subj, sec_name):
    s_clean = re.sub(r'(?i)\s*-\s*(ust|tchr|alim|sir|tr).*$', '', subj).strip()
    sec_clean = re.sub(r'\(.*?\)', '', sec_name).strip()
    sec_short = sec_clean.replace('GRADE ', 'G').replace('Grade ', 'G').replace('Kinder ', 'K').replace('KINDER ', 'K')
    if 'FACE TO FACE' in sec_name.upper():
        sec_short += ' (F2F)'
        
    return s_clean, sec_short

teacher_classes = defaultdict(lambda: defaultdict(dict))

for sec in sections:
    sname = sec['section_name']
    dept = sec['department']
    grade = sec['grade_level']
    shift = sec['shift']
    
    for p in sec['periods']:
        t_raw = p['time']
        row_id = map_time_to_row_id(t_raw, shift)
        if not row_id: continue
        
        if p.get('is_merged_all_days'):
            if not p.get('is_break'):
                tid = p.get('teacher_id')
                if not tid and p.get('teacher'):
                    t_res = resolve_teacher(p.get('teacher'))
                    if t_res: tid = t_res['id']
                    
                subj = p.get('subject', '').strip()
                if tid:
                    s_clean, sec_short = format_clean_short_label(subj, sname)
                    for d in DAYS:
                        teacher_classes[tid][row_id][d] = {
                            'subject': s_clean,
                            'section': sname,
                            'section_short': sec_short,
                            'grade': grade,
                            'shift': shift
                        }
        else:
            for d, cell in (p.get('days') or {}).items():
                if cell and not cell.get('is_break'):
                    tid = cell.get('teacher_id')
                    if not tid and cell.get('teacher'):
                        t_res = resolve_teacher(cell.get('teacher'))
                        if t_res: tid = t_res['id']
                        
                    subj = cell.get('subject', '').strip()
                    if tid:
                        s_clean, sec_short = format_clean_short_label(subj, sname)
                        teacher_classes[tid][row_id][d] = {
                            'subject': s_clean,
                            'section': sname,
                            'section_short': sec_short,
                            'grade': grade,
                            'shift': shift
                        }

final_faculty_schedules = {}

for t_info in sorted(TEACHER_REGISTRY, key=lambda x: x['canonical_name']):
    tid = t_info['id']
    c_name = t_info['canonical_name']
    dept = t_info['department']
    title = t_info['title']
    
    t_rows_data = teacher_classes.get(tid, {})
    distinct_subjs = set()
    total_class_count = 0
    
    rows = []
    for block in STANDARD_TIME_BLOCKS:
        rid = block["id"]
        b_time = block["time"]
        is_brk = block["is_break"]
        
        row_data = {
            "id": rid,
            "time": b_time,
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
                    "break_title": block.get("break_title", ""),
                    "label": block.get("break_title", "")
                }
        else:
            for d in DAYS:
                found = t_rows_data.get(rid, {}).get(d)
                if found:
                    total_class_count += 1
                    subj_name = found['subject']
                    distinct_subjs.add(subj_name)
                    color = get_subject_color(subj_name)
                    
                    row_data["days"][d] = {
                        "occupied": True,
                        "is_class": True,
                        "is_break": False,
                        "subject": subj_name,
                        "section": found['section'],
                        "section_short": found['section_short'],
                        "grade": found['grade'],
                        "shift": found['shift'],
                        "modality": found['shift'],
                        "label": f"{subj_name} - {found['section_short']}",
                        "color": color,
                        "bg": color['bg'],
                        "border": color['border'],
                        "text": color['text']
                    }
                else:
                    row_data["days"][d] = None
                    
        rows.append(row_data)

    final_faculty_schedules[tid] = {
        "teacher_id": tid,
        "teacher_name": c_name,
        "canonical_name": c_name,
        "department": dept,
        "title": title,
        "total_classes": total_class_count,
        "total_teaching_periods": total_class_count,
        "subjects": sorted(list(distinct_subjs)),
        "rows": rows
    }

print(f"Extracted and unified comprehensive faculty timetables for {len(final_faculty_schedules)} UNIQUE teachers!")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.json', 'w') as f:
    json.dump(final_faculty_schedules, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.js', 'w') as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(final_faculty_schedules, indent=2)};\n")
    f.write(f"const AMIS_TEACHER_WEEKLY_SCHEDULES = window.AMIS_TEACHER_WEEKLY_SCHEDULES;\n")

print("\nSuccessfully synchronized all Faculty Timetables in JSON & JS!")

