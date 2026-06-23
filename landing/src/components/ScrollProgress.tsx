"use client";

import { useEffect, useState } from "react";

/** Thin accent bar at the very top that fills as you scroll the page. */
export function ScrollProgress() {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    let raf = 0;
    const update = () => {
      raf = 0;
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      setPct(max > 0 ? Math.min(1, h.scrollTop / max) : 0);
    };
    const onScroll = () => {
      if (raf === 0) raf = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="fixed inset-x-0 top-0 z-[55] h-0.5 bg-transparent" aria-hidden>
      <div
        className="h-full bg-gradient-to-r from-accent to-accentHover transition-[width] duration-150 ease-out"
        style={{ width: `${pct * 100}%` }}
      />
    </div>
  );
}
