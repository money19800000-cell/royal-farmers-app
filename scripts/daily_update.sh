#!/bin/bash
# Royal Farmers FC — 每日数据更新流水线
# 每天 23:00 由 LaunchAgent 自动执行
# 全流程：Numbers → CSV → data.jsx → git push → Vercel
#
# 手动运行：bash scripts/daily_update.sh

set -e

PYTHON="/opt/homebrew/bin/python3.11"
REPO="/Users/macstudio/claude code/projects/royal-farmers-app"
LOG="/Users/macstudio/Library/Logs/royal-farmers-daily.log"
TODAY=$(date '+%Y-%m-%d %H:%M:%S')

log() { echo "$1" | tee -a "$LOG"; }

log "======================================"
log "$TODAY  ▶ 开始每日更新"
log "======================================"

cd "$REPO"

run_step() {
    local label="$1"
    local script="$2"
    log ""
    log "── $label ──"
    $PYTHON "$REPO/scripts/$script" 2>&1 | tee -a "$LOG"
}

# ── Step 0: Numbers → CSV（直读 iCloud，无需打开 Numbers App）──
log ""
log "── Step 0: Numbers → CSV ──"
$PYTHON "$REPO/scripts/export_numbers_csv.py" 2>&1 | tee -a "$LOG"

# ── Step 1: 赛季榜单 + 评分榜 ──
run_step "Step 1: 赛季榜单 + 评分榜" "update_season_stats.py"

# ── Step 2: 赛程 FIXTURES ──
run_step "Step 2: 赛程 FIXTURES"      "update_fixtures.py"

# ── Step 3: 里程碑 MILESTONES ──
run_step "Step 3: 里程碑 MILESTONES"  "check_milestones.py"

# ── Step 4: 月度榜单 MONTHLY ──
run_step "Step 4: 月度榜单 MONTHLY"   "update_monthly.py"

# ── Step 5: 连续纪录 + 全勤元老 ──
run_step "Step 5: 连续纪录 + 全勤元老" "update_streaks.py"

# ── Step 6: PLAYERS 数组 ──
run_step "Step 6: PLAYERS 数组"        "update_players.py"

# ── Step 6b: 黄金搭档 GOLDEN_PAIRS ──
run_step "Step 6b: 黄金搭档 GOLDEN_PAIRS" "compute_golden_pairs.py"

# ── Step 6c: 各赛季对战战绩 SEASON_MATCH_STATS ──
run_step "Step 6c: 赛季战绩统计" "compute_season_match_stats.py"

# ── Step 7: 本地 Qwen 生成每日简报（可选，仅 oMLX 运行时生效）──
log ""
log "── Step 7: Qwen 日报（可选）──"
if curl -s http://localhost:8001/v1/models > /dev/null 2>&1; then
    $PYTHON "$REPO/scripts/qwen_daily_summary.py" 2>&1 | tee -a "$LOG"
else
    log "   oMLX 未运行，跳过 Qwen 日报"
fi

# ── Git 提交 & 部署 ──
log ""
log "── Git 提交 & 部署 ──"
git add data.jsx
if git diff --cached --quiet; then
    log "   无数据变更，跳过部署"
    log ""
    log "======================================"
    log "$(date '+%Y-%m-%d %H:%M:%S')  ✅ 无变更，结束"
    log "======================================"
    exit 0
fi

git commit -m "每日自动更新 $(date '+%Y-%m-%d')" 2>&1 | tee -a "$LOG"
git push 2>&1 | tee -a "$LOG"

log ""
log "======================================"
log "$(date '+%Y-%m-%d %H:%M:%S')  ✅ 更新完成 → royalfarmers.club"
log "======================================"
