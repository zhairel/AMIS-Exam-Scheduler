'use strict';

const supabase = require('../server/supabase');
const schedules = require('../server/schedules');
const scheduleLocks = require('../server/schedule-locks');

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];

function clean(value, maxLength = 120) {
  return String(value == null ? '' : value).trim().slice(0, maxLength);
}

function idFilter(ids) {
  return ids.map((id) => encodeURIComponent(id)).join(',');
}

function key(value) {
  return clean(value).toLowerCase();
}

function identity(row, idField, nameField) {
  return key(row[idField] || row[nameField]);
}

function sameMergeContent(rows) {
  const first = rows[0];
  return rows.every((row) => identity(row, 'section_id', 'section') === identity(first, 'section_id', 'section')
    && row.start_time === first.start_time
    && row.end_time === first.end_time
    && key(row.subject) === key(first.subject)
    && identity(row, 'teacher_id', 'teacher') === identity(first, 'teacher_id', 'teacher')
    && key(row.schedule_type) === key(first.schedule_type)
    && key(row.status) === key(first.status));
}

module.exports = async function scheduleMergeApi(request, response) {
  supabase.noStore(response);
  if (request.method !== 'PATCH') {
    response.setHeader('Allow', 'PATCH');
    return response.status(405).json({ ok: false, error: 'Method not allowed.' });
  }

  const config = supabase.getConfig();
  if (!config.configured) return response.status(503).json({ ok: false, error: 'The Supabase schedule database is not connected.' });
  const session = await supabase.getAdminSession(request, response).catch(() => ({ authenticated: false }));
  if (!session.authenticated) return response.status(401).json({ ok: false, error: 'Administrator sign-in is required.' });

  const body = supabase.readBody(request);
  const ids = Array.from(new Set((Array.isArray(body.ids) ? body.ids : []).map((id) => clean(id, 100)).filter(Boolean)));
  const mergeGroup = clean(body.merge_group);
  if (!ids.length || ids.length > DAYS.length) return response.status(400).json({ ok: false, error: 'Select between one and five schedule cells.' });
  if (mergeGroup && ids.length < 2) return response.status(400).json({ ok: false, error: 'Select at least two cells to merge.' });

  const filter = idFilter(ids);
  const current = await supabase.restRequest(config, `/manual_schedules?select=*&id=in.(${filter})`, { method: 'GET', accessToken: session.accessToken })
    .catch(() => ({ ok: false, status: 502, data: {} }));
  if (!current.ok) return response.status(current.status >= 500 ? 502 : current.status).json({ ok: false, error: 'Unable to load the selected schedule cells.' });
  const rows = schedules.normalizeRows(current.data);
  if (rows.length !== ids.length) return response.status(404).json({ ok: false, error: 'One or more selected schedule cells no longer exist.' });

  const sections = [];
  rows.forEach((row) => {
    if (!sections.some((item) => key(item.section_id || item.section) === key(row.section_id || row.section))) sections.push(row);
  });
  for (const row of sections) {
    const lock = await scheduleLocks.findLock(config, session.accessToken, row.section, row.section_id)
      .catch(() => ({ ok: false, status: 502 }));
    if (!lock.ok) return response.status(lock.status >= 500 ? 502 : lock.status).json({ ok: false, error: 'Unable to verify the schedule lock.' });
    if (lock.data) return response.status(423).json({ ok: false, locked: true, error: `${row.section} is locked after review. Unlock it before merging or unmerging cells.` });
  }

  if (mergeGroup) {
    if (!sameMergeContent(rows)) return response.status(409).json({ ok: false, error: 'Selected cells must have the same subject/event, teacher, section, time, type, and status.' });
    const indexes = rows.map((row) => DAYS.indexOf(row.day)).sort((left, right) => left - right);
    if (indexes.some((index) => index < 0) || indexes.some((index, position) => position && index !== indexes[position - 1] + 1)) {
      return response.status(409).json({ ok: false, error: 'Selected days must be next to each other.' });
    }
  }

  const result = await supabase.restRequest(config, `/manual_schedules?id=in.(${filter})&select=*`, {
    method: 'PATCH',
    accessToken: session.accessToken,
    headers: { 'Content-Type': 'application/json', Prefer: 'return=representation' },
    body: JSON.stringify({ merge_group: mergeGroup })
  }).catch(() => ({ ok: false, status: 502, data: {} }));

  if (!result.ok) {
    const missingColumn = result.data && ['PGRST204', '42703'].includes(result.data.code);
    return response.status(missingColumn ? 503 : (result.status >= 500 ? 502 : result.status)).json({
      ok: false,
      error: missingColumn ? 'Cell merging is not installed in Supabase. Run migration 004, then retry.' : 'Unable to update the selected cells.'
    });
  }
  return response.status(200).json({ ok: true, schedules: schedules.normalizeRows(result.data) });
};
