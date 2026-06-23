/**
 * Market positioning quadrant — "where you stand".
 * x axis: price (affordable → premium) · y axis: capability (basic → advanced)
 */
const COMPETITORS = [
  { name: "AgriTechPlus", x: 74, y: 58 },
  { name: "FarmIQ", x: 38, y: 34 },
  { name: "GreenHarvest", x: 24, y: 56 },
  { name: "CropAI", x: 82, y: 40 },
];
const YOU = { x: 58, y: 82 };

export function PositioningMap() {
  return (
    <div className="rounded-xl border border-border bg-bg/70 p-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-[11px] uppercase tracking-wider text-muted">Your market positioning</p>
        <span className="rounded-full bg-accent/10 px-2.5 py-1 text-[11px] font-semibold text-accent">
          You lead on capability
        </span>
      </div>

      <div className="relative">
        {/* y-axis label */}
        <span className="absolute -left-1 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] font-medium uppercase tracking-wider text-muted">
          Capability
        </span>

        <div className="ml-5">
          {/* plot */}
          <div className="relative aspect-square w-full rounded-lg border border-border bg-surface/60">
            {/* quadrant grid lines */}
            <div className="absolute inset-x-0 top-1/2 border-t border-dashed border-border/70" />
            <div className="absolute inset-y-0 left-1/2 border-l border-dashed border-border/70" />

            {/* competitor dots */}
            {COMPETITORS.map((c) => (
              <div
                key={c.name}
                className="group absolute -translate-x-1/2 translate-y-1/2"
                style={{ left: `${c.x}%`, bottom: `${c.y}%` }}
              >
                <span className="block h-3 w-3 rounded-full border border-bg bg-muted/70" />
                <span className="pointer-events-none absolute left-1/2 top-4 -translate-x-1/2 whitespace-nowrap text-[10px] text-muted opacity-80">
                  {c.name}
                </span>
              </div>
            ))}

            {/* you */}
            <div
              className="absolute z-10 -translate-x-1/2 translate-y-1/2"
              style={{ left: `${YOU.x}%`, bottom: `${YOU.y}%` }}
            >
              <span className="block h-4 w-4 rounded-full border-2 border-bg bg-accent shadow-btnAccent animate-pulse-ring" />
              <span className="absolute left-1/2 top-5 -translate-x-1/2 whitespace-nowrap rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-bg">
                You
              </span>
            </div>
          </div>

          {/* x-axis labels */}
          <div className="mt-2 flex justify-between text-[10px] font-medium uppercase tracking-wider text-muted">
            <span>Affordable</span>
            <span>Price</span>
            <span>Premium</span>
          </div>
        </div>
      </div>
    </div>
  );
}
