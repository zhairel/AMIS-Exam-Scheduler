'use strict';

const crypto = require('crypto');

const COOKIE_NAME = 'amis_admin_session';
const DEFAULT_TTL_SECONDS = 8 * 60 * 60;

function base64Url(value) {
  return Buffer.from(value).toString('base64url');
}

function getConfig() {
  const username = process.env.AMIS_ADMIN_USERNAME || 'admin';
  const password = process.env.AMIS_ADMIN_PASSWORD || '';
  const secret = process.env.AMIS_ADMIN_SESSION_SECRET || '';
  const configured = username.length > 0 && password.length >= 8 && secret.length >= 32;
  return { username, password, secret, configured };
}

function safeEqual(left, right) {
  const leftHash = crypto.createHash('sha256').update(String(left)).digest();
  const rightHash = crypto.createHash('sha256').update(String(right)).digest();
  return crypto.timingSafeEqual(leftHash, rightHash);
}

function signPayload(encodedPayload, secret) {
  return crypto.createHmac('sha256', secret).update(encodedPayload).digest('base64url');
}

function createSessionToken(secret, nowSeconds = Math.floor(Date.now() / 1000)) {
  const payload = base64Url(JSON.stringify({ role: 'admin', iat: nowSeconds, exp: nowSeconds + DEFAULT_TTL_SECONDS }));
  return `${payload}.${signPayload(payload, secret)}`;
}

function verifySessionToken(token, secret, nowSeconds = Math.floor(Date.now() / 1000)) {
  if (!token || !secret) return false;
  const parts = String(token).split('.');
  if (parts.length !== 2) return false;
  const expected = signPayload(parts[0], secret);
  if (!safeEqual(parts[1], expected)) return false;
  try {
    const payload = JSON.parse(Buffer.from(parts[0], 'base64url').toString('utf8'));
    return payload.role === 'admin' && Number.isFinite(payload.exp) && payload.exp > nowSeconds;
  } catch (_) {
    return false;
  }
}

function parseCookies(request) {
  const result = {};
  String(request.headers.cookie || '').split(';').forEach((part) => {
    const separator = part.indexOf('=');
    if (separator < 0) return;
    const name = part.slice(0, separator).trim();
    const value = part.slice(separator + 1).trim();
    if (name) result[name] = decodeURIComponent(value);
  });
  return result;
}

function hasAdminSession(request) {
  const config = getConfig();
  if (!config.configured) return false;
  return verifySessionToken(parseCookies(request)[COOKIE_NAME], config.secret);
}

function sessionCookie(token) {
  return `${COOKIE_NAME}=${encodeURIComponent(token)}; Max-Age=${DEFAULT_TTL_SECONDS}; Path=/; HttpOnly; Secure; SameSite=Strict`;
}

function expiredSessionCookie() {
  return `${COOKIE_NAME}=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Strict`;
}

function noStore(response) {
  response.setHeader('Cache-Control', 'private, no-store, max-age=0');
  response.setHeader('Content-Type', 'application/json; charset=utf-8');
}

function readCredentials(request) {
  if (request.body && typeof request.body === 'object') {
    return { username: String(request.body.username || ''), password: String(request.body.password || '') };
  }
  if (typeof request.body === 'string') {
    try {
      const body = JSON.parse(request.body);
      return { username: String(body.username || ''), password: String(body.password || '') };
    } catch (_) {
      return { username: '', password: '' };
    }
  }
  return { username: '', password: '' };
}

module.exports = {
  COOKIE_NAME,
  getConfig,
  safeEqual,
  createSessionToken,
  verifySessionToken,
  hasAdminSession,
  sessionCookie,
  expiredSessionCookie,
  noStore,
  readCredentials
};
