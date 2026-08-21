(function () {
  'use strict';

  const core = window.AMISScheduleCore;
  const guard = window.AMISAdminGuard;
  const PAGE_SIZE = 100;
  let records = [];
  let filteredRecords = [];
  let page = 1;

  const rows = document.getElementById('manageRows');
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

  function renderRows() {
    const start = (page - 1) * PAGE_SIZE;
    const visible = filteredRecords.slice(start, start + PAGE_SIZE);
    if (!visible.length) {
      rows.innerHTML = '<tr><td colspan="10" class="manual-empty">No schedules match the selected filters.</td></tr>';
    } else {
      rows.innerHTML = visible.map((record) => {
        const official = isOfficial(record);
        const deactivate = record.status === 'active' ? `<button class="manual-icon-action manual-icon-delete" type="button" data-action="remove" data-id="${esc(record.id)}" title="${official ? 'Deactivate official schedule' : 'Delete manual schedule'}" aria-label="${official ? 'Deactivate' : 'Delete'} ${esc(record.subject)}">×</button>` : '';
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
          <td><div class="manual-actions"><a class="manual-icon-action" href="/class-schedule-manage/edit?id=${encodeURIComponent(record.id)}" title="Edit schedule" aria-label="Edit ${esc(record.subject)}">✎</a>${deactivate}</div></td>
        </tr>`;
      }).join('');
    }
    const end = Math.min(start + PAGE_SIZE, filteredRecords.length);
    document.getElementById('pageSummary').textContent = filteredRecords.length ? `Showing ${start + 1}–${end} of ${filteredRecords.length.toLocaleString()} records` : '0 records';
    document.getElementById('previousPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = end >= filteredRecords.length;
  }

  async function loadRecords() {
    records = await core.listSchedules();
    populateSelect(filters.teacher, 'teacher');
    populateSelect(filters.grade_level, 'grade_level');
    populateSelect(filters.section, 'section');
    populateSelect(filters.subject, 'subject');
    updateStats();
    applyFilters();
  }

  rows.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-action="remove"]');
    if (!button) return;
    const record = records.find((item) => item.id === button.dataset.id);
    if (!record) return;
    const official = isOfficial(record);
    const confirmed = window.confirm(official ? 'Deactivate this official schedule? It can be reactivated through Edit.' : 'Permanently delete this manual schedule?');
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
  });

  Object.values(filters).forEach((element) => element.addEventListener(element === filters.search ? 'input' : 'change', () => { page = 1; applyFilters(); }));
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
      notice(error.message || 'Unable to load Supabase schedules.', true);
    }
  })();
})();
