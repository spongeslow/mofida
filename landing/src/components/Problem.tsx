import { SectionHeading } from "./Section";
import { Icon, type IconName } from "./Icon";

const PAINS: { icon: IconName; title: string; text: string }[] = [
  {
    icon: "eyeOff",
    title: "Flying blind",
    text: "You're making six-figure decisions on gut feeling — no clear read on where your startup actually stands.",
  },
  {
    icon: "clock",
    title: "8+ hours/week lost",
    text: "Manually tracking competitors, market shifts and metrics across a dozen tabs. Time you should spend building.",
  },
  {
    icon: "banknote",
    title: "Consultants cost $10k+",
    text: "A real due-diligence report from an advisor is slow, expensive, and out of date the week you get it.",
  },
  {
    icon: "unlock",
    title: "Your idea, uploaded",
    text: "Most AI tools ship your most sensitive strategy to someone else's cloud.",
  },
];

export function Problem() {
  return (
    <section className="py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="The problem"
          title="Building a startup alone is brutal"
          subtitle="Most founders don't fail from lack of effort — they fail from blind spots no one flagged in time."
        />

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {PAINS.map((p, i) => (
            <div
              key={p.title}
              className="reveal card card-hover"
              style={{ transitionDelay: `${i * 80}ms` }}
            >
              <Icon name={p.icon} className="h-6 w-6 text-accent" />
              <h3 className="mt-4 font-heading text-lg font-bold text-ink">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{p.text}</p>
            </div>
          ))}
        </div>

        <div className="reveal mx-auto mt-14 max-w-3xl rounded-2xl border border-accent/25 bg-accent/5 p-8 text-center">
          <p className="font-heading text-xl font-semibold leading-snug text-ink sm:text-2xl">
            Moufida is the co-founder who reads everything, forgets nothing, and tells you the truth —{" "}
            <span className="text-accent">24/7, on your machine.</span>
          </p>
        </div>
      </div>
    </section>
  );
}
