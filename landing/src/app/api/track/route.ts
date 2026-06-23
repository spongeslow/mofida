import { NextRequest, NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase";
import { deviceFromUA, geoFromRequest, referrerHost } from "@/lib/request";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Body = {
  session_id?: string;
  path?: string;
  referrer?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

/**
 * Records a single page view. Country/city/region/timezone are derived
 * server-side from Vercel's geo headers — privacy-friendly (no raw IP stored,
 * no tracking cookie; session_id is a random per-tab id).
 */
export async function POST(req: NextRequest) {
  let body: Body = {};
  try {
    body = await req.json();
  } catch {
    /* tolerate empty/broken bodies — analytics must never block the page */
  }

  const supabase = getSupabaseAdmin();
  if (!supabase) {
    return NextResponse.json({ ok: true, simulated: true });
  }

  const geo = geoFromRequest(req);
  const ua = req.headers.get("user-agent");
  const referrer = body.referrer || req.headers.get("referer") || null;

  const { error } = await supabase.from("pageviews").insert({
    session_id: body.session_id || null,
    path: body.path || null,
    referrer,
    referrer_host: referrerHost(referrer) || null,
    country: geo.country,
    city: geo.city,
    region: geo.region,
    timezone: geo.timezone,
    utm_source: body.utm_source || null,
    utm_medium: body.utm_medium || null,
    utm_campaign: body.utm_campaign || null,
    device: deviceFromUA(ua),
    user_agent: ua,
  });

  if (error) console.error("[track] insert error:", error);

  // Always 200 — never let analytics surface an error to the visitor.
  return NextResponse.json({ ok: true });
}
