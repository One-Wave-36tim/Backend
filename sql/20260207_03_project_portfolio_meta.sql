alter table public.portfolios
  add column if not exists is_representative boolean not null default false;

alter table public.portfolios
  add column if not exists meta jsonb null;

create unique index if not exists ux_portfolios_project_representative
  on public.portfolios (project_id)
  where project_id is not null and is_representative = true;
