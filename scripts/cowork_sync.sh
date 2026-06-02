#!/bin/bash
# Royal Farmers FC — Cowork 沙箱同步脚本
# 在 Cowork/Claude 沙箱环境中运行，自动修补路径并完整同步数据
# 用法：bash scripts/cowork_sync.sh [--dry-run]

set -e

# ── 路径配置 ────────────────────────────────────────────────
# 沙箱内的挂载路径（Cowork 自动挂载）
SANDBOX_REPO="/sessions/practical-zen-ptolemy/mnt/royal-farmers-app"
SANDBOX_DATA="/sessions/practical-zen-ptolemy/mnt/numbers数据来源/shanghai farmers united"

# Mac 原始路径（脚本里的硬编码路径，需要替换）
MAC_REPO="/Users/macstudio/claude code/projects/royal-farmers-app"
MAC_DATA="/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"

PYTHON="python3"
TMP_DIR="/tmp/royal-farmers-patched"
DRY_RUN="${1:-}"

echo "========================================"
echo "Royal Farmers FC — Cowork 数据同步"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# ── 第一步：修补脚本路径 ────────────────────────────────────
echo ""
echo "📝 修补脚本路径..."
mkdir -p "$TMP_DIR"

for script in update_players.py update_season_stats.py update_fixtures.py check_milestones.py update_monthly.py; do
    cp "$SANDBOX_REPO/scripts/$script" "$TMP_DIR/$script"

    # 替换数据目录路径
    sed -i "s|$MAC_DATA|$SANDBOX_DATA|g" "$TMP_DIR/$script"

    # 替换项目目录路径（各种变量名写法）
    sed -i "s|PROJECT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))|PROJECT_DIR    = '$SANDBOX_REPO'|g" "$TMP_DIR/$script"
    sed -i "s|PROJECT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))|PROJECT_DIR  = '$SANDBOX_REPO'|g" "$TMP_DIR/$script"
    sed -i "s|PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))|PROJECT_DIR = '$SANDBOX_REPO'|g" "$TMP_DIR/$script"

    echo "   ✅ $script"
done

# ── 第二步：运行各脚本 ──────────────────────────────────────
echo ""
echo "🔄 运行数据更新脚本..."

cd "$SANDBOX_REPO"

run_step() {
    local label="$1"
    local script="$2"
    echo ""
    echo "→ $label"
    if [ "$DRY_RUN" = "--dry-run" ]; then
        $PYTHON "$TMP_DIR/$script" --dry-run 2>&1
    else
        $PYTHON "$TMP_DIR/$script" 2>&1
    fi
}

run_step "同步 PLAYERS 数组" "update_players.py"
run_step "更新赛季榜单" "update_season_stats.py"
run_step "更新赛程 FIXTURES" "update_fixtures.py"
run_step "检测里程碑 MILESTONES" "check_milestones.py"
run_step "更新月度榜单 MONTHLY" "update_monthly.py"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo ""
    echo "🔍 Dry-run 模式，不提交 git"
    exit 0
fi

# ── 第三步：Git 提交 + Push ────────────────────────────────
echo ""
echo "📦 Git 提交..."

# 清理残留锁文件
rm -f "$SANDBOX_REPO/.git/index.lock" \
       "$SANDBOX_REPO/.git/HEAD.lock" \
       "$SANDBOX_REPO/.git/objects/maintenance.lock" 2>/dev/null || true

git add data.jsx

if git diff --cached --quiet; then
    echo "✅ 无数据变更，跳过部署"
    exit 0
fi

TODAY=$(date '+%Y-%m-%d')
git -c user.email="us20190808@gmail.com" -c user.name="Royal Farmers" \
    commit -m "weekly sync $TODAY"

# GitHub token 通过环境变量传入（安全）
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ 未设置 GITHUB_TOKEN 环境变量，跳过 push"
    echo "   请在调用时传入：GITHUB_TOKEN=ghp_xxx bash scripts/cowork_sync.sh"
    exit 1
fi

REMOTE_URL="https://${GITHUB_TOKEN}@github.com/money19800000-cell/royal-farmers-app.git"
git push "$REMOTE_URL" main 2>&1 | sed "s/$GITHUB_TOKEN/***REDACTED***/g"

COMMIT=$(git rev-parse --short HEAD)
echo ""
echo "========================================"
echo "✅ 同步完成"
echo "   Commit: $COMMIT"
echo "   Vercel 已连接 GitHub，约 1 分钟后自动上线"
echo "   网站：https://www.royalfarmers.club/"
echo "========================================"
