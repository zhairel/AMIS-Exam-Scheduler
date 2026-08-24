'use strict';

const supabase = require('../server/supabase');
const locks = require('../server/schedule-locks');

module.exports = async function scheduleLocksApi(request, response) {
  supabase.noStore(response);
  if (!['GET', 'PATCH'].includes(request.method)) {
    response.setHeader('Allow', 'GET, PATCH');
    return response.status(405).json({ ok: false, error: 'Method not allowed.' });
  }

  const config = supabase.getConfig();
  if (!config.configured) return response.status(503).json({ ok: false, error: 'The Supabase schedule database is not connected.' });
  const session = await supabase.getAdminSession(request, response).catch(() => ({ authenticated: false }));
  if (!session.authenticated) return response.status(401).json({ ok: false, error: 'Administrator sign-in is required.' });

  if (request.method === 'GET') {
    const result = await locks.listLocks(config, session.accessToken).catch(() => ({ ok: false, status: 502 }));
    if (!result.ok) return response.status(result.status >= 500 ? 502 : result.status).json({ ok: false, error: 'Unable to load schedule locks.' });
    return response.status(200).json({ ok: true, locks: result.data });
  }

  const body = supabase.readBody(request);
  const locked = body.locked === true;
  const result = await locks.setLock(config, session.accessToken, body, locked).catch(() => ({ ok: false, status: 502, data: {} }));
  if (!result.ok) {
    return response.status(result.status >= 500 ? 502 : result.status).json({
      ok: false,
      error: (result.data && result.data.message) || 'Unable to update this schedule lock.'
    });
  }
  return response.status(200).json({ ok: true, locked, lock: result.data });
};
