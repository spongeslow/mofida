"use client";

import { useState } from "react";
import { getAttribution } from "@/lib/client-analytics";

type Props = {
  /** Where this form lives, for our own funnel notes. Not sent to server beyond path. */
  source?: string;
  size?: "default" | "large";
  className?: string;
};

type Status = "idle" | "loading" | "success" | "already" | "error";

export function WaitlistForm({ source = "inline", size = "default", className = "" }: Props) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (status === "loading") return;
    setStatus("loading");
    setMessage("");

    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, ...getAttribution() }),
      });
      const data = await res.json();

      if (!res.ok || !data.ok) {
        setStatus("error");
        setMessage(data.error || "Something went wrong. Please try again.");
        return;
      }
      if (data.alreadyJoined) {
        setStatus("already");
        setMessage("You're already on the list — see you on launch day.");
        return;
      }
      setStatus("success");
      setMessage("You're in. Check your inbox on June 28 for early access.");
      setEmail("");
    } catch {
      setStatus("error");
      setMessage("Network error. Please try again.");
    }
  }

  const done = status === "success" || status === "already";

  if (done) {
    return (
      <div
        className={`rounded-2xl border border-success/30 bg-success/10 px-5 py-4 text-center ${className}`}
        role="status"
      >
        <p className="font-semibold text-success">{message}</p>
      </div>
    );
  }

  const big = size === "large";

  return (
    <form
      onSubmit={onSubmit}
      data-source={source}
      className={`flex w-full flex-col gap-2.5 sm:flex-row ${className}`}
      noValidate
    >
      <div className="flex-1">
        <label htmlFor={`email-${source}`} className="sr-only">
          Email address
        </label>
        <input
          id={`email-${source}`}
          type="email"
          inputMode="email"
          autoComplete="email"
          required
          placeholder="you@startup.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={`input-mf ${big ? "sm:py-4 sm:text-lg" : ""}`}
          aria-invalid={status === "error"}
        />
      </div>
      <button
        type="submit"
        disabled={status === "loading"}
        className={`btn-accent shrink-0 ${big ? "sm:px-9 sm:text-lg" : ""} disabled:opacity-70`}
      >
        {status === "loading" ? "Joining…" : "Join the waitlist"}
      </button>
      {status === "error" && (
        <p className="w-full text-sm text-error sm:order-last sm:basis-full" role="alert">
          {message}
        </p>
      )}
    </form>
  );
}
