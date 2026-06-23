import { useEffect, useRef } from 'react';
import {
  CANVAS_W, CANVAS_H, drawChar, paletteFor,
} from '../../pixelArt/moufida';
import type { PaletteName } from '../../pixelArt/moufida';

interface Props {
  state?: string;
  /** CSS scale multiplier. Default = 1 (native 92×168 px). */
  cssScale?: number;
  showName?: boolean;
  /** Per-page costume palette (dress/sash/gold). Default = warm autumn. */
  theme?: PaletteName;
}

/**
 * React canvas component rendering the pixel-art Moufida character.
 * Uses the same drawing code as the companion desktop window.
 */
export function PixelMoufida({ state = 'idle', cssScale = 1, showName = false, theme = 'default' }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);

  // Keep a mutable ref to state so the animation loop sees the latest value
  // without needing to restart the rAF every time state changes.
  const stateRef = useRef(state);
  stateRef.current = state;

  // Resolve the palette once per theme change; the loop reads it via ref.
  const palRef = useRef(paletteFor(theme));
  palRef.current = paletteFor(theme);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d')!;
    ctx.imageSmoothingEnabled = false;

    let frame      = 0;
    let blinking   = false;
    let wavePhase  = 0;
    let lastToggle = 0;
    let lastBlink  = 0;
    let lastWave   = 0;
    let nextWaveGap = 5000;
    let waveTimer: ReturnType<typeof setTimeout> | null = null;
    let animId     = 0;

    function playWave() {
      const phases = [1, 2, 2, 1, 0, 1, 2, 1, 0];
      let i = 0;
      if (waveTimer) clearTimeout(waveTimer);
      function step() {
        wavePhase = phases[i++];
        if (i < phases.length) waveTimer = setTimeout(step, 180);
        else { wavePhase = 0; waveTimer = null; }
      }
      step();
    }

    function loop(ts: number) {
      const s = stateRef.current;

      // Walk-frame toggle for walking states
      if ((s === 'walk' || s === 'idle') && ts - lastToggle > 400) {
        frame = 1 - frame;
        lastToggle = ts;
      }

      // Blink
      if (!blinking && ts - lastBlink > 4200 + (Math.random() * 1200 | 0)) {
        blinking = true;
        lastBlink = ts;
        setTimeout(() => { blinking = false; }, 100);
      }

      // Idle wave with varied cadence so she doesn't feel robotic (3–8 s).
      if (s === 'idle' && ts - lastWave > nextWaveGap && wavePhase === 0) {
        lastWave = ts;
        nextWaveGap = 3000 + (Math.random() * 5000 | 0);
        playWave();
      }

      const walkBob = (s === 'walk' || s === 'idle') && frame === 1 ? 1 : 0;
      drawChar(ctx, frame, blinking, wavePhase, s, false, walkBob, showName, palRef.current);

      animId = requestAnimationFrame(loop);
    }

    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
      if (waveTimer) clearTimeout(waveTimer);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <canvas
      ref={ref}
      width={CANVAS_W}
      height={CANVAS_H}
      style={{
        width:           CANVAS_W * cssScale,
        height:          CANVAS_H * cssScale,
        imageRendering:  'pixelated',
        display:         'block',
      }}
    />
  );
}
