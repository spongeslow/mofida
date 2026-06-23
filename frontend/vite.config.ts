import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { port: 5173, strictPort: true },
  optimizeDeps: {
    exclude: ["@picovoice/porcupine-web"],
  },
  build: {
    rollupOptions: {
      input: {
        main:      resolve(__dirname, "index.html"),
        companion: resolve(__dirname, "companion.html"),
      },
      external: ["@picovoice/porcupine-web"],
    },
  },
});
