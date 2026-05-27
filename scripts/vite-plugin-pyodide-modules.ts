/**
 * Vite plugin that serves Python module sources as JSON for Pyodide in dev mode.
 *
 * In production, the CI pipeline bundles Python source into experiment_engine.tar.gz
 * (see .github/workflows/deploy.yml). But in dev mode, that tar.gz does not exist,
 * so Pyodide's mountFromInline() falls back to creating empty directories, causing
 * ModuleNotFoundError at runtime.
 *
 * This plugin adds a Vite middleware at /py/modules.json that:
 *   - Reads ALL .py files recursively from src/experiment_engine/
 *   - Serves their content as a JSON object: { "src/experiment_engine/foo.py": "content...", ... }
 *
 * The worker's mountFromInline() then fetches this JSON and writes actual Python files
 * into Pyodide's VFS via FS.writeFile.
 */

import type { Plugin, ViteDevServer } from 'vite';
import fs from 'fs';
import path from 'path';

/**
 * Recursively collect all .py files under `dir`, using the `prefix` param to
 * compute paths relative to the project src/ directory (so the JSON keys look
 * like "src/experiment_engine/foo.py" rather than absolute filesystem paths).
 */
function getAllPyFiles(dir: string, prefix: string): Record<string, string> {
  const result: Record<string, string> = {};
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      // Skip __pycache__ — no need to serve compiled bytecode
      if (entry.name === '__pycache__') continue;
      const subResult = getAllPyFiles(fullPath, prefix);
      Object.assign(result, subResult);
    } else if (entry.name.endsWith('.py')) {
      const relPath = path.relative(prefix, fullPath).replace(/\\/g, '/');
      result[relPath] = fs.readFileSync(fullPath, 'utf-8');
    }
  }
  return result;
}

export function pyodideModulesPlugin(): Plugin {
  return {
    name: 'pyodide-modules',
    apply: 'serve', // Only activate in dev server mode (not during build)

    configureServer(server: ViteDevServer) {
      // Middleware to serve Python module sources as JSON.
      // Vite middleware runs after built-in transforms; we place this before
      // the static file handler so it intercepts /py/modules.json even though
      // there is no physical file at that path.
      server.middlewares.use('/py/modules.json', (_req, res) => {
        const srcDir = path.resolve(process.cwd(), 'src');
        const modulesDir = path.resolve(srcDir, 'experiment_engine');
        const modules = getAllPyFiles(modulesDir, srcDir);

        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
        res.end(JSON.stringify(modules));
      });
    },
  };
}
