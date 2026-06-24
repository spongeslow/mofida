/**
 * AchievementsCard — lightweight gamification (Phase 5 / analysis §D3).
 * Milestones are derived from the live diagnostic state, persisted per project
 * in localStorage, and a celebrate pulse fires the first time one unlocks.
 */
import { useEffect, useMemo } from "react";
import type React from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { C, F, card } from "../../theme";
import {
  IconTarget, IconBolt, IconStar, IconShield, IconRocket, IconMap, IconTrophy, IconLock,
} from "../shared/icons";

interface BadgeDef {
  id: string;
  icon: React.ReactNode;
  labelKey: string;
  test: (s: {
    scores: Record<string, number>;
    blockers: unknown[];
    maturityStage: string | null;
    roadmap: unknown;
  }) => boolean;
}

const BADGES: BadgeDef[] = [
  { id: "first_score", icon: <IconTarget size={24} />, labelKey: "badge_first_score",
    test: (s) => Object.keys(s.scores).length > 0 },
  { id: "strong_axis", icon: <IconBolt size={24} />, labelKey: "badge_strong_axis",
    test: (s) => Object.values(s.scores).some((v) => v >= 4) },
  { id: "all_strong", icon: <IconStar size={24} />, labelKey: "badge_all_strong",
    test: (s) => Object.values(s.scores).length > 0 && Object.values(s.scores).every((v) => v >= 3.5) },
  { id: "no_blockers", icon: <IconShield size={24} />, labelKey: "badge_no_blockers",
    test: (s) => Object.keys(s.scores).length > 0 && s.blockers.length === 0 },
  { id: "advanced_stage", icon: <IconRocket size={24} />, labelKey: "badge_advanced_stage",
    test: (s) => !!s.maturityStage && ["Fundraising", "Launch Planning", "Growth"].includes(s.maturityStage) },
  { id: "roadmap_ready", icon: <IconMap size={24} />, labelKey: "badge_roadmap_ready",
    test: (s) => s.roadmap != null },
];

export function AchievementsCard() {
  const t = useT();
  const projectId     = useStore((s) => s.projectId);
  const scores        = useStore((s) => s.scores);
  const blockers      = useStore((s) => s.blockers);
  const maturityStage = useStore((s) => s.maturityStage);
  const roadmap       = useStore((s) => s.roadmap);
  const pulseCompanion = useStore((s) => s.pulseCompanion);

  const unlocked = useMemo(() => {
    const st = { scores, blockers, maturityStage, roadmap };
    return new Set(BADGES.filter((b) => b.test(st)).map((b) => b.id));
  }, [scores, blockers, maturityStage, roadmap]);

  // Persist + celebrate newly-unlocked badges (once).
  useEffect(() => {
    if (!projectId) return;
    const key = `moufida.badges.${projectId}`;
    let prev: string[] = [];
    try { prev = JSON.parse(localStorage.getItem(key) ?? "[]") as string[]; } catch { prev = []; }
    const prevSet = new Set(prev);
    const fresh = [...unlocked].filter((id) => !prevSet.has(id));
    if (fresh.length > 0) {
      try { localStorage.setItem(key, JSON.stringify([...prevSet, ...fresh])); } catch { /* ignore */ }
      pulseCompanion("celebrating");
    }
  }, [unlocked, projectId, pulseCompanion]);

  return (
    <div style={card}>
      <h3 style={{ margin: "0 0 14px", color: C.text, fontFamily: F.heading, fontSize: 16, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: C.accent }}><IconTrophy size={18} /></span>
        {t("badges_title")} <span style={{ color: C.muted, fontSize: 13, fontWeight: 400 }}>
          {unlocked.size} / {BADGES.length}
        </span>
      </h3>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        {BADGES.map((b) => {
          const got = unlocked.has(b.id);
          return (
            <div key={b.id} title={got ? t(b.labelKey) : t("badge_locked")} style={{
              display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
              width: 92, padding: "12px 8px", borderRadius: 12,
              background: got ? `${C.accent}14` : C.surfaceHigh,
              border: `1px solid ${got ? `${C.accent}55` : C.border}`,
              opacity: got ? 1 : 0.5, filter: got ? "none" : "grayscale(1)",
              transition: "all 0.3s ease",
            }}>
              <span style={{ lineHeight: 1, color: got ? C.accent : C.muted }}>{got ? b.icon : <IconLock size={22} />}</span>
              <span style={{ fontSize: 11, color: C.text, textAlign: "center", lineHeight: 1.3, fontFamily: F.body }}>
                {t(b.labelKey)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
