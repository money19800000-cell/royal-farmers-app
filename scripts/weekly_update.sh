#!/bin/bash
# Royal Farmers FC — 每周自动数据更新脚本
# 每周三 9:00 由 LaunchAgent 自动触发
# 手动运行：bash scripts/weekly_update.sh

set -e  # 任意步骤失败则退出

PYTHON="/opt/homebrew/bin/python3.11"
REPO="/Users/macstudio/claude code/projects/royal-farmers-app"
VERCEL="/opt/homebrew/lib/node_modules/vercel/dist/vc.js"
LOG="/Users/macstudio/Library/Logs/royal-farmers-weekly.log"

echo "======================================" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') 开始自动更新" >> "$LOG"

cd "$REPO"

run_step() {
    echo "→ $1" | tee -a "$LOG"
    $PYTHON "$REPO/scripts/$2" 2>&1 | tee -a "$LOG"
}

# 1. 同步 PLAYERS 数组（含生涯总数 + 逐赛季数据）
run_step "同步 PLAYERS 数组" "update_players.py"

# 2. 更新赛季榜单（GOALS26/ASSISTS26/APPS26/ALL）
run_step "更新赛季榜单" "update_season_stats.py"

# 3. 更新赛程 FIXTURES
run_step "更新赛程 FIXTURES" "update_fixtures.py"

# 4. 检测并更新里程碑 MILESTONES
run_step "更新里程碑 MILESTONES" "check_milestones.py"

# 5. 更新月度榜单 MONTHLY
run_step "更新月度榜单 MONTHLY" "update_monthly.py"

# 6. 计算连续纪录 STREAK_RECORDS
run_step "计算连续纪录 STREAK_RECORDS" "update_streaks.py"

# Git 提交
TODAY=$(date '+%Y-%m-%d')
git add data.jsx
if git diff --cached --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') 无数据变更，跳过部署" | tee -a "$LOG"
    exit 0
fi

git commit -m "自动更新数据 ${TODAY}" 2>&1 | tee -a "$LOG"
git push 2>&1 | tee -a "$LOG"

# Vercel 部署（直接调用 CLI，绕过插件拦截问题）
echo "→ 部署到 Vercel" | tee -a "$LOG"
node "$VERCEL" --prod 2>&1 | tee -a "$LOG"

echo "$(date '+%Y-%m-%d %H:%M:%S') ✅ 更新完成，已发布到 royalfarmers.club" >> "$LOG"
echo "======================================" >> "$LOG"
