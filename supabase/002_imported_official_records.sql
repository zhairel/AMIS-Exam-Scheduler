-- Allow the original teacher-assigned timetable cells to become database
-- records while preserving strict conflict protection for all new schedules.

alter table public.manual_schedules
  drop constraint if exists manual_schedules_source_check;

alter table public.manual_schedules
  add constraint manual_schedules_source_check
  check (source in ('manual', 'official'));

alter table public.manual_schedules
  drop constraint if exists manual_schedules_teacher_no_overlap;
alter table public.manual_schedules
  drop constraint if exists manual_schedules_section_no_overlap;
alter table public.manual_schedules
  drop constraint if exists manual_schedules_room_no_overlap;

alter table public.manual_schedules
  add constraint manual_schedules_teacher_no_overlap
  exclude using gist (day with =, teacher_key with =, slot_range with &&)
  where (status = 'active' and source = 'manual');

alter table public.manual_schedules
  add constraint manual_schedules_section_no_overlap
  exclude using gist (day with =, section_key with =, slot_range with &&)
  where (status = 'active' and source = 'manual');

alter table public.manual_schedules
  add constraint manual_schedules_room_no_overlap
  exclude using gist (day with =, room_key with =, slot_range with &&)
  where (status = 'active' and source = 'manual' and room_key <> '');

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
  new.source := case when new.source = 'official' then 'official' else 'manual' end;
  new.updated_at := now();
  new.updated_by := (select auth.uid());
  if tg_op = 'INSERT' then
    new.created_by := (select auth.uid());
  end if;

  if new.teacher = '' or new.subject = '' or new.grade_level = '' or new.section = '' then
    raise exception using errcode = '23514', message = 'Complete all required schedule fields.';
  end if;

  -- Imported official rows preserve the original published timetable exactly,
  -- including its pre-existing double bookings. New manual rows remain strict.
  if new.source = 'manual' and new.status = 'active' and exists (
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
      message = 'This active schedule conflicts with another assignment.';
  end if;

  return new;
end;
$$;

drop policy if exists "Public can view active AMIS schedules" on public.manual_schedules;
create policy "Public can view active AMIS schedules"
on public.manual_schedules
for select
to anon, authenticated
using (status = 'active' or source = 'official');
