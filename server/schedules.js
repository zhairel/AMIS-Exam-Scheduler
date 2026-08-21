'use strict';

const DAYS = new Set(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']);
const STATUSES = new Set(['active', 'inactive']);
const SCHOOL_DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];
const officialSections = require('../class_schedules_data.json');
const ALLOWED_FIELDS = [
  'id', 'teacher', 'teacher_id', 'subject', 'grade_level', 'section', 'section_id',
  'day', 'start_time', 'end_time', 'room', 'schedule_type', 'status'
];

function clean(value, maxLength = 200) {
  return String(value == null ? '' : value).trim().slice(0, maxLength);
}

function normalizeTime(value) {
  const match = clean(value, 8).match(/^(\d{2}):(\d{2})(?::\d{2})?$/);
  if (!match) return '';
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (hour > 23 || minute > 59) return '';
  return `${match[1]}:${match[2]}`;
}

function normalize(input, existingId) {
  const source = input && typeof input === 'object' ? input : {};
  const output = {};
  ALLOWED_FIELDS.forEach((field) => {
    if (Object.prototype.hasOwnProperty.call(source, field)) output[field] = clean(source[field]);
  });
  output.id = clean(existingId || output.id, 100);
  output.teacher = clean(output.teacher);
  output.teacher_id = clean(output.teacher_id, 100);
  output.subject = clean(output.subject);
  output.grade_level = clean(output.grade_level, 100);
  output.section = clean(output.section);
  output.section_id = clean(output.section_id, 100);
  output.day = clean(output.day, 20);
  output.start_time = normalizeTime(output.start_time);
  output.end_time = normalizeTime(output.end_time);
  output.room = clean(output.room, 100);
  output.schedule_type = clean(output.schedule_type || 'Academic Class', 100);
  output.status = clean(output.status || 'active', 20).toLowerCase();
  output.source = 'manual';
  return output;
}

function validate(record, requireId) {
  if (requireId && !record.id) return 'A schedule ID is required.';
  const teacherRequired = record.source !== 'official' || record.schedule_type !== 'Official Break / Assembly';
  if ((teacherRequired && !record.teacher) || !record.subject || !record.grade_level || !record.section) return 'Complete all required schedule fields.';
  if (!DAYS.has(record.day)) return 'Select a valid school day.';
  if (!record.start_time || !record.end_time || record.end_time <= record.start_time) return 'End time must be later than start time.';
  if (!STATUSES.has(record.status)) return 'Select a valid schedule status.';
  return '';
}

function normalizeRows(rows) {
  return (Array.isArray(rows) ? rows : []).map((row) => ({
    ...row,
    start_time: normalizeTime(row.start_time),
    end_time: normalizeTime(row.end_time),
    source: row.source === 'official' ? 'official' : 'manual'
  }));
}

function key(value) {
  return clean(value).toLowerCase();
}

function parseClock(value, fallbackMeridiem) {
  const text = clean(value).toUpperCase().replace(/\./g, '');
  const match = text.match(/^(\d{1,2}):(\d{2})(?:\s*(AM|PM))?$/);
  if (!match) return null;
  let hour = Number(match[1]);
  const minute = Number(match[2]);
  const meridiem = match[3] || fallbackMeridiem || '';
  if (minute > 59 || hour > 23) return null;
  if (meridiem) {
    if (hour < 1 || hour > 12) return null;
    if (hour === 12) hour = 0;
    if (meridiem === 'PM') hour += 12;
  }
  return hour * 60 + minute;
}

function parseRange(value) {
  const parts = clean(value).split(/\s*(?:–|—|-)\s*/);
  if (parts.length !== 2) return null;
  const startMeridiem = (parts[0].toUpperCase().match(/\b(AM|PM)\b/) || [])[1];
  const endMeridiem = (parts[1].toUpperCase().match(/\b(AM|PM)\b/) || [])[1];
  let start = parseClock(parts[0], endMeridiem);
  let end = parseClock(parts[1], startMeridiem);
  if (start == null || end == null) return null;
  if (end <= start && !endMeridiem && startMeridiem) end += 12 * 60;
  if (end <= start && !startMeridiem && endMeridiem && start >= 12 * 60) start -= 12 * 60;
  return end > start ? { start, end } : null;
}

function inputRange(record) {
  const start = parseClock(record.start_time);
  const end = parseClock(record.end_time);
  return start != null && end != null && end > start ? { start, end } : null;
}

function inputTime(totalMinutes) {
  return `${String(Math.floor(totalMinutes / 60)).padStart(2, '0')}:${String(totalMinutes % 60).padStart(2, '0')}`;
}

function buildOfficialEntries() {
  const entries = [];
  officialSections.forEach((section) => {
    (section.periods || section.rows || []).forEach((row) => {
      const range = parseRange(row.time);
      if (!range) return;
      SCHOOL_DAYS.forEach((day) => {
        let cell = row.days ? row.days[day] : null;
        if (row.is_merged_all_days && !cell && (row.subject || row.label)) cell = row;
        if (!cell || !(cell.subject || cell.label || row.subject || row.label)) return;
        const isBreak = Boolean(cell.is_break || row.is_break);
        entries.push({
          id: `official:${section.id || section.section_id}:${row.period_num || row.time}:${day}`,
          teacher: isBreak ? '' : clean(cell.teacher || row.teacher),
          teacher_id: isBreak ? '' : clean(cell.teacher_id || row.teacher_id),
          subject: clean(cell.subject || cell.label || row.subject || row.label),
          grade_level: clean(section.grade_level),
          section: clean(section.section_name),
          section_id: clean(section.id || section.section_id),
          day,
          start_time: inputTime(range.start),
          end_time: inputTime(range.end),
          room: clean(cell.room || row.room),
          schedule_type: isBreak ? 'Official Break / Assembly' : 'Automatic / Official',
          status: 'active',
          source: 'official'
        });
      });
    });
  });
  return entries;
}

const OFFICIAL_ENTRIES = buildOfficialEntries();

function editableOfficialEntries() {
  return OFFICIAL_ENTRIES.filter((entry) => entry.teacher && entry.subject && entry.schedule_type !== 'Official Break / Assembly').map((entry) => ({ ...entry }));
}

function officialDatabaseEntries() {
  return OFFICIAL_ENTRIES.map((entry) => ({ ...entry }));
}

function findConflicts(candidate, manualRows, excludeId) {
  if (candidate.status !== 'active') return [];
  const candidateRange = inputRange(candidate);
  if (!candidateRange) return [];
  const ignored = clean(excludeId || candidate.id);
  const conflicts = [];
  const seen = new Set();
  OFFICIAL_ENTRIES.concat(normalizeRows(manualRows)).forEach((entry) => {
    if (!entry || entry.status !== 'active' || clean(entry.id) === ignored || key(entry.day) !== key(candidate.day)) return;
    const range = inputRange(entry);
    if (!range || candidateRange.start >= range.end || range.start >= candidateRange.end) return;
    const reasons = [];
    if ((candidate.teacher_id && entry.teacher_id && key(candidate.teacher_id) === key(entry.teacher_id)) || (candidate.teacher && entry.teacher && key(candidate.teacher) === key(entry.teacher))) reasons.push('teacher');
    if ((candidate.section_id && entry.section_id && key(candidate.section_id) === key(entry.section_id)) || (candidate.section && entry.section && key(candidate.section) === key(entry.section))) reasons.push('section');
    if (candidate.room && entry.room && key(candidate.room) === key(entry.room)) reasons.push('room');
    if (reasons.length) {
      const signature = `${clean(entry.id)}|${reasons.slice().sort().join(',')}`;
      if (!seen.has(signature)) {
        seen.add(signature);
        conflicts.push({ id: entry.id, source: entry.source, reasons });
      }
    }
  });
  return conflicts;
}

function sameOccupancy(left, right) {
  if (!left || !right) return false;
  return key(left.teacher_id || left.teacher) === key(right.teacher_id || right.teacher)
    && key(left.section_id || left.section) === key(right.section_id || right.section)
    && key(left.day) === key(right.day)
    && normalizeTime(left.start_time) === normalizeTime(right.start_time)
    && normalizeTime(left.end_time) === normalizeTime(right.end_time)
    && key(left.room) === key(right.room);
}

function conflictKey(conflict) {
  return `${clean(conflict.id)}|${(conflict.reasons || []).slice().sort().join(',')}`;
}

function findBlockingConflicts(candidate, manualRows, excludeId, current) {
  const conflicts = findConflicts(candidate, manualRows, excludeId);
  if (!sameOccupancy(candidate, current)) return conflicts;
  const grandfathered = new Set(findConflicts(current, manualRows, excludeId).map(conflictKey));
  return conflicts.filter((conflict) => !grandfathered.has(conflictKey(conflict)));
}

module.exports = {
  normalize,
  validate,
  normalizeRows,
  findConflicts,
  findBlockingConflicts,
  editableOfficialEntries,
  officialDatabaseEntries,
  officialEntryCount: OFFICIAL_ENTRIES.length
};
