import re
import json

TEACHER_REGISTRY = [
    # ISAL / Islamic Studies Faculty
    {
        "id": "tchr_ali",
        "canonical_name": "Ustadz Ali",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": [
            "ali", "ust ali", "ust. ali", "ustadh ali", "ustadz ali", "ustadz muh ali", 
            "ustdz muh ali", "ustadh muh ali", "muh ali", "ust. muh ali", "tchr ali",
            "ustadh muh. ali", "ustadz muh. ali", "ust. muh. ali", "ust. ali"
        ]
    },
    {
        "id": "tchr_abdiraheem",
        "canonical_name": "Ustadh Abdiraheem",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["abdiraheem", "ust. abdi", "abdi", "ustadh abdi", "ust. abdiraheem", "ustadz abdiraheem", "ustadh abdiraheem", "ustadz abdi"]
    },
    {
        "id": "tchr_abdul_karim",
        "canonical_name": "Alim Abdul Karim",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["alim abdul karim", "abdul karim", "alim karim", "abdulkarim", "alim abdulkarim"]
    },
    {
        "id": "tchr_abdulwahab",
        "canonical_name": "Alim Abdulwahab",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["alim abdulwahab", "abdulwahab", "alim wahab", "abdul wahab", "alim abdul wahab"]
    },
    {
        "id": "tchr_bustamante",
        "canonical_name": "Alim Bustamante",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["alim bustamante", "bustamante", "ustadh bustamante", "ustadz bustamante"]
    },
    {
        "id": "tchr_dipatuan",
        "canonical_name": "Alim Dipatuan",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["alim dipatuan", "dipatuan", "ustadh dipatuan", "ustadz dipatuan"]
    },
    {
        "id": "tchr_ersahad",
        "canonical_name": "Ustadh Ersahad",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["ersahad", "ust. ersahad", "ustadh ersahad", "ustadz ersahad"]
    },
    {
        "id": "tchr_faidh",
        "canonical_name": "Ustadh Faidh",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["faidh", "ust. faidh", "ustadh faidh", "ustadz faidh", "faid", "ustadh faid"]
    },
    {
        "id": "tchr_hainur",
        "canonical_name": "Ustadh Hainur",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["hainur", "ust. hainur", "ustadh hainur", "ustadz hainur", "haynur", "ustadh haynur"]
    },
    {
        "id": "tchr_jaisam",
        "canonical_name": "Ustadh Jaisam",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["jaisam", "ust. jaisam", "ustadh jaisam", "ustadz jaisam", "jaysam", "ustadh jaysam"]
    },
    {
        "id": "tchr_mamonas",
        "canonical_name": "Alim Mamonas",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["alim mamonas", "mamonas", "ustadh mamonas", "ustadz mamonas"]
    },
    {
        "id": "tchr_obaydah",
        "canonical_name": "Ustadh Obaydah",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": [
            "obaydah", "ust. obaydah", "ustadh obaydah", "ustadz obaydah", "ubaidah", "ustadh ubaidah",
            "obayda", "ust. obayda", "ustadh obayda", "ustadz obayda", "ubaydah", "ust. ubaydah", "ustadh ubaydah", "ustadz ubaydah"
        ]
    },
    {
        "id": "tchr_raffy",
        "canonical_name": "Ustadh Raffy",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["raffy", "ust. raffy", "ustadh raffy", "ustadz raffy", "rafi", "ustadh rafi"]
    },
    {
        "id": "tchr_raslina",
        "canonical_name": "Ustadh Raslina",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["raslina", "ust. raslina", "ustadh raslina", "ustadz raslina"]
    },
    {
        "id": "tchr_saliha",
        "canonical_name": "Ustadha Saliha",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["saliha", "ust. saliha", "ustadha saliha", "ustadz saliha", "saleha", "ustadha saleha"]
    },
    {
        "id": "tchr_samsuddin",
        "canonical_name": "Alim Samsuddin",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["alim samsuddin", "samsuddin", "alim shamsuddin", "shamsuddin", "ustadh samsuddin"]
    },
    {
        "id": "tchr_silfah",
        "canonical_name": "Ustadha Silfah",
        "department": "ISAL Faculty",
        "title": "ISAL Teacher",
        "aliases": ["silfah", "ust. silfah", "ustadha silfah", "ustadz silfah", "silfa", "ustadha silfa", "ust. silfa"]
    },

    # Academic & High School / Elementary Faculty
    {
        "id": "tchr_mohaymen",
        "canonical_name": "Sir Mohaymen",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["sir mohaymen", "sir moh", "sir. mohaymen", "mohaymen", "sir mohaymin", "tchr mohaymen", "tr. mohaymen"]
    },
    {
        "id": "tchr_abegail",
        "canonical_name": "Teacher Abegail",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher abegail", "tchr. abegail", "tchr abegail", "abegail", "tr. abegail", "abigail", "teacher abigail"]
    },
    {
        "id": "tchr_angeleni",
        "canonical_name": "Teacher Angeleni",
        "department": "Elementary / HS Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher angeleni", "tchr. angeleni", "tchr angeleni", "angeleni", "tr. angeleni", "angel"]
    },
    {
        "id": "tchr_aniah",
        "canonical_name": "Teacher Aniah",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher aniah", "tchr. aniah", "tchr aniah", "aniah", "tr. aniah", "tr aniah"]
    },
    {
        "id": "tchr_anna",
        "canonical_name": "Teacher Anna",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher anna", "tchr. anna", "tchr anna", "anna", "tr. anna", "ana", "teacher ana"]
    },
    {
        "id": "tchr_arvin",
        "canonical_name": "Teacher Arvin",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher arvin", "tchr. arvin", "tchr arvin", "arvin", "tr. arvin", "sir arvin"]
    },
    {
        "id": "tchr_ayah",
        "canonical_name": "Teacher Ayah",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher ayah", "tchr. ayah", "tchr ayah", "ayah", "tr. ayah", "aya", "teacher aya"]
    },
    {
        "id": "tchr_ethel",
        "canonical_name": "Teacher Ethel",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher ethel", "tchr. ethel", "tchr ethel", "ethel", "tr. ethel"]
    },
    {
        "id": "tchr_fhairudz",
        "canonical_name": "Teacher Fhairudz",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher fhairudz", "tchr. fhairudz", "tchr fhairudz", "fhairudz", "fairudz", "fayrudz", "teacher fairudz"]
    },
    {
        "id": "tchr_franchette",
        "canonical_name": "Teacher Franchette",
        "department": "Elementary / HS Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher franchette", "tchr. franchette", "tchr franchette", "franchette", "tr. franchette"]
    },
    {
        "id": "tchr_halnaisa",
        "canonical_name": "Teacher Halnaisa",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher halnaisa", "tchr. halnaisa", "tchr halnaisa", "halnaisa", "halnaisah", "tr. halnaisa"]
    },
    {
        "id": "tchr_hannah",
        "canonical_name": "Teacher Hannah",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher hannah", "tchr. hannah", "tchr hannah", "hannah", "hana", "teacher hana"]
    },
    {
        "id": "tchr_jairah",
        "canonical_name": "Teacher Jairah",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher jairah", "teacher jayra", "tchr. jairah", "tchr. jayra", "tchr jairah", "tchr jayra", "jairah", "jayra", "tr. jairah", "tr. jayra", "tr jayra"]
    },
    {
        "id": "tchr_jenny",
        "canonical_name": "Teacher Jenny",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher jenny", "tchr. jenny", "tchr jenny", "jenny", "jeni", "teacher jeni"]
    },
    {
        "id": "tchr_jerlyn",
        "canonical_name": "Teacher Jerlyn",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher jerlyn", "tchr. jerlyn", "tchr jerlyn", "jerlyn", "gerlyn", "teacher gerlyn"]
    },
    {
        "id": "tchr_jessa",
        "canonical_name": "Teacher Jessa",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher jessa", "tchr. jessa", "tchr jessa", "jessa", "tr. jessa"]
    },
    {
        "id": "tchr_jhelyn",
        "canonical_name": "Teacher Jhelyn",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher jhelyn", "tchr. jhelyn", "tchr jhelyn", "jhelyn", "jhelin", "tr. jhelyn"]
    },
    {
        "id": "tchr_joanna",
        "canonical_name": "Teacher Joanna",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher joanna", "tchr. joanna", "tchr joanna", "joanna", "joana", "teacher joana"]
    },
    {
        "id": "tchr_junaisah",
        "canonical_name": "Teacher Junaisah",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher junaisah", "tchr. junaisah", "tchr junaisah", "junaisah", "junaisa", "teacher junaisa"]
    },
    {
        "id": "tchr_katrina",
        "canonical_name": "Teacher Katrina",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher katrina", "tchr. katrina", "tchr katrina", "katrina", "tr. katrina", "kat", "tchr. kat", "tchr kat", "teacher kat", "tr. kat"]
    },
    {
        "id": "tchr_keychell",
        "canonical_name": "Teacher Keychell",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher keychell", "tchr. keychell", "tchr keychell", "keychell", "kaychell", "tr. keychell"]
    },
    {
        "id": "tchr_marie",
        "canonical_name": "Teacher Marie",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher marie", "tchr. marie", "tchr marie", "marie", "tr. marie"]
    },
    {
        "id": "tchr_marham",
        "canonical_name": "Teacher Marham",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher marham", "tchr. marham", "tchr marham", "marham", "tr. marham"]
    },
    {
        "id": "tchr_monisa",
        "canonical_name": "Teacher Monisa",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher monisa", "tchr. monisa", "tchr monisa", "monisa", "monisah", "tr. monisa"]
    },
    {
        "id": "tchr_nadzra",
        "canonical_name": "Teacher Nadzra",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher nadzra", "tchr. nadzra", "tchr nadzra", "nadzra", "nadzrah", "tr. nadzra", "tchr.  nadzra"]
    },
    {
        "id": "tchr_nof",
        "canonical_name": "Teacher Nof",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher nof", "tchr. nof", "tchr nof", "nof", "tr. nof", "tchr nof"]
    },
    {
        "id": "tchr_norhaima",
        "canonical_name": "Teacher Norhaima",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher norhaima", "tchr. norhaima", "tchr norhaima", "norhaima", "norhaimah", "tr. norhaima"]
    },
    {
        "id": "tchr_norhydie",
        "canonical_name": "Teacher Norhydie",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher norhydie", "tchr. norhydie", "tchr norhydie", "norhydie", "norhidi", "tr. norhydie", "tchr. norhidi"]
    },
    {
        "id": "tchr_normylah",
        "canonical_name": "Teacher Normylah",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher normylah", "tchr. normylah", "tchr normylah", "normylah", "normilah", "tr. normylah", "normayla", "normaila", "tchr. normayla", "tchr normayla", "teacher normayla"]
    },
    {
        "id": "tchr_radzmia",
        "canonical_name": "Teacher Radzmia",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher radzmia", "tchr. radzmia", "tchr radzmia", "radzmia", "radzmiah", "tr. radzmia"]
    },
    {
        "id": "tchr_rowena",
        "canonical_name": "Teacher Rowena",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher rowena", "tchr. rowena", "tchr rowena", "rowena", "tr. rowena"]
    },
    {
        "id": "tchr_sahdia",
        "canonical_name": "Teacher Sahdia",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher sahdia", "tchr. sahdia", "tchr sahdia", "sahdia", "sadiya", "tr. sahdia"]
    },
    {
        "id": "tchr_saimonah",
        "canonical_name": "Teacher Saimonah",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher saimonah", "tchr. saimonah", "tchr saimonah", "saimonah", "saimona", "teacher saimona", "tchr. saimona"]
    },
    {
        "id": "tchr_shanen",
        "canonical_name": "Teacher Shanen",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher shanen", "tchr. shanen", "tchr shanen", "shanen", "tr. shanen"]
    },
    {
        "id": "tchr_shirehan",
        "canonical_name": "Teacher Shirehan",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher shirehan", "tchr. shirehan", "tchr shirehan", "shirehan", "tchr. shi", "tchr shi", "tr. shi", "shi", "teacher shi"]
    },
    {
        "id": "tchr_sitti_kauzar",
        "canonical_name": "Teacher Sitti Kauzar",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher sitti kauzar", "tchr. sitti kauzar", "sitti kauzar", "sitti", "kauzar"]
    },
    {
        "id": "tchr_sophia",
        "canonical_name": "Teacher Sophia",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher sophia", "tchr. sophia", "tchr sophia", "sophia", "sofia", "tr. sophia"]
    },
    {
        "id": "tchr_thea",
        "canonical_name": "Teacher Thea",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher thea", "tchr. thea", "tchr thea", "thea", "tr. thea"]
    },
    {
        "id": "tchr_wardah",
        "canonical_name": "Teacher Wardah",
        "department": "High School Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher wardah", "tchr. wardah", "tchr wardah", "wardah", "warda", "tr. wardah"]
    },
    {
        "id": "tchr_wendy",
        "canonical_name": "Teacher Wendy",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher wendy", "tchr. wendy", "tchr wendy", "wendy", "windi", "tr. wendy", "wendelyn", "tchr. wendelyn", "tchr wendelyn", "teacher wendelyn", "wendelin", "tchr. wendelin"]
    },
    {
        "id": "tchr_zara",
        "canonical_name": "Teacher Zara",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher zara", "tchr. zara", "tchr zara", "zara", "zahra", "teacher zahra"]
    },
    {
        "id": "tchr_zuhora",
        "canonical_name": "Teacher Zuhora",
        "department": "Elementary Faculty",
        "title": "Faculty Member",
        "aliases": ["teacher zuhora", "tchr. zuhora", "tchr zuhora", "zuhora", "zuhra", "teacher zuhra"]
    }
]

# Fast lookup map
LOOKUP_MAP = {}

def clean_key(s):
    if not s: return ""
    s = s.lower().strip()
    s = re.sub(r'[\(\)\[\]\,\.\-\_\—\:\;\"\']', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

for t_record in TEACHER_REGISTRY:
    tid = t_record["id"]
    LOOKUP_MAP[clean_key(t_record["canonical_name"])] = tid
    for a in t_record.get("aliases", []):
        LOOKUP_MAP[clean_key(a)] = tid

def resolve_teacher(raw_str):
    if not raw_str or not isinstance(raw_str, str):
        return None
        
    s = raw_str.strip()
    # Check if raw_str contains 'Subject - Teacher' (e.g. 'Filipino - Tchr. Normayla', 'Math - Tchr. Kat', "Qur'an - Ust. Obayda")
    if ' - ' in s:
        parts = s.split(' - ')
        s = parts[-1].strip()
    elif ' — ' in s:
        parts = s.split(' — ')
        s = parts[-1].strip()
        
    c_key = clean_key(s)
    if c_key in LOOKUP_MAP:
        tid = LOOKUP_MAP[c_key]
        for t in TEACHER_REGISTRY:
            if t["id"] == tid:
                return t
                
    # Try stripping common prefix titles
    # e.g. "tchr", "teacher", "ust", "ustadh", "ustadz", "alim", "sir", "tr"
    tokens = c_key.split()
    if len(tokens) > 1 and tokens[0] in ['tchr', 'teacher', 'ust', 'ustadh', 'ustadz', 'alim', 'sir', 'tr', 'ustadha']:
        core_key = ' '.join(tokens[1:])
        if core_key in LOOKUP_MAP:
            tid = LOOKUP_MAP[core_key]
            for t in TEACHER_REGISTRY:
                if t["id"] == tid:
                    return t
                    
    # Check if any token matches
    for tok in tokens:
        if tok in LOOKUP_MAP and len(tok) > 2:
            tid = LOOKUP_MAP[tok]
            for t in TEACHER_REGISTRY:
                if t["id"] == tid:
                    return t
                    
    return None

if __name__ == "__main__":
    test_cases = [
        "Ust Ali",
        "Ust. Ali",
        "Ustadh Ali",
        "Ustadz Ali",
        "Ustadz Muh Ali",
        "UST.   ALI",
        "Sir Moh",
        "Sir Mohaymen",
        "Teacher Jayra",
        "Tchr. Jairah",
        "Ust. Abdi",
        "Ustadh Abdiraheem",
        "Tchr. Shi",
        "Teacher Shirehan",
        "Tchr. Sahdia",
        "Sahdia",
        "Tchr. Saimona",
        "Saimonah",
        "Tchr. Jessa",
        "Jessa",
        "Ustadha Silfah",
        "Silfa",
        "Tchr. Wendy"
    ]
    
    print("Testing Teacher Resolver & Canonical IDs:")
    all_passed = True
    for tc in test_cases:
        res = resolve_teacher(tc)
        if res:
            print(f"  ✓ {tc:<22} -> ID: {res['id']:<18} | Canonical: {res['canonical_name']}")
        else:
            print(f"  ✗ {tc:<22} -> NOT RESOLVED!")
            all_passed = False
            
    print(f"\nAll test cases resolved successfully: {all_passed}")
