'use strict';

const fs = require('fs');
const path = require('path');

let inMemorySchedule = null;
let inMemoryLockedSections = [];
let inMemoryUpdatedAt = 0;

function tryLoadScheduleFromDisk() {
  const staticPath = path.join(__dirname, '../exam_data_2nd_term.json');
  let staticMtime = 0;
  let staticSchedule = null;
  if (fs.existsSync(staticPath)) {
    try {
      staticMtime = fs.statSync(staticPath).mtimeMs;
      const staticData = JSON.parse(fs.readFileSync(staticPath, 'utf8'));
      if (Array.isArray(staticData) && staticData.length > 50) {
        staticSchedule = staticData;
      }
    } catch (e) {}
  }

  const tmpPath = '/tmp/amis_exam_schedule.json';
  if (fs.existsSync(tmpPath)) {
    try {
      const tmpMtime = fs.statSync(tmpPath).mtimeMs;
      if (tmpMtime >= staticMtime) {
        const content = JSON.parse(fs.readFileSync(tmpPath, 'utf8'));
        if (content && Array.isArray(content.schedule) && content.schedule.length > 50) {
          inMemorySchedule = content.schedule;
          inMemoryUpdatedAt = Number(content.updated_at) || tmpMtime;
          if (Array.isArray(content.locked_sections)) {
            inMemoryLockedSections = content.locked_sections;
          }
          return;
        }
      }
    } catch (e) {}
  }

  if (staticSchedule) {
    inMemorySchedule = staticSchedule;
    inMemoryUpdatedAt = staticMtime || Date.now();
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

      if ((!exams || !Array.isArray(exams) || exams.length < 50) && (!body || !Array.isArray(body.locked_sections))) {
        return res.status(400).json({
          ok: false,
          error: 'Invalid payload: expected schedule array (>= 50) or locked_sections array'
        });
      }

      if (exams && Array.isArray(exams) && exams.length >= 50) {
        inMemorySchedule = exams;
        inMemoryUpdatedAt = updatedAt;
      }

      if (body && Array.isArray(body.locked_sections)) {
        inMemoryLockedSections = body.locked_sections;
      }

      if (!inMemorySchedule) {
        tryLoadScheduleFromDisk();
      }

      // Write to /tmp for durability across warm executions
      try {
        fs.writeFileSync('/tmp/amis_exam_schedule.json', JSON.stringify({
          schedule: inMemorySchedule,
          updated_at: inMemoryUpdatedAt,
          locked_sections: inMemoryLockedSections
        }), 'utf8');
      } catch (e) {}

      return res.status(200).json({
        ok: true,
        status: 'success',
        count: inMemorySchedule ? inMemorySchedule.length : 0,
        locked_sections_count: inMemoryLockedSections.length,
        updated_at: inMemoryUpdatedAt,
        message: 'Saved to Vercel realtime store'
      });
    } catch (err) {
      return res.status(500).json({ ok: false, error: err.message });
    }
  }

  if (req.method === 'GET') {
    const staticPath = path.join(__dirname, '../exam_data_2nd_term.json');
    let staticMtime = 0;
    if (fs.existsSync(staticPath)) {
      try { staticMtime = fs.statSync(staticPath).mtimeMs; } catch (e) {}
    }

    if (!inMemorySchedule || inMemorySchedule.length < 50 || (staticMtime > inMemoryUpdatedAt)) {
      tryLoadScheduleFromDisk();
    }

    if (inMemorySchedule && inMemorySchedule.length > 0) {
      return res.status(200).json({
        ok: true,
        status: 'success',
        count: inMemorySchedule.length,
        updated_at: inMemoryUpdatedAt || Date.now(),
        schedule: inMemorySchedule,
        locked_sections: inMemoryLockedSections || []
      });
    }

    return res.status(200).json({
      ok: true,
      status: 'success',
      count: 0,
      updated_at: 0,
      schedule: null,
      locked_sections: []
    });
  }

  res.setHeader('Allow', 'GET, POST, OPTIONS');
  return res.status(405).json({ ok: false, error: 'Method not allowed' });
};
