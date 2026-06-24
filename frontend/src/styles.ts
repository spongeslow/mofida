const CSS = `
/* ===================================================================
   MOUFIDA — Global Stylesheet  ·  "Atelier Lumière"
   Warm-autumn brand · Playfair Display + Plus Jakarta Sans
   Paper & ink depth · editorial type · one disciplined accent.
   =================================================================== */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --mf-accent: #C96A2D;
  --mf-accent-rgb: 201, 106, 45;
  --mf-ease: cubic-bezier(0.22, 1, 0.36, 1);
  --mf-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

body {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  background: #F4E9DA;
  color: #2C1E17;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* ── Scrollbars ─────────────────────────────────────────────────── */
.mf-scroll { overflow-y: auto; scrollbar-gutter: stable; }
.mf-scroll::-webkit-scrollbar { width: 9px; }
.mf-scroll::-webkit-scrollbar-track { background: transparent; }
.mf-scroll::-webkit-scrollbar-thumb {
  background: rgba(111, 78, 55, 0.20);
  border-radius: 999px;
  border: 3px solid transparent;
  background-clip: padding-box;
}
.mf-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(111, 78, 55, 0.36);
  background-clip: padding-box;
  border: 3px solid transparent;
}

/* ── Paper grain — fine warm tooth across the canvas ─────────────── */
.mf-grain::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.4;
  mix-blend-mode: multiply;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 0.43 0 0 0 0 0.31 0 0 0 0 0.21 0 0 0 0.05 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

/* ── Card hover lift + accent glow ring ─────────────────────────── */
.mf-card-hover {
  transition: box-shadow 0.32s var(--mf-ease), transform 0.32s var(--mf-ease), border-color 0.32s var(--mf-ease) !important;
  cursor: default;
}
.mf-card-hover:hover {
  box-shadow:
    0 16px 40px rgba(58,38,24,0.14),
    0 30px 70px rgba(58,38,24,0.10),
    0 0 0 1px rgba(var(--mf-accent-rgb), 0.28) !important;
  transform: translateY(-3px);
  border-color: rgba(var(--mf-accent-rgb), 0.32) !important;
}

/* ── View enter animation ───────────────────────────────────────── */
@keyframes mf-view-in {
  from { opacity: 0; transform: translateY(16px) scale(0.992); }
  to   { opacity: 1; transform: none; }
}
.mf-view-enter { animation: mf-view-in 0.46s var(--mf-ease) forwards; }

/* ── Sidebar nav items ──────────────────────────────────────────── */
.mf-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 13px;
  border-radius: 12px;
  cursor: pointer;
  color: #8B6E5A;
  font-size: 13.5px;
  font-weight: 500;
  letter-spacing: 0.005em;
  transition: color 0.2s var(--mf-ease), transform 0.2s var(--mf-ease);
  border: none;
  background: transparent;
  width: 100%;
  text-align: start;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  outline: none;
  isolation: isolate;
}
.mf-nav-item::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: rgba(111, 78, 55, 0.08);
  opacity: 0;
  transform: scale(0.96);
  transition: opacity 0.2s var(--mf-ease), transform 0.2s var(--mf-ease);
  z-index: -1;
}
.mf-nav-item:hover { color: #6F4E37; }
.mf-nav-item:hover::before { opacity: 1; transform: scale(1); }
.mf-nav-item:active { transform: scale(0.985); }
.mf-nav-item.active {
  color: #4A3322;
  font-weight: 650;
}
.mf-nav-item.active::before {
  opacity: 1;
  transform: scale(1);
  background: linear-gradient(100deg, rgba(var(--mf-accent-rgb),0.16), rgba(111,78,55,0.10));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.5);
}
/* Active "you are here" leading bar (logical → works LTR & RTL). */
.mf-nav-item.active::after {
  content: "";
  position: absolute;
  inset-inline-start: -10px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  border-radius: 999px;
  background: var(--mf-accent);
  box-shadow: 0 0 10px rgba(var(--mf-accent-rgb), 0.6);
}
.mf-nav-item:focus-visible { outline-offset: -2px; }

/* Nav section label */
.mf-nav-group-label {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #A9947F;
  padding: 0 14px;
  margin: 16px 0 6px;
}

/* ── Voice pulse indicator ──────────────────────────────────────── */
@keyframes mf-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(201, 106, 45, 0.55); }
  70%  { box-shadow: 0 0 0 9px rgba(201, 106, 45, 0);  }
  100% { box-shadow: 0 0 0 0 rgba(201, 106, 45, 0);    }
}
.mf-voice-pulse { animation: mf-pulse 1.6s ease-out infinite; }

/* ── Companion hover scale ──────────────────────────────────────── */
.mf-companion-wrap { transition: transform 0.3s var(--mf-spring), filter 0.24s ease; }
.mf-companion-wrap:hover { transform: scale(1.07) translateY(-2px); }
.mf-companion-wrap:active { transform: scale(1.0); }

/* ══════════════════════════════════════════════════════════════════
   BUTTONS — primary, accent, ghost, icon. Shine-sweep on emphasis.
   ══════════════════════════════════════════════════════════════════ */
.mf-btn-primary {
  position: relative; overflow: hidden; isolation: isolate;
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  background: linear-gradient(135deg, #7A573E 0%, #6F4E37 55%, #5A3D2B 100%);
  color: #FFF7EE;
  border: none;
  border-radius: 14px;
  padding: 13px 30px;
  font-size: 14.5px;
  font-weight: 650;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  letter-spacing: 0.01em;
  transition: transform 0.18s var(--mf-spring), box-shadow 0.24s var(--mf-ease), filter 0.2s ease;
  box-shadow: 0 6px 20px rgba(111, 78, 55, 0.30), inset 0 1px 0 rgba(255,255,255,0.18);
}
.mf-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(111, 78, 55, 0.40), inset 0 1px 0 rgba(255,255,255,0.22);
  filter: brightness(1.04);
}
.mf-btn-primary:active { transform: translateY(0) scale(0.985); box-shadow: 0 3px 10px rgba(111, 78, 55, 0.24); }

.mf-btn-accent {
  position: relative; overflow: hidden; isolation: isolate;
  display: inline-flex; align-items: center; justify-content: center; gap: 7px;
  background: linear-gradient(135deg, #D98A3A 0%, #C96A2D 60%, #A8521F 100%);
  color: #FFF7EE;
  border: none;
  border-radius: 12px;
  padding: 10px 18px;
  font-size: 13.5px;
  font-weight: 650;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  letter-spacing: 0.01em;
  transition: transform 0.18s var(--mf-spring), box-shadow 0.24s var(--mf-ease), filter 0.2s ease;
  box-shadow: 0 5px 16px rgba(201,106,45,0.34), inset 0 1px 0 rgba(255,255,255,0.22);
  white-space: nowrap;
}
.mf-btn-accent:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(201,106,45,0.44); filter: brightness(1.05); }
.mf-btn-accent:active { transform: translateY(0) scale(0.98); }
.mf-btn-accent:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; transform: none; filter: none; }

.mf-btn-ghost {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(255,252,247,0.66);
  color: #6F4E37;
  border: 1px solid #CBBAA8;
  border-radius: 12px;
  padding: 9px 15px;
  font-size: 13px;
  font-weight: 550;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  transition: background 0.2s var(--mf-ease), border-color 0.2s var(--mf-ease), transform 0.16s var(--mf-spring), box-shadow 0.2s ease;
  white-space: nowrap;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
.mf-btn-ghost:hover { background: #FFFCF7; border-color: #B79E86; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(58,38,24,0.08); }
.mf-btn-ghost:active { transform: translateY(0) scale(0.98); }
.mf-btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

/* Shine-sweep on emphasis buttons */
.mf-btn-primary::after, .mf-btn-accent::after {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 55%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.42), transparent);
  transform: translateX(-180%) skewX(-20deg);
  transition: transform 0.75s var(--mf-ease);
  pointer-events: none;
}
.mf-btn-primary:hover::after, .mf-btn-accent:hover::after { transform: translateX(280%) skewX(-20deg); }

/* Icon button — square, subtle, for chrome controls */
.mf-icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: #8B6E5A;
  cursor: pointer;
  transition: background 0.18s var(--mf-ease), color 0.18s var(--mf-ease), border-color 0.18s var(--mf-ease), transform 0.16s var(--mf-spring);
}
.mf-icon-btn:hover { background: rgba(111,78,55,0.09); color: #6F4E37; border-color: #DBCBB6; }
.mf-icon-btn:active { transform: scale(0.92); }

/* Button press micro-scale (generic utility) */
.mf-press { transition: transform 0.12s var(--mf-spring); }
.mf-press:active { transform: scale(0.97); }

/* ── Inputs ─────────────────────────────────────────────────────── */
.mf-input { transition: border-color 0.2s var(--mf-ease), box-shadow 0.2s var(--mf-ease), background 0.2s var(--mf-ease); }
.mf-input:focus, .mf-input:focus-visible {
  outline: none;
  border-color: var(--mf-accent) !important;
  box-shadow: 0 0 0 4px rgba(var(--mf-accent-rgb), 0.16);
  background: #FFFFFF;
}

/* ── Segmented control (lang switcher etc.) ─────────────────────── */
.mf-segment {
  display: flex; gap: 3px;
  background: #ECDFCC;
  border-radius: 11px;
  padding: 3px;
  border: 1px solid #DBCBB6;
}
.mf-segment-btn {
  flex: 1; border: none; border-radius: 8px;
  padding: 6px 4px; font-size: 12px;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-weight: 550; cursor: pointer;
  background: transparent; color: #8B6E5A;
  transition: all 0.2s var(--mf-ease);
}
.mf-segment-btn:hover { color: #6F4E37; }
.mf-segment-btn.active {
  background: linear-gradient(135deg, #7A573E, #6F4E37);
  color: #FFF7EE; font-weight: 700;
  box-shadow: 0 3px 10px rgba(111,78,55,0.28), inset 0 1px 0 rgba(255,255,255,0.18);
}

/* ── Chips & badges ─────────────────────────────────────────────── */
.mf-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 11px; border-radius: 999px;
  font-size: 11px; font-weight: 600;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  border: 1px solid #DBCBB6; background: rgba(255,252,247,0.6);
  color: #6F4E37;
}

/* Status pill row item in the rail */
.mf-status-pill {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 12px; border-radius: 12px;
  background: rgba(255,252,247,0.55);
  border: 1px solid #DBCBB6;
}

/* ── Entrance animations ────────────────────────────────────────── */
@keyframes mf-slide-up    { from { opacity: 0; transform: translateY(18px); }  to { opacity: 1; transform: none; } }
@keyframes mf-slide-right { from { opacity: 0; transform: translateX(-18px); } to { opacity: 1; transform: none; } }
@keyframes mf-fade-in     { from { opacity: 0; }                                to { opacity: 1; } }
@keyframes mf-scale-in    { from { opacity: 0; transform: scale(0.94); }        to { opacity: 1; transform: scale(1); } }

.mf-anim-card  { animation: mf-slide-up 0.5s var(--mf-ease) both; animation-delay: calc(var(--i, 0) * 60ms); }
.mf-anim-fade  { animation: mf-fade-in 0.34s ease both; }
.mf-anim-scale { animation: mf-scale-in 0.32s var(--mf-ease) both; }
.mf-anim-row   { animation: mf-slide-right 0.3s var(--mf-ease) both; animation-delay: calc(var(--i, 0) * 40ms); }

/* ── Live pulse rings & status dots ─────────────────────────────── */
@keyframes mf-pulse-ring {
  0%   { box-shadow: 0 0 0 0 rgba(var(--mf-accent-rgb), 0.45); }
  70%  { box-shadow: 0 0 0 7px rgba(var(--mf-accent-rgb), 0);  }
  100% { box-shadow: 0 0 0 0 rgba(var(--mf-accent-rgb), 0);    }
}
.mf-live-dot { border-radius: 50%; animation: mf-pulse-ring 2s ease-out infinite; }
.mf-dot-alive  { background: #2E7D32; animation: mf-pulse-ring 2.2s ease-out infinite; }
.mf-dot-paused { background: #C86A00; }
.mf-dot-offline{ background: #9A8C7C; }

/* ── Toast ──────────────────────────────────────────────────────── */
@keyframes mf-toast-in  { from { opacity: 0; transform: translate(-50%, 24px) scale(0.96); } to { opacity: 1; transform: translate(-50%, 0) scale(1); } }
.mf-toast { animation: mf-toast-in 0.36s var(--mf-spring) both; }

/* ── Skeleton shimmer ───────────────────────────────────────────── */
@keyframes mf-shimmer { 0% { background-position: -380px 0; } 100% { background-position: 380px 0; } }
.mf-skeleton {
  background: linear-gradient(90deg, rgba(111,78,55,0.06) 25%, rgba(111,78,55,0.14) 50%, rgba(111,78,55,0.06) 75%);
  background-size: 760px 100%;
  animation: mf-shimmer 1.3s linear infinite;
  border-radius: 8px;
}

/* ── Modal overlay ──────────────────────────────────────────────── */
.mf-overlay-backdrop { animation: mf-fade-in 0.24s ease both; }
.mf-overlay-panel    { animation: mf-scale-in 0.32s var(--mf-ease) both; }

/* ── Subtle dotted texture for content area ─────────────────────── */
.mf-textured {
  background-image: radial-gradient(rgba(var(--mf-accent-rgb), 0.04) 1px, transparent 1px);
  background-size: 24px 24px;
}

/* ══════════════════════════════════════════════════════════════════
   LAYOUT — section grammar, hero, responsive grid
   ══════════════════════════════════════════════════════════════════ */
.mf-dash-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: start;
}
@media (max-width: 1080px) { .mf-dash-grid-2 { grid-template-columns: 1fr; } }

/* Intro-aside + content layout (Personas, etc.) */
.mf-aside-grid {
  display: grid;
  grid-template-columns: minmax(260px, 320px) 1fr;
  gap: 20px;
  align-items: stretch;
}
@media (max-width: 900px) { .mf-aside-grid { grid-template-columns: 1fr; } }

/* Auto-fill card grid (personas, etc.) */
.mf-fill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 14px;
  align-content: start;
}

/* Scenario planner — editors column + results column */
.mf-planner-grid {
  display: grid;
  grid-template-columns: minmax(330px, 430px) 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 980px) { .mf-planner-grid { grid-template-columns: 1fr; } }

/* Section heading: eyebrow label that breaks the page into chapters. */
.mf-section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 10px 2px 0;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.13em;
  color: #8B6E5A;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}
.mf-section-title::before {
  content: "";
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--mf-accent);
  flex-shrink: 0;
  box-shadow: 0 0 8px rgba(var(--mf-accent-rgb), 0.5);
}
.mf-section-title::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(203,186,168,0.85), transparent);
}

/* Hero — glass paper banner with ambient accent bloom + sheen sweep. */
.mf-hero {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid rgba(255,255,255,0.55);
  background:
    radial-gradient(130% 150% at 90% -20%, rgba(var(--mf-accent-rgb), 0.18) 0%, transparent 52%),
    linear-gradient(160deg, rgba(255,252,247,0.86) 0%, rgba(239,227,211,0.74) 60%, rgba(231,216,196,0.7) 100%);
  backdrop-filter: blur(14px) saturate(1.2);
  -webkit-backdrop-filter: blur(14px) saturate(1.2);
  box-shadow:
    0 22px 60px rgba(58,38,24,0.16),
    0 6px 18px rgba(58,38,24,0.08),
    inset 0 1px 0 rgba(255,255,255,0.7);
}
.mf-hero::after {
  content: "";
  position: absolute; inset: 0;
  background-image: radial-gradient(rgba(111,78,55,0.05) 1px, transparent 1px);
  background-size: 22px 22px;
  pointer-events: none;
  opacity: 0.5;
}
@keyframes mf-sheen { 0% { transform: translateX(-130%) skewX(-18deg); } 100% { transform: translateX(240%) skewX(-18deg); } }
.mf-hero::before {
  content: "";
  position: absolute;
  top: 0; bottom: 0; left: 0;
  width: 40%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.34), transparent);
  transform: translateX(-130%) skewX(-18deg);
  animation: mf-sheen 8s ease-in-out 1.4s infinite;
  pointer-events: none;
  z-index: 0;
}

/* Stat chip in hero summary strip. */
.mf-stat-chip {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 15px;
  border-radius: 14px;
  background: rgba(255,252,247,0.55);
  border: 1px solid rgba(219,203,182,0.8);
  min-width: 96px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
  transition: transform 0.2s var(--mf-spring), box-shadow 0.2s ease;
}
.mf-stat-chip:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(58,38,24,0.10); }

/* ══════════════════════════════════════════════════════════════════
   CINEMATIC LAYER — ambient aurora, glass, animated wordmark
   Calmer than a screensaver: slow ambient warmth, premium depth.
   ══════════════════════════════════════════════════════════════════ */
@keyframes mf-aurora-a { 0%,100% { transform: translate(0,0) scale(1);    } 50% { transform: translate(6%,4%) scale(1.14);  } }
@keyframes mf-aurora-b { 0%,100% { transform: translate(0,0) scale(1.05); } 50% { transform: translate(-7%,-3%) scale(0.92);} }
@keyframes mf-aurora-c { 0%,100% { transform: translate(0,0) scale(0.95); } 50% { transform: translate(4%,-5%) scale(1.1);  } }
.mf-aurora { position: absolute; inset: 0; z-index: 0; overflow: hidden; pointer-events: none; }
.mf-aurora span { position: absolute; border-radius: 50%; filter: blur(80px); will-change: transform; }
.mf-aurora .orb-1 {
  width: 48vw; height: 48vw; top: -18%; right: -12%;
  background: radial-gradient(circle, rgba(var(--mf-accent-rgb), 0.30), transparent 66%);
  animation: mf-aurora-a 22s ease-in-out infinite;
}
.mf-aurora .orb-2 {
  width: 42vw; height: 42vw; bottom: -20%; left: -14%;
  background: radial-gradient(circle, rgba(111, 78, 55, 0.24), transparent 66%);
  animation: mf-aurora-b 27s ease-in-out infinite;
}
.mf-aurora .orb-3 {
  width: 32vw; height: 32vw; top: 32%; left: 38%;
  background: radial-gradient(circle, rgba(217, 138, 58, 0.20), transparent 68%);
  animation: mf-aurora-c 31s ease-in-out infinite;
}

/* Animated gradient wordmark */
@keyframes mf-grad-pan { 0% { background-position: 0% 50%; } 100% { background-position: 200% 50%; } }
.mf-wordmark {
  background: linear-gradient(100deg, #6F4E37 0%, #C96A2D 28%, #D98A3A 50%, #C96A2D 72%, #6F4E37 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: mf-grad-pan 7s linear infinite;
}

/* Glass surface — translucent, blurred, top inner highlight */
.mf-glass {
  background: linear-gradient(160deg, rgba(255,252,247,0.78) 0%, rgba(239,227,211,0.6) 100%);
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow:
    0 20px 54px rgba(58,38,24,0.18),
    0 4px 14px rgba(58,38,24,0.10),
    inset 0 1px 0 rgba(255,255,255,0.72);
}

/* Soft drifting float for hero decorations */
@keyframes mf-float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }
.mf-float { animation: mf-float 6.5s ease-in-out infinite; }

/* Glow pulse for the marquee CTA */
@keyframes mf-cta-glow {
  0%, 100% { box-shadow: 0 8px 26px rgba(var(--mf-accent-rgb), 0.40), 0 0 0 0 rgba(var(--mf-accent-rgb), 0.30); }
  50%      { box-shadow: 0 14px 36px rgba(var(--mf-accent-rgb), 0.56), 0 0 30px 5px rgba(var(--mf-accent-rgb), 0.22); }
}
.mf-cta-glow { animation: mf-cta-glow 3.4s ease-in-out infinite; }

/* Soft halo pedestal for the mascot */
@keyframes mf-halo { 0%,100% { opacity: 0.7; transform: translateX(-50%) scale(1); } 50% { opacity: 1; transform: translateX(-50%) scale(1.08); } }
.mf-halo { animation: mf-halo 4s ease-in-out infinite; }

/* ══════════════════════════════════════════════════════════════════
   Accessibility & cross-cutting polish
   ══════════════════════════════════════════════════════════════════ */
*:focus { outline: none; }
*:focus-visible {
  outline: 2px solid rgba(var(--mf-accent-rgb), 0.85);
  outline-offset: 2px;
  border-radius: 6px;
}
::selection { background: rgba(var(--mf-accent-rgb), 0.28); color: #2C1E17; }
button:disabled { cursor: not-allowed; }

/* Respect reduced-motion: drop loops & decorative transitions; collapse
   single-shot entrances to their final frame; keep content legible. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
  .mf-aurora, .mf-live-dot, .mf-dot-alive, .mf-voice-pulse,
  .mf-skeleton, .mf-companion-wrap, .mf-float, .mf-cta-glow, .mf-halo,
  .mf-hero::before { animation: none !important; }
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
