const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const browserWindow = {};
const context = {
  window: browserWindow,
  crypto: { randomUUID: () => 'test-id' },
  fetch: async () => { throw new Error('Network access is not used by these tests.'); },
};
browserWindow.crypto = context.crypto;
vm.createContext(context);
vm.runInContext(fs.readFileSync('class-schedule/schedule-core.js', 'utf8'), context);

const core = browserWindow.AMISScheduleCore;

function record(overrides = {}) {
  return {
    id: overrides.id || 'candidate',
    teacher: 'Teacher A',
    teacher_id: 'teacher-a',
    subject: 'Math',
    grade_level: 'Grade 1',
    section: 'GRADE 1 (FACE TO FACE)',
    section_id: 'grade-1',
    day: 'Wednesday',
    start_time: '10:00',
    end_time: '11:00',
    room: 'Room 1',
    schedule_type: 'Academic Class',
    status: 'active',
    ...overrides,
  };
}

{
  const blocker = record({ id: 'blocker', day: 'Sunday', start_time: '07:30', end_time: '08:30' });
  const suggestion = core.findSuggestion(record(), [blocker]);
  assert.strictEqual(suggestion.day, 'Sunday');
  assert.strictEqual(suggestion.start_time, '08:30');
  assert.strictEqual(suggestion.end_time, '09:30');
}

{
  const suggestion = core.findSuggestion(record({
    section: 'GRADE 7 - TEST (1ST SHIFT)',
    start_time: '15:00',
    end_time: '16:00',
  }), []);
  assert.strictEqual(suggestion.day, 'Sunday');
  assert.strictEqual(suggestion.start_time, '12:30');
}

{
  const suggestion = core.findSuggestion(record({
    section: 'GRADE 9 - TEST (2ND SHIFT)',
    start_time: '17:30',
    end_time: '18:30',
  }), []);
  assert.strictEqual(suggestion.day, 'Sunday');
  assert.strictEqual(suggestion.start_time, '15:30');
}

{
  const teacherBlock = record({ id: 'teacher-block', day: 'Sunday', start_time: '07:30', end_time: '08:30', section_id: 'other-section', room: 'Other Room' });
  const sectionBlock = record({ id: 'section-block', day: 'Sunday', start_time: '08:30', end_time: '09:30', teacher_id: 'other-teacher', teacher: 'Teacher B', room: 'Other Room' });
  const roomBlock = record({ id: 'room-block', day: 'Sunday', start_time: '09:30', end_time: '10:30', teacher_id: 'third-teacher', teacher: 'Teacher C', section_id: 'third-section' });
  const suggestion = core.findSuggestion(record(), [teacherBlock, sectionBlock, roomBlock]);
  assert.strictEqual(suggestion.start_time, '10:30');
}

console.log('PASS chronological class suggestions and F2F/ODL conflict constraints');
