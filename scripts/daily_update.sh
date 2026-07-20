#!/bin/bash
# Royal Farmers FC — 每日数据更新流水线
# 每天 23:00 由 LaunchAgent 自动执行
# 全流程：Numbers → CSV → data.jsx → git push → Vercel
#
# 手动运行：bash scripts/daily_update.sh

set -e

PYTHON="/opt/homebrew/bin/python3.11"
REPO="/Users/macstudio/Documents/CLAUDE CODE/projects/project-022-royal-farmers-app/src"
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
$PYTHON "$REPO/scripts/export_numbers_csv.py" 2>&1 | tee -a "$LOG" || log "   ⚠️  部分表导出失败，继续后续步骤"

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

# ── Step 6d: 联合阵容胜率 LINEUP_STATS ──
run_step "Step 6d: 联合阵容胜率" "compute_lineup_stats.py"

# ── Step 6e: 球员化学反应 PLAYER_CHEMISTRY ──
run_step "Step 6e: 球员化学反应" "compute_player_chemistry.py"

# ── Step 6f: 外部友谊赛（两队）战绩 EXTERNAL_MATCH_STATS ──
run_step "Step 6f: 外部友谊赛战绩" "compute_external_stats.py"

# ── Step 6g: 球员图片绑定（扫描 assets/players/ 自动补充 photo 字段）──
run_step "Step 6g: 球员图片绑定" "sync_player_photos.py"

# ── Step 6h-pre: 出勤率热力图 ATTENDANCE_HEATMAP ──
run_step "Step 6h-pre: 出勤率热力图" "compute_attendance_heatmap.py"

# ── Step 6h: IB 私募基金 LP 数据 ──
run_step "Step 6h: IB 私募基金数据" "gen_ib_fund_data.py"

# ── Step 7: 本地 Qwen 生成每日简报（可选，仅 oMLX 运行时生效）──
log ""
log "── Step 7: Qwen 日报（可选）──"
if curl -s http://localhost:8001/v1/models > /dev/null 2>&1; then
    $PYTHON "$REPO/scripts/qwen_daily_summary.py" 2>&1 | tee -a "$LOG"
else
    log "   oMLX 未运行，跳过 Qwen 日报"
fi

# ── Step 8: 前端预编译（esbuild，浏览器不再需要 Babel）──
log ""
log "── Step 8: 前端预编译 ──"
bash "$REPO/scripts/build.sh" 2>&1 | tee -a "$LOG"

# ── Git 提交 & 部署 ──
log ""
log "── Git 提交 & 部署 ──"
git add data.jsx assets/ ib-fund-data.js data.min.js components.min.js app.min.js index.html
if git diff --cached --quiet; then
    log "   无数据变更，跳过部署"
    log ""
    log "======================================"
    log "$(date '+%Y-%m-%d %H:%M:%S')  ✅ 无变更，结束"
    log "======================================"
    exit 0
fi

git commit -m "每日自动更新 $(date '+%Y-%m-%d')" 2>&1 | tee -a "$LOG"
git config --local http.version HTTP/1.1

# git push 最多重试 3 次（网络偶发 Empty reply 问题）
# ⚠️ 不能用 `git push | tee` 判断成败——管道退出码是 tee 的（恒为0），git 失败也会被判成功
PUSH_OK=0
for attempt in 1 2 3; do
    log "   git push（第 $attempt 次）..."
    if git push >>"$LOG" 2>&1; then
        PUSH_OK=1
        break
    fi
    [ $attempt -lt 3 ] && sleep 10
done

log ""
log "======================================"
if [ $PUSH_OK -eq 1 ]; then
    log "$(date '+%Y-%m-%d %H:%M:%S')  ✅ 更新完成 → royalfarmers.club"
else
    log "$(date '+%Y-%m-%d %H:%M:%S')  ⚠️  数据已更新但 git push 失败（3次重试均超时）"
fi
log "======================================"

exit $((1 - PUSH_OK))
