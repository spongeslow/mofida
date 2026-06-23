import { SectionHeading } from "./Section";
import { Icon, type IconName } from "./Icon";

const STEPS: { n: string; title: string; text: string; icon: IconName }[] = [
  {
    n: "01",
    title: "Describe your startup",
    text: "Talk to Moufida or type it in. She builds a living profile from your idea, traction and goals — in English, French or Arabic.",
    icon: "message",
  },
  {
    n: "02",
    title: "Get diagnosed & scored",
    text: "Moufida scores you across 10 expert axes with explainable reasoning, then runs full due diligence — product, market, legal, financial and competitive.",
    icon: "chart",
  },
  {
    n: "03",
    title: "Follow your roadmap",
    text: "Receive a personalised, prioritised roadmap. Moufida keeps monitoring 24/7, flags competitor moves, and updates your scores as you ship.",
    icon: "compass",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-20 bg-surface/40 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="How it works"
          title="From idea to investor-ready in three steps"
          subtitle="No dashboards to configure. No data to upload. Just answers."
        />

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <div key={s.n} className="reveal relative" style={{ transitionDelay: `${i * 100}ms` }}>
              <div className="card card-hover h-full">
                <div className="flex items-center justify-between">
                  <span className="font-pixel text-xs text-accent">{s.n}</span>
                  <Icon name={s.icon} className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mt-6 font-heading text-xl font-bold text-ink">{s.title}</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-muted">{s.text}</p>
              </div>
              {i < STEPS.length - 1 && (
                <div className="absolute -right-3 top-1/2 hidden -translate-y-1/2 text-2xl text-border md:block">
                  →
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
