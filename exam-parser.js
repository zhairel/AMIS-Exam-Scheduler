/**
 * AMIS Examination Calendar Maker - Core Parsing, Validation & Conflict Detection Engine
 * Browser-side Excel parsing powered by SheetJS (xlsx.js)
 */

(function(global) {
  'use strict';

  const STORAGE_DATA_KEY = 'amis_exam_schedule_data';
  const STORAGE_META_KEY = 'amis_exam_schedule_meta';

  // Priority sheet names to search first
  const PRIORITY_SHEET_NAMES = [
    'MASTER EXAM SCHEDULE',
    'EXAM SCHEDULE',
    'MASTER SCHEDULE',
    'TERM EXAMINATION SCHEDULE',
    'TERM EXAM 2026',
    'TERM EXAM 2026 - 2027',
    'TERM EXAM',
    '2026 MASTER',
    'MASTER',
    'DAILY EXAM SCHEDULE',
    'TEACHER EXAM CALENDAR',
    'SECTION EXAM CALENDAR',
    'F2F / ODL EXAM VIEW',
    'EXAM CALENDAR – ALL STAFF'
  ];

  /**
   * Normalize string for header matching
   */
  function normalizeCol(header) {
    if (header === null || header === undefined) return '';
    return String(header)
      .toLowerCase()
      .replace(/[\r\n\t_—–\/\.\:\#\-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Classify column header name into standard semantic key
   */
  function classifyColumn(header) {
    const norm = normalizeCol(header);
    if (!norm) return null;

    // Proctor / Invigilator
    if (norm.includes('proctor') || norm.includes('invigilator')) {
      return 'proctor';
    }

    // Teacher variations
    if (/^(assigned subject teacher|subject teacher|assigned teacher|teacher name|teacher|instructor|faculty|guro|tchr)$/i.test(norm) ||
        norm.includes('subject teacher') || norm.includes('assigned teacher') || norm === 'teacher') {
      if (!norm.includes('load') && !norm.includes('check') && !norm.includes('count')) return 'teacher';
    }
    if (norm.includes('teacher') && !norm.includes('load') && !norm.includes('check') && !norm.includes('count')) {
      return 'teacher';
    }

    // Time variations
    if (/^(examination time|exam time|time slot|class time|schedule time|time|oras)$/i.test(norm) ||
        norm === 'time' || norm.includes('exam time') || norm.includes('examination time')) {
      return 'time';
    }

    // Exam Day (e.g. "1st Day") vs Day (e.g. "Wednesday")
    if (/^(exam day|examination day)$/i.test(norm) || norm === 'exam day') {
      return 'exam_day';
    }
    if (/^(day of week|day|araw)$/i.test(norm) || norm === 'day') {
      return 'day';
    }

    // Combined Grade & Section / Group
    if (/^(grade section|grade group|grade and section|grade and group|grade level section|grade level group)$/i.test(norm) ||
        (norm.includes('grade') && (norm.includes('group') || norm.includes('section')))) {
      return 'grade_section';
    }

    // Grade variations
    if (/^(grade level|grade|level|year level|grade no|baitang)$/i.test(norm) || norm === 'grade' || norm === 'grade level') {
      return 'grade';
    }

    // Section variations
    if (/^(section name|section|sec|pangkat|class section|room section|group)$/i.test(norm) || norm === 'section' || norm === 'group') {
      return 'section';
    }

    // Subject variations
    if (/^(official subject|exam subject|subject name|subject|course|learning area|asignatura)$/i.test(norm) ||
        norm === 'subject' || (norm.includes('subject') && !norm.includes('teacher') && !norm.includes('check') && !norm.includes('coverage'))) {
      return 'subject';
    }

    // Modality variations
    if (/^(learning modality|modality|mode|delivery mode|schedule type|type)$/i.test(norm) || norm === 'modality' || norm.includes('modality')) {
      return 'modality';
    }

    // Shift variations
    if (/^(shift|session|time shift|schedule shift)$/i.test(norm) || norm === 'shift') {
      return 'shift';
    }

    // Date variations
    if (/^(examination date|exam date|date|petsa)$/i.test(norm) || norm === 'date' || norm.includes('exam date')) {
      return 'date';
    }

    // Room variations
    if (/^(examination room|exam room|room no|room|venue|silid)$/i.test(norm) || norm === 'room') {
      return 'room';
    }

    // Status variations
    if (/^(conflict status|status|schedule status|subject check|teacher check)$/i.test(norm) || norm === 'status') {
      return 'status';
    }

    // Remarks & Source
    if (/^(remarks|notes|comment|details)$/i.test(norm) || norm === 'remarks' || norm.includes('remarks')) {
      return 'remarks';
    }
    if (/^(source sheet|source|block|official schedule block)$/i.test(norm) || norm === 'source') {
      return 'source';
    }

    return null;
  }

  /**
   * Scan top 25 rows of a worksheet to detect header row and column mappings
   */
  function findHeaderRowAndMapping(ws, XLSX_LIB) {
    const XLSX_INST = XLSX_LIB || global.XLSX;
    if (!XLSX_INST || !ws) return { rowIdx: -1, mapping: {}, score: 0, totalRows: 0, missingCrucial: [] };

    const data = XLSX_INST.utils.sheet_to_json(ws, { header: 1, defval: '' });
    let bestRowIdx = -1;
    let bestMapping = {};
    let bestScore = -1;

    for (let r = 0; r < Math.min(25, data.length); r++) {
      const row = data[r];
      if (!row || !Array.isArray(row)) continue;
      const mapping = {};
      let score = 0;
      for (let c = 0; c < row.length; c++) {
        const cellVal = String(row[c] || '').trim();
        const colType = classifyColumn(cellVal);
        if (colType && mapping[colType] === undefined) {
          mapping[colType] = c;
          score += 10;
          if (['time', 'teacher', 'subject', 'date'].includes(colType)) score += 20;
          if (['grade', 'section', 'grade_section'].includes(colType)) score += 15;
          if (['modality', 'shift', 'day'].includes(colType)) score += 10;
        }
      }
      if (score > bestScore) {
        bestScore = score;
        bestRowIdx = r;
        bestMapping = mapping;
      }
    }

    // Identify missing crucial columns
    const missingCrucial = [];
    if (!bestMapping.teacher) missingCrucial.push('Teacher / Assigned Subject Teacher');
    if (!bestMapping.subject) missingCrucial.push('Subject');
    if (!bestMapping.time) missingCrucial.push('Examination Time');
    if (!bestMapping.date && !bestMapping.day) missingCrucial.push('Date / Day');
    if (!bestMapping.grade && !bestMapping.grade_section) missingCrucial.push('Grade Level');
    if (!bestMapping.section && !bestMapping.grade_section) missingCrucial.push('Section');

    return {
      rowIdx: bestRowIdx,
      mapping: bestMapping,
      score: bestScore,
      totalRows: data.length,
      missingCrucial,
      rawHeaders: bestRowIdx >= 0 ? data[bestRowIdx] : []
    };
  }

  /**
   * Automatically detect the best worksheet containing the master exam schedule
   */
  function autoDetectWorksheet(workbook, XLSX_LIB) {
    const XLSX_INST = XLSX_LIB || global.XLSX;
    if (!workbook || !workbook.SheetNames || workbook.SheetNames.length === 0) {
      throw new Error('Workbook contains no sheets.');
    }

    // 1. Try priority sheet names first
    for (const pName of PRIORITY_SHEET_NAMES) {
      const match = workbook.SheetNames.find(s => normalizeCol(s) === normalizeCol(pName));
      if (match) {
        const info = findHeaderRowAndMapping(workbook.Sheets[match], XLSX_INST);
        if (info.score >= 40) {
          return { sheetName: match, info, isPriorityMatch: true };
        }
      }
    }

    // 2. Scan all sheets and score them
    let bestSheet = workbook.SheetNames[0];
    let bestInfo = findHeaderRowAndMapping(workbook.Sheets[bestSheet], XLSX_INST);

    for (const sName of workbook.SheetNames) {
      const info = findHeaderRowAndMapping(workbook.Sheets[sName], XLSX_INST);
      if (info.score > bestInfo.score) {
        bestInfo = info;
        bestSheet = sName;
      }
    }

    return { sheetName: bestSheet, info: bestInfo, isPriorityMatch: false };
  }

  /**
   * Parse Excel serial date, ISO string, or natural date text
   */
  function parseExcelDate(val) {
    if (val === null || val === undefined || val === '') {
      return { dateStr: '', dayName: '', formatted: '' };
    }

    // Excel numeric date serial
    if (typeof val === 'number' || (!isNaN(val) && !isNaN(parseFloat(val)) && isFinite(val) && +val > 20000 && +val < 60000)) {
      const serial = +val;
      const d = new Date(Math.round((serial - 25569) * 86400 * 1000));
      if (!isNaN(d.getTime())) {
        const year = d.getUTCFullYear();
        const month = String(d.getUTCMonth() + 1).padStart(2, '0');
        const day = String(d.getUTCDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;
        const dayName = d.toLocaleDateString('en-US', { weekday: 'long', timeZone: 'UTC' });
        const formatted = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
        return { dateStr, dayName, formatted };
      }
    }

    const str = String(val).trim();
    // Try standard JavaScript Date
    const parsed = new Date(str);
    if (!isNaN(parsed.getTime()) && parsed.getFullYear() > 2000) {
      const year = parsed.getFullYear();
      const month = String(parsed.getMonth() + 1).padStart(2, '0');
      const day = String(parsed.getDate()).padStart(2, '0');
      const dateStr = `${year}-${month}-${day}`;
      const dayName = parsed.toLocaleDateString('en-US', { weekday: 'long' });
      const formatted = parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      return { dateStr, dayName, formatted };
    }

    return { dateStr: str, dayName: '', formatted: str };
  }

  /**
   * Parse 12-hour/24-hour time range string into minutes from midnight
   */
  function parseTimeRange(timeStr) {
    if (!timeStr) return null;
    const s = String(timeStr).replace(/[–—]/g, '-').toLowerCase().trim();
    const parts = s.split('-').map(x => x.trim()).filter(Boolean);
    if (parts.length < 2) return null;

    const endMerMatch = parts[1].match(/([ap])\.?m\.?/);
    const endMer = endMerMatch ? endMerMatch[1] : '';

    function parsePart(p, fallbackMer) {
      const m = p.match(/(\d{1,2}):(\d{2})/);
      if (!m) return null;
      let h = parseInt(m[1], 10);
      const min = parseInt(m[2], 10);
      const merMatch = p.match(/([ap])\.?m\.?/);
      const mer = merMatch ? merMatch[1] : fallbackMer;
      if (mer === 'p' && h !== 12) h += 12;
      if (mer === 'a' && h === 12) h = 0;
      return h * 60 + min;
    }

    let start = parsePart(parts[0], endMer);
    let end = parsePart(parts[1], endMer);
    if (start === null || end === null) return null;
    if (end <= start) end += 720;
    return { startMinutes: start, endMinutes: end, raw: timeStr };
  }

  /**
   * Extract gender (Boys, Girls, Mix) if present in strings
   */
  function extractGender(grade, section, block, extra) {
    const combined = `${grade || ''} ${section || ''} ${block || ''} ${extra || ''}`.toLowerCase();
    if (/\b(boys|boy|lalaki)\b/i.test(combined)) return 'Boys';
    if (/\b(girls|girl|babae)\b/i.test(combined)) return 'Girls';
    if (/\b(mix|mixed|co-ed|coed)\b/i.test(combined)) return 'Mix';
    return '';
  }

  /**
   * Separate combined Grade & Section strings if necessary
   */
  function parseGradeAndSection(gradeVal, sectionVal, gradeSectionVal) {
    let grade = String(gradeVal || '').trim();
    let section = String(sectionVal || '').trim();

    if (!grade && !section && gradeSectionVal) {
      const combined = String(gradeSectionVal).trim();
      if (combined.includes('—')) {
        const parts = combined.split('—').map(s => s.trim());
        grade = parts[0];
        section = parts.slice(1).join(' — ');
      } else if (combined.includes('-')) {
        const parts = combined.split('-').map(s => s.trim());
        grade = parts[0];
        section = parts.slice(1).join(' - ');
      } else {
        grade = combined;
        section = combined;
      }
    }

    // Handle nested format like GRADE 3 - ZAYD IBN HARITHA (2ND SHIFT) - GIRLS
    if (grade && !section && grade.includes(' - ')) {
      const parts = grade.split(' - ').map(s => s.trim());
      grade = parts[0];
      section = parts.slice(1).join(' - ');
    }

    // Default fallbacks if grade has section name
    if (!section && grade.toLowerCase().includes('grade')) {
      section = 'Official Class';
    }

    return { grade, section };
  }

  /**
   * Convert worksheet rows into clean JavaScript exam objects
   */
  function parseWorksheet(ws, sheetName, mappingInfo, XLSX_LIB) {
    const XLSX_INST = XLSX_LIB || global.XLSX;
    if (!ws || !mappingInfo) return [];

    const data = XLSX_INST.utils.sheet_to_json(ws, { header: 1, defval: '' });
    const { rowIdx, mapping } = mappingInfo;
    if (rowIdx < 0) return [];

    const records = [];
    for (let r = rowIdx + 1; r < data.length; r++) {
      const row = data[r];
      if (!row || row.every(c => c === '' || c === null || c === undefined)) continue;

      const getVal = key => {
        if (mapping[key] !== undefined && row[mapping[key]] !== undefined) {
          return row[mapping[key]];
        }
        return '';
      };

      const dateRaw = getVal('date');
      const dateInfo = parseExcelDate(dateRaw);
      const dayVal = String(getVal('day') || dateInfo.dayName || '').trim();
      const examDayVal = String(getVal('exam_day') || getVal('day') || '').trim();

      const gradeRaw = getVal('grade');
      const sectionRaw = getVal('section');
      const gradeSectionRaw = getVal('grade_section');
      const { grade, section } = parseGradeAndSection(gradeRaw, sectionRaw, gradeSectionRaw);

      let modality = String(getVal('modality') || '').trim();
      if (!modality) {
        if (section.toUpperCase().includes('F2F') || section.toUpperCase().includes('FACE TO FACE')) {
          modality = 'F2F';
        } else if (section.toUpperCase().includes('ODL') || section.toUpperCase().includes('ONLINE')) {
          modality = 'ODL';
        } else {
          modality = 'F2F';
        }
      }

      let shift = String(getVal('shift') || '').trim();
      if (!shift) {
        if (modality === 'F2F') shift = 'Day / F2F';
        else if (section.toLowerCase().includes('1st') || section.toLowerCase().includes('first')) shift = '1st Shift';
        else if (section.toLowerCase().includes('2nd') || section.toLowerCase().includes('second')) shift = '2nd Shift';
        else shift = 'Regular Shift';
      }

      const teacher = String(getVal('teacher') || '').trim();
      const subject = String(getVal('subject') || '').trim();
      const time = String(getVal('time') || '').trim();
      const proctor = String(getVal('proctor') || '').trim();
      const room = String(getVal('room') || '').trim();
      const status = String(getVal('status') || 'OK').trim() || 'OK';
      const remarks = String(getVal('remarks') || '').trim();
      const source = String(getVal('source') || sheetName || '').trim();
      const block = `${grade} ${section ? '— ' + section : ''}`.trim();

      // Extract gender (Boys, Girls, Mix, or "")
      const gender = extractGender(grade, section, block, remarks);

      // Only add row if it has some meaningful exam data (subject, time, teacher, or grade)
      if (subject || time || teacher || grade) {
        records.push({
          id: `exam_${records.length + 1}`,
          examDay: examDayVal || (dateInfo.dayName ? dateInfo.dayName : `Day ${records.length + 1}`),
          date: dateInfo.dateStr || dateRaw,
          day: dayVal || dateInfo.dayName,
          grade: grade || 'Unspecified Grade',
          section: section || 'Unspecified Section',
          gender: gender,
          modality: modality || 'F2F',
          shift: shift || 'Day / F2F',
          time: time,
          subject: subject,
          teacher: teacher,
          proctor: proctor,
          room: room,
          status: status,
          remarks: remarks,
          source: source,
          block: block
        });
      }
    }

    return records;
  }

  /**
   * Run comprehensive validation and conflict detection
   */
  function validateAndDetectConflicts(records) {
    const issues = [];
    const exactDuplicates = [];
    const teacherConflicts = [];
    const sectionConflicts = [];
    const exactSigMap = new Map();

    // 1. Per-record validation
    records.forEach((r, idx) => {
      const teacher = String(r.teacher || '').trim();
      const subject = String(r.subject || '').trim();
      const grade = String(r.grade || '').trim();
      const section = String(r.section || '').trim();
      const date = String(r.date || '').trim();
      const time = String(r.time || '').trim();
      const modality = String(r.modality || '').trim();
      const shift = String(r.shift || '').trim();

      // Missing teacher
      if (!teacher || /^(tbd|tba|none|n\/a|\?|--|---)$/i.test(teacher)) {
        issues.push({
          type: 'MISSING_TEACHER',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Missing teacher assignment for ${grade} - ${section} (${subject || 'No Subject'})`
        });
      }

      // Missing subject
      if (!subject || subject === '---') {
        issues.push({
          type: 'MISSING_SUBJECT',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Missing subject for ${grade} - ${section} at ${time || 'unspecified time'}`
        });
      }

      // Missing grade
      if (!grade || grade === 'Unspecified Grade') {
        issues.push({
          type: 'MISSING_GRADE',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Missing grade level for ${subject || 'exam'} with ${teacher || 'teacher'}`
        });
      }

      // Missing section
      if (!section || section === 'Unspecified Section') {
        issues.push({
          type: 'MISSING_SECTION',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Missing section for ${grade} - ${subject || 'exam'}`
        });
      }

      // Missing exam date
      if (!date) {
        issues.push({
          type: 'MISSING_DATE',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Missing exam date for ${grade} - ${section} (${subject})`
        });
      }

      // Missing exam time
      if (!time || !parseTimeRange(time)) {
        issues.push({
          type: 'MISSING_TIME',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Missing or unparseable exam time: "${time}" for ${subject} (${grade})`
        });
      }

      // Modality check
      const modUpper = modality.toUpperCase();
      if (modUpper && !['F2F', 'ODL', 'ONLINE', 'FACE TO FACE', 'FACE-TO-FACE', 'HYBRID'].includes(modUpper)) {
        issues.push({
          type: 'INVALID_MODALITY',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Non-standard modality "${modality}" in ${grade} - ${section}`
        });
      }

      // Shift check
      const shiftLow = shift.toLowerCase();
      if (shiftLow && !shiftLow.includes('shift') && !shiftLow.includes('f2f') && !shiftLow.includes('day') && !shiftLow.includes('regular')) {
        issues.push({
          type: 'INVALID_SHIFT',
          recordId: r.id,
          index: idx,
          record: r,
          message: `Unrecognized shift "${shift}" in ${grade} - ${section}`
        });
      }

      // Exact signature tracking
      const sig = `${date}|${time}|${grade}|${section}|${subject}|${teacher}`.toLowerCase().replace(/\s+/g, ' ');
      if (exactSigMap.has(sig)) {
        const firstIdx = exactSigMap.get(sig);
        exactDuplicates.push({
          type: 'EXACT_DUPLICATE',
          recordId: r.id,
          index: idx,
          firstIndex: firstIdx,
          record: r,
          firstRecord: records[firstIdx],
          message: `Exact duplicate exam entry detected for ${teacher} (${subject} / ${grade} ${section}) on ${date} at ${time}`
        });
      } else {
        exactSigMap.set(sig, idx);
      }
    });

    // 2. Pairwise conflict detection
    for (let i = 0; i < records.length; i++) {
      for (let j = i + 1; j < records.length; j++) {
        const a = records[i];
        const b = records[j];

        if (a.date !== b.date || !a.date) continue;

        const tA = parseTimeRange(a.time);
        const tB = parseTimeRange(b.time);
        const timeOverlaps = tA && tB
          ? (tA.startMinutes < tB.endMinutes && tB.startMinutes < tA.endMinutes)
          : (String(a.time).trim().toLowerCase() === String(b.time).trim().toLowerCase() && a.time !== '');

        if (timeOverlaps) {
          // Teacher double booking / overlapping
          if (a.teacher && b.teacher && a.teacher.trim().toLowerCase() === b.teacher.trim().toLowerCase() && !/^(tbd|tba|none)$/i.test(a.teacher)) {
            const isExact = (a.grade === b.grade && a.section === b.section && a.subject === b.subject);
            const isSameTime = (String(a.time).trim().toLowerCase() === String(b.time).trim().toLowerCase());
            const msg = isExact
              ? `Teacher ${a.teacher} has identical duplicate entry on ${a.date} at ${a.time}`
              : isSameTime
                ? `Teacher ${a.teacher} is double-booked at ${a.time} on ${a.date} (${a.grade}/${a.section} & ${b.grade}/${b.section})`
                : `Teacher ${a.teacher} has overlapping schedules on ${a.date} (${a.time} vs ${b.time})`;

            a.isTeacherConflict = true;
            b.isTeacherConflict = true;
            if (isExact) { a.isExactDuplicate = true; b.isExactDuplicate = true; }
            a.conflictMessage = msg;
            b.conflictMessage = msg;

            teacherConflicts.push({
              type: isExact ? 'EXACT_DUPLICATE' : (isSameTime ? 'TEACHER_SAME_TIME_DOUBLE_BOOKING' : 'TEACHER_OVERLAPPING_SCHEDULE'),
              teacher: a.teacher,
              date: a.date,
              timeA: a.time,
              timeB: b.time,
              aIdx: i,
              bIdx: j,
              a,
              b,
              message: msg
            });
          }

          // Section double booking (two different subjects scheduled for the same section at overlapping times)
          if (a.grade && b.grade && a.section && b.section &&
              `${a.grade}|${a.section}`.toLowerCase() === `${b.grade}|${b.section}`.toLowerCase() &&
              a.section !== 'FACE TO FACE' && a.section !== 'Unspecified Section') {
            if (a.subject !== b.subject || a.teacher !== b.teacher) {
              const secMsg = `Section ${a.grade} — ${a.section} has simultaneous exams at ${a.time}: "${a.subject}" (${a.teacher}) and "${b.subject}" (${b.teacher})`;
              a.isSectionConflict = true;
              b.isSectionConflict = true;
              a.sectionConflictMessage = secMsg;
              b.sectionConflictMessage = secMsg;

              sectionConflicts.push({
                type: 'SECTION_DOUBLE_BOOKING',
                section: `${a.grade} — ${a.section}`,
                date: a.date,
                timeA: a.time,
                timeB: b.time,
                aIdx: i,
                bIdx: j,
                a,
                b,
                message: secMsg
              });
            }
          }
        }
      }
    }

    const uniqueTeachers = [...new Set(records.map(r => r.teacher).filter(Boolean))];
    const uniqueDates = [...new Set(records.map(r => r.date).filter(Boolean))].sort();
    const uniqueSections = [...new Set(records.map(r => `${r.grade} — ${r.section}`).filter(Boolean))];

    return {
      totalEntries: records.length,
      teachersCount: uniqueTeachers.length,
      datesCount: uniqueDates.length,
      sectionsCount: uniqueSections.length,
      uniqueTeachers,
      uniqueDates,
      uniqueSections,
      issues,
      exactDuplicates,
      teacherConflicts,
      sectionConflicts,
      totalConflicts: exactDuplicates.length + teacherConflicts.length + sectionConflicts.length,
      hasIssues: issues.length > 0 || teacherConflicts.length > 0 || sectionConflicts.length > 0
    };
  }

  /**
   * Official AMIS Required Curriculum Subjects per Grade Level
   */
  const REQUIRED_CURRICULUM = {
    'Kinder 1': ['Circle Time 1', 'Circle Time 2', "Qur'an", 'Arabic', 'Hadith'],
    'Kinder 2': ['Circle Time 1', 'Circle Time 2', "Qur'an", 'Arabic', 'Hadith'],
    'Grade 1': ['GMRC', 'Language', 'Reading and Literacy', 'Math', 'SHAF', 'Makabansa', 'Arabic', "Qur'an"],
    'Grade 2': ['GMRC', 'English', 'Filipino', 'Math', 'Arabic', 'SHAF', 'Makabansa', "Qur'an"],
    'Grade 3': ['Science', 'Math', 'GMRC', 'Arabic', 'English', 'Makabansa', "Qur'an", 'SHAF', 'Filipino'],
    'Grade 4': ['AP', 'Math', 'TLE', 'GMRC', 'SHAF', 'Arabic', "Qur'an", 'MAPEH', 'English', 'Science', 'Filipino'],
    'Grade 5': ['SHAF', 'AP', 'Filipino', 'GMRC', 'English', "Qur'an", 'MAPEH', 'Arabic', 'Science', 'Math', 'TLE'],
    'Grade 6': ['AP', 'English', 'Science', 'Math', 'GMRC', 'MAPEH', 'SHAF', "Qur'an", 'TLE', 'Arabic', 'Filipino'],
    'Grade 7': ['GMRC', 'Sci', "Qur'an", 'MAPEH', 'English', 'TLE', 'Arabic', 'SHAF', 'Math', 'Soc.Sci', 'Filipino'],
    'Grade 8': ['Sci', 'Math', 'Values Ed.', 'Soc.Sci', 'MAPEH', 'English', 'Filipino', 'TLE', 'SHAF', "Qur'an", 'Arabic'],
    'Grade 9': ['SHAF', "Qur'an", 'Math', 'TLE', 'Soc.Sci', 'Arabic', 'English', 'MAPEH', 'Sci', 'ESP', 'Filipino'],
    'Grade 10': ["Qur'an", 'TLE', 'Arabic', 'SHAF', 'MAPEH', 'English', 'Soc.Sci', 'Math', 'Filipino', 'Sci', 'ESP'],
    'Grade 11': ['Arabic', 'Gen Bio 1', "Qur'an", 'Gen Math', 'EC', 'PSKP', 'LCS', 'SHAF', 'Gen Science'],
    'Grade 12': ['Gen. Physics 1', 'Gen Bio 1', 'SHAF', 'Arabic', "Qur'an", '21st Lit.', 'Prac. Res. 2', 'MIL', 'PE 12']
  };

  // Support combined junior high school designations
  REQUIRED_CURRICULUM['Grade 7 & 8'] = REQUIRED_CURRICULUM['Grade 7'];
  REQUIRED_CURRICULUM['Grade 9 & 10'] = REQUIRED_CURRICULUM['Grade 9'];

  /**
   * Normalize subject name to match curriculum standards
   */
  function normalizeSubjectKey(name) {
    let s = String(name || '').trim().toLowerCase();
    s = s.replace(/['`"\.]/g, '');
    // Handle specific numbered subjects first
    if (/^(circle time 1|ct 1|ct1)$/.test(s)) return 'circle time 1';
    if (/^(circle time 2|ct 2|ct2)$/.test(s)) return 'circle time 2';
    if (/^(gen bio 1|general biology 1|biology)$/.test(s)) return 'gen bio 1';
    if (/^(gen physics 1|general physics 1|gen physics)$/.test(s)) return 'gen physics 1';
    if (/^(prac res 2|practical research 2|pr2)$/.test(s)) return 'prac res 2';
    if (/^(pe 12|pe|physical education)$/.test(s)) return 'pe 12';

    // Strip trailing grade/shift numbers e.g. "Math 5", "Math5", "AP4", "Sci4", "Fil3", "GMRC5", "SHAF 5"
    s = s.replace(/\b(1st|2nd)\s+shift\b/g, '').trim();
    s = s.replace(/\/(hr|homeroom|advisory)\b/g, '').trim();
    s = s.replace(/\b(1|2|3|4|5|6|7|8|9|10|11|12)\b/g, '').trim();

    if (/^(reading and literacy|reading & literacy|r & l|rl|reading)$/.test(s)) return 'reading and literacy';
    if (/^(language|lang)$/.test(s)) return 'language';
    if (/^(makabansa|makabansa\d*)$/.test(s)) return 'makabansa';
    if (/^(quran|qur'an|quran\d*)$/.test(s)) return 'quran';
    if (/^(arabic|arab|arabic\d*)$/.test(s)) return 'arabic';
    if (/^(hadith)$/.test(s)) return 'hadith';
    if (/^(gmrc|gmrc\d*)$/.test(s)) return 'gmrc';
    if (/^(shaf|shaf\d*)$/.test(s)) return 'shaf';
    if (/^(filipino|fil|fil\d*)$/.test(s)) return 'filipino';
    if (/^(english|eng|eng\d*)$/.test(s)) return 'english';
    if (/^(math|gen math|general math|math\d*)$/.test(s)) return 'math';
    if (/^(science|sci|sci\d*|science\d*)$/.test(s)) return 'science';
    if (/^(ap|ap\d*|socsci|soc sci|social science)$/.test(s)) return 'ap';
    if (/^(mapeh|mapeh\d*)$/.test(s)) return 'mapeh';
    if (/^(tle|tle\d*)$/.test(s)) return 'tle';
    if (/^(values ed|values education|esp)$/.test(s)) return 'values ed';
    if (/^(gen science|general science)$/.test(s)) return 'gen science';
    if (/^(gen bio|gen bio 1|general biology 1|biology)$/.test(s)) return 'gen bio 1';
    if (/^(gen physics 1|general physics 1|gen physics)$/.test(s)) return 'gen physics 1';
    if (/^(21st lit|21st century literature|21st lit)$/.test(s)) return '21st lit';
    if (/^(prac res 2|practical research 2|pr2)$/.test(s)) return 'prac res 2';
    if (/^(mil|media and information literacy)$/.test(s)) return 'mil';
    if (/^(pe 12|pe|physical education)$/.test(s)) return 'pe 12';
    if (/^(lcs|lcs 11)$/.test(s)) return 'lcs';
    if (/^(pskp|pskp 11)$/.test(s)) return 'pskp';
    if (/^(ec)$/.test(s)) return 'ec';

    return s;
  }

  /**
   * Track subject completeness and duplicates for each section
   */
  function checkCurriculumCompleteness(records) {
    if (!Array.isArray(records) || records.length === 0) {
      return {
        totalSections: 0,
        completeSectionsCount: 0,
        incompleteSectionsCount: 0,
        duplicateSectionsCount: 0,
        sectionReports: []
      };
    }

    // Group records by distinct section
    const sectionMap = {};
    for (const r of records) {
      const key = `${r.grade} — ${r.section} (${r.modality} - ${r.shift})`;
      if (!sectionMap[key]) {
        sectionMap[key] = {
          sectionKey: key,
          grade: r.grade,
          section: r.section,
          gender: r.gender,
          modality: r.modality,
          shift: r.shift,
          exams: []
        };
      }
      sectionMap[key].exams.push(r);
    }

    let completeCount = 0;
    let incompleteCount = 0;
    let duplicateCount = 0;
    const sectionReports = [];

    for (const [secKey, secObj] of Object.entries(sectionMap)) {
      const reqList = REQUIRED_CURRICULUM[secObj.grade] || [];
      const scheduledNormalized = secObj.exams.map(e => ({
        origSubject: e.subject,
        normKey: normalizeSubjectKey(e.subject),
        exam: e
      }));

      const missing = [];
      const duplicates = [];
      const checklist = [];

      for (const req of reqList) {
        const reqKey = normalizeSubjectKey(req);
        const matches = scheduledNormalized.filter(s => s.normKey === reqKey);

        if (matches.length === 0) {
          missing.push(req);
          checklist.push({
            requiredSubject: req,
            status: 'MISSING',
            matches: []
          });
        } else if (matches.length === 1) {
          checklist.push({
            requiredSubject: req,
            status: 'OK',
            matches: matches.map(m => m.exam)
          });
        } else {
          // Multiple exams scheduled for the same required subject
          duplicates.push({
            requiredSubject: req,
            count: matches.length,
            matches: matches.map(m => m.exam)
          });
          checklist.push({
            requiredSubject: req,
            status: 'DUPLICATE',
            matches: matches.map(m => m.exam)
          });

          // Tag each individual exam record for UI rendering
          const summaryStr = matches.map(m => `${m.exam.date} ${m.exam.time} (${m.exam.subject})`).join(', ');
          for (const m of matches) {
            m.exam.isSubjectDuplicate = true;
            m.exam.duplicateSubjectName = req;
            m.exam.duplicateCount = matches.length;
            m.exam.duplicateSlotsSummary = summaryStr;
          }
        }
      }

      // Check extra unscheduled subjects
      const reqKeys = new Set(reqList.map(r => normalizeSubjectKey(r)));
      const extraSubjects = scheduledNormalized
        .filter(s => !reqKeys.has(s.normKey))
        .map(s => s.exam);

      const isComplete = reqList.length > 0 ? (missing.length === 0) : true;
      const hasDuplicates = duplicates.length > 0;

      if (isComplete) completeCount++;
      else incompleteCount++;

      if (hasDuplicates) duplicateCount++;

      sectionReports.push({
        sectionKey: secKey,
        grade: secObj.grade,
        section: secObj.section,
        gender: secObj.gender,
        modality: secObj.modality,
        shift: secObj.shift,
        totalRequired: reqList.length,
        foundCount: reqList.length - missing.length,
        percent: reqList.length > 0 ? Math.round(((reqList.length - missing.length) / reqList.length) * 100) : 100,
        isComplete,
        hasDuplicates,
        missingSubjects: missing,
        duplicateSubjects: duplicates,
        extraSubjects,
        checklist,
        examsCount: secObj.exams.length
      });
    }

    // Sort: Incomplete and duplicate sections first, then by Grade
    sectionReports.sort((a, b) => {
      if (a.isComplete !== b.isComplete) return a.isComplete ? 1 : -1;
      if (a.hasDuplicates !== b.hasDuplicates) return a.hasDuplicates ? -1 : 1;
      return a.grade.localeCompare(b.grade, undefined, { numeric: true }) || a.section.localeCompare(b.section);
    });

    return {
      totalSections: sectionReports.length,
      completeSectionsCount: completeCount,
      incompleteSectionsCount: incompleteCount,
      duplicateSectionsCount: duplicateCount,
      sectionReports
    };
  }

  /**
   * Save parsed schedule and metadata to localStorage
   */
  function saveScheduleToStorage(records, meta) {
    try {
      localStorage.setItem(STORAGE_DATA_KEY, JSON.stringify(records));
      localStorage.setItem(STORAGE_META_KEY, JSON.stringify(meta));
      return true;
    } catch (e) {
      console.warn('LocalStorage save failed, quota exceeded or private mode:', e);
      return false;
    }
  }

  /**
   * Load schedule and metadata from localStorage
   */
  function loadScheduleFromStorage() {
    try {
      const dataStr = localStorage.getItem(STORAGE_DATA_KEY);
      const metaStr = localStorage.getItem(STORAGE_META_KEY);
      if (!dataStr) return null;
      return {
        records: JSON.parse(dataStr),
        meta: metaStr ? JSON.parse(metaStr) : null
      };
    } catch (e) {
      console.warn('LocalStorage read error:', e);
      return null;
    }
  }

  /**
   * Clear schedule from storage
   */
  function clearScheduleStorage() {
    try {
      localStorage.removeItem(STORAGE_DATA_KEY);
      localStorage.removeItem(STORAGE_META_KEY);
    } catch (e) {
      console.warn('LocalStorage clear error:', e);
    }
  }

  // Export as namespace
  const AMISExamEngine = {
    STORAGE_DATA_KEY,
    STORAGE_META_KEY,
    PRIORITY_SHEET_NAMES,
    REQUIRED_CURRICULUM,
    normalizeCol,
    classifyColumn,
    findHeaderRowAndMapping,
    autoDetectWorksheet,
    parseExcelDate,
    parseTimeRange,
    parseGradeAndSection,
    extractGender,
    parseWorksheet,
    validateAndDetectConflicts,
    normalizeSubjectKey,
    checkCurriculumCompleteness,
    saveScheduleToStorage,
    loadScheduleFromStorage,
    clearScheduleStorage
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = AMISExamEngine;
  } else {
    global.AMISExamEngine = AMISExamEngine;
  }
})(typeof window !== 'undefined' ? window : this);

