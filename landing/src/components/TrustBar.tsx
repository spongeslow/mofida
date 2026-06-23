import { Icon, type IconName } from "./Icon";

const POINTS: { icon: IconName; text: string }[] = [
  { icon: "clipboard", text: "Product · Market · Legal · Financial diligence" },
  { icon: "search", text: "Whole-market competitor analysis" },
  { icon: "branch", text: "Explainable AI scoring" },
  { icon: "radar", text: "24/7 monitoring" },
  { icon: "shield", text: "100% local-first" },
];

export function TrustBar() {
  return (
    <section className="border-y border-border/60 bg-surface/40 py-5">
      <div className="container-mf reveal flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm font-medium text-muted">
        {POINTS.map((p) => (
          <span key={p.text} className="inline-flex items-center gap-2">
            <Icon name={p.icon} className="h-4 w-4 text-accent" />
            {p.text}
          </span>
        ))}
      </div>
    </section>
  );
}
