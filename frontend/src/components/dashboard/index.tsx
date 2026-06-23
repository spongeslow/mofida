import { useEffect, useRef, useState } from "react";
import type React from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { runDiagnostic, uploadDocument } from "../../api";
import { C, F, scoreColor } from "../../theme";
import { PixelMoufida } from "../companion/PixelMoufida";
import { MaturityCard } from "./MaturityCard";
import { ScoreGauge } from "./ScoreGauge";
import { ConceptBreakdown } from "./ConceptBreakdown";
import { BlockerList } from "./BlockerList";
import { RecommendationsCard } from "./RecommendationsCard";
import { RoadmapTimeline } from "./RoadmapTimeline";
import { CompetitorBoard } from "./CompetitorBoard";
import { OpportunityRadar } from "./OpportunityRadar";
import { EventFeed } from "../EventFeed";
import { WhatsNew } from "../WhatsNew";

const SCORE_LABELS: Record<string, string> = {
  market: "score_market",
  commercial_offer: "score_commercial_offer",
  innovation: "score_innovation",
  scalability: "score_scalability",
  green: "score_green",
};

// Section eyebrow that breaks the long page into legible chapters.
function SectionTitle({ children }: { children: React.ReactNode }) {
  return <div className="mf-section-title">{children}</div>;
}

// Animate a number toward its target (shared count-up easing).
function useCountUp(target: number, ms = 700): number {
  const [val, setVal] = useState(target);
  const fromRef = useRef(target);
  useEffect(() => {
    const from = fromRef.current;
    if (from === target) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(from + (target - from) * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return val;
}

// Circular gauge for the overall project health (0–5).
function HealthRing({ value }: { value: number }) {
  const t = useT();
  const animated = useCountUp(value);
  const r = 46;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, animated / 5));
  const color = scoreColor(animated);
  return (
    <div style={{ position: "relative", width: 116, height: 116, flexShrink: 0 }}>
      <svg width="116" height="116" viewBox="0 0 116 116" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="58" cy="58" r={r} fill="none" stroke={C.border} strokeWidth="9" opacity={0.6} />
        <circle
          cx="58" cy="58" r={r} fill="none" stroke={color} strokeWidth="9"
          strokeLinecap="round" strokeDasharray={circ}
          strokeDashoffset={circ * (1 - pct)}
          style={{ transition: "stroke 0.4s ease" }}
        />
      </svg>
      <div style={{
        position: "absolute", inset: 0, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
      }}>
        <span style={{ fontSize: 30, fontWeight: 800, color, lineHeight: 1, fontFamily: F.heading }}>
          {animated.toFixed(1)}
        </span>
        <span style={{ fontSize: 10.5, color: C.muted, textTransform: "uppercase", letterSpacing: 0.6, marginTop: 2 }}>
          {t("dash_health")}
        </span>
      </div>
    </div>
  );
}

function StatChip({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="mf-stat-chip">
      <span style={{ fontSize: 10.5, color: C.muted, textTransform: "uppercase", letterSpacing: 0.5, fontWeight: 600 }}>
        {label}
      </span>
      <span style={{ fontSize: 14, fontWeight: 700, color: color ?? C.text, lineHeight: 1.2 }}>
        {value}
      </span>
    </div>
  );
}

export function Dashboard() {
  const t = useT();
  const projectId             = useStore((s) => s.projectId);
  const lang                  = useStore((s) => s.lang);
  const scores                = useStore((s) => s.scores);
  const blockers              = useStore((s) => s.blockers);
  const recommendations       = useStore((s) => s.recommendations);
  const maturityStage         = useStore((s) => s.maturityStage);
  const applyDiagnosticResult = useStore((s) => s.applyDiagnosticResult);
  const diagnosticRequest     = useStore((s) => s.diagnosticRequest);
  const pulseCompanion        = useStore((s) => s.pulseCompanion);
  const setView               = useStore((s) => s.setView);

  const [loading, setLoading] = useState(false);
  const [quickLoading, setQuickLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !projectId) return;
    setUploadStatus(t("doc_uploading"));
    try {
      const r = await uploadDocument(projectId, file);
      setUploadStatus(`✓ ${r.filename} (${r.char_count} ${t("doc_chars")})`);
    } catch (err) {
      setUploadStatus(`⚠︎ ${err instanceof Error ? err.message : "error"}`);
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const runDiag = async (quick = false) => {
    if (!projectId) return;
    const setBusy = quick ? setQuickLoading : setLoading;
    setBusy(true);
    setError(null);
    pulseCompanion("thinking");
    try {
      const result = await runDiagnostic(projectId, quick);
      applyDiagnosticResult(result);
      pulseCompanion("celebrating");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
      pulseCompanion("worried");
    } finally {
      setBusy(false);
    }
  };

  // Auto-run on first load when there is no score data yet
  useEffect(() => {
    if (projectId && Object.keys(scores).length === 0) {
      void runDiag();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // External diagnostic requests (keyboard shortcut, companion double-click)
  useEffect(() => {
    if (diagnosticRequest.nonce > 0) void runDiag(diagnosticRequest.quick);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diagnosticRequest.nonce]);

  // ── Derived "at a glance" health summary ────────────────────────
  const scoreEntries = Object.entries(scores);
  const hasScores = scoreEntries.length > 0;
  const overall = hasScores
    ? scoreEntries.reduce((a, [, v]) => a + v, 0) / scoreEntries.length
    : 0;
  const criticalCount = blockers.filter((b) => b.severity === "critical").length;
  const busy = loading || quickLoading;

  const sorted = [...scoreEntries].sort((a, b) => b[1] - a[1]);
  const strongest = sorted[0];
  const weakest = sorted[sorted.length - 1];
  const nextMove =
    recommendations.find((r) => r.priority === "high")?.action ??
    recommendations[0]?.action ?? null;

  // Companion mood + narrated one-liner driven by project state.
  let charState = "idle";
  let summary = t("dash_summary_none");
  if (busy) {
    charState = "thinking";
    summary = t("dash_summary_loading");
  } else if (hasScores) {
    if (criticalCount > 0) {
      charState = "worried";
      summary = criticalCount === 1
        ? t("dash_summary_blockers_one")
        : t("dash_summary_blockers_many").replace("{n}", String(criticalCount));
    } else if (overall >= 3.5) {
      charState = "presenting";
      summary = t("dash_summary_strong");
    } else if (overall >= 2.5) {
      charState = "presenting";
      summary = t("dash_summary_ok");
    } else {
      charState = "worried";
      summary = t("dash_summary_weak");
    }
  }

  const scoreLabel = (name: string) => t(SCORE_LABELS[name] ?? name);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      {/* ── Hero: narrated health header ─────────────────────────── */}
      <div className="mf-hero mf-anim-card" style={{ padding: "22px 26px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 22, flexWrap: "wrap", position: "relative", zIndex: 1 }}>
          {/* Companion */}
          <div style={{ filter: "drop-shadow(0 8px 18px rgba(111,78,55,0.22))", flexShrink: 0 }}>
            <PixelMoufida state={charState} cssScale={0.92} />
          </div>

          {/* Narration + maturity + stats */}
          <div style={{ flex: 1, minWidth: 260 }}>
            <p style={{
              margin: 0, fontSize: 11.5, color: C.muted, textTransform: "uppercase",
              letterSpacing: 0.8, fontWeight: 600,
            }}>
              {t("dash_greeting")}
            </p>
            <h2 style={{
              margin: "6px 0 14px", fontSize: 21, lineHeight: 1.35, color: C.text,
              fontFamily: F.heading, fontWeight: 700, maxWidth: 560,
            }}>
              {summary}
            </h2>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {maturityStage && (
                <StatChip label={t("maturity_stage")} value={maturityStage} color={C.primary} />
              )}
              {hasScores && (
                <StatChip
                  label={t("dash_stat_blockers")}
                  value={String(blockers.length)}
                  color={criticalCount > 0 ? C.error : C.success}
                />
              )}
              {strongest && (
                <StatChip label={t("dash_stat_strength")} value={scoreLabel(strongest[0])} color={C.success} />
              )}
              {weakest && strongest && weakest[0] !== strongest[0] && (
                <StatChip label={t("dash_stat_focus")} value={scoreLabel(weakest[0])} color={C.warning} />
              )}
            </div>

            {nextMove && (
              <div style={{
                marginTop: 14, display: "flex", alignItems: "flex-start", gap: 8,
                fontSize: 13.5, color: C.text, maxWidth: 600,
              }}>
                <span style={{
                  fontSize: 10.5, fontWeight: 700, color: C.accent, textTransform: "uppercase",
                  letterSpacing: 0.5, whiteSpace: "nowrap", marginTop: 2,
                }}>
                  ➜ {t("dash_next_move")}
                </span>
                <span style={{ lineHeight: 1.5 }}>{nextMove}</span>
              </div>
            )}
          </div>

          {/* Health ring */}
          {hasScores && <HealthRing value={overall} />}
        </div>

        {/* Action bar */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap",
          marginTop: 20, paddingTop: 18, borderTop: `1px solid ${C.border}`,
          position: "relative", zIndex: 1,
        }}>
          <button onClick={() => { void runDiag(false); }} disabled={busy} className="mf-btn-accent mf-press">
            {loading ? t("running_diagnostic") : `↻ ${t("run_diagnostic")}`}
          </button>
          <button onClick={() => { void runDiag(true); }} disabled={busy} className="mf-btn-ghost mf-press">
            {quickLoading ? t("quick_diagnostic_running") : `⚡ ${t("quick_diagnostic")}`}
          </button>
          {hasScores && (
            <button onClick={() => setView("scenarios")} className="mf-btn-ghost mf-press">
              🔀 {t("scenario_whatif")}
            </button>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.md,application/pdf,text/plain"
            onChange={(e) => { void handleUpload(e); }}
            style={{ display: "none" }}
          />
          <button onClick={() => fileRef.current?.click()} className="mf-btn-ghost mf-press">
            📎 {t("doc_upload")}
          </button>
          {uploadStatus && <span style={{ color: C.muted, fontSize: 12 }}>{uploadStatus}</span>}
          {error && <span style={{ color: C.error, fontSize: 13 }}>{error}</span>}
        </div>
      </div>

      {/* ── Maturity detail + scores ─────────────────────────────── */}
      <SectionTitle>{t("section_scores")}</SectionTitle>
      <MaturityCard />
      <ScoreGauge />

      {/* ── What needs attention (blockers ↔ recommendations) ────── */}
      {hasScores && (blockers.length > 0 || (recommendations && recommendations.length > 0)) && (
        <>
          <SectionTitle>{t("section_attention")}</SectionTitle>
          <div className="mf-dash-grid-2">
            <BlockerList />
            <RecommendationsCard />
          </div>
        </>
      )}

      {/* ── Deep analysis ────────────────────────────────────────── */}
      <ConceptBreakdown />

      {/* ── Market & opportunities ───────────────────────────────── */}
      {projectId && (
        <>
          <SectionTitle>{t("section_market")}</SectionTitle>
          <div className="mf-dash-grid-2">
            <OpportunityRadar projectId={projectId} />
            <CompetitorBoard projectId={projectId} />
          </div>
          <WhatsNew projectId={projectId} lang={lang} />
        </>
      )}

      {/* ── Roadmap ──────────────────────────────────────────────── */}
      <SectionTitle>{t("section_roadmap")}</SectionTitle>
      <RoadmapTimeline />

      {/* ── Recent activity ──────────────────────────────────────── */}
      {projectId && (
        <>
          <SectionTitle>{t("section_activity")}</SectionTitle>
          <EventFeed projectId={projectId} />
        </>
      )}
    </div>
  );
}
