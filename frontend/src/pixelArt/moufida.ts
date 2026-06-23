// Shared pixel-art drawing code — no Tauri imports, usable in both
// the companion window (companion.ts) and the React app (PixelMoufida.tsx).

export const SC = 6;       // logical pixels per pixel-art unit
export const CW = 12;      // character art width (units)
export const CH = 24;      // character art height (units)
export const PAD = 10;     // horizontal margin
export const TOP = 18;     // name-badge height at canvas top
export const BOT = 6;      // bottom padding

export const CANVAS_W = CW * SC + PAD * 2; // 72 + 20 = 92
export const CANVAS_H = CH * SC + TOP + BOT; // 144 + 18 + 6 = 168

// ── Character states ──────────────────────────────────────────────
// Single source of truth for the (pixel) character's expressive states.
// Used by PixelMoufida (in-app) and companion.ts (desktop pet).
export type CharacterState =
  | 'idle'
  | 'walk'
  | 'listening'
  | 'thinking'
  | 'processing'
  | 'speaking'
  | 'alert'
  | 'celebrating'
  | 'sleeping'
  | 'skeptic'
  | 'presenting'
  | 'pointing_left'
  | 'worried'
  | 'surprised'
  | 'reading'
  | 'eating'
  | 'startled'
  | 'dragging';

// ── Palette ───────────────────────────────────────────────────────
export const P: Record<string, string> = {
  H: '#3A1F0E',  // hair dark
  h: '#5C3020',  // hair mid-tone
  S: '#D4956A',  // skin
  E: '#1A0A04',  // eye dark
  W: '#F5F0EC',  // eye white
  C: '#E08060',  // cheek blush
  N: '#C07845',  // nose
  M: '#8B3020',  // mouth
  T: '#F0C4A8',  // upper lip / teeth
  D: '#C96A2D',  // dress orange
  d: '#9B4D1C',  // dress shadow (sides)
  R: '#E07832',  // dress highlight
  B: '#7B4E30',  // sash/belt
  G: '#D98A3A',  // gold (earring, buckle)
  g: '#F0B848',  // gold highlight
  L: '#4A2810',  // tights/legs
  K: '#2C1007',  // shoes dark
};

// ── Per-page palette themes (Step 1.3) ───────────────────────────
// Each theme overrides only the costume colours (dress / sash / gold); skin,
// hair, and eyes stay constant so she's always recognisably Moufida.
export type PaletteName = 'default' | 'blue' | 'purple' | 'green' | 'rose';

const THEME_OVERRIDES: Record<PaletteName, Record<string, string>> = {
  default: {},
  blue:   { D: '#2D6FE0', d: '#1B4FA8', R: '#4D8AF0', B: '#1B3A6B', G: '#9CC2F5', g: '#CFE0FA' },
  purple: { D: '#7C4DD6', d: '#5A36A0', R: '#9466E6', B: '#3E2470', G: '#C7A8F0', g: '#E3D3FA' },
  green:  { D: '#2FA36B', d: '#1F7A4E', R: '#46B981', B: '#155039', G: '#9CE0BE', g: '#CFF3E0' },
  rose:   { D: '#D14D7A', d: '#A8365A', R: '#E66694', B: '#702443', G: '#F0A8C2', g: '#FAD3E0' },
};

/** Resolve a full colour palette for a theme (base P + costume overrides). */
export function paletteFor(name: PaletteName = 'default'): Record<string, string> {
  return { ...P, ...THEME_OVERRIDES[name] };
}

// ── Pixel-art rects [x, y, w, h, colorKey] ───────────────────────
type PR = [number, number, number, number, string];

export const BODY: PR[] = [
  // ── Hair ──────────────────────────────────────────────────────
  [3,0,6,1,'H'],              // hair top
  [2,1,8,1,'H'],              // hair mid
  [1,2,10,1,'H'],             // hair cap (widest)
  [1,3,2,6,'H'], [9,3,2,6,'H'],  // side hair (rows 3-8)
  // Hair highlight streak
  [4,0,4,1,'h'], [3,1,6,1,'h'],

  // ── Head skin ────────────────────────────────────────────────
  // Skin visible in the middle of hair (cols 3-8, rows 2-8)
  [3,2,6,7,'S'],

  // ── Eyes ─────────────────────────────────────────────────────
  // Left eye (cols 3-4, rows 4-5) – 2×2 expressive block
  [3,4,2,1,'E'],              // lid (dark top)
  [3,5,1,1,'W'], [4,5,1,1,'E'], // white + pupil

  // Right eye (cols 7-8, rows 4-5)
  [7,4,2,1,'E'],              // lid
  [7,5,1,1,'W'], [8,5,1,1,'E'], // white + pupil

  // Eye shine dots (1×1 white, top-left of each pupil)
  [3,4,1,1,'W'], [7,4,1,1,'W'],

  // ── Nose ─────────────────────────────────────────────────────
  [5,6,1,1,'N'], [6,6,1,1,'N'],

  // ── Cheeks ───────────────────────────────────────────────────
  [3,6,1,1,'C'], [8,6,1,1,'C'],
  [3,7,1,1,'C'], [8,7,1,1,'C'],

  // ── Mouth (smile) ────────────────────────────────────────────
  [4,8,1,1,'M'], [5,8,1,1,'M'], [6,8,1,1,'M'], [7,8,1,1,'M'],
  [4,8,1,1,'T'],  // small upper-lip highlight

  // ── Earrings (visible below side hair, rows 7-8) ─────────────
  [2,7,1,1,'G'], [2,8,1,1,'g'],   // left drop earring
  [9,7,1,1,'G'], [9,8,1,1,'g'],   // right drop earring

  // ── Neck ─────────────────────────────────────────────────────
  [4,9,4,2,'S'],

  // ── Dress / collar ───────────────────────────────────────────
  // V-collar (rows 11-12)
  [3,11,6,1,'D'], [4,11,1,1,'G'], [7,11,1,1,'G'],  // collar + gold accent
  [2,12,8,1,'D'],

  // Dress body (rows 13-18) with side shading
  [2,13,8,1,'D'],
  [2,14,8,1,'D'],
  [2,15,8,1,'D'],
  [2,16,8,1,'D'],
  [3,17,6,1,'D'], [3,18,6,1,'D'],  // hem narrows

  // Side shading (darker on dress sides for depth)
  [2,13,1,4,'d'], [9,13,1,4,'d'],
  [2,17,1,2,'d'], [9,17,1,2,'d'],

  // Dress highlight stripe (center, warm)
  [5,13,2,4,'R'],

  // ── Sash / belt (row 15) ─────────────────────────────────────
  [2,15,8,1,'B'],
  [5,15,2,1,'G'], [5,15,1,1,'g'],  // buckle + shine

  // ── Arms (rows 13-17, cols 0-1 and 10-11) ────────────────────
  [0,13,2,5,'S'], [10,13,2,5,'S'],
  // Arm shadow (inner edge)
  [1,13,1,5,'C'], [10,13,1,5,'C'],
];

// Walk animation: alternate leg positions between frame 0 and frame 1
export function getLegs(frame: number): PR[] {
  const baseY = 19;
  if (frame === 0) {
    return [
      // Legs spread (stride A)
      [2,baseY,3,3,'L'], [7,baseY,3,3,'L'],
      // Shoes
      [1,baseY+3,4,2,'K'], [7,baseY+3,4,2,'K'],
      // Shoe highlight
      [1,baseY+3,1,1,'h'], [7,baseY+3,1,1,'h'],
    ];
  }
  // Legs together (stride B)
  return [
    [3,baseY,3,3,'L'], [6,baseY,3,3,'L'],
    [2,baseY+3,4,2,'K'], [6,baseY+3,4,2,'K'],
    [2,baseY+3,1,1,'h'], [6,baseY+3,1,1,'h'],
  ];
}

// ── Blink overlay: replace eyes with closed lines ────────────────
export const BLINK: PR[] = [
  [3,4,2,2,'E'], [7,4,2,2,'E'],   // close both eyes
  [3,5,2,1,'S'], [7,5,2,1,'S'],   // restore skin on bottom row
];

// ── Wave overlay: right arm goes up ──────────────────────────────
// wavePhase: 0-2 → arm height (0=normal, 1=mid, 2=full up)
export function getWaveArm(phase: number): PR[] {
  const armX = 10;
  if (phase === 0) return [];
  if (phase === 1) return [[armX,11,2,2,'S']];   // arm raised partway
  return [[armX,9,2,4,'S']];                     // arm raised fully
}

// ── Expression / pose system (per-state overlays) ────────────────
// All overlays reuse the [x,y,w,h,colorKey] rect format and the P palette, so
// they stay crisp at any cssScale. Both PixelMoufida and the desktop pet get
// every pose for free since they share drawChar().

// Skin rect covering the default mouth row, drawn before a custom mouth.
const MOUTH_CLEAR: PR = [4, 8, 4, 1, 'S'];

/** Mouth expression per state. `open` toggles the speaking flap. */
export function getMouth(state: string, open: boolean): PR[] {
  switch (state) {
    case 'speaking':
      return open
        ? [MOUTH_CLEAR, [5, 8, 2, 1, 'M'], [5, 9, 2, 1, 'M']]  // open
        : [MOUTH_CLEAR, [4, 8, 4, 1, 'M']];                    // closed line
    case 'surprised':
      return [MOUTH_CLEAR, [5, 8, 2, 2, 'M']];                 // round "o"
    case 'eating':
      return open
        ? [MOUTH_CLEAR, [4, 8, 4, 2, 'M'], [5, 8, 2, 1, 'T']]  // wide chomp w/ teeth
        : [MOUTH_CLEAR, [5, 8, 2, 1, 'M']];                    // closed chew
    case 'skeptic':
    case 'worried':
      return [MOUTH_CLEAR, [4, 7, 1, 1, 'M'], [7, 7, 1, 1, 'M'], [5, 8, 2, 1, 'M']]; // frown
    default:
      return [];  // keep the default BODY smile
  }
}

// Generous boxes over the hanging arms, cleared to transparent before a re-pose.
const ARM_L_BOX: PR = [0, 9, 2, 9, ''];
const ARM_R_BOX: PR = [10, 9, 2, 9, ''];

/** Which hanging arm(s) to erase before drawing a custom arm pose. */
export function getArmClear(state: string): PR[] {
  switch (state) {
    case 'celebrating':                 return [ARM_L_BOX, ARM_R_BOX];
    case 'dragging':                    return [ARM_L_BOX, ARM_R_BOX];
    case 'skeptic':                     return [ARM_L_BOX, ARM_R_BOX];
    case 'reading':                     return [ARM_L_BOX, ARM_R_BOX];
    case 'pointing_left':               return [ARM_L_BOX];
    case 'presenting':                  return [ARM_R_BOX];
    case 'thinking':
    case 'processing':                  return [ARM_R_BOX];
    default:                            return [];
  }
}

/** Repositioned arm rects (skin) per state. */
export function getArmPose(state: string): PR[] {
  switch (state) {
    case 'celebrating':
      return [[0, 9, 2, 4, 'S'], [10, 9, 2, 4, 'S'], [0, 8, 1, 1, 'S'], [11, 8, 1, 1, 'S']]; // both up
    case 'dragging':
      // Arms stretched straight up as if being picked up by the scruff.
      return [[0, 7, 2, 6, 'S'], [10, 7, 2, 6, 'S'], [0, 6, 1, 1, 'S'], [11, 6, 1, 1, 'S']];
    case 'pointing_left':
      return [[0, 11, 2, 2, 'S'], [1, 13, 1, 2, 'S']];                  // left arm out/up
    case 'presenting':
      return [[10, 10, 2, 3, 'S'], [11, 9, 1, 1, 'S']];                 // right arm up
    case 'thinking':
    case 'processing':
      return [[10, 12, 2, 2, 'S'], [9, 10, 1, 2, 'S'], [9, 9, 1, 1, 'S']]; // hand to chin
    case 'skeptic':
      return [[2, 14, 8, 2, 'S'], [2, 14, 8, 1, 'C']];                  // crossed forearms
    case 'reading':
      return [[2, 16, 2, 2, 'S'], [8, 16, 2, 2, 'S']];                  // forearms forward
    default:
      return [];
  }
}

/** Held props (briefcase / pointer / book) per state, drawn in front. */
export function getAccessory(state: string): PR[] {
  switch (state) {
    case 'skeptic':     // briefcase by the right foot
      return [[9, 20, 3, 3, 'B'], [10, 19, 1, 1, 'K'], [10, 21, 1, 1, 'G']];
    case 'presenting':  // pointer stick from the raised right hand
      return [[11, 7, 1, 5, 'B'], [11, 6, 1, 1, 'g']];
    case 'reading':     // open book held in front
      return [[3, 15, 6, 3, 'B'], [4, 16, 4, 1, 'W'], [6, 15, 1, 3, 'K']];
    default:
      return [];
  }
}

/** Vertical body offset (px) for hop/slump states; `t` = ms timestamp. */
export function bodyOffset(state: string, t: number): number {
  switch (state) {
    case 'celebrating': return -Math.round(Math.abs(Math.sin(t / 180)) * 4) - 1;
    case 'alert':       return -Math.round(Math.abs(Math.sin(t / 120)) * 3);
    case 'surprised':   return -2;
    case 'dragging':    return Math.round(Math.sin(t / 90) * 1.5); // dangling jiggle
    case 'worried':     return 2;
    case 'sleeping':    return 1;
    case 'eating':      return Math.round(Math.sin(t / 100)); // small chew bob
    default:            return 0;
  }
}

/** Free-floating particles drawn in canvas space (flip-agnostic). */
export function drawParticles(
  ctx: CanvasRenderingContext2D, state: string, t: number, ox: number, oy: number,
): void {
  if (state === 'celebrating') {
    const colors = ['#C96A2D', '#E07832', '#D98A3A', '#F0B848', '#3C8C3C', '#5BA3D0'];
    const span = CW * SC;
    const fall = CH * SC * 0.78;
    for (let i = 0; i < 7; i++) {
      const px = ox + ((i * 13 + t * 0.04) % span);
      const py = oy - 4 + ((i * 29 + t * 0.11) % fall);
      ctx.fillStyle = colors[i % colors.length];
      ctx.fillRect(Math.round(px), Math.round(py), 3, 3);
    }
  } else if (state === 'worried') {
    ctx.fillStyle = '#5BA3D0';  // sweat drop at the temple
    const dy = ((t / 280) % 1) * 5;
    ctx.fillRect(ox + 9 * SC, Math.round(oy + 5 * SC + dy), 2, 3);
  } else if (state === 'eating') {
    // Crumbs flicking off the mouth as she chews.
    ctx.fillStyle = '#C96A2D';
    for (let i = 0; i < 3; i++) {
      const phase = (t / 240 + i * 0.33) % 1;
      const px = ox + (5 + i) * SC + Math.round(Math.sin((t / 90) + i) * 2);
      const py = oy + 9 * SC + Math.round(phase * 6);
      ctx.fillRect(px, py, 2, 2);
    }
  }
}

// ── Draw one character frame ──────────────────────────────────────
export function drawChar(
  ctx: CanvasRenderingContext2D,
  walkFrame: number,
  isBlinking: boolean,
  wavePhase: number,  // 0 = no wave, 1-2 = wave
  state: string,
  flipX: boolean,
  yBounce: number,
  showName: boolean,
  pal: Record<string, string> = P,
) {
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
  ctx.save();

  if (flipX) {
    ctx.translate(CANVAS_W, 0);
    ctx.scale(-1, 1);
  }

  const ox = PAD;
  const t  = typeof performance !== 'undefined' ? performance.now() : Date.now();
  const oy = TOP + yBounce + bodyOffset(state, t);

  // Base body
  for (const [x, y, w, h, c] of [...BODY, ...getLegs(walkFrame)]) {
    if (pal[c]) {
      ctx.fillStyle = pal[c];
      ctx.fillRect(ox + x * SC, oy + y * SC, w * SC, h * SC);
    }
  }

  // Per-state arm re-pose: erase the hanging arm(s), then draw the new pose.
  for (const [x, y, w, h] of getArmClear(state)) {
    ctx.clearRect(ox + x * SC, oy + y * SC, w * SC, h * SC);
  }
  for (const [x, y, w, h, c] of getArmPose(state)) {
    if (pal[c]) { ctx.fillStyle = pal[c]; ctx.fillRect(ox + x * SC, oy + y * SC, w * SC, h * SC); }
  }

  // Mouth expression (speaking flap / frown / surprised "o" / chewing).
  // Chewing flaps faster than speaking for a visible "nom nom".
  const mouthOpen = state === 'eating' ? (t % 180) < 90 : (t % 280) < 140;
  for (const [x, y, w, h, c] of getMouth(state, mouthOpen)) {
    if (pal[c]) { ctx.fillStyle = pal[c]; ctx.fillRect(ox + x * SC, oy + y * SC, w * SC, h * SC); }
  }

  // Eyes closed when blinking or asleep.
  if (isBlinking || state === 'sleeping') {
    for (const [x, y, w, h, c] of BLINK) {
      ctx.fillStyle = pal[c];
      ctx.fillRect(ox + x * SC, oy + y * SC, w * SC, h * SC);
    }
  }

  // Idle wave arm overlay.
  for (const [x, y, w, h, c] of getWaveArm(wavePhase)) {
    if (pal[c]) { ctx.fillStyle = pal[c]; ctx.fillRect(ox + x * SC, oy + y * SC, w * SC, h * SC); }
  }

  // Held accessories (briefcase / pointer / book) — drawn in front of the body.
  for (const [x, y, w, h, c] of getAccessory(state)) {
    if (pal[c]) { ctx.fillStyle = pal[c]; ctx.fillRect(ox + x * SC, oy + y * SC, w * SC, h * SC); }
  }

  // State overlays (speech / thought bubbles — drawn on unflipped side)
  ctx.restore();
  ctx.save();

  const overX = flipX ? PAD + SC * 0.5 : PAD + CW * SC + SC;
  const overY = TOP + yBounce;

  if (state === 'startled' || state === 'alert' || state === 'surprised' || state === 'dragging') {
    ctx.fillStyle = '#FFDD44';
    ctx.font = `bold ${SC * 2}px sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillText('!', overX, overY + SC);
  } else if (state === 'thinking' || state === 'processing') {
    ctx.fillStyle = 'rgba(80,40,10,0.55)';
    ctx.beginPath(); ctx.arc(overX, overY + SC * 0.5, 2, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(overX, overY - SC * 0.5, 3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#EDE0CE';
    ctx.strokeStyle = '#6F4E37';
    ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(overX, overY - SC * 3, 7, 0, Math.PI * 2);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#6F4E37';
    ctx.font = 'bold 7px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('?', overX, overY - SC * 3 + 3);
  } else if (state === 'listening') {
    ctx.fillStyle = '#C96A2D';
    ctx.font = `${SC + 3}px sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillText('♫', overX, overY);
  } else if (state === 'sleeping') {
    ctx.fillStyle = 'rgba(60,30,10,0.5)';
    ctx.font = `bold ${SC - 1}px sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillText('z', overX, overY);
    ctx.font = `bold ${SC + 1}px sans-serif`;
    ctx.fillText('z', overX + SC, overY - SC);
    ctx.font = `bold ${SC + 3}px sans-serif`;
    ctx.fillText('z', overX + SC * 2, overY - SC * 2.5);
  }

  ctx.restore();

  // Free-floating particles (confetti when celebrating, sweat when worried).
  drawParticles(ctx, state, t, PAD, TOP + yBounce);

  // ── Name badge (game-style) ───────────────────────────────────
  if (showName) {
    const cx = CANVAS_W / 2;
    const bw = 78;
    const bh = 14;
    // Dark semi-transparent box
    ctx.fillStyle = 'rgba(0,0,0,0.72)';
    ctx.fillRect(cx - bw / 2, 2, bw, bh);
    // Pixel border (1px lighter)
    ctx.strokeStyle = 'rgba(255,255,255,0.25)';
    ctx.lineWidth = 1;
    ctx.strokeRect(cx - bw / 2 + 0.5, 2.5, bw - 1, bh - 1);
    // Name text (game font, white)
    ctx.fillStyle = '#FFFFFF';
    ctx.font = "7px 'Press Start 2P', 'Courier New', monospace";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('MOUFIDA', cx, 10);
  }
}
