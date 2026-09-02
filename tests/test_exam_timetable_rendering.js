const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('exam-schedule.html', 'utf8');
const facultyHtml = fs.readFileSync('faculty-timetable-exam.html', 'utf8');
const records = require('../exam_data.json');

assert(facultyHtml.includes('faculty-document-heading'));
assert(facultyHtml.includes('TERM EXAM WEEK 2026 – 2027'));
assert(facultyHtml.includes('FACULTY EXAMINATION TIMETABLE'));
assert(facultyHtml.includes('المدرسة المنورة الإسلامية'));
assert(facultyHtml.includes('<h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>'));
assert.strictEqual((html.match(/<h1>AL MUNAWWARA ISLAMIC SCHOOL<\/h1>/g) || []).length, 2);
assert.strictEqual((html.match(/school-header school-header--branded/g) || []).length, 2);
assert(html.includes('document-header-title'));
assert(html.includes('document-header-arabic'));
assert(html.includes('المدرسة المنورة الإسلامية'));
assert(/\.teacher-meta-tag\s*\{\s*display:\s*none;/.test(html));
assert(/\.teacher-meta-tag\s*\{\s*display:\s*none;/.test(facultyHtml));
assert(!html.includes('<span class="teacher-meta-tag">'));
assert(!facultyHtml.includes('<span class="teacher-meta-tag">'));

const helperStart = html.indexOf('  function scheduleStartLabel');
const helperEnd = html.indexOf('  function getExamGenderChip', helperStart);
assert(helperStart >= 0 && helperEnd > helperStart, 'Schedule-row matching helpers are missing.');

const context = {};
vm.createContext(context);
vm.runInContext(`${html.slice(helperStart, helperEnd)}\nthis.matchesRow = examStartsAtScheduleRow;`, context);

function rowTimesFor(record) {
  if (record.shift === 'F2F') {
    return ['08:00 AM – 09:00 AM', '09:00 AM – 10:00 AM', '10:25 AM – 11:25 AM'];
  }
  if (record.shift === 'ODL - 1ST SHIFT') {
    return [
      '12:40 PM – 01:40 PM',
      '01:50 PM – 02:50 PM',
      '03:10 PM – 04:10 PM',
    ];
  }
  return [
    '03:10 PM – 04:10 PM',
    '04:20 PM – 05:20 PM',
    '05:30 PM – 06:30 PM',
  ];
}

const seniorHighRecords = records.filter(record => ['Grade 11', 'Grade 12'].includes(record.grade_level));
for (const record of seniorHighRecords) {
  const matchingRows = rowTimesFor(record).filter((rowTime, index) =>
    context.matchesRow(record, rowTime, index + 1)
  );
  assert.strictEqual(matchingRows.length, 1, `${record.id} must render in exactly one starting row.`);
  assert.strictEqual(
    matchingRows[0].split('–')[0].trim(),
    record.time_slot.split('–')[0].trim(),
    `${record.id} must render at its authoritative start time.`
  );
}

const subjectCounts = new Map();
for (const record of seniorHighRecords) {
  const key = `${record.section_id}|${record.subject_id}`;
  subjectCounts.set(key, (subjectCounts.get(key) || 0) + 1);
}
assert.strictEqual(
  [...subjectCounts.values()].filter(count => count > 1).length,
  0,
  'Grade 11/12 source data must not contain duplicate section-subject exams.'
);

const abuMusa = seniorHighRecords.filter(record => record.section === 'GRADE 12 - ABU MUSA AL-ASHARI');
assert.strictEqual(abuMusa.length, 9);
assert(abuMusa.every(record => record.start_m >= 760), 'Abu Musa exams must start at 12:40 PM or later.');

const normylahExams = records.filter(record => record.subject_teacher === 'Teacher Normylah');
assert(normylahExams.length > 0, 'Normylah reference assignments must remain in the official data.');
assert(
  normylahExams.every(record => record.proctor_id && record.proctor_status === 'ACTIVE_ASSIGNED'),
  'Every Normylah exam must retain active proctor coverage.'
);
assert(records.filter(record => /^fil(?:ipino|\d*)$/i.test(record.subject)).every(record => record.subject === 'Filipino'));
assert(!/"subject": "Fil\d*"/.test(html), 'Faculty roster must display Filipino instead of legacy Fil labels.');
const mergedIdentityRecords = records.filter(record => ['tchr_franchette','tchr_zara'].includes(record.teacher_id));
assert(mergedIdentityRecords.every(record => record.subject_teacher === 'Teacher Franchette Zarah M. Ranain'));
assert(!records.some(record => record.proctor_id === 'tchr_zara'), 'The duplicate Zara identity must never remain an active proctor ID.');
const mergedAlimRecords = records.filter(record => ['tchr_dipatuan', 'tchr_abdulwahab'].includes(record.teacher_id));
assert.strictEqual(mergedAlimRecords.length, 14, 'Dipatuan must own the combined 14-exam load.');
assert(mergedAlimRecords.every(record => record.subject_teacher === 'Alim Dipatuan'));
assert(!records.some(record => record.proctor_id === 'tchr_abdulwahab'), 'The duplicate Abdulwahab identity must never remain an active proctor ID.');
assert(html.includes("new Set(['tchr_zara', 'tchr_abdulwahab'])"), 'Both duplicate faculty identities must be hidden from the roster.');
assert(
  !records.some(record =>
    record.department === 'Elementary' &&
    (record.teacher_id === 'tchr_mamonas' || record.proctor_id === 'tchr_mamonas')
  ),
  'Alim Mamonas must not own or proctor Kinder or Elementary exams.'
);
const franchetteKhaleedMapeh = records.find(record =>
  record.id === 'exam_597' && record.subject_teacher_id === 'tchr_franchette'
);
const franchetteAmmarMakabansa = records.find(record => record.id === 'exam_173');
assert.deepStrictEqual(
  [franchetteKhaleedMapeh.day_number, franchetteKhaleedMapeh.start_m, franchetteKhaleedMapeh.end_m],
  [1, 910, 970],
  'Franchette Grade 6 Khaleed MAPEH must stay on Wednesday at 3:10 PM.'
);
assert.strictEqual(
  franchetteKhaleedMapeh.proctor_id,
  'tchr_ethel',
  'Grade 6 Khaleed MAPEH must be proctored by Teacher Ethel to cover Teacher Franchette Grade 3 Makabansa.'
);
assert.deepStrictEqual(
  [franchetteAmmarMakabansa.day_number, franchetteAmmarMakabansa.start_m, franchetteAmmarMakabansa.end_m],
  [1, 910, 970],
  'Franchette Grade 3 Ammar Makabansa must stay on Wednesday at 3:10 PM.'
);
for (const sectionId of [
  'sec_grade_5_ayyash_ibn_abi_rabi_ah_1st_shift',
  'sec_grade_5_ja_far_ibn_abi_talib_2nd_shift_mix',
]) {
  const mapeh = records.find(record => record.section_id === sectionId && record.subject === 'MAPEH');
  assert(mapeh, `${sectionId} must include its confirmed MAPEH exam.`);
  assert.strictEqual(mapeh.subject_teacher_id, 'tchr_saimonah');
}
assert(html.includes("match.proctor_assignment_source !== 'SUBJECT_TEACHER'"));
const sectionRenderer = html.slice(
  html.indexOf('// TAB 1: SECTION EXAM SCHEDULES'),
  html.indexOf('// TAB 2: FACULTY EXAM TIMETABLES')
);
assert(!sectionRenderer.includes('match.proctor'), 'Section schedules must not display proctor details.');
assert(!sectionRenderer.includes('Active proctor:'), 'Section schedules must not display active-proctor text.');
assert(html.includes('cell-proctor-duty-label'));
assert(html.includes("<span class=\"cell-section-name\">${esc(cleanSectionName(match.section_name))}</span>"));
assert(!html.includes('Gender not specified'));
assert(!facultyHtml.includes('Gender not specified'));
assert(facultyHtml.includes("exam.proctor_assignment_source !== 'SUBJECT_TEACHER'"));
assert(html.includes('match.display_as_proctor_duty === true'));
assert(facultyHtml.includes('exam.display_as_proctor_duty === true'));
assert(facultyHtml.includes('cell-proctor-label'));
assert(facultyHtml.includes("<span class=\"cell-section-name\">${esc(cleanSec)}</span>"));
for (const shiftColumnToken of ['col-shift', 'cell-shift', 'shift-stack']) {
  assert(html.includes(shiftColumnToken), `Main faculty timetable must include ${shiftColumnToken}.`);
  assert(facultyHtml.includes(shiftColumnToken), `Standalone faculty timetable must include ${shiftColumnToken}.`);
}
assert(html.includes("f2f: 'F<br>A<br>C<br>E<br><br>T<br>O<br><br>F<br>A<br>C<br>E'"));
assert(html.includes("first: '1<br>S<br>T<br><br>S<br>H<br>I<br>F<br>T'"));
assert(html.includes("second: '2<br>N<br>D<br><br>S<br>H<br>I<br>F<br>T'"));
assert(!html.includes('shift-time-shared'));
assert(!facultyHtml.includes('shift-time-shared'));
assert(facultyHtml.includes('return { ...row, shift_group: shiftGroup };'));
assert(!/\b\d+(?:\/\d+)? min\./i.test(html), 'Main timetable must not display lowercase min. labels.');
assert(!/\b\d+(?:\/\d+)? min\./i.test(facultyHtml), 'Faculty timetable must not display lowercase min. labels.');
assert(html.includes('60 MIN'));
assert(facultyHtml.includes('60 MIN'));
assert(html.includes('${match.duration_minutes || 60} MIN'));
assert(facultyHtml.includes('${exam.duration_minutes || 60} MIN'));

const abdulKarimProctorChipIds = new Set(['exam_13', 'exam_24', 'exam_160', 'exam_208', 'exam_309', 'exam_315']);
const abdulKarimProctorChipRecords = records.filter(record => record.display_as_proctor_duty === true);
assert.strictEqual(abdulKarimProctorChipRecords.length, 6);
assert.deepStrictEqual(new Set(abdulKarimProctorChipRecords.map(record => record.id)), abdulKarimProctorChipIds);
assert(abdulKarimProctorChipRecords.every(record => record.proctor_id === 'tchr_abdul_karim'));
assert(abdulKarimProctorChipRecords.every(record => record.proctor === 'Alim Abdul Karim'));
assert(abdulKarimProctorChipRecords.every(record => [1, 2].includes(record.day_number)));

const conflictHelperStart = html.indexOf('  function activeScheduleProctorId');
const conflictHelperEnd = html.indexOf('  function updateAntiConflictBadge', conflictHelperStart);
assert(conflictHelperStart >= 0 && conflictHelperEnd > conflictHelperStart, 'Strict conflict helpers are missing.');
const conflictContext = {
  EXAM_RECORDS: [
    {
      id: 'covered-exam', day_number: 4, start_m: 1050, end_m: 1110,
      grade_level: 'Grade 6', modality: 'ODL', section_id: 'grade-6', gender: '',
      teacher_id: 'inactive-teacher', proctor_id: 'shared-teacher',
      proctor_status: 'ACTIVE_ASSIGNED', proctor_pool: 'MANUAL_ADMIN_OVERRIDE',
    },
    {
      id: 'explicitly-unproctored-exam', day_number: 4, start_m: 1050, end_m: 1110,
      grade_level: 'Grade 9', modality: 'ODL', section_id: 'grade-9', gender: 'MALE',
      teacher_id: 'shared-teacher', proctor_id: '',
      proctor_status: 'NOT_ASSIGNED', proctor_pool: 'NONE',
    },
  ],
};
vm.createContext(conflictContext);
vm.runInContext(
  `${html.slice(conflictHelperStart, conflictHelperEnd)}\nthis.strictScheduleConflicts = strictScheduleConflicts;`,
  conflictContext
);
assert.strictEqual(
  conflictContext.strictScheduleConflicts().length,
  0,
  'An explicitly unproctored exam must not fall back to its subject teacher in conflict checks.'
);

assert(html.includes('@media (max-width: 720px)'), 'Exam schedule must include a phone layout breakpoint.');
assert(html.includes('Swipe left or right to view all exam days'), 'Mobile timetables must explain horizontal swiping.');
assert(html.includes('-webkit-overflow-scrolling: touch'), 'Timetable scrolling must be touch optimized.');
assert(/\.table-responsive-wrapper\s*\{[\s\S]*?overflow-x:\s*scroll;/.test(html), 'Phone timetable wrapper must scroll horizontally.');
assert(/\.timetable-grid\s*\{\s*width:\s*820px;\s*min-width:\s*820px;\s*\}/.test(html), 'Phone timetable columns must retain readable widths.');

console.log('PASS Grade 11/12 canonical rendering and PROCTOR-only faculty timetable cell labels');
