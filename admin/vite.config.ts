import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Standalone observability SPA for Moufida. Talks to the orchestrator admin API
// (default http://localhost:8001) directly from the browser — CORS on the
// orchestrator already allows any localhost origin.
export default defineConfig({
  plugins: [react()],
  server: { port: 3002, strictPort: true },
  preview: { port: 3002, strictPort: true },
});
