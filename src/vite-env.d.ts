/// <reference types="vite/client" />

// =============================================================================
// Vite client type declarations
// =============================================================================
// Provides types for `import.meta.env.*` used throughout the codebase:
//   import.meta.env.BASE_URL  — set by vite.config.ts `base` option
//   import.meta.env.MODE       — "development" | "production"
//   import.meta.env.DEV        — boolean
//   import.meta.env.PROD       — boolean
// =============================================================================
//
// plotly.js-dist-min v2.x does not ship TypeScript declarations; v3.x does, but
// we pin v2 for compatibility with the CDN-hosted Plotly.js version used by the
// Pyodide engine's JSON export path.
declare module 'plotly.js-dist-min';

declare module 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.mjs' {
  export function loadPyodide(options?: {
    indexURL?: string;
    fullStdLib?: boolean;
  }): Promise<any>;
}
