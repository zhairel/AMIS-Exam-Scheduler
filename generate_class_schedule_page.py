import json

HTML_CONTENT = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMIS — Official Class Timetable & Section Weekly Schedule</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">

<!-- html2pdf.js CDN with offline fallback -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

<!-- Embedded Master Section Class Data -->
<script src="class_schedules_data.js"></script>

<style>
:root {
  --brand-deep: #064e3b;
  --brand-green: #0b4d38;
  --brand-accent: #0f766e;
  --brand-surface: #f0fdf4;
  --brand-border: #a7f3d0;
  
  --ink: #0f172a;
  --ink-secondary: #334155;
  --muted: #64748b;
  --line: #cbd5e1;
  --line-strong: #94a3b8;
  --bg: #f8fafc;
  --surface: #ffffff;
  
  --break-bg: #f1f5f9;
  --break-text: #475569;
  --break-border: #cbd5e1;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  padding-bottom: 60px;
}

/* Screen Navigation Toolbar */
.top-toolbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: var(--brand-deep);
  color: #fff;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  flex-wrap: wrap;
}

.brand-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 38px;
  height: 38px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 16px;
}

.brand-text h1 {
  font-size: 15.5px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.brand-text p {
  font-size: 11.5px;
  color: #a7f3d0;
  font-weight: 600;
}

.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.2);
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.filter-label {
  font-size: 11.5px;
  font-weight: 800;
  color: #a7f3d0;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.filter-select {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: #ffffff;
  color: var(--ink);
  font-weight: 750;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.filter-select-section {
  min-width: 260px;
  max-width: 360px;
}

.btn-action {
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  border: 1.5px solid transparent;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  transition: all 0.15s ease;
}

.btn-print {
  background: #ffffff;
  color: var(--brand-deep);
  border-color: #ffffff;
}

.btn-print:hover {
  background: #f0fdf4;
}

.btn-back {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* Printable Container (A4 / Legal Landscape) */
.page-sheet-container {
  max-width: 1400px;
  margin: 24px auto 0;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.timetable-sheet {
  background: #ffffff;
  border: 2px solid var(--line-strong);
  border-radius: 12px;
  padding: 24px 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  page-break-after: always;
  break-after: page;
}

.timetable-sheet:last-child {
  page-break-after: auto;
  break-after: auto;
}

/* Header Block */
.school-header {
  text-align: center;
  margin-bottom: 14px;
}

.school-header h1 {
  font-size: 20px;
  font-weight: 900;
  color: var(--brand-deep);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.school-header h2 {
  font-size: 14px;
  font-weight: 800;
  color: var(--ink-secondary);
  letter-spacing: 0.02em;
  margin-top: 2px;
}

.school-header p {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-top: 1px;
}

/* Teacher / Section Banner */
.teacher-banner {
  background: var(--brand-deep);
  color: #ffffff;
  padding: 10px 16px;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 2px solid var(--brand-deep);
  border-bottom: 0;
}

.teacher-name-title {
  font-size: 17px;
  font-weight: 900;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.teacher-meta-tag {
  font-size: 12px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.02em;
}

/* Timetable Table Grid */
.timetable-grid {
  width: 100%;
  border-collapse: collapse;
  border: 2px solid var(--brand-deep);
  table-layout: fixed;
  background: #ffffff;
}

.timetable-grid thead th {
  background: var(--brand-green);
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
  text-align: center;
  padding: 8px 6px;
  border: 1.5px solid #043828;
  letter-spacing: 0.02em;
}

.timetable-grid thead th.col-time {
  width: 155px;
}

.timetable-grid thead th.col-mins {
  width: 75px;
}

.timetable-grid tbody td {
  border: 1.5px solid var(--line-strong);
  padding: 6px 8px;
  text-align: center;
  font-size: 12px;
  vertical-align: middle;
  height: 40px;
}

.timetable-grid tbody td.cell-time {
  background: #f8fafc;
  font-weight: 800;
  color: #1e293b;
  font-size: 11.5px;
  white-space: nowrap;
}

.timetable-grid tbody td.cell-mins {
  background: #f1f5f9;
  font-weight: 800;
  color: #475569;
  font-size: 12px;
}

/* Special Break Row */
.timetable-grid tbody tr.row-break td.cell-break {
  background: var(--break-bg) !important;
  color: var(--break-text) !important;
  font-size: 11.5px !important;
  font-weight: 900 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  text-align: center !important;
  padding: 6px 10px !important;
  height: 28px !important;
  border: 1.5px solid var(--break-border) !important;
}

/* Occupied Class Cell */
.timetable-grid tbody td.cell-class {
  font-weight: 850;
  line-height: 1.25;
}

.cell-class-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.cell-subject-sec {
  font-size: 11.5px;
  font-weight: 900;
  letter-spacing: -0.01em;
}

.cell-mod-badge {
  font-size: 10px;
  font-weight: 800;
  opacity: 0.95;
  text-transform: uppercase;
}

/* Empty Cell */
.timetable-grid tbody td.cell-empty {
  background: #ffffff;
}

/* Footer / Legend Block */
.sheet-footer {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 11px;
  color: var(--muted);
  font-weight: 700;
  border-top: 1.5px solid var(--line);
  padding-top: 10px;
}

.legend-strip {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.legend-box {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.2);
}

/* Print Specific Rules */
@media print {
  @page {
    size: A4 landscape;
    margin: 6mm 8mm;
  }

  body {
    background: #ffffff !important;
    padding: 0 !important;
  }

  .top-toolbar {
    display: none !important;
  }

  .page-sheet-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
  }

  .timetable-sheet {
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 20px !important;
  }

  .timetable-grid {
    page-break-inside: avoid !important;
  }

  .timetable-grid tbody td {
    height: 30px !important;
    padding: 4px 4px !important;
  }

  .cell-subject-sec {
    font-size: 10px !important;
  }

  .cell-mod-badge {
    font-size: 8.5px !important;
  }
}
</style>
</head>
<body>

<!-- Top Navigation Toolbar with Cascading Modality & Shift Filters -->
<header class="top-toolbar">
  <div class="brand-title">
    <div class="brand-icon">AMIS</div>
    <div class="brand-text">
      <h1>Official Class Timetable</h1>
      <p>S.Y. 2026–2027 • Weekly Class Program</p>
    </div>
  </div>

  <div class="toolbar-controls">
    <!-- Step 1: Modality Selector -->
    <div class="filter-group">
      <span class="filter-label">Modality:</span>
      <select id="modalitySelect" class="filter-select" aria-label="Select Modality">
        <option value="F2F">🏫 Face-to-Face (F2F)</option>
        <option value="ODL">💻 Online Distance (ODL)</option>
        <option value="ALL">🌟 Show All Sections</option>
      </select>
    </div>

    <!-- Step 2: ODL Shift Selector (Visible when Modality = ODL) -->
    <div class="filter-group" id="shiftGroup" style="display: none;">
      <span class="filter-label">ODL Shift:</span>
      <select id="shiftSelect" class="filter-select" aria-label="Select ODL Shift">
        <option value="ODL1">☀️ 1st Shift (12:30 PM)</option>
        <option value="ODL2">🌙 2nd Shift (03:30 PM)</option>
        <option value="ODL_ALL">⚡ All ODL Shifts</option>
      </select>
    </div>

    <!-- Step 3: Grade / Section Selector -->
    <div class="filter-group">
      <span class="filter-label">Section:</span>
      <select id="sectionSelect" class="filter-select filter-select-section" aria-label="Select Section">
        <option value="">Loading sections...</option>
      </select>
    </div>

    <button id="btnPrint" class="btn-action btn-print" onclick="window.print()">
      🖨️ Print
    </button>
    <a href="faculty-timetable-print.html" class="btn-action btn-back">
      👨‍🏫 Faculty
    </a>
    <a href="index.html" class="btn-action btn-back">
      📋 Exams
    </a>
  </div>
</header>

<!-- Main Printable Landscape Container -->
<main class="page-sheet-container" id="sheetsContainer">
  <!-- Dynamic Timetable Sheets rendered here -->
</main>

<script>
(function() {
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"];
  let SECTIONS_DATA = [];

  const modalitySelect = document.getElementById('modalitySelect');
  const shiftGroup = document.getElementById('shiftGroup');
  const shiftSelect = document.getElementById('shiftSelect');
  const sectionSelect = document.getElementById('sectionSelect');
  const sheetsContainer = document.getElementById('sheetsContainer');

  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatTime(t) {
    if (!t) return '-';
    let s = String(t).trim();
    s = s.replace(/a\.?m\.?/gi, 'AM').replace(/p\.?m\.?/gi, 'PM');
    return s;
  }

  function getSubjectColor(subj) {
    const s = (subj || "").toLowerCase();
    if (s.includes('gmrc') || s.includes('values') || s.includes('esp') || s.includes('homeroom') || s.includes('hg')) {
      return { bg: '#dcfce7', border: '#86efac', text: '#14532d' };
    }
    if (s.includes('arabic') || s.includes("qur'an") || s.includes('quran') || s.includes('hadith') || s.includes('shaf') || s.includes('islamic')) {
      return { bg: '#f3e8ff', border: '#d8b4fe', text: '#581c87' };
    }
    if (s.includes('math') || s.includes('calculus') || s.includes('statistics') || s.includes('algebra')) {
      return { bg: '#e0f2fe', border: '#7dd3fc', text: '#0369a1' };
    }
    if (s.includes('science') || s.includes('sci') || s.includes('biology') || s.includes('chemistry') || s.includes('physics') || s.includes('earth')) {
      return { bg: '#ccfbf1', border: '#5eead4', text: '#115e59' };
    }
    if (s.includes('english') || s.includes('reading') || s.includes('oral') || s.includes('literature') || s.includes('eapp') || s.includes('circle') || s.includes('meeting') || s.includes('wrap-up')) {
      return { bg: '#fef3c7', border: '#fde047', text: '#854d0e' };
    }
    if (s.includes('filipino') || s.includes('makabansa') || s.includes('ap') || s.includes('soc.sci') || s.includes('philo') || s.includes('kompan') || s.includes('ucsp')) {
      return { bg: '#ffedd5', border: '#fdba74', text: '#9a3412' };
    }
    if (s.includes('mapeh') || s.includes('tle') || s.includes('pe') || s.includes('entrep') || s.includes('e-tech') || s.includes('cpar') || s.includes('mil')) {
      return { bg: '#fae8ff', border: '#f0abfc', text: '#86198f' };
    }
    return { bg: '#f1f5f9', border: '#cbd5e1', text: '#1e293b' };
  }

  async function init() {
    if (window.OFFICIAL_CLASS_SCHEDULES && window.OFFICIAL_CLASS_SCHEDULES.length > 0) {
      SECTIONS_DATA = window.OFFICIAL_CLASS_SCHEDULES;
    } else if (typeof OFFICIAL_CLASS_SCHEDULES !== 'undefined' && OFFICIAL_CLASS_SCHEDULES.length > 0) {
      SECTIONS_DATA = OFFICIAL_CLASS_SCHEDULES;
    } else {
      try {
        const resp = await fetch('class_schedules_data.json?v=' + Date.now());
        if (resp.ok) {
          SECTIONS_DATA = await resp.json();
        }
      } catch (e) {
        console.warn('Failed to load JSON:', e);
      }
    }

    if (!SECTIONS_DATA || SECTIONS_DATA.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b;">No class schedule data available.</div>';
      return;
    }

    // Set initial filters based on URL or defaults
    const urlParams = new URLSearchParams(window.location.search);
    let initModality = urlParams.get('modality') || 'F2F';
    let initShift = urlParams.get('shift') || 'ODL1';
    let initSec = urlParams.get('section') || 'ALL_GROUP';

    modalitySelect.value = ['F2F', 'ODL', 'ALL'].includes(initModality.toUpperCase()) ? initModality.toUpperCase() : 'F2F';
    shiftSelect.value = ['ODL1', 'ODL2', 'ODL_ALL'].includes(initShift.toUpperCase()) ? initShift.toUpperCase() : 'ODL1';

    updateShiftVisibility();
    populateSectionDropdown();

    if (initSec) {
      sectionSelect.value = initSec;
      if (!sectionSelect.value) sectionSelect.selectedIndex = 0;
    }

    renderCurrentView();

    // Event listeners
    modalitySelect.addEventListener('change', () => {
      updateShiftVisibility();
      populateSectionDropdown();
      renderCurrentView();
    });

    shiftSelect.addEventListener('change', () => {
      populateSectionDropdown();
      renderCurrentView();
    });

    sectionSelect.addEventListener('change', () => {
      renderCurrentView();
    });
  }

  function updateShiftVisibility() {
    if (modalitySelect.value === 'ODL') {
      shiftGroup.style.display = 'flex';
    } else {
      shiftGroup.style.display = 'none';
    }
  }

  function getFilteredPool() {
    const mod = modalitySelect.value;
    const shift = shiftSelect.value;

    if (mod === 'F2F') {
      return SECTIONS_DATA.filter(s => s.shift === 'F2F');
    } else if (mod === 'ODL') {
      if (shift === 'ODL1') {
        return SECTIONS_DATA.filter(s => s.shift === 'ODL - 1ST SHIFT');
      } else if (shift === 'ODL2') {
        return SECTIONS_DATA.filter(s => s.shift === 'ODL - 2ND SHIFT');
      } else {
        return SECTIONS_DATA.filter(s => s.shift.includes('ODL'));
      }
    } else {
      return SECTIONS_DATA;
    }
  }

  function populateSectionDropdown() {
    const pool = getFilteredPool();
    const mod = modalitySelect.value;
    const shift = shiftSelect.value;

    let groupTitle = "All Sections";
    if (mod === 'F2F') groupTitle = `📋 [ALL F2F] Show All ${pool.length} F2F Classes`;
    else if (mod === 'ODL') {
      if (shift === 'ODL1') groupTitle = `📋 [ALL 1ST SHIFT] Show All ${pool.length} Classes`;
      else if (shift === 'ODL2') groupTitle = `📋 [ALL 2ND SHIFT] Show All ${pool.length} Classes`;
      else groupTitle = `📋 [ALL ODL] Show All ${pool.length} ODL Classes`;
    } else {
      groupTitle = `🌟 [ALL SECTIONS] Show All ${pool.length} Classes`;
    }

    let html = `<option value="ALL_GROUP">${groupTitle}</option>`;

    pool.forEach(s => {
      const globalIdx = SECTIONS_DATA.indexOf(s);
      html += `<option value="${globalIdx}">${esc(s.section_name)}</option>`;
    });

    sectionSelect.innerHTML = html;
    sectionSelect.value = "ALL_GROUP";
  }

  function renderCurrentView() {
    const secVal = sectionSelect.value;
    const pool = getFilteredPool();

    if (secVal === 'ALL_GROUP') {
      renderMultipleSections(pool);
    } else {
      const targetSec = SECTIONS_DATA[parseInt(secVal, 10)];
      if (targetSec) {
        renderMultipleSections([targetSec]);
      } else {
        renderMultipleSections(pool);
      }
    }
  }

  function renderMultipleSections(list) {
    const todayStr = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    let fullHtml = '';

    if (!list || list.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b; font-weight:700;">No section schedules found for this selection.</div>';
      return;
    }

    list.forEach(sec => {
      fullHtml += `
        <div class="timetable-sheet">
          <div class="school-header">
            <h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>
            <h2>Official Class Timetable / Section Weekly Schedule</h2>
            <p>School Year 2026–2027 • Official Class Program</p>
          </div>

          <div class="teacher-banner">
            <span class="teacher-name-title">${esc(sec.section_name.toUpperCase())}</span>
            <span class="teacher-meta-tag">${esc(sec.department)} • ${esc(sec.grade_level)} • ${esc(sec.shift)}</span>
          </div>

          <table class="timetable-grid">
            <thead>
              <tr>
                <th class="col-time">Time</th>
                <th class="col-mins">Minutes</th>
                <th>Sunday</th>
                <th>Monday</th>
                <th>Tuesday</th>
                <th>Wednesday</th>
                <th>Thursday</th>
              </tr>
            </thead>
            <tbody>
      `;

      sec.periods.forEach(p => {
        const timeStr = formatTime(p.time);

        if (p.is_merged_all_days) {
          if (p.is_break) {
            fullHtml += `
              <tr class="row-break">
                <td class="cell-time">${esc(timeStr)}</td>
                <td class="cell-mins">${esc(p.minutes)}</td>
                <td colspan="5" class="cell-break">${esc(p.label || p.subject || 'BREAK / ASSEMBLY')}</td>
              </tr>
            `;
          } else {
            const color = getSubjectColor(p.subject || p.label);
            fullHtml += `
              <tr>
                <td class="cell-time">${esc(timeStr)}</td>
                <td class="cell-mins">${esc(p.minutes)}</td>
                <td colspan="5" class="cell-class" style="background:${color.bg}; border-color:${color.border}; color:${color.text}; text-align:center;">
                  <div class="cell-class-inner">
                    <span class="cell-subject-sec">${esc(p.subject || p.label)}</span>
                    ${p.teacher ? `<span class="cell-mod-badge" style="color:${color.text}; font-weight:800;">${esc(p.teacher)}</span>` : ''}
                    ${p.extra ? `<span style="font-size:9.5px; opacity:0.8;">${esc(p.extra)}</span>` : ''}
                  </div>
                </td>
              </tr>
            `;
          }
        } else {
          const firstDay = p.days ? p.days['Sunday'] : null;
          const isBreakRow = firstDay && firstDay.is_break;

          if (isBreakRow) {
            fullHtml += `
              <tr class="row-break">
                <td class="cell-time">${esc(timeStr)}</td>
                <td class="cell-mins">${esc(p.minutes)}</td>
                <td colspan="5" class="cell-break">${esc(firstDay.label || 'BREAK / ASSEMBLY')}</td>
              </tr>
            `;
          } else {
            fullHtml += `
              <tr>
                <td class="cell-time">${esc(timeStr)}</td>
                <td class="cell-mins">${esc(p.minutes)}</td>
            `;

            DAYS.forEach(d => {
              const cell = p.days ? p.days[d] : null;
              if (!cell) {
                fullHtml += `<td class="cell-empty"></td>`;
              } else if (cell.is_break) {
                fullHtml += `<td class="cell-break" style="font-size:11px; font-weight:800; color:#64748b; background:#f1f5f9;">${esc(cell.label)}</td>`;
              } else {
                const color = getSubjectColor(cell.subject);
                fullHtml += `
                  <td class="cell-class" style="background:${color.bg}; border-color:${color.border}; color:${color.text};">
                    <div class="cell-class-inner">
                      <span class="cell-subject-sec">${esc(cell.subject)}</span>
                      ${cell.teacher ? `<span class="cell-mod-badge" style="color:${color.text}; font-weight:800;">${esc(cell.teacher)}</span>` : ''}
                      ${cell.extra ? `<span style="font-size:9.5px; opacity:0.8;">${esc(cell.extra)}</span>` : ''}
                    </div>
                  </td>
                `;
              }
            });

            fullHtml += `</tr>`;
          }
        }
      });

      fullHtml += `
            </tbody>
          </table>

          <div class="sheet-footer">
            <div class="legend-strip">
              <span style="font-weight: 800; color: var(--ink);">Subject Keys:</span>
              <div class="legend-box"><span class="legend-color-dot" style="background:#f3e8ff; border-color:#d8b4fe;"></span> Arabic / Qur'an / Islamic</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#dcfce7; border-color:#86efac;"></span> GMRC / Values / ESP</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#e0f2fe; border-color:#7dd3fc;"></span> Math / Physics</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ccfbf1; border-color:#5eead4;"></span> Science / Biology</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef3c7; border-color:#fde047;"></span> English / Reading</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ffedd5; border-color:#fdba74;"></span> AP / Social / Filipino</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fae8ff; border-color:#f0abfc;"></span> MAPEH / TLE</div>
            </div>
            <div>
              <span>Al Munawwara Islamic School • Generated on <strong>${todayStr}</strong></span>
            </div>
          </div>
        </div>
      `;
    });

    sheetsContainer.innerHTML = fullHtml;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
</body>
</html>
"""

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/class-schedule.html', 'w', encoding='utf-8') as f:
    f.write(HTML_CONTENT)

print("Updated class-schedule.html with cascading Modality -> Shift -> Section filters!")
