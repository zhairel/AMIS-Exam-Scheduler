'use strict';

const supabase = require('../server/supabase');

module.exports = async function adminSession(request, response) {
  supabase.noStore(response);
  if (request.method !== 'GET') {
    response.setHeader('Allow', 'GET');
    return response.status(405).json({ authenticated: false });
  }
  const session = await supabase.getAdminSession(request, response).catch(() => ({ authenticated: false, configured: supabase.getConfig().configured }));
  return response.status(200).json({
    authenticated: session.authenticated,
    configured: session.configured,
    provider: session.configured ? 'supabase' : null,
    role: session.authenticated ? 'admin' : null
  });
};
