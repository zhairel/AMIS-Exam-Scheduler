'use strict';

const supabase = require('../server/supabase');

module.exports = async function adminLogout(request, response) {
  supabase.noStore(response);
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ ok: false });
  }
  const config = supabase.getConfig();
  const cookies = supabase.parseCookies(request);
  if (config.configured) {
    await supabase.signOut(config, cookies[supabase.ACCESS_COOKIE]).catch(() => {});
  }
  response.setHeader('Set-Cookie', supabase.expiredSessionCookies());
  return response.status(200).json({ ok: true });
};
