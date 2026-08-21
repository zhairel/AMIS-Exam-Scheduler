'use strict';

const supabase = require('../server/supabase');
const schedules = require('../server/schedules');

const IMPORT_FIELDS = [
  'id', 'teacher', 'teacher_id', 'subject', 'grade_level', 'section', 'section_id',
  'day', 'start_time', 'end_time', 'room', 'schedule_type', 'status', 'source'
];

function importRecord(entry) {
  return Object.fromEntries(IMPORT_FIELDS.map((field) => [field, entry[field] == null ? '' : entry[field]]));
}

async function countImported(config, accessToken) {
  let count = 0;
  const pageSize = 1000;
  for (let offset = 0; ; offset += pageSize) {
    const result = await supabase.restRequest(
      config,
      `/manual_schedules?select=id&source=eq.official&limit=${pageSize}&offset=${offset}`,
      { method: 'GET', accessToken }
    );
    if (!result.ok) throw new Error('Unable to verify the imported schedule count.');
    const page = Array.isArray(result.data) ? result.data : [];
    count += page.length;
    if (page.length < pageSize) return count;
  }
}

async function main() {
  const password = String(process.env.AMIS_ADMIN_PASSWORD || '');
  if (!password) throw new Error('Set AMIS_ADMIN_PASSWORD before running the importer.');
  const config = supabase.getConfig();
  if (!config.configured) throw new Error('Supabase is not configured.');

  const login = await supabase.signIn(config, process.env.AMIS_ADMIN_USERNAME || 'admin', password);
  if (!login.ok) throw new Error('Unable to sign in as the allowlisted AMIS administrator.');

  try {
    const records = schedules.officialDatabaseEntries().map(importRecord);
    const batchSize = 100;
    for (let index = 0; index < records.length; index += batchSize) {
      const batch = records.slice(index, index + batchSize);
      const result = await supabase.restRequest(config, '/manual_schedules?on_conflict=id', {
        method: 'POST',
        accessToken: login.session.access_token,
        headers: {
          'Content-Type': 'application/json',
          Prefer: 'resolution=merge-duplicates,return=minimal'
        },
        body: JSON.stringify(batch)
      });
      if (!result.ok) {
        const code = result.data && result.data.code ? ` (${result.data.code})` : '';
        throw new Error(`Import stopped at record ${index + 1}${code}. Run the latest Supabase migration first.`);
      }
      process.stdout.write(`Imported ${Math.min(index + batch.length, records.length)} / ${records.length}\r`);
    }
    const count = await countImported(config, login.session.access_token);
    process.stdout.write('\n');
    console.log(JSON.stringify({ expected: records.length, imported: count, complete: count === records.length }));
    if (count !== records.length) process.exitCode = 1;
  } finally {
    await supabase.signOut(config, login.session.access_token).catch(() => {});
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
