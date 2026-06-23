import { useEffect, useRef, useState } from "react";
import { logStreamUrl } from "../api";
import { C, levelColor, mono } from "../theme";
import type { LogEntry } from "../types";
import { PageHeader, Pill, ChipButton } from "../ui";

const LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"];

export function Logs() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState("ALL");
  const [connected, setConnected] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const es = new EventSource(logStreamUrl());
    es.onopen = () => setConnected(true);
    es.onmessage = (e: MessageEvent<string>) => {
      try {
        const entry = JSON.parse(e.data) as LogEntry;
        setEntries((prev) => [...prev.slice(-800), entry]);
      } catch { /* keepalive */ }
    };
    es.onerror = () => setConnected(false);
    return () => es.close();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  const shown = filter === "ALL" ? entries : entries.filter((e) => e.level === filter);

  return (
    <div style={{ animation: "mf-fade .4s ease both" }}>
      <PageHeader
        eyebrow="Live stream"
        title="Logs"
        right={
          <>
            <Pill color={connected ? C.success : C.error}>
              <span style={{ width: 7, height: 7, borderRadius: "50%", background: connected ? C.success : C.error, display: "inline-block" }} />
              {connected ? "Live" : "Disconnected"}
            </Pill>
            <div style={{ display: "flex", gap: 6 }}>
              {LEVELS.map((l) => (
                <ChipButton key={l} active={filter === l} onClick={() => setFilter(l)}>{l}</ChipButton>
              ))}
            </div>
          </>
        }
      />
      <div
        style={{
          background: C.console,
          border: `1px solid ${C.border}`,
          borderRadius: 16,
          padding: "16px 18px",
          height: "calc(100vh - 260px)",
          overflowY: "auto",
          fontFamily: mono,
          fontSize: 12.5,
          lineHeight: 1.65,
          boxShadow: "inset 0 2px 12px rgba(0,0,0,0.25)",
        }}
      >
        {shown.map((e, i) => (
          <div key={i} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", padding: "1px 0" }}>
            <span style={{ color: "#8C7763" }}>[{e.ts.slice(11, 19)}]</span>{" "}
            <span style={{ color: levelColor(e.level), fontWeight: 600 }}>{e.level.padEnd(5)}</span>{" "}
            <span style={{ color: "#E0A45C" }}>{e.logger}</span>{" "}
            <span style={{ color: "#E9DCCB" }}>{e.message}</span>
          </div>
        ))}
        {shown.length === 0 && <div style={{ color: "#8C7763" }}>Waiting for logs…</div>}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
