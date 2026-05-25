import React, { useEffect } from "react"
import ReactDOM from "react-dom/client"
import { BrowserRouter, useNavigate } from "react-router-dom"
import App from "./App"
import "./index.css"

// =============================================================================
// SPA redirect restoration (GitHub Pages 404.html fallback)
// =============================================================================
// When a user navigates directly to a sub-route (e.g. /experiment-engine/dashboard),
// GitHub Pages serves 404.html, which stores the attempted URL in sessionStorage
// and redirects to the app root. This component reads that stored URL and
// navigates back to the intended route via React Router.
// =============================================================================

function RedirectRestorer(): React.ReactElement | null {
  const navigate = useNavigate()

  useEffect(() => {
    const attemptedUrl = sessionStorage.getItem("spa-redirect")
    if (attemptedUrl) {
      sessionStorage.removeItem("spa-redirect")
      // Extract the path portion after the basename so React Router can match it.
      // e.g. "/experiment-engine/dashboard" becomes "/dashboard"
      // If no basename prefix is found, use the URL as-is.
      const base = "/experiment-engine/"
      const route = attemptedUrl.startsWith(base)
        ? attemptedUrl.slice(base.length - 1) // keep leading "/"
        : attemptedUrl
      navigate(route, { replace: true })
    }
  }, [navigate])

  return null
}

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
      <RedirectRestorer />
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
