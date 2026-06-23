import { SectionHeading } from "./Section";
import { Icon, type IconName } from "./Icon";

const FEATURES: { icon: IconName; title: string; text: string; span?: string }[] = [
  {
    icon: "mic",
    title: "Voice-first by design",
    text: "Just talk. “Diagnose my project”, “send my weekly report to Slack”, “what's my biggest blocker?” Moufida answers — hands-free, in EN/FR/AR.",
    span: "lg:col-span-2",
  },
  {
    icon: "shield",
    title: "100% local",
    text: "Runs entirely on your machine. Your strategy never touches someone else's cloud.",
  },
  {
    icon: "branch",
    title: "Explainable scoring",
    text: "Every score is backed by a transparent decision tree — see exactly why Moufida rated you, with the evidence behind it.",
  },
  {
    icon: "radar",
    title: "24/7 background monitoring",
    text: "A lightweight daemon runs five watchers around the clock — budget, competitors, a legal radar, milestones and market trends — so you wake up to insight, not surprises.",
    span: "lg:col-span-2",
  },
  {
    icon: "sparkles",
    title: "Start from a spark",
    text: "No project yet? Creation Mode turns a raw idea into a complete, grounded plan — guided axis by axis, with Approve, Edit or Retry on every section.",
  },
  {
    icon: "route",
    title: "Personalised roadmap",
    text: "Prioritised next actions tailored to your stage — with curated local resources, grants and accelerator leads.",
    span: "lg:col-span-2",
  },
  {
    icon: "history",
    title: "“Mon Parcours” tracking",
    text: "A timeline of every score, decision and milestone — and compare any two diagnoses to see exactly what moved, week over week.",
  },
  {
    icon: "upload",
    title: "Upload your deck",
    text: "Drop in your business plan or pitch deck — Moufida extracts it and folds the evidence straight into your diagnosis.",
  },
  {
    icon: "message",
    title: "Debate any score",
    text: "Disagree with a rating? Argue it in chat. Make a convincing case and Moufida recomputes the score — and logs why.",
  },
  {
    icon: "gamepad",
    title: "A companion, not a tab",
    text: "An expressive pixel-art Moufida lives on your desktop — celebrating milestones, flagging alerts, present even when the window is closed.",
    span: "lg:col-span-2",
  },
];

export function Features() {
  return (
    <section id="features" className="scroll-mt-20 bg-surface/40 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading
          eyebrow="Why Moufida"
          title="Not a chatbot. A co-founder."
          subtitle="Purpose-built for founders who want clarity, not another dashboard to babysit."
        />

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className={`reveal card card-hover ${f.span ?? ""}`}
              style={{ transitionDelay: `${(i % 3) * 80}ms` }}
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Icon name={f.icon} className="h-5 w-5" />
              </span>
              <h3 className="mt-4 font-heading text-lg font-bold text-ink">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{f.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
