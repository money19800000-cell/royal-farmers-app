# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static website for Royal Farmers FC (上海皇家农夫足球俱乐部), deployed to https://www.royalfarmers.club/ via Vercel. No build step — `vercel.json` sets `outputDirectory: "."` so all files are served directly.

Vercel project ID: `prj_G9Ip4BjpOQbuOXpWqFYFnZcIDxJU` (team: `team_kO5LCWygwTNJxFASe8lMFpHW`). Vercel is connected to GitHub (`money19800000-cell/royal-farmers-app`, branch `main`) — every push auto-deploys.

## Architecture

The site has three JS files loaded in order by `index.html`:

1. **`data.jsx`** — all stats as plain JS `const` declarations (no imports). The only file the Python scripts modify.
2. **`components.jsx`** — React components, reads from `window.RF_DATA` which is populated by a script tag in `index.html` that assigns all `data.jsx` consts to that object.
3. **`app.jsx`** — top-level page layout and routing.

CSS is split across `site.css`, `colors_and_type.css`, and `players.css`.

`datacenter.html` is a separate standalone page (full stats table).

## Data Pipeline

All match/player data lives in Numbers spreadsheets synced to iCloud, exported as CSV to:
```
/Users/macstudio/claude code/numbers数据来源/shanghai farmers united/
```

Key CSV files:
- `花名册-球队花名册.csv` — player roster with career + per-season stats (cols 6/7/8 = apps/goals/assists career total; cols 9+ = per-season in groups of 4)
- `每场战报+总数据-具体战况.csv` — match-by-match records. **Sorted newest-first.** Match header rows have `YYMMDD-N` in col[1]. Goal rows: col[4]=home scorer, col[5]=home assist, col[8]=away scorer, col[9]=away assist.
- `每场战报+总数据-总射手榜.csv` / `总助攻榜.csv` / `总出场数.csv` — all-time career leaderboards

Python scripts (in `scripts/`) update `data.jsx` in place by regex-replacing named blocks.  
**Run via `daily_update.sh` (23:00 LaunchAgent) or manually:**

```bash
bash scripts/daily_update.sh
```

| Step | Script | Updates in data.jsx |
|------|--------|-------------------|
| 0 | `export_numbers_csv.py` | Numbers → CSV（无需开 App） |
| 1 | `update_season_stats.py` | `GOALS26/ASSISTS26/APPS26`, `GOALS_ALL/ASSISTS_ALL/APPS_ALL`, `MATCH_COUNT`, `RATINGS_*`, `RECORDS.career` ✅, `RECORDS.season`, `RECORDS.club` ✅ |
| 2 | `update_fixtures.py` | `FIXTURES` array（2026赛季全量）|
| 3 | `check_milestones.py` | `MILESTONES` array（精确日期）|
| 4 | `update_monthly.py` | `MONTHLY_HISTORY/GOALS/ASSISTS/APPS/PERIOD`, `PLAYER_HONORS` |
| 5 | `update_streaks.py` | `PLAYER_STREAKS`, `STREAK_RECORDS`, `ALLSEASON_PLAYERS` |
| 6 | `update_players.py` | `PLAYERS`, `PLAYER_LOOKUP` |
| 7 | `qwen_daily_summary.py` | Qwen 日报（可选）|

**Key data constants (2026-06-05):**

| Constant | Count/Value |
|----------|------------|
| `PLAYERS` | 51人（有照片）|
| `PLAYER_LOOKUP` | 103人（无照片，出场≥5次或有球衣号）|
| `MATCH_COUNT` | 481 |
| `MONTHLY_HISTORY` | 64个月（2021-01→2026-06）|
| `MILESTONES` | 112条 |
| `ALLSEASON_PLAYERS` | 27人（六赛季全勤）|
| `RECORDS.career` 生涯最多进球 | 909（姜珂）|
| `RECORDS.career` 生涯最多助攻 | 1179（姜珂）|
| `RECORDS.club` 历史总场次 | 481 |

**SEASON_MATCHES（评分门槛用）：** `{'2021':68,'2022':79,'2023':97,'2024':104,'2025':94,'2026':39}`

## Running Scripts

On Mac (normal):
```bash
cd "/Users/macstudio/claude code/projects/royal-farmers-app"
bash scripts/weekly_update.sh
```

The scripts have hardcoded Mac paths (`/Users/macstudio/claude code/...`). `PROJECT_DIR` is derived from `__file__` so it resolves correctly when run from the Mac.

From Cowork/Claude sandbox (paths are different — use the wrapper):
```bash
GITHUB_TOKEN="..." bash scripts/cowork_sync.sh
```
`cowork_sync.sh` patches all hardcoded paths at runtime via `sed` before executing.

## Known Issues & Fixes Applied

### Milestone date calculation (`check_milestones.py`)

**Bug (fixed):** Milestone dates were estimated using linear time interpolation within a season (`approx_date()`), which was inaccurate. The 2026 end date was also hardcoded as `2026-05-23` instead of being dynamic.

**Fix applied:** Added `parse_player_match_stats()` which parses `具体战况.csv` match-by-match to find the exact game date when a milestone was crossed. `approx_date()` remains as fallback for older events.

**Critical:** `具体战况.csv` is sorted **newest-first**. Always sort ascending before accumulating career stats.

### 同号码球员照片冲突（2026-06-05 修复）

`PHOTO_MAP` 按球衣号查照片，同号时取错人。处理方式：在 `NAME_PHOTO_OVERRIDE` 添加覆盖项。

| 号码 | 默认（PHOTO_MAP）| 覆盖（NAME_PHOTO_OVERRIDE）|
|------|-----------------|--------------------------|
| 22 | 麦超 | 鲍梁剑 → `22号鲍梁剑.jpeg` |
| 6  | 陶骏 | 朱寿卿 → `56号朱寿卿.jpeg` |

### RECORDS.career / RECORDS.club 自动更新（2026-06-05 新增）

以前这两个块脚本不更新，需手动维护导致数值过期。现已在 `update_season_stats.py` 中添加：
- `update_records_career_precise()` — 从 `GOALS_ALL/ASSISTS_ALL` 第一条自动同步生涯进球/助攻/效率
- `update_records_club_total()` — 从 `match_count` 自动更新历史总场次和 ctx 月份

### 具体战况 CSV 两种格式（影响 `update_monthly.py`）

| 格式 | 时期 | 进球行判断 |
|------|------|----------|
| 旧格式 | 2021-2024年6月 + 2025年12月起 | r[1]='' |
| 新格式 | 2024年7月—2025年11月 | r[1] 有日期且 r[6]/r[7]='' |

新格式进球行必须加 `current_in_month` 检查，否则月度进球会异常累积跨月。

### Vercel deployment

Vercel is connected to GitHub (linked 2026-05-31). Push to `main` triggers auto-deploy.

### Python path constants

All scripts use hardcoded absolute Mac paths for CSV data dir. Do not change these — `cowork_sync.sh` handles path substitution for non-Mac environments. If you add a new script, follow the same pattern.

## Deployment

```bash
git add data.jsx
git commit -m "weekly sync YYYY-MM-DD"
git push  # Vercel auto-deploys via GitHub webhook
```

Only `data.jsx` is modified by the data pipeline. All other files are edited manually.
