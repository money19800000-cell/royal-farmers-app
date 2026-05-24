#!/bin/bash
# Royal Farmers FC — 每周自动数据更新脚本
# 每周三 9:00 由 LaunchAgent 自动触发
# 手动运行：bash scripts/weekly_update.sh

set -e  # 任意步骤失败则退出

PYTHON="/opt/homebrew/bin/python3.11"
REPO="/Users/macstudio/claude code/projects/royal-farmers-app"
LOG="/Users/macstudio/Library/Logs/royal-farmers-weekly.log"

echo "======================================" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') 开始自动更新" >> "$LOG"

cd "$REPO"

run_step() {
    echo "→ $1" | tee -a "$LOG"
    $PYTHON "$REPO/scripts/$2" 2>&1 | tee -a "$LOG"
}

run_step "更新赛季榜单（GOALS26/ASSISTS26/APPS26/ALL）" "update_season_stats.py"
run_step "更新赛程 FIXTURES" "update_fixtures.py"
run_step "检测并更新里程碑 MILESTONES" "check_milestones.py"
run_step "更新月度榜单 MONTHLY" "update_monthly.py"

# Git 提交并推送（触发 Vercel 自动部署）
TODAY=$(date '+%Y-%m-%d')
git add data.jsx
git diff --cached --quiet && echo "$(date) 无变更，跳过提交" | tee -a "$LOG" && exit 0

git commit -m "自动更新数据 ${TODAY}" 2>&1 | tee -a "$LOG"
git push 2>&1 | tee -a "$LOG"

echo "$(date '+%Y-%m-%d %H:%M:%S') ✅ 更新完成，已推送到 Vercel" >> "$LOG"
echo "======================================" >> "$LOG"
