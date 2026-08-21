-- AMIS manual schedule database and admin authorization.
-- Run this entire file once in Supabase Dashboard > SQL Editor.

create table if not exists public.amis_admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

alter table public.amis_admin_users enable row level security;
revoke all on table public.amis_admin_users from anon, authenticated;

create or replace function public.amis_is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.amis_admin_users
    where user_id = (select auth.uid())
  );
$$;

revoke all on function public.amis_is_admin() from public, anon;
grant execute on function public.amis_is_admin() to authenticated;

create table if not exists public.manual_schedules (
  id text primary key,
  teacher text not null,
  teacher_id text not null default '',
  subject text not null,
  grade_level text not null,
  section text not null,
  section_id text not null default '',
  day text not null check (day in ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday')),
  start_time time without time zone not null,
  end_time time without time zone not null,
  room text not null default '',
  schedule_type text not null default 'Academic Class',
  status text not null default 'active' check (status in ('active', 'inactive')),
  source text not null default 'manual' check (source = 'manual'),
  created_by uuid references auth.users(id) on delete set null default auth.uid(),
  updated_by uuid references auth.users(id) on delete set null default auth.uid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  teacher_key text generated always as (lower(teacher)) stored,
  section_key text generated always as (lower(section)) stored,
  room_key text generated always as (lower(room)) stored,
  slot_range int4range generated always as (
    int4range(
      extract(epoch from start_time)::integer,
      extract(epoch from end_time)::integer,
      '[)'
    )
  ) stored,
  constraint manual_schedule_time_order check (end_time > start_time)
);

create extension if not exists btree_gist;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'manual_schedules_teacher_no_overlap'
      and conrelid = 'public.manual_schedules'::regclass
  ) then
    alter table public.manual_schedules
      add constraint manual_schedules_teacher_no_overlap
      exclude using gist (day with =, teacher_key with =, slot_range with &&)
      where (status = 'active');
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'manual_schedules_section_no_overlap'
      and conrelid = 'public.manual_schedules'::regclass
  ) then
    alter table public.manual_schedules
      add constraint manual_schedules_section_no_overlap
      exclude using gist (day with =, section_key with =, slot_range with &&)
      where (status = 'active');
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'manual_schedules_room_no_overlap'
      and conrelid = 'public.manual_schedules'::regclass
  ) then
    alter table public.manual_schedules
      add constraint manual_schedules_room_no_overlap
      exclude using gist (day with =, room_key with =, slot_range with &&)
      where (status = 'active' and room_key <> '');
  end if;
end
$$;

create index if not exists manual_schedules_slot_idx
  on public.manual_schedules (day, start_time, end_time)
  where status = 'active';
create index if not exists manual_schedules_teacher_idx on public.manual_schedules (lower(teacher));
create index if not exists manual_schedules_section_idx on public.manual_schedules (lower(section));
create index if not exists manual_schedules_room_idx on public.manual_schedules (lower(room));

create or replace function public.amis_prepare_manual_schedule()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.teacher := btrim(new.teacher);
  new.teacher_id := btrim(coalesce(new.teacher_id, ''));
  new.subject := btrim(new.subject);
  new.grade_level := btrim(new.grade_level);
  new.section := btrim(new.section);
  new.section_id := btrim(coalesce(new.section_id, ''));
  new.room := btrim(coalesce(new.room, ''));
  new.schedule_type := btrim(coalesce(new.schedule_type, 'Academic Class'));
  new.source := 'manual';
  new.updated_at := now();
  new.updated_by := (select auth.uid());
  if tg_op = 'INSERT' then
    new.created_by := (select auth.uid());
  end if;

  if new.teacher = '' or new.subject = '' or new.grade_level = '' or new.section = '' then
    raise exception using errcode = '23514', message = 'Complete all required schedule fields.';
  end if;

  if new.status = 'active' and exists (
    select 1
    from public.manual_schedules existing
    where existing.id <> new.id
      and existing.status = 'active'
      and existing.day = new.day
      and existing.start_time < new.end_time
      and new.start_time < existing.end_time
      and (
        (
          new.teacher_id <> '' and existing.teacher_id <> ''
          and lower(new.teacher_id) = lower(existing.teacher_id)
        )
        or lower(new.teacher) = lower(existing.teacher)
        or (
          new.section_id <> '' and existing.section_id <> ''
          and lower(new.section_id) = lower(existing.section_id)
        )
        or lower(new.section) = lower(existing.section)
        or (
          new.room <> '' and existing.room <> ''
          and lower(new.room) = lower(existing.room)
        )
      )
  ) then
    raise exception using
      errcode = '23P01',
      message = 'This active schedule conflicts with another manual assignment.';
  end if;

  return new;
end;
$$;

drop trigger if exists amis_prepare_manual_schedule_trigger on public.manual_schedules;
create trigger amis_prepare_manual_schedule_trigger
before insert or update on public.manual_schedules
for each row execute function public.amis_prepare_manual_schedule();

alter table public.manual_schedules enable row level security;

grant select on table public.manual_schedules to anon, authenticated;
grant insert, update, delete on table public.manual_schedules to authenticated;

drop policy if exists "Public can view active AMIS schedules" on public.manual_schedules;
create policy "Public can view active AMIS schedules"
on public.manual_schedules
for select
to anon, authenticated
using (status = 'active');

drop policy if exists "AMIS admins can view every schedule" on public.manual_schedules;
create policy "AMIS admins can view every schedule"
on public.manual_schedules
for select
to authenticated
using ((select public.amis_is_admin()));

drop policy if exists "AMIS admins can insert schedules" on public.manual_schedules;
create policy "AMIS admins can insert schedules"
on public.manual_schedules
for insert
to authenticated
with check ((select public.amis_is_admin()));

drop policy if exists "AMIS admins can update schedules" on public.manual_schedules;
create policy "AMIS admins can update schedules"
on public.manual_schedules
for update
to authenticated
using ((select public.amis_is_admin()))
with check ((select public.amis_is_admin()));

drop policy if exists "AMIS admins can delete schedules" on public.manual_schedules;
create policy "AMIS admins can delete schedules"
on public.manual_schedules
for delete
to authenticated
using ((select public.amis_is_admin()));

-- After creating admin@amis.local in Authentication > Users, allowlist it:
-- insert into public.amis_admin_users (user_id)
-- select id from auth.users where lower(email) = 'admin@amis.local'
-- on conflict (user_id) do nothing;
