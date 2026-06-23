import { Logo } from "./Logo";

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface/40">
      <div className="container-mf py-12">
        <div className="flex flex-col items-start justify-between gap-8 md:flex-row">
          <div className="max-w-sm">
            <div className="flex items-center gap-2.5">
              <Logo className="h-8 w-8" />
              <span className="font-heading text-xl font-bold text-ink">Moufida</span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              Your 24/7 AI co-founder. Diagnose, score and roadmap your startup — 100% local.
            </p>
            <p className="mt-4 text-xs text-muted">
              Built by Team Makrouna Kadheba · AINS Hackathon 2026
            </p>
          </div>

          <div className="grid grid-cols-2 gap-10 sm:grid-cols-3">
            <FooterCol
              title="Product"
              links={[
                { label: "How it works", href: "#how" },
                { label: "Due diligence", href: "#due-diligence" },
                { label: "Features", href: "#features" },
                { label: "Pricing", href: "#pricing" },
              ]}
            />
            <FooterCol
              title="Resources"
              links={[
                { label: "FAQ", href: "#faq" },
                { label: "GitHub", href: "https://github.com" },
                { label: "Documentation", href: "https://github.com" },
                { label: "Demo video", href: "#top" },
              ]}
            />
            <FooterCol
              title="Get started"
              links={[
                { label: "Join the waitlist", href: "#waitlist-final" },
                { label: "Early access", href: "#waitlist" },
              ]}
            />
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 text-xs text-muted sm:flex-row">
          <p>© 2026 Moufida. Open source.</p>
          <p>Built for founders.</p>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({
  title,
  links,
}: {
  title: string;
  links: { label: string; href: string }[];
}) {
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wider text-ink">{title}</h4>
      <ul className="mt-3 space-y-2.5">
        {links.map((l) => (
          <li key={l.label}>
            <a href={l.href} className="text-sm text-muted transition-colors hover:text-primary">
              {l.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
