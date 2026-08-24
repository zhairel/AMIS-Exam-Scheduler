#!/usr/bin/env python3
"""
apply_new_assignments_and_solve.py
Parses the latest official teacher assignments, constructs the exact section curriculum mapping,
and solves all 4 timetable options (Option A, Option B, Option C, Option D) using Google OR-Tools CP-SAT.
"""

import json
import os
import re
import sys
import time
from collections import defaultdict
import numpy as np
from ortools.sat.python import cp_model

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

RAW_SPEC = """
Alim Abdul Karim — TOTAL 11
- Arabic
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH
- SHAF
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM; G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH; G3 — HABIB IBN ZAYD AL-ANSARI (Girls)
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI; G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD

Alim Abdulwahab — TOTAL 9
- Qur'an
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls); G11 (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys); G11 (Boys)

Alim Bustamante — TOTAL 3
- Arabic
  ODL 2nd Shift: K1 — HUSAIN IBN ALI
- SHAF
  ODL 1st Shift: G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G10 — ABU AYYUB AL-ANSARI (Boys)

Alim Dipatuan — TOTAL 3
- Qur'an
  F2F: G11; G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI

Alim Mamonas — TOTAL 9
- Arabic
  F2F: G9–G10 Boys; G9–G10 Girls; G11; G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G10 — UTBAH IBN GHAZWAN (Girls); G11 (Girls); G12 — ABU MUSA AL-ASHARI
  ODL 2nd Shift: G10 — ABU AYYUB AL-ANSARI (Boys); G11 (Boys)

Alim Samsuddin — TOTAL 18
- SHAF
  F2F: G7–G8 Boys; G7–G8 Girls; G9–G10 Boys; G9–G10 Girls; G11; G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls); G9 — ABU HURAYRAH (Girls); G11 (Girls); G12 — ABU MUSA AL-ASHARI
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed); G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G11 (Boys)

Sir Mohaymen — TOTAL 8
- MAPEH
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)
- PE 12
  F2F: G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI

Teacher Angeleni — TOTAL 8
- MAPEH
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys)
- TLE
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)

Teacher Aniah — TOTAL 7
- General Physics 1
  F2F: G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI
- Practical Research 2
  F2F: G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI
- Science
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed)

Teacher Anna — TOTAL 15
- Science
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM; G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH; G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — IKRIMAH IBN ABI JAHL; G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB; G6 — KHALEED IBN WALEED
- TLE
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB

Teacher Arvin — TOTAL 15
- English
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — HASSAN IBN THABIT (Mixed); G4 — IKRIMAH IBN ABI JAHL
- Math
  F2F: G4
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — IKRIMAH IBN ABI JAHL
- TLE
  F2F: G6
  ODL 1st Shift: G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G6 — DIHYA IBN KHALIFAH (Girls); G6 — KHALEED IBN WALEED

Teacher Ayah — TOTAL 4
- Circle Time 1
  ODL 1st Shift: K2 — UTHMAN IBN AFFAN
  ODL 2nd Shift: K2 — ABDULLAH IBN MAS'UD
- Circle Time 2
  ODL 1st Shift: K2 — UTHMAN IBN AFFAN
  ODL 2nd Shift: K2 — ABDULLAH IBN MAS'UD

Teacher Ethel — TOTAL 5
- MIL
  F2F: G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI
- Math
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed)

Teacher Fhairudz — TOTAL 6
- Math
  F2F: G5
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB
- Science
  ODL 2nd Shift: G6 — DIHYA IBN KHALIFAH (Girls)

Teacher Franchette — TOTAL 8
- MAPEH
  F2F: G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Teacher Halnaisa — TOTAL 14
- MAPEH
  F2F: G4
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — IKRIMAH IBN ABI JAHL
- TLE
  F2F: G5; G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Teacher Hannah — TOTAL 5
- Math
  F2F: G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Teacher Jayra — TOTAL 13
- English
  F2F: G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)
- GMRC
  F2F: G5
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB

Teacher Jenny — TOTAL 13
- English
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed); G4 — USAYD IBN HUDHAYR (Mixed)
  ODL 2nd Shift: G3 — AS'AD IBN ZURARAH (Mixed)
- Filipino
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed); G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G3 — AS'AD IBN ZURARAH (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed)
- Makabansa
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed)
  ODL 2nd Shift: G3 — AS'AD IBN ZURARAH (Mixed)
- TLE
  ODL 1st Shift: G4 — USAYD IBN HUDHAYR (Mixed); G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G4 — HASSAN IBN THABIT (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed)

Teacher Jerlyn — TOTAL 12
- Math
  F2F: G3
  ODL 1st Shift: G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls); G3 — SALMAN AL FARSI (Mixed)
  ODL 2nd Shift: G3 — AS'AD IBN ZURARAH (Mixed); G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls)
- Science
  F2F: G3
  ODL 1st Shift: G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls)
  ODL 2nd Shift: G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls)

Teacher Jessa — TOTAL 13
- English
  F2F: G5; G6
  ODL 1st Shift: G5 — AYYASH IBN ABI RABI'AH; G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH; G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — JA'FAR IBN ABI TALIB (Mixed); G5 — MUS'AB IBN ABDUL MUTALIB; G6 — DIHYA IBN KHALIFAH (Girls); G6 — KHALEED IBN WALEED
- Filipino
  F2F: G5

Teacher Jhelyn — TOTAL 10
- General Mathematics
  F2F: G11
  ODL 1st Shift: G11 (Girls)
  ODL 2nd Shift: G11 (Boys)
- Math
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)

Teacher Joanna — TOTAL 12
- Circle Time 1
  ODL 1st Shift: K2 — ABU BAKR AS-SIDEEQ
  ODL 2nd Shift: K2 — UMAR IBN AL-KHATTAB
- Circle Time 2
  ODL 1st Shift: K2 — ABU BAKR AS-SIDEEQ
  ODL 2nd Shift: K2 — UMAR IBN AL-KHATTAB
- Filipino
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB
- Math
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI

Teacher Junaisah — TOTAL 2
- Science
  F2F: G4; G5

Teacher Katrina — TOTAL 8
- Math
  ODL 1st Shift: G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G6 — KHALEED IBN WALEED
- Reading and Literacy
  F2F: G1
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI

Teacher Keychelle — TOTAL 8
- AP
  ODL 1st Shift: G5 — MUHAMMAD IBN MASLAMAH
- Circle Time 1
  F2F: K2
  ODL 2nd Shift: K2 — KHABAAB IBN ARAT
- Circle Time 2
  F2F: K2
  ODL 2nd Shift: K2 — KHABAAB IBN ARAT
- MAPEH
  F2F: G5
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH

Teacher Marham — TOTAL 10
- English
  F2F: G2; G3
  ODL 1st Shift: G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH; G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls)
  ODL 2nd Shift: G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD; G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls)

Teacher Monisa — TOTAL 21
- AP
  F2F: G4
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM; G4 — USAYD IBN HUDHAYR (Mixed); G5 — HAMZA IBN ABDUL
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — HASSAN IBN THABIT (Mixed); G4 — IKRIMAH IBN ABI JAHL; G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB
- Filipino
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM
- Makabansa
  F2F: G2
  ODL 1st Shift: G2 — AMR IBN AL-JAMUH
  ODL 2nd Shift: G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD
- TLE
  F2F: G4
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — IKRIMAH IBN ABI JAHL

Teacher Nadzra — TOTAL 10
- EC
  F2F: G11
  ODL 1st Shift: G11 (Girls)
  ODL 2nd Shift: G11 (Boys)
- Filipino
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)

Teacher Nof — TOTAL 9
- 21st Century Literature
  F2F: G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI
- ESP
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)

Teacher Norhaima — TOTAL 10
- English
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)
- LCS
  F2F: G11
  ODL 1st Shift: G11 (Girls)
  ODL 2nd Shift: G11 (Boys)

Teacher Norhydie — TOTAL 12
- AP
  F2F: G5
- English
  F2F: G4
- Filipino
  F2F: G4
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — IKRIMAH IBN ABI JAHL
- MAPEH
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB
- Makabansa
  F2F: G1
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI

Teacher Normylah — TOTAL 12
- AP
  ODL 1st Shift: G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G6 — DIHYA IBN KHALIFAH (Girls); G6 — KHALEED IBN WALEED
- Filipino
  F2F: G3; G6
  ODL 1st Shift: G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls)
  ODL 2nd Shift: G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls); G6 — DIHYA IBN KHALIFAH (Girls); G6 — KHALEED IBN WALEED

Teacher Radzmia — TOTAL 9
- General Biology 1
  F2F: G11; G12 — SUHAYB AR-RUMI
  ODL 1st Shift: G12 — ABU MUSA AL-ASHARI
  ODL 2nd Shift: G11 (Boys)
- Science
  F2F: G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Teacher Rowena — TOTAL 11
- General Biology 1
  ODL 1st Shift: G11 (Girls)
- General Science
  F2F: G11
  ODL 1st Shift: G11 (Girls)
  ODL 2nd Shift: G11 (Boys)
- Science
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)

Teacher Sahdia — TOTAL 16
- Arabic
  F2F: G1
- GMRC
  F2F: G4
  ODL 1st Shift: G1 — HUDHAYFAH IBN AL-YAM; G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM; G4 — USAYD IBN HUDHAYR (Mixed)
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI; G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — HASSAN IBN THABIT (Mixed); G4 — IKRIMAH IBN ABI JAHL
- Language
  F2F: G1
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI

Teacher Saimonah — TOTAL 15
- AP
  ODL 1st Shift: G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G5 — JA'FAR IBN ABI TALIB (Mixed)
- MAPEH
  ODL 1st Shift: G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G5 — JA'FAR IBN ABI TALIB (Mixed)
- Math
  ODL 1st Shift: G4 — USAYD IBN HUDHAYR (Mixed); G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G4 — HASSAN IBN THABIT (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed); G6 — DIHYA IBN KHALIFAH (Girls)
- Science
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed); G4 — USAYD IBN HUDHAYR (Mixed); G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G3 — AS'AD IBN ZURARAH (Mixed); G4 — HASSAN IBN THABIT (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed)

Teacher Shirehan — TOTAL 11
- PSKP
  F2F: G11
  ODL 1st Shift: G11 (Girls)
  ODL 2nd Shift: G11 (Boys)
- Social Science
  F2F: G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Teacher Sitti Kauzar — TOTAL 9
- Filipino
  F2F: G2
  ODL 1st Shift: G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH
  ODL 2nd Shift: G2 — AASIM IBN THABIT
- Math
  F2F: G2
  ODL 1st Shift: G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH
  ODL 2nd Shift: G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD

Teacher Sophia — TOTAL 15
- Filipino
  F2F: G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)
- Social Science
  F2F: G9–G10 Boys; G9–G10 Girls
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls); G10 — UTBAH IBN GHAZWAN (Girls)
  ODL 2nd Shift: G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls); G10 — ABU AYYUB AL-ANSARI (Boys)

Teacher Wardah — TOTAL 3
- Values Education
  ODL 1st Shift: G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Teacher Wendy — TOTAL 7
- Circle Time 1
  F2F: K1
  ODL 2nd Shift: K1 — HUSAIN IBN ALI
- Circle Time 2
  F2F: K1
  ODL 2nd Shift: K1 — HUSAIN IBN ALI
- Makabansa
  F2F: G3
- Math
  F2F: G1
- Science
  F2F: G6

Teacher Zara — TOTAL 8
- MAPEH
  F2F: G6
  ODL 1st Shift: G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G6 — KHALEED IBN WALEED
- Makabansa
  ODL 1st Shift: G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls)
  ODL 2nd Shift: G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls)

Teacher Zuhora — TOTAL 11
- AP
  F2F: G6
- Filipino
  ODL 1st Shift: G4 — USAYD IBN HUDHAYR (Mixed); G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G2 — SAEED IBN ZAYD; G4 — HASSAN IBN THABIT (Mixed)
- GMRC
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed)
- MAPEH
  ODL 1st Shift: G4 — USAYD IBN HUDHAYR (Mixed)
  ODL 2nd Shift: G4 — HASSAN IBN THABIT (Mixed); G6 — DIHYA IBN KHALIFAH (Girls)
- Makabansa
  ODL 1st Shift: G2 — TALHA IBN UBAYDULLAH

Ustadh Abdiraheem — TOTAL 12
- SHAF
  F2F: G1; G4; G6
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM; G4 — USAYD IBN HUDHAYR (Mixed); G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — HASSAN IBN THABIT (Mixed); G4 — IKRIMAH IBN ABI JAHL; G6 — KHALEED IBN WALEED

Ustadh Ali — TOTAL 21
- Arabic
  F2F: G4; G6; G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM; G4 — USAYD IBN HUDHAYR (Mixed); G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM; G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — HASSAN IBN THABIT (Mixed); G4 — IKRIMAH IBN ABI JAHL; G6 — KHALEED IBN WALEED; G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed); G9 — ABU DHARR AL GHIFARRI (Boys); G9 — ABU JANDAL IBN SUHAYL (Girls)

Ustadh Ersahad — TOTAL 12
- Arabic
  F2F: G5
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB; G6 — DIHYA IBN KHALIFAH (Girls)
- Math
  F2F: G6
- SHAF
  F2F: G2; G3; G5
  ODL 1st Shift: G3 — AMMAR IBN YASIR (Boys)
  ODL 2nd Shift: G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls); G5 — AL HARITH BIN AWF

Ustadh Faidh — TOTAL 15
- Arabic
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed); G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: K2 — KHABAAB IBN ARAT; G3 — AS'AD IBN ZURARAH (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed)
- Hadith
  ODL 2nd Shift: K2 — KHABAAB IBN ARAT
- Qur'an
  F2F: G6
  ODL 1st Shift: G4 — USAYD IBN HUDHAYR (Mixed)
  ODL 2nd Shift: K2 — KHABAAB IBN ARAT; G4 — HASSAN IBN THABIT (Mixed)
- SHAF
  ODL 1st Shift: G3 — SALMAN AL FARSI (Mixed); G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G3 — AS'AD IBN ZURARAH (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed); G6 — DIHYA IBN KHALIFAH (Girls)

Ustadha Hainur — TOTAL 21
- Arabic
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM; G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH
  ODL 2nd Shift: G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI; G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD
- Hadith
  ODL 2nd Shift: K1 — HUSAIN IBN ALI; K2 — ABDULLAH IBN MAS'UD; K2 — UMAR IBN AL-KHATTAB
- Qur'an
  ODL 1st Shift: K2 — ABU BAKR AS-SIDEEQ; K2 — UTHMAN IBN AFFAN; G1 — ALI IBN ABI TALIB; G1 — HUDHAYFAH IBN AL-YAM
  ODL 2nd Shift: K1 — HUSAIN IBN ALI; K2 — ABDULLAH IBN MAS'UD; K2 — UMAR IBN AL-KHATTAB; G1 — SA'AD IBN ABI WAQQAAS; G1 — SUHAYB AR-RUMI
- SHAF
  ODL 2nd Shift: G5 — MUS'AB IBN ABDUL MUTALIB

Ustadh Jaisam — TOTAL 17
- Qur'an
  F2F: K1; K2; G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH; G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM; G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls); G8 — SA'AD IBN MUA'DH (Girls)
  ODL 2nd Shift: G5 — AL HARITH BIN AWF; G5 — MUS'AB IBN ABDUL MUTALIB; G6 — KHALEED IBN WALEED; G7 — ANAS IBN MALIK (Mixed); G8 — MU'ADH IBN JABAL (Boys); G8 — NUAYM IBN MAS'UD (Mixed)

Ustadh Obaydah — TOTAL 23
- Arabic
  F2F: G2
- Qur'an
  F2F: G1; G2; G3; G4; G5
  ODL 1st Shift: G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH; G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls); G3 — SALMAN AL FARSI (Mixed); G4 — ABDUR RAHMAN IBN AWF; G4 — HAKIM IBN HAZM; G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD; G3 — AS'AD IBN ZURARAH (Mixed); G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls); G4 — AZ ZUBAIR IBN AL AWWAAM; G4 — IKRIMAH IBN ABI JAHL; G5 — JA'FAR IBN ABI TALIB (Mixed); G6 — DIHYA IBN KHALIFAH (Girls)

Ustadh Raslina — TOTAL 3
- Arabic
  ODL 1st Shift: G9 — ABU HURAYRAH (Girls)
- SHAF
  ODL 1st Shift: G5 — HAMZA IBN ABDUL; G5 — MUHAMMAD IBN MASLAMAH

Ustadha Saliha — TOTAL 17
- Arabic
  F2F: K1; K2
- GMRC
  F2F: G1; G2; G3
  ODL 1st Shift: G1 — ALI IBN ABI TALIB; G2 — AMR IBN AL-JAMUH; G2 — TALHA IBN UBAYDULLAH; G5 — AYYASH IBN ABI RABI'AH
  ODL 2nd Shift: G2 — AASIM IBN THABIT; G2 — SAEED IBN ZAYD; G3 — AS'AD IBN ZURARAH (Mixed); G5 — JA'FAR IBN ABI TALIB (Mixed)
- Hadith
  F2F: K1; K2
  ODL 1st Shift: K2 — ABU BAKR AS-SIDEEQ; K2 — UTHMAN IBN AFFAN

Ustadha Silfah — TOTAL 23
- Arabic
  F2F: G3
  ODL 1st Shift: K2 — ABU BAKR AS-SIDEEQ; K2 — UTHMAN IBN AFFAN; G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls)
  ODL 2nd Shift: K2 — ABDULLAH IBN MAS'UD; K2 — UMAR IBN AL-KHATTAB; G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls)
- GMRC
  F2F: G6; G7–G8 Boys; G7–G8 Girls
  ODL 1st Shift: G3 — AMMAR IBN YASIR (Boys); G3 — HABIB IBN ZAYD AL-ANSARI (Girls); G6 — ABBAS IBN ABD AL-MUTTALIB; G6 — ABDULLAH IBN SALAAM; G7 — ABU SUFYAN IBN AL-HARITH (Boys); G7 — USAMA IBN ZAYD (Girls)
  ODL 2nd Shift: G3 — THABIT IBN QAYS (Boys); G3 — ZAYD IBN HARITHA (Girls); G6 — DIHYA IBN KHALIFAH (Girls); G6 — KHALEED IBN WALEED; G7 — ANAS IBN MALIK (Mixed)
"""

def clean_sec(s):
    s = s.strip()
    s = re.sub(r'\s*\((Boys|Girls|Mix|Mixed)\)', '', s, flags=re.I)
    s = re.sub(r'\s*—\s*(Boys|Girls|Mix|Mixed)', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*(Boys|Girls|Mix|Mixed)', '', s, flags=re.I)
    s = re.sub(r'\b(Boys|Girls|Mix|Mixed)\b', '', s, flags=re.I)
    return ' '.join(s.split()).strip()

# Parser for RAW_SPEC
lines = RAW_SPEC.strip().split('\n')
cur_teacher = None
cur_subject = None

# We will collect: list of (teacher, subject, grade, section_name, modality, shift, gender)
assignments = []

for line in lines:
    line = line.strip()
    if not line: continue
    
    # Teacher line: "Alim Abdul Karim — TOTAL 11"
    m_t = re.match(r'^([A-Za-z\s\'\.\-]+)\s*—\s*TOTAL\s*(\d+)', line)
    if m_t:
        cur_teacher = m_t.group(1).strip()
        continue
        
    # Subject line: "- Arabic"
    if line.startswith('- '):
        cur_subject = line[2:].strip()
        continue
        
    # Modality line: "F2F: G4; G6" or "ODL 1st Shift: G4 — ..."
    if ':' in line:
        parts = line.split(':', 1)
        mod_shift_part = parts[0].strip()
        items_part = parts[1].strip()
        
        modality = "F2F" if "F2F" in mod_shift_part else "ODL"
        if "1st" in mod_shift_part:
            shift = "1st Shift"
        elif "2nd" in mod_shift_part:
            shift = "2nd Shift"
        else:
            shift = "Day / F2F"
            
        # Parse individual section tokens separated by ';'
        sec_tokens = items_part.split(';')
        for tok in sec_tokens:
            tok = tok.strip()
            if not tok: continue
            
            # Detect gender
            gender = "NOT LABELED"
            if "(Girls)" in tok or "(GIRLS)" in tok or "Girls" in tok:
                gender = "GIRLS"
            elif "(Boys)" in tok or "(BOYS)" in tok or "Boys" in tok:
                gender = "BOYS"
            elif "(Mixed)" in tok or "(MIXED)" in tok or "Mixed" in tok:
                gender = "MIXED"
                
            # Grade extraction
            grade = ""
            if tok.startswith("K1") or tok.startswith("Kinder 1"):
                grade = "Kinder 1"
            elif tok.startswith("K2") or tok.startswith("Kinder 2"):
                grade = "Kinder 2"
            elif tok.startswith("G11") or tok.startswith("Grade 11"):
                grade = "Grade 11"
            elif tok.startswith("G12") or tok.startswith("Grade 12"):
                grade = "Grade 12"
            elif tok.startswith("G9–G10") or tok.startswith("G9-G10") or tok.startswith("Grade 9 & 10"):
                grade = "Grade 9 & 10"
            elif tok.startswith("G7–G8") or tok.startswith("G7-G8") or tok.startswith("Grade 7 & 8"):
                grade = "Grade 7 & 8"
            else:
                m_g = re.match(r'^G(\d+)', tok)
                if m_g:
                    grade = f"Grade {m_g.group(1)}"
                    
            # Section Name extraction
            sec_name = ""
            if "—" in tok or "-" in tok:
                sep = "—" if "—" in tok else "-"
                sec_name = clean_sec(tok.split(sep, 1)[1])
            else:
                if modality == "F2F":
                    if grade in ("Grade 7 & 8", "Grade 9 & 10"):
                        sec_name = "FACE TO FACE"
                    elif grade == "Grade 11":
                        sec_name = "FACE TO FACE"
                    elif grade == "Kinder 1" or grade == "Kinder 2":
                        sec_name = "FACE TO FACE"
                    else:
                        sec_name = "FACE TO FACE"
                else:
                    if grade == "Grade 11":
                        sec_name = "MAIN SECTION"
                    else:
                        sec_name = clean_sec(tok)
                        
            # Section text formatting
            full_sec = sec_name
            if modality == "F2F" and grade in ("Grade 7 & 8", "Grade 9 & 10"):
                full_sec = f"{gender} FACE TO FACE"
            elif modality == "ODL" and grade == "Grade 11":
                full_sec = "Girls" if gender == "GIRLS" else "Boys"
                
            assignments.append({
                "teacher": cur_teacher,
                "subject": cur_subject,
                "grade": grade,
                "section": full_sec,
                "section_name": sec_name,
                "modality": modality,
                "shift": shift,
                "gender": gender
            })

print(f"Total Ingested Assignments: {len(assignments)}")
assert len(assignments) == 602, f"Expected 602 assignments, got {len(assignments)}"

# Group assignments by Section Key: (grade, section, modality, shift)
sec_assignments = defaultdict(list)
for a in assignments:
    k = (a["grade"], a["section"], a["section_name"], a["modality"], a["shift"], a["gender"])
    sec_assignments[k].append((a["subject"], a["teacher"]))

print(f"Total Unique Individual Sections: {len(sec_assignments)}")

# -------------------------------------------------------------
# REBUILD CP-SAT TIMETABLE SOLVER
# -------------------------------------------------------------

EXAM_DAYS = [
    {"dayNo": 1, "date": "2026-09-02", "dayName": "Wednesday", "examDay": "Day 1"},
    {"dayNo": 2, "date": "2026-09-03", "dayName": "Thursday", "examDay": "Day 2"},
    {"dayNo": 3, "date": "2026-09-06", "dayName": "Sunday", "examDay": "Day 3"},
    {"dayNo": 4, "date": "2026-09-07", "dayName": "Monday", "examDay": "Day 4"}
]

def to_mins(t_str):
    t_str = t_str.strip()
    parts = t_str.split()
    hm = parts[0].split(":")
    h, m = int(hm[0]), int(hm[1])
    ampm = parts[1].upper()
    if ampm == "PM" and h != 12: h += 12
    if ampm == "AM" and h == 12: h = 0
    return h * 60 + m

def get_legal_slots(g, m, sh):
    if m == "F2F":
        if g == "Kinder 1":
            return [
                {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2", "periodNo": 2}
            ]
        elif g == "Kinder 2":
            return [
                {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "9:15 AM", "end": "10:15 AM", "time": "9:15 AM – 10:15 AM", "period": "Exam Period 2", "periodNo": 2}
            ]
        else: # Grades 1-12 F2F
            return [
                {"start": "8:00 AM", "end": "9:00 AM", "time": "8:00 AM – 9:00 AM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "9:00 AM", "end": "10:00 AM", "time": "9:00 AM – 10:00 AM", "period": "Exam Period 2", "periodNo": 2},
                {"start": "10:25 AM", "end": "11:25 AM", "time": "10:25 AM – 11:25 AM", "period": "Exam Period 3", "periodNo": 3}
            ]
    elif "1st" in sh:
        return [
            {"start": "12:40 PM", "end": "1:40 PM", "time": "12:40 PM – 1:40 PM", "period": "Exam Period 1", "periodNo": 1},
            {"start": "1:50 PM", "end": "2:50 PM", "time": "1:50 PM – 2:50 PM", "period": "Exam Period 2", "periodNo": 2},
            {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 3", "periodNo": 3}
        ]
    else: # ODL 2nd Shift
        if g == "Kinder 2":
            return [
                {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 2", "periodNo": 2}
            ]
        else:
            return [
                {"start": "3:10 PM", "end": "4:10 PM", "time": "3:10 PM – 4:10 PM", "period": "Exam Period 1", "periodNo": 1},
                {"start": "4:20 PM", "end": "5:20 PM", "time": "4:20 PM – 5:20 PM", "period": "Exam Period 2", "periodNo": 2},
                {"start": "5:30 PM", "end": "6:30 PM", "time": "5:30 PM – 6:30 PM", "period": "Exam Period 3", "periodNo": 3}
            ]

section_list = list(sec_assignments.keys())

def solve_option(option_name="OPTION_A"):
    print(f"\n--- SOLVING {option_name} ---")
    model = cp_model.CpModel()
    
    x = {}
    sec_slot_vars = defaultdict(list)
    sec_day_vars = defaultdict(list)
    teacher_intervals = defaultdict(list)
    teacher_day_vars = defaultdict(list)
    grade_sub_day_vars = defaultdict(list)
    var_lookup = {}
    
    for s_idx, sec_info in enumerate(section_list):
        g, sec, sec_name, mod, sh, gen = sec_info
        legal_slots = get_legal_slots(g, mod, sh)
        sub_list = sec_assignments[sec_info]
        
        for sub_name, teacher in sub_list:
            sub_vars = []
            for d_idx, day_info in enumerate(EXAM_DAYS):
                d_date = day_info["date"]
                for sl_idx, sl in enumerate(legal_slots):
                    var_key = (s_idx, sub_name, teacher, d_idx, sl_idx)
                    var = model.NewBoolVar(f"x_{s_idx}_{sub_name}_{d_idx}_{sl_idx}")
                    x[var_key] = var
                    var_lookup[var_key] = (day_info, sl, sec_info)
                    sub_vars.append(var)
                    
                    sec_slot_vars[(s_idx, d_idx, sl_idx)].append(var)
                    sec_day_vars[(s_idx, d_idx)].append(var)
                    teacher_day_vars[(teacher, d_idx)].append(var)
                    grade_sub_day_vars[(g, sub_name, d_idx)].append(var)
                    
                    st_m = to_mins(sl["start"])
                    et_m = to_mins(sl["end"])
                    dur = et_m - st_m
                    interval = model.NewOptionalIntervalVar(
                        st_m, dur, et_m, var,
                        f"interval_{teacher}_{d_date}_{s_idx}_{sub_name}_{sl_idx}"
                    )
                    teacher_intervals[(teacher, d_date)].append(interval)
                    
            model.AddExactlyOne(sub_vars)
            
    # Section slot constraint (max 1 exam per slot)
    for (s_idx, d_idx, sl_idx), v_list in sec_slot_vars.items():
        model.AddAtMostOne(v_list)
        
    # Section daily capacity
    for (s_idx, d_idx), v_list in sec_day_vars.items():
        sec_info = section_list[s_idx]
        num_subs = len(sec_assignments[sec_info])
        if num_subs in (11, 9): cap = 3
        elif num_subs == 8: cap = 2
        elif num_subs == 5: cap = 2
        else: cap = 2
        model.Add(sum(v_list) <= cap)
        
    # Teacher overlap constraint
    for (teacher, d_date), intervals in teacher_intervals.items():
        model.AddNoOverlap(intervals)
        
    # Objective Formulation
    obj_terms = []
    if option_name == "OPTION_A":
        # Baseline compact flow
        for (s_idx, sub_name, teacher, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 5 + d_idx))
    elif option_name == "OPTION_B":
        # Modality alignment reward
        for (g, sub_name, d_idx), vars_list in grade_sub_day_vars.items():
            if len(vars_list) > 1:
                same_day_cnt = model.NewIntVar(0, len(vars_list), f"cnt_{g}_{sub_name}_{d_idx}")
                model.Add(same_day_cnt == sum(vars_list))
                obj_terms.append(same_day_cnt * -30)
        for (s_idx, sub_name, teacher, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 6))
    elif option_name == "OPTION_C":
        # Teacher workload smoothing
        for (teacher, d_idx), vars_list in teacher_day_vars.items():
            if len(vars_list) > 0:
                t_day_load = model.NewIntVar(0, 10, f"tload_{teacher}_{d_idx}")
                model.Add(t_day_load == sum(vars_list))
                obj_terms.append(t_day_load * 15)
        for (s_idx, sub_name, teacher, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 4))
    elif option_name == "OPTION_D":
        # Student compact flow & early finish
        for (s_idx, sub_name, teacher, d_idx, sl_idx), var in x.items():
            obj_terms.append(var * (sl_idx * 20))
            if sub_name in ("Math", "Science", "English", "General Mathematics", "General Biology 1", "General Physics 1"):
                obj_terms.append(var * (d_idx * 2))
                
    model.Minimize(sum(obj_terms))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120.0
    solver.parameters.num_search_workers = 8
    
    t0 = time.time()
    status = solver.Solve(model)
    elapsed = round(time.time() - t0, 2)
    
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"✗ Solver failed for {option_name}: {solver.StatusName(status)}")
        return None
        
    print(f"✓ Solved {option_name} in {elapsed}s ({solver.StatusName(status)})")
    
    records = []
    for (s_idx, sub_name, teacher, d_idx, sl_idx), var in x.items():
        if solver.Value(var) == 1:
            day_info, sl, sec_info = var_lookup[(s_idx, sub_name, teacher, d_idx, sl_idx)]
            g, sec, sec_name, mod, sh, gen = sec_info
            
            records.append({
                "date": day_info["date"],
                "dayName": day_info["dayName"],
                "examDay": day_info["examDay"],
                "startTime": sl["start"],
                "endTime": sl["end"],
                "time": sl["time"],
                "period": sl.get("period", "Exam Period"),
                "periodNo": sl.get("periodNo", 1),
                "duration": "60 minutes",
                "grade": g,
                "section": sec,
                "section_name": sec_name,
                "gender": gen,
                "modality": mod,
                "shift": sh,
                "subject": sub_name,
                "teacher": teacher,
                "room": "",
                "proctor": teacher,
                "notes": "Term Examination",
                "status": "CONFIRMED"
            })
            
    return records

# Solve all 4 options
opt_a = solve_option("OPTION_A")
opt_b = solve_option("OPTION_B")
opt_c = solve_option("OPTION_C")
opt_d = solve_option("OPTION_D")

all_options_data = {
    "OPTION_A": opt_a,
    "OPTION_B": opt_b,
    "OPTION_C": opt_c,
    "OPTION_D": opt_d
}

out_path = os.path.join(BASE_DIR, "options_exam_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_options_data, f, indent=2, ensure_ascii=False)

with open(os.path.join(BASE_DIR, "exam_data.json"), "w", encoding="utf-8") as f:
    json.dump(opt_a, f, indent=2, ensure_ascii=False)

print(f"\nSaved updated options to: {out_path}")
