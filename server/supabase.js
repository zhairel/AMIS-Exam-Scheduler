'use strict';

const ACCESS_COOKIE = '__Host-amis_sb_access';
const REFRESH_COOKIE = '__Host-amis_sb_refresh';
const SESSION_TTL_SECONDS = 8 * 60 * 60;

function clean(value) {
  return String(value == null ? '' : value).trim();
}

function getConfig() {
  const url = clean(
    process.env.SUPABASE_URL ||
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    process.env.VITE_SUPABASE_URL
  ).replace(/\/$/, '');
  const key = clean(
    process.env.SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.VITE_SUPABASE_ANON_KEY
  );
  const emailDomain = clean(process.env.AMIS_ADMIN_EMAIL_DOMAIN || 'amis.local').toLowerCase();
  const configured = /^https:\/\/[^/]+$/i.test(url) && key.length >= 20 && /^[a-z0-9.-]+$/i.test(emailDomain);
  return { url, key, emailDomain, configured };
}

function noStore(response) {
  response.setHeader('Cache-Control', 'private, no-store, max-age=0');
  response.setHeader('Content-Type', 'application/json; charset=utf-8');
}

function parseCookies(request) {
  const result = {};
  String(request.headers.cookie || '').split(';').forEach((part) => {
    const separator = part.indexOf('=');
    if (separator < 0) return;
    const name = part.slice(0, separator).trim();
    const value = part.slice(separator + 1).trim();
    if (!name) return;
    try { result[name] = decodeURIComponent(value); } catch (_) { result[name] = value; }
  });
  return result;
}

function readBody(request) {
  if (request.body && typeof request.body === 'object') return request.body;
  if (typeof request.body !== 'string' || !request.body) return {};
  try { return JSON.parse(request.body); } catch (_) { return {}; }
}

function loginEmail(identifier, emailDomain) {
  const username = clean(identifier).toLowerCase();
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(username)) return username;
  if (!/^[a-z0-9._-]{1,64}$/.test(username)) return '';
  return `${username}@${emailDomain}`;
}

function cookie(name, value, maxAge) {
  return `${name}=${encodeURIComponent(value)}; Max-Age=${maxAge}; Path=/; HttpOnly; Secure; SameSite=Strict`;
}

function sessionCookies(session) {
  return [
    cookie(ACCESS_COOKIE, clean(session && session.access_token), SESSION_TTL_SECONDS),
    cookie(REFRESH_COOKIE, clean(session && session.refresh_token), SESSION_TTL_SECONDS)
  ];
}

function expiredSessionCookies() {
  return [cookie(ACCESS_COOKIE, '', 0), cookie(REFRESH_COOKIE, '', 0)];
}

function supabaseHeaders(config, accessToken) {
  const headers = { apikey: config.key, Accept: 'application/json' };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  return headers;
}

async function readJson(response) {
  const text = await response.text();
  if (!text) return {};
  try { return JSON.parse(text); } catch (_) { return { message: text }; }
}

async function authRequest(config, path, options) {
  const response = await fetch(`${config.url}/auth/v1${path}`, {
    ...options,
    headers: { ...supabaseHeaders(config, options && options.accessToken), ...(options && options.headers) }
  });
  return { ok: response.ok, status: response.status, data: await readJson(response) };
}

async function restRequest(config, path, options) {
  const response = await fetch(`${config.url}/rest/v1${path}`, {
    ...options,
    headers: { ...supabaseHeaders(config, options && options.accessToken), ...(options && options.headers) }
  });
  return { ok: response.ok, status: response.status, data: await readJson(response) };
}

async function isAdmin(config, accessToken) {
  if (!accessToken) return false;
  const result = await restRequest(config, '/rpc/amis_is_admin', {
    method: 'POST',
    accessToken,
    headers: { 'Content-Type': 'application/json' },
    body: '{}'
  });
  return result.ok && result.data === true;
}

async function signIn(config, identifier, password) {
  const email = loginEmail(identifier, config.emailDomain);
  if (!email || !clean(password)) return { ok: false, status: 401 };
  const result = await authRequest(config, '/token?grant_type=password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: String(password) })
  });
  if (!result.ok || !result.data.access_token || !result.data.refresh_token) {
    return { ok: false, status: result.status, error: result.data };
  }
  if (!await isAdmin(config, result.data.access_token)) {
    await signOut(config, result.data.access_token).catch(() => {});
    return { ok: false, status: 403 };
  }
  return { ok: true, session: result.data, user: result.data.user || null };
}

async function refresh(config, refreshToken) {
  if (!refreshToken) return { ok: false };
  const result = await authRequest(config, '/token?grant_type=refresh_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  if (!result.ok || !result.data.access_token || !result.data.refresh_token) return { ok: false };
  if (!await isAdmin(config, result.data.access_token)) return { ok: false };
  return { ok: true, session: result.data, user: result.data.user || null };
}

async function getUser(config, accessToken) {
  if (!accessToken) return { ok: false };
  return authRequest(config, '/user', { method: 'GET', accessToken });
}

async function getAdminSession(request, response) {
  const config = getConfig();
  if (!config.configured) return { authenticated: false, configured: false, config };
  const cookies = parseCookies(request);
  const accessToken = cookies[ACCESS_COOKIE];
  const current = await getUser(config, accessToken).catch(() => ({ ok: false }));
  if (current.ok && await isAdmin(config, accessToken)) {
    return { authenticated: true, configured: true, config, accessToken, user: current.data };
  }
  const renewed = await refresh(config, cookies[REFRESH_COOKIE]).catch(() => ({ ok: false }));
  if (!renewed.ok) {
    if (accessToken || cookies[REFRESH_COOKIE]) response.setHeader('Set-Cookie', expiredSessionCookies());
    return { authenticated: false, configured: true, config };
  }
  response.setHeader('Set-Cookie', sessionCookies(renewed.session));
  return {
    authenticated: true,
    configured: true,
    config,
    accessToken: renewed.session.access_token,
    user: renewed.user
  };
}

async function signOut(config, accessToken) {
  if (!accessToken) return;
  await authRequest(config, '/logout', { method: 'POST', accessToken });
}

module.exports = {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  getConfig,
  noStore,
  parseCookies,
  readBody,
  loginEmail,
  sessionCookies,
  expiredSessionCookies,
  restRequest,
  signIn,
  signOut,
  getAdminSession
};
