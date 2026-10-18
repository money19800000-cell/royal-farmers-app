#!/bin/bash
# Royal Farmers FC — 每日数据更新流水线
# 每天 23:00 由 LaunchAgent 自动执行
# 全流程：Numbers → CSV → data.jsx → git push → Vercel
#
# 手动运行：bash scripts/daily_update.sh

set -eo pipefail

export PYTHON="${PYTHON:-/opt/homebrew/bin/python3.11}"
REPO="/Users/macstudio/Documents/Codex/codex-claude-code-projects/royal-farmers-fc/work/royal-farmers-app"
MINIPROGRAM_SYNC="/Users/macstudio/Documents/CLAUDE CODE/projects/project-033-royal-farmers-miniprogram/scripts/sync_data.py"
LOG="/Users/macstudio/Library/Logs/royal-farmers-daily.log"
WEBSITE_ONLY=0
LOCAL_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --website-only) WEBSITE_ONLY=1; export SKIP_DAILY_REPORT=1 ;;
        --local-only) LOCAL_ONLY=1; WEBSITE_ONLY=1; export SKIP_DAILY_REPORT=1 ;;
        *) echo "用法：bash scripts/daily_update.sh [--website-only|--local-only]"; exit 2 ;;
    esac
done
TODAY=$(date '+%Y-%m-%d %H:%M:%S')

log() { echo "$1" | tee -a "$LOG"; }

sync_miniprogram_after_publish() {
    local expectedVersion remoteIndex attempt
    expectedVersion=$(sed -nE 's/.*data\.min\.js\?v=([0-9]+).*/\1/p' "$REPO/index.html" | head -1)
    if [ -z "$expectedVersion" ]; then
        log "   ⚠️ 无法读取网站数据版本，跳过小程序同步"
        return 1
    fi

    log "   等待网站 data.min.js?v=${expectedVersion} 发布…"
    for attempt in $(seq 1 12); do
        remoteIndex=$(curl -fsSL --connect-timeout 10 --max-time 20 "https://www.royalfarmers.club/index.html?sync=${expectedVersion}" 2>/dev/null || true)
        if printf '%s' "$remoteIndex" | grep -Fq "data.min.js?v=${expectedVersion}"; then
            log "   网站已发布，开始同步微信小程序云数据"
            if RF_WEBSITE_DATA="$REPO/data.jsx" "$PYTHON" "$MINIPROGRAM_SYNC" >>"$LOG" 2>&1; then
                log "   ✅ 微信小程序云数据已同步至网站版本 ${expectedVersion}"
                return 0
            fi
            log "   ⚠️ 微信小程序云数据上传失败"
            return 1
        fi
        [ "$attempt" -lt 12 ] && sleep 10
    done
    log "   ⚠️ 网站发布等待超时，未同步微信小程序，避免发布旧版本数据"
    return 1
}

log "======================================"
log "$TODAY  ▶ 开始每日更新"
log "======================================"

cd "$REPO"
LOCK_DIR="$REPO/.sync-lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    log "❌ 已有同步任务或遗留锁：$LOCK_DIR；请检查 pid 文件，不要并行执行"
    exit 1
fi
echo $$ > "$LOCK_DIR/pid"
DEPLOY_DIR=""
cleanup_sync() {
    local result=$?
    if [ -n "$DEPLOY_DIR" ]; then
        git -C "$REPO" worktree remove --force "$DEPLOY_DIR" >/dev/null 2>&1 || true
    fi
    rm -f "$LOCK_DIR/pid"
    rmdir "$LOCK_DIR" 2>/dev/null || true
    if [ "$result" -ne 0 ]; then log "❌ 同步失败（退出码 $result），见上方原因；未确认网站发布成功"; fi
}
trap cleanup_sync EXIT

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

# ── Step 1b: 逐场出勤明细（Ranking Race 曲线）──
run_step "Step 1b: 逐场出勤明细" "update_roster_log.py"

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
run_step "加盟后出勤率" "compute_join_attendance.py"

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

# ── Step 9: 生成日报长图并推送（邮箱 / 飞书 / 企业微信，按环境变量启用）──
log ""
log "── Step 9: 生成并推送球队日报 ──"
if [ "${SKIP_DAILY_REPORT:-0}" = "1" ]; then
    log "   全局网站同步模式：日报由独立任务发送，本次跳过"
else
    if [ -f "$REPO/scripts/daily-report.env" ]; then
        set -a
        source "$REPO/scripts/daily-report.env"
        set +a
    fi
    $PYTHON "$REPO/scripts/generate_daily_report.py" 2>&1 | tee -a "$LOG" || log "   ⚠️  日报生成或推送失败，不阻断网站更新"
fi

if [ "$LOCAL_ONLY" = "1" ]; then
    log "✅ 本地同步、重算和测试完成；未发布网站"
    exit 0
fi

# ── Git 提交 & 部署 ──
log ""
log "── Git 提交 & 部署 ──"
# 本仓库同时用于日常开发，main 可能长期分叉并带有未提交文件。直接在这里
# commit/rebase 会反复冲突。发布时从最新 origin/main 创建一次性干净 worktree，
# 只覆盖生成物；重试时再次基于最新远端重建提交，避免历史分叉累积。
DEPLOY_DIR=$(mktemp -d /tmp/royal-farmers-deploy.XXXXXX)

if ! git fetch origin main >>"$LOG" 2>&1 || \
   ! git worktree add --detach "$DEPLOY_DIR" origin/main >>"$LOG" 2>&1; then
    log "   ❌ 无法创建干净发布目录"
    exit 1
fi

copy_deploy_artifacts() {
    "$PYTHON" "$REPO/scripts/release_manifest.py" --copy "$DEPLOY_DIR"
    # 日报图片保留在本地，不随网站部署；其他静态资源增量覆盖。
    rsync -a --exclude 'report/' "$REPO/assets/" "$DEPLOY_DIR/assets/"
}

# ⚠️ 不使用 `git push | tee` 判断成败，避免 tee 掩盖 git 的退出码。
PUSH_OK=0
MINIAPP_SYNC_OK=1
for attempt in 1 2 3; do
    if [ $attempt -gt 1 ]; then
        if ! git fetch origin main >>"$LOG" 2>&1; then
            log "   ⚠️  获取远端 main 失败，稍后重试"
            sleep 10
            continue
        fi
        # 只重置一次性发布目录，绝不触碰开发工作区及其中的未提交文件。
        git -C "$DEPLOY_DIR" reset --hard origin/main >>"$LOG" 2>&1
    fi

    copy_deploy_artifacts
    git -C "$DEPLOY_DIR" add --all

    if git -C "$DEPLOY_DIR" diff --cached --quiet; then
        log "   远端已包含最新数据，无需重复提交"
        PUSH_OK=1
        break
    fi

    git -C "$DEPLOY_DIR" commit -m "每日自动更新 $(date '+%Y-%m-%d')" >>"$LOG" 2>&1
    git -C "$DEPLOY_DIR" config http.version HTTP/1.1
    log "   git push（第 $attempt 次）..."
    if git -C "$DEPLOY_DIR" push origin HEAD:main >>"$LOG" 2>&1; then
        PUSH_OK=1
        break
    fi
    log "   ⚠️  推送失败；将基于最新远端重建发布提交"
    [ $attempt -lt 3 ] && sleep 10
done

log ""
log "======================================"
if [ $PUSH_OK -eq 1 ]; then
    log "$(date '+%Y-%m-%d %H:%M:%S')  ✅ Git 推送完成，正在核验网站发布"
    log ""
    VERIFIED=0
    for attempt in $(seq 1 12); do
        if "$PYTHON" "$REPO/scripts/release_manifest.py" --verify-url https://www.royalfarmers.club >>"$LOG" 2>&1; then
            VERIFIED=1
            break
        fi
        [ "$attempt" -lt 12 ] && sleep 10
    done
    if [ "$VERIFIED" != "1" ]; then
        log "❌ 推送成功但线上版本验证失败；停止后续同步"
        exit 1
    fi
    log "✅ 网站版本、里程碑规则与数据文件已核验一致"
    if [ "$WEBSITE_ONLY" != "1" ]; then
        log "── 微信小程序数据同步（网站发布后）──"
        sync_miniprogram_after_publish || MINIAPP_SYNC_OK=0
    fi
else
    log "$(date '+%Y-%m-%d %H:%M:%S')  ⚠️  数据已更新但 git push 失败（已基于最新远端重试 3 次）"
fi
log "======================================"

exit $((1 - PUSH_OK + 1 - MINIAPP_SYNC_OK))
