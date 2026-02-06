alter table public.users
  add column if not exists name varchar(100) not null default '';

alter table public.users
  add column if not exists target_role varchar(120) null;

alter table public.users
  add column if not exists coach_status varchar(20) not null default 'COACHING';

alter table public.users
  add column if not exists avatar_url text null;

alter table public.users
  add column if not exists updated_at timestamptz not null default now();

