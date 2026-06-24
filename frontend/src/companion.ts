import { getCurrentWindow, LogicalPosition } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import { listen, emitTo } from '@tauri-apps/api/event';
import {
  CANVAS_W, CANVAS_H, drawChar,
} from './pixelArt/moufida';
import type { CharacterState } from './pixelArt/moufida';
import { setupDragDrop } from './companionIngest';

// ── Types ──────────────────────────────────────────────────────────
type State = CharacterState;

// ── App state ─────────────────────────────────────────────────────
let posX       = 0;
let posY       = 0;
let dir        = -1;         // 1 = right, -1 = left
let walkFrame  = 0;
let cState: State = 'walk';
let yBounce    = 0;
let blinking   = false;
let wavePhase  = 0;          // 0 = no wave, 1 = arm up mid, 2 = arm up high

// Timing
let lastWalkToggle  = 0;
let lastPosUpdate   = 0;
let lastBlink       = 0;
let lastIdleAnim    = 0;
let lastInteraction = 0;    // last direct physical interaction (mouse events)
let lastActivity    = 0;    // last any notable event (includes main-window pushes)
let waveTimer: ReturnType<typeof setTimeout> | null = null;
let autoTypingTimer: ReturnType<typeof setTimeout> | null = null;
let reactTimer: ReturnType<typeof setTimeout> | null = null;

const WALK_MS        = 380;      // ms between walk-frame switches
const POS_MS         = 55;       // ms between window setPosition calls
const BLINK_MS       = 4500;     // ms between blinks (random offset added)
const IDLE_MS        = 5000;     // ms between idle animations
const TYPING_IDLE_MS = 55_000;   // no-interaction time before auto-typing kicks in
const TYPING_DUR_MS  = 10_000;   // how long she types before returning to walk
const SLEEP_MS       = 180_000;  // no-activity time before she falls asleep

// How long each reactive state plays before auto-reverting to walk.
const REACT_DUR: Partial<Record<State, number>> = {
  cool:     4500,
  facepalm: 3000,
  crying:   5500,
};

// Roaming: only move 200 logical px left from the right edge.
let ROAM_RIGHT = 0;
let ROAM_LEFT  = 0;

// ── Drag-to-move ──────────────────────────────────────────────────
const ROAM_HALF_SPAN = 110;
const DRAG_THRESHOLD = 4;
let pointerDown   = false;
let isDragging    = false;
let dragStartX    = 0;
let dragStartY    = 0;
let stateBeforeDrag: State = 'walk';
let suppressClickUntil = 0;

// ─────────────────────────────────────────────────────────────────
// Bounce animation for startled state
// ─────────────────────────────────────────────────────────────────
function playBounce(onDone: () => void) {
  let t = 0;
  const id = setInterval(() => {
    t += 35;
    yBounce = t < 240 ? Math.round(-24 * Math.sin((t / 240) * Math.PI)) : 0;
    if (t >= 320) {
      clearInterval(id);
      yBounce = 0;
      onDone();
    }
  }, 35);
}

// ─────────────────────────────────────────────────────────────────
// Wave animation (arm raises and lowers)
// ─────────────────────────────────────────────────────────────────
function playWave() {
  const frames: number[] = [1, 2, 2, 1, 0, 1, 2, 2, 1, 0];
  let i = 0;
  if (waveTimer) clearTimeout(waveTimer);
  function step() {
    wavePhase = frames[i++];
    if (i < frames.length) {
      waveTimer = setTimeout(step, 160);
    } else {
      wavePhase = 0;
      waveTimer = null;
    }
  }
  step();
}

// ─────────────────────────────────────────────────────────────────
// Stretch — Y-arms reach, slow breath float; returns to idle.
// ─────────────────────────────────────────────────────────────────
function playStretch() {
  cState = 'stretching';
  setTimeout(() => {
    if (cState === 'stretching') cState = 'idle';
  }, 2400);
}

// ─────────────────────────────────────────────────────────────────
// Shrug — ¿ pose with floating "?"; returns to idle.
// ─────────────────────────────────────────────────────────────────
function playShrug() {
  cState = 'shrug';
  setTimeout(() => {
    if (cState === 'shrug') cState = 'idle';
  }, 1800);
}

// ─────────────────────────────────────────────────────────────────
// Idle animation pool — wave / stretch / shrug, weighted randomly.
// ─────────────────────────────────────────────────────────────────
function playIdleAnim() {
  const r = Math.random();
  if (r < 0.5)       playWave();
  else if (r < 0.75) playStretch();
  else               playShrug();
}

// ─────────────────────────────────────────────────────────────────
// Reactive states (cool / facepalm / crying) — auto-revert to walk.
// ─────────────────────────────────────────────────────────────────
function playReaction(state: State) {
  cState = state;
  if (reactTimer) clearTimeout(reactTimer);
  reactTimer = setTimeout(() => {
    if (cState === state) { cState = 'walk'; walkFrame = 0; }
    reactTimer = null;
  }, REACT_DUR[state] ?? 3000);
}

// ─────────────────────────────────────────────────────────────────
// Apply an incoming state from the main window.
// Reactive states auto-revert; everything else is a direct assignment.
// ─────────────────────────────────────────────────────────────────
function applyIncomingState(state: State) {
  if (REACT_DUR[state] !== undefined) {
    playReaction(state);
  } else {
    cState = state;
    if (state === 'walk') { walkFrame = 0; wavePhase = 0; }
  }
}

// ─────────────────────────────────────────────────────────────────
// Auto-typing — fires after TYPING_IDLE_MS with no interaction.
// Resets lastActivity so she doesn't immediately sleep after typing.
// ─────────────────────────────────────────────────────────────────
function startTyping() {
  cState = 'typing';
  lastActivity = performance.now();
  if (autoTypingTimer) clearTimeout(autoTypingTimer);
  autoTypingTimer = setTimeout(() => {
    if (cState === 'typing') {
      cState = 'walk';
      walkFrame = 0;
      // Reset lastInteraction so she doesn't immediately type again.
      lastInteraction = performance.now();
    }
    autoTypingTimer = null;
  }, TYPING_DUR_MS);
}

// ─────────────────────────────────────────────────────────────────
// interact() — call on any direct user interaction with the companion.
// Resets idle timers and wakes her from sleep / cancels typing.
// ─────────────────────────────────────────────────────────────────
function interact() {
  const now = performance.now();
  lastInteraction = now;
  lastActivity    = now;

  if (cState === 'sleeping') {
    cState = 'startled';
    playBounce(() => { cState = 'walk'; });
  } else if (cState === 'typing' && autoTypingTimer) {
    clearTimeout(autoTypingTimer);
    autoTypingTimer = null;
    cState = 'walk';
  }
}

// ─────────────────────────────────────────────────────────────────
// Drag helpers
// ─────────────────────────────────────────────────────────────────
async function syncPosFromWindow(win: ReturnType<typeof getCurrentWindow>) {
  try {
    const phys = await win.outerPosition();
    const sf   = await win.scaleFactor();
    posX = phys.x / sf;
    posY = phys.y / sf;
  } catch (e) {
    console.warn('[companion] position sync:', e);
  }
  const maxX = Math.max(0, window.screen.width - CANVAS_W);
  ROAM_LEFT  = Math.max(0,    posX - ROAM_HALF_SPAN);
  ROAM_RIGHT = Math.min(maxX, posX + ROAM_HALF_SPAN);
}

// ─────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────
async function main() {
  const canvas = document.getElementById('c') as HTMLCanvasElement;
  canvas.width  = CANVAS_W;
  canvas.height = CANVAS_H;
  canvas.style.width  = `${CANVAS_W}px`;
  canvas.style.height = `${CANVAS_H}px`;

  const ctx = canvas.getContext('2d')!;
  ctx.imageSmoothingEnabled = false;

  const win = getCurrentWindow();

  canvas.style.cursor = 'grab';

  // Seed idle timers so she doesn't type or sleep on the first frame.
  lastInteraction = performance.now();
  lastActivity    = performance.now();

  function endDrag() {
    if (!isDragging) return;
    isDragging  = false;
    pointerDown = false;
    canvas.style.cursor = 'grab';
    suppressClickUntil = performance.now() + 400;
    void syncPosFromWindow(win).then(() => {
      cState = 'startled';
      playBounce(() => {
        cState = (stateBeforeDrag === 'dragging' || stateBeforeDrag === 'idle')
          ? 'walk'
          : stateBeforeDrag;
        walkFrame = 0;
      });
    });
  }

  canvas.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    interact();
    pointerDown     = true;
    isDragging      = false;
    dragStartX      = e.screenX;
    dragStartY      = e.screenY;
    stateBeforeDrag = cState;
  });

  canvas.addEventListener('pointermove', (e) => {
    if (!pointerDown || isDragging) return;
    const dx = e.screenX - dragStartX;
    const dy = e.screenY - dragStartY;
    if (Math.hypot(dx, dy) <= DRAG_THRESHOLD) return;

    isDragging          = true;
    cState              = 'dragging';
    wavePhase           = 0;
    canvas.style.cursor = 'grabbing';
    win.startDragging().catch((err) => {
      console.warn('[companion] startDragging:', err);
      endDrag();
    });
  });

  canvas.addEventListener('pointerup', () => { if (!isDragging) pointerDown = false; });
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);
  window.addEventListener('blur', endDrag);

  canvas.addEventListener('click', () => {
    if (performance.now() < suppressClickUntil) return;
    void handleClick();
  });
  canvas.addEventListener('dblclick', () => {
    if (performance.now() < suppressClickUntil) return;
    void handleDblClick();
  });

  // Hover: pause walking, wake from sleep, cancel typing.
  canvas.addEventListener('mouseenter', () => {
    interact();
    if (!isDragging && cState === 'walk') cState = 'idle';
  });
  canvas.addEventListener('mouseleave', () => {
    if (!isDragging && cState === 'idle') cState = 'walk';
  });

  const sw = window.screen.width;
  const sh = window.screen.height;

  ROAM_RIGHT = sw - CANVAS_W - 20;
  ROAM_LEFT  = Math.max(0, sw - CANVAS_W - 220);
  posX = ROAM_RIGHT;
  posY = sh - CANVAS_H - 48;

  try {
    await win.setPosition(new LogicalPosition(Math.round(posX), Math.round(posY)));
  } catch (e) {
    console.warn('[companion] setPosition:', e);
  }

  const dragDrop = setupDragDrop({
    setState: (s) => { cState = s; },
    rest:     () => { cState = 'walk'; walkFrame = 0; wavePhase = 0; },
  });

  try {
    await listen<string>('companion_state', (ev) => {
      if (dragDrop.isBusy()) return;
      const incoming = ev.payload as State;

      // Any main-window push resets the sleep timer.
      lastActivity = performance.now();

      // Cancel auto-typing so the reaction is immediately visible.
      if (autoTypingTimer) {
        clearTimeout(autoTypingTimer);
        autoTypingTimer = null;
      }

      // Wake from sleep with a startled bounce, then apply the new state.
      if (cState === 'sleeping') {
        if (incoming !== 'walk' && incoming !== 'sleeping') {
          cState = 'startled';
          playBounce(() => { applyIncomingState(incoming); });
        } else {
          cState = 'walk';
        }
        return;
      }

      applyIncomingState(incoming);
    });
  } catch (e) {
    console.warn('[companion] listen:', e);
  }

  // ── Animation loop ──────────────────────────────────────────────
  requestAnimationFrame(loop);

  function loop(ts: number) {
    const isWalking = cState === 'walk';

    // Walk frame toggle
    if (isWalking && ts - lastWalkToggle > WALK_MS) {
      walkFrame = 1 - walkFrame;
      lastWalkToggle = ts;
    }

    // Move window left/right within the roam strip
    if (isWalking && ts - lastPosUpdate > POS_MS) {
      posX += dir * 1.0;
      if (posX <= ROAM_LEFT)  dir =  1;
      if (posX >= ROAM_RIGHT) dir = -1;
      win.setPosition(new LogicalPosition(Math.round(posX), Math.round(posY)));
      lastPosUpdate = ts;
    }

    // Blink every ~4.5 s (eyes already closed while sleeping)
    if (!blinking && cState !== 'sleeping' && ts - lastBlink > BLINK_MS + (Math.random() * 1500 | 0)) {
      blinking = true;
      lastBlink = ts;
      setTimeout(() => { blinking = false; }, 120);
    }

    // Idle random animations: wave / stretch / shrug
    if (cState === 'idle' && ts - lastIdleAnim > IDLE_MS && wavePhase === 0) {
      lastIdleAnim = ts;
      playIdleAnim();
    }

    // Auto-typing: she starts typing when ignored for TYPING_IDLE_MS.
    if ((cState === 'walk' || cState === 'idle')
        && wavePhase === 0
        && autoTypingTimer === null
        && ts - lastInteraction > TYPING_IDLE_MS) {
      startTyping();
    }

    // Auto-sleep: she nods off after SLEEP_MS of no activity.
    if ((cState === 'walk' || cState === 'idle')
        && autoTypingTimer === null
        && ts - lastActivity > SLEEP_MS) {
      cState = 'sleeping';
    }

    // Body bob: 1px down on walk-frame 1 to simulate stepping
    const walkBob = isWalking && walkFrame === 1 ? 1 : 0;
    const totalBounce = yBounce + walkBob;

    const flipX = dir === -1;
    drawChar(ctx, walkFrame, blinking, wavePhase, cState, flipX, totalBounce, true);

    requestAnimationFrame(loop);
  }
}

// ─────────────────────────────────────────────────────────────────
// Click handler — show main Moufida window
// ─────────────────────────────────────────────────────────────────
async function handleClick() {
  if (cState === 'startled') return;

  cState = 'startled';
  playBounce(() => { cState = 'walk'; });

  try {
    await invoke<void>('show_main_window');
  } catch (err) {
    console.error('[companion] show_main_window failed:', err);
  }
}

// ─────────────────────────────────────────────────────────────────
// Double-click handler — show main window + trigger a quick diagnostic
// ─────────────────────────────────────────────────────────────────
async function handleDblClick() {
  try {
    await invoke<void>('show_main_window');
    await emitTo('main', 'run_quick_diagnostic', {});
  } catch (err) {
    console.error('[companion] quick diagnostic failed:', err);
  }
}

main().catch(console.error);
