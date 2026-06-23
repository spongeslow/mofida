import { SectionHeading } from "./Section";
import { WaitlistForm } from "./WaitlistForm";
import { Icon } from "./Icon";

const TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    tagline: "See where you stand.",
    cta: "Start free",
    featured: false,
    features: [
      "Full startup diagnosis & maturity stage",
      "Scores across all 10 axes",
      "~20% of your due-diligence report",
      "Voice commands & dashboard",
      "100% local — your data stays put",
    ],
    note: "Some report sections stay locked until you upgrade.",
  },
  {
    name: "Founder",
    price: "Early-bird",
    period: "for waitlist members",
    tagline: "The whole co-founder, unlocked.",
    cta: "Get early access",
    featured: true,
    features: [
      "Everything in Free, fully unlocked",
      "Complete due-diligence report (all sections)",
      "Competitor deep-search & 24/7 monitoring",
      "Personalised roadmap + local resources",
      "All tool integrations (Slack, Notion, GitHub…)",
      "“Mon Parcours” history & investor exports",
    ],
    note: "Waitlist members get founder pricing locked in for life.",
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="scroll-mt-20 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="Pricing"
          title="Start free. Upgrade when it pays for itself."
          subtitle="Join the waitlist to lock in founder pricing before launch."
        />

        <div className="mx-auto mt-14 grid max-w-4xl gap-5 md:grid-cols-2">
          {TIERS.map((t, i) => (
            <div
              key={t.name}
              className={`reveal relative flex flex-col rounded-2xl border p-7 ${
                t.featured
                  ? "border-accent bg-surface shadow-cardHover"
                  : "border-border bg-surface/60"
              }`}
              style={{ transitionDelay: `${i * 90}ms` }}
            >
              {t.featured && (
                <span className="absolute -top-3 left-7 rounded-full bg-accent px-3 py-1 text-xs font-bold text-bg">
                  Most popular
                </span>
              )}
              <h3 className="font-heading text-xl font-bold text-ink">{t.name}</h3>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="font-heading text-3xl font-bold text-ink">{t.price}</span>
                <span className="text-sm text-muted">{t.period}</span>
              </div>
              <p className="mt-1 text-sm text-muted">{t.tagline}</p>

              <ul className="mt-6 flex-1 space-y-3">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-ink">
                    <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-success" strokeWidth={2.5} />
                    {f}
                  </li>
                ))}
              </ul>

              <p className="mt-5 text-xs italic text-muted">{t.note}</p>

              <a
                href="#waitlist-final"
                className={`mt-5 ${t.featured ? "btn-accent" : "btn-ghost"} w-full`}
              >
                {t.cta}
              </a>
            </div>
          ))}
        </div>

        <div className="reveal mx-auto mt-10 max-w-xl">
          <WaitlistForm source="pricing" />
        </div>
      </div>
    </section>
  );
}
