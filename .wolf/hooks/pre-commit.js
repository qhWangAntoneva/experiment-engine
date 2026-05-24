import { execSync } from "node:child_process";
import { readStdin } from "./shared.js";

async function main() {
    const raw = await readStdin();
    let input;
    try { input = JSON.parse(raw); }
    catch { process.exit(0); return; }

    const cmd = input.tool_input?.command ?? "";
    // Only intervene for git commit (not push, status, diff, etc.)
    if (!/\bgit\s+commit\b/.test(cmd)) {
        process.exit(0);
        return;
    }

    process.stderr.write("[pre-commit hook] Formatting + staging all files before commit...\n");
    try {
        execSync("uv run ruff format .", { stdio: "pipe", timeout: 30000 });
        execSync("uv run ruff check --fix .", { stdio: "pipe", timeout: 30000 });
        execSync("git add -u", { stdio: "pipe", timeout: 10000 });
        process.stderr.write("[pre-commit hook] Done — all files formatted and staged.\n");
    } catch (e) {
        process.stderr.write(`[pre-commit hook] Warning: format/check failed (continuing anyway): ${e.message}\n`);
    }
    process.exit(0);
}

main().catch(() => process.exit(0));
