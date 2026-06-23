"use client";

import { useEffect, useState } from "react";

/** Small social-proof line. Shows a baseline so it never reads "0 founders". */
const BASELINE = 280;

export function WaitlistCount() {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/waitlist")
      .then((r) => r.json())
      .then((d) => setCount((d?.count ?? 0) + BASELINE))
      .catch(() => setCount(BASELINE));
  }, []);

  return (
    <div className="flex items-center gap-2.5">
      <div className="flex -space-x-2">
        {["#C96A2D", "#6F4E37", "#2E7D32", "#1565C0"].map((c, i) => (
          <span
            key={i}
            className="h-7 w-7 rounded-full border-2 border-bg"
            style={{ background: c }}
            aria-hidden
          />
        ))}
      </div>
      <p className="text-sm text-muted">
        Join{" "}
        <span className="font-semibold text-ink">
          {count === null ? "300+" : `${count.toLocaleString()}`}
        </span>{" "}
        founders already on the list
      </p>
    </div>
  );
}
