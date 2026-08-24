const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('exam-schedule.html', 'utf8');
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

console.log('PASS Grade 11/12 exams render once at their authoritative time; Abu Musa starts at 12:40 PM');
