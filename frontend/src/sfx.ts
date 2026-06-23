// Tiny Web Audio sound cues for companion reactions (Phase 7 / analysis §D4).
// Subtle, synthesized (no assets); best-effort and silent on failure.

let ctx: AudioContext | null = null;

function audioCtx(): AudioContext | null {
  try {
    const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return null;
    ctx = ctx ?? new Ctor();
    return ctx;
  } catch {
    return null;
  }
}

function tone(ac: AudioContext, freq: number, start: number, dur: number, gain = 0.05, type: OscillatorType = "sine") {
  const osc = ac.createOscillator();
  const g = ac.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  g.gain.setValueAtTime(0, start);
  g.gain.linearRampToValueAtTime(gain, start + 0.02);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(g).connect(ac.destination);
  osc.start(start);
  osc.stop(start + dur + 0.02);
}

/** Play a short cue for a companion state, if any is defined for it. */
export function playChime(kind: string): void {
  const ac = audioCtx();
  if (!ac) return;
  if (ac.state === "suspended") void ac.resume().catch(() => {});
  const t0 = ac.currentTime + 0.01;
  if (kind === "celebrating") {
    [523.25, 659.25, 783.99].forEach((f, i) => tone(ac, f, t0 + i * 0.09, 0.22, 0.05, "triangle"));
  } else if (kind === "alert") {
    tone(ac, 330, t0, 0.16, 0.06, "square");
    tone(ac, 247, t0 + 0.16, 0.22, 0.06, "square");
  } else if (kind === "surprised") {
    tone(ac, 660, t0, 0.12, 0.04, "sine");
    tone(ac, 880, t0 + 0.1, 0.14, 0.04, "sine");
  }
}
