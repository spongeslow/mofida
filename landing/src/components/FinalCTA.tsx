import { WaitlistForm } from "./WaitlistForm";
import { Countdown } from "./Countdown";
import { WaitlistCount } from "./WaitlistCount";

export function FinalCTA() {
  return (
    <section className="py-20 sm:py-28">
      <div className="container-mf">
        <div className="reveal relative overflow-hidden rounded-[28px] border border-border bg-gradient-to-br from-primary to-primaryDark px-6 py-14 text-center text-bg sm:px-12 sm:py-20">
          <div
            className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-accent/30 blur-3xl"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute -bottom-20 -left-10 h-64 w-64 rounded-full bg-accentHover/20 blur-3xl"
            aria-hidden
          />

          <span className="font-pixel text-[10px] uppercase tracking-widest text-bg/70">
            Launching June 28, 2026
          </span>
          <h2 className="mx-auto mt-5 max-w-2xl font-heading text-3xl font-bold leading-tight sm:text-5xl">
            Meet the co-founder who never sleeps.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-bg/85">
            Join the waitlist for day-one early access and founder pricing locked in for life.
          </p>

          <div id="waitlist-final" className="mx-auto mt-8 max-w-xl scroll-mt-24">
            <WaitlistForm source="final" size="large" />
          </div>

          <div className="mt-10 flex flex-col items-center gap-6">
            <div className="rounded-2xl bg-bg/10 px-6 py-4 backdrop-blur-sm">
              <Countdown onDark />
            </div>
            <div className="text-bg [&_*]:!text-bg/90">
              <WaitlistCount />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
