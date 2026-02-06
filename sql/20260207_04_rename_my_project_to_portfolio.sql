-- Rename legacy my_project tables/columns to portfolio naming.
-- Safe to run multiple times.

do $$
begin
  if to_regclass('public.my_projects') is not null
     and to_regclass('public.portfolio_items') is null then
    execute 'alter table public.my_projects rename to portfolio_items';
  end if;
end
$$;

do $$
begin
  if to_regclass('public.project_my_projects') is not null
     and to_regclass('public.project_portfolios') is null then
    execute 'alter table public.project_my_projects rename to project_portfolios';
  end if;
end
$$;

do $$
begin
  if exists (
      select 1
      from information_schema.columns
      where table_schema = 'public'
        and table_name = 'project_portfolios'
        and column_name = 'my_project_id'
    )
    and not exists (
      select 1
      from information_schema.columns
      where table_schema = 'public'
        and table_name = 'project_portfolios'
        and column_name = 'portfolio_item_id'
    ) then
    execute 'alter table public.project_portfolios rename column my_project_id to portfolio_item_id';
  end if;
end
$$;

do $$
begin
  if exists (
    select 1
    from pg_constraint c
    join pg_class t on c.conrelid = t.oid
    join pg_namespace n on n.oid = t.relnamespace
    where n.nspname = 'public'
      and t.relname = 'portfolio_items'
      and c.conname = 'my_projects_pkey'
  ) then
    execute 'alter table public.portfolio_items rename constraint my_projects_pkey to portfolio_items_pkey';
  end if;
end
$$;

do $$
begin
  if exists (
    select 1
    from pg_constraint c
    join pg_class t on c.conrelid = t.oid
    join pg_namespace n on n.oid = t.relnamespace
    where n.nspname = 'public'
      and t.relname = 'project_portfolios'
      and c.conname = 'project_my_projects_pkey'
  ) then
    execute 'alter table public.project_portfolios rename constraint project_my_projects_pkey to project_portfolios_pkey';
  end if;
end
$$;

do $$
begin
  if to_regclass('public.ix_my_projects_user') is not null
     and to_regclass('public.ix_portfolio_items_user') is null then
    execute 'alter index public.ix_my_projects_user rename to ix_portfolio_items_user';
  elsif to_regclass('public.ix_my_projects_user') is not null
        and to_regclass('public.ix_portfolio_items_user') is not null then
    execute 'drop index public.ix_my_projects_user';
  end if;
end
$$;

do $$
begin
  if to_regclass('public.ix_pmp_project') is not null
     and to_regclass('public.ix_project_portfolios_project') is null then
    execute 'alter index public.ix_pmp_project rename to ix_project_portfolios_project';
  elsif to_regclass('public.ix_pmp_project') is not null
        and to_regclass('public.ix_project_portfolios_project') is not null then
    execute 'drop index public.ix_pmp_project';
  end if;
end
$$;

do $$
begin
  if to_regclass('public.ix_pmp_my_project') is not null
     and to_regclass('public.ix_project_portfolios_item') is null then
    execute 'alter index public.ix_pmp_my_project rename to ix_project_portfolios_item';
  elsif to_regclass('public.ix_pmp_my_project') is not null
        and to_regclass('public.ix_project_portfolios_item') is not null then
    execute 'drop index public.ix_pmp_my_project';
  end if;
end
$$;

do $$
begin
  if to_regclass('public.ix_pmp_rep') is not null
     and to_regclass('public.ix_project_portfolios_rep') is null then
    execute 'alter index public.ix_pmp_rep rename to ix_project_portfolios_rep';
  elsif to_regclass('public.ix_pmp_rep') is not null
        and to_regclass('public.ix_project_portfolios_rep') is not null then
    execute 'drop index public.ix_pmp_rep';
  end if;
end
$$;

create index if not exists ix_portfolio_items_user on public.portfolio_items (user_id);
create index if not exists ix_project_portfolios_project on public.project_portfolios (project_id);
create index if not exists ix_project_portfolios_item
  on public.project_portfolios (portfolio_item_id);
create index if not exists ix_project_portfolios_rep
  on public.project_portfolios (project_id, is_representative);
