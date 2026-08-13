#!/bin/bash
# Royal Farmers FC — 每日数据更新流水线
# 每天 23:00 由 LaunchAgent 自动执行
# 全流程：Numbers → CSV → data.jsx → git push → Vercel
#
# 手动运行：bash scripts/daily_update.sh

set -e
set -o pipefail

PYTHON="/opt/homebrew/bin/python3.11"
REPO="/Users/macstudio/Documents/CLAUDE CODE/projects/project-022-royal-farmers-app/src"
LOG="/Users/macstudio/Library/Logs/royal-farmers-daily.log"
TODAY=$(date '+%Y-%m-%d %H:%M:%S')

log() { echo "$1" | tee -a "$LOG"; }

log "======================================"
log "$TODAY  ▶ 开始每日更新"
log "======================================"

cd "$REPO"

# 先同步远端代码，避免数据全部生成后才发现 main 已经前进。
# --ff-only 不会改写历史；若本地已有未推送提交，则留到部署阶段合并。
log ""
log "── Git 远端预检 ──"
if ! git fetch origin >>"$LOG" 2>&1; then
    log "   ❌ 无法获取远端更新，停止本次流水线（避免基于过期代码生成数据）"
    exit 1
fi
if git merge-base --is-ancestor HEAD origin/main; then
    git merge --ff-only origin/main >>"$LOG" 2>&1
    log "   ✅ 已同步至最新远端 main"
elif git merge-base --is-ancestor origin/main HEAD; then
    log "   ℹ️  本地含待推送提交，继续生成并在部署阶段推送"
else
    log "   ❌ 本地与远端 main 已分叉，需要先合并；停止以避免覆盖远端改动"
    exit 1
fi

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

# git push 最多重试 3 次（仅针对网络瞬时错误）。
# 推送前再次 fetch，明确区分“远端已前进”和网络故障，避免无意义重试。
PUSH_OK=0
PUSH_REASON="未知错误"
for attempt in 1 2 3; do
    log "   git push（第 $attempt 次）..."
    if ! git fetch origin >>"$LOG" 2>&1; then
        PUSH_REASON="无法获取远端状态（网络或 GitHub 认证异常）"
    elif ! git merge-base --is-ancestor origin/main HEAD; then
        PUSH_REASON="远端 main 在运行期间出现新提交，本地与远端已分叉"
        log "   ❌ $PUSH_REASON；停止重试，避免覆盖远端改动"
        break
    elif git push origin HEAD:main >>"$LOG" 2>&1; then
        PUSH_OK=1
        break
    else
        PUSH_REASON="网络或 GitHub 服务异常"
    fi
    [ $attempt -lt 3 ] && sleep 10
done

log ""
log "======================================"
if [ $PUSH_OK -eq 1 ]; then
    log "$(date '+%Y-%m-%d %H:%M:%S')  ✅ 更新完成 → royalfarmers.club"
else
    log "$(date '+%Y-%m-%d %H:%M:%S')  ⚠️  数据已更新但 git push 失败：$PUSH_REASON"
fi
log "======================================"

exit $((1 - PUSH_OK))
