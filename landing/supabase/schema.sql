-- ============================================================================
-- Moufida landing page — Supabase schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL → New query) once.
-- ============================================================================

-- ── Waitlist ────────────────────────────────────────────────────────────────
create table if not exists public.waitlist (
  id          uuid primary key default gen_random_uuid(),
  email       text not null,
  created_at  timestamptz not null default now(),
  -- attribution / analytics captured at signup
  country     text,
  city        text,
  region      text,
  referrer    text,
  utm_source  text,
  utm_medium  text,
  utm_campaign text,
  landing_path text,
  user_agent  text
);

-- one row per email (case-insensitive)
create unique index if not exists waitlist_email_unique
  on public.waitlist (lower(email));

-- ── Page views (privacy-friendly: no raw IP, no cookies) ─────────────────────
create table if not exists public.pageviews (
  id           bigint generated always as identity primary key,
  created_at   timestamptz not null default now(),
  session_id   text,                 -- random id from sessionStorage, not a tracking cookie
  path         text,
  referrer     text,
  referrer_host text,                 -- e.g. "reddit.com", "news.ycombinator.com"
  country      text,
  city         text,
  region       text,
  timezone     text,
  utm_source   text,
  utm_medium   text,
  utm_campaign text,
  device       text,                  -- mobile | tablet | desktop
  user_agent   text
);

create index if not exists pageviews_created_at_idx on public.pageviews (created_at desc);
create index if not exists pageviews_referrer_host_idx on public.pageviews (referrer_host);
create index if not exists pageviews_country_idx on public.pageviews (country);
create index if not exists pageviews_utm_source_idx on public.pageviews (utm_source);

-- ── Row Level Security ───────────────────────────────────────────────────────
-- Both tables are written ONLY by the server using the service-role key, which
-- bypasses RLS. We enable RLS with no public policies so the anon/public key
-- can never read or write these tables directly.
alter table public.waitlist  enable row level security;
alter table public.pageviews enable row level security;

-- ── Handy analytics views ────────────────────────────────────────────────────
create or replace view public.waitlist_stats as
  select count(*) as total,
         count(*) filter (where created_at > now() - interval '24 hours') as last_24h,
         count(*) filter (where created_at > now() - interval '7 days')   as last_7d
  from public.waitlist;

create or replace view public.traffic_by_source as
  select coalesce(utm_source, referrer_host, 'direct') as source,
         count(*)                       as views,
         count(distinct session_id)     as sessions
  from public.pageviews
  group by 1
  order by views desc;

create or replace view public.traffic_by_country as
  select coalesce(country, 'unknown') as country,
         count(*)                     as views,
         count(distinct session_id)   as sessions
  from public.pageviews
  group by 1
  order by views desc;
