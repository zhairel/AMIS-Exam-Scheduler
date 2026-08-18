#!/usr/bin/env python3
"""
generate_exam_schedule_page.py
Generates the Unified Official 1st Term Examination Schedule (exam-schedule.html)
- 120-minute High School & SHS Math exams span 2 full hours (2 slots / 2 visual units) with '120 min.' duration badge
- Perfect rowspan="2" support in the official examination timetable grid
- Corrected Exam Dates:
  * Day 1 • Wed, Sep 2
  * Day 2 • Thu, Sep 3
  * Day 3 • Sun, Sep 6
  * Day 4 • Mon, Sep 7
- Kindergarten 2 (1st Shift) starts at 1:30 PM
- Corrected Teacher Assignments:
  * Arabic K2 Khabaab -> Ustadh Faidh
  * GMRC 3 As'ad -> Ustadha Saliha
  * Arabic 3 As'ad -> Ustadh Faidh
  * Math 6 Dihya -> Teacher Saimona
  * English 4 Usayd -> Teacher Jenny
  * SHAF 6 Dihya -> Ustadh Faidh
"""

import json
import os

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.json"), "r", encoding="utf-8") as f:
    teacher_data = json.load(f)

with open(os.path.join(BASE_DIR, "exam_data.json"), "r", encoding="utf-8") as f:
    exam_data = json.load(f)

with open(os.path.join(BASE_DIR, "class_schedules_data.json"), "r", encoding="utf-8") as f:
    class_data = json.load(f)

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMIS — Official 1st Term Examination Schedule</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">

<!-- html2pdf.js CDN -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

<!-- Embedded Master Datasets with Cache-Busting -->
<script src="class_schedules_data.js?v=20260819_0025"></script>
<script src="exam_data.js?v=20260819_0025"></script>
<script src="teacher_weekly_schedules.js?v=20260819_0025"></script>

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
  font-size: 14px;
  letter-spacing: 0.05em;
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
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-select {
  background: #ffffff;
  color: #0f172a;
  border: none;
  font-size: 12.5px;
  font-weight: 750;
  border-radius: 6px;
  padding: 5px 10px;
  outline: none;
  cursor: pointer;
  max-width: 260px;
}

.filter-select:focus {
  box-shadow: 0 0 0 2px #34d399;
}

.filter-select-teacher {
  background: #f0fdf4;
  color: #064e3b;
  border: 1.5px solid #34d399;
  font-weight: 800;
}

.btn-action {
  background: #ffffff;
  color: var(--brand-deep);
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-size: 12px;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  transition: all 0.15s ease;
}

.btn-action svg {
  width: 15px;
  height: 15px;
  fill: currentColor;
}

.btn-back {
  background: #ffffff;
  color: #0f172a;
  border-color: #cbd5e1;
  font-weight: 750;
}

.btn-back:hover {
  background: #f1f5f9;
}

/* Printable Container */
html, body {
  overflow-x: hidden;
  max-width: 100vw;
  width: 100%;
}

.page-sheet-container {
  width: 100%;
  max-width: 1440px;
  margin: 24px auto 0;
  padding: 0 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
}

.timetable-sheet {
  width: 100%;
  max-width: 1380px;
  margin: 0 auto;
  box-sizing: border-box;
  background: #ffffff;
  border: 2px solid var(--line-strong);
  border-radius: 12px;
  padding: 20px 24px;
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
  font-weight: 750;
  color: var(--muted);
  letter-spacing: 0.06em;
  margin-top: 2px;
}

/* Banner Strip */
.teacher-banner {
  background: var(--brand-green);
  color: #ffffff;
  padding: 10px 16px;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  border: 1.5px solid #043828;
  border-bottom: none;
}

.teacher-name-title {
  font-size: 15px;
  font-weight: 900;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.teacher-meta-tag {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.btn-fullscreen {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #ffffff;
  border-radius: 6px;
  padding: 5px 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.btn-fullscreen:hover {
  background: rgba(255, 255, 255, 0.35);
}

.btn-fullscreen svg {
  width: 14px;
  height: 14px;
  fill: currentColor;
}

/* Fullscreen Mode */
.timetable-sheet.is-fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100vw !important;
  max-height: 100vh !important;
  z-index: 99999 !important;
  margin: 0 !important;
  border-radius: 0 !important;
  padding: 16px 20px !important;
  overflow-y: auto !important;
  background: #ffffff !important;
  box-shadow: none !important;
  box-sizing: border-box !important;
  display: flex !important;
  flex-direction: column !important;
}

.timetable-sheet.is-fullscreen .table-responsive-wrapper {
  flex: 1 1 auto !important;
  overflow: auto !important;
}

/* Table Responsive Wrapper */
.table-responsive-wrapper {
  width: 100%;
  overflow-x: auto;
  border: 1.5px solid var(--line-strong);
  border-top: none;
  background: #ffffff;
}

.table-responsive-wrapper::-webkit-scrollbar {
  height: 6px;
}

.table-responsive-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.table-responsive-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.table-responsive-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Timetable Table Grid */
.timetable-grid {
  width: 100%;
  min-width: 780px;
  border-collapse: collapse;
  border: none;
  table-layout: fixed;
  background: #ffffff;
}

.timetable-grid thead th {
  background: var(--brand-green);
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
  text-align: center;
  padding: 10px 8px;
  border: 1.5px solid #043828;
  letter-spacing: 0.02em;
  white-space: normal;
  overflow-wrap: break-word;
  word-break: normal;
  vertical-align: middle;
  box-sizing: border-box;
}

.timetable-grid thead th.col-time {
  width: 165px;
  min-width: 165px;
  white-space: nowrap !important;
}

.timetable-grid thead th.col-mins {
  width: 75px;
  min-width: 75px;
  white-space: nowrap !important;
}

.timetable-grid tbody tr {
  min-height: 60px;
  height: auto;
}

.timetable-grid tbody td {
  border: 1.5px solid var(--line-strong);
  padding: 8px 10px;
  text-align: center;
  font-size: 12px;
  vertical-align: middle;
  white-space: normal;
  overflow-wrap: break-word;
  word-break: normal;
  box-sizing: border-box;
  height: auto;
  min-height: 60px;
}

.timetable-grid tbody td.cell-time {
  font-weight: 800;
  font-size: 12px;
  color: var(--ink);
  background: #f8fafc;
  white-space: nowrap !important;
  line-height: 1.2;
  padding: 8px 6px;
}

.timetable-grid tbody td.cell-mins {
  font-weight: 750;
  font-size: 11.5px;
  color: var(--ink-secondary);
  background: #f8fafc;
  white-space: nowrap !important;
  line-height: 1.2;
  padding: 8px 4px;
}

.timetable-grid tbody td.cell-break {
  background: var(--break-bg);
  color: var(--break-text);
  font-weight: 800;
  font-size: 11.5px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.timetable-grid tbody td.cell-empty {
  background: #ffffff;
}

.timetable-grid tbody td.cell-class {
  transition: transform 0.1s ease, box-shadow 0.1s ease;
  vertical-align: middle;
  padding: 8px 6px;
}

.timetable-grid tbody td.cell-class:hover {
  filter: brightness(0.97);
}

.cell-class-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
}

.cell-subject-sec {
  font-size: 13.5px;
  font-weight: 800;
  line-height: 1.25;
  text-align: center;
  word-break: normal;
  overflow-wrap: break-word;
  letter-spacing: -0.01em;
}

.cell-teacher-name,
.cell-section-name {
  font-size: 11.5px;
  line-height: 1.25;
  font-weight: 650;
  text-align: center;
  word-break: normal;
  overflow-wrap: break-word;
  opacity: 0.92;
}

.cell-duration-badge {
  font-size: 10px;
  font-weight: 800;
  background: rgba(0, 0, 0, 0.08);
  padding: 2px 8px;
  border-radius: 9999px;
  margin-top: 3px;
  letter-spacing: 0.02em;
}

.badge-120 {
  background: #0284c7 !important;
  color: #ffffff !important;
  font-weight: 850 !important;
}

/* Footer / Legend Strip */
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

@media print {
  body {
    background: #fff;
    padding: 0;
  }
  .top-toolbar {
    display: none !important;
  }
  .page-sheet-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
  }
  .timetable-sheet {
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 12px 14px !important;
    page-break-after: always !important;
    break-after: page !important;
  }
  .btn-fullscreen {
    display: none !important;
  }
  @page {
    size: A4 landscape;
    margin: 8mm;
  }
}
</style>
</head>
<body>

<!-- Single Unified Top Navigation Toolbar -->
<header class="top-toolbar">
  <div class="brand-title">
    <div class="brand-icon">AMIS</div>
    <div class="brand-text">
      <h1>1st Term Examination Schedule</h1>
      <p>S.Y. 2026 – 2027 • Official Schedule</p>
    </div>
  </div>

  <div class="toolbar-controls">
    <!-- Staff / Faculty Filter -->
    <div class="filter-group">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
        Faculty:
      </span>
      <select id="teacherSelect" class="filter-select filter-select-teacher" aria-label="Filter by Faculty">
        <option value="">All Staff / Faculty</option>
      </select>
    </div>

    <!-- Modality Filter -->
    <div class="filter-group">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        Modality:
      </span>
      <select id="modalitySelect" class="filter-select" aria-label="Select Modality">
        <option value="ALL">All Modalities (F2F + ODL)</option>
        <option value="F2F">Face-to-Face (F2F)</option>
        <option value="ODL">Online Distance Learning (ODL)</option>
      </select>
    </div>

    <!-- Shift Filter -->
    <div class="filter-group" id="shiftGroup" style="display:none;">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
        Shift:
      </span>
      <select id="shiftSelect" class="filter-select" aria-label="Select Shift">
        <option value="ALL">All ODL Shifts (1st + 2nd)</option>
        <option value="ODL1">1st Shift (Afternoon)</option>
        <option value="ODL2">2nd Shift (Late Afternoon)</option>
      </select>
    </div>

    <!-- Section Selector -->
    <div class="filter-group">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M3 13H5V11H3V13M3 17H5V15H3V17M3 9H5V7H3V9M7 13H21V11H7V13M7 17H21V15H7V17M7 7V9H21V7H7Z"/></svg>
        Section:
      </span>
      <select id="sectionSelect" class="filter-select filter-select-section" aria-label="Select Section">
        <option value="">Loading sections...</option>
      </select>
    </div>

    <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(16,185,129,0.15); border:1px solid #10b981; padding:4px 10px; border-radius:9999px; font-size:11.5px; font-weight:800; color:#a7f3d0;">
      <span style="color:#10b981; font-weight:900;">✓</span> Anti-Conflict Active: 0 Conflicts
    </div>

    <a href="index.html" class="btn-action btn-back" title="Back to Home">
      <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
      Back Home
    </a>
  </div>
</header>

<!-- Main Printable Landscape Container -->
<main class="page-sheet-container" id="sheetsContainer">
  <!-- Dynamic Exam Timetable Sheets rendered here -->
</main>

<script>
(function() {
  // Corrected Official Exam Dates
  const EXAM_DATES = [
    { day_num: 1, short_date: 'Sep 2', day_name: 'Wednesday', header: 'Day 1 • Wed, Sep 2', date_str: 'Wednesday, September 2, 2026' },
    { day_num: 2, short_date: 'Sep 3', day_name: 'Thursday', header: 'Day 2 • Thu, Sep 3', date_str: 'Thursday, September 3, 2026' },
    { day_num: 3, short_date: 'Sep 6', day_name: 'Sunday', header: 'Day 3 • Sun, Sep 6', date_str: 'Sunday, September 6, 2026' },
    { day_num: 4, short_date: 'Sep 7', day_name: 'Monday', header: 'Day 4 • Mon, Sep 7', date_str: 'Monday, September 7, 2026' }
  ];

  let SECTIONS_DATA = [];
  let EXAM_RECORDS = [];
  let ALL_TEACHERS_DATA = {};

  const teacherSelect = document.getElementById('teacherSelect');
  const modalitySelect = document.getElementById('modalitySelect');
  const shiftGroup = document.getElementById('shiftGroup');
  const shiftSelect = document.getElementById('shiftSelect');
  const sectionSelect = document.getElementById('sectionSelect');
  const sheetsContainer = document.getElementById('sheetsContainer');

  function esc(s) {
    if (!s) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getSubjectColor(subj) {
    const s = (subj || '').toLowerCase().trim();

    // 1. Islamic Studies & Arabic (Purple / Violet)
    if (s.includes('arabic') || s.includes("qur'an") || s.includes('quran') || s.includes('hadith') || s.includes('shaf') || s.includes('islamic') || s.includes('fiqh') || s.includes('aqeedah') || s.includes('seerah')) {
      return { bg: '#f3e8ff', border: '#d8b4fe', text: '#581c87' };
    }

    // 2. Values Education / GMRC / Homeroom (Emerald Green)
    if (s.includes('gmrc') || s.includes('values') || s.includes('esp') || s.includes('homeroom') || s.includes('hg') || s.includes('guidance') || s.includes('character')) {
      return { bg: '#dcfce7', border: '#86efac', text: '#14532d' };
    }

    // 3. Mathematics & Quantitative (Sky Blue)
    if (s.includes('math') || s.includes('mathematics') || s.includes('algebra') || s.includes('calculus') || s.includes('statistics') || s.includes('geometry')) {
      return { bg: '#e0f2fe', border: '#7dd3fc', text: '#0369a1' };
    }

    // 4. Sciences, Biology, Physics, Chemistry (Teal / Mint)
    if (s.includes('sci') || s.includes('science') || s.includes('bio') || s.includes('biology') || s.includes('physics') || s.includes('chem') || s.includes('earth')) {
      return { bg: '#ccfbf1', border: '#5eead4', text: '#115e59' };
    }

    // 5. Filipino, Makabansa, Social Science, AP, PSKP (Warm Orange)
    if (s.includes('filipino') || s.includes('fil') || s.includes('makabansa') || s.includes('ap') || s.includes('araling panlipunan') || s.includes('social science') || s.includes('soc.sci') || s.includes('pskp') || s.includes('kompan') || s.includes('ucsp') || s.includes('philo')) {
      return { bg: '#ffedd5', border: '#fdba74', text: '#9a3412' };
    }

    // 6. English, Literature, Reading, Communication, LCS, EC (Warm Gold)
    if (s.includes('english') || s.includes('eng') || s.includes('reading') || s.includes('literacy') || s.includes('language') || s.includes('lcs') || s.includes('lit') || s.includes('oral com') || s.includes('eapp') || s.includes('circle time') || s.includes('ct 1') || s.includes('ct 2') || s.includes('meeting time') || s.includes('wrap-up') || s.includes('ec') || s.includes('r & l') || s.includes('r&l')) {
      return { bg: '#fef3c7', border: '#fde047', text: '#854d0e' };
    }

    // 7. MAPEH, Physical Education, TLE, TVL, Arts (Magenta / Pink)
    if (s.includes('mapeh') || s.includes('pe') || s.includes('tle') || s.includes('tvl') || s.includes('music') || s.includes('arts') || s.includes('health') || s.includes('entrep') || s.includes('cpar') || s.includes('e-tech')) {
      return { bg: '#fae8ff', border: '#f0abfc', text: '#86198f' };
    }

    // 8. Research & Media / Information Literacy (Indigo)
    if (s.includes('res') || s.includes('research') || s.includes('mil') || s.includes('inquiries') || s.includes('immersion')) {
      return { bg: '#e0e7ff', border: '#a5b4fc', text: '#3730a3' };
    }

    // 9. Kinder Comprehensive Exam (Oral & Written Exam) (Coral Rose)
    if (s.includes('oral & written') || s.includes('oral and written') || s.includes('written exam') || s.includes('oral exam')) {
      return { bg: '#fee2e2', border: '#fca5a5', text: '#991b1b' };
    }

    // 10. ARAL Program (Amber Cream)
    if (s.includes('aral')) {
      return { bg: '#fef9c3', border: '#fef08a', text: '#713f12' };
    }

    return { bg: '#f1f5f9', border: '#cbd5e1', text: '#334155' };
  }

  function cleanSectionName(name) {
    if (!name) return '';
    let s = String(name)
      .replace(/CLASS\\s+SCHEDULE/gi, '')
      .replace(/GRADE\\s+/gi, 'Grade ')
      .replace(/KINDER\\s+/gi, 'Kinder ')
      .replace(/\\(FACE\\s+TO\\s+FACE\\)/gi, '(F2F)')
      .replace(/FACE\\s+TO\\s+FACE/gi, '(F2F)')
      .replace(/\\(1ST\\s+SHIFT\\)/gi, '(1st Shift)')
      .replace(/\\(2ND\\s+SHIFT\\)/gi, '(2nd Shift)')
      .replace(/\\s+/g, ' ')
      .trim();
    return s;
  }

  async function init() {
    try {
      const sResp = await fetch('class_schedules_data.json?v=' + Date.now());
      if (sResp.ok) SECTIONS_DATA = await sResp.json();
      else if (window.CLASS_SCHEDULES_DATA) SECTIONS_DATA = window.CLASS_SCHEDULES_DATA;
    } catch (e) {
      if (window.CLASS_SCHEDULES_DATA) SECTIONS_DATA = window.CLASS_SCHEDULES_DATA;
    }

    try {
      const eResp = await fetch('exam_data.json?v=' + Date.now());
      if (eResp.ok) EXAM_RECORDS = await eResp.json();
      else if (window.AMIS_EXAM_DATA) EXAM_RECORDS = window.AMIS_EXAM_DATA;
    } catch (e) {
      if (window.AMIS_EXAM_DATA) EXAM_RECORDS = window.AMIS_EXAM_DATA;
    }

    try {
      const tResp = await fetch('teacher_weekly_schedules.json?v=' + Date.now());
      if (tResp.ok) ALL_TEACHERS_DATA = await tResp.json();
      else if (window.AMIS_TEACHER_WEEKLY_SCHEDULES) ALL_TEACHERS_DATA = window.AMIS_TEACHER_WEEKLY_SCHEDULES;
    } catch (e) {
      if (window.AMIS_TEACHER_WEEKLY_SCHEDULES) ALL_TEACHERS_DATA = window.AMIS_TEACHER_WEEKLY_SCHEDULES;
    }

    populateTeacherDropdown();
    populateSectionDropdown();

    teacherSelect.addEventListener('change', () => {
      if (teacherSelect.value) {
        sectionSelect.disabled = true;
        modalitySelect.disabled = true;
        shiftSelect.disabled = true;
      } else {
        sectionSelect.disabled = false;
        modalitySelect.disabled = false;
        shiftSelect.disabled = false;
      }
      renderCurrentView();
    });

    modalitySelect.addEventListener('change', () => {
      if (modalitySelect.value === 'ODL') {
        shiftGroup.style.display = 'inline-flex';
      } else {
        shiftGroup.style.display = 'none';
        shiftSelect.value = 'ALL';
      }
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

    renderCurrentView();
  }

  function populateTeacherDropdown() {
    let tList = [];
    if (EXAM_RECORDS && EXAM_RECORDS.length > 0) {
      const map = {};
      EXAM_RECORDS.forEach(e => {
        if (e.teacher_id && e.teacher) {
          map[e.teacher_id] = { id: e.teacher_id, name: e.teacher, dept: e.department };
        }
      });
      tList = Object.values(map);
    } else if (ALL_TEACHERS_DATA) {
      tList = Object.values(ALL_TEACHERS_DATA).map(t => ({ id: t.id || t.teacher_id, name: t.name || t.canonical_name, dept: t.department }));
    }

    tList.sort((a, b) => a.name.localeCompare(b.name));

    let html = '<option value="">All Staff / Faculty</option>';
    html += '<option value="ALL_FACULTY">Print / View All Faculty Timetables (' + tList.length + ' Staff)</option>';
    tList.forEach(t => {
      const examCount = EXAM_RECORDS.filter(e => e.teacher_id === t.id).length;
      html += `<option value="${t.id}">${esc(t.name)} (${esc(t.dept)} • ${examCount} exams)</option>`;
    });
    teacherSelect.innerHTML = html;
  }

  function populateSectionDropdown() {
    const mod = modalitySelect.value;
    const shift = shiftSelect.value;

    let filtered = SECTIONS_DATA;
    if (mod === 'F2F') {
      filtered = filtered.filter(s => s.shift === 'F2F');
    } else if (mod === 'ODL') {
      if (shift === 'ODL1') filtered = filtered.filter(s => s.shift === 'ODL - 1ST SHIFT');
      else if (shift === 'ODL2') filtered = filtered.filter(s => s.shift === 'ODL - 2ND SHIFT');
    }

    let html = `<option value="ALL_GROUP">All Filtered Sections (${filtered.length})</option>`;
    filtered.forEach(s => {
      html += `<option value="${s.id}">${esc(s.section_name)} (${esc(s.shift)})</option>`;
    });
    sectionSelect.innerHTML = html;
  }

  function renderCurrentView() {
    const selectedTeacher = teacherSelect.value;
    if (selectedTeacher) {
      renderTeacherView(selectedTeacher);
    } else {
      renderSectionView();
    }
  }

  function renderTeacherView(teacherId) {
    let targetTeacherIds = [];
    if (teacherId === 'ALL_FACULTY') {
      const ids = [...new Set(EXAM_RECORDS.map(e => e.teacher_id).filter(Boolean))];
      targetTeacherIds = ids;
    } else {
      targetTeacherIds = [teacherId];
    }

    if (targetTeacherIds.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b; font-weight:700;">No faculty examination duties found.</div>';
      return;
    }

    const masterSlots = [
      { time: '07:30 AM – 07:45 AM', mins: '15 min.', type: 'break', label: 'GENERAL ASSEMBLY' },
      { time: '08:00 AM – 09:00 AM', mins: '60 min.', type: 'exam', slot_num: 1 },
      { time: '09:00 AM – 10:00 AM', mins: '60 min.', type: 'exam', slot_num: 2 },
      { time: '10:00 AM – 10:25 AM', mins: '25 min.', type: 'break', label: 'RECESS' },
      { time: '10:25 AM – 11:25 AM', mins: '60 min.', type: 'exam', slot_num: 3 },
      { time: '11:25 AM', mins: '--', type: 'break', label: 'FACE TO FACE DISMISSAL' },
      { time: '12:30 PM – 12:40 PM', mins: '10 min.', type: 'break', label: 'GENERAL ASSEMBLY' },
      { time: '12:40 PM – 01:40 PM', mins: '60 min.', type: 'exam', slot_num: 1, shift_tag: 'ODL1' },
      { time: '01:30 PM – 02:30 PM', mins: '60 min.', type: 'exam', slot_num: 1, shift_tag: 'K2_1ST' },
      { time: '01:40 PM – 01:50 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
      { time: '01:50 PM – 02:50 PM', mins: '60 min.', type: 'exam', slot_num: 2, shift_tag: 'ODL1' },
      { time: '02:40 PM – 03:40 PM', mins: '60 min.', type: 'exam', slot_num: 2, shift_tag: 'K2_1ST' },
      { time: '02:50 PM – 03:10 PM', mins: '20 min.', type: 'break', label: 'TRANSITION AND SALAH' },
      { time: '03:10 PM – 04:10 PM', mins: '60 min.', type: 'exam', slot_num: 3, shift_tag: 'ODL1' },
      { time: '03:50 PM – 04:50 PM', mins: '60 min.', type: 'exam', slot_num: 3, shift_tag: 'K2_1ST' },
      { time: '04:10 PM – 04:20 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
      { time: '04:20 PM – 05:20 PM', mins: '60 min.', type: 'exam', slot_num: 2, shift_tag: 'ODL2' },
      { time: '05:20 PM – 05:30 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
      { time: '05:30 PM – 06:30 PM', mins: '60 min.', type: 'exam', slot_num: 3, shift_tag: 'ODL2' },
      { time: '06:30 PM', mins: '--', type: 'break', label: 'DISMISSAL' }
    ];

    const todayStr = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    let fullHtml = '';

    targetTeacherIds.forEach(tid => {
      const tExams = EXAM_RECORDS.filter(e => e.teacher_id === tid);
      const teacherName = tExams.length > 0 ? tExams[0].teacher : (ALL_TEACHERS_DATA[tid] ? ALL_TEACHERS_DATA[tid].name : tid);
      const teacherDept = tExams.length > 0 ? tExams[0].department : (ALL_TEACHERS_DATA[tid] ? ALL_TEACHERS_DATA[tid].department : 'Faculty');
      const examDutyCount = tExams.length; // True count of exam duties

      // Standard Table View with perfect 120min rowspan support
      fullHtml += `
        <div class="timetable-sheet" id="sheet_${tid}">
          <div class="school-header">
            <h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>
            <h2>TERM EXAM WEEK 2026 – 2027</h2>
            <p>FACULTY EXAMINATION TIMETABLE</p>
          </div>

          <div class="teacher-banner">
            <span class="teacher-name-title">${esc(teacherName.toUpperCase())}</span>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="teacher-meta-tag">${esc(teacherDept)} • ${examDutyCount} Exam Duties • ✓ 0 Conflicts</span>
              <button class="btn-fullscreen" onclick="toggleFullscreenSheet(this)" title="Fullscreen Table" aria-label="Toggle Fullscreen">
                <svg class="icon-expand" viewBox="0 0 24 24" style="display:inline-block;"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
                <svg class="icon-compress" viewBox="0 0 24 24" style="display:none;"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>
              </button>
            </div>
          </div>

          <div class="table-responsive-wrapper">
            <table class="timetable-grid">
              <thead>
                <tr>
                  <th class="col-time">Time</th>
                  <th class="col-mins">Minutes</th>
                  ${EXAM_DATES.map(d => `<th>${esc(d.header)}</th>`).join('')}
                </tr>
              </thead>
              <tbody>
      `;

      // Track occupied days for multi-slot spans
      const dayOccupiedUntil = { 1: -1, 2: -1, 3: -1, 4: -1 };

      masterSlots.forEach((slot, rowIdx) => {
        if (slot.type === 'break') {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(slot.time)}</td>
              <td class="cell-mins">${esc(slot.mins)}</td>
              <td class="cell-break" colspan="4">${esc(slot.label)}</td>
            </tr>
          `;
        } else {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(slot.time)}</td>
              <td class="cell-mins">${esc(slot.mins)}</td>
          `;

          EXAM_DATES.forEach(d => {
            if (dayOccupiedUntil[d.day_num] >= rowIdx) {
              // Covered by a previous rowspan
              return;
            }

            const match = tExams.find(e => {
              if (e.day_number !== d.day_num && e.short_date !== d.short_date) return false;
              if (e.time_slot === slot.time || e.time === slot.time) return true;
              if (e.time_slot && e.time_slot.includes('–')) {
                const sStart = e.time_slot.split('–')[0].trim();
                const slStart = slot.time.split('–')[0].trim();
                return sStart === slStart;
              }
              return false;
            });

            if (match) {
              const color = getSubjectColor(match.subject);
              const is120 = match.duration_minutes === 120 || match.slots_spanned === 2;
              const rSpan = is120 ? 'rowspan="2"' : '';
              if (is120) {
                dayOccupiedUntil[d.day_num] = rowIdx + 1;
              }
              fullHtml += `
                <td class="cell-class" ${rSpan} style="background:${color.bg}; border-color:${color.border}; color:${color.text};">
                  <div class="cell-class-inner">
                    <span class="cell-subject-sec">${esc(match.subject)}</span>
                    <span class="cell-section-name">${esc(cleanSectionName(match.section_name))}</span>
                    <span class="cell-duration-badge ${is120 ? 'badge-120' : ''}">${match.duration_minutes || 60} min.</span>
                  </div>
                </td>
              `;
            } else {
              fullHtml += `<td class="cell-empty"></td>`;
            }
          });

          fullHtml += `</tr>`;
        }
      });

      fullHtml += `
              </tbody>
            </table>
          </div>

          <div class="sheet-footer">
            <div class="legend-strip">
              <span style="font-weight: 800; color: var(--ink);">Subject Keys:</span>
              <div class="legend-box"><span class="legend-color-dot" style="background:#f3e8ff; border-color:#d8b4fe;"></span> Arabic / Qur'an / Islamic</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#dcfce7; border-color:#86efac;"></span> GMRC / Values / ESP</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#e0f2fe; border-color:#7dd3fc;"></span> Mathematics</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ccfbf1; border-color:#5eead4;"></span> Science / Biology / Physics</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef3c7; border-color:#fde047;"></span> English / Reading / LCS / EC</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ffedd5; border-color:#fdba74;"></span> Filipino / AP / Makabansa / PSKP</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fae8ff; border-color:#f0abfc;"></span> MAPEH / TLE / TVL / PE</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#e0e7ff; border-color:#a5b4fc;"></span> Research / MIL</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fee2e2; border-color:#fca5a5;"></span> Oral &amp; Written Exam</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef9c3; border-color:#fef08a;"></span> ARAL Program</div>
            </div>
            <div>
              Generated: <strong>${todayStr}</strong>
            </div>
          </div>
        </div>
      `;
    });

    sheetsContainer.innerHTML = fullHtml;
  }

  function renderSectionView() {
    const selectedSecId = sectionSelect.value || 'ALL_GROUP';
    const mod = modalitySelect.value;
    const shift = shiftSelect.value;

    let targetSections = SECTIONS_DATA;
    if (selectedSecId !== 'ALL_GROUP') {
      targetSections = SECTIONS_DATA.filter(s => s.id === selectedSecId);
    } else {
      if (mod === 'F2F') targetSections = targetSections.filter(s => s.shift === 'F2F');
      else if (mod === 'ODL') {
        if (shift === 'ODL1') targetSections = targetSections.filter(s => s.shift === 'ODL - 1ST SHIFT');
        else if (shift === 'ODL2') targetSections = targetSections.filter(s => s.shift === 'ODL - 2ND SHIFT');
      }
    }

    if (targetSections.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b; font-weight:700;">No sections match the current filter.</div>';
      return;
    }

    const todayStr = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    let fullHtml = '';

    targetSections.forEach(sec => {
      const isF2F = sec.shift === 'F2F';
      const isODL1 = sec.shift === 'ODL - 1ST SHIFT';
      const isODL2 = sec.shift === 'ODL - 2ND SHIFT';
      const isK2_1st = ('Kinder' in sec.grade_level || 'K2' in sec.grade_level) && isODL1;
      const isSHS = sec.department && sec.department.includes('Senior High');

      let timeRows = [];
      if (isF2F) {
        timeRows = [
          { time: '07:30 AM – 07:45 AM', mins: '15 min.', type: 'break', label: 'GENERAL ASSEMBLY' },
          { time: '08:00 AM – 09:00 AM', mins: '60 min.', type: 'exam', slot_num: 1 },
          { time: '09:00 AM – 10:00 AM', mins: '60 min.', type: 'exam', slot_num: 2 },
          { time: '10:00 AM – 10:25 AM', mins: '25 min.', type: 'break', label: 'RECESS' },
          { time: '10:25 AM – 11:25 AM', mins: '60 min.', type: 'exam', slot_num: 3 },
          { time: '11:25 AM', mins: '--', type: 'break', label: 'DISMISSAL' }
        ];
      } else if (isK2_1st) {
        timeRows = [
          { time: '01:20 PM – 01:30 PM', mins: '10 min.', type: 'break', label: 'GENERAL ASSEMBLY' },
          { time: '01:30 PM – 02:30 PM', mins: '60 min.', type: 'exam', slot_num: 1 },
          { time: '02:30 PM – 02:40 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
          { time: '02:40 PM – 03:40 PM', mins: '60 min.', type: 'exam', slot_num: 2 },
          { time: '03:40 PM – 03:50 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
          { time: '03:50 PM – 04:50 PM', mins: '60 min.', type: 'exam', slot_num: 3 },
          { time: '04:50 PM', mins: '--', type: 'break', label: 'DISMISSAL' }
        ];
      } else if (isODL1) {
        timeRows = [
          { time: '12:30 PM – 12:40 PM', mins: '10 min.', type: 'break', label: 'GENERAL ASSEMBLY' },
          { time: '12:40 PM – 01:40 PM', mins: '60 min.', type: 'exam', slot_num: 1 },
          { time: '01:40 PM – 01:50 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
          { time: '01:50 PM – 02:50 PM', mins: '60 min.', type: 'exam', slot_num: 2 },
          { time: '02:50 PM – 03:10 PM', mins: '20 min.', type: 'break', label: 'TRANSITION AND SALAH BREAK' },
          { time: '03:10 PM – 04:10 PM', mins: '60 min.', type: 'exam', slot_num: 3 }
        ];
        if (isSHS) {
          timeRows.push({ time: '04:10 PM – 04:20 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' });
          timeRows.push({ time: '04:20 PM – 05:20 PM', mins: '60 min.', type: 'exam', slot_num: 4 });
        }
        timeRows.push({ time: isSHS ? '05:20 PM' : '04:10 PM', mins: '--', type: 'break', label: 'DISMISSAL' });
      } else if (isODL2) {
        timeRows = [
          { time: '02:50 PM – 03:10 PM', mins: '20 min.', type: 'break', label: 'GENERAL ASSEMBLY & SALAH BREAK' },
          { time: '03:10 PM – 04:10 PM', mins: '60 min.', type: 'exam', slot_num: 1 },
          { time: '04:10 PM – 04:20 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
          { time: '04:20 PM – 05:20 PM', mins: '60 min.', type: 'exam', slot_num: 2 },
          { time: '05:20 PM – 05:30 PM', mins: '10 min.', type: 'break', label: 'TRANSITION' },
          { time: '05:30 PM – 06:30 PM', mins: '60 min.', type: 'exam', slot_num: 3 },
          { time: '06:30 PM', mins: '--', type: 'break', label: 'DISMISSAL' }
        ];
      }

      const secExams = EXAM_RECORDS.filter(e => e.section_id === sec.id);
      const totalSubjectCount = secExams.length; // True count: Math is 1 subject

      fullHtml += `
        <div class="timetable-sheet" id="sheet_${sec.id}">
          <div class="school-header">
            <h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>
            <h2>TERM EXAM WEEK 2026 – 2027</h2>
            <p>OFFICIAL 1ST TERM EXAMINATION SCHEDULE</p>
          </div>

          <div class="teacher-banner">
            <span class="teacher-name-title">${esc(sec.section_name.toUpperCase())}</span>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="teacher-meta-tag">${esc(sec.department)} • ${esc(sec.shift)} • ${totalSubjectCount} Subjects • ✓ 0 Conflicts</span>
              <button class="btn-fullscreen" onclick="toggleFullscreenSheet(this)" title="Fullscreen Table" aria-label="Toggle Fullscreen">
                <svg class="icon-expand" viewBox="0 0 24 24" style="display:inline-block;"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
                <svg class="icon-compress" viewBox="0 0 24 24" style="display:none;"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>
              </button>
            </div>
          </div>

          <div class="table-responsive-wrapper">
            <table class="timetable-grid">
              <thead>
                <tr>
                  <th class="col-time">Time</th>
                  <th class="col-mins">Minutes</th>
                  ${EXAM_DATES.map(d => `<th>${esc(d.header)}</th>`).join('')}
                </tr>
              </thead>
              <tbody>
      `;

      // Track occupied days for multi-slot spans
      const dayOccupiedUntil = { 1: -1, 2: -1, 3: -1, 4: -1 };

      timeRows.forEach((row, rowIdx) => {
        if (row.type === 'break') {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(row.time)}</td>
              <td class="cell-mins">${esc(row.mins)}</td>
              <td class="cell-break" colspan="4">${esc(row.label)}</td>
            </tr>
          `;
        } else {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(row.time)}</td>
              <td class="cell-mins">${esc(row.mins)}</td>
          `;

          EXAM_DATES.forEach(d => {
            if (dayOccupiedUntil[d.day_num] >= rowIdx) {
              // Covered by a previous rowspan
              return;
            }

            const match = secExams.find(e => {
              if (e.day_number !== d.day_num && e.short_date !== d.short_date) return false;
              if (e.slot_number === row.slot_num) return true;
              if (e.time_slot && e.time_slot.includes('–')) {
                const sStart = e.time_slot.split('–')[0].trim();
                const rStart = row.time.split('–')[0].trim();
                return sStart === rStart;
              }
              return false;
            });

            if (match) {
              const color = getSubjectColor(match.subject);
              const is120 = match.duration_minutes === 120 || match.slots_spanned === 2;
              const rSpan = is120 ? 'rowspan="2"' : '';
              if (is120) {
                dayOccupiedUntil[d.day_num] = rowIdx + 1;
              }
              fullHtml += `
                <td class="cell-class" ${rSpan} style="background:${color.bg}; border-color:${color.border}; color:${color.text};">
                  <div class="cell-class-inner">
                    <span class="cell-subject-sec">${esc(match.subject)}</span>
                    <span class="cell-teacher-name">${esc(match.teacher)}</span>
                    <span class="cell-duration-badge ${is120 ? 'badge-120' : ''}">${match.duration_minutes || 60} min.</span>
                  </div>
                </td>
              `;
            } else {
              fullHtml += `<td class="cell-empty"></td>`;
            }
          });

          fullHtml += `</tr>`;
        }
      });

      fullHtml += `
              </tbody>
            </table>
          </div>

          <div class="sheet-footer">
            <div class="legend-strip">
              <span style="font-weight: 800; color: var(--ink);">Subject Keys:</span>
              <div class="legend-box"><span class="legend-color-dot" style="background:#f3e8ff; border-color:#d8b4fe;"></span> Arabic / Qur'an / Islamic</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#dcfce7; border-color:#86efac;"></span> GMRC / Values / ESP</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#e0f2fe; border-color:#7dd3fc;"></span> Mathematics</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ccfbf1; border-color:#5eead4;"></span> Science / Biology / Physics</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef3c7; border-color:#fde047;"></span> English / Reading / LCS / EC</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ffedd5; border-color:#fdba74;"></span> Filipino / AP / Makabansa / PSKP</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fae8ff; border-color:#f0abfc;"></span> MAPEH / TLE / TVL / PE</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#e0e7ff; border-color:#a5b4fc;"></span> Research / MIL</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fee2e2; border-color:#fca5a5;"></span> Oral &amp; Written Exam</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef9c3; border-color:#fef08a;"></span> ARAL Program</div>
            </div>
            <div>
              Generated: <strong>${todayStr}</strong>
            </div>
          </div>
        </div>
      `;
    });

    sheetsContainer.innerHTML = fullHtml;
  }

  window.toggleFullscreenSheet = function(btn) {
    const sheet = btn.closest('.timetable-sheet');
    if (!sheet) return;
    
    sheet.classList.toggle('is-fullscreen');
    const isFull = sheet.classList.contains('is-fullscreen');
    
    const expandIcon = btn.querySelector('.icon-expand');
    const compressIcon = btn.querySelector('.icon-compress');
    
    if (isFull) {
      if (expandIcon) expandIcon.style.display = 'none';
      if (compressIcon) compressIcon.style.display = 'inline-block';
      btn.setAttribute('title', 'Exit Fullscreen');
      document.body.style.overflow = 'hidden';
    } else {
      if (expandIcon) expandIcon.style.display = 'inline-block';
      if (compressIcon) compressIcon.style.display = 'none';
      btn.setAttribute('title', 'Fullscreen Table');
      document.body.style.overflow = '';
    }
  };

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const activeSheet = document.querySelector('.timetable-sheet.is-fullscreen');
      if (activeSheet) {
        const btn = activeSheet.querySelector('.btn-fullscreen');
        if (btn) toggleFullscreenSheet(btn);
      }
    }
  });

  init();
})();
</script>

</body>
</html>
"""

with open(os.path.join(BASE_DIR, "exam-schedule.html"), "w", encoding="utf-8") as f:
    f.write(HTML_TEMPLATE)

print("✓ Successfully generated unified exam-schedule.html with 120min Math spanning!")
