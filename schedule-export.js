(function () {
  'use strict';

  const SCHOOL_YEAR = 'SY_2026-2027';
  const EXPORT_SCALE = 2;

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function controlsHtml() {
    return `
      <span class="sheet-export-actions" data-html2canvas-ignore="true">
        <button type="button" class="btn-sheet-export" onclick="event.stopPropagation(); AMISScheduleExport.downloadSheet(this, 'png')" title="Download this schedule as PNG" aria-label="Download PNG">
          <span aria-hidden="true">▣</span> PNG
        </button>
        <button type="button" class="btn-sheet-export" onclick="event.stopPropagation(); AMISScheduleExport.downloadSheet(this, 'pdf')" title="Download this schedule as PDF" aria-label="Download PDF">
          <span aria-hidden="true">⇩</span> PDF
        </button>
      </span>`;
  }

  function toolbarButtonHtml() {
    return `
      <button type="button" class="btn-action btn-export-all" onclick="AMISScheduleExport.downloadVisiblePdf(this)" title="Download every schedule currently displayed as one PDF">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
        PDF All Visible
      </button>`;
  }

  function safePart(value) {
    return String(value || 'Schedule')
      .normalize('NFKD')
      .replace(/[^a-zA-Z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 90) || 'Schedule';
  }

  function sheetFilename(sheet, extension) {
    const kind = safePart(sheet.dataset.exportKind || 'Exam');
    const name = safePart(sheet.dataset.exportName || sheet.querySelector('.teacher-name-title')?.textContent);
    return `AMIS_${kind}_${name}_${SCHOOL_YEAR}.${extension}`;
  }

  function ensureLibraries(format) {
    if (typeof window.html2canvas !== 'function') {
      throw new Error('The image export library did not load. Please check your connection and refresh the page.');
    }
    if (format === 'pdf' && !(window.jspdf && window.jspdf.jsPDF)) {
      throw new Error('The PDF export library did not load. Please check your connection and refresh the page.');
    }
  }

  function setBusy(button, busy) {
    if (!button) return;
    if (busy) {
      button.dataset.originalHtml = button.innerHTML;
      button.disabled = true;
      button.classList.add('is-exporting');
      button.innerHTML = '<span class="export-spinner" aria-hidden="true"></span> Exporting…';
    } else {
      button.disabled = false;
      button.classList.remove('is-exporting');
      if (button.dataset.originalHtml) button.innerHTML = button.dataset.originalHtml;
      delete button.dataset.originalHtml;
    }
  }

  function showToast(message, isError) {
    let toast = document.getElementById('scheduleExportToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'scheduleExportToast';
      toast.className = 'schedule-export-toast';
      toast.setAttribute('role', 'status');
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.toggle('is-error', Boolean(isError));
    toast.classList.add('is-visible');
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.remove('is-visible'), isError ? 5000 : 2600);
  }

  function prepareClone(sheet) {
    const clone = sheet.cloneNode(true);
    clone.classList.remove('is-fullscreen');
    clone.querySelectorAll('.sheet-export-actions, .btn-fullscreen, .mobile-scroll-hint').forEach(node => node.remove());
    clone.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));

    const originalTable = sheet.querySelector('.timetable-grid');
    const tableWidth = originalTable ? Math.ceil(Math.max(originalTable.scrollWidth, originalTable.getBoundingClientRect().width)) : 0;
    const targetWidth = Math.ceil(Math.max(sheet.getBoundingClientRect().width, tableWidth + 32, 900));

    const stage = document.createElement('div');
    stage.className = 'schedule-export-stage';
    stage.style.width = `${targetWidth}px`;
    clone.style.width = `${targetWidth}px`;
    clone.style.maxWidth = 'none';
    clone.style.height = 'auto';
    clone.style.maxHeight = 'none';
    clone.style.margin = '0';
    clone.style.overflow = 'visible';

    const wrapper = clone.querySelector('.table-responsive-wrapper');
    if (wrapper) {
      wrapper.style.width = '100%';
      wrapper.style.maxWidth = 'none';
      wrapper.style.overflow = 'visible';
    }
    const table = clone.querySelector('.timetable-grid');
    if (table) {
      table.style.width = '100%';
      table.style.minWidth = `${tableWidth || 820}px`;
    }

    stage.appendChild(clone);
    document.body.appendChild(stage);
    return { stage, clone };
  }

  async function renderSheet(sheet) {
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    const prepared = prepareClone(sheet);
    try {
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      return await window.html2canvas(prepared.clone, {
        scale: EXPORT_SCALE,
        backgroundColor: '#ffffff',
        useCORS: true,
        logging: false,
        scrollX: 0,
        scrollY: 0,
        windowWidth: prepared.clone.scrollWidth,
        windowHeight: prepared.clone.scrollHeight
      });
    } finally {
      prepared.stage.remove();
    }
  }

  function saveBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function canvasBlob(canvas) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Could not create the PNG file.')), 'image/png');
    });
  }

  function addCanvasPage(pdf, canvas, addPage) {
    if (addPage) pdf.addPage('a4', 'landscape');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 7;
    const availableWidth = pageWidth - (margin * 2);
    const availableHeight = pageHeight - (margin * 2);
    const ratio = Math.min(availableWidth / canvas.width, availableHeight / canvas.height);
    const width = canvas.width * ratio;
    const height = canvas.height * ratio;
    const x = (pageWidth - width) / 2;
    const y = (pageHeight - height) / 2;
    pdf.addImage(canvas.toDataURL('image/jpeg', 0.96), 'JPEG', x, y, width, height, undefined, 'FAST');
  }

  async function downloadSheet(button, format) {
    const sheet = button && button.closest('.timetable-sheet');
    if (!sheet) return;
    setBusy(button, true);
    try {
      ensureLibraries(format);
      const canvas = await renderSheet(sheet);
      if (format === 'png') {
        saveBlob(await canvasBlob(canvas), sheetFilename(sheet, 'png'));
      } else {
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4', compress: true });
        addCanvasPage(pdf, canvas, false);
        pdf.save(sheetFilename(sheet, 'pdf'));
      }
      showToast(`${format.toUpperCase()} downloaded successfully.`);
    } catch (error) {
      console.error('Schedule export failed:', error);
      showToast(error.message || 'The schedule could not be exported.', true);
    } finally {
      setBusy(button, false);
    }
  }

  async function downloadVisiblePdf(button) {
    const sheets = Array.from(document.querySelectorAll('#sheetsContainer .timetable-sheet'))
      .filter(sheet => sheet.offsetParent !== null);
    if (!sheets.length) {
      showToast('No schedules are currently visible.', true);
      return;
    }

    setBusy(button, true);
    try {
      ensureLibraries('pdf');
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4', compress: true });
      for (let index = 0; index < sheets.length; index += 1) {
        showToast(`Preparing schedule ${index + 1} of ${sheets.length}…`);
        const canvas = await renderSheet(sheets[index]);
        addCanvasPage(pdf, canvas, index > 0);
      }
      const tabName = document.querySelector('.exam-tab-btn.active')?.textContent || 'Visible_Schedules';
      pdf.save(`AMIS_${safePart(tabName)}_${sheets.length}_Schedules_${SCHOOL_YEAR}.pdf`);
      showToast(`${sheets.length} schedule${sheets.length === 1 ? '' : 's'} downloaded in one PDF.`);
    } catch (error) {
      console.error('Bulk schedule export failed:', error);
      showToast(error.message || 'The schedules could not be exported.', true);
    } finally {
      setBusy(button, false);
    }
  }

  window.AMISScheduleExport = {
    controlsHtml,
    toolbarButtonHtml,
    downloadSheet,
    downloadVisiblePdf,
    escapeHtml
  };
}());
