"use client";

/**
 * Lightweight, cookie-free client analytics. A per-tab random session id lives
 * in sessionStorage; UTM params + referrer are captured for attribution. All
 * calls are best-effort and must never throw into the page.
 */

const SESSION_KEY = "mf_session_id";

function sessionId(): string {
  if (typeof window === "undefined") return "";
  try {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
      id =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return "";
  }
}

export interface Attribution {
  referrer: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  landing_path: string;
}

/** Captures UTM params, referrer, and the current path for form submissions. */
export function getAttribution(): Attribution {
  if (typeof window === "undefined") {
    return { referrer: "", utm_source: "", utm_medium: "", utm_campaign: "", landing_path: "" };
  }
  const params = new URLSearchParams(window.location.search);
  return {
    referrer: document.referrer || "",
    utm_source: params.get("utm_source") || "",
    utm_medium: params.get("utm_medium") || "",
    utm_campaign: params.get("utm_campaign") || "",
    landing_path: window.location.pathname || "",
  };
}

/** Fires a single page view to /api/track. Silent on any failure. */
export function trackPageview(): void {
  if (typeof window === "undefined") return;
  const attr = getAttribution();
  const payload = {
    session_id: sessionId(),
    path: window.location.pathname,
    referrer: attr.referrer,
    utm_source: attr.utm_source,
    utm_medium: attr.utm_medium,
    utm_campaign: attr.utm_campaign,
  };
  try {
    fetch("/api/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* never let analytics break the page */
  }
}
