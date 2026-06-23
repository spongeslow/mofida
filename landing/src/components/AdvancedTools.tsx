import { SectionHeading } from "./Section";
import { Icon, type IconName } from "./Icon";

/** Deep, interactive coaching modules — grounded in your own diagnostic data. */
const TOOLS: { icon: IconName; title: string; color: string; desc: string; points: string[] }[] = [
  {
    icon: "presentation",
    title: "Investor Pitch Simulator",
    color: "#6D28D9",
    desc: "Rehearse your pitch against an AI investor persona — Seed VC, Angel — whose questions are grounded only in your real scores and blockers, so it probes your weakest story.",
    points: ["Choose your investor persona", "Questions drawn from your data", "Readiness report at the end"],
  },
  {
    icon: "shuffle",
    title: "Pivot Scenario Planner",
    color: "#1D4ED8",
    desc: "Model a strategic change — “what if we target a different segment?” — and watch Moufida project the impact across all your scores, with confidence levels and reasoning.",
    points: ["What-if on any axis", "Projected score impact", "De-risk before you commit"],
  },
  {
    icon: "users",
    title: "Customer Persona Simulator",
    color: "#C96A2D",
    desc: "Moufida generates distinct customer personas from your project, then lets you chat with each one to hear real objections, buying triggers and pain points.",
    points: ["Personas built from your data", "Chat to surface objections", "Sharpen your value prop"],
  },
];

export function AdvancedTools() {
  return (
    <section id="coaching" className="scroll-mt-20 bg-surface/40 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="Advanced coaching"
          title={
            <>
              Practice the hard parts.{" "}
              <span className="text-accent">Before they cost you.</span>
            </>
          }
          subtitle="Interactive simulators that go beyond reports — each one grounded in your actual diagnostic data, so the coaching is about your startup, not a generic template."
        />

        <div className="mt-14 grid gap-5 lg:grid-cols-3">
          {TOOLS.map((t, i) => (
            <div
              key={t.title}
              className="reveal card card-hover flex flex-col"
              style={{ transitionDelay: `${i * 90}ms` }}
            >
              <span
                className="flex h-11 w-11 items-center justify-center rounded-xl"
                style={{ background: `${t.color}14`, color: t.color }}
              >
                <Icon name={t.icon} className="h-5 w-5" />
              </span>
              <h3 className="mt-4 font-heading text-lg font-bold text-ink">{t.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{t.desc}</p>
              <ul className="mt-4 space-y-2">
                {t.points.map((p) => (
                  <li key={p} className="flex items-center gap-2 text-sm font-medium text-ink">
                    <Icon name="check" className="h-4 w-4 shrink-0 text-success" strokeWidth={2.5} /> {p}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
