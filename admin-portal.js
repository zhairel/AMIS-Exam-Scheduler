(function () {
  'use strict';

  const loading = document.getElementById('sessionLoading');
  const loginPanel = document.getElementById('loginPanel');
  const portalPanel = document.getElementById('portalPanel');
  const form = document.getElementById('adminLoginForm');
  const username = document.getElementById('adminUsername');
  const password = document.getElementById('adminPassword');
  const errorBox = document.getElementById('loginError');
  const loginButton = document.getElementById('loginButton');

  function show(panel) {
    [loading, loginPanel, portalPanel].forEach((item) => { item.hidden = item !== panel; });
  }

  function setError(message) {
    errorBox.textContent = message || '';
    errorBox.hidden = !message;
  }

  function safeNextUrl() {
    const next = new URLSearchParams(location.search).get('next') || '';
    return next.startsWith('/') && !next.startsWith('//') ? next : '';
  }

  async function readSession() {
    const response = await fetch('/api/admin-session', { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to check the admin session.');
    return response.json();
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    setError('');
    loginButton.disabled = true;
    loginButton.textContent = 'Signing In…';
    try {
      const response = await fetch('/api/admin-login', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.value, password: password.value })
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || !result.ok) throw new Error(result.error || 'Unable to sign in.');
      password.value = '';
      const next = safeNextUrl();
      if (next) location.replace(next);
      else show(portalPanel);
    } catch (error) {
      setError(error.message || 'Unable to sign in.');
      password.focus();
    } finally {
      loginButton.disabled = false;
      loginButton.textContent = 'Sign In Securely';
    }
  });

  document.getElementById('togglePassword').addEventListener('click', (event) => {
    const visible = password.type === 'text';
    password.type = visible ? 'password' : 'text';
    event.currentTarget.textContent = visible ? 'Show' : 'Hide';
    event.currentTarget.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
  });

  document.getElementById('logoutButton').addEventListener('click', async () => {
    await fetch('/api/admin-logout', { method: 'POST', credentials: 'same-origin' }).catch(() => {});
    show(loginPanel);
    password.focus();
  });

  readSession().then((session) => {
    if (session.authenticated) {
      const next = safeNextUrl();
      if (next) location.replace(next);
      else show(portalPanel);
    } else {
      show(loginPanel);
      if (!session.configured) setError('Admin access is not configured on this deployment. Add the required environment variables in Vercel, then redeploy.');
    }
  }).catch((error) => {
    show(loginPanel);
    setError(error.message);
  });
})();
