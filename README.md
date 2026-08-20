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
- Records are stored transactionally in the browser's IndexedDB database (`AMIS_CLASS_SCHEDULE_DB`), rather than mixed into the generated official JSON or saved as UI state in `localStorage`.
- Every active write is checked against the official generated timetable and all active manual records for teacher, section, room, and partial time overlaps.
- Inactive records stay in the database but do not occupy a time slot.
- Active manual records are overlaid onto the existing section and faculty timetable views without changing the generated source datasets.

Because this repository is a static Vercel deployment, IndexedDB data belongs to the browser profile where it was created. A shared multi-device deployment would require connecting the same store interface to a hosted database service.

### Admin portal

Schedule mutation controls are protected by the `/admin` portal. Public visitors can view the official timetable, while create, edit, delete, activate, and deactivate actions require a valid server-signed admin session.

Configure these Vercel environment variables for Production, Preview, and Development as appropriate, then redeploy:

```text
AMIS_ADMIN_USERNAME=admin
AMIS_ADMIN_PASSWORD=<a unique password with at least 8 characters>
AMIS_ADMIN_SESSION_SECRET=<at least 32 random characters>
```

Generate a strong session secret with `openssl rand -hex 32`. The session is stored in a Secure, HTTP-only, SameSite=Strict cookie and expires after eight hours.

## 📄 License
MIT License.
