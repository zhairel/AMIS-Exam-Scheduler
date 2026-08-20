(function (global) {
  'use strict';

  const DB_NAME = 'AMIS_CLASS_SCHEDULE_DB';
  const DB_VERSION = 1;
  const STORE_NAME = 'manual_schedules';
  const SCHOOL_DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];

  class ScheduleConflictError extends Error {
    constructor(conflicts) {
      super('The selected schedule conflicts with an active schedule.');
      this.name = 'ScheduleConflictError';
      this.conflicts = conflicts;
    }
  }

  function requestResult(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('Database request failed.'));
    });
  }

  function transactionDone(transaction) {
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error || new Error('Database transaction failed.'));
      transaction.onabort = () => reject(transaction.error || new Error('Database transaction was aborted.'));
    });
  }

  function openDatabase() {
    if (!('indexedDB' in global)) {
      return Promise.reject(new Error('This browser does not support the schedule database (IndexedDB).'));
    }

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        const store = db.objectStoreNames.contains(STORE_NAME)
          ? request.transaction.objectStore(STORE_NAME)
          : db.createObjectStore(STORE_NAME, { keyPath: 'id' });

        const indexes = ['teacher', 'grade_level', 'section', 'subject', 'day', 'status'];
        indexes.forEach((name) => {
          if (!store.indexNames.contains(name)) store.createIndex(name, name, { unique: false });
        });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('Unable to open the schedule database.'));
      request.onblocked = () => reject(new Error('Close other AMIS schedule tabs, then try again.'));
    });
  }

  function clean(value) {
    return String(value == null ? '' : value).trim();
  }

  function key(value) {
    return clean(value).toLocaleLowerCase();
  }

  function normalizeStatus(value) {
    return key(value) === 'inactive' ? 'inactive' : 'active';
  }

  function normalizeRecord(input) {
    const now = new Date().toISOString();
    return {
      id: clean(input.id) || (global.crypto && crypto.randomUUID ? crypto.randomUUID() : `manual_${Date.now()}_${Math.random().toString(16).slice(2)}`),
      teacher: clean(input.teacher),
      teacher_id: clean(input.teacher_id),
      subject: clean(input.subject),
      grade_level: clean(input.grade_level),
      section: clean(input.section),
      section_id: clean(input.section_id),
      day: clean(input.day),
      start_time: clean(input.start_time),
      end_time: clean(input.end_time),
      room: clean(input.room),
      schedule_type: clean(input.schedule_type) || 'Academic Class',
      status: normalizeStatus(input.status),
      source: 'manual',
      created_at: clean(input.created_at) || now,
      updated_at: now
    };
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

  function parseTimeRange(value) {
    const parts = clean(value).split(/\s*(?:–|—|-)\s*/);
    if (parts.length !== 2) return null;
    const startMeridiem = (parts[0].toUpperCase().match(/\b(AM|PM)\b/) || [])[1];
    const endMeridiem = (parts[1].toUpperCase().match(/\b(AM|PM)\b/) || [])[1];
    let start = parseClock(parts[0], endMeridiem);
    let end = parseClock(parts[1], startMeridiem);
    if (start == null || end == null) return null;

    // School periods such as "12:40 – 1:25 PM" inherit PM on both sides.
    // If an inherited meridiem still creates an impossible reversal, use the
    // closest same-day interpretation.
    if (end <= start && !endMeridiem && startMeridiem) end += 12 * 60;
    if (end <= start && !startMeridiem && endMeridiem && start >= 12 * 60) start -= 12 * 60;
    if (end <= start) return null;
    return { start, end };
  }

  function recordRange(record) {
    const start = parseClock(record.start_time);
    const end = parseClock(record.end_time);
    if (start == null || end == null || end <= start) return null;
    return { start, end };
  }

  function formatInputTime(totalMinutes) {
    const safe = Math.max(0, Math.min(23 * 60 + 59, totalMinutes));
    return `${String(Math.floor(safe / 60)).padStart(2, '0')}:${String(safe % 60).padStart(2, '0')}`;
  }

  function formatDisplayTime(value) {
    const minutes = parseClock(value);
    if (minutes == null) return clean(value);
    const hour24 = Math.floor(minutes / 60);
    const minute = minutes % 60;
    const meridiem = hour24 >= 12 ? 'PM' : 'AM';
    const hour = hour24 % 12 || 12;
    return `${hour}:${String(minute).padStart(2, '0')} ${meridiem}`;
  }

  function formatRange(record) {
    return `${formatDisplayTime(record.start_time)} – ${formatDisplayTime(record.end_time)}`;
  }

  function gradeFromSection(sectionName, fallback) {
    const match = clean(sectionName).match(/\b(KINDER\s*[12]?|GRADE\s*\d{1,2})\b/i);
    if (!match) return clean(fallback);
    return match[1].replace(/\s+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function officialEntriesFromSections(sections) {
    const entries = [];
    (Array.isArray(sections) ? sections : []).forEach((section) => {
      const rows = section.periods || section.rows || [];
      rows.forEach((row) => {
        const range = parseTimeRange(row.time);
        if (!range) return;
        SCHOOL_DAYS.forEach((day) => {
          let cell = row.days ? row.days[day] : null;
          if (row.is_merged_all_days && !cell && (row.subject || row.label)) cell = row;
          if (!cell || !(cell.subject || cell.label || row.subject || row.label)) return;
          const isBreak = Boolean(cell.is_break || row.is_break);
          entries.push({
            id: `official:${section.id || section.section_id || section.section_name}:${row.period_num || row.time}:${day}`,
            teacher: isBreak ? '' : clean(cell.teacher || row.teacher),
            teacher_id: isBreak ? '' : clean(cell.teacher_id || row.teacher_id),
            subject: clean(cell.subject || cell.label || row.subject || row.label),
            grade_level: clean(section.grade_level),
            section: clean(section.section_name),
            section_id: clean(section.id || section.section_id),
            day,
            start_time: formatInputTime(range.start),
            end_time: formatInputTime(range.end),
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

  function overlap(a, b) {
    const aRange = recordRange(a);
    const bRange = recordRange(b);
    return Boolean(aRange && bRange && aRange.start < bRange.end && bRange.start < aRange.end);
  }

  function findConflicts(candidateInput, entries, excludeId) {
    const candidate = normalizeRecord(candidateInput);
    if (candidate.status !== 'active') return [];
    const ignoredId = clean(excludeId || candidate.id);
    const conflicts = [];

    (entries || []).forEach((entry) => {
      if (!entry || normalizeStatus(entry.status) !== 'active') return;
      if (clean(entry.id) === ignoredId) return;
      if (key(entry.day) !== key(candidate.day) || !overlap(candidate, entry)) return;

      const reasons = [];
      const sameTeacher = (candidate.teacher_id && entry.teacher_id && key(candidate.teacher_id) === key(entry.teacher_id))
        || (candidate.teacher && entry.teacher && key(candidate.teacher) === key(entry.teacher));
      const sameSection = (candidate.section_id && entry.section_id && key(candidate.section_id) === key(entry.section_id))
        || (candidate.section && entry.section && key(candidate.section) === key(entry.section));
      const sameRoom = candidate.room && entry.room && key(candidate.room) === key(entry.room);
      if (sameTeacher) reasons.push('teacher');
      if (sameSection) reasons.push('section');
      if (sameRoom) reasons.push('room');
      if (reasons.length) conflicts.push({ entry, reasons });
    });
    return conflicts;
  }

  function findTeacherConflicts(candidate, entries, excludeId) {
    return findConflicts(candidate, entries, excludeId).filter((conflict) => conflict.reasons.includes('teacher'));
  }

  function findSuggestion(candidateInput, entries, excludeId) {
    const candidate = normalizeRecord(candidateInput);
    const range = recordRange(candidate);
    if (!range || candidate.status !== 'active') return null;
    const duration = range.end - range.start;
    const dayOrder = [candidate.day].concat(SCHOOL_DAYS.filter((day) => day !== candidate.day));
    const increments = [];
    for (let offset = 15; offset <= 12 * 60; offset += 15) {
      increments.push(offset, -offset);
    }

    for (const day of dayOrder) {
      const bases = day === candidate.day ? increments : [0].concat(increments);
      for (const offset of bases) {
        const start = range.start + offset;
        const end = start + duration;
        if (start < 7 * 60 + 30 || end > 19 * 60) continue;
        const suggested = { ...candidate, day, start_time: formatInputTime(start), end_time: formatInputTime(end) };
        if (findConflicts(suggested, entries, excludeId).length === 0) return suggested;
      }
    }
    return null;
  }

  async function listSchedules() {
    const db = await openDatabase();
    try {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const records = await requestResult(transaction.objectStore(STORE_NAME).getAll());
      await transactionDone(transaction);
      return records.sort((a, b) => `${a.day}|${a.start_time}|${a.teacher}`.localeCompare(`${b.day}|${b.start_time}|${b.teacher}`));
    } finally {
      db.close();
    }
  }

  async function getSchedule(id) {
    const db = await openDatabase();
    try {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const record = await requestResult(transaction.objectStore(STORE_NAME).get(clean(id)));
      await transactionDone(transaction);
      return record || null;
    } finally {
      db.close();
    }
  }

  async function saveScheduleChecked(input, officialEntries) {
    const record = normalizeRecord(input);
    if (!record.teacher || !record.subject || !record.grade_level || !record.section || !record.day) {
      throw new Error('Complete all required schedule fields.');
    }
    if (!SCHOOL_DAYS.includes(record.day)) throw new Error('Select a valid school day.');
    if (!recordRange(record)) throw new Error('End time must be later than start time.');

    const db = await openDatabase();
    try {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const existing = await requestResult(store.getAll());
      const current = existing.find((item) => item.id === record.id);
      if (current) record.created_at = current.created_at;
      const conflicts = findConflicts(record, (officialEntries || []).concat(existing), record.id);
      if (conflicts.length) {
        transaction.abort();
        try { await transactionDone(transaction); } catch (_) {}
        throw new ScheduleConflictError(conflicts);
      }
      store.put(record);
      await transactionDone(transaction);
      return record;
    } finally {
      db.close();
    }
  }

  async function deleteSchedule(id) {
    const db = await openDatabase();
    try {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      transaction.objectStore(STORE_NAME).delete(clean(id));
      await transactionDone(transaction);
    } finally {
      db.close();
    }
  }

  async function loadOfficialData(basePath) {
    const prefix = clean(basePath || '.').replace(/\/$/, '');
    const response = await fetch(`${prefix}/class_schedules_data.json?v=${Date.now()}`, { cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to load the official class schedule data.');
    return response.json();
  }

  global.AMISScheduleCore = Object.freeze({
    SCHOOL_DAYS,
    ScheduleConflictError,
    clean,
    key,
    normalizeRecord,
    parseClock,
    parseTimeRange,
    recordRange,
    formatInputTime,
    formatDisplayTime,
    formatRange,
    gradeFromSection,
    officialEntriesFromSections,
    findConflicts,
    findTeacherConflicts,
    findSuggestion,
    listSchedules,
    getSchedule,
    saveScheduleChecked,
    deleteSchedule,
    loadOfficialData
  });
})(window);
