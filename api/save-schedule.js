'use strict';

let inMemorySchedule = null;
let inMemoryUpdatedAt = 0;

module.exports = async function saveScheduleHandler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    try {
      let body = req.body;
      if (typeof body === 'string') {
        body = JSON.parse(body);
      }
      let exams = null;
      let updatedAt = Date.now();

      if (Array.isArray(body)) {
        exams = body;
      } else if (body && Array.isArray(body.schedule)) {
        exams = body.schedule;
        if (body.updated_at) updatedAt = Number(body.updated_at);
      }

      if (!exams || !Array.isArray(exams) || exams.length < 50) {
        return res.status(400).json({
          ok: false,
          error: 'Invalid exam data payload: expected array of >= 50 exams'
        });
      }

      inMemorySchedule = exams;
      inMemoryUpdatedAt = updatedAt;

      return res.status(200).json({
        ok: true,
        status: 'success',
        count: exams.length,
        updated_at: inMemoryUpdatedAt,
        message: 'Saved to Vercel realtime store'
      });
    } catch (err) {
      return res.status(500).json({ ok: false, error: err.message });
    }
  }

  if (req.method === 'GET') {
    if (inMemorySchedule && inMemorySchedule.length > 0) {
      return res.status(200).json({
        ok: true,
        status: 'success',
        count: inMemorySchedule.length,
        updated_at: inMemoryUpdatedAt,
        schedule: inMemorySchedule
      });
    }

    return res.status(200).json({
      ok: true,
      status: 'success',
      count: 0,
      updated_at: 0,
      schedule: null
    });
  }

  res.setHeader('Allow', 'GET, POST, OPTIONS');
  return res.status(405).json({ ok: false, error: 'Method not allowed' });
};
