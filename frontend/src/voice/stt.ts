// Speech-to-text via Whisper (whisper-cli binary) invoked through Tauri.
// Records from the microphone using MediaRecorder, detects silence, then
// sends base64-encoded WAV to the Tauri `transcribe` command.

import { useStore } from "../store";

const SILENCE_THRESHOLD = 0.015; // RMS below this = silence
const SILENCE_DURATION_MS = 1500; // stop after 1.5s of silence
const MAX_DURATION_MS = 30_000;

function rms(buf: Float32Array): number {
  let sum = 0;
  for (const s of buf) sum += s * s;
  return Math.sqrt(sum / buf.length);
}

async function audioBufferToWavBase64(chunks: Blob[]): Promise<string> {
  const blob = new Blob(chunks, { type: "audio/webm" });
  const arrayBuf = await blob.arrayBuffer();
  const bytes = new Uint8Array(arrayBuf);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

export async function startListening(): Promise<string> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const ctx = new AudioContext();
  const source = ctx.createMediaStreamSource(stream);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 2048;
  source.connect(analyser);

  const recorder = new MediaRecorder(stream);
  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };

  useStore.getState().setVoiceState("listening");
  recorder.start(100);

  return new Promise((resolve, reject) => {
    const buf = new Float32Array(analyser.fftSize);
    let silenceStart: number | null = null;
    const deadline = Date.now() + MAX_DURATION_MS;

    const check = () => {
      analyser.getFloatTimeDomainData(buf);
      const level = rms(buf);

      if (level < SILENCE_THRESHOLD) {
        if (silenceStart === null) silenceStart = Date.now();
        else if (Date.now() - silenceStart > SILENCE_DURATION_MS) {
          stop();
          return;
        }
      } else {
        silenceStart = null;
      }

      if (Date.now() > deadline) { stop(); return; }
      requestAnimationFrame(check);
    };

    const stop = () => {
      recorder.stop();
      stream.getTracks().forEach((t) => t.stop());
      ctx.close();
    };

    recorder.onstop = async () => {
      useStore.getState().setVoiceState("transcribing");
      try {
        const b64 = await audioBufferToWavBase64(chunks);
        const { invoke } = await import("@tauri-apps/api/core");
        const transcript = await invoke<string>("transcribe", { audioB64: b64 });
        resolve(transcript);
      } catch (err) {
        reject(err);
      }
    };

    requestAnimationFrame(check);
  });
}
