const TOOLS = [
  "Slack", "Notion", "GitHub", "Stripe", "QuickBooks", "Google Calendar",
  "Trello", "HubSpot", "Mailchimp", "Figma", "Zoom", "Discord",
];

export function Integrations() {
  return (
    <section className="py-16">
      <div className="container-mf reveal text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-muted">
          Plugs into the tools you already use
        </p>
        <p className="mx-auto mt-3 max-w-2xl text-muted">
          Moufida reads from and writes back to your stack — daily briefings to Slack, roadmap tasks
          to Trello, profiles to Notion, burn rate from QuickBooks. You don&apos;t change your workflow.
        </p>
        <div className="mx-auto mt-7 flex max-w-3xl flex-wrap items-center justify-center gap-2.5">
          {TOOLS.map((t) => (
            <span
              key={t}
              className="rounded-full border border-border bg-surface px-4 py-2 text-sm font-medium text-ink"
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
