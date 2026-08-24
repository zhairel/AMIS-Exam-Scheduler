import openpyxl
import re
import json

EXCEL_PATH = '/home/tatsuya/Projects/AMIS/amis_exam_calendar/SCHEDULE SY 2026-2027 TW.xlsx'
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

def normalize_teacher_name(raw):
    if not raw:
        return ''
    s = str(raw).strip()
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    
    # Strip prefix
    s_clean = re.sub(r'^(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)\s*', '', s, flags=re.IGNORECASE).strip()
    s_low = s_clean.lower()
    
    # Aliases
    if ('muh' in s_low and 'ali' in s_low) or s_low == 'ali' or s_low == 'muhammad ali' or s_low == 'mohammad ali':
        return 'Ustadh Ali'
    if 'jairah' in s_low or 'jayra' in s_low:
        return 'Teacher Jairah'
    if 'silfa' in s_low or 'silfah' in s_low:
        return 'Ustadha Silfah'
    if 'norhydie' in s_low or 'norhidi' in s_low:
        return 'Teacher Norhydie'
    if 'monisa' in s_low:
        return 'Teacher Monisa'
    if 'sitti' in s_low:
        return 'Teacher Sitti'
    if 'marham' in s_low:
        return 'Teacher Marham'
    if 'faidh' in s_low or 'faid' in s_low:
        return 'Ustadh Faidh'
    if 'obaydah' in s_low:
        return 'Ustadh Obaydah'
    if 'abdiraheem' in s_low or 'abdulraheem' in s_low:
        return 'Ustadh Abdiraheem'
    if 'saliha' in s_low:
        return 'Ustadha Saliha'
    if 'bustamante' in s_low:
        return 'Alim Bustamante'
    if 'mamonas' in s_low:
        return 'Alim Mamonas'
    if 'samsuddin' in s_low:
        return 'Alim Samsuddin'
    if 'abdulwahab' in s_low or 'abdul wahab' in s_low or 'abdul-wahab' in s_low:
        return 'Alim Abdulwahab'
    if 'dipatuan' in s_low:
        return 'Alim Dipatuan'
    if 'jaisam' in s_low or 'jaesam' in s_low:
        return 'Ustadh Jaisam'
    if 'raffy' in s_low:
        return 'Ustadh Raffy'
    if 'arvin' in s_low:
        return 'Teacher Arvin'
    if 'saimonah' in s_low:
        return 'Teacher Saimonah'
    if 'jenny' in s_low:
        return 'Teacher Jenny'
    if 'halnaisa' in s_low:
        return 'Teacher Halnaisa'
    if 'shanen' in s_low:
        return 'Teacher Shanen'
    if 'shirehan' in s_low or s_low == 'shi':
        return 'Teacher Shirehan'
    if 'abegail' in s_low:
        return 'Teacher Abegail'
    if 'rowena' in s_low:
        return 'Teacher Rowena'
    if 'nof' in s_low:
        return 'Teacher Nof'
    if 'thea' in s_low:
        return 'Teacher Thea'
    if 'nadzra' in s_low:
        return 'Teacher Nadzra'
    if 'sophia' in s_low:
        return 'Teacher Sophia'
    if 'ethel' in s_low:
        return 'Teacher Ethel'
    if 'mohaymen' in s_low or 'moh' in s_low:
        return 'Sir Mohaymen'
    if 'marie' in s_low:
        return 'Teacher Marie'
    if 'ahmad' in s_low:
        return 'Teacher Ahmad'
    if 'jerlyn' in s_low:
        return 'Teacher Jerlyn'
    if 'wendy' in s_low:
        return 'Teacher Wendy'
    if 'kat' in s_low:
        return 'Teacher Kat'
    if 'junaisa' in s_low:
        return 'Teacher Junaisa'
    if 'zara' in s_low:
        return 'Teacher Zara'
    if 'ersahad' in s_low:
        return 'Ustadh Ersahad'
    if 'hainur' in s_low:
        return 'Ustadha Hainur'
    if 'abdul karim' in s_low or 'abdulkarim' in s_low:
        return 'Alim Abdul Karim'
    if 'zuhora' in s_low:
        return 'Teacher Zuhora'
    if 'nashra' in s_low:
        return 'Teacher Nashra'
    if 'fahima' in s_low:
        return 'Teacher Fahima'
    if 'hamida' in s_low:
        return 'Teacher Hamida'
    if 'raihan' in s_low:
        return 'Teacher Raihan'
    if 'amerah' in s_low:
        return 'Teacher Amerah'
    
    return s

def parse_subject_and_teacher(cell_str):
    if not cell_str:
        return None, None
    s = cell_str.strip()
    if not s or any(k in s.upper() for k in ['GENERAL ASSEMBLY', 'RECESS', 'LUNCH', 'DEPARTURE', 'TRANSITION', 'SALAH']):
        return None, None
    
    # Common formats:
    # "Math - Tchr. Ahmad"
    # "Arabic - Alim Mamonas"
    # "English - Tchr. Jairah (7&8 Girls)"
    # "ARAL Reading - Tchr. Kat"
    # "Qur'an - Ust. Obaydah"
    # "Science - Tchr. Jerlyn"
    # "GMRC - Ustadha Saliha"
    # "PRE-CAL - TCHR. AHMAD"
    # "KomPan - Tchr. Thea"
    # "Biology 12 - Tchr. Rowena"
    # "GeneraL Physics 12"
    
    # Pattern: Subject - Teacher [extra]
    m = re.match(r'^(.*?)\s*[-–—]\s*(Tchr\.|Teacher|Tr\.|Ust\.|Ustdz\.|Ustadh|Ustadha|Alim|Sir)?\s*([A-Za-z\s\.\'\`]+?)(\s*\(.*?\))?$', s, flags=re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        teacher_raw = (m.group(2) or '') + ' ' + m.group(3).strip()
        teacher = normalize_teacher_name(teacher_raw)
        return subj, teacher
        
    return s, None

# Load current exam data
with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/exam_data.json') as f:
    current_exam_data = json.load(f)

print(f"Current exam sessions count: {len(current_exam_data)}")

