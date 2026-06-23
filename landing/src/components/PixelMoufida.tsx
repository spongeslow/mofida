"use client";

import { useEffect, useRef } from "react";
import {
  CANVAS_W,
  CANVAS_H,
  drawChar,
  paletteFor,
  type PaletteName,
} from "@/lib/pixel-moufida";

interface Props {
  state?: string;
  /** CSS scale multiplier. Default = 1 (native 92×168 px). */
  cssScale?: number;
  showName?: boolean;
  /** Per-page costume palette (dress/sash/gold). Default = warm autumn. */
  theme?: PaletteName;
  /** Mirror horizontally — used so she faces her direction of travel. */
  flip?: boolean;
  className?: string;
}

/**
 * Canvas-rendered pixel-art Moufida — the exact same character used in the
 * desktop app. Shares the framework-agnostic drawing code in lib/pixel-moufida.
 */
export function PixelMoufida({
  state = "idle",
  cssScale = 1,
  showName = false,
  theme = "default",
  flip = false,
  className,
}: Props) {
  const ref = useRef<HTMLCanvasElement>(null);

  // Mutable refs so the rAF loop always sees the latest props without restart.
  const stateRef = useRef(state);
  stateRef.current = state;
  const flipRef = useRef(flip);
  flipRef.current = flip;
  const palRef = useRef(paletteFor(theme));
  palRef.current = paletteFor(theme);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.imageSmoothingEnabled = false;

    let frame = 0;
    let blinking = false;
    let wavePhase = 0;
    let lastToggle = 0;
    let lastBlink = 0;
    let lastWave = 0;
    let nextWaveGap = 5000;
    let waveTimer: ReturnType<typeof setTimeout> | null = null;
    let animId = 0;

    function playWave() {
      const phases = [1, 2, 2, 1, 0, 1, 2, 1, 0];
      let i = 0;
      if (waveTimer) clearTimeout(waveTimer);
      function step() {
        wavePhase = phases[i++];
        if (i < phases.length) waveTimer = setTimeout(step, 180);
        else {
          wavePhase = 0;
          waveTimer = null;
        }
      }
      step();
    }

    function loop(ts: number) {
      const s = stateRef.current;

      if ((s === "walk" || s === "idle") && ts - lastToggle > 400) {
        frame = 1 - frame;
        lastToggle = ts;
      }

      if (!blinking && ts - lastBlink > 4200 + ((Math.random() * 1200) | 0)) {
        blinking = true;
        lastBlink = ts;
        setTimeout(() => {
          blinking = false;
        }, 100);
      }

      if (s === "idle" && ts - lastWave > nextWaveGap && wavePhase === 0) {
        lastWave = ts;
        nextWaveGap = 3000 + ((Math.random() * 5000) | 0);
        playWave();
      }

      const walkBob = (s === "walk" || s === "idle") && frame === 1 ? 1 : 0;
      drawChar(ctx!, frame, blinking, wavePhase, s, flipRef.current, walkBob, showName, palRef.current);

      animId = requestAnimationFrame(loop);
    }

    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
      if (waveTimer) clearTimeout(waveTimer);
    };
  }, [showName]);

  return (
    <canvas
      ref={ref}
      width={CANVAS_W}
      height={CANVAS_H}
      className={className}
      style={{
        width: CANVAS_W * cssScale,
        height: CANVAS_H * cssScale,
        imageRendering: "pixelated",
        display: "block",
      }}
    />
  );
}
