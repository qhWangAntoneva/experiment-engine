import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

// =============================================================================
// Vite config for GitHub Pages deployment
// =============================================================================
// In production, assets are served from /experiment-engine/ (subdirectory).
// In development, assets are served from / (root of localhost:3000).

export default defineConfig(({ mode }) => ({
  plugins: [react()],

  base: mode === "production" ? "/experiment-engine/" : "/",

  server: {
    port: 3000,
    host: '127.0.0.1',
    open: true,
  },

  // Web Worker: ES module worker — Pyodide loaded via dynamic import()
  worker: {
    format: "es",
  },

  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false,
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-plotly": ["plotly.js-dist-min"],
        },
      },
    },
  },

  // Pyodide is loaded via dynamic import() from CDN in the Web Worker, not bundled
  optimizeDeps: {
    exclude: ["pyodide"],
  },
}))
