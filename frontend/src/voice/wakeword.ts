// Wake word detection for "Hey Moufida".
// When VITE_PORCUPINE_KEY env var is set and hey-moufida.ppn is present,
// the Porcupine Web SDK is loaded dynamically. Otherwise falls back to the
// Ctrl+Space keyboard shortcut so the app is fully usable without the key.

declare global {
  interface ImportMeta {
    readonly env: Record<string, string | undefined>;
  }
}

type PorcupineWorkerModule = {
  PorcupineWorker: {
    create: (
      key: string,
      model: unknown,
      cb: () => void
    ) => Promise<{ start: () => Promise<void>; release: () => void }>;
  };
};

export async function startWakeWordDetection(onWake: () => void): Promise<() => void> {
  const porcupineKey = import.meta.env["VITE_PORCUPINE_KEY"];

  if (porcupineKey) {
    try {
      // @vite-ignore disables import-analysis so the missing package doesn't
      // break the dev server. Install @picovoice/porcupine-web when the key
      // and hey-moufida.ppn are available.
      const mod = await (
        // eslint-disable-next-line @typescript-eslint/no-implied-eval
        new Function('pkg', 'return import(pkg)')("@picovoice/porcupine-web") as Promise<PorcupineWorkerModule>
      );
      const ppnResp = await fetch("/hey-moufida.ppn");
      if (!ppnResp.ok) throw new Error("hey-moufida.ppn not found");
      const worker = await mod.PorcupineWorker.create(
        porcupineKey,
        { label: "Hey Moufida", publicPath: "/hey-moufida.ppn" },
        () => onWake()
      );
      await worker.start();
      return () => { worker.release(); };
    } catch (err) {
      console.warn("[wakeword] Porcupine unavailable:", err);
    }
  }

  // Keyboard fallback: Ctrl+Space triggers the wake callback.
  const handler = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.code === "Space") {
      e.preventDefault();
      onWake();
    }
  };
  window.addEventListener("keydown", handler);
  return () => window.removeEventListener("keydown", handler);
}
