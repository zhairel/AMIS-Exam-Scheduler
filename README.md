# AMIS-Exam-Scheduler

**Al Munawwara Islamic School (AMIS) — Master Term Examination Scheduler S.Y. 2026–2027**

An automated, conflict-free examination scheduling system and interactive web application built with Google OR-Tools CP-SAT constraint programming.

## 🌟 Features
- **Deterministic 0-Conflict Scheduling**: Constraint satisfaction model solving 597 exam sessions across 63 individual sections (F2F Classroom, ODL 1st Shift, ODL 2nd Shift) with 0 teacher double-booking and 0 section overlaps.
- **Official Term Examination Hours**:
  - **F2F**: 8:00 AM – 11:25 AM (General Assembly, Exam 1, Exam 2, Recess 10:00–10:25 AM, Exam 3, Dismissal at 11:25 AM)
  - **ODL 1st Shift**: 12:40 PM – 4:10 PM (General Assembly, Exam 1, Exam 2, Salah Break 2:50–3:10 PM, Exam 3, Dismissal at 4:10 PM)
  - **ODL 2nd Shift**: 3:10 PM – 6:30 PM (Salah Break 2:50–3:10 PM, Exam 1, Exam 2, Exam 3, Dismissal at 6:30 PM)
- **Interactive Web App**:
  - Auto-pop interactive drawer/modal when clicking any subject or exam card showing all assigned sections, teachers, dates, and times.
  - 4 View Modes: Grade Posters, Daily Timetable Grid, Subject Directory, and Faculty Timetables.
  - Multi-criteria real-time filters and search.
  - Instant CSV export and printable high-res poster layout.
- **Vercel Ready**: Static single-page application with bundled dataset for instant deployment.

## 🚀 Live Demo & Deployment
- Open `index.html` in any web browser or deploy directly to [Vercel](https://vercel.com).

## Manual Class Schedule Management

The `/class-schedule` page includes a separate manual-schedule record system:

- `/class-schedule/create` creates a manual assignment.
- `/class-schedule/:id/edit` edits an existing manual assignment through the Vercel rewrite in `vercel.json`.
- Records are stored in the shared Supabase Postgres database, rather than mixed into the generated official JSON or saved as browser-only state.
- Every active write is checked against the official generated timetable and all active manual records for teacher, section, room, and partial time overlaps.
- Inactive records stay in the database but do not occupy a time slot.
- Active manual records are overlaid onto the existing section and faculty timetable views without changing the generated source datasets.

Supabase makes active manual assignments immediately available to every device. Database constraints prevent overlapping active manual assignments during concurrent writes.

### Admin portal

Schedule mutation controls are protected by Supabase Auth and Postgres Row Level Security (RLS). Public visitors can read active schedules, while create, edit, delete, activate, deactivate, and inactive-record access require an allowlisted Supabase user.

1. Create a Supabase project and run [`supabase/001_amis_schedule.sql`](supabase/001_amis_schedule.sql) in **SQL Editor**.
2. In **Authentication → Users**, create `admin@amis.local` with the chosen password. The portal username `admin` maps to this email.
3. Run the allowlist statement shown at the bottom of the migration.
4. Configure these Vercel environment variables for Production, Preview, and Development, then redeploy:

```text
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=<Supabase publishable key>
```

Legacy `SUPABASE_ANON_KEY` is also supported. Do not use or expose a Supabase secret/service-role key: all application requests use the low-privilege publishable key plus the signed-in user's token, and RLS remains authoritative. The session tokens are stored in Secure, HTTP-only, SameSite=Strict cookies.

## 📄 License
MIT License.
