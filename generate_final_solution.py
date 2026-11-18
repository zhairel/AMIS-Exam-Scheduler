import json
import re

print("Starting full generation of official AMIS 2nd Term schedule...")

# 1. Load clean official 48 teachers and their 639 loads
with open('clean_official_44_teachers.json') as f:
    clean_teachers = json.load(f)

# 2. Load existing exams as templates
with open('exam_data_2nd_term.json') as f:
    existing_exams = json.load(f)

# Build a lookup of existing exams by ID
existing_by_id = {e['id']: e for e in existing_exams}

# Build section template lookup (to copy time_slot, room, etc.)
section_templates = {}
for e in existing_exams:
    sec = e.get('section_name')
    if sec and sec not in section_templates:
        section_templates[sec] = e

# Canonical section resolver
def resolve_section(load, dept):
    raw = load.strip()
    l_lower = raw.lower()
    
    clean_no_parens = re.sub(r'\(.*?\)', ' ', l_lower).strip()
    clean_no_subj_nums = re.sub(r'\b(physics|bio|circle time|aral reading|aral math|aral science)\s*[12]\b', ' ', clean_no_parens)
    is_f2f = 'f2f' in l_lower or 'face' in l_lower
    
    if is_f2f:
        if 'kinder 1' in l_lower or 'k1' in l_lower: return 'KINDER 1 CLASS SCHEDULE (F2F)'
        if 'kinder 2' in l_lower or 'k2' in l_lower: return 'KINDER 2 CLASS SCHEDULE (F2F)'
        if '7 & 8' in l_lower or '7 and 8' in l_lower:
            if 'girl' in l_lower: return 'GRADE 7 & 8 GIRLS (FACE TO FACE)'
            return 'GRADE 7 & 8 BOYS (FACE TO FACE)'
        if '9 & 10' in l_lower or '9 and 10' in l_lower:
            if 'girl' in l_lower: return 'GRADE 9 & 10 GIRLS (FACE TO FACE)'
            return 'GRADE 9 & 10 BOYS (FACE TO FACE)'
        
        m_g = re.search(r'\b(12|11|10|9|8|7|6|5|4|3|2|1)\b', clean_no_subj_nums)
        if m_g:
            g = m_g.group(1)
            if g == '12': return 'GRADE 12 - SUHAYB AR-RUMI'
            if g == '11': return 'GRADE 11 (FACE TO FACE)'
            if g in ['10', '9']:
                if 'girl' in l_lower: return 'GRADE 9 & 10 GIRLS (FACE TO FACE)'
                return 'GRADE 9 & 10 BOYS (FACE TO FACE)'
            if g in ['8', '7']:
                if 'girl' in l_lower: return 'GRADE 7 & 8 GIRLS (FACE TO FACE)'
                return 'GRADE 7 & 8 BOYS (FACE TO FACE)'
            if g == '6': return 'GRADE  6  FACE TO FACE'
            if g == '5': return 'GRADE 5 (FACE TO FACE)'
            if g == '4': return 'GRADE 4 (FACE TO FACE)'
            if g == '3': return 'GRADE 3 (FACE TO FACE)'
            if g == '2': return 'GRADE 2 (FACE TO FACE)'
            if g == '1': return 'GRADE 1 (FACE TO FACE)'
    
    if '12 (odl)' in l_lower or '12 odl' in l_lower or 'grade 12 odl' in l_lower: return 'GRADE 12 - ABU MUSA AL-ASHARI'
    if any(k in l_lower for k in ['aral science 3', 'aral math 3', 'aral reading 3', 'arabic 3 (new)']): return 'GRADE 3 (FACE TO FACE)'
    if 'homeroom guidance' in l_lower and 'norhaima' in l_lower: return 'GRADE 11 (FACE TO FACE)'
    if 'husain' in l_lower or 'husayn' in l_lower or 'advisory (tchr. wendy)' in l_lower or 'k1' in l_lower: return 'K1 - HUSAIN IBN ALI (2ND SHIFT)'
    if 'abu bakr' in l_lower: return 'Kinder 2 ABU BAKR AS-SIDEEQ (1ST SHIFT)'
    if 'khabbaab' in l_lower or 'khabaab' in l_lower: return 'Kinder 2 KHABAAB IBN ARAT (2ND SHIFT)'
    if 'uthman' in l_lower: return 'Kinder 2 UTHMAN IBN AFFAN (1ST SHIFT)'
    if "mas'ud" in l_lower and ('abdullah' in l_lower or 'k2' in l_lower or 'kinder' in l_lower): return "K2 - ABDULLAH IBN MAS'UD (2ND SHIFT)"
    if 'umar' in l_lower: return 'K2 - UMAR IBN AL-KHATTAB (2ND SHIFT)'
    if 'kinder 1' in l_lower: return 'KINDER 1 CLASS SCHEDULE (F2F)'
    if 'kinder 2' in l_lower or 'k2' in l_lower: return 'KINDER 2 CLASS SCHEDULE (F2F)'
    if 'suhayb ar-rumi' in l_lower or ('suhayb' in l_lower and any(x in l_lower for x in ['12', 'physics', 'cpar', 'ucsp', 'pfpl', 'pe 12', 'bio 2'])): return 'GRADE 12 - SUHAYB AR-RUMI'
    if 'abu musa' in l_lower: return 'GRADE 12 - ABU MUSA AL-ASHARI'
    if '11' in l_lower:
        if 'girl' in l_lower: return 'GRADE 11 (1ST SHIFT GIRLS)'
        if 'boy' in l_lower: return 'GRADE 11 (2ND SHIFT BOYS)'
        return 'GRADE 11 (FACE TO FACE)'
    if '7 & 8' in l_lower or '7 and 8' in l_lower:
        if 'girl' in l_lower: return 'GRADE 7 & 8 GIRLS (FACE TO FACE)'
        return 'GRADE 7 & 8 BOYS (FACE TO FACE)'
    if '9 & 10' in l_lower or '9 and 10' in l_lower:
        if 'girl' in l_lower: return 'GRADE 9 & 10 GIRLS (FACE TO FACE)'
        return 'GRADE 9 & 10 BOYS (FACE TO FACE)'
    if 'utbah' in l_lower: return 'GRADE 10 - UTBAH IBN GHAZWAN (1ST SHIFT) GIRLS'
    if 'abu ayyub' in l_lower or 'ayyub' in l_lower: return 'GRADE 10 - ABU AYYUB AL-ANSARI (2ND SHIFT) BOYS'
    if 'abu hurayrah' in l_lower or 'hurayrah' in l_lower: return 'GRADE 9 - ABU HURAYRAH (1ST SHIFT) GIRLS'
    if 'abu jandal' in l_lower or 'jandal' in l_lower: return 'GRADE 9 - ABU JANDAL IBN SUHAYL (2ND SHIFT) GIRLS'
    if 'abu dharr' in l_lower or 'dharr' in l_lower: return 'GRADE 9 - ABU DHARR AL GHIFARRI (2ND SHIFT) BOYS'
    if '9 (mix)' in l_lower or 'math 9 (mix)' in l_lower or 'tle 9 (mix)' in l_lower or 'shaf 9 (mix)' in l_lower: return 'GRADE 9 - ABU JANDAL IBN SUHAYL (2ND SHIFT) GIRLS'
    if "sa'ad" in l_lower and ('8' in l_lower or "mua'dh" in l_lower or "mu'adh" in l_lower or dept == 'High School Faculty'): return "GRADE 8 - SA'AD IBN MUA'DH (1ST SHIFT) - MIX"
    if "mu'adh" in l_lower or 'muadh' in l_lower: return "GRADE 8 - MU'ADH IBN JABAL (2ND SHIFT) - BOYS"
    if 'nuaym' in l_lower or "nu'aym" in l_lower: return "GRADE 8 - NUAYM IBN MAS'UD (2ND SHIFT) MIX"
    if 'abu sufyan' in l_lower or 'sufyan' in l_lower: return 'GRADE 7 - ABU SUFYAN IBN AL-HARITH (1ST SHIFT) BOYS'
    if 'usama' in l_lower: return 'GRADE 7 - USAMA IBN ZAYD (1ST SHIFT) GIRLS'
    if 'anas' in l_lower: return 'GRADE 7 - ANAS IBN MALIK (2ND SHIFT) - MIX'
    if 'abbas' in l_lower: return 'GRADE 6 - ABBAS IBN ABD AL-MUTTALIB (1ST SHIFT)'
    if 'abdullah' in l_lower and ('6' in l_lower or 'salaam' in l_lower): return 'GRADE 6 - ABDULLAH IBN SALAAM (1ST SHIFT)'
    if 'dihya' in l_lower: return 'GRADE 6 - DIHYA IBN KHALIFAH (2ND SHIFT) GIRLS'
    if 'khaleed' in l_lower: return 'GRADE 6 - KHALEED IBN WALEED (2ND SHIFT)'
    if 'hamza' in l_lower: return 'GRADE 5 - HAMZA IBN ABDUL (1ST SHIFT)'
    if 'muhammad' in l_lower: return 'GRADE 5 - MUHAMMAD IBN MASLAMAH (1ST SHIFT)'
    if 'ayyash' in l_lower: return "GRADE 5 - AYYASH IBN ABI RABI'AH(1ST SHIFT)"
    if 'al harith' in l_lower or 'harith' in l_lower: return 'GRADE 5 - AL HARITH BIN AWF (2ND SHIFT)'
    if "mus'ab" in l_lower or 'musab' in l_lower: return "GRADE 5 - MUS'AB IBN ABDUL MUTALIB (2ND SHIFT)"
    if "ja'far" in l_lower or 'jafar' in l_lower: return "GRADE 5 - JA'FAR IBN ABI TALIB (2ND SHIFT) - MIX"
    if 'abdur rahman' in l_lower or 'awf' in l_lower: return 'GRADE 4 - ABDUR RAHMAN IBN AWF (1ST SHIFT)'
    if 'hakim' in l_lower: return 'GRADE 4 - HAKIM IBN HAZM(1ST SHIFT)'
    if 'usayd' in l_lower: return 'GRADE 4 - USAYD IBN HUDHAYR (1ST SHIFT) - MIX'
    if 'ikrimah' in l_lower: return 'GRADE 4 - IKRIMAH IBN ABI JAHL (2ND SHIFT)'
    if 'az zubair' in l_lower or 'zubair' in l_lower: return 'GRADE 4 - AZ ZUBAIR IBN AL AWWAAM (2ND SHIFT)'
    if 'hassan' in l_lower: return 'GRADE 4 -HASSAN IBN THABIT (2ND SHIFT) - MIX'
    if 'habib' in l_lower: return 'Grade 3 - HABIB IBN ZAYD AL-ANSARI (1ST SHIFT) - GIRLS'
    if 'ammar' in l_lower: return 'GRADE 3 -AMMAR IBN YASIR (1ST SHIFT) - BOYS'
    if 'salman' in l_lower: return 'GRADE 3 - SALMAN AL FARSI (1ST SHIFT) MIX'
    if "as'ad" in l_lower or 'asad' in l_lower: return "GRADE 3 - AS'AD IBN ZURARAH (2ND SHIFT) MIX"
    if 'zayd' in l_lower: return 'GRADE 3 - ZAYD IBN HARITHA (2ND SHIFT) - GIRLS'
    if 'thabit' in l_lower: return 'GRADE 3 - THABIT IBN QAYS (2ND SHIFT) - BOYS'
    if 'talha' in l_lower: return 'GRADE 2 - TALHA IBN UBAYDULLAH (1ST SHIFT)'
    if 'amr' in l_lower: return 'GRADE 2 - AMR IBN AL-JAMUH (1ST SHIFT)'
    if 'saeed' in l_lower: return 'GRADE 2 - SAEED IBN ZAYD (2ND SHIFT)'
    if 'aasim' in l_lower: return 'GRADE 2 - AASIM IBN THABIT (2ND SHIFT)'
    if 'hudhayfah' in l_lower: return 'GRADE 1 - HUDHAYFAH IBN AL-YAM (1ST SHIFT)'
    if 'ali' in l_lower and '1' in l_lower: return 'GRADE 1 - ALI IBN ABI TALIB(1ST SHIFT)'
    if "sa'ad" in l_lower and '1' in l_lower: return "GRADE 1 - SA'AD IBN ABI WAQQAAS (2ND SHIFT)"
    if 'suhayb' in l_lower and '1' in l_lower: return 'GRADE 1 - SUHAYB AR-RUMI (2ND SHIFT)'
    return 'GRADE 1 (FACE TO FACE)'

def extract_subject(load):
    parts = re.split(r'\s*[–-]\s*', load.strip(), maxsplit=1)
    fl = re.sub(r'\(.*?\)', '', parts[0]).strip().lower()
    if 'circle time 1' in fl: return 'Circle Time 1'
    if 'circle time 2' in fl: return 'Circle Time 2'
    if 'circle time' in fl: return 'Circle Time 1'
    if 'meeting time' in fl: return 'Meeting Time'
    if 'wrap' in fl: return 'Wrap-Up Time'
    if 'homeroom guidance' in fl: return 'Homeroom Guidance'
    if 'reading & literacy' in fl or 'reading and literacy' in fl: return 'Reading & Literacy'
    if 'aral reading' in fl: return 'Aral Reading'
    if 'aral math' in fl: return 'Aral Math'
    if 'aral science' in fl: return 'Aral Science'
    if 'aral program' in fl: return 'ARAL Program'
    if 'araling panlipunan' in fl: return 'Araling Panlipunan'
    if 'social science' in fl: return 'Social Science'
    if 'general physics' in fl: return 'General Physics 2'
    if 'gen bio 2' in fl or 'general biology 2' in fl: return 'Gen Bio 2'
    if 'general science' in fl: return 'General Science 11'
    if 'general math' in fl: return 'General Math 11'
    if 'values education' in fl: return 'Values Education'
    if 'esp' in fl: return 'ESP'
    if 'pananaliksik' in fl or 'pskp' in fl: return 'PSKP 11'
    if 'pfpl' in fl: return 'PFPL 12'
    if 'ucsp' in fl: return 'UCSP 12'
    if 'cpar' in fl: return 'CPAR 12'
    if 'ec 11' in fl or 'effective communication' in fl: return 'Effective Communication 11'
    if 'lcs 11' in fl or 'literature' in fl: return '21st Century Literature 11'
    if 'pe 12' in fl: return 'PE 12'
    if 'makabansa' in fl: return 'Makabansa'
    if 'language' in fl: return 'Language'
    if 'gmrc' in fl: return 'GMRC'
    if 'math' in fl: return 'Math'
    if 'science' in fl: return 'Science'
    if 'filipino' in fl: return 'Filipino'
    if 'english' in fl: return 'English'
    if 'mapeh' in fl: return 'MAPEH'
    if 'tle' in fl: return 'TLE'
    if 'arabic' in fl: return 'Arabic'
    if "qur'an" in fl or 'quran' in fl: return "Qur'an"
    if 'hadith' in fl: return 'Hadith'
    if 'shaf' in fl: return 'SHAF'
    if 'isal' in fl: return 'ISAL'
    return parts[0].strip()

def norm_sub(sub):
    if not sub: return ''
    s = sub.lower().strip()
    if 'panlipunan' in s or s == 'ap' or 'social science' in s or 'social studies' in s or 'kasaysayan' in s: return 'ap'
    if 'makabansa' in s: return 'makabansa'
    if 'aral math' in s: return 'aral_math'
    if 'aral reading' in s: return 'aral_reading'
    if 'aral science' in s: return 'aral_science'
    if 'aral program' in s or s == 'aral': return 'aral'
    if 'reading & literacy' in s or 'reading and literacy' in s or 'r & l' in s: return 'english'
    if 'english' in s: return 'english'
    if 'math' in s or 'gen math' in s: return 'math'
    if 'physics' in s: return 'physics'
    if 'bio' in s: return 'biology'
    if 'science' in s: return 'science'
    if 'filipino' in s or 'pagsulat' in s or 'pfpl' in s: return 'filipino'
    if 'pananaliksik' in s or 'pskp' in s: return 'pskp'
    if 'effective communication' in s or 'ec' in s or 'komunikasyon' in s: return 'ec'
    if 'cpar' in s: return 'cpar'
    if 'ucsp' in s: return 'ucsp'
    if 'lcs' in s or 'literature' in s: return 'lcs'
    if 'mapeh' in s or 'pe' in s or 'physical education' in s: return 'mapeh'
    if 'tle' in s or 'tvl' in s or 'entrepreneurship' in s: return 'tle'
    if 'gmrc' in s or 'values' in s or 'esp' in s: return 'gmrc'
    if 'arabic' in s: return 'arabic'
    if 'qur' in s: return 'quran'
    if 'hadith' in s: return 'hadith'
    if any(x in s for x in ['shaf', 'seerah', 'sirah', 'aqeedah', 'fiqh', 'tawheed']): return 'shaf'
    if 'circle time' in s or 'ct' in s: return 'circle_time'
    if 'meeting time' in s: return 'circle_time'
    if 'wrap' in s: return 'circle_time'
    if 'language' in s: return 'language'
    return s

def extract_grade_level(sec):
    s = sec.lower()
    if 'kinder 1' in s or 'k1' in s: return 'Kinder 1'
    if 'kinder 2' in s or 'k2' in s: return 'Kinder 2'
    if '12' in s: return 'Grade 12'
    if '11' in s: return 'Grade 11'
    if '10' in s: return 'Grade 10'
    if '9' in s: return 'Grade 9'
    if '8' in s: return 'Grade 8'
    if '7' in s: return 'Grade 7'
    if '6' in s: return 'Grade 6'
    if '5' in s: return 'Grade 5'
    if '4' in s: return 'Grade 4'
    if '3' in s: return 'Grade 3'
    if '2' in s: return 'Grade 2'
    if '1' in s: return 'Grade 1'
    return 'Elementary'

# Load existing roster map
with open('exam-schedule-2nd-term.html') as f:
    lines = f.readlines()
start, end = None, None
for i, l in enumerate(lines):
    if 'const FACULTY_ROSTER_DATA =' in l: start = i
    if start is not None and i > start and l.strip().startswith('];'): end = i; break
roster_text = ''.join(lines[start:end+1]).split('=', 1)[1].strip().rstrip(';')
old_roster = json.loads(roster_text)
roster_map = {t['name'].lower(): t['id'] for t in old_roster}

# Manual known reassignments to pre-claim
MANUAL_REASSIGNMENTS = {
    'exam_462': {'teacher_id': 'tchr_angeleni', 'teacher': 'Teacher Angeleni', 'subject': 'MAPEH'},
    'exam_460': {'teacher_id': 'tchr_aniah', 'teacher': 'Teacher Aniah', 'subject': 'General Physics 2'},
    'exam_221': {'teacher_id': 'tchr_aniah', 'teacher': 'Teacher Aniah', 'subject': 'General Physics 2'},
    'exam_18':  {'teacher_id': 'tchr_mohaymen', 'teacher': 'Sir Mohaymen', 'subject': 'TLE'},
    'exam_159': {'teacher_id': 'tchr_ethel', 'teacher': 'Teacher Ethel', 'subject': 'UCSP 12'},
    'exam_347': {'teacher_id': 'tchr_ethel', 'teacher': 'Teacher Ethel', 'subject': 'UCSP 12'},
    'exam_295': {'teacher_id': 'tchr_ethel', 'teacher': 'Teacher Ethel', 'subject': 'CPAR 12'},
    'exam_372': {'teacher_id': 'tchr_ethel', 'teacher': 'Teacher Ethel', 'subject': 'CPAR 12'},
    'exam_148': {'teacher_id': 'tchr_nof', 'teacher': 'Teacher Nof', 'subject': 'PFPL 12'},
    'exam_480': {'teacher_id': 'tchr_nof', 'teacher': 'Teacher Nof', 'subject': 'PFPL 12'},
    'exam_14':  {'teacher_id': 'tchr_radzmia', 'teacher': 'Teacher Radzmia', 'subject': 'Gen Bio 2'},
    'exam_201': {'teacher_id': 'tchr_radzmia', 'teacher': 'Teacher Radzmia', 'subject': 'Gen Bio 2'},
}

ARVIN_MATH_EXAMS = [
    ('exam_319', 'GRADE 4 (FACE TO FACE)'),
    ('exam_229', 'GRADE 4 - USAYD IBN HUDHAYR (1ST SHIFT) - MIX'),
    ('exam_351', 'GRADE 4 - ABDUR RAHMAN IBN AWF (1ST SHIFT)'),
    ('exam_505', 'GRADE 4 - HAKIM IBN HAZM(1ST SHIFT)'),
    ('exam_435', 'GRADE 4 - IKRIMAH IBN ABI JAHL (2ND SHIFT)'),
    ('exam_379', 'GRADE 4 - AZ ZUBAIR IBN AL AWWAAM (2ND SHIFT)'),
    ('exam_135', 'GRADE 4 -HASSAN IBN THABIT (2ND SHIFT) - MIX'),
    ('exam_174', 'GRADE 5 (FACE TO FACE)'),
    ('exam_90',  'GRADE 5 - HAMZA IBN ABDUL (1ST SHIFT)'),
    ('exam_356', 'GRADE 5 - MUHAMMAD IBN MASLAMAH (1ST SHIFT)'),
    ('exam_61',  "GRADE 5 - AYYASH IBN ABI RABI'AH(1ST SHIFT)"),
    ('exam_194', 'GRADE 5 - AL HARITH BIN AWF (2ND SHIFT)'),
    ('exam_284', "GRADE 5 - MUS'AB IBN ABDUL MUTALIB (2ND SHIFT)"),
    ('exam_415', "GRADE 5 - JA'FAR IBN ABI TALIB (2ND SHIFT) - MIX"),
    ('exam_568', 'GRADE 6 - KHALEED IBN WALEED (2ND SHIFT)'),
    ('exam_95',  'GRADE 6 - DIHYA IBN KHALIFAH (2ND SHIFT) GIRLS'),
    ('exam_157', 'GRADE  6  FACE TO FACE'),
]

for eid, sec in ARVIN_MATH_EXAMS:
    MANUAL_REASSIGNMENTS[eid] = {
        'teacher_id': 'tchr_arvin',
        'teacher': 'Teacher Arvin',
        'subject': 'Math',
        'section_name': sec
    }

for e in existing_exams:
    eid = e.get('id')
    if eid in MANUAL_REASSIGNMENTS:
        for k, v in MANUAL_REASSIGNMENTS[eid].items():
            e[k] = v

# Track claimed existing exams
claimed_existing_ids = set()

# Process each teacher and build final exam list & final roster
final_exam_records = []
final_roster_data = []

exam_counter = 1

for teacher_info in clean_teachers:
    tname = teacher_info['name']
    tid = roster_map[tname.lower()]
    dept = teacher_info['department']
    loads = teacher_info['loads']
    
    teacher_assignments = []
    
    for load in loads:
        canon_sec = resolve_section(load, dept)
        subj = extract_subject(load)
        n_sub = norm_sub(load)
        is_f2f = 'f2f' in canon_sec.lower() or 'face' in canon_sec.lower() or 'f2f' in load.lower()
        shift = 'F2F' if is_f2f else 'ODL'
        
        # Add to roster assignments
        teacher_assignments.append({
            'subject': subj,
            'section': canon_sec,
            'shift': shift,
            'raw': load
        })
        
        # Match with existing exam
        matched_e = None
        # Priority 1: Exam already under this teacher
        for e in existing_exams:
            if e['id'] in claimed_existing_ids: continue
            if (e.get('teacher_id') or e.get('subject_teacher_id')) == tid:
                if norm_sub(e.get('subject', '')) == n_sub and e.get('section_name') == canon_sec:
                    matched_e = e
                    break
        # Priority 2: Exam under another teacher (or inactive)
        if not matched_e:
            for e in existing_exams:
                if e['id'] in claimed_existing_ids: continue
                if norm_sub(e.get('subject', '')) == n_sub and e.get('section_name') == canon_sec:
                    matched_e = e
                    break
        
        if matched_e:
            claimed_existing_ids.add(matched_e['id'])
            # Clone and ensure correct teacher metadata
            e_rec = dict(matched_e)
            e_rec['id'] = f"exam_{exam_counter}"
            e_rec['subject'] = subj
            e_rec['section'] = canon_sec
            e_rec['section_name'] = canon_sec
            e_rec['teacher'] = tname
            e_rec['teacher_id'] = tid
            e_rec['subject_teacher'] = tname
            e_rec['subject_teacher_id'] = tid
            e_rec['active_subject_teacher'] = tname
            e_rec['active_subject_teacher_id'] = tid
            e_rec['proctor'] = tname
            e_rec['proctor_id'] = tid
            e_rec['shift'] = shift
            e_rec['modality'] = shift
            e_rec['grade'] = extract_grade_level(canon_sec)
            e_rec['grade_level'] = extract_grade_level(canon_sec)
            final_exam_records.append(e_rec)
        else:
            # Create new exam record using section template
            template = section_templates.get(canon_sec)
            if template:
                e_rec = dict(template)
            else:
                e_rec = dict(existing_exams[0])
                e_rec['day_number'] = 1
                e_rec['date'] = "Tuesday, December 1, 2026"
                e_rec['short_date'] = "Dec 1"
                e_rec['day_name'] = "Tuesday"
                e_rec['time_slot'] = "08:00 AM – 09:00 AM"
                e_rec['time'] = "08:00 AM – 09:00 AM"
                e_rec['duration_minutes'] = 60
                e_rec['start_m'] = 480
                e_rec['end_m'] = 540
            
            e_rec['id'] = f"exam_{exam_counter}"
            e_rec['subject'] = subj
            e_rec['subject_id'] = f"subj_{subj.lower().replace(' ', '_').replace('&', 'and')}"
            e_rec['section'] = canon_sec
            e_rec['section_name'] = canon_sec
            e_rec['section_id'] = f"sec_{canon_sec.lower().replace(' ', '_').replace('&', 'and')}"
            e_rec['teacher'] = tname
            e_rec['teacher_id'] = tid
            e_rec['subject_teacher'] = tname
            e_rec['subject_teacher_id'] = tid
            e_rec['active_subject_teacher'] = tname
            e_rec['active_subject_teacher_id'] = tid
            e_rec['proctor'] = tname
            e_rec['proctor_id'] = tid
            e_rec['shift'] = shift
            e_rec['modality'] = shift
            e_rec['grade'] = extract_grade_level(canon_sec)
            e_rec['grade_level'] = extract_grade_level(canon_sec)
            e_rec['teacher_status'] = 'VERIFIED'
            e_rec['subject_teacher_active'] = True
            e_rec['replacement_teacher_required'] = False
            e_rec['subject_teacher_status'] = 'ACTIVE_VERIFIED'
            e_rec['proctor_status'] = 'ACTIVE_ASSIGNED'
            e_rec['proctor_assignment_source'] = 'SUBJECT_TEACHER'
            e_rec['proctor_conflict_status'] = 'CLEAR'
            e_rec['proctor_pool'] = 'SUBJECT_TEACHER'
            
            final_exam_records.append(e_rec)
        
        exam_counter += 1

    final_roster_data.append({
        'id': tid,
        'name': tname,
        'department': dept,
        'assignments': teacher_assignments
    })

print(f"Total final exam records: {len(final_exam_records)}")
print(f"Total teachers in final roster: {len(final_roster_data)}")
total_loads = sum(len(t['assignments']) for t in final_roster_data)
print(f"Total assignments in final roster: {total_loads}")

# Save JSON and JS files
with open('exam_data_2nd_term.json', 'w') as f:
    json.dump(final_exam_records, f, indent=2)
print("Saved exam_data_2nd_term.json")

with open('exam_data_2nd_term.js', 'w') as f:
    f.write('const ALL_EXAM_RECORDS = ')
    json.dump(final_exam_records, f, indent=2)
    f.write(';\n\nwindow.AMIS_EXAM_DATA = ALL_EXAM_RECORDS;\n')
print("Saved exam_data_2nd_term.js")

# Now update FACULTY_ROSTER_DATA in exam-schedule-2nd-term.html
with open('exam-schedule-2nd-term.html') as f:
    html_content = f.read()

# Replace FACULTY_ROSTER_DATA block
roster_json_str = json.dumps(final_roster_data, indent=2)
new_roster_decl = f"const FACULTY_ROSTER_DATA = {roster_json_str};"

pattern = r'const FACULTY_ROSTER_DATA = \[.*?\];'
html_content = re.sub(pattern, lambda m: new_roster_decl, html_content, flags=re.DOTALL)

with open('exam-schedule-2nd-term.html', 'w') as f:
    f.write(html_content)
print("Updated exam-schedule-2nd-term.html with new FACULTY_ROSTER_DATA!")

