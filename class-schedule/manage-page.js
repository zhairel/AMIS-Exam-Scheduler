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
  let classes = [];
  let originalEntries = [];
  let selectedTeacher = '';
  let selectedSection = '';
  let page = 1;

  const rows = document.getElementById('manageRows');
  const classCalendarRows = document.getElementById('classCalendarRows');
  const classDirectoryList = document.getElementById('classDirectoryList');
  const classDirectorySearch = document.getElementById('classDirectorySearch');
  const personnelRows = document.getElementById('personnelScheduleRows');
  const directoryList = document.getElementById('teacherDirectoryList');
  const directorySearch = document.getElementById('teacherDirectorySearch');
  const filters = {
    search: document.getElementById('manageSearch'), teacher: document.getElementById('manageTeacher'),
    grade_level: document.getElementById('manageGrade'), section: document.getElementById('manageSection'),
    subject: document.getElementById('manageSubject'), day: document.getElementById('manageDay'),
    status: document.getElementById('manageStatus'), source: document.getElementById('manageSource')
  };

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  }

  function isOfficial(record) {
    return record.source === 'official' || String(record.id || '').startsWith('official:');
  }

  function isEvent(record) {
    return record.schedule_type === 'Official Break / Assembly' || !record.teacher;
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

  function removeButton(record, className) {
    if (record._database === false) return '';
    const official = isOfficial(record);
    if (official && record.status !== 'active') return '';
    const action = official ? 'Deactivate' : 'Delete';
    const deleteClass = className.includes('calendar') ? 'calendar-icon-delete' : 'manual-icon-delete';
    return `<button class="${className} ${deleteClass}" type="button" data-action="remove" data-id="${esc(record.id)}" title="${action} schedule" aria-label="${action} ${esc(record.subject)}">${ICONS.trash}</button>`;
  }

  function editLink(record, className) {
    if (record._database === false) return '';
    return `<a class="${className}" href="/class-schedule-manage/edit?id=${encodeURIComponent(record.id)}" title="Edit schedule" aria-label="Edit ${esc(record.subject)}">${ICONS.edit}</a>`;
  }

  function applyFilters() {
    const search = filters.search.value.trim().toLowerCase();
    filteredRecords = records.filter((record) => {
      if (['teacher', 'grade_level', 'section', 'subject', 'day', 'status', 'source'].some((field) => filters[field].value && record[field] !== filters[field].value)) return false;
      return !search || [record.teacher, record.subject, record.grade_level, record.section, record.day, record.room, record.schedule_type, record.status, record.source].join(' ').toLowerCase().includes(search);
    });
    page = Math.min(page, Math.max(1, Math.ceil(filteredRecords.length / PAGE_SIZE)));
    renderRows();
  }

  function renderRows() {
    const start = (page - 1) * PAGE_SIZE;
    const visible = filteredRecords.slice(start, start + PAGE_SIZE);
    rows.innerHTML = visible.length ? visible.map((record) => `<tr>
      <td><strong>${esc(record.teacher || 'School Event')}</strong></td><td>${esc(record.subject)}</td>
      <td><strong>${esc(record.grade_level)}</strong><br>${esc(record.section)}</td><td>${esc(record.day)}</td>
      <td>${esc(core.formatRange(record))}</td><td>${record.room ? esc(record.room) : '—'}</td><td>${esc(record.schedule_type)}</td>
      <td><span class="status-pill manual-source-pill">${isOfficial(record) ? 'OFFICIAL DB' : 'MANUAL'}</span></td>
      <td><span class="status-pill status-${esc(record.status)}">${esc(record.status.toUpperCase())}</span></td>
      <td><div class="manual-actions">${editLink(record, 'manual-icon-action')}${removeButton(record, 'manual-icon-action')}</div></td>
    </tr>`).join('') : '<tr><td colspan="10" class="manual-empty">No schedules match the selected filters.</td></tr>';
    const end = Math.min(start + PAGE_SIZE, filteredRecords.length);
    document.getElementById('pageSummary').textContent = filteredRecords.length ? `Showing ${start + 1}–${end} of ${filteredRecords.length.toLocaleString()} records` : '0 records';
    document.getElementById('previousPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = end >= filteredRecords.length;
  }

  function buildPersonnel(teacherData) {
    const people = new Map();
    Object.values(teacherData || {}).forEach((teacher) => {
      const name = core.clean(teacher.canonical_name || teacher.teacher_name || teacher.name);
      if (name) people.set(name, { name, department: core.clean(teacher.department || 'Faculty / Staff') });
    });
    records.forEach((record) => {
      if (record.teacher && !people.has(record.teacher)) people.set(record.teacher, { name: record.teacher, department: 'Faculty / Staff' });
    });
    personnel = Array.from(people.values()).sort((left, right) => left.name.localeCompare(right.name));
    document.getElementById('teacherCount').textContent = personnel.length.toLocaleString();
  }

  function buildClasses(sectionData) {
    const map = new Map();
    (sectionData || []).forEach((section) => {
      const name = core.clean(section.section_name);
      if (name) map.set(name, { name, id: core.clean(section.id || section.section_id), grade: core.clean(section.grade_level), department: core.clean(section.department), shift: core.clean(section.shift || section.modality) });
    });
    records.forEach((record) => {
      if (record.section && !map.has(record.section)) map.set(record.section, { name: record.section, id: record.section_id || '', grade: record.grade_level, department: '', shift: 'MANUAL' });
    });
    classes = Array.from(map.values());
    document.getElementById('classCount').textContent = classes.length.toLocaleString();
  }

  function recordsForTeacher(name) {
    return records.filter((record) => record.teacher === name);
  }

  function completeClassRecords(name) {
    const combined = new Map();
    originalEntries.filter((record) => record.section === name).forEach((record) => combined.set(record.id, { ...record, _database: false }));
    records.filter((record) => record.section === name).forEach((record) => combined.set(record.id, { ...record, _database: true }));
    return Array.from(combined.values());
  }

  function subjectCounts(items) {
    const counts = new Map();
    items.forEach((record) => counts.set(record.subject, (counts.get(record.subject) || 0) + 1));
    return Array.from(counts.entries()).sort((left, right) => left[0].localeCompare(right[0]));
  }

  function initials(name) {
    return String(name || '').split(/\s+/).filter(Boolean).slice(-2).map((part) => part[0]).join('').toUpperCase() || '—';
  }

  function gradeBadge(grade) {
    const kinder = String(grade).match(/Kinder\s*(\d)?/i);
    if (kinder) return `K${kinder[1] || ''}`;
    const gradeNumber = String(grade).match(/\d+/);
    return gradeNumber ? `G${gradeNumber[0]}` : String(grade).slice(0, 4);
  }

  function renderClassDirectory() {
    const query = classDirectorySearch.value.trim().toLowerCase();
    const visible = classes.filter((item) => !query || `${item.grade} ${item.name} ${item.shift}`.toLowerCase().includes(query));
    classDirectoryList.innerHTML = visible.length ? visible.map((item) => {
      const count = completeClassRecords(item.name).length;
      return `<button class="teacher-directory-item class-directory-item${item.name === selectedSection ? ' selected' : ''}" type="button" data-section="${esc(item.name)}" aria-pressed="${item.name === selectedSection}">
        <span class="class-grade-badge">${esc(gradeBadge(item.grade))}</span><span class="teacher-directory-copy"><strong>${esc(item.name)}</strong><small>${esc([item.grade, item.shift].filter(Boolean).join(' • '))}</small></span><span class="teacher-record-count">${count}</span>
      </button>`;
    }).join('') : '<div class="workspace-empty">No grade or section matches your search.</div>';
  }

  function renderPersonnelDirectory() {
    const query = directorySearch.value.trim().toLowerCase();
    const visible = personnel.filter((person) => {
      const subjects = subjectCounts(recordsForTeacher(person.name)).map(([subject]) => subject).join(' ');
      return !query || `${person.name} ${person.department} ${subjects}`.toLowerCase().includes(query);
    });
    directoryList.innerHTML = visible.length ? visible.map((person) => {
      const assignments = recordsForTeacher(person.name);
      const subjects = Array.from(new Set(assignments.map((record) => record.subject))).slice(0, 2);
      return `<button class="teacher-directory-item${person.name === selectedTeacher ? ' selected' : ''}" type="button" data-teacher="${esc(person.name)}" aria-pressed="${person.name === selectedTeacher}">
        <span class="teacher-avatar">${esc(initials(person.name))}</span><span class="teacher-directory-copy"><strong>${esc(person.name)}</strong><small>${esc(subjects.length ? subjects.join(' • ') : 'No assigned subjects')}</small></span><span class="teacher-record-count">${assignments.length}</span>
      </button>`;
    }).join('') : '<div class="workspace-empty">No person or subject matches your search.</div>';
  }

  function overlapsBand(record, day, startTime, endTime) {
    if (record.day !== day || record.status !== 'active') return false;
    const recordStart = core.parseClock(record.start_time), recordEnd = core.parseClock(record.end_time);
    const bandStart = core.parseClock(startTime), bandEnd = core.parseClock(endTime);
    return recordStart != null && recordEnd != null && bandStart != null && bandEnd != null && recordStart < bandEnd && bandStart < recordEnd;
  }

  function classCreateUrl(day, startTime, endTime) {
    const selected = classes.find((item) => item.name === selectedSection) || {};
    const params = new URLSearchParams({ grade_level: selected.grade || '', section: selected.name || '', day, start_time: startTime, end_time: endTime, schedule_type: 'Academic Class', status: 'active' });
    return `/class-schedule-manage/create?${params.toString()}`;
  }

  function renderClassCard(record) {
    const event = isEvent(record);
    const pending = record._database === false;
    return `<article class="calendar-card${event ? ' event' : ''}${record.status === 'inactive' ? ' inactive' : ''}" title="${esc(`${record.subject} — ${record.teacher || 'School event'}`)}">
      <strong>${esc(record.subject)}</strong><span>${esc(record.teacher || 'School event')}</span><span>${pending ? 'Original timetable' : (record.status === 'inactive' ? 'INACTIVE' : 'ACTIVE')}</span>
      <div class="calendar-card-actions">${editLink(record, 'calendar-icon-action')}${removeButton(record, 'calendar-icon-action')}</div>
    </article>`;
  }

  function mergedEventRow(dayRecords) {
    if (dayRecords.length !== core.SCHOOL_DAYS.length || !dayRecords.every((record) => isEvent(record))) return false;
    const first = dayRecords[0];
    return dayRecords.every((record) => record.subject === first.subject
      && record.start_time === first.start_time
      && record.end_time === first.end_time
      && record.schedule_type === first.schedule_type
      && record.status === first.status);
  }

  function renderMergedEventCard(dayRecords) {
    const first = dayRecords[0];
    const databaseRecords = dayRecords.filter((record) => record._database !== false);
    const ids = databaseRecords.map((record) => record.id);
    const edit = ids.length === core.SCHOOL_DAYS.length
      ? `<a class="calendar-icon-action" href="/class-schedule-manage/edit?id=${encodeURIComponent(ids[0])}&group_ids=${encodeURIComponent(ids.join(','))}" title="Edit this event for all school days" aria-label="Edit ${esc(first.subject)} for all school days">${ICONS.edit}</a>`
      : '';
    const remove = ids.length === core.SCHOOL_DAYS.length && first.status === 'active'
      ? `<button class="calendar-icon-action calendar-icon-delete" type="button" data-action="remove-group" data-ids="${esc(ids.join(','))}" title="Deactivate this event for all school days" aria-label="Deactivate ${esc(first.subject)} for all school days">${ICONS.trash}</button>`
      : '';
    return `<article class="calendar-card event merged-event" title="${esc(first.subject)} — all school days"><strong>${esc(first.subject)}</strong><span>All School Days</span><span>${ids.length === core.SCHOOL_DAYS.length ? 'ACTIVE • DATABASE' : 'Original timetable'}</span><div class="calendar-card-actions">${edit}${remove}</div></article>`;
  }

  function renderClassCalendar() {
    const selected = classes.find((item) => item.name === selectedSection);
    const classRecords = completeClassRecords(selectedSection);
    document.getElementById('classCalendarTitle').textContent = selected ? selected.name : 'Class Weekly Calendar';
    document.getElementById('selectedClassMeta').textContent = selected ? `${selected.grade}${selected.shift ? ` • ${selected.shift}` : ''} • ${classRecords.length} timetable cells` : 'Choose a grade and section.';
    const createParams = selected ? `?grade_level=${encodeURIComponent(selected.grade)}&section=${encodeURIComponent(selected.name)}` : '';
    document.getElementById('classCreateLink').href = `/class-schedule-manage/create${createParams}`;
    const subjects = subjectCounts(classRecords);
    document.getElementById('classSubjectList').innerHTML = subjects.length ? subjects.map(([subject, count]) => `<span class="subject-chip">${esc(subject)} <b>${count}</b></span>`).join('') : '<span class="subject-empty">No assignments or events yet.</span>';
    if (!selected) {
      classCalendarRows.innerHTML = '<tr><td colspan="6" class="workspace-empty">Select a class to view its complete calendar.</td></tr>';
      return;
    }
    let bands = Array.from(new Map(classRecords.map((record) => [`${record.start_time}|${record.end_time}`, [record.start_time, record.end_time]])).values());
    if (!bands.length) bands = DEFAULT_TIME_BANDS.slice();
    bands.sort((left, right) => `${left[0]}|${left[1]}`.localeCompare(`${right[0]}|${right[1]}`));
    classCalendarRows.innerHTML = bands.map(([startTime, endTime]) => {
      const label = core.formatRange({ start_time: startTime, end_time: endTime });
      const dayRecords = core.SCHOOL_DAYS.map((day) => classRecords.filter((record) => record.day === day && record.start_time === startTime && record.end_time === endTime));
      const mergeCandidates = dayRecords.map((items) => items.length === 1 ? items[0] : null);
      if (mergeCandidates.every(Boolean) && mergedEventRow(mergeCandidates)) {
        return `<tr><td class="calendar-time">${esc(label)}</td><td class="calendar-cell calendar-merged-cell" colspan="5">${renderMergedEventCard(mergeCandidates)}</td></tr>`;
      }
      const cells = core.SCHOOL_DAYS.map((day) => {
        const exact = classRecords.filter((record) => record.day === day && record.start_time === startTime && record.end_time === endTime);
        const overlap = !exact.length && classRecords.some((record) => overlapsBand(record, day, startTime, endTime));
        const content = exact.length ? exact.map(renderClassCard).join('') : overlap ? '<div class="calendar-overlap-state"><span>Occupied</span><small>Overlapping time</small></div>' : `<a class="calendar-empty-link" href="${classCreateUrl(day, startTime, endTime)}"><strong>＋</strong><span>Available</span></a>`;
        return `<td class="calendar-cell">${content}</td>`;
      }).join('');
      return `<tr><td class="calendar-time">${esc(label)}</td>${cells}</tr>`;
    }).join('');
  }

  function renderPersonnelList() {
    const person = personnel.find((item) => item.name === selectedTeacher);
    const assignments = recordsForTeacher(selectedTeacher).sort((a, b) => `${core.SCHOOL_DAYS.indexOf(a.day)}|${a.start_time}`.localeCompare(`${core.SCHOOL_DAYS.indexOf(b.day)}|${b.start_time}`));
    document.getElementById('personnelListTitle').textContent = selectedTeacher || 'Faculty / Staff Schedule';
    document.getElementById('selectedTeacherMeta').textContent = person ? `${person.department} • ${assignments.filter((record) => record.status === 'active').length} active • ${assignments.length} total assignments` : 'Choose a person from the directory.';
    document.getElementById('teacherCreateLink').href = selectedTeacher ? `/class-schedule-manage/create?teacher=${encodeURIComponent(selectedTeacher)}` : '/class-schedule-manage/create';
    const subjects = subjectCounts(assignments);
    document.getElementById('teacherSubjectList').innerHTML = subjects.length ? subjects.map(([subject, count]) => `<span class="subject-chip">${esc(subject)} <b>${count}</b></span>`).join('') : '<span class="subject-empty">No assigned subjects yet.</span>';
    personnelRows.innerHTML = assignments.length ? assignments.map((record) => `<tr><td><strong>${esc(record.day)}</strong></td><td>${esc(core.formatRange(record))}</td><td class="personnel-subject"><strong>${esc(record.subject)}</strong><small>${esc(record.room || record.schedule_type)}</small></td><td><strong>${esc(record.grade_level)}</strong><br>${esc(record.section)}</td><td>${esc(record.schedule_type)}</td><td><span class="status-pill status-${esc(record.status)}">${esc(record.status.toUpperCase())}</span></td><td><div class="manual-actions">${editLink(record, 'manual-icon-action')}${removeButton(record, 'manual-icon-action')}</div></td></tr>`).join('') : '<tr><td colspan="7" class="workspace-empty">No schedule assignments for this person.</td></tr>';
  }

  function selectSection(name) {
    selectedSection = name;
    renderClassDirectory();
    renderClassCalendar();
  }

  function selectTeacher(name) {
    selectedTeacher = name;
    renderPersonnelDirectory();
    renderPersonnelList();
  }

  function switchWorkspace(name) {
    document.getElementById('classWorkspace').hidden = name !== 'classes';
    document.getElementById('personnelWorkspace').hidden = name !== 'personnel';
    document.querySelectorAll('[data-workspace]').forEach((button) => {
      const active = button.dataset.workspace === name;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', String(active));
    });
  }

  async function loadRecords() {
    const [scheduleRecords, teacherResponse, classResponse] = await Promise.all([
      core.listSchedules(), fetch('/teacher_weekly_schedules.json?v=' + Date.now(), { cache: 'no-store' }), fetch('/class_schedules_data.json?v=' + Date.now(), { cache: 'no-store' })
    ]);
    records = scheduleRecords.map((record) => ({ ...record, _database: true }));
    const teacherData = teacherResponse.ok ? await teacherResponse.json() : {};
    const sectionData = classResponse.ok ? await classResponse.json() : [];
    originalEntries = core.officialEntriesFromSections(sectionData);
    buildPersonnel(teacherData);
    buildClasses(sectionData);
    populateSelect(filters.teacher, 'teacher'); populateSelect(filters.grade_level, 'grade_level'); populateSelect(filters.section, 'section'); populateSelect(filters.subject, 'subject');
    if (!selectedTeacher) selectedTeacher = (personnel.find((person) => recordsForTeacher(person.name).length) || personnel[0] || {}).name || '';
    if (!selectedSection) selectedSection = (classes[0] || {}).name || '';
    updateStats(); renderClassDirectory(); renderClassCalendar(); renderPersonnelDirectory(); renderPersonnelList(); applyFilters();
  }

  async function handleRemove(event) {
    const button = event.target.closest('[data-action="remove"], [data-action="remove-group"]');
    if (!button) return;
    const ids = button.dataset.ids ? button.dataset.ids.split(',').filter(Boolean) : [button.dataset.id];
    const targets = ids.map((id) => records.find((item) => item.id === id)).filter(Boolean);
    if (!targets.length) return;
    const official = targets.every(isOfficial);
    const grouped = targets.length > 1;
    if (!window.confirm(grouped ? `Deactivate ${targets[0].subject} for all school days?` : (official ? 'Deactivate this official timetable item? It can be reactivated through Edit.' : 'Are you sure you want to permanently delete this manual schedule?'))) return;
    button.disabled = true;
    try {
      for (const target of targets) await core.deleteSchedule(target.id);
      notice(grouped ? 'All-day event deactivated for every school day.' : (official ? 'Official timetable item deactivated.' : 'Manual schedule deleted.'));
      await loadRecords();
    } catch (error) {
      notice(error.message || 'Unable to update this schedule.', true);
      button.disabled = false;
    }
  }

  document.addEventListener('click', handleRemove);
  document.querySelectorAll('[data-workspace]').forEach((button) => button.addEventListener('click', () => switchWorkspace(button.dataset.workspace)));
  classDirectoryList.addEventListener('click', (event) => { const button = event.target.closest('[data-section]'); if (button) selectSection(button.dataset.section); });
  directoryList.addEventListener('click', (event) => { const button = event.target.closest('[data-teacher]'); if (button) selectTeacher(button.dataset.teacher); });
  classDirectorySearch.addEventListener('input', renderClassDirectory);
  directorySearch.addEventListener('input', renderPersonnelDirectory);
  Object.entries(filters).forEach(([name, element]) => element.addEventListener(element === filters.search ? 'input' : 'change', () => { page = 1; if (name === 'teacher' && element.value) selectTeacher(element.value); if (name === 'section' && element.value) selectSection(element.value); applyFilters(); }));
  document.getElementById('previousPage').addEventListener('click', () => { if (page > 1) { page -= 1; renderRows(); } });
  document.getElementById('nextPage').addEventListener('click', () => { if (page * PAGE_SIZE < filteredRecords.length) { page += 1; renderRows(); } });
  document.getElementById('manageLogout').addEventListener('click', async () => { await fetch('/api/admin-logout', { method: 'POST', credentials: 'same-origin' }).catch(() => {}); location.replace('/admin'); });

  (async function init() {
    if (!core || !guard || !await guard.requireAdmin(true)) return;
    document.body.classList.remove('manage-pending');
    const message = new URLSearchParams(location.search).get('notice');
    if (message) notice(message);
    try {
      await loadRecords();
    } catch (error) {
      rows.innerHTML = `<tr><td colspan="10" class="manual-empty">${esc(error.message || 'Unable to load Supabase schedules.')}</td></tr>`;
      classCalendarRows.innerHTML = '<tr><td colspan="6" class="workspace-empty">Unable to load class calendars.</td></tr>';
      personnelRows.innerHTML = '<tr><td colspan="7" class="workspace-empty">Unable to load personnel schedules.</td></tr>';
      notice(error.message || 'Unable to load schedule data.', true);
    }
  })();
})();
