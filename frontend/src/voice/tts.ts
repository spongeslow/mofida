// Text-to-speech via Piper (FR) or Kokoro (EN) invoked through Tauri.
// Calls the `speak` Tauri command which pipes text through the binary and aplay.

import { useStore } from "../store";

export async function speak(text: string, lang: string): Promise<void> {
  useStore.getState().setVoiceState("speaking");
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("speak", { text, lang });
  } catch (err) {
    console.warn("[tts] speak failed:", err);
  } finally {
    useStore.getState().setVoiceState("idle");
  }
}
