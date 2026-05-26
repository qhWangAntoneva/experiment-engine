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

    process.stderr.write("[pre-commit hook] Running all pre-commit fixes + staging before commit...\n");
    try {
        // Run ALL pre-commit hooks (end-of-file-fixer, trailing-whitespace,
        // ruff-format, ruff, etc.) to fix everything before the actual commit.
        // This prevents the stash-conflict infinite loop where:
        //   1. non-Python files (e.g. memory.md) lack trailing newlines
        //   2. ruff alone doesn't fix them
        //   3. git add -u stages broken files
        //   4. The real git hook's end-of-file-fixer modifies staged files
        //   5. Stash/unstash cycle conflicts and reverts fixes
        execSync("uv run pre-commit run --all-files", {
            stdio: "pipe",
            timeout: 60000,
        });
        // Stage all fixes applied by pre-commit hooks
        execSync("git add -u", { stdio: "pipe", timeout: 10000 });
        process.stderr.write("[pre-commit hook] Done — all pre-commit checks pass, files staged.\n");
    } catch (e) {
        process.stderr.write(
            `[pre-commit hook] Warning: pre-commit run failed (continuing anyway): ${e.message}\n`
        );
    }
    process.exit(0);
}

main().catch(() => process.exit(0));
