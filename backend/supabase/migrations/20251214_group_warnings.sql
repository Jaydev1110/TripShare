-- Create table for tracking group expiry warnings
create table if not exists group_warnings (
  id uuid default uuid_generate_v4() primary key,
  group_id uuid references groups(id) on delete cascade not null,
  days_left int not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Index for faster lookups
create index if not exists idx_group_warnings_group_id on group_warnings(group_id);
