const CSS = `
/* ===================================================================
   MOUFIDA — Global Stylesheet
   Warm Autumn palette · Playfair Display + Plus Jakarta Sans
   =================================================================== */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  background: #F5EBDD;
  color: #2C1E17;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Scrollbars ─────────────────────────────────────────────────── */
.mf-scroll { overflow-y: auto; }
.mf-scroll::-webkit-scrollbar { width: 5px; }
.mf-scroll::-webkit-scrollbar-track { background: transparent; }
.mf-scroll::-webkit-scrollbar-thumb {
  background: rgba(111, 78, 55, 0.22);
  border-radius: 6px;
}
.mf-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(111, 78, 55, 0.38);
}

/* ── Card hover lift ────────────────────────────────────────────── */
.mf-card-hover {
  transition: box-shadow 0.22s ease, transform 0.22s ease !important;
  cursor: default;
}
.mf-card-hover:hover {
  box-shadow: 0 8px 32px rgba(111,78,55,0.13), 0 2px 8px rgba(111,78,55,0.07) !important;
  transform: translateY(-2px);
}

/* ── View enter animation ───────────────────────────────────────── */
@keyframes mf-view-in {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0);    }
}
.mf-view-enter {
  animation: mf-view-in 0.34s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

/* ── Sidebar nav items ──────────────────────────────────────────── */
.mf-nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px 14px;
  border-radius: 12px;
  cursor: pointer;
  color: #8B6E5A;
  font-size: 13.5px;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: background 0.18s ease, color 0.18s ease;
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  outline: none;
}
.mf-nav-item:hover {
  background: rgba(111, 78, 55, 0.09);
  color: #6F4E37;
}
.mf-nav-item.active {
  background: rgba(111, 78, 55, 0.13);
  color: #6F4E37;
  font-weight: 600;
}

/* ── Voice pulse indicator ──────────────────────────────────────── */
@keyframes mf-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(201, 106, 45, 0.55); }
  70%  { box-shadow: 0 0 0 9px rgba(201, 106, 45, 0);  }
  100% { box-shadow: 0 0 0 0 rgba(201, 106, 45, 0);    }
}
.mf-voice-pulse { animation: mf-pulse 1.6s ease-out infinite; }

/* ── Companion hover scale ──────────────────────────────────────── */
.mf-companion-wrap { transition: transform 0.24s cubic-bezier(0.34,1.56,0.64,1), filter 0.2s ease; }
.mf-companion-wrap:hover { transform: scale(1.06); }

/* ── Primary & accent buttons ───────────────────────────────────── */
.mf-btn-primary {
  background: #6F4E37;
  color: #F5EBDD;
  border: none;
  border-radius: 12px;
  padding: 13px 34px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(111, 78, 55, 0.28);
}
.mf-btn-primary:hover {
  background: #5A3D2B;
  box-shadow: 0 6px 22px rgba(111, 78, 55, 0.38);
  transform: translateY(-1px);
}
.mf-btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(111, 78, 55, 0.22);
}

/* ── Input focus ring ───────────────────────────────────────────── */
.mf-input:focus {
  outline: none;
  border-color: #C96A2D !important;
  box-shadow: 0 0 0 3px rgba(201, 106, 45, 0.18);
}

/* ──────────────────────────────────────────────────────────────────
   MOUFIDA CHARACTER — CSS Animations
   ────────────────────────────────────────────────────────────────── */

/* --- Character root group --- */
.mf-char {
  transform-box: fill-box;
  transform-origin: center bottom;
  transition: opacity 0.55s ease;
}

/* --- Keyframes --- */
@keyframes mf-idle {
  0%,  100% { transform: translateY(0px)  rotate(0deg);   }
  35%        { transform: translateY(-7px) rotate(0.6deg); }
  65%        { transform: translateY(-4px) rotate(-0.5deg);}
}
@keyframes mf-listen {
  0%,  100% { transform: translateY(-2px) rotate(-4deg); }
  50%        { transform: translateY(-6px) rotate(-7deg); }
}
@keyframes mf-think {
  0%,  100% { transform: translateY(0px) rotate(0deg);    }
  25%        { transform: translateY(-5px) rotate(2.5deg); }
  75%        { transform: translateY(-5px) rotate(-2.5deg);}
}
@keyframes mf-speak-body {
  0%,  100% { transform: translateY(0px) scale(1);      }
  50%        { transform: translateY(-3px) scale(1.012); }
}
@keyframes mf-alert-jump {
  0%   { transform: translateY(0)    rotate(0deg)   scale(1);    }
  12%  { transform: translateY(-34px) rotate(13deg) scale(1.07); }
  28%  { transform: translateY(-34px) rotate(-13deg) scale(1.07);}
  44%  { transform: translateY(-20px) rotate(8deg)  scale(1.03); }
  58%  { transform: translateY(-20px) rotate(-8deg) scale(1.03); }
  78%  { transform: translateY(-6px)  rotate(2deg)  scale(1.01); }
  100% { transform: translateY(0)    rotate(0deg)   scale(1);    }
}
@keyframes mf-celebrate {
  0%   { transform: translateY(0)    rotate(0deg)   scale(1);    }
  18%  { transform: translateY(-24px) rotate(15deg) scale(1.09); }
  38%  { transform: translateY(-14px) rotate(-12deg) scale(1.05);}
  58%  { transform: translateY(-24px) rotate(12deg)  scale(1.1); }
  78%  { transform: translateY(-14px) rotate(-15deg) scale(1.07);}
  100% { transform: translateY(0)    rotate(0deg)   scale(1);    }
}
@keyframes mf-sleep {
  0%,  100% { transform: translateY(0px) scaleY(1);     }
  50%        { transform: translateY(3px) scaleY(0.974); }
}
@keyframes mf-mouth-flap {
  0%,  100% { transform: scaleY(0.14); }
  45%, 55%  { transform: scaleY(1);    }
}
@keyframes mf-zzz-1 {
  0%   { opacity: 0; transform: translate(0, 0)    scale(0.5); }
  18%  { opacity: 1;                                            }
  100% { opacity: 0; transform: translate(13px,-28px) scale(1.1); }
}
@keyframes mf-zzz-2 {
  0%   { opacity: 0; transform: translate(0, 0)    scale(0.5); }
  18%  { opacity: 1;                                            }
  100% { opacity: 0; transform: translate(17px,-36px) scale(1.35); }
}
@keyframes mf-think-pulse {
  0%,  100% { opacity: 0.68; transform: scale(0.94); }
  50%        { opacity: 1;    transform: scale(1.06); }
}
@keyframes mf-blink {
  0%, 82%, 100% { transform: scaleY(1);    }
  88%, 94%      { transform: scaleY(0.06); }
}
@keyframes mf-sparkle-a {
  0%   { opacity: 0; transform: scale(0) rotate(0deg);   }
  25%  { opacity: 1; transform: scale(1) rotate(60deg);  }
  70%  { opacity: 0.85; transform: scale(1.2) rotate(150deg); }
  100% { opacity: 0; transform: scale(0) rotate(360deg); }
}
@keyframes mf-sparkle-b {
  0%   { opacity: 0; transform: scale(0) rotate(0deg);    }
  35%  { opacity: 1; transform: scale(0.9) rotate(-80deg);}
  75%  { opacity: 0.9; transform: scale(1.3) rotate(-180deg); }
  100% { opacity: 0; transform: scale(0) rotate(-360deg); }
}
@keyframes mf-sparkle-c {
  0%   { opacity: 0; transform: scale(0) rotate(0deg);   }
  20%  { opacity: 0.9; transform: scale(1) rotate(45deg); }
  65%  { opacity: 1; transform: scale(1.1) rotate(120deg);}
  100% { opacity: 0; transform: scale(0) rotate(270deg);  }
}

/* --- State classes --- */
.mf-char.idle        { animation: mf-idle       3.4s ease-in-out infinite;  opacity: 0.92; }
.mf-char.listening   { animation: mf-listen     1.5s ease-in-out infinite;  opacity: 1;    }
.mf-char.thinking,
.mf-char.processing  { animation: mf-think      1.1s ease-in-out infinite;  opacity: 1;    }
.mf-char.speaking    { animation: mf-speak-body 0.38s ease-in-out infinite; opacity: 1;    }
.mf-char.alert       { animation: mf-alert-jump 1.9s ease-in-out 2;        opacity: 1;    }
.mf-char.celebrating { animation: mf-celebrate  0.72s ease-in-out infinite; opacity: 1;    }
.mf-char.sleeping    { animation: mf-sleep      4.5s ease-in-out infinite;  opacity: 0.65; }

/* --- Eye blink --- */
.mf-eye-group {
  transform-box: fill-box;
  transform-origin: center center;
  animation: mf-blink 5.5s ease-in-out infinite;
}
.mf-char.sleeping .mf-eye-group      { animation: none; opacity: 0; transition: opacity 0.4s ease; }
.mf-eye-closed-group                 { opacity: 0; transition: opacity 0.4s ease; }
.mf-char.sleeping .mf-eye-closed-group { opacity: 1; }

/* --- Mouth --- */
.mf-mouth-smile, .mf-mouth-smile-teeth { transition: opacity 0.12s ease; }
.mf-mouth-open {
  opacity: 0;
  transform-box: fill-box;
  transform-origin: center top;
  transition: opacity 0.12s ease;
}
.mf-char.speaking .mf-mouth-smile       { opacity: 0; }
.mf-char.speaking .mf-mouth-smile-teeth { opacity: 0; }
.mf-char.speaking .mf-mouth-open        { opacity: 1; animation: mf-mouth-flap 0.27s ease-in-out infinite; }

/* --- Thinking bubble --- */
.mf-think-bubble {
  opacity: 0;
  transition: opacity 0.35s ease;
  transform-box: fill-box;
  transform-origin: center;
}
.mf-char.thinking .mf-think-bubble,
.mf-char.processing .mf-think-bubble { opacity: 1; animation: mf-think-pulse 1.1s ease-in-out infinite; }

/* --- Sleeping ZZZs --- */
.mf-sleep-zzz { opacity: 0; pointer-events: none; }
.mf-char.sleeping .mf-sleep-zzz { opacity: 1; }
.mf-char.sleeping .mf-zzz-1 { animation: mf-zzz-1 2.8s ease-out infinite; }
.mf-char.sleeping .mf-zzz-2 { animation: mf-zzz-2 2.8s ease-out 1.4s infinite; }

/* --- Celebrating sparkles --- */
.mf-sparkles { opacity: 0; pointer-events: none; }
.mf-char.celebrating .mf-sparkles { opacity: 1; }
.mf-char.celebrating .mf-sparkle-1 { transform-box: fill-box; transform-origin: center; animation: mf-sparkle-a 0.85s ease-in-out infinite; }
.mf-char.celebrating .mf-sparkle-2 { transform-box: fill-box; transform-origin: center; animation: mf-sparkle-b 0.85s ease-in-out 0.28s infinite; }
.mf-char.celebrating .mf-sparkle-3 { transform-box: fill-box; transform-origin: center; animation: mf-sparkle-c 0.85s ease-in-out 0.56s infinite; }

/* ──────────────────────────────────────────────────────────────────
   H5 — Sector-adaptive accent + animation system + decorations
   ────────────────────────────────────────────────────────────────── */

/* Accent custom properties (overridden per-sector at runtime by setAccent()). */
:root {
  --mf-accent: #C96A2D;
  --mf-accent-rgb: 201, 106, 45;
}

/* --- Entrance animations --- */
@keyframes mf-slide-up    { from { opacity: 0; transform: translateY(16px); }  to { opacity: 1; transform: none; } }
@keyframes mf-slide-right { from { opacity: 0; transform: translateX(-16px); } to { opacity: 1; transform: none; } }
@keyframes mf-fade-in     { from { opacity: 0; }                                to { opacity: 1; } }
@keyframes mf-scale-in    { from { opacity: 0; transform: scale(0.94); }        to { opacity: 1; transform: scale(1); } }

.mf-anim-card  { animation: mf-slide-up 0.36s cubic-bezier(0.22,1,0.36,1) both; animation-delay: calc(var(--i, 0) * 55ms); }
.mf-anim-fade  { animation: mf-fade-in 0.3s ease both; }
.mf-anim-scale { animation: mf-scale-in 0.26s cubic-bezier(0.22,1,0.36,1) both; }
.mf-anim-row   { animation: mf-slide-right 0.28s cubic-bezier(0.22,1,0.36,1) both; }

/* --- Live pulse ring (uses accent) --- */
@keyframes mf-pulse-ring {
  0%   { box-shadow: 0 0 0 0 rgba(var(--mf-accent-rgb), 0.45); }
  70%  { box-shadow: 0 0 0 7px rgba(var(--mf-accent-rgb), 0);  }
  100% { box-shadow: 0 0 0 0 rgba(var(--mf-accent-rgb), 0);    }
}
.mf-live-dot { border-radius: 50%; animation: mf-pulse-ring 2s ease-out infinite; }

/* --- Daemon status pill dots --- */
.mf-dot-alive  { background: #2E7D32; animation: mf-pulse-ring 2.2s ease-out infinite; }
.mf-dot-paused { background: #C86A00; }
.mf-dot-offline{ background: #9A8C7C; }

/* --- Toast --- */
@keyframes mf-toast-in  { from { opacity: 0; transform: translateX(24px); } to { opacity: 1; transform: none; } }
.mf-toast { animation: mf-toast-in 0.28s cubic-bezier(0.22,1,0.36,1) both; }

/* --- Skeleton shimmer --- */
@keyframes mf-shimmer { 0% { background-position: -380px 0; } 100% { background-position: 380px 0; } }
.mf-skeleton {
  background: linear-gradient(90deg, rgba(111,78,55,0.07) 25%, rgba(111,78,55,0.15) 50%, rgba(111,78,55,0.07) 75%);
  background-size: 760px 100%;
  animation: mf-shimmer 1.3s linear infinite;
  border-radius: 8px;
}

/* --- Modal overlay backdrop --- */
.mf-overlay-backdrop { animation: mf-fade-in 0.2s ease both; }
.mf-overlay-panel    { animation: mf-scale-in 0.26s cubic-bezier(0.22,1,0.36,1) both; }

/* --- Subtle background texture for content area --- */
.mf-textured {
  background-image: radial-gradient(rgba(var(--mf-accent-rgb), 0.05) 1px, transparent 1px);
  background-size: 22px 22px;
}

/* --- Button press --- */
.mf-press { transition: transform 0.12s ease; }
.mf-press:active { transform: scale(0.97); }

/* ──────────────────────────────────────────────────────────────────
   Dashboard layout — hierarchy, hero, responsive grid
   ────────────────────────────────────────────────────────────────── */

/* Two-column content grid that collapses on narrow windows. */
.mf-dash-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: start;
}
@media (max-width: 1080px) {
  .mf-dash-grid-2 { grid-template-columns: 1fr; }
}

/* Section heading: small eyebrow label that breaks the page into chapters. */
.mf-section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 6px 2px 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: #8B6E5A;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}
.mf-section-title::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(203,186,168,0.7), transparent);
}

/* Hero header — warm gradient banner that anchors the dashboard. */
.mf-hero {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  border: 1px solid #CBBAA8;
  background:
    radial-gradient(120% 140% at 88% -10%, rgba(var(--mf-accent-rgb), 0.16) 0%, transparent 55%),
    linear-gradient(135deg, #EFE3D2 0%, #EDE0CE 60%, #E7D8C4 100%);
  box-shadow: 0 4px 24px rgba(111,78,55,0.10), 0 1px 4px rgba(111,78,55,0.05);
}
.mf-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(111,78,55,0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
  opacity: 0.6;
}

/* Stat chip in the hero summary strip. */
.mf-stat-chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 9px 14px;
  border-radius: 12px;
  background: rgba(255,255,255,0.42);
  border: 1px solid rgba(203,186,168,0.6);
  min-width: 92px;
}

/* Accent (CTA) button — primary diagnostic action. */
.mf-btn-accent {
  background: #C96A2D;
  color: #FFF7EE;
  border: none;
  border-radius: 10px;
  padding: 9px 18px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  letter-spacing: 0.01em;
  transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.12s ease;
  box-shadow: 0 3px 12px rgba(201,106,45,0.30);
  white-space: nowrap;
}
.mf-btn-accent:hover { background: #D98A3A; box-shadow: 0 5px 18px rgba(201,106,45,0.38); transform: translateY(-1px); }
.mf-btn-accent:active { transform: translateY(0) scale(0.98); }
.mf-btn-accent:disabled { opacity: 0.55; cursor: default; box-shadow: none; transform: none; }

/* Ghost button — secondary actions in the hero action bar. */
.mf-btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.5);
  color: #6F4E37;
  border: 1px solid #CBBAA8;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.12s ease;
  white-space: nowrap;
}
.mf-btn-ghost:hover { background: rgba(255,255,255,0.85); border-color: #B79E86; }
.mf-btn-ghost:active { transform: scale(0.98); }
.mf-btn-ghost:disabled { opacity: 0.5; cursor: default; }

/* ──────────────────────────────────────────────────────────────────
   H5.1 — Additional character states + costume overlays
   ────────────────────────────────────────────────────────────────── */
@keyframes mf-skeptic {
  0%, 100% { transform: translateY(0) rotate(-1deg); }
  50%      { transform: translateY(-2px) rotate(1deg); }
}
@keyframes mf-present {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%      { transform: translateY(-4px) rotate(1.5deg); }
}
@keyframes mf-worried {
  0%, 100% { transform: translateY(2px) rotate(0deg) scaleY(0.98); }
  50%      { transform: translateY(3px) rotate(-1deg) scaleY(0.97); }
}
@keyframes mf-surprised {
  0%   { transform: translateY(0) scale(1); }
  30%  { transform: translateY(-8px) scale(1.05); }
  60%  { transform: translateY(-2px) scale(1.02); }
  100% { transform: translateY(0) scale(1); }
}
@keyframes mf-reading {
  0%, 100% { transform: translateY(0) rotate(-3deg); }
  50%      { transform: translateY(-2px) rotate(-5deg); }
}
.mf-char.skeptic    { animation: mf-skeptic   2.6s ease-in-out infinite; opacity: 1; }
.mf-char.presenting { animation: mf-present    2.2s ease-in-out infinite; opacity: 1; }
.mf-char.pointing_left { animation: mf-present 2.2s ease-in-out infinite; opacity: 1; }
.mf-char.worried    { animation: mf-worried   2.8s ease-in-out infinite; opacity: 0.92; }
.mf-char.surprised  { animation: mf-surprised 1.1s ease-in-out 2;        opacity: 1; }
.mf-char.reading    { animation: mf-reading   3.0s ease-in-out infinite; opacity: 1; }

/* Costume overlays: hidden by default, shown for matching state. */
.mf-costume-skeptic, .mf-costume-presenting { opacity: 0; transition: opacity 0.4s ease; }
.mf-char.skeptic .mf-costume-skeptic        { opacity: 1; }
.mf-char.presenting .mf-costume-presenting,
.mf-char.pointing_left .mf-costume-presenting { opacity: 1; }
/* Skeptic darkens the dress + shows a frown; worried shows the frown too. */
.mf-char.skeptic .mf-dress-main,
.mf-char.worried .mf-dress-main { fill: #8B4A1E; transition: fill 0.4s ease; }
.mf-char.skeptic .mf-mouth-smile,
.mf-char.worried .mf-mouth-smile { opacity: 0; }
.mf-char.skeptic .mf-mouth-frown,
.mf-char.worried .mf-mouth-frown { opacity: 1; }
.mf-mouth-frown { opacity: 0; transition: opacity 0.2s ease; }

/* ══════════════════════════════════════════════════════════════════
   CINEMATIC LAYER — ambient aurora, glass, glow, gradient chrome
   The "jury wow" pass: depth + slow ambient motion over the warm
   identity. Every effect degrades gracefully under reduced-motion.
   ══════════════════════════════════════════════════════════════════ */

/* --- Living aurora: slow-drifting warm light blooms behind content --- */
@keyframes mf-aurora-a {
  0%, 100% { transform: translate(0, 0) scale(1);        }
  50%      { transform: translate(7%, 5%) scale(1.18);   }
}
@keyframes mf-aurora-b {
  0%, 100% { transform: translate(0, 0) scale(1.05);     }
  50%      { transform: translate(-8%, -4%) scale(0.9);  }
}
@keyframes mf-aurora-c {
  0%, 100% { transform: translate(0, 0) scale(0.95);     }
  50%      { transform: translate(5%, -6%) scale(1.12);  }
}
.mf-aurora {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}
.mf-aurora span {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  will-change: transform;
}
.mf-aurora .orb-1 {
  width: 50vw; height: 50vw; top: -16%; right: -10%;
  background: radial-gradient(circle, rgba(var(--mf-accent-rgb), 0.42), transparent 66%);
  animation: mf-aurora-a 19s ease-in-out infinite;
}
.mf-aurora .orb-2 {
  width: 44vw; height: 44vw; bottom: -18%; left: -12%;
  background: radial-gradient(circle, rgba(111, 78, 55, 0.34), transparent 66%);
  animation: mf-aurora-b 23s ease-in-out infinite;
}
.mf-aurora .orb-3 {
  width: 34vw; height: 34vw; top: 30%; left: 36%;
  background: radial-gradient(circle, rgba(217, 138, 58, 0.30), transparent 68%);
  animation: mf-aurora-c 27s ease-in-out infinite;
}

/* --- Animated gradient wordmark --- */
@keyframes mf-grad-pan { 0% { background-position: 0% 50%; } 100% { background-position: 200% 50%; } }
.mf-wordmark {
  background: linear-gradient(100deg, #6F4E37 0%, #C96A2D 28%, #D98A3A 50%, #C96A2D 72%, #6F4E37 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: mf-grad-pan 6s linear infinite;
}

/* --- Glass surface: translucent, blurred, with a top inner highlight --- */
.mf-glass {
  background: linear-gradient(160deg, rgba(255,250,243,0.78) 0%, rgba(243,232,216,0.62) 100%);
  backdrop-filter: blur(18px) saturate(1.25);
  -webkit-backdrop-filter: blur(18px) saturate(1.25);
  border: 1px solid rgba(255,255,255,0.55);
  box-shadow:
    0 18px 50px rgba(111,78,55,0.18),
    0 4px 14px rgba(111,78,55,0.10),
    inset 0 1px 0 rgba(255,255,255,0.7);
}

/* --- Hero: glass + ambient accent bloom + soft sheen sweep --- */
.mf-hero {
  backdrop-filter: blur(10px) saturate(1.15);
  -webkit-backdrop-filter: blur(10px) saturate(1.15);
  box-shadow:
    0 22px 60px rgba(111,78,55,0.16),
    0 6px 18px rgba(111,78,55,0.08),
    inset 0 1px 0 rgba(255,255,255,0.65) !important;
}
@keyframes mf-sheen { 0% { transform: translateX(-120%) skewX(-18deg); } 100% { transform: translateX(220%) skewX(-18deg); } }
.mf-hero::before {
  content: "";
  position: absolute;
  top: 0; bottom: 0; left: 0;
  width: 42%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.40), transparent);
  transform: translateX(-120%) skewX(-18deg);
  animation: mf-sheen 7s ease-in-out 1.2s infinite;
  pointer-events: none;
  z-index: 0;
}

/* --- Card hover: lift + accent glow ring --- */
.mf-card-hover:hover {
  box-shadow:
    0 16px 44px rgba(111,78,55,0.16),
    0 4px 12px rgba(111,78,55,0.08),
    0 0 0 1px rgba(var(--mf-accent-rgb), 0.30) !important;
  transform: translateY(-3px);
}

/* --- Shine-sweep on primary & accent buttons --- */
.mf-btn-primary, .mf-btn-accent { position: relative; overflow: hidden; isolation: isolate; }
.mf-btn-primary::after, .mf-btn-accent::after {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent);
  transform: translateX(-160%) skewX(-20deg);
  transition: transform 0.7s cubic-bezier(0.22,1,0.36,1);
  pointer-events: none;
}
.mf-btn-primary:hover::after, .mf-btn-accent:hover::after { transform: translateX(260%) skewX(-20deg); }

/* --- Soft drifting float for hero decorations --- */
@keyframes mf-float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }
.mf-float { animation: mf-float 6s ease-in-out infinite; }

/* --- Glow pulse for the marquee CTA --- */
@keyframes mf-cta-glow {
  0%, 100% { box-shadow: 0 8px 26px rgba(var(--mf-accent-rgb), 0.40), 0 0 0 0 rgba(var(--mf-accent-rgb), 0.30); }
  50%      { box-shadow: 0 12px 34px rgba(var(--mf-accent-rgb), 0.55), 0 0 26px 4px rgba(var(--mf-accent-rgb), 0.22); }
}
.mf-cta-glow { animation: mf-cta-glow 3.2s ease-in-out infinite; }

/* ──────────────────────────────────────────────────────────────────
   Accessibility & cross-cutting polish
   ────────────────────────────────────────────────────────────────── */

/* Keyboard focus ring — only shows for keyboard nav, never on mouse click.
   Uses the sector accent so it harmonises with the active theme. */
*:focus { outline: none; }
*:focus-visible {
  outline: 2px solid rgba(var(--mf-accent-rgb), 0.85);
  outline-offset: 2px;
  border-radius: 6px;
}
.mf-nav-item:focus-visible {
  outline-offset: -2px;
}

/* Warm text-selection highlight to match the palette. */
::selection {
  background: rgba(var(--mf-accent-rgb), 0.28);
  color: #2C1E17;
}

/* Active nav item: accent bar on the leading edge for a clearer
   "you are here" cue (logical property → works in both LTR & RTL). */
.mf-nav-item { position: relative; }
.mf-nav-item.active::before {
  content: "";
  position: absolute;
  inset-inline-start: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  border-radius: 3px;
  background: var(--mf-accent);
}

/* Consistent disabled affordance for all buttons. */
button:disabled { cursor: not-allowed; }

/* Respect users who prefer reduced motion: drop the looping/idle
   character animations and decorative transitions, keep content legible.
   Single-shot entrance animations collapse to their final frame. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
  .mf-char, .mf-live-dot, .mf-dot-alive, .mf-voice-pulse,
  .mf-skeleton, .mf-companion-wrap { animation: none !important; }
}
`;

export function injectStyles(): void {
  if (typeof document === "undefined") return;
  if (document.getElementById("mf-global-styles")) return;
  const el = document.createElement("style");
  el.id = "mf-global-styles";
  el.textContent = CSS;
  document.head.appendChild(el);
}
