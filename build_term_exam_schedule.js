const XLSX = require('./xlsx.full.min.js');
const engine = require('./exam-parser.js');
const fs = require('fs');
const path = require('path');

// 1. Official Curriculum Requirements per Grade
const CURRICULUM = {
  "Kinder 1": ["Circle Time 1", "Circle Time 2", "Qur'an", "Arabic", "Hadith"],
  "Kinder 2": ["Circle Time 1", "Circle Time 2", "Qur'an", "Arabic", "Hadith"],
  "Grade 1": ["GMRC", "Language", "Reading and Literacy", "Math", "SHAF", "Makabansa", "Arabic", "Qur'an"],
  "Grade 2": ["GMRC", "English", "Filipino", "Math", "Arabic", "SHAF", "Makabansa", "Qur'an"],
  "Grade 3": ["Science", "Math", "GMRC", "Arabic", "English", "Makabansa", "Qur'an", "SHAF", "Filipino"],
  "Grade 4": ["AP", "Math", "TLE", "GMRC", "SHAF", "Arabic", "Qur'an", "MAPEH", "English", "Science", "Filipino"],
  "Grade 5": ["SHAF", "AP", "Filipino", "GMRC", "English", "Qur'an", "MAPEH", "Arabic", "Science", "Math", "TLE"],
  "Grade 6": ["AP", "English", "Science", "Math", "GMRC", "MAPEH", "SHAF", "Qur'an", "TLE", "Arabic", "Filipino"],
  "Grade 7": ["GMRC", "Sci", "Qur'an", "MAPEH", "English", "TLE", "Arabic", "SHAF", "Math", "Soc.Sci", "Filipino"],
  "Grade 7 & 8": ["GMRC", "Sci", "Qur'an", "MAPEH", "English", "TLE", "Arabic", "SHAF", "Math", "Soc.Sci", "Filipino"],
  "Grade 8": ["Sci", "Math", "Values Ed.", "Soc.Sci", "MAPEH", "English", "Filipino", "TLE", "SHAF", "Qur'an", "Arabic"],
  "Grade 9": ["SHAF", "Qur'an", "Math", "TLE", "Soc.Sci", "Arabic", "English", "MAPEH", "Sci", "ESP", "Filipino"],
  "Grade 9 & 10": ["SHAF", "Qur'an", "Math", "TLE", "Soc.Sci", "Arabic", "English", "MAPEH", "Sci", "ESP", "Filipino"],
  "Grade 10": ["Qur'an", "TLE", "Arabic", "SHAF", "MAPEH", "English", "Soc.Sci", "Math", "Filipino", "Sci", "ESP"],
  "Grade 11": ["Arabic", "Gen Bio 1", "Qur'an", "Gen Math", "EC", "PSKP", "LCS", "SHAF", "Gen Science"],
  "Grade 12": ["Gen. Physics 1", "Gen Bio 1", "SHAF", "Arabic", "Qur'an", "21st Lit.", "Prac. Res. 2", "MIL", "PE 12"]
};

// 2. Official Faculty Registry by Department
const FACULTY = {
  "ELEMENTARY": {
    "Tchr. Wendy": ["Circle Time 1", "Circle Time 2", "Math", "Makabansa", "Science"],
    "Tchr. Katrina": ["Reading and Literacy", "Math", "Language", "R & L"],
    "Tchr. Norhydie": ["Makabansa", "Filipino", "English", "AP", "MAPEH"],
    "Tchr. Jerlyn": ["Science", "Math"],
    "Tchr. Sahdia": ["GMRC", "Language", "Arabic"],
    "Tchr. Sitti": ["Math", "Filipino"],
    "Tchr. Arvin": ["Math", "English", "TLE"],
    "Tchr. Ayah": ["Circle Time 1", "Circle Time 2"],
    "Tchr. Junaisah": ["Science"],
    "Tchr. Joanna": ["Circle Time 1", "Circle Time 2", "Math", "Filipino"],
    "Tchr. Marham": ["English"],
    "Tchr. Saimona": ["Math", "Science", "MAPEH", "AP"],
    "Tchr. Jessa": ["English", "Filipino"],
    "Tchr. Anna": ["Science", "TLE"],
    "Tchr. Zuhora": ["Filipino", "Makabansa", "MAPEH", "GMRC", "AP"],
    "Tchr. Monisa": ["Makabansa", "AP", "TLE", "Filipino"],
    "Tchr. Normylah": ["Filipino", "AP"],
    "Tchr. Keychell": ["Circle Time 1", "Circle Time 2", "MAPEH", "AP"],
    "Tchr. Jenny": ["English", "Filipino", "TLE", "Makabansa"],
    "Tchr. Hannah": ["Math"],
    "Tchr. Zara": ["Makabansa", "MAPEH"],
    "Tchr. Fhairudz": ["Math", "Science"]
  },
  "HIGH SCHOOL / SHS": {
    "Tchr. Radzmia": ["Science", "General Biology 1", "General Biology 2", "Sci", "Gen Bio 1"],
    "Tchr. Halnaisa": ["TLE", "MAPEH"],
    "Tchr. Shirehan": ["Social Science", "PSKP", "Soc.Sci", "PSKP 11"],
    "Tchr. Angeleni": ["TLE", "MAPEH"],
    "Tchr. Franchette": ["MAPEH"],
    "Tchr. Sophia": ["Filipino", "Social Science", "Soc.Sci"],
    "Tchr. Jhelyn": ["Math", "General Mathematics", "Gen Math", "Gen Math/HR"],
    "Tchr. Jayra": ["English", "GMRC"],
    "Tchr. Nadzra": ["Filipino", "EC"],
    "Tchr. Ethel": ["Math", "MIL", "UCSP", "CPAR", "Entrepreneurship"],
    "Tchr. Aniah": ["Science", "General Physics 1", "General Physics 2", "Practical Research 2", "3 I's", "Research/Capstone", "Sci", "Gen. Physics 1", "Prac. Res. 2"],
    "Tchr. Norhaima": ["English", "LCS"],
    "Tchr. Nof": ["ESP", "21st Century Literature", "Pagsulat sa Filipino", "EAPP", "21st Lit."],
    "Sir Moh": ["MAPEH", "PE 12"],
    "Tchr. Rowena": ["Science", "General Science", "General Biology 1", "General Biology 2", "Gen Science", "Sci", "Gen Bio 1"],
    "Tchr. Wardah": ["Values Education", "Values Ed."]
  },
  "ISAL": {
    "Alim Mamonas": ["Arabic"],
    "Alim Bustamante": ["Arabic", "SHAF"],
    "Ust. Silfah": ["Arabic", "GMRC"],
    "Alim Dipatuan": ["Qur'an"],
    "Ust. Abdiraheem": ["SHAF"],
    "Ust. Saliha": ["Hadith", "Arabic", "GMRC"],
    "Alim Samsuddin": ["SHAF"],
    "Ust. Ali": ["Arabic"],
    "Ust. Hainur": ["Qur'an", "Hadith", "Arabic", "SHAF"],
    "Ust. Jaisam": ["Qur'an"],
    "Ust. Obaydah": ["Qur'an", "Arabic"],
    "Ust. Faidh": ["Qur'an", "SHAF", "Arabic", "Hadith"],
    "Ust. Ersahad": ["SHAF", "Arabic", "Math"],
    "Alim Abdul Karim": ["SHAF", "Arabic"],
    "Alim Abdulwahab": ["Qur'an"],
    "Ust. Raslina": ["SHAF", "Arabic"],
    "Ustadh Muh Ali": ["Arabic"]
  }
};

// 3. Exam Days & Time Slots
const EXAM_DAYS = [
  { dayNo: 1, date: "2026-09-02", dayName: "Wednesday", examDay: "1st Day" },
  { dayNo: 2, date: "2026-09-03", dayName: "Thursday", examDay: "2nd Day" },
  { dayNo: 3, date: "2026-09-09", dayName: "Wednesday", examDay: "3rd Day" },
  { dayNo: 4, date: "2026-09-10", dayName: "Thursday", examDay: "4th Day" }
];

const TIME_SLOTS = {
  "F2F": ["7:40-8:25 a.m.", "8:25-9:05 a.m.", "9:05-9:45 a.m."],
  "ODL_1": ["12:40-01:20 p.m.", "01:30-02:10 p.m.", "02:20-03:00 p.m."],
  "ODL_2": ["3:40-4:20 p.m.", "4:30-5:10 p.m.", "5:20-6:00 p.m."]
};

function normalizeSub(s) {
  return String(s || '').toLowerCase().replace(/[\.\,\-\_]/g, ' ').replace(/\s+/g, ' ').trim();
}

function isIslamicSubject(sub) {
  const norm = normalizeSub(sub);
  return norm.includes("qur'an") || norm.includes("quran") || norm.includes("arabic") || 
         norm.includes("hadith") || norm.includes("shaf") || norm.includes("gmrc");
}

function getCandidateTeachers(subject, grade) {
  const norm = normalizeSub(subject);
  const isElementary = /kinder|grade\s*[1-6]\b/i.test(grade);
  const isHS = /grade\s*(7|8|9|10|11|12|7 & 8|9 & 10)\b/i.test(grade);

  let candidates = [];

  // If Islamic subject, check ISAL first
  if (isIslamicSubject(subject)) {
    for (const [tName, subs] of Object.entries(FACULTY["ISAL"])) {
      if (subs.some(s => normalizeSub(s) === norm || norm.includes(normalizeSub(s)) || normalizeSub(s).includes(norm))) {
        candidates.push(tName);
      }
    }
  }

  // Elementary general subjects
  if (isElementary) {
    for (const [tName, subs] of Object.entries(FACULTY["ELEMENTARY"])) {
      if (subs.some(s => normalizeSub(s) === norm || norm.includes(normalizeSub(s)) || normalizeSub(s).includes(norm))) {
        if (!candidates.includes(tName)) candidates.push(tName);
      }
    }
  }

  // HS / SHS general subjects
  if (isHS) {
    for (const [tName, subs] of Object.entries(FACULTY["HIGH SCHOOL / SHS"])) {
      if (subs.some(s => normalizeSub(s) === norm || norm.includes(normalizeSub(s)) || normalizeSub(s).includes(norm))) {
        if (!candidates.includes(tName)) candidates.push(tName);
      }
    }
  }

  // Fallback check across all departments if still empty
  if (candidates.length === 0) {
    for (const dept of Object.values(FACULTY)) {
      for (const [tName, subs] of Object.entries(dept)) {
        if (subs.some(s => normalizeSub(s) === norm || norm.includes(normalizeSub(s)) || normalizeSub(s).includes(norm))) {
          if (!candidates.includes(tName)) candidates.push(tName);
        }
      }
    }
  }

  return candidates;
}

// 4. Main Schedule Builder
function buildTermExamSchedule() {
  // Load existing sections to maintain identical structure and room numbers
  const buf = fs.readFileSync("/home/tatsuya/Downloads/Term Examination Schedule S.Y. 2026-2027.xlsx");
  const wb = XLSX.read(buf, { type: "buffer" });
  const ws = wb.Sheets["MASTER EXAM SCHEDULE"];
  const mappingInfo = engine.findHeaderRowAndMapping(ws, XLSX);
  const rawRecords = engine.parseWorksheet(ws, "MASTER EXAM SCHEDULE", mappingInfo, XLSX);

  const sectionsMap = {};
  for (const r of rawRecords) {
    const key = `${r.grade} — ${r.section} (${r.modality} - ${r.shift})`;
    if (!sectionsMap[key]) {
      sectionsMap[key] = {
        grade: r.grade,
        section: r.section,
        gender: r.gender,
        modality: r.modality,
        shift: r.shift,
        room: r.room || ""
      };
    }
  }

  const sectionList = Object.values(sectionsMap);
  console.log(`Scheduling ${sectionList.length} sections across Kinder 1 to Grade 12...`);

  const generatedRecords = [];
  const teacherTimeBookings = new Map(); // `${date}_${time}` => Set of busy teachers
  const teacherLoad = new Map(); // teacher => count
  const sectionPrevTeacher = new Map(); // `${sectionKey}_${date}` => last assigned teacher

  // Helper to check if teacher is free
  function isTeacherFree(teacher, date, time) {
    const key = `${date}_${time}`;
    if (!teacherTimeBookings.has(key)) return true;
    return !teacherTimeBookings.get(key).has(teacher);
  }

  function bookTeacher(teacher, date, time) {
    const key = `${date}_${time}`;
    if (!teacherTimeBookings.has(key)) {
      teacherTimeBookings.set(key, new Set());
    }
    teacherTimeBookings.get(key).add(teacher);
    teacherLoad.set(teacher, (teacherLoad.get(teacher) || 0) + 1);
  }

  // For each section, plan subject distribution across 4 days
  for (const sec of sectionList) {
    const reqSubs = CURRICULUM[sec.grade] || CURRICULUM["Grade 1"];
    const totalSubs = reqSubs.length;

    // Distribute subjects across 4 days
    // e.g. 11: [3, 3, 3, 2], 9: [3, 2, 2, 2], 8: [2, 2, 2, 2], 5: [2, 1, 1, 1]
    let dayCounts = [0, 0, 0, 0];
    if (totalSubs === 11) dayCounts = [3, 3, 3, 2];
    else if (totalSubs === 9) dayCounts = [3, 2, 2, 2];
    else if (totalSubs === 8) dayCounts = [2, 2, 2, 2];
    else if (totalSubs === 5) dayCounts = [2, 1, 1, 1];
    else {
      let rem = totalSubs;
      for (let i = 0; i < 4; i++) {
        const take = Math.ceil(rem / (4 - i));
        dayCounts[i] = take;
        rem -= take;
      }
    }

    let subIndex = 0;
    const timeSlotCategory = sec.modality === "F2F" ? "F2F" : (sec.shift.includes("2nd") ? "ODL_2" : "ODL_1");
    const slots = TIME_SLOTS[timeSlotCategory];

    for (let d = 0; d < 4; d++) {
      const dayInfo = EXAM_DAYS[d];
      const countForDay = dayCounts[d];

      for (let s = 0; s < countForDay; s++) {
        if (subIndex >= reqSubs.length) break;
        const subject = reqSubs[subIndex++];
        const timeSlot = slots[s];

        const candidates = getCandidateTeachers(subject, sec.grade);
        const secDateKey = `${sec.grade}_${sec.section}_${dayInfo.date}`;
        const prevTeacher = sectionPrevTeacher.get(secDateKey);

        // Sort candidates by:
        // 1. Free at (date, time)
        // 2. Anti-consecutive (prefer teacher != prevTeacher)
        // 3. Lowest overall load
        candidates.sort((a, b) => {
          const aFree = isTeacherFree(a, dayInfo.date, timeSlot) ? 0 : 1;
          const bFree = isTeacherFree(b, dayInfo.date, timeSlot) ? 0 : 1;
          if (aFree !== bFree) return aFree - bFree;

          // Anti-consecutive rule: separate not continuous same teacher
          const aIsPrev = (a === prevTeacher) ? 1 : 0;
          const bIsPrev = (b === prevTeacher) ? 1 : 0;
          if (aIsPrev !== bIsPrev) return aIsPrev - bIsPrev;

          // Workload balance
          return (teacherLoad.get(a) || 0) - (teacherLoad.get(b) || 0);
        });

        let assignedTeacher = candidates.find(c => isTeacherFree(c, dayInfo.date, timeSlot));
        if (!assignedTeacher) {
          // If all preferred are busy, pick least loaded candidate
          assignedTeacher = candidates[0] || "TBD";
        }

        bookTeacher(assignedTeacher, dayInfo.date, timeSlot);
        sectionPrevTeacher.set(secDateKey, assignedTeacher);

        generatedRecords.push({
          date: dayInfo.date,
          dayName: dayInfo.dayName,
          examDay: dayInfo.examDay,
          time: timeSlot,
          grade: sec.grade,
          section: sec.section,
          gender: sec.gender,
          modality: sec.modality,
          shift: sec.shift,
          subject: subject,
          teacher: assignedTeacher,
          room: sec.room || "",
          proctor: assignedTeacher,
          remarks: "Term Examination",
          status: "OK"
        });
      }
    }
  }

  console.log(`Generated ${generatedRecords.length} exam slots.`);

  // Validate Generated Schedule
  const valReport = engine.validateAndDetectConflicts(generatedRecords);
  const curReport = engine.checkCurriculumCompleteness(generatedRecords);

  console.log("\n==========================================");
  console.log(" VALIDATION & COMPLETENESS VERIFICATION");
  console.log("==========================================");
  console.log("- Total Records:", generatedRecords.length);
  console.log("- Teacher Conflicts:", valReport.teacherConflicts.length);
  console.log("- Section Conflicts:", valReport.sectionConflicts.length);
  console.log("- Exact Duplicates :", valReport.exactDuplicates.length);
  console.log("- Duplicate Subject Sections:", curReport.duplicateSectionsCount);
  console.log("- Incomplete Sections:", curReport.incompleteSectionsCount);
  console.log("- Overall Curriculum Completeness:", curReport.overallCompletenessPercent + "%");

  // Save generated JSON
  fs.writeFileSync(
    path.join(__dirname, 'exam_data.json'),
    JSON.stringify(generatedRecords, null, 2)
  );

  // Save as Excel workbook
  const outWb = XLSX.utils.book_new();
  const outWs = XLSX.utils.json_to_sheet(generatedRecords.map(r => ({
    "DATE": r.date,
    "DAY": r.dayName,
    "EXAM DAY": r.examDay,
    "TIME": r.time,
    "GRADE": r.grade,
    "SECTION": r.section,
    "GENDER": r.gender,
    "MODALITY": r.modality,
    "SHIFT": r.shift,
    "SUBJECT": r.subject,
    "TEACHER": r.teacher,
    "ROOM": r.room,
    "PROCTOR": r.proctor,
    "REMARKS": r.remarks
  })));

  XLSX.utils.book_append_sheet(outWb, outWs, "MASTER EXAM SCHEDULE");
  const xlsxBuf = XLSX.write(outWb, { type: "buffer", bookType: "xlsx" });
  const xlsxPath = path.join(__dirname, "Term_Examination_Schedule_S.Y._2026-2027_Optimized.xlsx");
  fs.writeFileSync(xlsxPath, xlsxBuf);
  console.log(`Saved optimized Excel to: ${xlsxPath}`);

  return { generatedRecords, valReport, curReport };
}

buildTermExamSchedule();
