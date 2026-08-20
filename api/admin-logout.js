'use strict';

const auth = require('../server/admin-auth');

module.exports = function adminLogout(request, response) {
  auth.noStore(response);
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ ok: false });
  }
  response.setHeader('Set-Cookie', auth.expiredSessionCookie());
  return response.status(200).json({ ok: true });
};
