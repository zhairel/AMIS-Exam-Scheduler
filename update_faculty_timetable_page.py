import re

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/faculty-timetable-print.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make .page-sheet-container flex column with gap
old_sheet_css = """.page-sheet-container {
  max-width: 1400px;
  margin: 24px auto 0;
  padding: 0 20px;
}

.timetable-sheet {
  background: #ffffff;
  border: 2px solid var(--line-strong);
  border-radius: 12px;
  padding: 24px 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}"""

new_sheet_css = """.page-sheet-container {
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
}"""

if old_sheet_css in content:
    content = content.replace(old_sheet_css, new_sheet_css)

# Update HTML structure of .page-sheet-container to hold dynamic sheets
old_main = """<main class="page-sheet-container">
  <div class="timetable-sheet" id="printArea">
    
    <!-- School Title Header -->
    <div class="school-header">
      <h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>
      <h2>Faculty Timetable / Teacher Weekly Schedule</h2>
      <p>School Year 2026–2027 • Official Class Program</p>
    </div>

    <!-- Teacher Name Banner -->
    <div class="teacher-banner">
      <span class="teacher-name-title" id="dispTeacherName">USTADHA SILFAH</span>
      <span class="teacher-meta-tag" id="dispTeacherMeta">23 Total Weekly Classes</span>
    </div>

    <!-- Master Weekly Schedule Table -->
    <table class="timetable-grid" id="timetableGrid">
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
      <tbody id="gridBody">
        <!-- Rendered dynamically -->
      </tbody>
    </table>

    <!-- Sheet Footer & Legend -->
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
        <span>Al Munawwara Islamic School • Generated on <strong id="currentDateStr"></strong></span>
      </div>
    </div>

  </div>
</main>"""

new_main = """<main class="page-sheet-container" id="sheetsContainer">
  <!-- Dynamic Faculty Sheets rendered here -->
</main>"""

if old_main in content:
    content = content.replace(old_main, new_main)

# Replace JS logic to support ALL_FACULTY
js_replacement = """
<script>
(function() {
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"];
  let ALL_TEACHERS_DATA = {};
  let currentTeacher = "Ustadha Silfah";

  const teacherSelect = document.getElementById('teacherSelect');
  const sheetsContainer = document.getElementById('sheetsContainer');

  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  async function loadData() {
    if (window.AMIS_TEACHER_WEEKLY_SCHEDULES) {
      ALL_TEACHERS_DATA = window.AMIS_TEACHER_WEEKLY_SCHEDULES;
    } else {
      try {
        const resp = await fetch('teacher_weekly_schedules.json?v=' + Date.now());
        if (resp.ok) {
          ALL_TEACHERS_DATA = await resp.json();
        }
      } catch (e) {
        console.warn('Failed to load JSON:', e);
      }
    }

    const teacherNames = Object.keys(ALL_TEACHERS_DATA).sort((a, b) => a.localeCompare(b));
    if (teacherNames.length === 0) {
      sheetsContainer.innerHTML = '<div style="text-align:center; padding:50px; color:#64748b;">No schedule data available.</div>';
      return;
    }

    // Populate Select Box
    let selectHtml = `<option value="ALL_FACULTY">🌟 [ALL FACULTY] Show & Print All ${teacherNames.length} Teachers</option><optgroup label="── Individual Faculty ──">`;
    selectHtml += teacherNames.map(t => `<option value="${esc(t)}">${esc(t)}</option>`).join('');
    selectHtml += `</optgroup>`;
    teacherSelect.innerHTML = selectHtml;

    // Check URL Param ?teacher=...
    const urlParams = new URLSearchParams(window.location.search);
    const paramTeacher = urlParams.get('teacher');
    if (paramTeacher && ['all', 'all_faculty'].includes(paramTeacher.toLowerCase())) {
      currentTeacher = "ALL_FACULTY";
    } else if (paramTeacher && ALL_TEACHERS_DATA[paramTeacher]) {
      currentTeacher = paramTeacher;
    } else if (paramTeacher) {
      const match = teacherNames.find(t => t.toLowerCase() === paramTeacher.toLowerCase());
      if (match) currentTeacher = match;
    }

    teacherSelect.value = currentTeacher;
    renderSelectedTeachers(currentTeacher);

    teacherSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      currentTeacher = val;
      const newUrl = new URL(window.location);
      if (val === 'ALL_FACULTY') newUrl.searchParams.set('teacher', 'all');
      else newUrl.searchParams.set('teacher', currentTeacher);
      window.history.replaceState({}, '', newUrl);
      renderSelectedTeachers(currentTeacher);
    });
  }

  function renderSelectedTeachers(val) {
    if (val === 'ALL_FACULTY') {
      const teacherNames = Object.keys(ALL_TEACHERS_DATA).sort((a, b) => a.localeCompare(b));
      renderMultipleTeacherSheets(teacherNames);
    } else {
      if (ALL_TEACHERS_DATA[val]) {
        renderMultipleTeacherSheets([val]);
      }
    }
  }

  function renderMultipleTeacherSheets(tNames) {
    const todayStr = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    let fullHtml = '';

    tNames.forEach(tName => {
      const data = ALL_TEACHERS_DATA[tName];
      if (!data) return;

      const metaStr = `${data.total_classes} Assigned Class${data.total_classes === 1 ? '' : 'es'} (${(data.subjects || []).join(', ')})`;

      fullHtml += `
        <div class="timetable-sheet">
          <div class="school-header">
            <h1>AL MUNAWWARA ISLAMIC SCHOOL</h1>
            <h2>Faculty Timetable / Teacher Weekly Schedule</h2>
            <p>School Year 2026–2027 • Official Class Program</p>
          </div>

          <div class="teacher-banner">
            <span class="teacher-name-title">${esc(tName.toUpperCase())}</span>
            <span class="teacher-meta-tag">${esc(metaStr)}</span>
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

      const rows = data.rows || [];
      rows.forEach(r => {
        if (r.is_break) {
          fullHtml += `
            <tr class="row-break">
              <td class="cell-time">${esc(r.time)}</td>
              <td class="cell-mins">${r.minutes}m</td>
              <td colspan="5" class="cell-break">${esc(r.break_title)}</td>
            </tr>
          `;
        } else {
          fullHtml += `
            <tr>
              <td class="cell-time">${esc(r.time)}</td>
              <td class="cell-mins">${r.minutes}m</td>
          `;

          for (const d of DAYS) {
            const cell = r.days ? r.days[d] : null;
            if (cell && cell.occupied) {
              const color = cell.color || { bg: '#f1f5f9', border: '#cbd5e1', text: '#1e293b' };
              fullHtml += `
                <td class="cell-class" style="background:${color.bg}; border-color:${color.border}; color:${color.text};">
                  <div class="cell-class-inner">
                    <span class="cell-subject-sec">${esc(cell.label)}</span>
                    <span class="cell-mod-badge">${esc(cell.modality)}</span>
                  </div>
                </td>
              `;
            } else {
              fullHtml += `<td class="cell-empty"></td>`;
            }
          }

          fullHtml += `</tr>`;
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

  window.exportToPDF = function() {
    window.print();
  };

  document.addEventListener('DOMContentLoaded', loadData);
})();
</script>
"""

# Replace the script block at the end
content = re.sub(r'<script>.*?</script>', js_replacement.strip(), content, flags=re.DOTALL)

with open('/home/tatsuya/Projects/AMIS/amis_exam_calendar/faculty-timetable-print.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated faculty-timetable-print.html to support ALL FACULTY batch view & print!")
