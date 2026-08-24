'use strict';

const crypto = require('crypto');
const supabase = require('./supabase');

const LOCK_TYPE = 'Schedule Lock';

function clean(value, maxLength = 200) {
  return String(value == null ? '' : value).trim().slice(0, maxLength);
}

function key(value) {
  return clean(value).toLowerCase();
}

function isLockRecord(record) {
  return key(record && record.schedule_type) === key(LOCK_TYPE);
}

function lockMatches(lock, section, sectionId) {
  const wantedId = key(sectionId);
  const lockId = key(lock && lock.section_id);
  if (wantedId && lockId && wantedId === lockId) return true;
  return Boolean(key(section) && key(lock && lock.section) === key(section));
}

function lockId(section, sectionId) {
  const identity = key(sectionId || section);
  return `schedule-lock:${crypto.createHash('sha256').update(identity).digest('hex').slice(0, 48)}`;
}

function normalizeLock(row) {
  return {
    id: clean(row && row.id, 100),
    grade_level: clean(row && row.grade_level, 100),
    section: clean(row && row.section),
    section_id: clean(row && row.section_id, 100),
    locked_at: clean(row && row.created_at, 80)
  };
}

async function listLocks(config, accessToken) {
  const result = await supabase.restRequest(config, `/manual_schedules?select=id,grade_level,section,section_id,created_at&schedule_type=eq.${encodeURIComponent(LOCK_TYPE)}&order=created_at.desc`, {
    method: 'GET',
    accessToken
  });
  if (!result.ok) return result;
  return { ...result, data: (Array.isArray(result.data) ? result.data : []).map(normalizeLock) };
}

async function findLock(config, accessToken, section, sectionId) {
  const result = await listLocks(config, accessToken);
  if (!result.ok) return result;
  return { ...result, data: result.data.find((lock) => lockMatches(lock, section, sectionId)) || null };
}

async function setLock(config, accessToken, input, locked) {
  const section = clean(input && input.section);
  const sectionId = clean(input && input.section_id, 100);
  const gradeLevel = clean(input && input.grade_level, 100);
  if (!section) return { ok: false, status: 400, data: { message: 'Select a class section first.' } };

  const existing = await findLock(config, accessToken, section, sectionId);
  if (!existing.ok) return existing;
  if (locked && existing.data) return { ok: true, status: 200, data: existing.data };

  if (!locked) {
    if (!existing.data) return { ok: true, status: 200, data: null };
    const result = await supabase.restRequest(config, `/manual_schedules?id=eq.${encodeURIComponent(existing.data.id)}`, {
      method: 'DELETE',
      accessToken,
      headers: { Prefer: 'return=representation' }
    });
    return result.ok ? { ok: true, status: 200, data: null } : result;
  }

  const record = {
    id: lockId(section, sectionId),
    teacher: 'AMIS Schedule Administrator',
    teacher_id: '',
    subject: 'Locked after schedule review',
    grade_level: gradeLevel || 'Class Schedule',
    section,
    section_id: sectionId,
    day: 'Sunday',
    start_time: '00:00',
    end_time: '00:01',
    room: '',
    schedule_type: LOCK_TYPE,
    status: 'inactive',
    source: 'manual',
    merge_group: ''
  };
  const result = await supabase.restRequest(config, '/manual_schedules?on_conflict=id&select=*', {
    method: 'POST',
    accessToken,
    headers: { 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=representation' },
    body: JSON.stringify(record)
  });
  if (!result.ok) return result;
  const saved = Array.isArray(result.data) ? result.data[0] : result.data;
  return { ok: true, status: 200, data: normalizeLock(saved || record) };
}

module.exports = {
  LOCK_TYPE,
  isLockRecord,
  lockMatches,
  listLocks,
  findLock,
  setLock
};
