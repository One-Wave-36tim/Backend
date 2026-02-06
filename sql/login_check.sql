-- 1) Create simple login table
create table if not exists public.users (
    id bigserial primary key,
    user_id varchar(50) unique not null,
    password varchar(255) not null
);

-- 2) Seed sample account (id/pw)
insert into public.users (user_id, password)
values ('demo', '1234')
on conflict (user_id) do nothing;

-- 3) Verify row exists
select id, user_id
from public.users
where user_id = 'demo';
