# Moufida — Landing Page & Waitlist

Conversion-focused marketing site for **Moufida**, the 24/7 AI co-founder. Built to
capture waitlist emails and rich, privacy-friendly visit analytics (country, time,
referrer/UTM source) ahead of the **June 28, 2026** launch.

- **Framework:** Next.js 14 (App Router) + TypeScript
- **Styling:** Tailwind CSS — mirrors the desktop app's "Warm Autumn" palette
- **Data:** Supabase (Postgres) for the waitlist + page-view analytics
- **Hosting:** Vercel (free tier) — geo headers power server-side country detection

---

## 1. Set up Supabase (one time)

1. Create a free project at [supabase.com](https://supabase.com).
2. Open **SQL Editor → New query**, paste the contents of [`supabase/schema.sql`](./supabase/schema.sql), and run it.
3. Go to **Project Settings → API** and copy:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **`service_role` secret key** → `SUPABASE_SERVICE_ROLE_KEY` (server-only — never expose this)

## 2. Configure environment

```bash
cp .env.example .env.local
# then fill in the values
```

| Variable | What it's for |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side writes (waitlist + analytics) |
| `NEXT_PUBLIC_SITE_URL` | Canonical URL for SEO/OG tags |
| `NEXT_PUBLIC_LAUNCH_DATE` | ISO date driving the countdown (default `2026-06-28T09:00:00Z`) |

> The app runs fine **without** Supabase locally — writes are skipped and logged so you
> can develop the UI offline.

## 3. Run locally

```bash
npm install
npm run dev      # http://localhost:3000
```

## 4. Deploy to Vercel

1. Push the repo and **Import** it in Vercel. Set the **Root Directory** to `landing/`.
2. Add the four env vars above in **Project Settings → Environment Variables**.
3. Deploy. Vercel automatically injects `x-vercel-ip-country` / `-city` / `-region`
   headers in production, so visitor country/city/region is detected with **no extra
   API key**.

---

## Analytics

Every visit records a row in `pageviews` via `POST /api/track` (fired client-side with
`navigator.sendBeacon`). We store:

- **country / city / region / timezone** — derived server-side from Vercel geo headers
- **referrer + referrer host** — e.g. `reddit.com`, `news.ycombinator.com`
- **utm_source / medium / campaign** — tag your links: `?utm_source=reddit&utm_campaign=launch`
- **device** (mobile/tablet/desktop), **path**, **timestamp**, **session id**

> Privacy-friendly by design: **no raw IP is stored** and there's **no tracking cookie**
> (`session_id` is a random per-tab id). This matches Moufida's local-first positioning.

### Reading your data

In the Supabase SQL editor:

```sql
select * from waitlist order by created_at desc;     -- signups
select * from waitlist_stats;                         -- totals / 24h / 7d
select * from traffic_by_source;                      -- where visitors came from
select * from traffic_by_country;                     -- visitor countries
```

Use **per-channel UTM links** when you post:

| Channel | Link |
| --- | --- |
| Reddit | `https://moufida.ai/?utm_source=reddit&utm_medium=social&utm_campaign=launch` |
| Hacker News | `https://moufida.ai/?utm_source=hn&utm_medium=social&utm_campaign=launch` |
| LinkedIn | `https://moufida.ai/?utm_source=linkedin&utm_medium=social&utm_campaign=launch` |
| Indie Hackers | `https://moufida.ai/?utm_source=indiehackers&utm_medium=social&utm_campaign=launch` |
| Product Hunt | `https://moufida.ai/?utm_source=producthunt&utm_medium=social&utm_campaign=launch` |

---

## Project structure

```
landing/
├── supabase/schema.sql        # run once in Supabase
├── src/
│   ├── app/
│   │   ├── layout.tsx          # fonts, SEO/OG metadata
│   │   ├── page.tsx            # section composition
│   │   ├── globals.css
│   │   ├── opengraph-image.tsx # dynamic 1200×630 social preview
│   │   ├── robots.ts / sitemap.ts
│   │   └── api/
│   │       ├── waitlist/route.ts  # POST signup · GET count
│   │       └── track/route.ts     # POST page view
│   ├── components/             # Hero, DueDiligence, Pricing, FAQ, ...
│   └── lib/                    # supabase client, request/geo helpers, client analytics
```
