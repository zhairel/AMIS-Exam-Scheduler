import json
import re
from datetime import datetime
from collections import defaultdict
from teacher_registry import TEACHER_REGISTRY, resolve_teacher

RAW_JSON_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/OFFICIAL_CLASS_SCHEDULE_raw.json'

with open(RAW_JSON_PATH) as f:
    raw_data = json.load(f)

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

def openpyxl_utils_col(c):
    res = ""
    while c > 0:
        c, rem = divmod(c - 1, 26)
        res = chr(65 + rem) + res
    return res

SUBJECT_CANONICAL_MAP = {
    'GMRC': 'GMRC',
    'ARABIC': 'Arabic',
    'QUR\'AN': 'Qur\'an',
    'QURAN': 'Qur\'an',
    'HADITH': 'Hadith',
    'SHAF': 'SHAF',
    'MATH': 'Mathematics',
    'MATHEMATICS': 'Mathematics',
    'GEN MATH': 'General Mathematics',
    'GENERAL MATHEMATICS': 'General Mathematics',
    'PRE-CAL': 'Pre-Calculus',
    'PRE CALCULUS': 'Pre-Calculus',
    'BASIC CALCULUS': 'Basic Calculus',
    'STATISTICS': 'Statistics and Probability',
    'STATISTICS AND PROBABILITY': 'Statistics and Probability',
    'SCIENCE': 'Science',
    'GEN SCIENCE': 'General Science',
    'GENERAL SCIENCE': 'General Science',
    'GEN BIO 1': 'General Biology 1',
    'GEN BIO 2': 'General Biology 2',
    'BIOLOGY': 'Biology',
    'BIOLOGY 12': 'Biology 12',
    'GEN. PHYSICS 1': 'General Physics 1',
    'GENERAL PHYSICS 1': 'General Physics 1',
    'GENERAL PHYSICS 2': 'General Physics 2',
    'GEN. PHYSICS 2': 'General Physics 2',
    'GENERAL CHEMISTRY 1': 'General Chemistry 1',
    'GENERAL CHEMISTRY 2': 'General Chemistry 2',
    'EARTH SCIENCE': 'Earth Science',
    'DRRR': 'Disaster Readiness & Risk Reduction',
    'ENGLISH': 'English',
    'READING AND LITERACY': 'Reading and Literacy',
    'R & L': 'Reading and Literacy',
    'LANGUAGE': 'Language',
    'ORAL COM': 'Oral Communication',
    '21ST LIT': '21st Century Literature',
    '21ST CENTURY LITERATURE': '21st Century Literature',
    'EAPP': 'English for Academic and Professional Purposes',
    'FILIPINO': 'Filipino',
    'MAKABANSA': 'Makabansa',
    'AP': 'Araling Panlipunan',
    'ARALING PANLIPUNAN': 'Araling Panlipunan',
    'SOC.SCI': 'Social Science',
    'SOCIAL SCIENCE': 'Social Science',
    'MAPEH': 'MAPEH',
    'PE': 'Physical Education',
    'PE 11': 'Physical Education 11',
    'PE 12': 'Physical Education 12',
    'TLE': 'Technology and Livelihood Education',
    'ENTREPRENEURSHIP': 'Entrepreneurship',
    'ENTREP': 'Entrepreneurship',
    'MIL': 'Media and Information Literacy',
    'PRAC. RES. 1': 'Practical Research 1',
    'PRAC. RES. 2': 'Practical Research 2',
    'PRACTICAL RESEARCH 2': 'Practical Research 2',
    'CAPSTONE': 'Research/Capstone Project',
    'RESEARCH/CAPSTONE PROJECT': 'Research/Capstone Project',
    '3 I\'S': 'Inquiries, Investigations, and Immersions',
    '3IS': 'Inquiries, Investigations, and Immersions',
    '3 I’S': 'Inquiries, Investigations, and Immersions',
    'PPITTP': 'Pambungad sa Pilosopiya ng Tao',
    'PHILO': 'Introduction to Philosophy of the Human Person',
    'PHILOSOPHY': 'Introduction to Philosophy of the Human Person',
    'PERDEV': 'Personal Development',
    'PSKP': 'Pagbasa at Pagsusuri ng Iba\'t Ibang Teksto',
    'PAGSULAT SA FIL': 'Pagsulat sa Filipino sa Piling Larangan',
    'PFPL': 'Pagsulat sa Filipino sa Piling Larangan',
    'KOMPAN': 'Komunikasyon at Pananaliksik',
    'LCS': 'Life and Career Skills',
    'UCSP': 'Understanding Culture, Society, and Politics',
    'ESP': 'Edukasyon sa Pagpapakatao',
    'VALUES ED': 'Values Education',
    'HOMEROOM': 'Homeroom Guidance',
    'HOMEROOM GUIDANCE': 'Homeroom Guidance',
    'HG': 'Homeroom Guidance',
    'ARAL READING': 'ARAL Reading',
    'ARAL MATH': 'ARAL Math',
    'ARAL SCIENCE': 'ARAL Science',
    'ARAL PROGRAM': 'ARAL Program',
    'CIRCLE TIME 1': 'Circle Time 1',
    'CIRCLE TIME 2': 'Circle Time 2',
    'CT 1': 'Circle Time 1',
    'CT 2': 'Circle Time 2',
    'MEETING TIME': 'Meeting Time',
    'WRAP-UP TIME': 'Wrap-Up Time'
}

def resolve_subject(raw_str):
    if not raw_str:
        return None, "Unassigned Subject"
    
    clean = raw_str.strip()
    clean_no_teacher = re.sub(r'(?i)\s*-\s*(tchr|teacher|ust|ustadh|ustadha|alim|sir|tr).*$', '', clean).strip()
    clean_no_grade = re.sub(r'(?i)\b(grade\s*\d+|g\d+|k\d+|kinder\s*\d+|7&8|9&10|f2f|odl|mix|boys|girls|1st shift|2nd shift)\b', '', clean_no_teacher).strip()
    clean_no_grade = re.sub(r'[\(\)]', '', clean_no_grade).strip()
    
    clean_up = clean_no_grade.upper()
    for key, cname in SUBJECT_CANONICAL_MAP.items():
        if clean_up == key or clean_up.startswith(key + ' ') or clean_up.endswith(' ' + key) or (' ' + key + ' ') in clean_up:
            subj_id = f"subj_{cname.lower().replace(' ', '_').replace('/', '_').replace('&', 'and').replace('\'', '')}"
            return subj_id, cname
            
    subj_title = clean_no_grade.title() if clean_no_grade else clean.title()
    subj_id = f"subj_{subj_title.lower().replace(' ', '_').replace('/', '_').replace('&', 'and').replace('\'', '')}"
    return subj_id, subj_title

def parse_time_range(raw_t):
    if not raw_t:
        return None, None, None, "Missing time string"
    s = str(raw_t).strip()
    s = re.sub(r'(\d{1,2}:\d{2}):00\b', r'\1', s)
    
    times = re.findall(r'(\d{1,2}:\d{2})', s)
    has_am = bool(re.search(r'(?i)\b(a\.m\.|am)\b', s))
    has_pm = bool(re.search(r'(?i)\b(p\.m\.|pm)\b', s))
    
    if len(times) >= 2:
        t1, t2 = times[0], times[1]
        h1, m1_val = int(t1.split(':')[0]), t1.split(':')[1]
        h2, m2_val = int(t2.split(':')[0]), t2.split(':')[1]
        
        if has_pm and not has_am:
            merid1 = 'AM' if h1 in [7, 8, 9, 10, 11] and h2 in [12, 1, 2, 3] else 'PM'
            merid2 = 'PM'
        elif has_am and not has_pm:
            merid1 = 'AM'
            merid2 = 'AM'
        else:
            merid1 = 'AM' if h1 in [7, 8, 9, 10, 11] else 'PM'
            merid2 = 'AM' if h2 in [7, 8, 9, 10, 11] else 'PM'
            
        start_fmt = f"{h1:02d}:{m1_val} {merid1}"
        end_fmt = f"{h2:02d}:{m2_val} {merid2}"
        
        h1_24 = h1 if merid1 == 'AM' or h1 == 12 else h1 + 12
        if merid1 == 'AM' and h1 == 12: h1_24 = 0
        h2_24 = h2 if merid2 == 'AM' or h2 == 12 else h2 + 12
        if merid2 == 'AM' and h2 == 12: h2_24 = 0
        
        tot1 = h1_24 * 60 + int(m1_val)
        tot2 = h2_24 * 60 + int(m2_val)
        dur = tot2 - tot1
        if dur < 0: dur += 24 * 60
        
        return start_fmt, end_fmt, dur, None
    elif len(times) == 1:
        t1 = times[0]
        h1, m1_val = int(t1.split(':')[0]), t1.split(':')[1]
        merid1 = 'AM' if (has_am or h1 in [7, 8, 9, 10, 11]) and not has_pm else 'PM'
        start_fmt = f"{h1:02d}:{m1_val} {merid1}"
        return start_fmt, None, None, None
        
    return None, None, None, f"Malformed time string: {raw_t}"

print("Building Master Single-Source Class Schedule from OFFICIAL_CLASS_SCHEDULE_raw.json...")

sheets_dict = {s['name']: s for s in raw_data['sheets']}

all_sections = []
audit_warnings = []
flat_schedule_records = []

# Exact active section sheets: ELEM, HS SCHED (NEW), and SHS
target_sheets = ['ELEM', 'HS SCHED (NEW)', 'SHS']

for sname in target_sheets:
    if sname not in sheets_dict:
        continue
    sheet = sheets_dict[sname]
    
    cell_map = {}
    for c in sheet['nonempty_cells']:
        cell_map[(c['row'], c['col'])] = c['value']
        
    merged_map = {}
    for m_str in sheet['merged_ranges']:
        parts = m_str.split(':')
        if len(parts) == 2:
            def coord_to_rc(coord):
                m = re.match(r'([A-Z]+)(\d+)', coord)
                col_letters, r_str = m.group(1), int(m.group(2))
                c_num = 0
                for ch in col_letters:
                    c_num = c_num * 26 + (ord(ch) - ord('A') + 1)
                return r_str, c_num
                
            r1, c1 = coord_to_rc(parts[0])
            r2, c2 = coord_to_rc(parts[1])
            top_val = cell_map.get((r1, c1))
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    merged_map[(r, c)] = top_val

    max_r = max([c['row'] for c in sheet['nonempty_cells']] or [1])
    max_c = max([c['col'] for c in sheet['nonempty_cells']] or [1])
    
    tables = []
    for r in range(1, max_r + 1):
        for c in range(1, max_c + 1):
            val = merged_map.get((r, c), cell_map.get((r, c)))
            if val and isinstance(val, str):
                s_up = val.strip().upper()
                if any(k in s_up for k in ['GRADE', 'KINDER', 'SCHEDULE', 'K1', 'K2']) and len(s_up) < 80 and not any(k in s_up for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'DEPARTURE']):
                    for tr in [r+1, r+2]:
                        r_vals = [str(merged_map.get((tr, cc), cell_map.get((tr, cc)))).lower() for cc in range(c, min(max_c+1, c+5))]
                        if any('time' in x or 'mins' in x or 'minutes' in x or 'sunday' in x for x in r_vals):
                            tables.append({
                                'sheet': sname,
                                'title': val.strip(),
                                'title_row': r,
                                'time_row': tr,
                                'col': c,
                                'cell_coord': f"{openpyxl_utils_col(c)}{r}"
                            })
                            break

    tables.sort(key=lambda t: (t['col'], t['title_row']))
    for i, t in enumerate(tables):
        next_r = None
        for other in tables:
            if other != t and other['title_row'] > t['title_row'] and abs(other['col'] - t['col']) <= 5:
                if next_r is None or other['title_row'] < next_r:
                    next_r = other['title_row']
        t['end_row'] = next_r - 1 if next_r else min(max_r, t['time_row'] + 25)

    seen_sec_titles = set()
    for t in tables:
        raw_title = t['title']
        if raw_title in seen_sec_titles:
            continue
        seen_sec_titles.add(raw_title)
        
        s_up = raw_title.upper()
        dept = "Elementary"
        if any(k in s_up for k in ['GRADE 7', 'GRADE 8', 'GRADE 9', 'GRADE 10', '7 & 8', '9 & 10', '7&8', '9&10']):
            dept = "Junior High School"
        elif any(k in s_up for k in ['GRADE 11', 'GRADE 12', 'SHS']):
            dept = "Senior High School"
        elif 'KINDER' in s_up or 'K1' in s_up or 'K2' in s_up:
            dept = "Kindergarten"
            
        grade = "Grade"
        m_g = re.search(r'\b(GRADE\s*\d+|KINDER\s*\d+|K1|K2|7\s*&\s*8|9\s*&\s*10)\b', s_up)
        if m_g: grade = m_g.group(1).title()
        
        shift = "F2F"
        if '2ND SHIFT' in s_up or 'SECOND SHIFT' in s_up:
            shift = "ODL - 2ND SHIFT"
        elif '1ST SHIFT' in s_up or 'FIRST SHIFT' in s_up:
            shift = "ODL - 1ST SHIFT"
        elif 'ODL' in s_up:
            shift = "ODL"
            
        periods = []
        c_time = t['col']
        c_mins = t['col'] + 1
        c_days_start = t['col'] + 2
        
        for r in range(t['time_row'] + 1, t['end_row'] + 1):
            time_raw = merged_map.get((r, c_time), cell_map.get((r, c_time)))
            mins_raw = merged_map.get((r, c_mins), cell_map.get((r, c_mins)))
            
            if not time_raw and not mins_raw:
                continue
                
            start_t, end_t, dur_calc, time_err = parse_time_range(time_raw)
            if time_err:
                audit_warnings.append({
                    "type": "MALFORMED_TIME",
                    "sheet": sname,
                    "cell": f"{openpyxl_utils_col(c_time)}{r}",
                    "section": raw_title,
                    "raw_value": str(time_raw),
                    "message": time_err
                })
                
            time_str = f"{start_t} – {end_t}" if start_t and end_t else (start_t or str(time_raw))
            mins_str = f"{mins_raw} min." if str(mins_raw).isdigit() else str(mins_raw or "-")
            
            if dur_calc and str(mins_raw).isdigit():
                if int(mins_raw) != dur_calc:
                    audit_warnings.append({
                        "type": "DURATION_MISMATCH",
                        "sheet": sname,
                        "cell": f"{openpyxl_utils_col(c_mins)}{r}",
                        "section": raw_title,
                        "time_range": time_str,
                        "calculated_duration": dur_calc,
                        "table_minutes": int(mins_raw),
                        "message": f"Time range calculates to {dur_calc}m but table minutes column says {mins_raw}m"
                    })
                    
            day_cells = {}
            has_any = False
            for didx, dname in enumerate(DAYS):
                col_idx = c_days_start + didx
                c_coord = f"{openpyxl_utils_col(col_idx)}{r}"
                raw_cell_val = merged_map.get((r, col_idx), cell_map.get((r, col_idx)))
                
                if raw_cell_val and str(raw_cell_val).strip():
                    has_any = True
                    c_txt = str(raw_cell_val).strip()
                    
                    is_break = any(k in c_txt.lower() for k in ['recess', 'assembly', 'lunch', 'departure', 'salah', 'transition', 'homeroom', 'break'])
                    
                    t_obj = resolve_teacher(c_txt)
                    tid = t_obj['id'] if t_obj else None
                    tname = t_obj['canonical_name'] if t_obj else ("Assigned Faculty" if is_break else c_txt)
                    
                    sub_id, sub_name = resolve_subject(c_txt)
                    
                    if not is_break and not tid:
                        audit_warnings.append({
                            "type": "MISSING_TEACHER_MAPPING",
                            "sheet": sname,
                            "cell": c_coord,
                            "section": raw_title,
                            "day": dname,
                            "time": time_str,
                            "raw_text": c_txt,
                            "message": f"Could not match teacher in '{c_txt}' to canonical teacher registry"
                        })
                        
                    cell_obj = {
                        "label": c_txt,
                        "subject": sub_name,
                        "subject_id": sub_id,
                        "teacher": tname,
                        "teacher_id": tid,
                        "is_break": is_break,
                        "raw_cell": c_coord,
                        "source_sheet": sname
                    }
                    day_cells[dname] = cell_obj
                    
                    if not is_break:
                        flat_schedule_records.append({
                            "section_id": f"sec_{len(all_sections)+1}",
                            "section_name": raw_title,
                            "department": dept,
                            "grade": grade,
                            "shift": shift,
                            "day": dname,
                            "time": time_str,
                            "start_time": start_t,
                            "end_time": end_t,
                            "duration_minutes": dur_calc or (int(mins_raw) if str(mins_raw).isdigit() else 40),
                            "subject": sub_name,
                            "subject_id": sub_id,
                            "teacher": tname,
                            "teacher_id": tid,
                            "source_cell": c_coord,
                            "source_sheet": sname,
                            "raw_text": c_txt
                        })
                else:
                    day_cells[dname] = None
                    
            if not has_any and not start_t:
                continue
                
            labels = [c['label'] for c in day_cells.values() if c]
            is_merged = (len(labels) == 5 and len(set(labels)) == 1)
            
            p_obj = {
                "period_num": len(periods) + 1,
                "time": time_str,
                "minutes": mins_str,
                "is_merged_all_days": is_merged
            }
            if is_merged and day_cells['Sunday']:
                p_obj['label'] = day_cells['Sunday']['label']
                p_obj['subject'] = day_cells['Sunday']['subject']
                p_obj['subject_id'] = day_cells['Sunday']['subject_id']
                p_obj['teacher'] = day_cells['Sunday']['teacher']
                p_obj['teacher_id'] = day_cells['Sunday']['teacher_id']
                p_obj['is_break'] = day_cells['Sunday']['is_break']
                p_obj['source_cell'] = day_cells['Sunday']['raw_cell']
                p_obj['source_sheet'] = sname
            else:
                p_obj['days'] = day_cells
                
            periods.append(p_obj)
            
        all_sections.append({
            "id": f"sec_{len(all_sections)+1}",
            "section_name": raw_title,
            "department": dept,
            "grade_level": grade,
            "shift": shift,
            "total_periods": len(periods),
            "source_sheet": sname,
            "source_cell": t['cell_coord'],
            "periods": periods
        })

print(f"Reconstructed {len(all_sections)} sections with {len(flat_schedule_records)} distinct class sessions.")

# Conflict and overlap audits on flat_schedule_records
teacher_slot_usage = defaultdict(list)
section_slot_usage = defaultdict(list)

for rec in flat_schedule_records:
    tid = rec['teacher_id']
    sec_name = rec['section_name']
    day = rec['day']
    t_str = rec['time']
    
    if tid:
        teacher_slot_usage[(tid, day, t_str)].append(rec)
    section_slot_usage[(sec_name, day, t_str)].append(rec)

for (tid, day, t_str), recs in teacher_slot_usage.items():
    if len(recs) > 1:
        distinct_secs = set(r['section_name'] for r in recs)
        if len(distinct_secs) > 1:
            tname = recs[0]['teacher']
            audit_warnings.append({
                "type": "TEACHER_SCHEDULE_CONFLICT",
                "teacher_id": tid,
                "teacher_name": tname,
                "day": day,
                "time": t_str,
                "conflicting_sections": list(distinct_secs),
                "message": f"Teacher '{tname}' scheduled concurrently in {list(distinct_secs)} on {day} at {t_str}"
            })

for (sec_name, day, t_str), recs in section_slot_usage.items():
    if len(recs) > 1:
        audit_warnings.append({
            "type": "SECTION_DOUBLE_SCHEDULED",
            "section_name": sec_name,
            "day": day,
            "time": t_str,
            "sessions": [f"{r['subject']} ({r['teacher']})" for r in recs],
            "message": f"Section '{sec_name}' scheduled twice on {day} at {t_str}"
        })

print(f"Total audit warnings/flags recorded: {len(audit_warnings)}")

# Dynamically derive Faculty Timetable from flat_schedule_records!
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

def map_time_to_row_id(time_str):
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

def start_time_to_minutes(st):
    if not st: return 0
    st_str = str(st).strip()
    parts = st_str.split(' ')
    if len(parts) < 2: return 0
    hm = parts[0].split(':')
    try:
        h = int(hm[0])
        m = int(hm[1]) if len(hm) > 1 else 0
    except:
        return 0
    ampm = parts[1].upper()
    if ampm == 'PM' and h != 12: h += 12
    if ampm == 'AM' and h == 12: h = 0
    return h * 60 + m

faculty_timetables = {}

for tinfo in sorted(TEACHER_REGISTRY, key=lambda x: x['canonical_name']):
    tid = tinfo['id']
    c_name = tinfo['canonical_name']
    dept = tinfo['department']
    title = tinfo['title']
    
    t_recs = [r for r in flat_schedule_records if r['teacher_id'] == tid]
    distinct_subjs = sorted(list(set(r['subject'] for r in t_recs)))
    total_class_count = len(t_recs)
    
    # Extract unique time slots for this specific teacher
    unique_slots = []
    seen_slots = set()
    for r in t_recs:
        t_key = (r['start_time'], r['end_time'], r['duration_minutes'], r['time'])
        if t_key not in seen_slots:
            seen_slots.add(t_key)
            unique_slots.append(t_key)
            
    # Sort chronologically by start time
    unique_slots.sort(key=lambda s: start_time_to_minutes(s[0] or s[3]))
    
    rows = []
    for s in unique_slots:
        start_t, end_t, dur, t_str = s
        slot_clean = str(start_t or t_str or 'slot').replace(' ', '_').replace(':', '').replace('-', '_').replace('–', '_')
        rid = f"slot_{slot_clean}"
        
        row_data = {
            "id": rid,
            "time": t_str,
            "start_time": start_t,
            "end_time": end_t,
            "minutes": f"{dur} min.",
            "duration_minutes": dur,
            "is_break": False,
            "days": {}
        }
        
        for d in DAYS:
            matches = [r for r in t_recs if r['day'] == d and r['time'] == t_str]
            if len(matches) == 1:
                rec = matches[0]
                sec_short = re.sub(r'\(.*?\)', '', rec['section_name']).strip().replace('GRADE ', 'G').replace('Grade ', 'G').replace('Kinder ', 'K')
                if 'FACE TO FACE' in rec['section_name'].upper() or 'F2F' in rec['section_name'].upper():
                    sec_short += ' (F2F)'
                    
                color = get_subject_color(rec['subject'])
                row_data["days"][d] = {
                    "occupied": True,
                    "is_class": True,
                    "is_break": False,
                    "has_conflict": False,
                    "subject": rec['subject'],
                    "subject_id": rec['subject_id'],
                    "section": rec['section_name'],
                    "section_short": sec_short,
                    "grade": rec['grade'],
                    "shift": rec['shift'],
                    "modality": rec['shift'],
                    "start_time": rec['start_time'],
                    "end_time": rec['end_time'],
                    "time": rec['time'],
                    "duration_minutes": rec['duration_minutes'],
                    "label": f"{rec['subject']} - {sec_short}",
                    "source_cell": rec['source_cell'],
                    "source_sheet": rec['source_sheet'],
                    "color": color,
                    "bg": color['bg'],
                    "border": color['border'],
                    "text": color['text']
                }
            elif len(matches) > 1:
                # Multiple classes scheduled in exact same slot on the same day (Conflict!)
                sec_shorts = []
                for m in matches:
                    sh = re.sub(r'\(.*?\)', '', m['section_name']).strip().replace('GRADE ', 'G').replace('Grade ', 'G').replace('Kinder ', 'K')
                    if 'FACE TO FACE' in m['section_name'].upper() or 'F2F' in m['section_name'].upper():
                        sh += ' (F2F)'
                    sec_shorts.append(sh)
                
                row_data["days"][d] = {
                    "occupied": True,
                    "is_class": True,
                    "is_break": False,
                    "has_conflict": True,
                    "conflict_message": "TEACHER SCHEDULE CONFLICT",
                    "subject": matches[0]['subject'],
                    "section": " / ".join(m['section_name'] for m in matches),
                    "section_short": " / ".join(sec_shorts),
                    "grade": matches[0]['grade'],
                    "shift": matches[0]['shift'],
                    "modality": matches[0]['shift'],
                    "start_time": matches[0]['start_time'],
                    "end_time": matches[0]['end_time'],
                    "time": matches[0]['time'],
                    "duration_minutes": matches[0]['duration_minutes'],
                    "label": f"⚠️ CONFLICT: {matches[0]['subject']} - {' / '.join(sec_shorts)}",
                    "classes": matches,
                    "color": {"bg": "#fee2e2", "border": "#ef4444", "text": "#991b1b"},
                    "bg": "#fee2e2",
                    "border": "#ef4444",
                    "text": "#991b1b"
                }
            else:
                row_data["days"][d] = None
                
        rows.append(row_data)

    faculty_timetables[tid] = {
        "teacher_id": tid,
        "faculty_id": tid,
        "teacher_name": c_name,
        "canonical_name": c_name,
        "department": dept,
        "title": title,
        "total_classes": total_class_count,
        "total_teaching_periods": total_class_count,
        "subjects": distinct_subjs,
        "rows": rows
    }

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json', 'w') as f:
    json.dump(all_sections, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.js', 'w') as f:
    f.write(f"window.CLASS_SCHEDULES_DATA = {json.dumps(all_sections, indent=2)};\n")
    f.write(f"const CLASS_SCHEDULES_DATA = window.CLASS_SCHEDULES_DATA;\n")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.json', 'w') as f:
    json.dump(faculty_timetables, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/teacher_weekly_schedules.js', 'w') as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(faculty_timetables, indent=2)};\n")
    f.write(f"const AMIS_TEACHER_WEEKLY_SCHEDULES = window.AMIS_TEACHER_WEEKLY_SCHEDULES;\n")

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/schedule_audit_report.json', 'w') as f:
    json.dump({
        "generated_at": datetime.now().isoformat(),
        "source_file": "OFFICIAL_CLASS_SCHEDULE_raw.json",
        "total_sections": len(all_sections),
        "total_active_class_sessions": len(flat_schedule_records),
        "total_warnings": len(audit_warnings),
        "warnings": audit_warnings
    }, f, indent=2)

print("\n✓ Synchronized Class Schedules & Faculty Timetables from OFFICIAL_CLASS_SCHEDULE_raw.json!")
print(f"✓ Saved class_schedules_data.json ({len(all_sections)} sections)")
print(f"✓ Saved teacher_weekly_schedules.json ({len(faculty_timetables)} teachers dynamically linked)")
print(f"✓ Saved schedule_audit_report.json ({len(audit_warnings)} warnings flagged for manual review)")
