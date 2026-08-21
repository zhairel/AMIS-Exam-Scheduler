-- Persist administrator-defined calendar cell groups.

alter table public.manual_schedules
  add column if not exists merge_group text not null default '';

create index if not exists manual_schedules_merge_group_idx
  on public.manual_schedules (merge_group)
  where merge_group <> '';
