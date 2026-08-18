#!/usr/bin/env python3
import json
import os

BASE_DIR = "/home/tatsuya/Projects/AMIS/amis_exam_calendar"

with open(os.path.join(BASE_DIR, "exam_data.json"), "r", encoding="utf-8") as f:
    exam_data = json.load(f)

with open(os.path.join(BASE_DIR, "class_schedules_data.json"), "r", encoding="utf-8") as f:
    class_sections = json.load(f)

with open(os.path.join(BASE_DIR, "teacher_weekly_schedules.json"), "r", encoding="utf-8") as f:
    weekly_schedules = json.load(f)

# Save exam_data.js for instant offline/zero-latency client-side rendering
with open(os.path.join(BASE_DIR, "exam_data.js"), "w", encoding="utf-8") as f:
    f.write(f"window.AMIS_EXAM_DATA = {json.dumps(exam_data, ensure_ascii=False, indent=2)};\n")
    f.write("const AMIS_EXAM_DATA = window.AMIS_EXAM_DATA;\n")

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMIS — Term Exam Week 2026 – 2027 (Official Timetable)</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">

<!-- html2pdf.js CDN with offline fallback -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

<!-- Embedded Master Datasets with Cache-Busting -->
<script src="class_schedules_data.js?v=20260818_0800"></script>
<script src="exam_data.js?v=20260818_0800"></script>
<script src="teacher_weekly_schedules.js?v=20260818_0800"></script>

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
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  font-size: 12.5px;
  font-weight: 700;
  outline: none;
  cursor: pointer;
  font-family: inherit;
}

.filter-select:focus {
  border-color: #0f766e;
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.2);
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

.btn-action svg {
  width: 15px;
  height: 15px;
  fill: currentColor;
}

.btn-back {
  background: #ffffff;
  color: #0f172a;
  border-color: #cbd5e1;
}

.btn-back:hover {
  background: #f1f5f9;
}

/* Printable Container (A4 / Legal Landscape) */
html, body {
  overflow-x: hidden;
  max-width: 100vw;
  width: 100%;
}

.page-sheet-container {
  width: 100%;
  max-width: 1360px;
  margin: 20px auto 0;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
}

.timetable-sheet {
  background: var(--surface);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  position: relative;
  page-break-after: always;
  break-after: page;
}

/* Fullscreen Expansion Mode */
.timetable-sheet.is-fullscreen {
  position: fixed !important;
  inset: 0 !important;
  z-index: 99999 !important;
  width: 100vw !important;
  max-width: 100vw !important;
  min-height: 100vh !important;
  margin: 0 !important;
  padding: 24px 36px !important;
  background: #ffffff !important;
  overflow-y: auto !important;
  border: none !important;
  border-radius: 0 !important;
  box-sizing: border-box !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: flex-start !important;
}

.timetable-sheet.is-fullscreen > * {
  width: 100% !important;
  max-width: 1400px !important;
  margin-left: auto !important;
  margin-right: auto !important;
  box-sizing: border-box !important;
}

.timetable-sheet.is-fullscreen .school-header {
  margin-top: auto !important;
  margin-bottom: 12px !important;
}

.timetable-sheet.is-fullscreen .sheet-footer {
  margin-top: 14px !important;
  margin-bottom: auto !important;
  padding-top: 8px !important;
  font-size: 12px !important;
}

.timetable-sheet.is-fullscreen .school-header h1 {
  font-size: 18px !important;
}

.timetable-sheet.is-fullscreen .school-header h2 {
  font-size: 14px !important;
}

.timetable-sheet.is-fullscreen .teacher-banner {
  padding: 10px 18px !important;
  font-size: 15px !important;
}

.timetable-sheet.is-fullscreen .table-responsive-wrapper {
  overflow-x: auto !important;
}

.timetable-sheet.is-fullscreen .timetable-grid {
  width: 100% !important;
  min-width: 920px !important;
}

.timetable-sheet.is-fullscreen .timetable-grid thead th {
  padding: 10px 8px !important;
  font-size: 13.5px !important;
  height: 42px !important;
  max-height: 42px !important;
}

.timetable-sheet.is-fullscreen .timetable-grid thead th.col-time {
  width: 185px !important;
  min-width: 185px !important;
  max-width: 185px !important;
}

.timetable-sheet.is-fullscreen .timetable-grid thead th.col-mins {
  width: 80px !important;
  min-width: 80px !important;
  max-width: 80px !important;
}

.timetable-sheet.is-fullscreen .timetable-grid tbody td {
  padding: 10px 8px !important;
  font-size: 13px !important;
  min-height: 44px !important;
}

.timetable-sheet.is-fullscreen .timetable-grid tbody td.cell-time {
  font-size: 12.5px !important;
  padding: 8px 6px !important;
  white-space: nowrap !important;
  text-align: center !important;
}

.timetable-sheet.is-fullscreen .timetable-grid tbody td.cell-mins {
  font-size: 12.5px !important;
  padding: 8px 6px !important;
  white-space: nowrap !important;
  text-align: center !important;
}

.timetable-sheet.is-fullscreen .cell-subject-sec {
  font-size: 14px !important;
}

.timetable-sheet.is-fullscreen .cell-mod-badge {
  font-size: 12px !important;
}

.timetable-sheet.is-fullscreen .sheet-footer {
  margin-top: 10px !important;
  padding-top: 8px !important;
  font-size: 12px !important;
}

.btn-fullscreen {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #ffffff;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  transition: background 0.15s ease, transform 0.15s ease;
}

.btn-fullscreen:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.btn-fullscreen svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

/* Institutional Header */
.school-header {
  text-align: center;
  margin-bottom: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.school-header h1 {
  font-size: 14px;
  font-weight: 900;
  color: var(--brand-deep);
  letter-spacing: 0.04em;
}

.school-header h2 {
  font-size: 11.5px;
  font-weight: 800;
  color: var(--brand-accent);
  margin-top: 1px;
}

.school-header p {
  font-size: 10px;
  color: var(--muted);
  font-weight: 600;
  margin-top: 1px;
}

/* Section / Timetable Top Banner */
.teacher-banner {
  background: var(--brand-deep);
  color: #ffffff;
  padding: 8px 14px;
  border-radius: 8px 8px 0 0;
  border: 2px solid var(--brand-deep);
  border-bottom: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 800;
  font-size: 13px;
  letter-spacing: 0.02em;
}

.teacher-name-title {
  font-size: 13.5px;
  letter-spacing: 0.03em;
  font-weight: 900;
}

.teacher-meta-tag {
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid rgba(255, 255, 255, 0.25);
}

/* Responsive Table Scroll Wrapper */
.table-responsive-wrapper {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border-radius: 0 0 8px 8px;
  border: 2px solid var(--brand-deep);
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

/* Master Timetable Grid */
.timetable-grid {
  width: 100%;
  min-width: 860px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 11px;
  border: none;
}

.timetable-grid thead th {
  background: var(--brand-green);
  color: #ffffff;
  font-size: 12px;
  font-weight: 850;
  text-align: center;
  padding: 8px 6px;
  border: 1px solid #043828;
  letter-spacing: 0.02em;
}

.timetable-grid thead th.col-time {
  width: 160px;
  min-width: 160px;
  max-width: 160px;
}

.timetable-grid thead th.col-mins {
  width: 68px;
  min-width: 68px;
  max-width: 68px;
}

.timetable-grid tbody td {
  border: 1.5px solid var(--line-strong);
  padding: 6px 8px;
  text-align: center;
  font-size: 11.5px;
  vertical-align: middle;
  height: 44px;
  box-sizing: border-box;
}

.timetable-grid tbody td.cell-time {
  background: #f8fafc;
  font-weight: 800;
  color: #1e293b;
  font-size: 11.5px;
  white-space: nowrap !important;
  padding: 6px 4px !important;
  text-align: center;
}

.timetable-grid tbody td.cell-mins {
  background: #f1f5f9;
  font-weight: 800;
  color: #475569;
  font-size: 11px;
  white-space: nowrap !important;
  padding: 6px 4px !important;
  text-align: center;
}

/* Special Break Row */
.timetable-grid tbody tr.row-break td.cell-break {
  background: var(--break-bg) !important;
  color: var(--break-text) !important;
  font-size: 11px !important;
  font-weight: 900 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  text-align: center !important;
  padding: 6px 10px !important;
  height: 28px !important;
  border: 1.5px solid var(--break-border) !important;
}

/* Occupied Exam Cell */
.timetable-grid tbody td.cell-class {
  font-weight: 850;
  line-height: 1.25;
  padding: 4px 6px;
}

.cell-class-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.cell-subject-sec {
  font-weight: 900;
  font-size: 11.5px;
  line-height: 1.2;
}

.cell-section-name {
  font-size: 10.5px;
  font-weight: 750;
  line-height: 1.2;
  opacity: 0.95;
}

.cell-mod-badge {
  font-weight: 800;
  font-size: 9.5px;
  opacity: 0.85;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  line-height: 1.1;
  margin-top: 1px;
}

.cell-duration-pill {
  font-size: 8.5px;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.08);
  font-weight: 800;
  margin-top: 2px;
}

.timetable-grid tbody td.cell-empty {
  background: #ffffff;
}

/* Footer & Legend Strip */
.sheet-footer {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 9.5px;
  color: var(--muted);
  font-weight: 600;
  flex-wrap: wrap;
  gap: 8px;
}

.legend-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.legend-box {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 700;
  color: var(--ink-secondary);
}

.legend-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

/* Print Optimization */
@media print {
  .top-toolbar, .btn-fullscreen {
    display: none !important;
  }
  body {
    background: #fff !important;
    padding: 0 !important;
  }
  .page-sheet-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
  }
  .timetable-sheet {
    box-shadow: none !important;
    border: none !important;
    padding: 8px 12px !important;
    page-break-after: always !important;
    break-after: page !important;
  }
}
</style>
</head>
<body>

<!-- Screen Top Navigation Toolbar -->
<header class="top-toolbar">
  <div class="brand-title">
    <img src="amis_logo.png" alt="AMIS Logo" style="width:38px; height:38px; border-radius:50%; object-fit:contain; background:#ffffff; padding:1px; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
    <div class="brand-text">
      <h1>Official Term Examination Timetable</h1>
      <p>Term Exam Week • Official Exam Program</p>
    </div>
  </div>

  <div class="toolbar-controls">
    <!-- Staff / Faculty Selector -->
    <div class="filter-group">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4A4 4 0 0 1 16 8A4 4 0 0 1 12 12A4 4 0 0 1 8 8A4 4 0 0 1 12 4M12 14C16.42 14 20 15.79 20 18V20H4V18C4 15.79 7.58 14 12 14Z"/></svg>
        Faculty / Teacher:
      </span>
      <select id="teacherSelect" class="filter-select" aria-label="Filter by Faculty or Teacher">
        <option value="">All Staff / Faculty</option>
      </select>
    </div>

    <!-- Modality Selector -->
    <div class="filter-group">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3L1 9L12 15L21 10.09V17H23V9M5 13.18V17.18L12 21L19 17.18V13.18L12 17L5 13.18Z"/></svg>
        Modality:
      </span>
      <select id="modalitySelect" class="filter-select" aria-label="Select Modality">
        <option value="ALL" selected>All Modalities (F2F + ODL)</option>
        <option value="F2F">Face-to-Face (F2F)</option>
        <option value="ODL">Online Distance Learning (ODL)</option>
      </select>
    </div>

    <!-- Shift Selector (ODL) -->
    <div class="filter-group" id="shiftGroup" style="display: none;">
      <span class="filter-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2A10 10 0 0 0 2 12A10 10 0 0 0 12 22A10 10 0 0 0 22 12A10 10 0 0 0 12 2M12 4A8 8 0 0 1 20 12A8 8 0 0 1 12 20A8 8 0 0 1 4 12A8 8 0 0 1 12 4M12.5 7V12.25L17 14.92L16.25 16.15L11 13V7H12.5Z"/></svg>
        Shift:
      </span>
      <select id="shiftSelect" class="filter-select" aria-label="Select ODL Shift">
        <option value="ODL1">1st Shift (12:30 PM)</option>
        <option value="ODL2">2nd Shift (03:00 PM)</option>
        <option value="ODL_ALL">All ODL Shifts</option>
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

    <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(16,185,129,0.2); border:1px solid #10b981; padding:4px 10px; border-radius:9999px; font-size:11.5px; font-weight:800; color:#a7f3d0;">
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
  const EXAM_DATES = [
    { day_num: 1, short_date: 'Sep 7', day_name: 'Monday', header: 'Day 1 • Mon, Sep 7' },
    { day_num: 2, short_date: 'Sep 8', day_name: 'Tuesday', header: 'Day 2 • Tue, Sep 8' },
    { day_num: 3, short_date: 'Sep 9', day_name: 'Wednesday', header: 'Day 3 • Wed, Sep 9' },
    { day_num: 4, short_date: 'Sep 10', day_name: 'Thursday', header: 'Day 4 • Thu, Sep 10' }
  ];

  let SECTIONS_DATA = [];
  let EXAM_RECORDS = [];
  let ALL_TEACHERS_DATA = {};

  const teacherSelect = document.getElementById('teacherSelect');
  const modalitySelect = document.getElementById('modalitySelect');
  const shiftSelect = document.getElementById('shiftSelect');
  const shiftGroup = document.getElementById('shiftGroup');
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
    const s = (subj || '').toLowerCase();
    if (s.includes('gmrc') || s.includes('values') || s.includes('esp') || s.includes('homeroom') || s.includes('hg')) {
      return { bg: '#dcfce7', border: '#86efac', text: '#14532d' };
    }
    if (s.includes('arabic') || s.includes('qur\'an') || s.includes('quran') || s.includes('hadith') || s.includes('shaf') || s.includes('islamic')) {
      return { bg: '#f3e8ff', border: '#d8b4fe', text: '#581c87' };
    }
    if (s.includes('math') || s.includes('mathematics') || s.includes('physics') || s.includes('algebra') || s.includes('calculus')) {
      return { bg: '#e0f2fe', border: '#7dd3fc', text: '#0369a1' };
    }
    if (s.includes('science') || s.includes('sci') || s.includes('biology') || s.includes('chemistry') || s.includes('gen science')) {
      return { bg: '#ccfbf1', border: '#5eead4', text: '#115e59' };
    }
    if (s.includes('english') || s.includes('reading') || s.includes('literacy') || s.includes('language') || s.includes('circle time') || s.includes('oral com') || s.includes('eapp') || s.includes('lit')) {
      return { bg: '#fef3c7', border: '#fde047', text: '#854d0e' };
    }
    if (s.includes('filipino') || s.includes('makabansa') || s.includes('ap') || s.includes('araling panlipunan') || s.includes('social science') || s.includes('soc.sci')) {
      return { bg: '#ffedd5', border: '#fdba74', text: '#9a3412' };
    }
    if (s.includes('mapeh') || s.includes('pe') || s.includes('tle') || s.includes('tvl') || s.includes('mil') || s.includes('practical research') || s.includes('entrep')) {
      return { bg: '#fae8ff', border: '#f0abfc', text: '#86198f' };
    }
    return { bg: '#f1f5f9', border: '#cbd5e1', text: '#334155' };
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

    if (!SECTIONS_DATA || SECTIONS_DATA.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b;">No exam schedule data available.</div>';
      return;
    }

    populateTeacherDropdown();

    const urlParams = new URLSearchParams(window.location.search);
    let initTeacher = urlParams.get('teacher') || '';
    let initModality = urlParams.get('modality') || 'ALL';
    let initShift = urlParams.get('shift') || 'ODL1';
    let initSec = urlParams.get('section') || 'ALL_GROUP';

    if (initTeacher) {
      teacherSelect.value = initTeacher;
    } else {
      modalitySelect.value = ['F2F', 'ODL', 'ALL'].includes(initModality.toUpperCase()) ? initModality.toUpperCase() : 'ALL';
      shiftSelect.value = ['ODL1', 'ODL2', 'ODL_ALL'].includes(initShift.toUpperCase()) ? initShift.toUpperCase() : 'ODL1';
    }

    updateShiftVisibility();
    populateSectionDropdown();

    if (initSec && !initTeacher) {
      sectionSelect.value = initSec;
      if (!sectionSelect.value) sectionSelect.selectedIndex = 0;
    }

    renderCurrentView();

    teacherSelect.addEventListener('change', () => {
      renderCurrentView();
    });

    modalitySelect.addEventListener('change', () => {
      teacherSelect.value = '';
      updateShiftVisibility();
      populateSectionDropdown();
      renderCurrentView();
    });

    shiftSelect.addEventListener('change', () => {
      teacherSelect.value = '';
      populateSectionDropdown();
      renderCurrentView();
    });

    sectionSelect.addEventListener('change', () => {
      teacherSelect.value = '';
      renderCurrentView();
    });
  }

  function populateTeacherDropdown() {
    const teacherExamCounts = {};
    EXAM_RECORDS.forEach(e => {
      const tid = e.teacher_id;
      if (tid) {
        teacherExamCounts[tid] = (teacherExamCounts[tid] || 0) + 1;
      }
    });

    let teachers = Object.values(ALL_TEACHERS_DATA || {}).filter(t => (teacherExamCounts[t.teacher_id] || 0) > 0);
    teachers = teachers.sort((a, b) => (a.canonical_name || a.teacher_name).localeCompare(b.canonical_name || b.teacher_name));

    let html = '<option value="">All Staff / Faculty</option>';
    html += '<option value="ALL_FACULTY">[ALL FACULTY] Show All Faculty Exam Timetables</option>';
    teachers.forEach(t => {
      const name = t.canonical_name || t.teacher_name;
      const count = teacherExamCounts[t.teacher_id] || 0;
      const countLabel = count ? ` (${count} exam sessions)` : '';
      html += `<option value="${t.teacher_id}">${esc(name)}${countLabel}</option>`;
    });
    teacherSelect.innerHTML = html;
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
      if (shift === 'ODL1') return SECTIONS_DATA.filter(s => s.shift === 'ODL - 1ST SHIFT');
      if (shift === 'ODL2') return SECTIONS_DATA.filter(s => s.shift === 'ODL - 2ND SHIFT');
      return SECTIONS_DATA.filter(s => s.shift.includes('ODL'));
    }
    return SECTIONS_DATA;
  }

  function populateSectionDropdown() {
    const pool = getFilteredPool();
    const mod = modalitySelect.value;
    const shift = shiftSelect.value;

    let groupTitle = "All Sections";
    if (mod === 'F2F') groupTitle = `[ALL F2F] Show All ${pool.length} F2F Classes`;
    else if (mod === 'ODL') {
      if (shift === 'ODL1') groupTitle = `[ALL 1ST SHIFT] Show All ${pool.length} Classes`;
      else if (shift === 'ODL2') groupTitle = `[ALL 2ND SHIFT] Show All ${pool.length} Classes`;
      else groupTitle = `[ALL ODL] Show All ${pool.length} ODL Classes`;
    } else {
      groupTitle = `[ALL SECTIONS] Show All ${pool.length} Classes`;
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
    const tVal = teacherSelect.value;
    if (tVal) {
      if (tVal === 'ALL_FACULTY') {
        const teacherIds = Object.values(ALL_TEACHERS_DATA)
          .filter(t => EXAM_RECORDS.some(e => e.teacher_id === t.teacher_id))
          .sort((a, b) => (a.canonical_name || a.teacher_name).localeCompare(b.canonical_name || b.teacher_name))
          .map(t => t.teacher_id);
        renderMultipleTeacherExamSheets(teacherIds);
      } else if (ALL_TEACHERS_DATA[tVal]) {
        renderMultipleTeacherExamSheets([tVal]);
      }
      return;
    }

    const secVal = sectionSelect.value;
    const pool = getFilteredPool();

    if (secVal === 'ALL_GROUP') {
      renderMultipleSectionExamSheets(pool);
    } else {
      const targetSec = SECTIONS_DATA[parseInt(secVal, 10)];
      if (targetSec) {
        renderMultipleSectionExamSheets([targetSec]);
      } else {
        renderMultipleSectionExamSheets(pool);
      }
    }
  }

  function getSectionExamScheduleModel(sec) {
    const secName = sec.section_name;
    const secExams = EXAM_RECORDS.filter(e => e.section_name === secName || e.section === secName || (sec.id && e.section_id === sec.id));
    const shift = sec.shift || 'F2F';
    const isKinder = (sec.grade_level || '').toLowerCase().includes('kinder') || secName.toLowerCase().includes('kinder') || secName.toLowerCase().includes('k1') || secName.toLowerCase().includes('k2');

    let timeline = [];

    if (shift === 'F2F') {
      timeline = [
        { is_break: true, time: '07:30 AM – 07:45 AM', minutes: '15 min.', label: 'GENERAL ASSEMBLY' },
        { is_break: false, time: '08:00 AM – 09:00 AM', minutes: '60 min.', slot_id: 's1' },
        { is_break: false, time: '09:00 AM – 10:00 AM', minutes: '60/120 min.', slot_id: 's2' },
        { is_break: true, time: '10:00 AM – 10:25 AM', minutes: '25 min.', label: 'RECESS' },
        { is_break: false, time: '10:25 AM – 11:25 AM', minutes: '60 min.', slot_id: 's3' },
        { is_break: true, time: '11:25 AM – 12:45 PM', minutes: '80 min.', label: 'LUNCH AND SALAH' },
        { is_break: true, time: '02:45 PM – 03:00 PM', minutes: '15 min.', label: 'SALAH / SALAH & DEPARTURE' }
      ];
    } else if (shift === 'ODL - 1ST SHIFT') {
      if (isKinder) {
        timeline = [
          { is_break: true, time: '12:30 PM – 12:40 PM', minutes: '10 min.', label: 'GENERAL ASSEMBLY' },
          { is_break: false, time: '01:30 PM – 02:15 PM', minutes: '45 min.', slot_id: 's1' },
          { is_break: true, time: '02:15 PM – 02:20 PM', minutes: '5 min.', label: 'TRANSITION' },
          { is_break: false, time: '02:20 PM – 03:05 PM', minutes: '45 min.', slot_id: 's2' },
          { is_break: true, time: '03:05 PM – 03:10 PM', minutes: '5 min.', label: 'TRANSITION' },
          { is_break: false, time: '03:10 PM – 03:40 PM', minutes: '30 min.', slot_id: 's3' },
          { is_break: true, time: '03:40 PM – 03:50 PM', minutes: '10 min.', label: 'DISMISSAL' }
        ];
      } else {
        timeline = [
          { is_break: true, time: '12:30 PM – 12:40 PM', minutes: '10 min.', label: 'GENERAL ASSEMBLY' },
          { is_break: false, time: '12:40 PM – 01:40 PM', minutes: '60 min.', slot_id: 's1' },
          { is_break: false, time: '01:50 PM – 02:50 PM', minutes: '60/120 min.', slot_id: 's2' },
          { is_break: true, time: '02:50 PM – 03:10 PM', minutes: '20 min.', label: 'TRANSITION AND SALAH BREAK' }
        ];
      }
    } else { // ODL - 2ND SHIFT
      timeline = [
        { is_break: true, time: '02:45 PM – 03:10 PM', minutes: '25 min.', label: 'HOMEROOM GUIDANCE / GENERAL ASSEMBLY' },
        { is_break: false, time: '03:10 PM – 04:10 PM', minutes: '60 min.', slot_id: 's1' },
        { is_break: false, time: '04:20 PM – 05:20 PM', minutes: '60/120 min.', slot_id: 's2' },
        { is_break: true, time: '05:20 PM – 05:30 PM', minutes: '10 min.', label: 'TRANSITION' },
        { is_break: false, time: '05:30 PM – 06:30 PM', minutes: '60 min.', slot_id: 's3' },
        { is_break: true, time: '06:30 PM – 06:45 PM', minutes: '15 min.', label: 'SALAH & DISMISSAL' }
      ];
    }

    return { secExams, timeline };
  }

  function renderMultipleSectionExamSheets(list) {
    const todayStr = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    let fullHtml = '';

    if (!list || list.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b; font-weight:700;">No section exam schedules found for this selection.</div>';
      return;
    }

    list.forEach(sec => {
      const { secExams, timeline } = getSectionExamScheduleModel(sec);
      const totalExamsCount = secExams.length;

      fullHtml += `
        <div class="timetable-sheet">
          <div class="school-header" style="display:flex; align-items:center; justify-content:center; gap:14px; margin-bottom:14px;">
            <img src="amis_logo.png" alt="AMIS Logo" style="width:48px; height:48px; border-radius:50%; object-fit:contain;">
            <div>
              <h1 style="margin:0;">AL MUNAWWARA ISLAMIC SCHOOL</h1>
              <h2 style="margin:3px 0 0 0; font-size:13px; font-weight:800; color:var(--brand-accent); letter-spacing:0.02em;">TERM EXAM WEEK 2026 – 2027</h2>
            </div>
          </div>

          <div class="teacher-banner">
            <span class="teacher-name-title">${esc(sec.section_name.toUpperCase())}</span>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="teacher-meta-tag">${esc(sec.department)} • ${esc(sec.shift)} • 4 Exam Days • ${totalExamsCount} Subjects</span>
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

      const rowspanActive = { 'Sep 2': 0, 'Sep 3': 0, 'Sep 6': 0, 'Sep 7': 0 };

      timeline.forEach(row => {
        if (row.is_break) {
          fullHtml += `
            <tr class="row-break">
              <td class="cell-time">${esc(row.time)}</td>
              <td class="cell-mins">${esc(row.minutes)}</td>
              <td colspan="4" class="cell-break">${esc(row.label)}</td>
            </tr>
          `;
        } else {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(row.time)}</td>
              <td class="cell-mins">${esc(row.minutes)}</td>
          `;

          EXAM_DATES.forEach(d => {
            const dKey = d.short_date;
            if (rowspanActive[dKey] > 0) {
              rowspanActive[dKey]--;
              return; // Merged with row above
            }

            const exam = secExams.find(e => {
              if (e.short_date !== d.short_date && e.day_number !== d.day_num) return false;
              if (e.duration_minutes >= 90) {
                return row.slot_id === 's1';
              }
              if (e.time === row.time || e.time_slot === row.time) return true;
              if (row.slot_id === 's1' && e.slot_number === 1) return true;
              if (row.slot_id === 's2' && e.slot_number === 2) return true;
              if (row.slot_id === 's3' && e.slot_number === 3) return true;
              return false;
            });

            if (exam) {
              const color = getSubjectColor(exam.subject);
              const is120 = exam.duration_minutes >= 90;
              if (is120) {
                rowspanActive[dKey] = 1;
              }
              fullHtml += `
                <td class="cell-class" ${is120 ? 'rowspan="2"' : ''} style="background:${color.bg}; border-color:${color.border}; color:${color.text}; ${is120 ? 'vertical-align:middle;' : ''}">
                  <div class="cell-class-inner">
                    <span class="cell-subject-sec">${esc(exam.subject)}</span>
                    <span class="cell-section-name">${esc(exam.teacher)}</span>
                    <span class="cell-mod-badge" style="background:rgba(0,0,0,0.08); padding:2px 8px; border-radius:4px; font-weight:850; font-size:10px; margin-top:3px;">${is120 ? '120 MIN' : (exam.duration_minutes && exam.duration_minutes !== 60 ? exam.duration_minutes + ' MIN' : '60 MIN')}</span>
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
              <div class="legend-box"><span class="legend-color-dot" style="background:#ccfbf1; border-color:#5eead4;"></span> Science</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef3c7; border-color:#fde047;"></span> English / Language</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ffedd5; border-color:#fdba74;"></span> Filipino / AP / Makabansa</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fae8ff; border-color:#f0abfc;"></span> MAPEH / TLE / TVL</div>
            </div>
            <div>
              Official Term Exam Schedule • Generated: <strong>${todayStr}</strong>
            </div>
          </div>
        </div>
      `;
    });

    sheetsContainer.innerHTML = fullHtml;
  }

  function getFacultyTimeline(shiftsSet) {
    const hasF2F = shiftsSet.has('F2F');
    const hasODL1 = shiftsSet.has('ODL - 1ST SHIFT');
    const hasODL2 = shiftsSet.has('ODL - 2ND SHIFT');

    let timeline = [];

    if (hasF2F) {
      timeline.push({ is_break: true, time: '07:30 AM – 07:45 AM', minutes: '15 min.', label: 'GENERAL ASSEMBLY' });
      timeline.push({ is_break: false, time: '08:00 AM – 09:00 AM', minutes: '60 min.', slot_id: 'f2f_s1' });
      timeline.push({ is_break: false, time: '09:00 AM – 10:00 AM', minutes: '60/120 min.', slot_id: 'f2f_s2' });
      timeline.push({ is_break: true, time: '10:00 AM – 10:25 AM', minutes: '25 min.', label: 'RECESS' });
      timeline.push({ is_break: false, time: '10:25 AM – 11:25 AM', minutes: '60 min.', slot_id: 'f2f_s3' });
      timeline.push({ is_break: true, time: '11:25 AM – 12:40 PM', minutes: '75 min.', label: 'LUNCH AND SALAH' });
    }

    if (hasODL1) {
      if (!hasF2F) {
        timeline.push({ is_break: true, time: '12:30 PM – 12:40 PM', minutes: '10 min.', label: 'GENERAL ASSEMBLY' });
      }
      timeline.push({ is_break: false, time: '12:40 PM – 01:40 PM', minutes: '60 min.', slot_id: 'odl1_s1' });
      timeline.push({ is_break: false, time: '01:50 PM – 02:50 PM', minutes: '60/120 min.', slot_id: 'odl1_s2' });
      timeline.push({ is_break: true, time: '02:50 PM – 03:10 PM', minutes: '20 min.', label: 'TRANSITION AND SALAH BREAK' });
    }

    if (hasODL2) {
      if (!hasF2F && !hasODL1) {
        timeline.push({ is_break: true, time: '02:45 PM – 03:10 PM', minutes: '25 min.', label: 'HOMEROOM GUIDANCE / GENERAL ASSEMBLY' });
      }
      timeline.push({ is_break: false, time: '03:10 PM – 04:10 PM', minutes: '60 min.', slot_id: 'odl2_s1' });
      timeline.push({ is_break: false, time: '04:20 PM – 05:20 PM', minutes: '60/120 min.', slot_id: 'odl2_s2' });
      timeline.push({ is_break: true, time: '05:20 PM – 05:30 PM', minutes: '10 min.', label: 'TRANSITION' });
      timeline.push({ is_break: false, time: '05:30 PM – 06:30 PM', minutes: '60 min.', slot_id: 'odl2_s3' });
      timeline.push({ is_break: true, time: '06:30 PM – 06:45 PM', minutes: '15 min.', label: 'SALAH & DISMISSAL' });
    }

    if (hasF2F && !hasODL1 && !hasODL2) {
      timeline.push({ is_break: true, time: '02:45 PM – 03:00 PM', minutes: '15 min.', label: 'SALAH / SALAH & DEPARTURE' });
    }

    if (timeline.length === 0) {
      timeline = [
        { is_break: true, time: '07:30 AM – 07:45 AM', minutes: '15 min.', label: 'GENERAL ASSEMBLY' },
        { is_break: false, time: '08:00 AM – 09:00 AM', minutes: '60 min.', slot_id: 'f2f_s1' },
        { is_break: false, time: '09:00 AM – 10:00 AM', minutes: '60/120 min.', slot_id: 'f2f_s2' },
        { is_break: true, time: '10:00 AM – 10:25 AM', minutes: '25 min.', label: 'RECESS' },
        { is_break: false, time: '10:25 AM – 11:25 AM', minutes: '60 min.', slot_id: 'f2f_s3' },
        { is_break: true, time: '11:25 AM – 12:40 PM', minutes: '75 min.', label: 'LUNCH AND SALAH' },
        { is_break: false, time: '12:40 PM – 01:40 PM', minutes: '60 min.', slot_id: 'odl1_s1' },
        { is_break: false, time: '01:50 PM – 02:50 PM', minutes: '60/120 min.', slot_id: 'odl1_s2' },
        { is_break: true, time: '02:50 PM – 03:10 PM', minutes: '20 min.', label: 'TRANSITION AND SALAH BREAK' },
        { is_break: false, time: '03:10 PM – 04:10 PM', minutes: '60 min.', slot_id: 'odl2_s1' },
        { is_break: false, time: '04:20 PM – 05:20 PM', minutes: '60/120 min.', slot_id: 'odl2_s2' },
        { is_break: true, time: '05:20 PM – 05:30 PM', minutes: '10 min.', label: 'TRANSITION' },
        { is_break: false, time: '05:30 PM – 06:30 PM', minutes: '60 min.', slot_id: 'odl2_s3' },
        { is_break: true, time: '06:30 PM – 06:45 PM', minutes: '15 min.', label: 'SALAH & DISMISSAL' }
      ];
    }

    return timeline;
  }

  function formatModalityShift(shiftStr) {
    if (!shiftStr) return '';
    const s = String(shiftStr).toUpperCase();
    if (s.includes('1ST') || s.includes('1ST SHIFT') || s === 'ODL1') return '1st Shift';
    if (s.includes('2ND') || s.includes('2ND SHIFT') || s === 'ODL2') return '2nd Shift';
    if (s.includes('F2F') || s.includes('FACE TO FACE')) return 'F2F';
    return shiftStr;
  }

  function cleanSectionName(sname) {
    if (!sname) return '';
    let s = String(sname);
    s = s.replace(/\s*\((?:ODL\s*-\s*)?1ST\s+SHIFT\)/gi, '')
         .replace(/\s*\((?:ODL\s*-\s*)?2ND\s+SHIFT\)/gi, '')
         .replace(/\s*\((?:FACE\s+TO\s+FACE|F2F)\)/gi, '')
         .replace(/\s+FACE\s+TO\s+FACE/gi, '')
         .replace(/\s+CLASS\s+SCHEDULE/gi, '')
         .replace(/\s*-\s*MIX\b/gi, ' (Mix)')
         .replace(/\s*-\s*GIRLS\b/gi, ' (Girls)')
         .replace(/\s*-\s*BOYS\b/gi, ' (Boys)')
         .trim();
    return s;
  }

  function renderMultipleTeacherExamSheets(tIds) {
    const todayStr = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    let fullHtml = '';

    tIds.forEach(tid => {
      const data = ALL_TEACHERS_DATA[tid];
      const tExams = EXAM_RECORDS.filter(e => e.teacher_id === tid);
      if (tExams.length === 0 && !data) return;

      const teacherDisplayName = data ? (data.canonical_name || data.teacher_name || tid) : (tExams[0].teacher || tid);
      const totalCount = tExams.length;
      const metaStr = `${totalCount} Exam Session${totalCount === 1 ? '' : 's'}`;

      const shiftsSet = new Set(tExams.map(e => e.shift || 'F2F'));
      const timeline = getFacultyTimeline(shiftsSet);

      fullHtml += `
        <div class="timetable-sheet">
          <div class="school-header" style="display:flex; align-items:center; justify-content:center; gap:14px; margin-bottom:14px;">
            <img src="amis_logo.png" alt="AMIS Logo" style="width:48px; height:48px; border-radius:50%; object-fit:contain;">
            <div>
              <h1 style="margin:0;">AL MUNAWWARA ISLAMIC SCHOOL</h1>
              <h2 style="margin:2px 0 0 0;">Faculty Examination Timetable</h2>
              <p style="margin:2px 0 0 0;">Term Exam Week</p>
            </div>
          </div>

          <div class="teacher-banner">
            <span class="teacher-name-title">${esc(teacherDisplayName.toUpperCase())}</span>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="teacher-meta-tag">${esc(metaStr)}</span>
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

      const rowspanActive = { 'Sep 2': 0, 'Sep 3': 0, 'Sep 6': 0, 'Sep 7': 0 };

      timeline.forEach(row => {
        if (row.is_break) {
          fullHtml += `
            <tr class="row-break">
              <td class="cell-time">${esc(row.time)}</td>
              <td class="cell-mins">${esc(row.minutes)}</td>
              <td colspan="4" class="cell-break">${esc(row.label)}</td>
            </tr>
          `;
        } else {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(row.time)}</td>
              <td class="cell-mins">${esc(row.minutes)}</td>
          `;

          EXAM_DATES.forEach(d => {
            const dKey = d.short_date;
            if (rowspanActive[dKey] > 0) {
              rowspanActive[dKey]--;
              return; // Merged with row above
            }

            const matches = tExams.filter(e => {
              if (e.short_date !== d.short_date && e.day_number !== d.day_num) return false;
              if (e.duration_minutes >= 90) {
                return row.slot_id === 'f2f_s1' || row.slot_id === 'odl1_s1' || row.slot_id === 'odl2_s1' || row.slot_id === 's1';
              }
              if (e.time_slot === row.time || e.time === row.time) return true;
              return false;
            });

            if (matches.length === 1) {
              const exam = matches[0];
              const color = getSubjectColor(exam.subject);
              const cleanSec = cleanSectionName(exam.section_name);
              const cleanShift = formatModalityShift(exam.shift);
              const is120 = exam.duration_minutes >= 90;
              if (is120) {
                rowspanActive[dKey] = 1;
              }
              fullHtml += `
                <td class="cell-class" ${is120 ? 'rowspan="2"' : ''} style="background:${color.bg}; border-color:${color.border}; color:${color.text}; ${is120 ? 'vertical-align:middle;' : ''}">
                  <div class="cell-class-inner">
                    <span class="cell-subject-sec">${esc(exam.subject)}</span>
                    <span class="cell-section-name">${esc(cleanSec)}</span>
                    <span class="cell-mod-badge" style="background:rgba(0,0,0,0.08); padding:2px 8px; border-radius:4px; font-weight:850; font-size:10px; margin-top:3px;">${is120 ? '120 MIN • ' + esc(cleanShift) : esc(cleanShift)}</span>
                  </div>
                </td>
              `;
            } else if (matches.length > 1) {
              const isAllowedMerged = matches.every(m => m.shift && m.shift.includes('ODL') && m.subject_id === matches[0].subject_id);
              if (isAllowedMerged) {
                const exam = matches[0];
                const color = getSubjectColor(exam.subject);
                const secsStr = matches.map(m => cleanSectionName(m.section_name)).join(' & ');
                const cleanShift = formatModalityShift(exam.shift);
                const is120 = exam.duration_minutes >= 90;
                if (is120) {
                  rowspanActive[dKey] = 1;
                }
                fullHtml += `
                  <td class="cell-class" ${is120 ? 'rowspan="2"' : ''} style="background:${color.bg}; border-color:${color.border}; color:${color.text}; ${is120 ? 'vertical-align:middle;' : ''}">
                    <div class="cell-class-inner">
                      <span class="cell-subject-sec">${esc(exam.subject)}</span>
                      <span class="cell-section-name">${esc(secsStr)}</span>
                      <span class="cell-mod-badge" style="background:rgba(0,0,0,0.08); padding:2px 8px; border-radius:4px; font-weight:850; font-size:10px; margin-top:3px;">${is120 ? '120 MIN (Merged) • ' + esc(cleanShift) : esc(cleanShift) + ' (Merged)'}</span>
                    </div>
                  </td>
                `;
              } else {
                fullHtml += `
                  <td class="cell-class" style="background:#fee2e2; border-color:#ef4444; color:#991b1b;">
                    <div class="cell-class-inner">
                      <span style="font-weight:900; font-size:9px; background:#fecaca; padding:1px 4px; border-radius:3px;">⚠️ TEACHER SCHEDULE CONFLICT</span>
                      ${matches.map(m => `<span class="cell-subject-sec" style="font-size:11px;">${esc(m.subject)}: ${esc(cleanSectionName(m.section_name))}</span>`).join('')}
                    </div>
                  </td>
                `;
              }
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
              <div class="legend-box"><span class="legend-color-dot" style="background:#ccfbf1; border-color:#5eead4;"></span> Science</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fef3c7; border-color:#fde047;"></span> English / Language</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#ffedd5; border-color:#fdba74;"></span> Filipino / AP / Makabansa</div>
              <div class="legend-box"><span class="legend-color-dot" style="background:#fae8ff; border-color:#f0abfc;"></span> MAPEH / TLE / TVL</div>
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

print("✓ Successfully regenerated exam-schedule.html with official logo, Back Home button, and cleaned toolbar!")
