"use client";

import { useEffect, useRef, useState } from "react";
import { PixelMoufida } from "./PixelMoufida";

/**
 * Guided tour companion — the same pixel-art Moufida from the desktop app.
 * She greets visitors in the centre of the screen, then settles into the corner
 * and guides them section by section as they scroll.
 */

type Stop = {
  id: string;
  state: string; // character pose for this section
  msg: string;
};

const STOPS: Stop[] = [
  { id: "top", state: "idle", msg: "Hi, I'm Moufida! 👋 Tap me anytime to move on — let's take a look together." },
  { id: "how", state: "presenting", msg: "Here's how I work: idea in, full diagnosis out — in three simple steps." },
  { id: "due-diligence", state: "reading", msg: "I back every claim with real evidence — a full due-diligence report." },
  { id: "features", state: "presenting", msg: "These are the things I can do for your startup, across 10 expert axes." },
  { id: "pricing", state: "presenting", msg: "Simple pricing — and early access is completely free." },
  { id: "faq", state: "thinking", msg: "Got questions? I've probably already answered them right here." },
  { id: "waitlist-final", state: "celebrating", msg: "Ready to build together? Join the waitlist — see you at launch! 🎉" },
];

const INTRO_KEY = "mf_guide_intro";
const DISMISS_KEY = "mf_guide_dismissed";

type Phase = "loading" | "intro" | "tour" | "hidden";

export function Guide() {
  const [phase, setPhase] = useState<Phase>("loading");
  const [stops, setStops] = useState<Stop[]>([]);
  const [active, setActive] = useState(0);
  const [collapsed, setCollapsed] = useState(false);
  const activeRef = useRef(0);
  activeRef.current = active;

  // Decide the opening phase: respect a prior dismiss / completed intro.
  useEffect(() => {
    let dismissed = false;
    let introDone = false;
    try {
      dismissed = sessionStorage.getItem(DISMISS_KEY) === "1";
      introDone = sessionStorage.getItem(INTRO_KEY) === "1";
    } catch {
      /* ignore */
    }
    if (dismissed) {
      setPhase("hidden");
      return;
    }
    const present = STOPS.filter((s) => document.getElementById(s.id));
    if (present.length === 0) {
      setPhase("hidden");
      return;
    }
    setStops(present);
    setPhase(introDone ? "tour" : "intro");
  }, []);

  // Track the section in view → active = last section whose start passed the
  // viewport midpoint. Order-respecting so top anchors can't hijack it.
  useEffect(() => {
    if (phase !== "tour" || stops.length === 0) return;
    let raf = 0;
    const recompute = () => {
      raf = 0;
      const mid = window.scrollY + window.innerHeight * 0.45;
      let idx = 0;
      stops.forEach((s, i) => {
        const el = document.getElementById(s.id);
        if (el && el.getBoundingClientRect().top + window.scrollY <= mid) idx = i;
      });
      setActive(idx);
    };
    const onScroll = () => {
      if (raf === 0) raf = requestAnimationFrame(recompute);
    };
    recompute();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [phase, stops]);

  const remember = (key: string) => {
    try {
      sessionStorage.setItem(key, "1");
    } catch {
      /* ignore */
    }
  };

  const startTour = (showBubble: boolean) => {
    remember(INTRO_KEY);
    setCollapsed(!showBubble);
    setActive(0);
    setPhase("tour");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const goTo = (idx: number) => {
    const stop = stops[idx];
    if (!stop) return;
    document.getElementById(stop.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setActive(idx);
  };

  const goNext = () => goTo((activeRef.current + 1) % stops.length);

  const dismiss = () => {
    setPhase("hidden");
    remember(DISMISS_KEY);
  };

  // ── Welcome intro ───────────────────────────────────────────────
  if (phase === "intro") {
    return (
      <div className="fixed inset-0 z-[60] flex items-center justify-center bg-ink/60 px-6 backdrop-blur-md">
        <div className="animate-fade-up flex w-full max-w-md flex-col items-center rounded-3xl border border-border bg-bg px-8 pb-8 pt-0 text-center shadow-cardHover">
          <span className="-mt-16 drop-shadow-[0_14px_30px_rgba(111,78,55,0.35)]">
            <PixelMoufida state="idle" cssScale={2.1} showName />
          </span>
          <h2 className="mt-3 font-heading text-3xl font-bold text-ink sm:text-4xl">
            Meet Moufida
          </h2>
          <p className="mt-3 text-base leading-relaxed text-muted">
            Hi! I&apos;m your 24/7 AI co-founder. Want me to walk you through
            everything I can do — or would you rather explore on your own?
          </p>
          <div className="mt-7 flex w-full flex-col gap-3 sm:flex-row sm:justify-center">
            <button onClick={() => startTour(true)} className="btn-accent !px-7 !py-3">
              Show me around
            </button>
            <button onClick={() => startTour(false)} className="btn-ghost !px-7 !py-3">
              I&apos;ll explore myself
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (phase !== "tour" || stops.length === 0) return null;

  const stop = stops[active] ?? stops[0];
  const isLast = active === stops.length - 1;

  return (
    <div className="fixed bottom-4 right-4 z-40 flex max-w-[88vw] flex-col items-end gap-2 sm:bottom-6 sm:right-6">
      {/* Speech bubble */}
      {!collapsed && (
        <div
          key={active}
          className="animate-fade-up relative max-w-[17rem] rounded-2xl border border-border bg-surface/95 p-4 shadow-cardHover backdrop-blur-sm"
          role="status"
          aria-live="polite"
        >
          <button
            onClick={() => setCollapsed(true)}
            aria-label="Hide guide message"
            className="absolute right-2.5 top-2.5 text-muted/70 transition-colors hover:text-primary"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
            </svg>
          </button>

          <p className="pr-4 text-sm leading-relaxed text-ink">{stop.msg}</p>

          <div className="mt-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-1.5">
              {stops.map((s, i) => (
                <button
                  key={s.id}
                  onClick={() => goTo(i)}
                  aria-label={`Go to section ${i + 1}`}
                  className={`h-1.5 rounded-full transition-all ${
                    i === active ? "w-4 bg-accent" : "w-1.5 bg-border hover:bg-muted"
                  }`}
                />
              ))}
            </div>

            <button
              onClick={isLast ? dismiss : goNext}
              className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-bg transition-colors hover:bg-primaryDark"
            >
              {isLast ? "Got it" : "Next"}
              {!isLast && (
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </button>
          </div>

          {/* Bubble tail */}
          <div className="absolute -bottom-1.5 right-10 h-3 w-3 rotate-45 border-b border-r border-border bg-surface/95" />
        </div>
      )}

      {/* Character */}
      <button
        onClick={() => (collapsed ? setCollapsed(false) : goNext())}
        aria-label={collapsed ? "Show guide" : "Next section"}
        className="group relative cursor-pointer select-none outline-none"
        title={collapsed ? "Ask Moufida to guide you" : "Tap to continue"}
      >
        <span className="block drop-shadow-[0_8px_18px_rgba(111,78,55,0.28)] transition-transform duration-200 group-hover:scale-105">
          <PixelMoufida state={stop.state} cssScale={1.05} />
        </span>
        {collapsed && (
          <span className="absolute right-1 top-2 h-2.5 w-2.5 animate-pulse-ring rounded-full bg-accent" />
        )}
      </button>
    </div>
  );
}
