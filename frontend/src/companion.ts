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
let lastWalkToggle = 0;
let lastPosUpdate  = 0;
let lastBlink      = 0;
let lastIdleAnim   = 0;
let waveTimer: ReturnType<typeof setTimeout> | null = null;

const WALK_MS    = 380;   // ms between walk-frame switches
const POS_MS     = 55;    // ms between window setPosition calls
const BLINK_MS   = 4500; // ms between blinks (random offset added)
const IDLE_MS    = 5000; // ms between idle animations

// Roaming: only move 200 logical px left from the right edge.
let ROAM_RIGHT = 0;
let ROAM_LEFT  = 0;

// ── Drag-to-move ──────────────────────────────────────────────────
// The companion window is borderless/transparent, so we move it ourselves by
// tracking the cursor in *screen* coordinates (stable while the window moves).
const ROAM_HALF_SPAN = 110;   // logical px the roam strip extends each side of the drop point
const DRAG_THRESHOLD = 4;     // px the pointer must travel before it counts as a drag (vs. a click)
let pointerDown   = false;
let isDragging    = false;
let dragStartX    = 0;        // pointer screen X at press
let dragStartY    = 0;        // pointer screen Y at press
let stateBeforeDrag: State = 'walk';
let suppressClickUntil = 0;   // ignore the synthetic click the browser fires after a drag

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
// Drag helpers
// ─────────────────────────────────────────────────────────────────
/**
 * Read the window's real position back from the OS (it moved under us during a
 * compositor-driven drag) and re-anchor the roaming strip around where she
 * landed. Best-effort: position queries can be limited on some platforms.
 */
async function syncPosFromWindow(win: ReturnType<typeof getCurrentWindow>) {
  try {
    const phys = await win.outerPosition();      // physical pixels
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

  // ── Async init (failures don't block animation) ─────────────────
  const win = getCurrentWindow();

  // ── Pointer drag-to-move + click handlers (synchronous) ─────────
  // Registered before any await so they're always live. A press becomes a
  // *drag* only once the pointer travels past DRAG_THRESHOLD; otherwise it
  // stays a click (open main window) / double-click (quick diagnostic).
  //
  // We move the window via win.startDragging(): on Wayland an app cannot set
  // its own absolute position (setPosition is ignored), so we hand the move off
  // to the compositor. This works on X11/macOS/Windows too.
  canvas.style.cursor = 'grab';

  /** Called once the user releases after a drag (or the window loses focus). */
  function endDrag() {
    if (!isDragging) return;
    isDragging  = false;
    pointerDown = false;
    canvas.style.cursor = 'grab';
    // Swallow the synthetic click some platforms emit after a drag.
    suppressClickUntil = performance.now() + 400;
    // Resync to where the compositor left the window, then settle + resume.
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

    // Promote to a drag: grab her, freeze roaming/idle, hand off to the OS.
    isDragging          = true;
    cState              = 'dragging';
    wavePhase           = 0;
    canvas.style.cursor = 'grabbing';
    win.startDragging().catch((err) => {
      console.warn('[companion] startDragging:', err);
      // Fallback for platforms where it fails: keep her grabbed-looking,
      // but immediately settle so she isn't stuck in the dragging pose.
      endDrag();
    });
  });

  // The compositor owns the drag once it starts, so the reliable "drop" signal
  // is a window/document pointer-release or focus loss — listen broadly.
  canvas.addEventListener('pointerup', () => { if (!isDragging) pointerDown = false; });
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);
  window.addEventListener('blur', endDrag);

  // Click → open main window. Double-click → quick diagnostic.
  canvas.addEventListener('click', () => {
    if (performance.now() < suppressClickUntil) return;
    void handleClick();
  });
  canvas.addEventListener('dblclick', () => {
    if (performance.now() < suppressClickUntil) return;
    void handleDblClick();
  });

  // Hover: pause walking so the user can interact (but never while dragging).
  canvas.addEventListener('mouseenter', () => {
    if (!isDragging && cState === 'walk') cState = 'idle';
  });
  canvas.addEventListener('mouseleave', () => {
    if (!isDragging && cState === 'idle') cState = 'walk';
  });

  const sw = window.screen.width;
  const sh = window.screen.height;

  // Roam only within a 200px strip at the bottom-right
  ROAM_RIGHT = sw - CANVAS_W - 20;
  ROAM_LEFT  = Math.max(0, sw - CANVAS_W - 220);
  posX = ROAM_RIGHT;
  posY = sh - CANVAS_H - 48;   // above taskbar

  try {
    await win.setPosition(new LogicalPosition(Math.round(posX), Math.round(posY)));
  } catch (e) {
    console.warn('[companion] setPosition:', e);
  }

  // Drag-and-drop PDF ingestion: Moufida reacts (surprised → chewing →
  // celebrate/worried) locally and notifies the main window to refresh the KB.
  const dragDrop = setupDragDrop({
    setState: (s) => { cState = s; },
    rest:     () => { cState = 'walk'; walkFrame = 0; wavePhase = 0; },
  });

  try {
    await listen<string>('companion_state', (ev) => {
      // Local ingest reactions take priority over mood pushed from the main window.
      if (dragDrop.isBusy()) return;
      cState = ev.payload as State;
      if (cState === 'walk') { walkFrame = 0; wavePhase = 0; }
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

    // Blink every ~4.5 s
    if (!blinking && ts - lastBlink > BLINK_MS + (Math.random() * 1500 | 0)) {
      blinking = true;
      lastBlink = ts;
      setTimeout(() => { blinking = false; }, 120);
    }

    // Idle random actions (wave or another blink) when standing still
    if (cState === 'idle' && ts - lastIdleAnim > IDLE_MS && wavePhase === 0) {
      lastIdleAnim = ts;
      playWave();
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
