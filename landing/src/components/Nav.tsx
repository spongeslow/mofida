"use client";

import { useEffect, useState } from "react";
import { Logo } from "./Logo";

const LINKS = [
  { href: "#how", label: "How it works" },
  { href: "#due-diligence", label: "Due diligence" },
  { href: "#features", label: "Features" },
  { href: "#coaching", label: "Coaching" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? "border-b border-border/70 bg-bg/85 backdrop-blur-md" : "border-b border-transparent"
      }`}
    >
      <nav className="container-mf flex h-16 items-center justify-between">
        <a href="#top" className="flex items-center gap-2.5" aria-label="Moufida home">
          <Logo className="h-8 w-8" />
          <span className="font-heading text-xl font-bold text-ink">Moufida</span>
        </a>

        <div className="hidden items-center gap-7 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-muted transition-colors hover:text-primary"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <a href="#waitlist" className="hidden btn-accent !px-5 !py-2.5 sm:inline-flex">
            Get early access
          </a>
          <button
            className="rounded-lg border border-border p-2 md:hidden"
            aria-label="Toggle menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {open ? <path d="M18 6 6 18M6 6l12 12" /> : <path d="M3 12h18M3 6h18M3 18h18" />}
            </svg>
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-border/70 bg-bg/95 backdrop-blur-md md:hidden">
          <div className="container-mf flex flex-col gap-1 py-3">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-2 py-2.5 text-sm font-medium text-muted hover:bg-primary/5 hover:text-primary"
              >
                {l.label}
              </a>
            ))}
            <a href="#waitlist" onClick={() => setOpen(false)} className="btn-accent mt-2">
              Get early access
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
