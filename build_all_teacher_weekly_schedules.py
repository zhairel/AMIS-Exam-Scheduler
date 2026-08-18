#!/usr/bin/env python3
"""
build_all_teacher_weekly_schedules.py
Rebuilds teacher_weekly_schedules.json & .js directly from the canonical class dataset
class_schedules_data.json (ELEM + HS SCHED (NEW)).
Populates periods, total_classes, total_teaching_periods, subjects, and structured rows.
"""

import os
import json
from collections import defaultdict
from teacher_registry import resolve_teacher, TEACHER_REGISTRY

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "class_schedules_data.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)

def get_subj_color(sname):
    s = (sname or '').lower()
    if any(k in s for k in ['arabic', 'qur', 'hadith', 'shaf', 'islamic']):
        return {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#6b21a8'}
    if any(k in s for k in ['gmrc', 'values', 'esp']):
        return {'bg': '#dcfce7', 'border': '#86efac', 'text': '#166534'}
    if any(k in s for k in ['math', 'calculus', 'statistics']):
        return {'bg': '#e0f2fe', 'border': '#7dd3fc', 'text': '#0369a1'}
    if any(k in s for k in ['sci', 'physics', 'bio', 'chem']):
        return {'bg': '#ccfbf1', 'border': '#5eead4', 'text': '#0f766e'}
    if any(k in s for k in ['eng', 'language', 'reading', 'literacy', 'oral', '21st', 'lit']):
        return {'bg': '#fef3c7', 'border': '#fde047', 'text': '#854d0e'}
    if any(k in s for k in ['fil', 'ap', 'araling', 'makabansa', 'soc', 'pskp', 'pilosopiya']):
        return {'bg': '#ffedd5', 'border': '#fdba74', 'text': '#9a3412'}
    if any(k in s for k in ['mapeh', 'pe', 'tle', 'mil', 'prac', 'lcs']):
        return {'bg': '#fae8ff', 'border': '#f0abfc', 'text': '#86198f'}
    return {'bg': '#f1f5f9', 'border': '#cbd5e1', 'text': '#334155'}

# Initialize all canonical teachers
teacher_data = {}
for t in TEACHER_REGISTRY:
    teacher_data[t['id']] = {
        'teacher_id': t['id'],
        'teacher_name': t['canonical_name'],
        'canonical_name': t['canonical_name'],
        'department': t.get('department', 'Faculty'),
        'periods': [],
        'total_classes': 0,
        'total_teaching_periods': 0,
        'subjects': [],
        'rows': []
    }

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

for sec in sections:
    sname = sec['section_name']
    dept = sec['department']
    grade = sec['grade_level']
    shift = sec['shift']
    sec_id = sec['id']
    
    for p in sec.get('periods', []):
        time_str = p.get('time')
        mins_str = p.get('minutes')
        p_num = p.get('period_num')
        
        if p.get('is_merged_all_days'):
            if not p.get('is_break'):
                raw = p.get('label') or p.get('subject') or ''
                tchr = p.get('teacher')
                tid = p.get('teacher_id')
                t_res = resolve_teacher(tchr) or resolve_teacher(raw)
                if t_res:
                    tid = t_res['id']
                    tchr = t_res['canonical_name']
                if tid and tid in teacher_data:
                    for day in DAYS:
                        teacher_data[tid]['periods'].append({
                            'section_id': sec_id,
                            'section_name': sname,
                            'department': dept,
                            'grade_level': grade,
                            'shift': shift,
                            'period_num': p_num,
                            'time': time_str,
                            'minutes': mins_str,
                            'day': day,
                            'subject': p.get('subject') or raw,
                            'raw_label': raw
                        })
        else:
            for day, cell in (p.get('days') or {}).items():
                if cell and not cell.get('is_break'):
                    raw = cell.get('label') or cell.get('subject') or ''
                    tchr = cell.get('teacher')
                    tid = cell.get('teacher_id')
                    t_res = resolve_teacher(tchr) or resolve_teacher(raw)
                    if t_res:
                        tid = t_res['id']
                        tchr = t_res['canonical_name']
                    if tid and tid in teacher_data:
                        teacher_data[tid]['periods'].append({
                            'section_id': sec_id,
                            'section_name': sname,
                            'department': dept,
                            'grade_level': grade,
                            'shift': shift,
                            'period_num': p_num,
                            'time': time_str,
                            'minutes': mins_str,
                            'day': day,
                            'subject': cell.get('subject') or raw,
                            'raw_label': raw
                        })

# Build structured `rows` for each teacher
for tid, tinfo in teacher_data.items():
    tinfo['total_classes'] = len(tinfo['periods'])
    tinfo['total_teaching_periods'] = len(tinfo['periods'])
    tinfo['subjects'] = sorted(list(set(p['subject'] for p in tinfo['periods'])))
    
    by_time = defaultdict(lambda: {d: None for d in DAYS})
    time_order = []
    time_mins = {}
    
    for p in tinfo['periods']:
        t_str = p['time']
        if t_str not in by_time:
            time_order.append(t_str)
            time_mins[t_str] = p['minutes']
            
        d = p['day']
        color = get_subj_color(p['subject'])
        sec_short = p['section_name'].replace('GRADE ', 'G').replace('Grade ', 'G').replace('Kinder ', 'K')
        
        has_conflict = False
        if by_time[t_str][d] is not None:
            has_conflict = True
            
        by_time[t_str][d] = {
            'occupied': True,
            'is_class': True,
            'subject': p['subject'],
            'label': p['raw_label'],
            'section': p['section_name'],
            'section_short': sec_short,
            'modality': p['shift'],
            'shift': p['shift'],
            'color': color,
            'has_conflict': has_conflict
        }
        
    rows = []
    for t_str in time_order:
        rows.append({
            'time': t_str,
            'minutes': time_mins.get(t_str, '-'),
            'is_break': False,
            'days': by_time[t_str]
        })
        
    tinfo['rows'] = rows

# Save JSON and JS
with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.json"), "w", encoding="utf-8") as f:
    json.dump(teacher_data, f, indent=2, ensure_ascii=False)

with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.js"), "w", encoding="utf-8") as f:
    f.write(f"window.AMIS_TEACHER_WEEKLY_SCHEDULES = {json.dumps(teacher_data, indent=2, ensure_ascii=False)};\n")
    f.write("const AMIS_TEACHER_WEEKLY_SCHEDULES = window.AMIS_TEACHER_WEEKLY_SCHEDULES;\n")

print(f"✓ Successfully built teacher_weekly_schedules.json and .js for {len(teacher_data)} teachers!")
