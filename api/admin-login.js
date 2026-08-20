'use strict';

const auth = require('../server/admin-auth');

module.exports = async function adminLogin(request, response) {
  auth.noStore(response);
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ ok: false, error: 'Method not allowed.' });
  }

  const config = auth.getConfig();
  if (!config.configured) {
    return response.status(503).json({
      ok: false,
      error: 'Admin access is not configured. Set the AMIS admin credentials and session secret in Vercel.'
    });
  }

  const credentials = auth.readCredentials(request);
  const validUsername = credentials.username && auth.safeEqual(credentials.username.toLowerCase(), config.username.toLowerCase());
  const validPassword = credentials.password && auth.safeEqual(credentials.password, config.password);
  if (!validUsername || !validPassword) {
    await new Promise((resolve) => setTimeout(resolve, 350));
    return response.status(401).json({ ok: false, error: 'Invalid username or password.' });
  }

  response.setHeader('Set-Cookie', auth.sessionCookie(auth.createSessionToken(config.secret)));
  return response.status(200).json({ ok: true, role: 'admin' });
};
