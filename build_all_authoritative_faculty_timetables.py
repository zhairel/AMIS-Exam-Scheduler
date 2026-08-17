import openpyxl
import json
import re
from collections import defaultdict

EXCEL_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/SCHEDULE SY 2026-2027 TW.xlsx'
CLASS_DATA_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json'

wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

with open(CLASS_DATA_PATH) as f:
    sections = json.load(f)

from parse_all_authoritative_schedules import normalize_teacher_name

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

STANDARD_TIME_BLOCKS = [
    {"id": "f2f_assembly", "time": "07:30 AM – 07:40 AM", "minutes": 10, "is_break": True, "break_title": "GENERAL ASSEMBLY (F2F)", "shift_type": "F2F"},
    {"id": "p1_f2f", "time": "07:40 AM – 08:25 AM", "minutes": 45, "is_break": False, "shift_type": "F2F"},
    {"id": "p2_f2f", "time": "08:25 AM – 09:05 AM", "minutes": 40, "is_break": False, "shift_type": "F2F"},
    {"id": "p3_f2f", "time": "09:05 AM – 09:45 AM", "minutes": 40, "is_break": False, "shift_type": "F2F"},
    {"id": "f2f_recess", "time": "09:45 AM – 10:00 AM", "minutes": 15, "is_break": True, "break_title": "RECESS", "shift_type": "F2F"},
    {"id": "p4_f2f", "time": "10:00 AM – 10:45 AM", "minutes": 45, "is_break": False, "shift_type": "F2F"},
    {"id": "p5_f2f", "time": "10:45 AM – 11:30 AM", "minutes": 45, "is_break": False, "shift_type": "F2F"},
    {"id": "f2f_lunch", "time": "11:30 AM – 12:30 PM", "minutes": 60, "is_break": True, "break_title": "LUNCH and SALAH", "shift_type": "F2F"},
    {"id": "odl1_assembly", "time": "12:30 PM – 12:40 PM", "minutes": 10, "is_break": True, "break_title": "GENERAL ASSEMBLY (FIRST SHIFT)", "shift_type": "ODL 1st Shift"},
    {"id": "p6_f2f_odl1", "time": "12:40 PM – 01:25 PM", "minutes": 45, "is_break": False, "shift_type": "F2F / ODL 1"},
    {"id": "p7_f2f_odl1", "time": "01:25 PM – 02:10 PM", "minutes": 45, "is_break": False, "shift_type": "F2F / ODL 1"},
    {"id": "p8_f2f_odl1", "time": "02:15 PM – 03:00 PM", "minutes": 45, "is_break": False, "shift_type": "F2F / ODL 1"},
    {"id": "f2f_salah_departure", "time": "03:00 PM – 03:30 PM", "minutes": 30, "is_break": True, "break_title": "SALAH & DEPARTURE (F2F) • HOMEROOM GUIDANCE (ODL 1)", "shift_type": "F2F / ODL 1"},
    {"id": "odl2_assembly", "time": "03:30 PM – 03:40 PM", "minutes": 10, "is_break": True, "break_title": "GENERAL ASSEMBLY (SECOND SHIFT)", "shift_type": "ODL 2nd Shift"},
    {"id": "p1_odl2", "time": "03:40 PM – 04:20 PM", "minutes": 40, "is_break": False, "shift_type": "ODL 2nd Shift"},
    {"id": "p2_odl2", "time": "04:30 PM – 05:10 PM", "minutes": 40, "is_break": False, "shift_type": "ODL 2nd Shift"},
    {"id": "p3_odl2", "time": "05:20 PM – 06:00 PM", "minutes": 40, "is_break": False, "shift_type": "ODL 2nd Shift"}
]

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

# 1. Direct class timetable inverted extraction
teacher_classes = defaultdict(lambda: defaultdict(dict))

for sec in sections:
    sname = sec['section_name']
    dept = sec['department']
    grade = sec['grade_level']
    shift = sec['shift']
    
    for p in sec['periods']:
        t_str = p['time']
        m_str = p['minutes']
        
        if p.get('is_merged_all_days'):
            if not p.get('is_break'):
                tchr_raw = p.get('teacher', '').strip()
                tchr = normalize_teacher_name(tchr_raw)
                subj = p.get('subject', '').strip()
                if tchr and tchr != "Assigned Faculty":
                    for d in DAYS:
                        teacher_classes[tchr][t_str][d] = {
                            'subject': subj,
                            'section': sname,
                            'grade': grade,
                            'shift': shift,
                            'minutes': m_str
                        }
        else:
            for d, cell in (p.get('days') or {}).items():
                if cell and not cell.get('is_break'):
                    tchr_raw = cell.get('teacher', '').strip()
                    tchr = normalize_teacher_name(tchr_raw)
                    subj = cell.get('subject', '').strip()
                    if tchr and tchr != "Assigned Faculty":
                        teacher_classes[tchr][t_str][d] = {
                            'subject': subj,
                            'section': sname,
                            'grade': grade,
                            'shift': shift,
                            'minutes': m_str
                        }

# 2. Add specific direct grids from HS LOADS & ISAL UPDATED
for sname in ['HS LOADS', 'ISAL UPDATED']:
    ws = wb[sname]
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=r, column=c).value
            if v and isinstance(v, str):
                v_str = v.strip()
                if any(k in v_str.upper() for k in ['TEACHER', 'TCHR', 'SIR', 'USTADH', 'ALIM', 'USTADHA']):
                    # Check if next row is Time header
                    if r+1 <= ws.max_row and any('time' in str(ws.cell(row=r+1, column=cc).value).lower() for cc in range(c, min(ws.max_column+1, c+5))):
                        tchr_norm = normalize_teacher_name(v_str)
                        time_row = r + 1
                        time_col = c
                        first_day_col = c + 2
                        
                        for pr in range(time_row + 1, time_row + 18):
                            if pr > ws.max_row: break
                            t_val = ws.cell(row=pr, column=time_col).value
                            if not t_val: continue
                            t_str = str(t_val).strip()
                            if any(k in t_str.upper() for k in ['TEACHER', 'SIR', 'USTADH', 'ALIM']): break
                            
                            for didx, d in enumerate(DAYS):
                                cell_val = ws.cell(row=pr, column=first_day_col + didx).value
                                if cell_val and isinstance(cell_val, str):
                                    c_str = cell_val.strip()
                                    if c_str and not any(k in c_str.upper() for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'SALAH', 'DEPARTURE']):
                                        # Parse subject and section
                                        teacher_classes[tchr_norm][t_str][d] = {
                                            'subject': c_str,
                                            'section': c_str,
                                            'grade': '',
                                            'shift': 'F2F / ODL',
                                            'minutes': '45 min.'
                                        }

# 3. Compile standard grid for each teacher
final_faculty_schedules = {}

for tchr, t_slots in sorted(teacher_classes.items()):
    distinct_subjs = set()
    total_class_count = 0
    
    rows = []
    for block in STANDARD_TIME_BLOCKS:
        b_time = block["time"]
        is_brk = block["is_break"]
        
        row_data = {
            "id": block["id"],
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
                found = None
                
                # Check exact or approximate time slot match
                for raw_t, d_map in t_slots.items():
                    if d in d_map:
                        # check hour match
                        b_h = b_time[:5]
                        if b_h in raw_t or raw_t[:5] in b_time:
                            found = d_map[d]
                            break
                            
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
                        "grade": found['grade'],
                        "shift": found['shift'],
                        "label": f"{subj_name} - {found['section']}" if found['section'] and found['section'] != subj_name else subj_name,
                        "color": color,
                        "bg": color['bg'],
                        "border": color['border'],
                        "text": color['text']
                    }
                else:
                    row_data["days"][d] = None
                    
        rows.append(row_data)

    final_faculty_schedules[tchr] = {
        "teacher_name": tchr,
        "title": "Faculty Member",
        "total_classes": total_class_count,
        "total_teaching_periods": total_class_count,
        "subjects": sorted(list(distinct_subjs)),
        "rows": rows
    }

print(f"Extracted and unified comprehensive faculty timetables for {len(final_faculty_schedules)} teachers!")

# Print verification for Teacher Jairah and others
for sample_t in ["Teacher Jairah", "Teacher Aniah", "Ustadha Silfah", "Ustadh Ali", "Teacher Wendy"]:
    if sample_t in final_faculty_schedules:
        f_data = final_faculty_schedules[sample_t]
        print(f"\n{sample_t}: {f_data['total_classes']} classes, Subjects: {f_data['subjects']}")
        for r in f_data['rows']:
            for d, c in r['days'].items():
                if c and c.get('is_class'):
                    print(f"  {r['time']:<22} | {d:<10} -> {c['label']}")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.json', 'w') as f:
    json.dump(final_faculty_schedules, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.js', 'w') as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(final_faculty_schedules, indent=2)};\n")
    f.write(f"const AMIS_TEACHER_WEEKLY_SCHEDULES = window.AMIS_TEACHER_WEEKLY_SCHEDULES;\n")

print("\nSuccessfully synchronized all Faculty Timetables in JSON & JS!")

