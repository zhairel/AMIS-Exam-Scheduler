(function (global) {
  'use strict';

  let cachedSession = null;
  let checkedAt = 0;

  async function check(force) {
    const now = Date.now();
    if (!force && cachedSession && now - checkedAt < 30_000) return cachedSession;
    const response = await fetch('/api/admin-session', {
      credentials: 'same-origin',
      cache: 'no-store',
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) throw new Error('Unable to verify the admin session.');
    cachedSession = await response.json();
    checkedAt = now;
    return cachedSession;
  }

  async function requireAdmin(force) {
    let session;
    try {
      session = await check(force);
    } catch (_) {
      session = { authenticated: false };
    }
    if (session.authenticated) return true;
    const next = `${location.pathname}${location.search}${location.hash}`;
    location.replace(`/admin?next=${encodeURIComponent(next)}`);
    return false;
  }

  function clearCache() {
    cachedSession = null;
    checkedAt = 0;
  }

  global.AMISAdminGuard = Object.freeze({ check, requireAdmin, clearCache });
})(window);
