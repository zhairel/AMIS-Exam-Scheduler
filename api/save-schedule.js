'use strict';

const fs = require('fs');
const path = require('path');

let inMemorySchedule = null;
let inMemoryUpdatedAt = 0;

function tryLoadScheduleFromDisk() {
  const tmpPath = '/tmp/amis_exam_schedule.json';
  if (fs.existsSync(tmpPath)) {
    try {
      const content = JSON.parse(fs.readFileSync(tmpPath, 'utf8'));
      if (content && Array.isArray(content.schedule) && content.schedule.length > 50) {
        inMemorySchedule = content.schedule;
        inMemoryUpdatedAt = Number(content.updated_at) || fs.statSync(tmpPath).mtimeMs;
        return;
      }
    } catch (e) {}
  }

  const staticPath = path.join(__dirname, '../exam_data_2nd_term.json');
  if (fs.existsSync(staticPath)) {
    try {
      const staticData = JSON.parse(fs.readFileSync(staticPath, 'utf8'));
      if (Array.isArray(staticData) && staticData.length > 50) {
        inMemorySchedule = staticData;
        inMemoryUpdatedAt = fs.statSync(staticPath).mtimeMs;
      }
    } catch (e) {}
  }
}

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

      // Write to /tmp for durability across warm executions
      try {
        fs.writeFileSync('/tmp/amis_exam_schedule.json', JSON.stringify({
          schedule: exams,
          updated_at: updatedAt
        }), 'utf8');
      } catch (e) {}

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
    if (!inMemorySchedule || inMemorySchedule.length < 50) {
      tryLoadScheduleFromDisk();
    }

    if (inMemorySchedule && inMemorySchedule.length > 0) {
      return res.status(200).json({
        ok: true,
        status: 'success',
        count: inMemorySchedule.length,
        updated_at: inMemoryUpdatedAt || Date.now(),
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
