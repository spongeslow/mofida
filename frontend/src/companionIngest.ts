// Drag-and-drop PDF ingestion for the standalone companion window.
//
// The OS file-drop lands on Moufida (the roaming pixel companion). Tauri gives us
// file *paths*, so we read the bytes in Rust (`read_dropped_file`), rebuild a
// `File`, and POST it to the existing ingestion endpoint via `uploadDocument`.
// Moufida reacts locally — surprised as the file approaches, chewing while she
// ingests, then celebrating (or worried on failure) — and notifies the main
// window so the KB browser refreshes.
import { getCurrentWindow } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import { emitTo } from '@tauri-apps/api/event';
import { uploadDocument } from './api';
import type { CharacterState } from './pixelArt/moufida';

// Shared with the main window's zustand store (same Tauri origin → shared storage).
const PROJECT_ID_KEY = 'moufida.projectId';

interface DroppedFile { name: string; mime: string; bytes_b64: string }

export interface DragDropHooks {
  /** Drive Moufida into a reaction state. */
  setState: (s: CharacterState) => void;
  /** Return Moufida to her resting (walking) behaviour. */
  rest: () => void;
}

export interface DragDropHandle {
  /** True while a hover/ingest reaction is playing — local control should win. */
  isBusy: () => boolean;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

export function setupDragDrop(hooks: DragDropHooks): DragDropHandle {
  let ingesting = false;
  let surprised = false;

  async function reactError(reason: string, filename?: string) {
    hooks.setState('worried');
    void emitTo('main', 'kb_ingest_error', { reason, filename });
    await sleep(2800);
  }

  async function ingest(path: string) {
    if (ingesting) return;
    ingesting = true;
    try {
      const projectId = localStorage.getItem(PROJECT_ID_KEY);
      if (!projectId) { await reactError('no_project'); return; }

      hooks.setState('eating');

      let file: DroppedFile;
      try {
        file = await invoke<DroppedFile>('read_dropped_file', { path });
      } catch (err) {
        // Rust rejects unsupported types / oversize files with a coded message.
        await reactError(String(err));
        return;
      }

      const buf = b64ToBytes(file.bytes_b64).buffer as ArrayBuffer;
      const f = new File([buf], file.name, { type: file.mime });

      try {
        const res = await uploadDocument(projectId, f);
        if (res.persisted) {
          hooks.setState('celebrating');
          void emitTo('main', 'kb_ingested', {
            filename: res.filename, char_count: res.char_count,
          });
          await sleep(4000);
        } else {
          await reactError(res.warning ?? 'no_extractable_text', file.name);
        }
      } catch {
        await reactError('upload_failed', file.name);
      }
    } finally {
      ingesting = false;
      surprised = false;
      hooks.rest();
    }
  }

  void getCurrentWindow().onDragDropEvent((event) => {
    const payload = event.payload as { type: string; paths?: string[] };
    switch (payload.type) {
      case 'enter':
      case 'over':
        if (!ingesting && !surprised) { surprised = true; hooks.setState('surprised'); }
        break;
      case 'leave':
        if (surprised && !ingesting) { surprised = false; hooks.rest(); }
        break;
      case 'drop': {
        surprised = false;
        const path = payload.paths?.[0];
        if (path) void ingest(path);
        else hooks.rest();
        break;
      }
    }
  });

  return { isBusy: () => ingesting || surprised };
}
