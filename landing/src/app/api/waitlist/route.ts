import { NextRequest, NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase";
import { geoFromRequest, isValidEmail } from "@/lib/request";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Body = {
  email?: string;
  referrer?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  landing_path?: string;
};

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid request." }, { status: 400 });
  }

  const email = body.email?.trim().toLowerCase();
  if (!isValidEmail(email)) {
    return NextResponse.json(
      { ok: false, error: "Please enter a valid email address." },
      { status: 422 }
    );
  }

  const supabase = getSupabaseAdmin();
  if (!supabase) {
    // No DB configured (e.g. local dev without env). Don't break the UX.
    console.log("[waitlist] (no-db) would store:", email);
    return NextResponse.json({ ok: true, simulated: true });
  }

  const geo = geoFromRequest(req);

  const { error } = await supabase.from("waitlist").insert({
    email,
    country: geo.country,
    city: geo.city,
    region: geo.region,
    referrer: body.referrer || req.headers.get("referer") || null,
    utm_source: body.utm_source || null,
    utm_medium: body.utm_medium || null,
    utm_campaign: body.utm_campaign || null,
    landing_path: body.landing_path || null,
    user_agent: req.headers.get("user-agent"),
  });

  if (error) {
    // 23505 = unique_violation → already on the list. Treat as success.
    if (error.code === "23505") {
      return NextResponse.json({ ok: true, alreadyJoined: true });
    }
    console.error("[waitlist] insert error:", error);
    return NextResponse.json(
      { ok: false, error: "Something went wrong. Please try again." },
      { status: 500 }
    );
  }

  return NextResponse.json({ ok: true });
}

// Public, cached count for social proof ("Join N founders").
export async function GET() {
  const supabase = getSupabaseAdmin();
  if (!supabase) return NextResponse.json({ count: 0 });

  const { count } = await supabase
    .from("waitlist")
    .select("*", { count: "exact", head: true });

  return NextResponse.json(
    { count: count ?? 0 },
    { headers: { "Cache-Control": "public, s-maxage=60, stale-while-revalidate=300" } }
  );
}
