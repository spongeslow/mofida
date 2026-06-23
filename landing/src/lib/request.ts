import type { NextRequest } from "next/server";

export interface Geo {
  country: string | null;
  city: string | null;
  region: string | null;
  timezone: string | null;
}

/**
 * Derives coarse, privacy-friendly geo from Vercel's edge headers. No raw IP is
 * ever read or stored. Values are absent locally / off-Vercel.
 */
export function geoFromRequest(req: NextRequest): Geo {
  const h = req.headers;
  const decode = (v: string | null): string | null => {
    if (!v) return null;
    try {
      return decodeURIComponent(v);
    } catch {
      return v;
    }
  };
  return {
    country: h.get("x-vercel-ip-country") || null,
    city: decode(h.get("x-vercel-ip-city")),
    region: h.get("x-vercel-ip-country-region") || null,
    timezone: h.get("x-vercel-ip-timezone") || null,
  };
}

/** Very rough device class from the user-agent string. */
export function deviceFromUA(ua: string | null): string {
  if (!ua) return "unknown";
  const s = ua.toLowerCase();
  if (/ipad|tablet|playbook|silk|(android(?!.*mobile))/.test(s)) return "tablet";
  if (/mobi|iphone|ipod|android.*mobile|windows phone/.test(s)) return "mobile";
  if (/bot|crawl|spider|slurp|bingpreview/.test(s)) return "bot";
  return "desktop";
}

/** Bare hostname of a referrer URL, or null when absent/unparseable. */
export function referrerHost(referrer: string | null): string | null {
  if (!referrer) return null;
  try {
    return new URL(referrer).hostname || null;
  } catch {
    return null;
  }
}

/** Conservative email shape check (real validation happens via double opt-in). */
export function isValidEmail(email: string | undefined): email is string {
  if (!email) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254;
}
