import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import type { VoiceState } from "../../types";
import { PixelMoufida } from "./PixelMoufida";
import type { CharacterState, PaletteName } from "../../pixelArt/moufida";

function voiceToChar(v: VoiceState): CharacterState {
  switch (v) {
    case "listening":    return "listening";
    case "transcribing": return "thinking";
    case "processing":   return "thinking";
    case "speaking":     return "speaking";
    default:             return "idle";
  }
}

interface Props {
  onClick: () => void;
  /** Per-page costume palette. */
  theme?: PaletteName;
}

/**
 * Persistent floating pixel companion (Phase 2.1). Reacts to voice state,
 * critical alerts, and transient "pulses" emitted from anywhere via the store
 * (SSE events, diagnostic lifecycle, …), then settles back to idle.
 */
export function MoufidaCompanion({ onClick, theme = "default" }: Props) {
  const voiceState = useStore((s) => s.voiceState);
  const alerts     = useStore((s) => s.alerts);
  const pulse      = useStore((s) => s.companionPulse);
  const daemonPaused = useStore((s) => s.daemonPaused);

  const [override, setOverride] = useState<CharacterState | null>(null);
  const prevCritCount = useRef(0);

  // Trigger alert animation when a new critical alert arrives.
  const critCount = alerts.filter((a) => !a.dismissed && a.severity === "critical").length;
  useEffect(() => {
    if (critCount > prevCritCount.current) {
      setOverride("alert");
      const t = setTimeout(() => setOverride(null), 3600);
      prevCritCount.current = critCount;
      return () => clearTimeout(t);
    }
    prevCritCount.current = critCount;
  }, [critCount]);

  // Play transient pulses (celebrating / worried / surprised / thinking / …).
  useEffect(() => {
    if (pulse.nonce === 0) return;
    setOverride(pulse.state as CharacterState);
    const dur = pulse.state === "celebrating" ? 4200 : 3200;
    const t = setTimeout(() => setOverride(null), dur);
    return () => clearTimeout(t);
  }, [pulse.nonce, pulse.state]);

  const charState: CharacterState =
    override ?? (daemonPaused && voiceState === "idle" ? "sleeping" : voiceToChar(voiceState));

  return (
    <div
      className="mf-companion-wrap"
      style={{
        position:     "fixed",
        bottom:       0,
        right:        22,
        zIndex:       9999,
        cursor:       "pointer",
        userSelect:   "none",
        pointerEvents:"all",
        filter:       "drop-shadow(0 6px 24px rgba(111,78,55,0.28))",
        overflow:     "visible",
      }}
      onClick={onClick}
      title="Parler à Moufida"
    >
      <PixelMoufida state={charState} cssScale={1.2} theme={theme} />
    </div>
  );
}
