import openpyxl
import json
import re
from collections import defaultdict
from teacher_registry import resolve_teacher

EXCEL_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/SCHEDULE SY 2026-2027 TW.xlsx'
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

def format_time_clean(raw_t):
    if not raw_t: return ""
    s = str(raw_t).strip()
    
    # Remove seconds if present e.g. 03:00:00 -> 03:00
    s = re.sub(r'(\d{1,2}:\d{2}):00\b', r'\1', s)
    
    # Standardize am/pm
    s = re.sub(r'(?i)\b(a\.m\.|am)\b', 'AM', s)
    s = re.sub(r'(?i)\b(p\.m\.|pm)\b', 'PM', s)
    s = re.sub(r'(\d+:\d+)\s*-\s*(\d+:\d+)', r'\1 – \2', s)
    
    # If no AM/PM, infer based on hour
    if 'AM' not in s and 'PM' not in s:
        # Check start hour
        m = re.match(r'^(\d{1,2}):(\d{2})', s)
        if m:
            hh = int(m.group(1))
            if hh in [7, 8, 9, 10, 11]:
                s += ' AM'
            elif hh in [12, 1, 2, 3, 4, 5, 6]:
                s += ' PM'
                
    # Pad hour to 2 digits e.g. 7:30 AM -> 07:30 AM
    def pad_hour(m):
        hh = int(m.group(1))
        mm = m.group(2)
        return f"{hh:02d}:{mm}"
    s = re.sub(r'\b(\d{1}):(\d{2})\b', pad_hour, s)
    return s

def format_mins_clean(raw_m):
    if not raw_m: return "45 min."
    s = str(raw_m).strip()
    if s.endswith('.0'): s = s[:-2]
    if s == '-' or s == '0': return "-"
    if s.isdigit(): return f"{s} min."
    if 'min' not in s.lower() and 'm' not in s.lower():
        return f"{s} min."
    return s

def parse_teacher_from_text(text):
    if not text: return None, "Assigned Faculty"
    t_obj = resolve_teacher(text)
    if t_obj:
        return t_obj['id'], t_obj['canonical_name']
    return None, text.strip()

def parse_cell(cell_val):
    if not cell_val or not str(cell_val).strip():
        return None
    s = str(cell_val).strip()
    
    is_break = False
    s_low = s.lower()
    if any(k in s_low for k in ['recess', 'assembly', 'lunch', 'departure', 'salah', 'transition', 'homeroom', 'short break', 'break']):
        is_break = True
        
    tid, tchr = parse_teacher_from_text(s)
    
    subj = s
    if ' - ' in s:
        subj = s.split(' - ')[0].strip()
    elif ' — ' in s:
        subj = s.split(' — ')[0].strip()
        
    return {
        'label': s,
        'subject': subj,
        'teacher_id': tid,
        'teacher': tchr,
        'is_break': is_break
    }

def get_all_table_bounding_boxes():
    all_boxes = []
    seen_names = set()
    
    for sname in ['ELEM', 'HS SCHED (NEW)', 'SHS', 'HS SCHED']:
        ws = wb[sname]
        tables = []
        
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                v = ws.cell(row=r, column=c).value
                if v and isinstance(v, str):
                    s = v.strip().upper()
                    if any(k in s for k in ['GRADE', 'KINDER', 'SCHEDULE', 'K1', 'K2']) and len(s) < 80 and not any(k in s for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'DEPARTURE']):
                        for tr in [r+1, r+2]:
                            if tr <= ws.max_row:
                                r_vals = [str(ws.cell(row=tr, column=cc).value).lower() for cc in range(c, min(ws.max_column+1, c+5))]
                                if any('time' in x or 'mins' in x or 'minutes' in x or 'sunday' in x for x in r_vals):
                                    tables.append({
                                        'sheet': sname,
                                        'title': v.strip(),
                                        'title_row': r,
                                        'time_row': tr,
                                        'col': c,
                                        'end_row': None
                                    })
                                    break

        tables.sort(key=lambda t: (t['col'], t['title_row']))
        
        for i, t in enumerate(tables):
            next_t_row = None
            for other in tables:
                if other != t and other['title_row'] > t['title_row'] and abs(other['col'] - t['col']) <= 5:
                    if next_t_row is None or other['title_row'] < next_t_row:
                        next_t_row = other['title_row']
                        
            if next_t_row is not None:
                t['end_row'] = next_t_row - 1
            else:
                t['end_row'] = min(ws.max_row, t['time_row'] + 25)

        for t in tables:
            raw_title = t['title']
            if raw_title in seen_names:
                continue
            seen_names.add(raw_title)
            
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
                
            all_boxes.append({
                'sheet': t['sheet'],
                'name': raw_title,
                'dept': dept,
                'grade': grade,
                'shift': shift,
                'start_row': t['time_row'] + 1,
                'end_row': t['end_row'],
                'time_col': t['col'],
                'mins_col': t['col'] + 1,
                'days_col_start': t['col'] + 2
            })
            
    return all_boxes

table_boxes = get_all_table_bounding_boxes()
all_sections_data = []

for tinfo in table_boxes:
    ws = wb[tinfo['sheet']]
    sname = tinfo['name']
    dept = tinfo['dept']
    grade = tinfo['grade']
    shift = tinfo['shift']
    
    r_start = tinfo['start_row']
    r_end = tinfo['end_row']
    c_time = tinfo['time_col']
    c_mins = tinfo['mins_col']
    c_days_start = tinfo['days_col_start']
    
    periods = []
    
    for r in range(r_start, r_end + 1):
        time_raw = ws.cell(row=r, column=c_time).value
        mins_raw = ws.cell(row=r, column=c_mins).value
        
        if not time_raw and not mins_raw:
            continue
            
        time_str = format_time_clean(time_raw)
        mins_str = format_mins_clean(mins_raw)
        
        if any(k in time_str.upper() for k in ['TIME', 'MINUTES', 'SUNDAY', 'MONDAY', 'GRADE', 'KINDER', 'K1', 'K2']):
            continue
            
        day_cells = {}
        has_any_content = False
        for didx, dname in enumerate(DAYS):
            col_idx = c_days_start + didx
            cval = ws.cell(row=r, column=col_idx).value
            cell_parsed = parse_cell(cval)
            day_cells[dname] = cell_parsed
            if cell_parsed:
                has_any_content = True
                
        if not time_str and not has_any_content:
            continue
            
        labels = [c['label'] for c in day_cells.values() if c]
        is_merged = False
        merged_cell_info = None
        
        if len(labels) == 5 and len(set(labels)) == 1:
            is_merged = True
            merged_cell_info = day_cells['Sunday']
        elif len(labels) == 1 and day_cells['Sunday']:
            is_merged = True
            merged_cell_info = day_cells['Sunday']
            
        p_obj = {
            'period_num': len(periods) + 1,
            'time': time_str,
            'minutes': mins_str,
            'is_merged_all_days': is_merged
        }
        
        if is_merged and merged_cell_info:
            p_obj['label'] = merged_cell_info['label']
            p_obj['subject'] = merged_cell_info['subject']
            p_obj['teacher_id'] = merged_cell_info.get('teacher_id')
            p_obj['teacher'] = merged_cell_info.get('teacher', 'Assigned Faculty')
            p_obj['is_break'] = merged_cell_info['is_break']
        else:
            p_obj['days'] = day_cells
            
        periods.append(p_obj)
        
    all_sections_data.append({
        'id': f"sec_{len(all_sections_data)+1}",
        'section_name': sname,
        'department': dept,
        'grade_level': grade,
        'shift': shift,
        'total_periods': len(periods),
        'periods': periods
    })

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.json', 'w') as f:
    json.dump(all_sections_data, f, indent=2)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class_schedules_data.js', 'w') as f:
    f.write(f"window.CLASS_SCHEDULES_DATA = {json.dumps(all_sections_data, indent=2)};\n")
    f.write(f"const CLASS_SCHEDULES_DATA = window.CLASS_SCHEDULES_DATA;\n")

print(f"Successfully generated class_schedules_data.json and class_schedules_data.js for {len(all_sections_data)} sections!")

