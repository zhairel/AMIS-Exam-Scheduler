(function () {
  'use strict';

  const core = window.AMISScheduleCore;
  const form = document.getElementById('scheduleForm');
  if (!core || !form) return;

  const mode = document.body.dataset.mode || 'create';
  const fields = Object.fromEntries(Array.from(form.elements).filter((element) => element.name).map((element) => [element.name, element]));
  const availabilityState = document.getElementById('availabilityState');
  const availabilityDetail = document.getElementById('availabilityDetail');
  const conflictPanel = document.getElementById('conflictPanel');
  const conflictList = document.getElementById('conflictList');
  const originalSlot = document.getElementById('originalSlot');
  const suggestedSlot = document.getElementById('suggestedSlot');
  const useSuggestion = document.getElementById('useSuggestion');
  const keepEditing = document.getElementById('keepEditing');
  const formError = document.getElementById('formError');
  const saveButton = document.getElementById('saveButton');
  const loadingStatus = document.getElementById('loadingStatus');
  let officialSections = [];
  let officialEntries = [];
  let manualEntries = [];
  let currentId = '';
  let currentRecord = null;
  let currentSuggestion = null;
  let evaluationTimer = null;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  }

  function getIdFromUrl() {
    const queryId = new URLSearchParams(location.search).get('id');
    if (queryId) return queryId;
    const match = location.pathname.match(/\/class-schedule\/([^/]+)\/edit\/?$/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function setError(message) {
    formError.textContent = message || '';
    formError.classList.toggle('show', Boolean(message));
  }

  function setAvailability(state, detail) {
    availabilityState.className = `availability-state availability-${state}`;
    availabilityState.textContent = state === 'available' ? 'AVAILABLE' : state === 'unavailable' ? 'UNAVAILABLE' : 'SELECT A TEACHER AND TIME';
    availabilityDetail.innerHTML = detail || '';
  }

  function recordFromForm() {
    const selectedTeacher = fields.teacher.options[fields.teacher.selectedIndex];
    const selectedSection = fields.section.options[fields.section.selectedIndex];
    return {
      ...(currentRecord || {}),
      id: currentId || undefined,
      teacher: fields.teacher.value,
      teacher_id: selectedTeacher ? selectedTeacher.dataset.id || '' : '',
      subject: fields.subject.value,
      grade_level: fields.grade_level.value,
      section: fields.section.value,
      section_id: selectedSection ? selectedSection.dataset.id || '' : '',
      day: fields.day.value,
      start_time: fields.start_time.value,
      end_time: fields.end_time.value,
      room: fields.room.value,
      schedule_type: fields.schedule_type.value,
      status: fields.status.value
    };
  }

  function allEntries() {
    return officialEntries.concat(manualEntries);
  }

  function describeConflict(conflict) {
    const item = conflict.entry;
    const labels = conflict.reasons.map((reason) => reason.charAt(0).toUpperCase() + reason.slice(1)).join(', ');
    return `<strong>${esc(labels)} conflict:</strong> ${esc(item.teacher || 'Unassigned')} — ${esc(item.subject)} — ${esc(item.section)} — ${esc(item.day)} ${esc(core.formatRange(item))}${item.source === 'official' ? ' <em>(official schedule)</em>' : ''}`;
  }

  function showConflict(candidate, conflicts) {
    currentSuggestion = core.findSuggestion(candidate, allEntries(), currentId);
    conflictList.innerHTML = conflicts.map((conflict) => `<li>${describeConflict(conflict)}</li>`).join('');
    originalSlot.textContent = `${candidate.day} ${core.formatRange(candidate)}`;
    suggestedSlot.textContent = currentSuggestion ? `${currentSuggestion.day} ${core.formatRange(currentSuggestion)}` : 'No valid slot found between 7:00 AM and 7:00 PM.';
    useSuggestion.disabled = !currentSuggestion;
    conflictPanel.classList.add('show');
  }

  function evaluate() {
    const candidate = recordFromForm();
    setError('');
    conflictPanel.classList.remove('show');
    currentSuggestion = null;

    if (!candidate.teacher || !candidate.day || !candidate.start_time || !candidate.end_time) {
      setAvailability('idle', 'Availability updates automatically as the teacher, day, and time change.');
      saveButton.disabled = false;
      return;
    }

    if (!core.recordRange(candidate)) {
      setAvailability('unavailable', 'End time must be later than start time.');
      saveButton.disabled = true;
      return;
    }

    if (candidate.status === 'inactive') {
      setAvailability('available', 'Inactive schedules are saved but do not occupy the teacher, section, or room.');
      saveButton.disabled = false;
      return;
    }

    const conflicts = core.findBlockingConflicts(candidate, allEntries(), currentId, currentRecord);
    const teacherConflicts = conflicts.filter((conflict) => conflict.reasons.includes('teacher'));
    if (teacherConflicts.length) {
      setAvailability('unavailable', teacherConflicts.map(describeConflict).join('<br>'));
    } else {
      setAvailability('available', `${esc(candidate.teacher)} has no active schedule during this period.`);
    }

    if (conflicts.length) {
      showConflict(candidate, conflicts);
      saveButton.disabled = true;
    } else {
      saveButton.disabled = false;
    }
  }

  function scheduleEvaluation() {
    clearTimeout(evaluationTimer);
    evaluationTimer = setTimeout(evaluate, 80);
  }

  function populateTeachers(teacherData) {
    const map = new Map();
    Object.values(teacherData || {}).forEach((teacher) => {
      const name = core.clean(teacher.canonical_name || teacher.teacher_name || teacher.name);
      if (name) map.set(name, core.clean(teacher.teacher_id || teacher.id));
    });
    officialSections.forEach((section) => {
      (section.periods || section.rows || []).forEach((row) => {
        core.SCHOOL_DAYS.forEach((day) => {
          const cell = row.days ? row.days[day] : null;
          const name = core.clean((cell && cell.teacher) || row.teacher);
          if (name && !map.has(name)) map.set(name, core.clean((cell && cell.teacher_id) || row.teacher_id));
        });
      });
    });
    fields.teacher.innerHTML = '<option value="">Select Teacher / Faculty / Staff</option>' + Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0])).map(([name, id]) => `<option value="${esc(name)}" data-id="${esc(id)}">${esc(name)}</option>`).join('');
  }

  function populateSections() {
    const seen = new Set();
    fields.section.innerHTML = '<option value="">Select class section</option>' + officialSections.filter((section) => {
      const name = core.clean(section.section_name);
      if (!name || seen.has(name)) return false;
      seen.add(name);
      return true;
    }).sort((a, b) => a.section_name.localeCompare(b.section_name)).map((section) => `<option value="${esc(section.section_name)}" data-id="${esc(section.id || section.section_id)}" data-grade="${esc(section.grade_level)}">${esc(section.section_name)}</option>`).join('');
  }

  function applyRecord(record) {
    Object.entries(record || {}).forEach(([name, value]) => {
      if (fields[name]) fields[name].value = value == null ? '' : value;
    });
    document.getElementById('pageTitle').textContent = 'Edit Schedule';
    document.getElementById('pageDescription').textContent = 'Update the assignment. Conflict and availability checks run automatically before saving.';
    saveButton.textContent = 'Update Schedule';
  }

  async function init() {
    try {
      if (!window.AMISAdminGuard || !await window.AMISAdminGuard.requireAdmin(true)) return;
      document.body.classList.remove('admin-pending');
      loadingStatus.textContent = 'Loading official schedules and shared Supabase records…';
      const [sections, teacherResponse, manuals] = await Promise.all([
        core.loadOfficialData('..'),
        fetch('../teacher_weekly_schedules.json?v=' + Date.now(), { cache: 'no-store' }),
        core.listSchedules()
      ]);
      officialSections = sections;
      officialEntries = core.officialEntriesFromSections(sections);
      manualEntries = manuals;
      const teacherData = teacherResponse.ok ? await teacherResponse.json() : {};
      populateTeachers(teacherData);
      populateSections();

      if (mode === 'edit') {
        currentId = getIdFromUrl();
        if (!currentId) throw new Error('No schedule ID was provided.');
        currentRecord = await core.getSchedule(currentId);
        if (!currentRecord) throw new Error('This manual schedule was not found. It may have been deleted.');
        applyRecord(currentRecord);
      } else {
        const params = new URLSearchParams(location.search);
        ['teacher', 'subject', 'grade_level', 'section', 'day', 'start_time', 'end_time', 'room', 'schedule_type', 'status'].forEach((name) => {
          if (params.has(name) && fields[name]) fields[name].value = params.get(name);
        });
      }
      loadingStatus.textContent = 'All changes are stored in the shared AMIS Supabase database.';
      evaluate();
    } catch (error) {
      setError(error.message || 'Unable to load the schedule form.');
      saveButton.disabled = true;
      loadingStatus.textContent = '';
    }
  }

  fields.section.addEventListener('change', () => {
    const selected = fields.section.options[fields.section.selectedIndex];
    if (selected && selected.dataset.grade) fields.grade_level.value = selected.dataset.grade;
    scheduleEvaluation();
  });
  Object.values(fields).forEach((field) => field.addEventListener('input', scheduleEvaluation));
  Object.values(fields).forEach((field) => field.addEventListener('change', scheduleEvaluation));

  useSuggestion.addEventListener('click', () => {
    if (!currentSuggestion) return;
    fields.day.value = currentSuggestion.day;
    fields.start_time.value = currentSuggestion.start_time;
    fields.end_time.value = currentSuggestion.end_time;
    conflictPanel.classList.remove('show');
    evaluate();
    fields.start_time.focus();
  });
  keepEditing.addEventListener('click', () => {
    conflictPanel.classList.remove('show');
    fields.start_time.focus();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    setError('');
    if (!window.AMISAdminGuard || !await window.AMISAdminGuard.requireAdmin(true)) return;
    const candidate = recordFromForm();
    const conflicts = core.findBlockingConflicts(candidate, allEntries(), currentId, currentRecord);
    if (conflicts.length) {
      showConflict(candidate, conflicts);
      saveButton.disabled = true;
      return;
    }
    saveButton.disabled = true;
    saveButton.textContent = mode === 'edit' ? 'Updating…' : 'Saving…';
    try {
      await core.saveScheduleChecked(candidate, officialEntries);
      location.href = `/class-schedule-manage?notice=${encodeURIComponent(mode === 'edit' ? 'Schedule updated successfully.' : 'Schedule created successfully.')}`;
    } catch (error) {
      if (error instanceof core.ScheduleConflictError) {
        manualEntries = await core.listSchedules();
        showConflict(candidate, error.conflicts);
      } else {
        setError(error.message || 'Unable to save this schedule.');
      }
      saveButton.disabled = false;
      saveButton.textContent = mode === 'edit' ? 'Update Schedule' : 'Save Schedule';
    }
  });

  init();
})();
