'use strict';

const auth = require('../server/admin-auth');

module.exports = function adminSession(request, response) {
  auth.noStore(response);
  if (request.method !== 'GET') {
    response.setHeader('Allow', 'GET');
    return response.status(405).json({ authenticated: false });
  }
  const config = auth.getConfig();
  const authenticated = auth.hasAdminSession(request);
  return response.status(200).json({
    authenticated,
    configured: config.configured,
    role: authenticated ? 'admin' : null
  });
};
