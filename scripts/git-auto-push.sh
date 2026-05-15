#!/bin/bash
# ==============================================================================
# git-auto-push.sh — 批处理后自动 commit & push
# 用途：每个工作批次后调用，确保所有改动及时入库，避免文件积压导致回档困难
# 用法：bash scripts/git-auto-push.sh
# ==============================================================================
set -euo pipefail

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录（脚本所在目录的上一级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${CYAN}  git-auto-push  —  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}  项目: $(basename "$PROJECT_ROOT")${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"

# ──────────────────────────────────────────────────
# 1. 检视当前仓库状态
# ──────────────────────────────────────────────────
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "detached")
if [ "$BRANCH" = "detached" ]; then
  echo -e "${RED}✗ HEAD 处于分离状态，无法推送。先 checkout 一个分支。${NC}"
  exit 1
fi

# 检查是否有远程仓库
REMOTE=$(git remote 2>/dev/null || echo "")
if [ -z "$REMOTE" ]; then
  echo -e "${YELLOW}⚠  无远程仓库配置，跳过 push。${NC}"
  NO_PUSH=true
else
  NO_PUSH=false
fi

# ──────────────────────────────────────────────────
# 2. 暂存所有改动
#    git add -A = 新文件 + 修改 + 删除，遵守 .gitignore
# ──────────────────────────────────────────────────
echo -e "${YELLOW}→ 扫描文件改动...${NC}"

# 先看看有哪些未跟踪/改动文件
UNTRACKED=$(git ls-files --others --exclude-standard | head -20)
MODIFIED=$(git diff --name-only 2>/dev/null | head -20)
DELETED=$(git diff --name-only --diff-filter=D 2>/dev/null | head -20)
STAGED=$(git diff --cached --name-only 2>/dev/null | head -20)

# 总计改动数（含未跟踪 + 已修改 + 已暂存 + 已删除）
TOTAL_CHANGES=$( \
  { git ls-files --others --exclude-standard; git diff --name-only; git diff --cached --name-only; } \
  | sort -u | wc -l \
)

if [ "$TOTAL_CHANGES" -eq 0 ]; then
  echo -e "${GREEN}✓ 工作区干净，无需提交。${NC}"
  exit 0
fi

echo -e "  发现 ${YELLOW}${TOTAL_CHANGES}${NC} 个文件有改动"

# 暂存所有
git add -A

# ──────────────────────────────────────────────────
# 3. 再次确认有内容可提交
#    (git add -A 可能 .gitignore 排除了所有新文件)
# ──────────────────────────────────────────────────
if git diff --cached --quiet; then
  echo -e "${GREEN}✓ 暂存区为空（所有改动被 .gitignore 排除），无需提交。${NC}"
  exit 0
fi

# ──────────────────────────────────────────────────
# 4. 生成描述性的 commit message
# ──────────────────────────────────────────────────
CHANGED_FILES=$(git diff --cached --name-only)
FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)

# 分类统计
SRC_COUNT=$(echo "$CHANGED_FILES" | grep -cE '^src/' || true)
WOLF_COUNT=$(echo "$CHANGED_FILES" | grep -cE '^\.wolf/' || true)
CONFIG_COUNT=$(echo "$CHANGED_FILES" | grep -cE '\.(json|yaml|yml|toml)$' || true)

# 提取主要变更文件列表（取前5个有代表性的）
KEY_FILES=$(echo "$CHANGED_FILES" | head -8 | sed 's/^/  • /')

# 动态生成分类标签
TAGS=""
[ "$SRC_COUNT" -gt 0 ] && TAGS="${TAGS}[src]"
[ "$WOLF_COUNT" -gt 0 ] && TAGS="${TAGS}[wolf]"
[ "$CONFIG_COUNT" -gt 0 ] && TAGS="${TAGS}[config]"
[ -z "$TAGS" ] && TAGS="[misc]"

# 构建 commit body
BODY=""
if [ -n "$KEY_FILES" ]; then
  BODY="${BODY}Changed files:
${KEY_FILES}
"
fi

# 如果有 .wolf/ 改动，附上说明
if [ "$WOLF_COUNT" -gt 0 ]; then
  BODY="${BODY}
📋 OpenWolf: ${WOLF_COUNT} file(s) updated (anatomy/memory/ledger/buglog)"
fi

COMMIT_MSG="auto: ${FILE_COUNT} file(s) ${TAGS}

${BODY}"

# ──────────────────────────────────────────────────
# 5. 执行 commit
# ──────────────────────────────────────────────────
echo -e "${YELLOW}→ 提交 ${FILE_COUNT} 个文件...${NC}"
git commit -m "$COMMIT_MSG" --no-verify 2>&1 | sed 's/^/  /'

COMMIT_HASH=$(git rev-parse --short HEAD)
echo -e "${GREEN}✓ 提交成功: ${COMMIT_HASH}${NC}"

# ──────────────────────────────────────────────────
# 6. 推送到远程
# ──────────────────────────────────────────────────
if [ "$NO_PUSH" = true ]; then
  echo -e "${YELLOW}⚠  无远程仓库，跳过推送。${NC}"
  exit 0
fi

echo -e "${YELLOW}→ 推送到 origin/${BRANCH}...${NC}"

# 先拉取远程，避免非快进冲突
# 使用 rebase 模式拉取，保持历史线性
set +e
git pull --rebase --autostash origin "$BRANCH" 2>&1 | sed 's/^/  /'
PULL_EXIT=$?
set -e

if [ $PULL_EXIT -ne 0 ]; then
  echo -e "${RED}✗ git pull 失败（exit=$PULL_EXIT）${NC}"
  echo -e "${YELLOW}  可能原因：远程有冲突需要手动解决。${NC}"
  echo -e "${YELLOW}  本地提交已存在（${COMMIT_HASH}），解决冲突后手动 push。${NC}"
  exit $PULL_EXIT
fi

# 推送
set +e
git push origin "$BRANCH" 2>&1 | sed 's/^/  /'
PUSH_EXIT=$?
set -e

if [ $PUSH_EXIT -ne 0 ]; then
  echo -e "${RED}✗ git push 失败（exit=$PUSH_EXIT）${NC}"
  echo -e "${YELLOW}  本地提交已存在（${COMMIT_HASH}），稍后手动重试即可。${NC}"
  exit $PUSH_EXIT
fi

echo -e "${GREEN}✓ 推送成功 → origin/${BRANCH}${NC}"
echo ""
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 完成: ${FILE_COUNT} 文件已提交并推送${NC}"
echo -e "${GREEN}     commit: ${COMMIT_HASH}${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
