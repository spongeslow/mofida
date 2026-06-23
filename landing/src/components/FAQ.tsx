import { SectionHeading } from "./Section";

const FAQS = [
  {
    q: "What does “100% local” actually mean?",
    a: "Moufida runs on your own machine — your StartupProfile, scores and reports stay on your device. Nothing about your idea is uploaded unless you explicitly connect an integration (like a Slack webhook). Your strategy is yours.",
  },
  {
    q: "How is this different from ChatGPT?",
    a: "ChatGPT answers prompts. Moufida is a structured co-founder: she maintains a living model of your startup, scores it across 10 expert axes with explainable reasoning, monitors your market 24/7, and gives you a prioritised roadmap — not just text you have to interpret.",
  },
  {
    q: "What's in the due-diligence report?",
    a: "Diligence across five domains: product (BMC, personas, PRD, SWOT, PEST, UX, roadmap to MVP), market (TAM/SAM/SOM, trends, viability), competitive (positioning map, pricing & feature gaps, moat), financial (unit economics, burn & runway, 3-year model, funding needs) and legal (entity & IP, compliance, contracts, data-privacy) — plus go-to-market and funding (GTM, pitch deck, investor outreach). 25+ structured deliverables, all explained and kept up to date.",
  },
  {
    q: "How does the competitor & market analysis work?",
    a: "It's real deep-search across your whole market. Moufida auto-discovers your actual competitors, pulls sourced, cited signals — funding rounds, launches, pricing and hiring moves — and maps your positioning against the field so you can see exactly where you stand, your edge, your gaps and the open space to win. When something material changes, your scores and roadmap update automatically.",
  },
  {
    q: "When does it launch and what do I get for joining the waitlist?",
    a: "Launch is June 28, 2026. Waitlist members get early access on day one and founder pricing locked in for life.",
  },
  {
    q: "Which languages does it support?",
    a: "Voice and reports work in English, French and Arabic — built for founders across the MENA region and beyond.",
  },
];

export function FAQ() {
  return (
    <section id="faq" className="scroll-mt-20 py-24 sm:py-28">
      <div className="container-mf">
        <SectionHeading eyebrow="FAQ" title="Questions, answered" />

        <div className="mx-auto mt-12 max-w-3xl divide-y divide-border">
          {FAQS.map((f, i) => (
            <details
              key={f.q}
              className="reveal group py-5"
              style={{ transitionDelay: `${i * 50}ms` }}
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-heading text-lg font-semibold text-ink">
                {f.q}
                <span className="shrink-0 text-accent transition-transform duration-200 group-open:rotate-45">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <path d="M12 5v14M5 12h14" strokeLinecap="round" />
                  </svg>
                </span>
              </summary>
              <p className="mt-3 text-muted leading-relaxed">{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
