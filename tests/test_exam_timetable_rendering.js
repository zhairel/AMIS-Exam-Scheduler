const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('exam-schedule.html', 'utf8');
const facultyHtml = fs.readFileSync('faculty-timetable-exam.html', 'utf8');
const records = require('../exam_data.json');

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

const proctorCoverage = records.filter(record => record.replacement_teacher_required && record.proctor_id);
assert.strictEqual(proctorCoverage.length, 12, 'All 12 Normylah exams must have active proctor coverage.');
assert(records.filter(record => /^fil(?:ipino|\d*)$/i.test(record.subject)).every(record => record.subject === 'Filipino'));
assert(!/"subject": "Fil\d*"/.test(html), 'Faculty roster must display Filipino instead of legacy Fil labels.');
const mergedIdentityRecords = records.filter(record => ['tchr_franchette','tchr_zara'].includes(record.teacher_id));
assert(mergedIdentityRecords.every(record => record.subject_teacher === 'Teacher Franchette Zarah M. Ranain'));
assert(!records.some(record => record.proctor_id === 'tchr_zara'), 'The duplicate Zara identity must never remain an active proctor ID.');
assert(html.includes("match.proctor_assignment_source !== 'SUBJECT_TEACHER'"));
assert(html.includes('<span class="cell-proctor-duty-label">PROCTOR</span>'));
assert(html.includes("<span class=\"cell-section-name\">${esc(cleanSectionName(match.section_name))}</span>"));
assert(!html.includes('Gender not specified'));
assert(!facultyHtml.includes('Gender not specified'));
assert(facultyHtml.includes("exam.proctor_assignment_source !== 'SUBJECT_TEACHER'"));
assert(facultyHtml.includes('<span class="cell-proctor-label">PROCTOR</span>'));
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

console.log('PASS Grade 11/12 canonical rendering and PROCTOR-only faculty timetable cell labels');
