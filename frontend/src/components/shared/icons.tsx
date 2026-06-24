/**
 * Shared monochrome line-icon set — replaces emoji across screens so the UI
 * reads as a single crafted system. All icons inherit `currentColor` and a
 * default 16px box; pass `size` to override.
 */
type P = { size?: number };
const base = (size: number) => ({
  width: size, height: size, viewBox: "0 0 18 18", fill: "none",
  stroke: "currentColor", strokeWidth: 1.7,
  strokeLinecap: "round" as const, strokeLinejoin: "round" as const,
});

export function IconUser({ size = 16 }: P) {
  return (<svg {...base(size)}><circle cx="9" cy="6" r="3" /><path d="M3.5 15.5c0-3 2.5-4.8 5.5-4.8s5.5 1.8 5.5 4.8" /></svg>);
}
export function IconChat({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M2.5 3.5h13a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H8l-3.5 2.6V12.5H2.5a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Z" /></svg>);
}
export function IconLock({ size = 16 }: P) {
  return (<svg {...base(size)}><rect x="3.5" y="8" width="11" height="7.5" rx="1.8" /><path d="M5.8 8V5.8a3.2 3.2 0 0 1 6.4 0V8" /></svg>);
}
export function IconLink({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M7.5 10.5a3 3 0 0 0 4.3.2l2-2a3 3 0 0 0-4.2-4.2l-1 1" /><path d="M10.5 7.5a3 3 0 0 0-4.3-.2l-2 2a3 3 0 0 0 4.2 4.2l1-1" /></svg>);
}
export function IconDoc({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M5 1.5h5l4 4v11a0 0 0 0 1 0 0H5a1 1 0 0 1-1-1v-13a1 1 0 0 1 1-1Z" /><path d="M10 1.5v4h4" /></svg>);
}
export function IconFiles({ size = 16 }: P) {
  return (<svg {...base(size)}><rect x="2.5" y="5.5" width="10" height="10" rx="1.5" /><path d="M5.5 5.5v-2a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1h-2" /></svg>);
}
export function IconBook({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M3 3.5h5a2 2 0 0 1 2 2V15a1.6 1.6 0 0 0-1.6-1.5H3Z" /><path d="M15 3.5h-5a2 2 0 0 0-2 2V15a1.6 1.6 0 0 1 1.6-1.5H15Z" /></svg>);
}
export function IconChart({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M2.5 15.5h13" /><path d="M5 15.5V9M9 15.5V4.5M13 15.5v-4" /></svg>);
}
export function IconChevron({ size = 16, open = false }: P & { open?: boolean }) {
  return (<svg {...base(size)} style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 0.22s var(--mf-ease)" }}><path d="M4.5 6.5L9 11l4.5-4.5" /></svg>);
}
export function IconTrophy({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M5 2.5h8v3a4 4 0 0 1-8 0v-3Z" /><path d="M5 3.5H2.8v1A2.2 2.2 0 0 0 5 6.7M13 3.5h2.2v1A2.2 2.2 0 0 1 13 6.7M9 9.5v2.5M6.5 15.5h5M7 13h4l.5 2.5h-5Z" /></svg>);
}
export function IconEye({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M1.5 9S4.5 3.5 9 3.5 16.5 9 16.5 9 13.5 14.5 9 14.5 1.5 9 1.5 9Z" /><circle cx="9" cy="9" r="2.3" /></svg>);
}
export function IconMic({ size = 16 }: P) {
  return (<svg {...base(size)}><rect x="6.5" y="1.5" width="5" height="9" rx="2.5" /><path d="M3.8 8.2a5.2 5.2 0 0 0 10.4 0M9 13.5V16M6.5 16h5" /></svg>);
}
export function IconGear({ size = 16 }: P) {
  return (<svg {...base(size)}><circle cx="9" cy="9" r="2.6" /><path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.7 3.7l1.4 1.4M12.9 12.9l1.4 1.4M3.7 14.3l1.4-1.4M12.9 5.1l1.4-1.4" /></svg>);
}
export function IconPlug({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M6 2v4M12 2v4M4.5 6h9v2a4.5 4.5 0 0 1-9 0V6ZM9 12.5V16" /></svg>);
}
export function IconTrend({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M2.5 12.5l4-4 3 3 6-6" /><path d="M11.5 5.5h4v4" /></svg>);
}

export function IconHandshake({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M1.5 6.5L4 5l3 2 1.5-1 1.5 1 3-2 2.5 1.5" /><path d="M7 7l-2.5 2.5a1.3 1.3 0 0 0 1.8 1.8L7 10.5l1.5 1.4a1.3 1.3 0 0 0 1.8 0 1.3 1.3 0 0 0 0-1.8 1.3 1.3 0 0 0 1.8 0L11 8.5" /></svg>);
}
export function IconBolt({ size = 16 }: P) {
  return (<svg {...base(size)} fill="currentColor" stroke="none"><path d="M10 1L3 10h4l-1 7 7-9H9l1-7z" /></svg>);
}
export function IconTarget({ size = 16 }: P) {
  return (<svg {...base(size)}><circle cx="9" cy="9" r="6.5" /><circle cx="9" cy="9" r="3.5" /><circle cx="9" cy="9" r="0.6" fill="currentColor" /></svg>);
}
export function IconStar({ size = 16 }: P) {
  return (<svg {...base(size)} fill="currentColor" stroke="none"><path d="M9 1.5l2 4.4 4.8.5-3.6 3.2 1.1 4.7L9 11.9 4.7 14.3l1.1-4.7L2.2 6.4 7 5.9z" /></svg>);
}
export function IconShield({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M9 1.5l5.5 2v4.2c0 3.6-2.3 6.4-5.5 7.8C5.8 14.1 3.5 11.3 3.5 7.7V3.5z" /><path d="M6.5 8.8L8.2 10.5 11.8 7" /></svg>);
}
export function IconRocket({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M9 1.5c2.6 1.4 4 4 4 7l-1.8 1.8H6.8L5 8.5c0-3 1.4-5.6 4-7Z" /><circle cx="9" cy="6.5" r="1.3" /><path d="M6.8 10.3l-2 2M5 12.5l-1.8 2.3 2.3-1.8M11.2 10.3l2 2" /></svg>);
}
export function IconMap({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M6.5 2.5L2 4.5v11l4.5-2 5 2 4.5-2v-11l-4.5 2z" /><path d="M6.5 2.5v11M11.5 4.5v11" /></svg>);
}
export function IconConfetti({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M2.5 15.5l4-10 5.5 5.5z" /><path d="M11 2.5l.5 1.5M14.5 4l-1 1M15.5 8h-1.5M12.5 6.5l3-3" /></svg>);
}
export function IconTrendDown({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M2.5 5.5l4 4 3-3 6 6" /><path d="M15.5 8.5v4h-4" /></svg>);
}
export function IconTrash({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M3 4.5h12M7 4.5V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1.5M4.5 4.5l.8 10a1 1 0 0 0 1 .9h5.4a1 1 0 0 0 1-.9l.8-10M7.5 7.5v5M10.5 7.5v5" /></svg>);
}
export function IconDownload({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M9 2v8.5M5.5 7L9 10.5 12.5 7M3 14.5h12" /></svg>);
}
export function IconSignal({ size = 16 }: P) {
  return (<svg {...base(size)}><circle cx="9" cy="13" r="1.5" /><path d="M5.5 9.5a5 5 0 0 1 7 0M3 7a8.5 8.5 0 0 1 12 0" /></svg>);
}
export function IconSparkle({ size = 16 }: P) {
  return (<svg {...base(size)} fill="currentColor" stroke="none"><path d="M9 1.2l1.4 4a3 3 0 0 0 1.7 1.7l4 1.4-4 1.4a3 3 0 0 0-1.7 1.7L9 15.4l-1.4-4a3 3 0 0 0-1.7-1.7L1.9 8.3l4-1.4A3 3 0 0 0 7.6 5.2z" /></svg>);
}
export function IconCheck({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M3.5 9.5L7 13l7.5-8" /></svg>);
}
export function IconBranch({ size = 16 }: P) {
  return (<svg {...base(size)}><circle cx="5" cy="4" r="2.2" /><circle cx="5" cy="14" r="2.2" /><circle cx="13" cy="7" r="2.2" /><path d="M5 6.2v5.6M5 11c0-3.4 1.8-4 8-4" /></svg>);
}
export function IconEdit({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M11.5 2.5l4 4M2.5 15.5l1-3.5L12 3.5l3 3-8.5 8.5z" /></svg>);
}
export function IconWarn({ size = 16 }: P) {
  return (<svg {...base(size)}><path d="M9 2.5l7 12.5H2z" /><path d="M9 7v3.5M9 12.6v.1" /></svg>);
}

/** Colored severity dot — replaces the 🔴🟡🔵 emoji grammar everywhere. */
export function SeverityDot({ sev, size = 9 }: { sev: string; size?: number }) {
  const color = sev === "critical" ? "#B71C1C" : sev === "warning" ? "#C86A00" : "#1565C0";
  return (<span style={{
    display: "inline-block", width: size, height: size, borderRadius: "50%",
    background: color, flexShrink: 0,
    boxShadow: `0 0 0 3px ${color}1f`,
  }} />);
}
