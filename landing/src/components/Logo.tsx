/** Moufida mark — a coffee-bean "M" in the warm brand gradient. */
export function Logo({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" aria-hidden role="img">
      <defs>
        <linearGradient id="mf-logo" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#C96A2D" />
          <stop offset="1" stopColor="#6F4E37" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill="url(#mf-logo)" />
      <path
        d="M10 28V13.5c0-.6.73-.9 1.15-.46L20 22l8.85-8.96c.42-.43 1.15-.13 1.15.47V28"
        stroke="#F5EBDD"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="20" cy="29" r="1.9" fill="#F5EBDD" />
    </svg>
  );
}
