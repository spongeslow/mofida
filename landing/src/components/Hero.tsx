import { WaitlistForm } from "./WaitlistForm";
import { WaitlistCount } from "./WaitlistCount";
import { Countdown } from "./Countdown";
import { AppMock } from "./AppMock";

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden pt-28 pb-16 sm:pt-32">
      <div className="container-mf grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
        {/* Copy */}
        <div className="reveal">
          <span className="eyebrow">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse-ring" />
            Launching June 28, 2026
          </span>

          <h1 className="mt-5 font-heading text-4xl font-bold leading-[1.08] text-ink sm:text-5xl lg:text-6xl">
            Your 24/7 AI{" "}
            <span className="relative whitespace-nowrap text-accent">
              co-founder
              <svg
                className="absolute -bottom-1 left-0 w-full"
                viewBox="0 0 200 12"
                fill="none"
                preserveAspectRatio="none"
                aria-hidden
              >
                <path d="M2 9C50 3 150 3 198 9" stroke="#C96A2D" strokeWidth="3" strokeLinecap="round" opacity="0.5" />
              </svg>
            </span>{" "}
            that never sleeps
          </h1>

          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">
            Moufida runs <span className="font-semibold text-ink">complete due diligence</span> on your
            startup — <span className="font-semibold text-ink">product, market, legal &amp; financial</span> —
            then deep-searches your entire market to show{" "}
            <span className="font-semibold text-ink">exactly where you&apos;re positioned</span> against
            every competitor. Scored, explained, and kept live 24/7.{" "}
            <span className="font-semibold text-primary">100% local — your data never leaves your machine.</span>
          </p>

          <div id="waitlist" className="mt-8 max-w-xl scroll-mt-24">
            <WaitlistForm source="hero" size="large" />
            <p className="mt-2.5 text-xs text-muted">
              Early access on launch day · No spam · Unsubscribe anytime
            </p>
          </div>

          <div className="mt-7 flex flex-col gap-5 sm:flex-row sm:items-center sm:gap-8">
            <WaitlistCount />
            <div className="hidden h-8 w-px bg-border sm:block" />
            <Countdown compact />
          </div>
        </div>

        {/* Product mock */}
        <div className="reveal lg:justify-self-end" style={{ transitionDelay: "120ms" }}>
          <AppMock />
        </div>
      </div>
    </section>
  );
}
