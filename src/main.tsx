import React from "react"
import ReactDOM from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import App from "./App"
import "./index.css"

// =============================================================================
// BrowserRouter basename — GitHub Pages subdirectory routing
// =============================================================================
// Vite config sets `base: '/experiment-engine/'` in production, which
// makes `import.meta.env.BASE_URL` === '/experiment-engine/'.
//
// React Router's `<BrowserRouter basename>` must match this path so that
// client-side routes work correctly:
//   /experiment-engine/dashboard  →  App matches /dashboard
//   /experiment-engine/input      →  App matches /input
//
// In dev mode BASE_URL is '/', so basename is empty (no prefix needed).
// =============================================================================

const BASENAME = import.meta.env.BASE_URL.replace(/\/+$/, "")

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter basename={BASENAME}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
