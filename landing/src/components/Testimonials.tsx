import { SectionHeading } from "./Section";
import { Icon } from "./Icon";

const QUOTES = [
  {
    quote:
      "It caught a competitor's pricing change before I did — and rewrote my GTM plan the same morning. Felt like having a co-founder who never logs off.",
    name: "Yassine B.",
    role: "Solo founder, AgriTech",
  },
  {
    quote:
      "The due-diligence report saved me from a meeting with a consultant who'd have charged thousands. I walked into my accelerator interview ready.",
    name: "Salma K.",
    role: "Pre-seed, HealthTech",
  },
  {
    quote:
      "The explainable scores are the killer feature. I finally understood *why* my finances were the weak axis — and exactly what to fix.",
    name: "Omar T.",
    role: "Bootstrapped SaaS",
  },
];

export function Testimonials() {
  return (
    <section className="bg-surface/40 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="Loved by early builders"
          title="Founders are already shipping faster"
          subtitle="From our private beta during the AINS Hackathon."
        />

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {QUOTES.map((q, i) => (
            <figure
              key={q.name}
              className="reveal card card-hover flex flex-col"
              style={{ transitionDelay: `${i * 90}ms` }}
            >
              <div className="flex gap-0.5 text-accent" aria-hidden>
                {Array.from({ length: 5 }).map((_, s) => (
                  <Icon key={s} name="star" className="h-4 w-4" strokeWidth={0} />
                ))}
              </div>
              <blockquote className="mt-3 flex-1 text-sm leading-relaxed text-ink">
                “{q.quote}”
              </blockquote>
              <figcaption className="mt-5 border-t border-border pt-4">
                <p className="font-semibold text-ink">{q.name}</p>
                <p className="text-xs text-muted">{q.role}</p>
              </figcaption>
            </figure>
          ))}
        </div>

        <p className="reveal mt-6 text-center text-xs text-muted">
          Beta quotes from hackathon participants. Names abbreviated for privacy.
        </p>
      </div>
    </section>
  );
}
