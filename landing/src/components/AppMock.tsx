import { Icon } from "./Icon";

/** A lightweight, image-free mock of the Moufida dashboard for the hero. */

const SCORES = [
  { label: "Market", value: 4.1, color: "#1D4ED8" },
  { label: "Product", value: 3.4, color: "#6D28D9" },
  { label: "Finance", value: 2.6, color: "#B45309" },
  { label: "Scale", value: 3.8, color: "#059669" },
];

function Gauge({ value, color, label }: { value: number; color: string; label: string }) {
  const pct = (value / 5) * 100;
  const r = 26;
  const c = 2 * Math.PI * r;
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative h-[64px] w-[64px]">
        <svg viewBox="0 0 64 64" className="h-full w-full -rotate-90">
          <circle cx="32" cy="32" r={r} fill="none" stroke="#E3D3BE" strokeWidth="7" />
          <circle
            cx="32"
            cy="32"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c - (c * pct) / 100}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-ink">
          {value.toFixed(1)}
        </span>
      </div>
      <span className="text-[11px] font-medium text-muted">{label}</span>
    </div>
  );
}

export function AppMock() {
  return (
    <div className="relative w-full max-w-md">
      {/* glow */}
      <div className="absolute -inset-6 -z-10 rounded-[32px] bg-accent/10 blur-2xl" aria-hidden />

      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-cardHover">
        {/* window chrome */}
        <div className="flex items-center gap-2 border-b border-border bg-surfaceHigh px-4 py-2.5">
          <span className="h-3 w-3 rounded-full bg-error/70" />
          <span className="h-3 w-3 rounded-full bg-warning/70" />
          <span className="h-3 w-3 rounded-full bg-success/70" />
          <span className="ml-2 text-xs font-medium text-muted">Moufida · Mon Tableau de bord</span>
        </div>

        <div className="space-y-4 p-5">
          {/* maturity */}
          <div className="flex items-center justify-between rounded-xl bg-bg/60 px-4 py-3">
            <div>
              <p className="text-[11px] uppercase tracking-wider text-muted">Maturity stage</p>
              <p className="font-heading text-lg font-bold text-ink">Market Validation</p>
            </div>
            <span className="rounded-full bg-info/10 px-3 py-1 text-xs font-semibold text-info">
              Stage 2 / 6
            </span>
          </div>

          {/* score gauges */}
          <div className="grid grid-cols-4 gap-2 rounded-xl bg-bg/60 px-3 py-4">
            {SCORES.map((s) => (
              <Gauge key={s.label} {...s} />
            ))}
          </div>

          {/* roadmap rows */}
          <div className="rounded-xl bg-bg/60 px-4 py-3">
            <p className="mb-2 text-[11px] uppercase tracking-wider text-muted">Next on your roadmap</p>
            <ul className="space-y-2 text-sm">
              {[
                { t: "Validate pricing with 5 design partners", done: true },
                { t: "Ship landing page + waitlist", done: true },
                { t: "Run competitor deep-search", done: false },
              ].map((row) => (
                <li key={row.t} className="flex items-center gap-2.5">
                  <span
                    className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-[5px] border ${
                      row.done ? "border-success bg-success text-bg" : "border-border"
                    }`}
                  >
                    {row.done && (
                      <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                        <path d="M2 6l3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </span>
                  <span className={row.done ? "text-muted line-through" : "text-ink"}>{row.t}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* alert */}
          <div className="flex items-start gap-2.5 rounded-xl border border-warning/30 bg-warning/10 px-4 py-3">
            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-warning" />
            <p className="text-xs leading-relaxed text-ink">
              <span className="font-semibold">Competitor signal:</span> AgriTechPlus just raised a seed
              round. Moufida updated your Market score and suggested 2 roadmap actions.
            </p>
          </div>
        </div>
      </div>

      {/* floating voice pill */}
      <div className="absolute -bottom-4 -left-4 flex items-center gap-2 rounded-full border border-border bg-bg px-4 py-2.5 shadow-card animate-float">
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-bg animate-pulse-ring">
          <Icon name="mic" className="h-3.5 w-3.5" strokeWidth={2} />
        </span>
        <span className="text-xs font-medium text-ink">&ldquo;Diagnose my startup&rdquo;</span>
      </div>
    </div>
  );
}
