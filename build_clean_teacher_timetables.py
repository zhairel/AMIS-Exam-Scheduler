import json
import re
from collections import defaultdict

CLASS_DATA_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json'

with open(CLASS_DATA_PATH) as f:
    sections = json.load(f)

from parse_all_authoritative_schedules import normalize_teacher_name

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

STANDARD_TIME_BLOCKS = [
    {
        "id": "f2f_assembly",
        "time": "07:30 AM – 07:40 AM",
        "minutes": "10 min.",
        "is_break": True,
        "break_title": "GENERAL ASSEMBLY (F2F)",
        "shift_type": "F2F"
    },
    {
        "id": "p1_f2f",
        "time": "07:40 AM – 08:25 AM",
        "minutes": "45 min.",
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "p2_f2f",
        "time": "08:25 AM – 09:05 AM",
        "minutes": "40 min.",
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "p3_f2f",
        "time": "09:05 AM – 09:45 AM",
        "minutes": "40 min.",
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "f2f_recess",
        "time": "09:45 AM – 10:00 AM",
        "minutes": "15 min.",
        "is_break": True,
        "break_title": "RECESS",
        "shift_type": "F2F"
    },
    {
        "id": "p4_f2f",
        "time": "10:00 AM – 10:45 AM",
        "minutes": "45 min.",
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "p5_f2f",
        "time": "10:45 AM – 11:30 AM",
        "minutes": "45 min.",
        "is_break": False,
        "shift_type": "F2F"
    },
    {
        "id": "f2f_lunch",
        "time": "11:30 AM – 12:30 PM",
        "minutes": "60 min.",
        "is_break": True,
        "break_title": "LUNCH and SALAH",
        "shift_type": "F2F"
    },
    {
        "id": "odl1_assembly",
        "time": "12:30 PM – 12:40 PM",
        "minutes": "10 min.",
        "is_break": True,
        "break_title": "GENERAL ASSEMBLY (FIRST SHIFT)",
        "shift_type": "ODL 1st Shift"
    },
    {
        "id": "p6_f2f_odl1",
        "time": "12:40 PM – 01:25 PM",
        "minutes": "45 min.",
        "is_break": False,
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "p7_f2f_odl1",
        "time": "01:25 PM – 02:10 PM",
        "minutes": "45 min.",
        "is_break": False,
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "p8_f2f_odl1",
        "time": "02:15 PM – 03:00 PM",
        "minutes": "45 min.",
        "is_break": False,
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "f2f_salah_departure",
        "time": "03:00 PM – 03:30 PM",
        "minutes": "30 min.",
        "is_break": True,
        "break_title": "SALAH & DEPARTURE (F2F) • HOMEROOM GUIDANCE (ODL 1)",
        "shift_type": "F2F / ODL 1"
    },
    {
        "id": "odl2_assembly",
        "time": "03:30 PM – 03:40 PM",
        "minutes": "10 min.",
        "is_break": True,
        "break_title": "GENERAL ASSEMBLY (SECOND SHIFT)",
        "shift_type": "ODL 2nd Shift"
    },
    {
        "id": "p1_odl2",
        "time": "03:40 PM – 04:20 PM",
        "minutes": "40 min.",
        "is_break": False,
        "shift_type": "ODL 2nd Shift"
    },
    {
        "id": "p2_odl2",
        "time": "04:30 PM – 05:10 PM",
        "minutes": "40 min.",
        "is_break": False,
        "shift_type": "ODL 2nd Shift"
    },
    {
        "id": "p3_odl2",
        "time": "05:20 PM – 06:00 PM",
        "minutes": "40 min.",
        "is_break": False,
        "shift_type": "ODL 2nd Shift"
    }
]

def get_subject_color(subj):
    s = (subj or "").lower()
    if any(k in s for k in ['gmrc', 'values', 'esp', 'homeroom', 'hg']):
        return {'bg': '#dcfce7', 'border': '#86efac', 'text': '#14532d'}
    if any(k in s for k in ['arabic', "qur'an", 'quran', 'hadith', 'shaf', 'islamic']):
        return {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#581c87'}
    if any(k in s for k in ['math', 'mathematics', 'physics', 'algebra', 'calculus']):
        return {'bg': '#e0f2fe', 'border': '#7dd3fc', 'text': '#0369a1'}
    if any(k in s for k in ['science', 'biology', 'chemistry', 'gen science']):
        return {'bg': '#ccfbf1', 'border': '#5eead4', 'text': '#115e59'}
    if any(k in s for k in ['english', 'reading', 'literacy', 'language', 'lit', 'circle', 'meeting']):
        return {'bg': '#fef3c7', 'border': '#fde047', 'text': '#854d0e'}
    if any(k in s for k in ['filipino', 'makabansa', 'ap', 'araling panlipunan', 'social science', 'soc.sci']):
        return {'bg': '#ffedd5', 'border': '#fdba74', 'text': '#9a3412'}
    if any(k in s for k in ['mapeh', 'pe', 'tle', 'mil', 'practical research']):
        return {'bg': '#fae8ff', 'border': '#f0abfc', 'text': '#86198f'}
    return {'bg': '#f1f5f9', 'border': '#cbd5e1', 'text': '#334155'}

# Extract all teacher classes directly from class_schedules_data.json
teacher_raw_assignments = defaultdict(list)

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
                        teacher_raw_assignments[tchr].append({
                            'day': d,
                            'time': t_str,
                            'minutes': m_str,
                            'subject': subj,
                            'section': sname,
                            'grade': grade,
                            'shift': shift
                        })
        else:
            for d, cell in (p.get('days') or {}).items():
                if cell and not cell.get('is_break'):
                    tchr_raw = cell.get('teacher', '').strip()
                    tchr = normalize_teacher_name(tchr_raw)
                    subj = cell.get('subject', '').strip()
                    if tchr and tchr != "Assigned Faculty":
                        teacher_raw_assignments[tchr].append({
                            'day': d,
                            'time': t_str,
                            'minutes': m_str,
                            'subject': subj,
                            'section': sname,
                            'grade': grade,
                            'shift': shift
                        })

all_teacher_schedules = {}

for tchr, assign_list in sorted(teacher_raw_assignments.items()):
    # Map assignments by (time, day)
    assign_by_slot = defaultdict(dict)
    for a in assign_list:
        assign_by_slot[a['time']][a['day']] = a

    # Build weekly rows
    rows = []
    
    # 1. Use standard time blocks
    # Match teacher assignments into standard time blocks
    used_assignments = set()
    
    for block in STANDARD_TIME_BLOCKS:
        row_id = block["id"]
        is_brk = block["is_break"]
        b_time = block["time"]
        
        row_data = {
            "id": row_id,
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
            # Find matching assigned classes for this time window
            for d in DAYS:
                found_assign = None
                # Exact time match
                if b_time in assign_by_slot and d in assign_by_slot[b_time]:
                    found_assign = assign_by_slot[b_time][d]
                else:
                    # Fuzzy time match within shift
                    for a_time, d_map in assign_by_slot.items():
                        if d in d_map:
                            cand = d_map[d]
                            # Check start hour overlap
                            b_start = b_time[:5]
                            if b_start in a_time:
                                found_assign = cand
                                break
                                
                if found_assign:
                    color = get_subject_color(found_assign['subject'])
                    row_data["days"][d] = {
                        "is_break": False,
                        "is_class": True,
                        "subject": found_assign['subject'],
                        "section": found_assign['section'],
                        "grade": found_assign['grade'],
                        "shift": found_assign['shift'],
                        "label": f"{found_assign['subject']} - {found_assign['section']}",
                        "bg_color": color['bg'],
                        "border_color": color['border'],
                        "text_color": color['text']
                    }
                else:
                    row_data["days"][d] = None
                    
        rows.append(row_data)

    total_classes = len(assign_list)
    all_teacher_schedules[tchr] = {
        "teacher_name": tchr,
        "title": "Faculty Member",
        "total_teaching_periods": total_classes,
        "rows": rows
    }

print(f"Built authoritative faculty weekly timetables for {len(all_teacher_schedules)} teachers!")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.json', 'w') as f:
    json.dump(all_teacher_schedules, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.js', 'w') as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(all_teacher_schedules, indent=2)};\n")
    f.write(f"const AMIS_TEACHER_WEEKLY_SCHEDULES = window.AMIS_TEACHER_WEEKLY_SCHEDULES;\n")

print("Saved teacher_weekly_schedules.json and teacher_weekly_schedules.js successfully!")

