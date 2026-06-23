"use client";

import { useEffect, useState } from "react";

const LAUNCH = process.env.NEXT_PUBLIC_LAUNCH_DATE || "2026-06-28T09:00:00Z";

function diff(target: number) {
  const ms = Math.max(0, target - Date.now());
  const days = Math.floor(ms / 86_400_000);
  const hours = Math.floor((ms % 86_400_000) / 3_600_000);
  const minutes = Math.floor((ms % 3_600_000) / 60_000);
  const seconds = Math.floor((ms % 60_000) / 1000);
  return { days, hours, minutes, seconds, done: ms === 0 };
}

export function Countdown({ compact = false, onDark = false }: { compact?: boolean; onDark?: boolean }) {
  const target = new Date(LAUNCH).getTime();
  const [t, setT] = useState(() => diff(target));
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setT(diff(target));
    const id = setInterval(() => setT(diff(target)), 1000);
    return () => clearInterval(id);
  }, [target]);

  // Avoid hydration mismatch: render static zeros until mounted.
  const cells = [
    { v: mounted ? t.days : 0, l: "days" },
    { v: mounted ? t.hours : 0, l: "hrs" },
    { v: mounted ? t.minutes : 0, l: "min" },
    { v: mounted ? t.seconds : 0, l: "sec" },
  ];

  if (t.done && mounted) {
    return (
      <span className="font-pixel text-xs text-accent">WE&apos;RE LIVE — go grab it</span>
    );
  }

  const numColor = onDark ? "text-bg" : "text-primary";
  const labelColor = onDark ? "text-bg/70" : "text-muted";
  const sepColor = onDark ? "text-bg/40" : "text-border";

  return (
    <div className={`flex items-center ${compact ? "gap-2" : "gap-3"}`} aria-label="Countdown to launch">
      {cells.map((c, i) => (
        <div key={c.l} className="flex items-center gap-3">
          <div className="flex flex-col items-center">
            <span
              className={`tabular-nums font-heading font-bold ${numColor} ${
                compact ? "text-2xl" : "text-3xl sm:text-4xl"
              }`}
            >
              {String(c.v).padStart(2, "0")}
            </span>
            <span className={`text-[10px] font-semibold uppercase tracking-widest ${labelColor}`}>
              {c.l}
            </span>
          </div>
          {i < cells.length - 1 && <span className={`pb-4 text-2xl ${sepColor}`}>:</span>}
        </div>
      ))}
    </div>
  );
}
