create extension if not exists "uuid-ossp";

-- 1) Projects
create table if not exists public.projects (
  id uuid not null default uuid_generate_v4(),
  user_id bigint not null,
  company_name varchar(100) not null,
  role_title varchar(120) not null,
  status varchar(20) not null default 'IN_PROGRESS',
  started_at date null,
  deadline_at date null,
  progress_percent int not null default 0,
  last_activity_at timestamptz null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint projects_pkey primary key (id)
);

create index if not exists ix_projects_user_id on public.projects (user_id);
create index if not exists ix_projects_status on public.projects (status);
create index if not exists ix_projects_last_activity on public.projects (last_activity_at desc);

-- 2) Job posting
create table if not exists public.project_job_postings (
  id uuid not null default uuid_generate_v4(),
  project_id uuid not null,
  user_id bigint not null,
  url text null,
  text text not null default '',
  extracted jsonb null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint project_job_postings_pkey primary key (id)
);

create index if not exists ix_pjp_project_id on public.project_job_postings (project_id);
create index if not exists ix_pjp_user_id on public.project_job_postings (user_id);

-- 3) Routine items
create table if not exists public.routine_items (
  id uuid not null default uuid_generate_v4(),
  user_id bigint not null,
  project_id uuid null,
  label varchar(200) not null,
  checked boolean not null default false,
  source varchar(30) not null default 'AI_RECOMMENDATION',
  routine_date date not null default current_date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint routine_items_pkey primary key (id)
);

create index if not exists ix_routine_user_date on public.routine_items (user_id, routine_date desc);
create index if not exists ix_routine_project_date on public.routine_items (project_id, routine_date desc);

-- 4) Portfolio items
create table if not exists public.portfolio_items (
  id uuid not null default uuid_generate_v4(),
  user_id bigint not null,
  title varchar(200) not null,
  tech_stack jsonb null,
  period_start date null,
  period_end date null,
  summary text null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint portfolio_items_pkey primary key (id)
);

create index if not exists ix_portfolio_items_user on public.portfolio_items (user_id);

create table if not exists public.project_portfolios (
  id uuid not null default uuid_generate_v4(),
  project_id uuid not null,
  portfolio_item_id uuid not null,
  role_type varchar(10) not null default 'SUB',
  is_representative boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint project_portfolios_pkey primary key (id)
);

create index if not exists ix_project_portfolios_project on public.project_portfolios (project_id);
create index if not exists ix_project_portfolios_item on public.project_portfolios (portfolio_item_id);
create index if not exists ix_project_portfolios_rep
  on public.project_portfolios (project_id, is_representative);

-- 5) Resume + paragraphs
create table if not exists public.resumes (
  id uuid not null default uuid_generate_v4(),
  project_id uuid not null,
  user_id bigint not null,
  title varchar(200) not null default '자기소개서',
  status varchar(20) not null default 'IN_PROGRESS',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint resumes_pkey primary key (id)
);

create index if not exists ix_resumes_project on public.resumes (project_id);
create index if not exists ix_resumes_user on public.resumes (user_id);

create table if not exists public.resume_paragraphs (
  id uuid not null default uuid_generate_v4(),
  resume_id uuid not null,
  project_id uuid not null,
  user_id bigint not null,
  title varchar(120) not null,
  sort_order int not null default 0,
  char_limit int not null default 500,
  text text not null default '',
  status varchar(20) not null default 'IN_PROGRESS',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint resume_paragraphs_pkey primary key (id)
);

create index if not exists ix_rp_resume_order on public.resume_paragraphs (resume_id, sort_order);
create index if not exists ix_rp_project on public.resume_paragraphs (project_id);
create index if not exists ix_rp_user on public.resume_paragraphs (user_id);

-- 6) Unified sessions
create table if not exists public.sessions (
  id uuid not null default uuid_generate_v4(),
  project_id uuid not null,
  user_id bigint not null,
  session_type varchar(30) not null,
  status varchar(20) not null default 'IN_PROGRESS',
  total_items int null,
  current_index int not null default 1,
  started_at timestamptz null,
  ended_at timestamptz null,
  duration_sec int null,
  meta jsonb null,
  result_json jsonb null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint sessions_pkey primary key (id)
);

create index if not exists ix_sessions_project on public.sessions (project_id, session_type, created_at desc);
create index if not exists ix_sessions_user on public.sessions (user_id, session_type, created_at desc);
create index if not exists ix_sessions_status on public.sessions (status);

-- 7) Session turns
create table if not exists public.session_turns (
  id uuid not null default uuid_generate_v4(),
  session_id uuid not null,
  project_id uuid not null,
  user_id bigint not null,
  turn_index int not null,
  role varchar(10) not null,
  speaker varchar(50) null,
  prompt text null,
  user_answer text null,
  message text null,
  intent text null,
  feedback text null,
  score numeric(5,2) null,
  score_delta jsonb null,
  meta jsonb null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint session_turns_pkey primary key (id)
);

create index if not exists ix_turns_session_order on public.session_turns (session_id, turn_index);
create index if not exists ix_turns_project on public.session_turns (project_id, created_at desc);
create index if not exists ix_turns_user on public.session_turns (user_id, created_at desc);

-- 8) Existing portfolio tables: project binding
alter table public.portfolios
  add column if not exists project_id uuid null;

create index if not exists idx_portfolios_project_id
  on public.portfolios (project_id);

alter table public.portfolios
  add column if not exists is_representative boolean not null default false;

alter table public.portfolios
  add column if not exists meta jsonb null;

create unique index if not exists ux_portfolios_project_representative
  on public.portfolios (project_id)
  where project_id is not null and is_representative = true;

alter table public.portfolio_analyses
  add column if not exists project_id uuid null;

create index if not exists idx_portfolio_analyses_project_id
  on public.portfolio_analyses (project_id);

-- 9) Existing simulation tables normalization
alter table public.simulation_sessions
  alter column user_id type bigint using user_id::bigint;

alter table public.simulation_sessions
  add column if not exists project_id uuid null;

create index if not exists ix_simulation_sessions_project_id
  on public.simulation_sessions (project_id);

alter table public.simulation_logs
  add column if not exists project_id uuid null;

create index if not exists ix_simulation_logs_project_id
  on public.simulation_logs (project_id);
