import { SectionHeading } from "./Section";
import { PositioningMap } from "./PositioningMap";
import { Icon, type IconName } from "./Icon";

/** The domains of diligence Moufida runs — each as deep as a top advisor's. */
const DOMAINS: { icon: IconName; title: string; color: string; desc: string }[] = [
  {
    icon: "lightbulb",
    title: "Product diligence",
    color: "#6D28D9",
    desc: "Is it worth building? Business Model Canvas, user personas, PRD, SWOT, PEST, UX advice and a roadmap to MVP.",
  },
  {
    icon: "trending",
    title: "Market diligence",
    color: "#1D4ED8",
    desc: "How big is the prize? TAM / SAM / SOM sizing, growth rates, market trends, business viability and segmentation.",
  },
  {
    icon: "target",
    title: "Competitive diligence",
    color: "#C96A2D",
    desc: "Where do you stand? A whole-market scan with positioning maps, pricing & feature gaps, traction and moat analysis.",
  },
  {
    icon: "dollar",
    title: "Financial diligence",
    color: "#B45309",
    desc: "Do the numbers work? Unit economics (CAC, LTV, payback), burn rate & runway, a 3-year model and funding needs.",
  },
  {
    icon: "scale",
    title: "Legal diligence",
    color: "#0F766E",
    desc: "What could bite you? Entity & IP structure, regulatory / compliance checks, contracts and data-privacy posture.",
  },
  {
    icon: "rocket",
    title: "Go-to-market & funding",
    color: "#059669",
    desc: "How do you win? Marketing & GTM strategy, monetization, a YC-style pitch deck and an investor outreach plan.",
  },
];

/** A curated sample of deliverables that prove the depth of every report. */
const DELIVERABLES = [
  "Business Model Canvas", "User Personas", "SWOT & PEST", "TAM / SAM / SOM",
  "Competitor matrix", "Positioning map", "Unit economics", "3-year financial model",
  "IP & trademark check", "Compliance review", "GTM strategy", "YC-style pitch deck",
  "Investor outreach plan",
];

export function DueDiligence() {
  return (
    <section id="due-diligence" className="scroll-mt-20 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="AI due diligence"
          title={
            <>
              Five kinds of due diligence.{" "}
              <span className="text-accent">One co-founder.</span>
            </>
          }
          subtitle="Moufida runs the same diligence a top-tier advisor would — across every dimension of your startup, not just the product — and keeps it live as you build. A $10k report, generated in minutes."
        />

        {/* Domains */}
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {DOMAINS.map((d, i) => (
            <div
              key={d.title}
              className="reveal card card-hover"
              style={{ transitionDelay: `${(i % 3) * 80}ms` }}
            >
              <div className="flex items-center gap-3">
                <span
                  className="flex h-11 w-11 items-center justify-center rounded-xl"
                  style={{ background: `${d.color}14`, color: d.color }}
                >
                  <Icon name={d.icon} className="h-5 w-5" />
                </span>
                <h3 className="font-heading text-lg font-bold text-ink">{d.title}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted">{d.desc}</p>
            </div>
          ))}
        </div>

        {/* Depth proof — deliverables */}
        <div className="reveal mt-10 rounded-2xl border border-border bg-surface/50 p-7 sm:p-8">
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-muted">
            Every report goes deep — 25+ structured deliverables, fully explained
          </p>
          <p className="sr-only">A sample of what each report includes:</p>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            {DELIVERABLES.map((d) => (
              <span
                key={d}
                className="rounded-full border border-border bg-bg/70 px-3 py-1.5 text-xs font-medium text-ink"
              >
                {d}
              </span>
            ))}
          </div>
        </div>

        {/* Competitive intelligence + positioning */}
        <div className="reveal mt-8 overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-surface to-surfaceHigh">
          <div className="grid items-center gap-8 p-7 sm:p-9 lg:grid-cols-[1fr_1fr]">
            <div>
              <span className="eyebrow">
                <Icon name="search" className="h-3.5 w-3.5" /> Competitive intelligence
              </span>
              <h3 className="mt-4 font-heading text-2xl font-bold text-ink sm:text-3xl">
                Know exactly where you stand in your market
              </h3>
              <p className="mt-3 text-muted">
                Moufida deep-searches your{" "}
                <span className="font-semibold text-ink">entire market</span> — auto-discovering
                competitors and tracking funding, launches, pricing and hiring signals. It maps your{" "}
                <span className="font-semibold text-ink">positioning</span> against every player, so
                you see your edge, your gaps, and the open space to win — all sourced and cited.
              </p>
              <ul className="mt-5 grid gap-2.5 sm:grid-cols-2">
                {[
                  "Auto-discovers competitors",
                  "Positioning map vs. the field",
                  "Pricing & feature gap analysis",
                  "Funding & launch alerts",
                  "Sourced, cited findings",
                  "Updates your scores live",
                ].map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm font-medium text-ink">
                    <Icon name="check" className="h-4 w-4 shrink-0 text-success" strokeWidth={2.5} /> {f}
                  </li>
                ))}
              </ul>
            </div>

            <PositioningMap />
          </div>

          {/* Live competitor feed strip */}
          <div className="border-t border-border bg-bg/40 px-7 py-5 sm:px-9">
            <p className="mb-3 text-[11px] uppercase tracking-wider text-muted">
              Live competitor feed
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { c: "AgriTechPlus", t: "Raised $2.1M seed · 3h ago", color: "#C86A00" },
                { c: "FarmIQ", t: "Launched mobile app · 1d ago", color: "#1565C0" },
                { c: "GreenHarvest", t: "Cut pricing 20% · 2d ago", color: "#B71C1C" },
              ].map((row) => (
                <div
                  key={row.c}
                  className="flex items-start gap-2.5 rounded-lg border border-border bg-surface/70 px-3 py-2.5"
                >
                  <span
                    className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                    style={{ background: row.color }}
                  />
                  <div>
                    <p className="text-sm font-semibold text-ink">{row.c}</p>
                    <p className="text-xs text-muted">{row.t}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
