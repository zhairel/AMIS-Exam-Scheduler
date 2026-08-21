'use strict';

const supabase = require('../server/supabase');

module.exports = async function adminLogin(request, response) {
  supabase.noStore(response);
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ ok: false, error: 'Method not allowed.' });
  }

  const config = supabase.getConfig();
  if (!config.configured) {
    return response.status(503).json({
      ok: false,
      error: 'Supabase is not connected. Add the project URL and publishable key in Vercel, then redeploy.'
    });
  }

  const body = supabase.readBody(request);
  const result = await supabase.signIn(config, body.username, body.password).catch(() => ({ ok: false, status: 502 }));
  if (!result.ok) {
    await new Promise((resolve) => setTimeout(resolve, 350));
    if (result.status === 403) {
      return response.status(403).json({ ok: false, error: 'This account is not authorized to manage AMIS schedules.' });
    }
    if (result.status >= 500) {
      return response.status(502).json({ ok: false, error: 'Unable to reach Supabase Auth. Try again shortly.' });
    }
    return response.status(401).json({ ok: false, error: 'Invalid username or password.' });
  }

  response.setHeader('Set-Cookie', supabase.sessionCookies(result.session));
  return response.status(200).json({ ok: true, role: 'admin' });
};
