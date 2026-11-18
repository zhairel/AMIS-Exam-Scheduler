import re
import openpyxl

wb_new = openpyxl.load_workbook('/home/tatsuya/.gemini/antigravity/brain/306f0037-2aea-46d3-9052-c9a48dba1afc/.user_uploaded/media_1794891181069_65ca2fb8.xlsx', data_only=True)
wb_old = openpyxl.load_workbook('/home/tatsuya/.gemini/antigravity/brain/306f0037-2aea-46d3-9052-c9a48dba1afc/.user_uploaded/media_1794794150498_8d58cafa.xlsx', data_only=True)

# Standard section display names
SECTIONS = {
    'habib': 'Habib',
    'ammar': 'Ammar',
    'salman': 'Salman',
    "as'ad": "As'ad",
    'asad': "As'ad",
    'zayd': 'Zayd',
    'thabit': 'Thabit',
    'hakim': 'Hakim',
    'abdur rahman': 'Abdur Rahman',
    'abdurrahman': 'Abdur Rahman',
    'abdur-rahman': 'Abdur Rahman',
    'abas': 'Abbas',
    'abbas': 'Abbas',
    'abdullah': 'Abdullah',
    'ikrimah': 'Ikrimah',
    'hassan': 'Hassan',
    'hasan': 'Hassan',
    'az zubair': 'Az Zubair',
    'azzubair': 'Az Zubair',
    'az-zubair': 'Az Zubair',
    'dihya': 'Dihya',
    'khaleed': 'Khaleed',
    'khalid': 'Khaleed',
    'hamza': 'Hamza',
    'muhammad': 'Muhammad',
    "mus'ab": "Mus'ab",
    'musab': "Mus'ab",
    'al harith': 'Al Harith',
    'al-harith': 'Al Harith',
    'alharith': 'Al Harith',
    'al- harith': 'Al Harith',
    'ayyash': 'Ayyash',
    'ayash': 'Ayyash',
    'ayyas': 'Ayyash',
    'suhayb': 'Suhayb',
    'ali': 'Ali',
    'hudhayfah': 'Hudhayfah',
    "sa'ad": "Sa'ad",
    'saad': "Sa'ad",
    'talha': 'Talha',
    'amr': 'Amr',
    'saeed': 'Saeed',
    'aasim': 'Aasim',
    'asim': 'Aasim',
    'k2 khabbaab': 'K2 Khabbaab',
    'k2 khabbab': 'K2 Khabbaab',
    'k2-khabbab': 'K2 Khabbaab',
    'khabbaab': 'K2 Khabbaab',
    'khabbab': 'K2 Khabbaab',
    'usayd': 'Usayd',
    "ja'far": "Ja'far",
    'jafar': "Ja'far",
    'k1 husain': 'K1 Husayn Ibn Ali',
    'k1 - husain': 'K1 Husayn Ibn Ali',
    'husain': 'K1 Husayn Ibn Ali',
    'husayn': 'K1 Husayn Ibn Ali',
    'abu bakr': 'K2 Abu Bakr',
    'k2 abu bakr': 'K2 Abu Bakr',
    'k2 abu bakar': 'K2 Abu Bakr',
    'abu bkr': 'K2 Abu Bakr',
    'k2 abu bkr': 'K2 Abu Bakr',
    'k2 umar': 'K2 Umar',
    'umar': 'K2 Umar',
    'k2 abdullah': "K2 Abdullah Ibn Mas'ud",
    "k2 abdullah ibn mas'ud": "K2 Abdullah Ibn Mas'ud",
    "abdullah ibn mas'ud": "K2 Abdullah Ibn Mas'ud",
    'uthman ibn affan': 'K2 Uthman Ibn Affan',
    'k2 uthman ibn affan': 'K2 Uthman Ibn Affan',
    'k2 uthman': 'K2 Uthman Ibn Affan',
    'uthman': 'K2 Uthman Ibn Affan',
    'abu sufyan': 'Abu Sufyan',
    'usama': 'Usama',
    'anas': 'Anas',
    'nuaym': 'Nuaym',
    "mu'adh": "Mu'adh",
    'muadh': "Mu'adh",
    'utbah': 'Utbah',
    'abu ayyub': 'Abu Ayyub',
    'abu hurayrah': 'Abu Hurayrah',
    'abu dharr': 'Abu Dharr',
    'abu jandal': 'Abu Jandal',
    'abu musa': 'Abu Musa',
    'suhayb ar-rumi': 'Suhayb Ar-Rumi'
}

subj_map = {
    'filipino': 'Filipino', 'fil': 'Filipino',
    'math': 'Math',
    'science': 'Science', 'sci': 'Science',
    'english': 'English', 'eng': 'English',
    'ap': 'Araling Panlipunan',
    'tle': 'TLE',
    'mapeh': 'MAPEH',
    'gmrc': 'GMRC',
    'arabic': 'Arabic',
    "qur'an": "Qur'an", 'quran': "Qur'an",
    'shaf': 'SHAF',
    'soc.sci': 'Social Science', 'soc. sci': 'Social Science', 'soc sci': 'Social Science',
    'esp': 'Values Education (ESP)', 'val. ed': 'Values Education', 'val ed': 'Values Education',
    'pskp': 'PSKP', 'lcs': 'LCS', 'ec': 'Effective Communication',
    'cpar': 'CPAR', 'ucsp': 'UCSP', 'pfpl': 'PFPL',
    'gen math': 'General Mathematics', 'gen science': 'General Science',
    'gen bio 2': 'General Biology 2', 'gen bio': 'General Biology',
    'physics 2': 'Physics 2', 'physics': 'Physics',
    'pe 12': 'PE 12', 'pe': 'PE',
    'hadith': 'Hadith'
}

def normalize_item(val, teacher_name=""):
    s = str(val or '').strip()
    s = re.sub(r'^\d+\.\s*', '', s)
    # Only separate subject glued to digit, do NOT separate F2F or K1/K2
    s = re.sub(r'\b(english|filipino|fil|math|science|sci|ap|tle|mapeh|gmrc|arabic|qur\'?an|shaf|esp)(\d+)\b', r'\1 \2', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+', ' ', s)
    low = s.lower()
    
    # Ignore non-teaching / headers / times
    if low in ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']:
        return None
    if low in ['time', 'minutes', 'clock out']:
        return None
    if any(ign in low for ign in [
        'general assembly', 'assembly', 'recess', 'lunch and salah',
        'salah & departure', 'salah and departure', 'departure',
        'homeroom guidance (adviser)', 'advisory', 'homeroom g4 f2f',
        'homeroom guidance', 'homeroom - g6 f2f', 'homeroom/hr'
    ]):
        return None
    if low in ['homeroom', 'lunch', 'salah', 'recess', 'f', '']:
        return None

    # Circle Time
    if 'circle time 1 - k1' in low or 'circle time 1 - kinder 1' in low:
        return 'Circle Time 1 – Kinder 1'
    if 'circle time 2 - k1' in low or 'circle time 2 - kinder 1' in low:
        return 'Circle Time 2 – Kinder 1'
    if 'circle time 1 - tchr. wendy' in low:
        return 'Circle Time 1 – Advisory (Tchr. Wendy)'
    if 'ct 2 - tchr. wendy' in low:
        return 'Circle Time 2 – Advisory (Tchr. Wendy)'
    if 'circle time 1 - k2 (f2f)' in low:
        if 'assist' in low:
            return 'Circle Time 1 – K2 (F2F) [Assistant]'
        return 'Circle Time 1 – K2 (F2F)'
    if 'circle time 2 - k2 (f2f)' in low:
        if 'assist' in low:
            return 'Circle Time 2 – K2 (F2F) [Assistant]'
        return 'Circle Time 2 – K2 (F2F)'
    if 'meeting time - k2 (f2f)' in low:
        return 'Meeting Time – K2 (F2F)'
    if 'wrap-up time - k2 (f2f)' in low:
        return 'Wrap-Up Time – K2 (F2F)'
    if 'isal - k2 (f2f)' in low:
        return 'ISAL – K2 (F2F) [Assistant]'
    if 'circle time 1 - k2 abu bakr' in low or 'circle time 1 - abu bakr' in low or 'ct 1 - k2 abu bakr' in low:
        return 'Circle Time 1 – K2 Abu Bakr'
    if 'ct 2 - k2 abu bak' in low or 'circle time 2 - k2 abu bak' in low or 'ct 2 - abu bak' in low:
        return 'Circle Time 2 – K2 Abu Bakr'
    if 'ct 1 - k2 umar' in low or 'circle time 1 - k2 umar' in low or 'ct 1- k2 umar' in low:
        return 'Circle Time 1 – K2 Umar'
    if 'ct 2 - k2 umar' in low or 'circle time 2 - k2 umar' in low or 'ct 2- k2 umar' in low:
        return 'Circle Time 2 – K2 Umar'
    if 'circle time 2 - k2 uthman ibn affan' in low or 'ct 2 - uthman ibn affan' in low:
        return 'Circle Time 2 – K2 Uthman Ibn Affan'
    if "ct 1 abdullah ibn mas'ud" in low:
        return "Circle Time 1 – K2 Abdullah Ibn Mas'ud"
    if "ct 2 abdullah ibn mas'ud" in low:
        return "Circle Time 2 – K2 Abdullah Ibn Mas'ud"
    if 'circle 1 - khabbaab' in low or 'circle 1 - khabbab' in low:
        return 'Circle Time 1 – Khabbaab'
    if 'circle 2 - khabbaab' in low or 'circle 2 - khabbab' in low:
        return 'Circle Time 2 – Khabbaab'
    if low in ['ct 1', 'ct 1 (f2f)', 'ct 1 ( f2f )']:
        return 'Circle Time 1 (F2F)'
    if low in ['ct 2', 'ct 2 (f2f)', 'ct 2 ( f2f )']:
        return 'Circle Time 2 (F2F)'
        
    # Reading & Literacy
    if 'reading and literacy 1' in low and 'f2f' in low:
        return 'Reading & Literacy 1 (F2F)'
    if 'reading and literacy 1' in low and ('ali' not in low and 'hudhayfah' not in low):
        return 'Reading & Literacy 1 (F2F)'
    if 'r & l - g1 ali' in low or 'reading and literacy 1 ali' in low:
        return 'Reading & Literacy 1 – Ali'
    if 'r & l - g1 hudhayfah' in low or 'reading and literacy 1 hudhayfah' in low:
        return 'Reading & Literacy 1 – Hudhayfah'
    if 'r & l - g1 saad' in low or "r & l - g1 sa'ad" in low:
        return "Reading & Literacy 1 – Sa'ad"
    if 'r & l - g1 suhayb' in low:
        return 'Reading & Literacy 1 – Suhayb'
    if 'aral reading 1' in low and 'f2f' in low:
        return 'Aral Reading 1 (F2F)'
    if 'aral reading 1' in low and ('ali' not in low and 'hudhayfah' not in low):
        return 'Aral Reading 1 (F2F)'
    if 'aral reading - g1 ali' in low:
        return 'Aral Reading 1 – Ali'
    if 'aral reading - g1 hudhayfah' in low:
        return 'Aral Reading 1 – Hudhayfah'
    if "aral reading - g1 sa'ad" in low or 'aral reading - g1 saad' in low:
        return "Aral Reading 1 – Sa'ad"
    if 'aral reading - g1 suhayb' in low:
        return 'Aral Reading 1 – Suhayb'
    if 'aral reading 2 talha' in low:
        return 'Aral Reading 2 – Talha'
    if 'aral reading 2 amr' in low:
        return 'Aral Reading 2 – Amr'
    if 'aral reading 2 aasim' in low or 'aral reading 2 asim' in low:
        return 'Aral Reading 2 – Aasim'
    if 'aral reading 2 saeed' in low:
        return 'Aral Reading 2 – Saeed'
    if 'aral reading 2' in low and ('f2f' in low or 'ftf' in low):
        return 'Aral Reading 2 (F2F)'
    if 'aral reading 3' in low:
        return 'Aral Reading 3'
    if 'aral reading 4' in low and ('f2f' in low or 'ftf' in low):
        return 'Aral Reading 4 (F2F)'

    # Aral Math & Science
    if '7/8 boys - aral math' in low:
        return 'Aral Math – Grades 7 & 8 (Boys)'
    if '7/8 girls - aral math' in low:
        return 'Aral Math – Grades 7 & 8 (Girls)'
    if '9/10 boys - aral math' in low:
        return 'Aral Math – Grades 9 & 10 (Boys)'
    if '9/10 girls - aral math' in low:
        return 'Aral Math – Grades 9 & 10 (Girls)'
    if 'aral math g1 f2f' in low or 'aral math 1 f2f' in low:
        return 'Aral Math 1 (F2F)'
    if 'aral math g2 f2f' in low or 'aral math 2 f2f' in low:
        return 'Aral Math 2 (F2F)'
    if 'aral math 3' in low:
        return 'Aral Math 3'
    if 'aral science 3' in low:
        return 'Aral Science 3'
    if 'aral program 4' in low and ('f2f' in low or 'ftf' in low):
        return 'Aral Program 4 (F2F)'
    if 'aral program 5' in low and ('f2f' in low or 'ftf' in low):
        return 'Aral Program 5 (F2F)'
    if 'aral program 6' in low and ('f2f' in low or 'ftf' in low):
        return 'Aral Program 6 (F2F)'
    if low in ['aral 6', 'aral program 6']:
        return 'Aral Program 6 (F2F)'
    if "aral - g1 sa'ad" in low or 'aral - g1 saad' in low:
        return "Aral Program 1 – Sa'ad"
    if 'aral - g1 suhayb' in low:
        return 'Aral Program 1 – Suhayb'

    # Language
    if 'language - 1 f2f' in low or 'language 1 f2f' in low:
        return 'Language 1 (F2F)'
    if 'language 1 ali' in low:
        return 'Language 1 – Ali'
    if 'language 1 hudhayfah' in low:
        return 'Language 1 – Hudhayfah'
    if "language 1 sa'ad" in low or 'language 1 saad' in low:
        return "Language 1 – Sa'ad"
    if 'language 1 suhayb' in low:
        return 'Language 1 – Suhayb'

    # Makabansa
    if 'makabansa 3 (f2f)' in low or 'makabansa 3 f2f' in low or low == 'makabansa 3':
        return 'Makabansa 3 (F2F)'
    if 'makabansa 1 f2f' in low:
        return 'Makabansa 1 (F2F)'
    if 'makabansa 1 ali' in low:
        return 'Makabansa 1 – Ali'
    if 'makabansa 1 hudhayfah' in low:
        return 'Makabansa 1 – Hudhayfah'
    if 'makabansa 1 suhayb' in low:
        return 'Makabansa 1 – Suhayb'
    if "makabansa 1 sa'ad" in low or 'makabansa 1 saad' in low:
        return "Makabansa 1 – Sa'ad"
    if 'makabansa 2 f2f' in low:
        return 'Makabansa 2 (F2F)'
    if 'makabansa 2 amr' in low:
        return 'Makabansa 2 – Amr'
    if 'makabansa 2 saeed' in low:
        return 'Makabansa 2 – Saeed'
    if 'makabansa 2 aasim' in low or 'makabansa 2 asim' in low:
        return 'Makabansa 2 – Aasim'
    if 'makabansa - 2 talha' in low or 'makabansa 2 talha' in low or 'makabansa-2talha' in low:
        return 'Makabansa 2 – Talha'
    if 'makabansa 3 habib' in low:
        return 'Makabansa 3 – Habib'
    if 'makabansa 3 ammar' in low:
        return 'Makabansa 3 – Ammar'
    if 'makabansa 3 thabit' in low:
        return 'Makabansa 3 – Thabit'
    if 'makabansa 3 zayd' in low:
        return 'Makabansa 3 – Zayd'
    if "makabansa 3 - as'ad" in low or 'makabansa 3 asad' in low:
        return "Makabansa 3 – As'ad"
    if 'makabansa 3 - salman' in low or 'makabansa 3 salman' in low:
        return 'Makabansa 3 – Salman'

    # Homeroom Guidance
    if 'hg 1 f2f' in low:
        return 'Homeroom Guidance 1 (F2F)'
    if 'hg - 7&8 boys' in low or 'hg 7&8 boys' in low or 'hg 7 & 8 boys' in low:
        return 'Homeroom Guidance – Grades 7 & 8 (Boys)'
    if 'hg - 7&8 girls' in low or 'hg 7&8 girls' in low or 'hg 7 & 8 girls' in low:
        return 'Homeroom Guidance – Grades 7 & 8 (Girls)'
    if 'hg - 9&10 boys' in low or 'hg 9&10 boys' in low or 'hg 9 & 10 boys' in low:
        return 'Homeroom Guidance – Grades 9 & 10 (Boys)'
    if 'hg - tchr. norhaima' in low or 'hg - tchr norhaima' in low:
        return 'Homeroom Guidance – Grade 9 Advisory'

    # SHS specific
    if 'gen math' in low:
        if '2nd shift' in low:
            return 'General Mathematics 11 (ODL 2nd Shift)'
        elif 'odl' in low or '1st shift' in low:
            return 'General Mathematics 11 (ODL 1st Shift)'
        return 'General Mathematics 11 (F2F)'
    if 'gen science' in low or 'gen sci' in low:
        if 'odl' in low:
            return 'General Science 11 (ODL)'
        return 'General Science 11 (F2F)'
    if 'gen bio 2' in low or 'gen bio' in low:
        if 'g11/g12 f2f' in low or 'f2f' in low:
            return 'General Biology 2 – Grades 11 & 12 (F2F)'
        if '2nd shift' in low:
            return 'General Biology 2 – Grade 11 (2nd Shift ODL)'
        if '1st shift' in low:
            return 'General Biology 2 – Grade 11 (1st Shift ODL)'
        if '12 odl' in low or 'odl' in low:
            return 'General Biology 2 – Grade 12 (ODL)'
        return 'General Biology 2 (SHS)'
    if 'pskp 11' in low or 'pskp' in low:
        if 'odl' in low:
            return 'PSKP 11 (ODL)'
        return 'PSKP 11 (F2F)'
    if 'lcs 11' in low or 'lcs' in low:
        if '2nd shift' in low:
            return 'LCS 11 (2nd Shift ODL)'
        if 'odl' in low:
            return 'LCS 11 (1st Shift ODL)'
        return 'LCS 11 (F2F)'
    if 'ec 11' in low or low == 'ec':
        if '2nd shift' in low:
            return 'Effective Communication 11 (2nd Shift ODL)'
        if 'odl' in low:
            return 'Effective Communication 11 (1st Shift ODL)'
        return 'Effective Communication 11 (F2F)'
    if 'cpar 12' in low or 'cpar' in low:
        if 'abu musa' in low:
            return 'CPAR 12 – Abu Musa (ODL)'
        return 'CPAR 12 – Suhayb Ar-Rumi (F2F)'
    if 'ucsp 12' in low or 'ucsp' in low:
        if 'abu musa' in low:
            return 'UCSP 12 – Abu Musa (ODL)'
        return 'UCSP 12 – Suhayb Ar-Rumi (F2F)'
    if 'pfpl 12' in low or 'pfpl' in low:
        if 'abu musa' in low:
            return 'PFPL 12 – Abu Musa (ODL)'
        return 'PFPL 12 – Suhayb Ar-Rumi (F2F)'
    if 'physics 2' in low or 'physics' in low:
        if 'abu musa' in low:
            return 'Physics 2 – Abu Musa (ODL)'
        if 'review' in low:
            return 'Physics Review 12 (F2F)'
        return 'Physics 2 – Suhayb Ar-Rumi (F2F)'
    if 'review 12 f2f' in low:
        return 'Physics Review 12 (F2F)'
    if 'pe 12' in low:
        return 'PE 12 – Suhayb Ar-Rumi (F2F)'

    # High school group sections (Boys / Girls)
    m_hs = re.match(r'^(filipino|fil|math|science|sci|english|eng|soc\.?\s*sci|tle|mapeh|gmrc|arabic|qur\'?an|shaf|esp)\s*[-–]?\s*(7\s*&\s*8|7&8|7\s*/\s*8|9\s*&\s*10|9&10|9\s*/\s*10)\s*[-–]?\s*(boys|girls)?', low)
    if m_hs:
        found_key = m_hs.group(1)
        subj = subj_map.get(found_key, found_key.title())
        gr_str = m_hs.group(2).replace('&', ' & ').replace('/', ' & ')
        gr = re.sub(r'\s+', ' ', gr_str)
        gender = m_hs.group(3)
        if gender:
            return f"{subj} {gr} ({gender.title()})"
        return f"{subj} {gr}"

    # F2F check
    if low in ['filipino 6', 'filipino 6 (f2f)', 'filipino - g2 f2f', 'filipino 2 f2f', 'filipino 3 - f2f', 'filipino 3 f2f', 'filipino 5 f2f', 'fil 4 f2f', 'filipino 4 f2f']:
        m = re.search(r'\d+', low)
        gr = m.group(0) if m else ''
        return f"Filipino {gr} (F2F)"
    if low in ['ap 6 - f2f', 'ap 6 f2f', 'ap 5 f2f', 'ap 5 ftf', 'ap 4 f2f']:
        m = re.search(r'\d+', low)
        gr = m.group(0) if m else ''
        return f"Araling Panlipunan {gr} (F2F)"
    if low in ['mapeh g6', 'mapeh 6', 'mapeh 6 f2f', 'mapeh 4 f2f', 'mapeh 5 f2f']:
        m = re.search(r'\d+', low)
        gr = m.group(0) if m else '6'
        return f"MAPEH {gr} (F2F)"
    if low in ['gmrc 1', 'gmrc 1 f2f', 'gmrc 2 (f2f)', 'gmrc 2 f2f', 'gmrc 3 (f2f)', 'gmrc 3 f2f', 'gmrc - 4 f2f', 'gmrc 4 f2f', 'gmrc 5 f2f', 'gmrc- g6', 'gmrc - g 6', 'gmrc 6']:
        m = re.search(r'\d+', low)
        gr = m.group(0) if m else '1'
        return f"GMRC {gr} (F2F)"

    m_f2f = re.match(r'^(filipino|fil|math|science|sci|english|eng|ap|tle|mapeh|gmrc|arabic|qur\'?an|shaf|hadith)\s*[-–]?\s*([gk]?\d+)?\s*(f2f|ftf)', low)
    if m_f2f:
        found_key = m_f2f.group(1)
        subj = subj_map.get(found_key, found_key.title())
        gr = m_f2f.group(2) or ''
        gr = gr.replace('g', '').replace('k', 'K')
        if gr:
            return f"{subj} {gr} (F2F)"
        return f"{subj} (F2F)"

    # Specific Arabic & Islamic subjects
    if low in ['arabic 12', 'arabic 12 f2f']:
        return 'Arabic 12 (F2F)'
    if 'arabic 12 odl' in low:
        return 'Arabic 12 (ODL)'
    if 'arabic 11 1st shift (girls)' in low or 'arabic 11 1st shift' in low:
        return 'Arabic 11 (1st Shift Girls ODL)'
    if 'arabic 11 2nd shift' in low:
        return 'Arabic 11 (2nd Shift Boys ODL)'
    if 'arabic k2' in low and not any(k in low for k in ['abu', 'uthman', 'bkr', 'khabb']):
        return 'Arabic – Kinder 2 (F2F)'
    if 'arabic - 3 new' in low or 'arabic 3 new' in low or 'arabic-3new' in low:
        return 'Arabic 3 (New)'
    if 'hadith k2' in low and not any(k in low for k in ['uthman', 'umar', 'khabb']):
        return 'Hadith – Kinder 2 (F2F)'
    if 'hadith k1 f2f' in low or 'hadith k1 (f2f)' in low:
        return 'Hadith – Kinder 1 (F2F)'
    if 'qur\'an 11 odl 1st shift' in low or 'qur\'an 11 odl 1 st shift' in low:
        return 'Qur\'an 11 (1st Shift ODL)'
    if 'qur\'an 11 odl 2nd shift' in low:
        return 'Qur\'an 11 (2nd Shift ODL)'
    if 'shaf 11 odl (first shift)' in low:
        return 'SHAF 11 (1st Shift ODL)'
    if 'shaf 11 odl (2nd shift)' in low:
        return 'SHAF 11 (2nd Shift ODL)'
    if 'shaf g12 odl' in low or 'shaf 12 odl' in low:
        return 'SHAF 12 (ODL)'
    if 'math 9 - mix' in low or 'math 9 mix' in low:
        return 'Math 9 (Mix)'
    if 'tle 9 - mix' in low or 'tle 9 mix' in low:
        return 'TLE 9 (Mix)'
    if 'shaf 9 mix' in low or 'shaf 9 - mix' in low:
        return 'SHAF 9 (Mix)'
    if 'tle 7 & 8' in low or 'tle 7&8' in low:
        if 'girls' in low:
            return 'TLE 7 & 8 (Girls)'
        return 'TLE 7 & 8 (Boys)'

    # Check sections with grade level
    for s_raw, s_clean in sorted(SECTIONS.items(), key=lambda x: -len(x[0])):
        if re.search(r'\b' + re.escape(s_raw) + r'\b', low) or s_raw in low:
            rest = low.replace(s_raw, '').strip(' -–()')
            is_kinder = ('k1' in s_raw or 'k2' in s_raw or 'k1' in low or 'k2' in low or 'kinder' in low)
            if is_kinder:
                gr = ""
            else:
                m_gr = re.search(r'\b(?:g|grade)?\s*([1-9]|10|11|12)\b', rest)
                gr = m_gr.group(1) if m_gr else ''
            
            found_subj = None
            for k, val in sorted(subj_map.items(), key=lambda x: -len(x[0])):
                if re.search(r'\b' + re.escape(k) + r'\b', rest) or (k in ['ap', 'fil', 'sci'] and re.search(r'\b' + re.escape(k) + r'\b', low)):
                    found_subj = val
                    break
            if not found_subj:
                for k, val in sorted(subj_map.items(), key=lambda x: -len(x[0])):
                    if re.search(r'\b' + re.escape(k) + r'\b', low):
                        found_subj = val
                        break
            if found_subj:
                shift_tag = ""
                if 'odl' in low:
                    shift_tag = " (ODL)"
                elif '2nd shift' in low:
                    shift_tag = " (2nd Shift)"
                elif '1st shift' in low:
                    shift_tag = " (1st Shift)"
                if gr:
                    return f"{found_subj} {gr} – {s_clean}{shift_tag}"
                else:
                    return f"{found_subj} – {s_clean}{shift_tag}"

    # Capitalization tidy
    s = re.sub(r'^(ARABIC|FILIPINO|SCIENCE|MATH|ENGLISH|AP|TLE|MAPEH|GMRC|SHAF)\b',
               lambda m: m.group(0).title() if m.group(0) not in ['TLE', 'MAPEH', 'GMRC', 'SHAF'] else m.group(0), s)
    return s

# Teachers definition
ELEMENTARY_FACULTY = [
    ('Teacher Wendy', 'ELEM LOADs', 2, 2, wb_new),
    ('Teacher Katrina', 'ELEM LOADs', 2, 10, wb_new),
    ('Teacher Norhydie', 'ELEM LOADs', 2, 19, wb_new),
    ('Teacher Jerlyn', 'ELEM LOADs', 22, 2, wb_old),
    ('Teacher Sahdia', 'ELEM LOADs', 22, 10, wb_new),
    ('Teacher Sitti Kauzar', 'ELEM LOADs', 22, 19, wb_new),
    ('Teacher Arvin', 'ELEM LOADs', 42, 2, wb_old),
    ('Teacher Ayah', 'ELEM LOADs', 42, 10, wb_new),
    ('Teacher Junaisah', 'ELEM LOADs', 42, 19, wb_new),
    ('Teacher Joanna', 'ELEM LOADs', 62, 2, wb_new),
    ('Teacher Marham', 'ELEM LOADs', 62, 10, wb_new),
    ('Teacher Saimonah', 'ELEM LOADs', 62, 19, wb_new),
    ('Teacher Jessa', 'ELEM LOADs', 83, 2, wb_new),
    ('Teacher Anna', 'ELEM LOADs', 83, 10, wb_new),
    ('Teacher Erica', 'ELEM LOADs', 83, 19, wb_new),
    ('Teacher Monisa', 'ELEM LOADs', 104, 2, wb_new),
    ('Teacher Keychell', 'ELEM LOADs', 104, 19, wb_new),
    ('Teacher Jenny', 'ELEM LOADs', 125, 19, wb_new),
]

HIGH_SCHOOL_FACULTY = [
    ('Teacher Radzmia', 'HS LOADS (NEW)', 2, 2, wb_new),
    ('Teacher Halnaisa', 'HS LOADS (NEW)', 2, 10, wb_new),
    ('Teacher Fhairudz', 'HS LOADS (NEW)', 2, 18, wb_new),
    ('Teacher Shirehan', 'HS LOADS (NEW)', 24, 2, wb_new),
    ('Teacher Angeleni', 'HS LOADS (NEW)', 24, 10, wb_new),
    ('Teacher Franchette', 'HS LOADS (NEW)', 24, 18, wb_new),
    ('Teacher Sophia', 'HS LOADS (NEW)', 46, 2, wb_new),
    ('Teacher Jhelyn', 'HS LOADS (NEW)', 46, 10, wb_new),
    ('Teacher Jayra', 'HS LOADS (NEW)', 46, 18, wb_new),
    ('Teacher Nadzra', 'HS LOADS (NEW)', 67, 2, wb_new),
    ('Teacher Ethel', 'HS LOADS (NEW)', 67, 10, wb_new),
    ('Teacher Aniah', 'HS LOADS (NEW)', 67, 18, wb_new),
    ('Teacher Norhaima', 'HS LOADS (NEW)', 88, 2, wb_new),
    ('Teacher Nof', 'HS LOADS (NEW)', 88, 10, wb_new),
    ('Sir Mohaymen', 'HS LOADS (NEW)', 88, 18, wb_new),
    ('Teacher Rowena', 'HS LOADS (NEW)', 109, 2, wb_new),
    ('Teacher Wardah', 'HS LOADS (NEW)', 109, 10, wb_new),
    ('Teacher Hainur', 'HS LOADS (NEW)', 109, 18, wb_old),
]

ISAL_FACULTY = [
    ('Alim Mamonas', 'ISAL LOADs (NEW) ', 3, 2, wb_new),
    ('Alim Bustamante', 'ISAL LOADs (NEW) ', 3, 10, wb_new),
    ('Ustadha Silfah', 'ISAL LOADs (NEW) ', 3, 18, wb_new),
    ('Alim Dipatuan', 'ISAL LOADs (NEW) ', 23, 2, wb_new),
    ('Ustadh Abdiraheem', 'ISAL LOADs (NEW) ', 23, 10, wb_new),
    ('Ustadha Saliha', 'ISAL LOADs (NEW) ', 23, 18, wb_new),
    ('Alim Samsuddin', 'ISAL LOADs (NEW) ', 43, 2, wb_new),
    ('Ustadh Ali', 'ISAL LOADs (NEW) ', 43, 10, wb_new),
    ('Ustadha Samsida', 'ISAL LOADs (NEW) ', 43, 18, wb_new),
    ('Ustadh Jaisam', 'ISAL LOADs (NEW) ', 63, 2, wb_new),
    ('Ustadh Laurel/Nawawi', 'ISAL LOADs (NEW) ', 63, 18, wb_new),
    ('Ustadh Faidh', 'ISAL LOADs (NEW) ', 84, 2, wb_new),
    ('Teacher / Ustadh Ersahad', 'ISAL LOADs (NEW) ', 84, 10, wb_new),
]

ADDITIONAL_FACULTY = [
    ('Ustadh Obaydah', [
        "Arabic 2 (F2F)",
        "Qur'an 1 (F2F)",
        "Qur'an 2 (F2F)",
        "Qur'an 2 – Talha (1st Shift ODL)",
        "Qur'an 2 – Amr (1st Shift ODL)",
        "Qur'an 2 – Saeed (2nd Shift ODL)",
        "Qur'an 2 – Aasim (2nd Shift ODL)",
        "Qur'an 3 (F2F)",
        "Qur'an 3 – Habib (1st Shift ODL)",
        "Qur'an 3 – Ammar (1st Shift ODL)",
        "Qur'an 3 – Salman (1st Shift ODL)",
        "Qur'an 3 – As'ad (2nd Shift ODL)",
        "Qur'an 3 – Zayd (2nd Shift ODL)",
        "Qur'an 3 – Thabit (2nd Shift ODL)",
        "Qur'an 4 (F2F)",
        "Qur'an 4 – Abdur Rahman (1st Shift ODL)",
        "Qur'an 4 – Hakim (1st Shift ODL)",
        "Qur'an 4 – Ikrimah (2nd Shift ODL)",
        "Qur'an 4 – Az Zubair (2nd Shift ODL)",
        "Qur'an 5 (F2F)",
        "Qur'an 5 – Ayyash (1st Shift ODL)",
        "Qur'an 5 – Ja'far (2nd Shift ODL)",
        "Qur'an 6 – Dihya (2nd Shift ODL)"
    ]),
    ('Alim Abdulwahab', [
        "Qur'an 9 & 10 (Boys F2F)",
        "Qur'an 9 & 10 (Girls F2F)",
        "Qur'an 9 – Abu Hurayrah (1st Shift ODL)",
        "Qur'an 9 – Abu Dharr (2nd Shift ODL)",
        "Qur'an 9 – Abu Jandal (2nd Shift ODL)",
        "Qur'an 10 – Utbah (1st Shift ODL)",
        "Qur'an 10 – Abu Ayyub (2nd Shift ODL)",
        "Qur'an 11 (1st Shift Girls ODL)",
        "Qur'an 11 (2nd Shift Boys ODL)"
    ]),
    ('Alim Abdul Karim', [
        "SHAF 1 – Ali (1st Shift ODL)",
        "SHAF 1 – Hudhayfah (1st Shift ODL)",
        "SHAF 1 – Sa'ad (2nd Shift ODL)",
        "SHAF 1 – Suhayb (2nd Shift ODL)",
        "SHAF 2 – Talha (1st Shift ODL)",
        "SHAF 2 – Amr (1st Shift ODL)",
        "SHAF 2 – Saeed (2nd Shift ODL)",
        "SHAF 2 – Aasim (2nd Shift ODL)",
        "SHAF 3 – Habib (1st Shift ODL)",
        "Arabic 5 – Hamza (1st Shift ODL)",
        "Arabic 5 – Muhammad (1st Shift ODL)"
    ])
]

def extract_teacher_loads(t_list, max_r=22):
    res = []
    for name, sname, r, c, wb in t_list:
        sheet = wb[sname]
        items = []
        for row in range(r+2, r+max_r):
            for col in range(c+2, c+7):
                v = sheet.cell(row, col).value
                norm = normalize_item(v, name)
                if norm and norm not in items:
                    items.append(norm)
        res.append((name, items))
    return res

elem_res = extract_teacher_loads(ELEMENTARY_FACULTY, 20)
hs_res = extract_teacher_loads(HIGH_SCHOOL_FACULTY, 22)
isal_res = extract_teacher_loads(ISAL_FACULTY, 20)

# Build text output
lines = []
lines.append("======================================================================")
lines.append("AMIS FACULTY TEACHING LOADS & SUBJECT ASSIGNMENTS")
lines.append("Academic Year: Second Term (Standardized & Expanded)")
lines.append("======================================================================")
lines.append("")

def append_group(group_name, teacher_data):
    lines.append("----------------------------------------------------------------------")
    lines.append(f"  {group_name.upper()}")
    lines.append("----------------------------------------------------------------------")
    lines.append("")
    for t_name, items in teacher_data:
        lines.append(f"{t_name}")
        for idx, it in enumerate(items, 1):
            lines.append(f"  {idx}. {it}")
        lines.append("")

append_group("Elementary Faculty", elem_res)
append_group("High School Faculty", hs_res)
append_group("ISAL Faculty (Islamic Studies & Arabic Language)", isal_res)
append_group("Additional ISAL Faculty", ADDITIONAL_FACULTY)

output_txt = "\n".join(lines)
output_path = "/home/tatsuya/Projects/AMIS/AMIS_Teacher_Subject_Loads.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(output_txt)

print(f"File successfully created: {output_path} ({len(lines)} lines)")
