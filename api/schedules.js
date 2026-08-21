'use strict';

const supabase = require('../server/supabase');
const schedules = require('../server/schedules');

function upstreamMessage(result, fallback) {
  const data = result && result.data;
  if (data && typeof data === 'object' && ['42P01', 'PGRST205'].includes(data.code)) {
    return 'The Supabase schedule schema is not installed. Run the AMIS migration, then retry.';
  }
  return fallback;
}

async function readAllSchedules(config, accessToken, filter) {
  const records = [];
  const pageSize = 1000;
  for (let offset = 0; ; offset += pageSize) {
    const suffix = filter ? `&${filter}` : '';
    const result = await supabase.restRequest(
      config,
      `/manual_schedules?select=*&order=day.asc,start_time.asc,teacher.asc&limit=${pageSize}&offset=${offset}${suffix}`,
      { method: 'GET', accessToken }
    );
    if (!result.ok) return result;
    const page = Array.isArray(result.data) ? result.data : [];
    records.push(...page);
    if (page.length < pageSize) return { ok: true, status: 200, data: records };
  }
}

module.exports = async function scheduleApi(request, response) {
  supabase.noStore(response);
  const config = supabase.getConfig();
  if (!config.configured) {
    return response.status(503).json({ ok: false, error: 'The Supabase schedule database is not connected.' });
  }

  if (request.method === 'GET') {
    const session = await supabase.getAdminSession(request, response).catch(() => ({ authenticated: false }));
    const id = String((request.query && request.query.id) || '').trim();
    const filter = id ? `id=eq.${encodeURIComponent(id)}` : '';
    const result = await readAllSchedules(config, session.authenticated ? session.accessToken : '', filter)
      .catch(() => ({ ok: false, status: 502, data: {} }));
    if (!result.ok) {
      return response.status(result.status >= 500 ? 502 : result.status).json({
        ok: false,
        error: upstreamMessage(result, 'Unable to load schedules from Supabase.')
      });
    }
    return response.status(200).json({ ok: true, schedules: schedules.normalizeRows(result.data) });
  }

  if (!['POST', 'PATCH', 'DELETE'].includes(request.method)) {
    response.setHeader('Allow', 'GET, POST, PATCH, DELETE');
    return response.status(405).json({ ok: false, error: 'Method not allowed.' });
  }

  const session = await supabase.getAdminSession(request, response).catch(() => ({ authenticated: false }));
  if (!session.authenticated) return response.status(401).json({ ok: false, error: 'Administrator sign-in is required.' });

  const queryId = String((request.query && request.query.id) || '').trim();
  if (request.method === 'DELETE') {
    if (!queryId) return response.status(400).json({ ok: false, error: 'A schedule ID is required.' });
    if (queryId.startsWith('official:')) {
      const result = await supabase.restRequest(config, `/manual_schedules?id=eq.${encodeURIComponent(queryId)}`, {
        method: 'PATCH',
        accessToken: session.accessToken,
        headers: { 'Content-Type': 'application/json', Prefer: 'return=representation' },
        body: JSON.stringify({ status: 'inactive' })
      }).catch(() => ({ ok: false, status: 502, data: {} }));
      if (!result.ok) return response.status(result.status >= 500 ? 502 : result.status).json({ ok: false, error: upstreamMessage(result, 'Unable to deactivate this official schedule.') });
      if (!Array.isArray(result.data) || result.data.length === 0) return response.status(404).json({ ok: false, error: 'This schedule was not found.' });
      return response.status(200).json({ ok: true, deactivated: true });
    }
    const result = await supabase.restRequest(config, `/manual_schedules?id=eq.${encodeURIComponent(queryId)}`, {
      method: 'DELETE',
      accessToken: session.accessToken,
      headers: { Prefer: 'return=representation' }
    }).catch(() => ({ ok: false, status: 502, data: {} }));
    if (!result.ok) return response.status(result.status >= 500 ? 502 : result.status).json({ ok: false, error: upstreamMessage(result, 'Unable to delete this schedule.') });
    if (!Array.isArray(result.data) || result.data.length === 0) return response.status(404).json({ ok: false, error: 'This schedule was not found.' });
    return response.status(200).json({ ok: true });
  }

  const body = supabase.readBody(request);
  const record = schedules.normalize(body, request.method === 'PATCH' ? queryId : '');
  const validationError = schedules.validate(record, true);
  if (validationError) return response.status(400).json({ ok: false, error: validationError });

  const isUpdate = request.method === 'PATCH';
  const currentResult = await readAllSchedules(config, session.accessToken, '')
    .catch(() => ({ ok: false, status: 502, data: {} }));
  if (!currentResult.ok) {
    return response.status(currentResult.status >= 500 ? 502 : currentResult.status).json({
      ok: false,
      error: upstreamMessage(currentResult, 'Unable to validate this schedule against current assignments.')
    });
  }
  const current = currentResult.data.find((item) => item.id === record.id);
  if (isUpdate && current) record.source = current.source === 'official' ? 'official' : 'manual';
  const conflicts = schedules.findBlockingConflicts(record, currentResult.data, record.id, current);
  if (conflicts.length) {
    return response.status(409).json({
      ok: false,
      conflict: true,
      error: 'This active schedule conflicts with an official or manual assignment.'
    });
  }

  const path = isUpdate
    ? `/manual_schedules?id=eq.${encodeURIComponent(record.id)}&select=*`
    : '/manual_schedules?select=*';
  const result = await supabase.restRequest(config, path, {
    method: request.method,
    accessToken: session.accessToken,
    headers: { 'Content-Type': 'application/json', Prefer: 'return=representation' },
    body: JSON.stringify(record)
  }).catch(() => ({ ok: false, status: 502, data: {} }));

  if (!result.ok) {
    const conflict = result.status === 409 || (result.data && ['23P01', '23505'].includes(result.data.code));
    return response.status(conflict ? 409 : (result.status >= 500 ? 502 : result.status)).json({
      ok: false,
      conflict,
      error: conflict ? 'This active schedule conflicts with another manual assignment.' : upstreamMessage(result, 'Unable to save this schedule.')
    });
  }
  if (!Array.isArray(result.data) || result.data.length === 0) return response.status(404).json({ ok: false, error: 'This schedule was not found.' });
  return response.status(isUpdate ? 200 : 201).json({ ok: true, schedule: schedules.normalizeRows(result.data)[0] });
};
