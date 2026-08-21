(function () {
  'use strict';

  const core = window.AMISScheduleCore;
  const guard = window.AMISAdminGuard;
  const PAGE_SIZE = 100;
  const DEFAULT_TIME_BANDS = [
    ['07:40', '08:25'], ['08:25', '09:10'], ['09:30', '10:15'],
    ['12:40', '13:25'], ['13:25', '14:10'], ['14:20', '15:00'],
    ['15:00', '15:40'], ['15:40', '16:20'], ['16:30', '17:10'], ['17:20', '18:00']
  ];
  const ICONS = {
    edit: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm17.71-10.04a1 1 0 0 0 0-1.42l-2.5-2.5a1 1 0 0 0-1.42 0l-1.96 1.96 3.75 3.75 2.13-1.79z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12zm3.46-8.88 1.41-1.41L12 9.84l1.13-1.13 1.41 1.41L13.41 11.25l1.13 1.13-1.41 1.41L12 12.66l-1.13 1.13-1.41-1.41 1.13-1.13-1.13-1.13zM15.5 4l-1-1h-5l-1 1H5v2h14V4z"/></svg>'
  };

  let records = [];
  let filteredRecords = [];
  let personnel = [];
  let selectedTeacher = '';
  let page = 1;

  const rows = document.getElementById('manageRows');
  const calendarRows = document.getElementById('teacherCalendarRows');
  const directoryList = document.getElementById('teacherDirectoryList');
  const directorySearch = document.getElementById('teacherDirectorySearch');
  const filters = {
    search: document.getElementById('manageSearch'),
    teacher: document.getElementById('manageTeacher'),
    grade_level: document.getElementById('manageGrade'),
    section: document.getElementById('manageSection'),
    subject: document.getElementById('manageSubject'),
    day: document.getElementById('manageDay'),
    status: document.getElementById('manageStatus'),
    source: document.getElementById('manageSource')
  };

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  }

  function isOfficial(record) {
    return record.source === 'official' || String(record.id || '').startsWith('official:');
  }

  function notice(message, error) {
    const element = document.getElementById('manageNotice');
    element.textContent = message || '';
    element.hidden = !message;
    element.classList.toggle('error', Boolean(error));
  }

  function unique(field) {
    return Array.from(new Set(records.map((record) => record[field]).filter(Boolean))).sort((a, b) => a.localeCompare(b));
  }

  function populateSelect(element, field) {
    const label = element.options[0].textContent;
    const selected = element.value;
    element.innerHTML = `<option value="">${esc(label)}</option>` + unique(field).map((value) => `<option value="${esc(value)}">${esc(value)}</option>`).join('');
    element.value = selected;
  }

  function updateStats() {
    document.getElementById('totalRecords').textContent = records.length.toLocaleString();
    document.getElementById('activeRecords').textContent = records.filter((record) => record.status === 'active').length.toLocaleString();
    document.getElementById('officialRecords').textContent = records.filter(isOfficial).length.toLocaleString();
    document.getElementById('manualRecords').textContent = records.filter((record) => !isOfficial(record)).length.toLocaleString();
  }

  function applyFilters() {
    const search = filters.search.value.trim().toLowerCase();
    filteredRecords = records.filter((record) => {
      if (['teacher', 'grade_level', 'section', 'subject', 'day', 'status', 'source'].some((field) => filters[field].value && record[field] !== filters[field].value)) return false;
      if (!search) return true;
      return [record.teacher, record.subject, record.grade_level, record.section, record.day, record.room, record.schedule_type, record.status, record.source].join(' ').toLowerCase().includes(search);
    });
    const pages = Math.max(1, Math.ceil(filteredRecords.length / PAGE_SIZE));
    page = Math.min(page, pages);
    renderRows();
  }

  function removeButton(record, className) {
    const official = isOfficial(record);
    if (official && record.status !== 'active') return '';
    const action = official ? 'Deactivate' : 'Delete';
    const deleteClass = className.includes('calendar') ? 'calendar-icon-delete' : 'manual-icon-delete';
    return `<button class="${className} ${deleteClass}" type="button" data-action="remove" data-id="${esc(record.id)}" title="${action} schedule" aria-label="${action} ${esc(record.subject)}">${ICONS.trash}</button>`;
  }

  function renderRows() {
    const start = (page - 1) * PAGE_SIZE;
    const visible = filteredRecords.slice(start, start + PAGE_SIZE);
    if (!visible.length) {
      rows.innerHTML = '<tr><td colspan="10" class="manual-empty">No schedules match the selected filters.</td></tr>';
    } else {
      rows.innerHTML = visible.map((record) => {
        const official = isOfficial(record);
        return `<tr>
          <td><strong>${esc(record.teacher)}</strong></td>
          <td>${esc(record.subject)}</td>
          <td><strong>${esc(record.grade_level)}</strong><br>${esc(record.section)}</td>
          <td>${esc(record.day)}</td>
          <td>${esc(core.formatRange(record))}</td>
          <td>${record.room ? esc(record.room) : '—'}</td>
          <td>${esc(record.schedule_type)}</td>
          <td><span class="status-pill manual-source-pill">${official ? 'OFFICIAL DB' : 'MANUAL'}</span></td>
          <td><span class="status-pill status-${esc(record.status)}">${esc(record.status.toUpperCase())}</span></td>
          <td><div class="manual-actions"><a class="manual-icon-action" href="/class-schedule-manage/edit?id=${encodeURIComponent(record.id)}" title="Edit schedule" aria-label="Edit ${esc(record.subject)}">${ICONS.edit}</a>${removeButton(record, 'manual-icon-action')}</div></td>
        </tr>`;
      }).join('');
    }
    const end = Math.min(start + PAGE_SIZE, filteredRecords.length);
    document.getElementById('pageSummary').textContent = filteredRecords.length ? `Showing ${start + 1}–${end} of ${filteredRecords.length.toLocaleString()} records` : '0 records';
    document.getElementById('previousPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = end >= filteredRecords.length;
  }

  function initials(name) {
    return String(name || '').split(/\s+/).filter(Boolean).slice(-2).map((part) => part[0]).join('').toUpperCase() || '—';
  }

  function buildPersonnel(teacherData) {
    const people = new Map();
    Object.values(teacherData || {}).forEach((teacher) => {
      const name = core.clean(teacher.canonical_name || teacher.teacher_name || teacher.name);
      if (!name) return;
      people.set(name, {
        name,
        id: core.clean(teacher.teacher_id || teacher.id),
        department: core.clean(teacher.department || 'Faculty / Staff')
      });
    });
    records.forEach((record) => {
      if (!record.teacher || people.has(record.teacher)) return;
      people.set(record.teacher, { name: record.teacher, id: record.teacher_id || '', department: 'Faculty / Staff' });
    });
    personnel = Array.from(people.values()).sort((left, right) => left.name.localeCompare(right.name));
    document.getElementById('teacherCount').textContent = personnel.length.toLocaleString();
  }

  function recordsForTeacher(name) {
    return records.filter((record) => record.teacher === name);
  }

  function subjectsForTeacher(name) {
    const counts = new Map();
    recordsForTeacher(name).forEach((record) => counts.set(record.subject, (counts.get(record.subject) || 0) + 1));
    return Array.from(counts.entries()).sort((left, right) => left[0].localeCompare(right[0]));
  }

  function renderDirectory() {
    const query = directorySearch.value.trim().toLowerCase();
    const visible = personnel.filter((person) => {
      const subjects = subjectsForTeacher(person.name).map(([subject]) => subject).join(' ');
      return !query || `${person.name} ${person.department} ${subjects}`.toLowerCase().includes(query);
    });
    if (!visible.length) {
      directoryList.innerHTML = '<div class="workspace-empty">No teacher or subject matches your search.</div>';
      return;
    }
    directoryList.innerHTML = visible.map((person) => {
      const assignments = recordsForTeacher(person.name);
      const subjects = Array.from(new Set(assignments.map((record) => record.subject))).slice(0, 2);
      const summary = subjects.length ? subjects.join(' • ') : 'No assigned subjects';
      return `<button class="teacher-directory-item${person.name === selectedTeacher ? ' selected' : ''}" type="button" data-teacher="${esc(person.name)}" aria-pressed="${person.name === selectedTeacher}">
        <span class="teacher-avatar">${esc(initials(person.name))}</span>
        <span class="teacher-directory-copy"><strong>${esc(person.name)}</strong><small>${esc(summary)}</small></span>
        <span class="teacher-record-count" title="${assignments.length} schedule records">${assignments.length}</span>
      </button>`;
    }).join('');
  }

  function createUrl(day, startTime, endTime) {
    const params = new URLSearchParams({ teacher: selectedTeacher, day, start_time: startTime, end_time: endTime, schedule_type: 'Academic Class', status: 'active' });
    return `/class-schedule-manage/create?${params.toString()}`;
  }

  function overlapsBand(record, day, startTime, endTime) {
    if (record.day !== day || record.status !== 'active') return false;
    const recordStart = core.parseClock(record.start_time);
    const recordEnd = core.parseClock(record.end_time);
    const bandStart = core.parseClock(startTime);
    const bandEnd = core.parseClock(endTime);
    return recordStart != null && recordEnd != null && bandStart != null && bandEnd != null && recordStart < bandEnd && bandStart < recordEnd;
  }

  function renderCalendarCard(record) {
    return `<article class="calendar-card${record.status === 'inactive' ? ' inactive' : ''}" title="${esc(`${record.subject} — ${record.grade_level} ${record.section}`)}">
      <strong>${esc(record.subject)}</strong>
      <span>${esc(record.grade_level)} • ${esc(record.section)}</span>
      <span>${record.status === 'inactive' ? 'INACTIVE' : (record.room ? `Room: ${esc(record.room)}` : 'ACTIVE')}</span>
      <div class="calendar-card-actions"><a class="calendar-icon-action" href="/class-schedule-manage/edit?id=${encodeURIComponent(record.id)}" title="Edit schedule" aria-label="Edit ${esc(record.subject)}">${ICONS.edit}</a>${removeButton(record, 'calendar-icon-action')}</div>
    </article>`;
  }

  function renderTeacherCalendar() {
    const person = personnel.find((item) => item.name === selectedTeacher);
    const teacherRecords = recordsForTeacher(selectedTeacher);
    const activeCount = teacherRecords.filter((record) => record.status === 'active').length;
    document.getElementById('teacherCalendarTitle').textContent = selectedTeacher || 'Teacher Weekly Calendar';
    document.getElementById('selectedTeacherMeta').textContent = person ? `${person.department} • ${activeCount} active • ${teacherRecords.length} total assignments` : 'Choose a teacher from the directory.';
    document.getElementById('teacherCreateLink').href = selectedTeacher ? `/class-schedule-manage/create?teacher=${encodeURIComponent(selectedTeacher)}` : '/class-schedule-manage/create';

    const subjects = subjectsForTeacher(selectedTeacher);
    document.getElementById('teacherSubjectList').innerHTML = subjects.length
      ? subjects.map(([subject, count]) => `<span class="subject-chip">${esc(subject)} <b>${count}</b></span>`).join('')
      : '<span class="subject-empty">No assigned subjects yet. Use an empty slot to add one.</span>';

    if (!selectedTeacher) {
      calendarRows.innerHTML = '<tr><td colspan="6" class="workspace-empty">Select a teacher to view the weekly calendar.</td></tr>';
      return;
    }

    let bands = Array.from(new Map(teacherRecords.map((record) => [`${record.start_time}|${record.end_time}`, [record.start_time, record.end_time]])).values());
    if (!bands.length) bands = DEFAULT_TIME_BANDS.slice();
    bands.sort((left, right) => `${left[0]}|${left[1]}`.localeCompare(`${right[0]}|${right[1]}`));
    calendarRows.innerHTML = bands.map(([startTime, endTime]) => {
      const rangeLabel = core.formatRange({ start_time: startTime, end_time: endTime });
      const dayCells = core.SCHOOL_DAYS.map((day) => {
        const assignments = teacherRecords.filter((record) => record.day === day && record.start_time === startTime && record.end_time === endTime);
        const hasOtherOverlap = !assignments.length && teacherRecords.some((record) => overlapsBand(record, day, startTime, endTime));
        const content = assignments.length
          ? assignments.map(renderCalendarCard).join('')
          : hasOtherOverlap
            ? '<div class="calendar-overlap-state"><span>Occupied</span><small>Overlapping time</small></div>'
            : `<a class="calendar-empty-link" href="${createUrl(day, startTime, endTime)}" aria-label="Add schedule for ${esc(selectedTeacher)} on ${day} at ${esc(rangeLabel)}"><strong>＋</strong><span>Available</span></a>`;
        return `<td class="calendar-cell">${content}</td>`;
      }).join('');
      return `<tr><td class="calendar-time">${esc(rangeLabel)}</td>${dayCells}</tr>`;
    }).join('');
  }

  function selectTeacher(name) {
    selectedTeacher = name;
    renderDirectory();
    renderTeacherCalendar();
  }

  async function loadRecords() {
    const [scheduleRecords, teacherResponse] = await Promise.all([
      core.listSchedules(),
      fetch('/teacher_weekly_schedules.json?v=' + Date.now(), { cache: 'no-store' }).catch(() => null)
    ]);
    records = scheduleRecords;
    let teacherData = {};
    if (teacherResponse && teacherResponse.ok) teacherData = await teacherResponse.json();
    populateSelect(filters.teacher, 'teacher');
    populateSelect(filters.grade_level, 'grade_level');
    populateSelect(filters.section, 'section');
    populateSelect(filters.subject, 'subject');
    buildPersonnel(teacherData);
    if (!selectedTeacher || !personnel.some((person) => person.name === selectedTeacher)) {
      selectedTeacher = (personnel.find((person) => recordsForTeacher(person.name).length) || personnel[0] || {}).name || '';
    }
    updateStats();
    renderDirectory();
    renderTeacherCalendar();
    applyFilters();
  }

  async function handleRemove(event) {
    const button = event.target.closest('[data-action="remove"]');
    if (!button) return;
    const record = records.find((item) => item.id === button.dataset.id);
    if (!record) return;
    const official = isOfficial(record);
    const confirmed = window.confirm(official ? 'Deactivate this official schedule? It can be reactivated through Edit.' : 'Are you sure you want to permanently delete this manual schedule?');
    if (!confirmed) return;
    button.disabled = true;
    try {
      await core.deleteSchedule(record.id);
      notice(official ? 'Official schedule deactivated.' : 'Manual schedule deleted.');
      await loadRecords();
    } catch (error) {
      notice(error.message || 'Unable to update this schedule.', true);
      button.disabled = false;
    }
  }

  document.addEventListener('click', handleRemove);
  directoryList.addEventListener('click', (event) => {
    const button = event.target.closest('[data-teacher]');
    if (button) selectTeacher(button.dataset.teacher);
  });
  directorySearch.addEventListener('input', renderDirectory);
  Object.entries(filters).forEach(([name, element]) => element.addEventListener(element === filters.search ? 'input' : 'change', () => {
    page = 1;
    if (name === 'teacher' && element.value) selectTeacher(element.value);
    applyFilters();
  }));
  document.getElementById('previousPage').addEventListener('click', () => { if (page > 1) { page -= 1; renderRows(); } });
  document.getElementById('nextPage').addEventListener('click', () => { if (page * PAGE_SIZE < filteredRecords.length) { page += 1; renderRows(); } });
  document.getElementById('manageLogout').addEventListener('click', async () => {
    await fetch('/api/admin-logout', { method: 'POST', credentials: 'same-origin' }).catch(() => {});
    location.replace('/admin');
  });

  (async function init() {
    if (!core || !guard || !await guard.requireAdmin(true)) return;
    document.body.classList.remove('manage-pending');
    const message = new URLSearchParams(location.search).get('notice');
    if (message) notice(message);
    try {
      await loadRecords();
    } catch (error) {
      rows.innerHTML = `<tr><td colspan="10" class="manual-empty">${esc(error.message || 'Unable to load Supabase schedules.')}</td></tr>`;
      calendarRows.innerHTML = '<tr><td colspan="6" class="workspace-empty">Unable to load the weekly calendar.</td></tr>';
      directoryList.innerHTML = '<div class="workspace-empty">Unable to load personnel.</div>';
      notice(error.message || 'Unable to load Supabase schedules.', true);
    }
  })();
})();
