#!/usr/bin/env python3
"""生成皇家农民工 FC 日报长图，并按环境变量推送到邮箱/飞书/企业微信。"""

from __future__ import annotations

import argparse
import datetime as dt
import email.message
import html
import json
import os
import pathlib
import re
import smtplib
import subprocess
import sys
import urllib.request
import tempfile

import requests

from football_editorial import build_editorial


PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_DIR / "reports"
REPORT_STATE_FILE = REPORT_DIR / ".daily-report-state.json"
DATA_FILE = PROJECT_DIR / "data.jsx"
CHROME_PATH = pathlib.Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PUBLIC_REPORT_URL = os.getenv("REPORT_PUBLIC_URL", "")
PUBLIC_INDEX_URL = os.getenv("REPORT_DATA_URL", "https://www.royalfarmers.club/index.html")
FEISHU_CONFIG_FILE = pathlib.Path(os.getenv("FEISHU_CONFIG_FILE", "/Users/macstudio/.claude/www/scripts/email_report_config.json"))
DEFAULT_IMAGE_PYTHON = pathlib.Path(
    "/Users/macstudio/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)


def load_data() -> dict:
    """优先读取网站当前发布的数据，网络失败时回退本地源码。"""
    source_path = DATA_FILE
    temporary_path: pathlib.Path | None = None
    try:
        index_request = urllib.request.Request(PUBLIC_INDEX_URL, headers={"User-Agent": "Mozilla/5.0 RoyalFarmersReport/1.0"})
        with urllib.request.urlopen(index_request, timeout=20) as response:
            index_markup = response.read().decode("utf-8")
        match = re.search(r'<script src="(data\.min\.js[^\"]*)"', index_markup)
        if not match:
            raise RuntimeError("线上页面没有找到 data.min.js")
        data_url = urllib.request.urljoin(PUBLIC_INDEX_URL, match.group(1))
        data_request = urllib.request.Request(data_url, headers={"User-Agent": "Mozilla/5.0 RoyalFarmersReport/1.0"})
        with urllib.request.urlopen(data_request, timeout=30) as response:
            source = response.read()
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as file:
            file.write(source)
            temporary_path = pathlib.Path(file.name)
            source_path = temporary_path
        print(f"数据源：线上网站 {data_url}")
    except Exception as error:
        print(f"线上数据读取失败，回退本地 data.jsx：{error}")
    script = (
        "const fs=require('fs');global.window={};"
        "eval(fs.readFileSync(process.argv[1],'utf8'));"
        "process.stdout.write(JSON.stringify(window.RF_DATA));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(source_path)], check=True, capture_output=True, text=True
    )
    if temporary_path:
        temporary_path.unlink(missing_ok=True)
    return json.loads(result.stdout)


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def leaderboard(title: str, rows: list[dict], field: str, unit: str, photos: dict[str, str]) -> str:
    items = []
    for index, row in enumerate(rows[:5], 1):
        number = f'<span class="shirt">{escape(row.get("num") or "—")}</span>'
        photo = photos.get(row["name"], "")
        portrait = f'<img class="portrait" src="../{escape(photo)}">' if photo else '<span class="portrait fallback">RF</span>'
        items.append(
            f'<li><b>{index:02d}</b>{portrait}{number}<span class="player">{escape(row["name"])}</span>'
            f'<strong>{escape(row[field])}<small>{unit}</small></strong></li>'
        )
    return f'<section class="ranking"><h3>{title}</h3><ol>{"".join(items)}</ol></section>'


def milestone_section(milestones: list[dict], report_date: dt.date, photos: dict[str, str]) -> str:
    report_day = report_date.isoformat()
    eligible = [item for item in milestones if item.get("date") and item["date"] <= report_day]
    today_items = [item for item in eligible if item.get("date") == report_day]
    selected = today_items if today_items else sorted(eligible, key=lambda item: item.get("date", ""), reverse=True)[:3]
    heading = "今日新里程碑" if today_items else "近期里程碑回顾"
    cards = []
    for item in selected:
        photo = item.get("photo") or photos.get(item.get("name", ""), "")
        portrait = f'<img src="../{escape(photo)}">' if photo else '<span class="milestone-fallback">RF</span>'
        cards.append(
            f'<article class="milestone-card">{portrait}<div><time>{escape(item.get("date", "—"))}</time>'
            f'<b>{escape(item.get("label", "里程碑"))}</b></div></article>'
        )
    empty = '<p class="milestone-empty">尚无里程碑记录</p>' if not cards else ""
    return f'<section class="milestones"><div class="milestone-head"><h3>{heading}</h3><span>MILESTONE / 荣耀时刻</span></div><div class="milestone-grid">{"".join(cards)}{empty}</div></section>'


def fixture_key(fixture: dict) -> str:
    """Create a stable identifier without mutating the published match data."""
    fields = ("date", "home", "homeScore", "awayScore", "away", "comp")
    return "|".join(str(fixture.get(field, "")) for field in fields)


def load_report_state() -> dict:
    try:
        return json.loads(REPORT_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_report_state(latest: dict) -> None:
    REPORT_STATE_FILE.write_text(
        json.dumps({"latestFixtureKey": fixture_key(latest)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_new_fixture(latest: dict, state: dict) -> bool:
    return bool(latest) and fixture_key(latest) != state.get("latestFixtureKey")


def match_commentary(latest: dict) -> str:
    """Write a factual match note from the score and recorded scorer/assist entries."""
    if not latest:
        return "尚未录入可点评的比赛。"
    home_goals = len([name for name in latest.get("homeScorers", []) if name])
    away_goals = len([name for name in latest.get("awayScorers", []) if name])
    home_assists = len([name for name in latest.get("homeAssists", []) if name])
    away_assists = len([name for name in latest.get("awayAssists", []) if name])
    total_goals = home_goals + away_goals
    total_assists = home_assists + away_assists
    score_gap = abs(int(latest.get("homeScore", 0)) - int(latest.get("awayScore", 0)))
    result_note = "胜负只在一球之间，比赛始终保持悬念。" if score_gap == 1 else (
        "双方战成平局，攻守转换决定了比赛节奏。" if score_gap == 0 else "比分差距拉开，进攻端效率成为分水岭。"
    )
    assist_note = "多点传射串联明显。" if total_assists >= max(2, total_goals * 0.6) else "不少进球依靠个人终结，最后一传仍有提升空间。"
    return f"本场记录 {total_goals} 名次进球、{total_assists} 次助攻；{result_note}{assist_note}"


def feature_section(data: dict, feature_index: int, photos: dict[str, str], report_date: dt.date) -> tuple[str, str, str]:
    """Rotate homepage leaderboard subjects on non-match days."""
    record_groups = data.get("RECORDS", {})
    records = [record for group in record_groups.values() for record in group] if isinstance(record_groups, dict) else []
    golden_pairs = data.get("GOLDEN_PAIRS", {}).get("all", [])
    features = [
        ("队史总进球榜", leaderboard("队史总进球榜", data.get("GOALS_ALL", []), "goals", "球", photos), "从生涯火力榜回看长期输出。"),
        ("队史总助攻榜", leaderboard("队史总助攻榜", data.get("ASSISTS_ALL", []), "assists", "助", photos), "助攻榜记录每一次为队友创造机会。"),
        ("队史总出勤榜", leaderboard("队史总出勤榜", data.get("APPS_ALL", []), "apps", "场", photos), "稳定到场，是球队最可靠的底色。"),
        ("黄金搭档", golden_pair_section(golden_pairs), "进球与助攻之间，沉淀出最默契的连接。"),
        ("最佳组合", lineup_section(data.get("LINEUP_STATS", [])), "共同出场的胜率，记录搭档之间的化学反应。"),
        ("队史纪录", records_section(records), "纪录页收藏球队跨赛季的高光刻度。"),
        ("里程碑", milestone_section(data.get("MILESTONES", []), report_date, photos), "每一项里程碑，都是球队共同积累的章节。"),
    ]
    return features[feature_index % len(features)]


def golden_pair_section(pairs: list[dict]) -> str:
    items = "".join(
        f'<div class="feature-row"><b>{index:02d}</b><span>{escape(pair.get("scorer", "—"))} × {escape(pair.get("ast", "—"))}</span><strong>{escape(pair.get("count", 0))}<small>次连线</small></strong></div>'
        for index, pair in enumerate(pairs[:5], 1)
    ) or '<p class="milestone-empty">暂无黄金搭档数据</p>'
    return f'<section class="feature"><h3>黄金搭档</h3><div class="feature-list">{items}</div></section>'


def lineup_section(lineups: list[dict]) -> str:
    items = "".join(
        f'<div class="feature-row"><b>{index:02d}</b><span>{escape(pair.get("p1", "—"))} × {escape(pair.get("p2", "—"))}<small>共同出场 {escape(pair.get("apps", 0))} 场</small></span><strong>{float(pair.get("rate", 0)):.1%}<small>胜率</small></strong></div>'
        for index, pair in enumerate(lineups[:5], 1)
    ) or '<p class="milestone-empty">暂无最佳组合数据</p>'
    return f'<section class="feature"><h3>最佳组合</h3><div class="feature-list">{items}</div></section>'


def records_section(records: list[dict]) -> str:
    rows = []
    for record in records[:5]:
        holder = str(record.get("holder") or "").strip()
        number = str(record.get("num") or "").strip()
        holder_label = f'{number}号 {holder}' if number and holder else holder
        record_label = escape(record.get("label", "队史纪录"))
        # 部分俱乐部纪录没有个人保持者；只有存在 holder 时才添加姓名。
        title = f'<em class="record-holder">{escape(holder_label)}</em> · {record_label}' if holder_label else record_label
        rows.append(
            f'<div class="feature-row"><b>{escape(record.get("icon", "★"))}</b>'
            f'<span>{title}<small>{escape(record.get("ctx", ""))}</small></span>'
            f'<strong>{escape(record.get("value", "—"))}<small>{escape(record.get("unit", ""))}</small></strong></div>'
        )
    items = "".join(rows) or '<p class="milestone-empty">暂无队史纪录数据</p>'
    return f'<section class="feature"><h3>队史纪录</h3><div class="feature-list">{items}</div></section>'


def render_html(data: dict, report_date: dt.date, new_match: bool, editorial: dict[str, str]) -> str:
    monthly_goals = data.get("MONTHLY_GOALS", [])
    monthly_assists = data.get("MONTHLY_ASSISTS", [])
    monthly_apps = data.get("MONTHLY_APPS", [])
    fixtures = data.get("FIXTURES", [])
    latest = fixtures[0] if fixtures else {}
    season_goals = data.get("GOALS26", [])
    season_assists = data.get("ASSISTS26", [])
    record = data.get("EXTERNAL_MATCH_STATS", {}).get("seasons", [])
    current_record = record[-1].get("record", {}) if record else {}
    lookup_players = data.get("PLAYER_LOOKUP", {})
    lookup_values = lookup_players.values() if isinstance(lookup_players, dict) else lookup_players
    photos = {
        player.get("name", ""): player.get("photo", "")
        for player in [*data.get("PLAYERS", []), *lookup_values]
        if isinstance(player, dict) and player.get("photo")
    }
    issue = (report_date - dt.date(report_date.year, 1, 1)).days + 1
    weekday = "一二三四五六日"[report_date.weekday()]
    date_label = f"{report_date.year}年{report_date.month}月{report_date.day}日周{weekday}"
    latest_title = "本月领跑者尚待揭晓"
    latest_subtitle = "新月份的第一次破门，会写下新的头条。"
    if monthly_goals:
        leader = monthly_goals[0]
        latest_title = f'{leader["name"]}领跑{report_date.month}月射手榜'
        latest_subtitle = f'{leader.get("num") or "—"}号球员已攻入 {leader["goals"]} 球 · 月度竞争持续升温'

    recent_result = "暂无最新赛果"
    if latest:
        recent_result = (
            f'{latest.get("home", "")} {latest.get("homeScore", "–")} : '
            f'{latest.get("awayScore", "–")} {latest.get("away", "")}'
        )

    if new_match:
        headline_title = f'新赛果：{recent_result}'
        headline_subtitle = "月度射手、助攻、出勤三榜已随本场数据同步更新"
        main_content = (
            f'<section class="match-review"><h3>本场点评 · MATCH REVIEW</h3><p>{escape(match_commentary(latest))}</p></section>'
            f'<div class="rankings">{leaderboard("当月射手榜", monthly_goals, "goals", "球", photos)}'
            f'{leaderboard("当月助攻榜", monthly_assists, "assists", "助", photos)}'
            f'{leaderboard("当月出勤榜", monthly_apps, "apps", "场", photos)}</div>'
        )
        lead_story = "新比赛数据已进入日报。本期先复盘比分、进球与助攻记录，再同步更新月度三项核心榜单。"
        brief_title = f'{data.get("MONTHLY_PERIOD", "本月")}三榜更新'
        brief_text = "新赛果触发月度榜单与赛后点评，不遗漏每一次数据变化。"
    else:
        feature_title, main_content, feature_summary = feature_section(data, issue - 1, photos, report_date)
        headline_title = f'今日焦点：{feature_title}'
        headline_subtitle = "首页榜单每日轮换，换一个角度读懂皇家农民工 FC"
        lead_story = feature_summary
        brief_title = f'轮换专题 · {feature_title}'
        brief_text = "无新增比赛时，日报轮换展示首页的不同榜单与荣誉板块。"

    # 版面由稳定的结构化数据驱动，标题与导语则交给“编辑台”按当日稿型组织。
    headline_title = editorial["headline"]
    headline_subtitle = editorial["deck"]
    lead_story = editorial["story"]
    brief_title = f'{editorial["templateName"]} · 编辑台'
    brief_text = editorial["watch"]
    story_drop = lead_story[:1]
    story_rest = lead_story[1:]

    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>皇家农民工FC日报 · {report_date.isoformat()}</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;background:#d2c8b3;color:#1b1813}}
body{{font-family:"Songti SC","STSong","Noto Serif CJK SC",serif}}
.paper{{width:1080px;min-height:1680px;margin:0 auto;padding:66px 72px 48px;background:#e9ddc1;
background-image:radial-gradient(#2e1f100f .8px,transparent .9px),linear-gradient(90deg,#6f4c2110,transparent 18%,#fff2 52%,transparent 83%,#6f4c2112);background-size:5px 5px,100% 100%;text-shadow:.25px .15px #3a291c55}}
.mast{{display:grid;grid-template-columns:136px 1fr 260px;gap:24px;align-items:center;border-bottom:4px solid #222;padding-bottom:26px}}
.disc{{width:124px;height:124px;border-radius:50%;background:#166b9e;display:grid;place-items:center}}
.disc img{{width:92px;height:92px;border-radius:50%;object-fit:cover;filter:saturate(.7)}}
.brand h1{{font-family:"STSong","Songti SC",serif;font-size:60px;line-height:.95;margin:0 0 13px;font-weight:900;letter-spacing:3px}}
.date{{font:900 31px/1.25 "Songti SC","STSong",serif;color:#276f94;letter-spacing:1px;white-space:nowrap}}.issue{{font:800 17px/1.4 Arial;letter-spacing:1px}}
.brief{{border-left:2px solid #222;padding-left:22px}}.brief b{{font-size:23px;line-height:1.15;display:block}}
.brief p{{font-size:15px;line-height:1.5;margin:10px 0 0}}.kicker{{font:700 13px Arial;letter-spacing:2px}}
.headline{{text-align:center;padding:32px 0 25px;border-bottom:3px solid #222}}
.headline h2{{font-family:"STSong","Songti SC",serif;font-size:53px;line-height:1.08;margin:0 0 10px;font-weight:900;letter-spacing:1px}}.headline p{{font-size:25px;margin:0;letter-spacing:2px}}
.lead{{display:grid;grid-template-columns:310px 1fr;gap:28px;padding:26px 0;border-bottom:3px solid #222}}
.story{{font-size:20px;line-height:1.8;text-align:justify}}.story .drop{{font-size:58px;float:left;line-height:.85;margin:8px 8px 0 0}}
.scorebox{{border:2px solid #222;padding:22px;text-align:center;background:#e9e4d9}}
.scorebox .label{{font:700 14px Arial;letter-spacing:2px}}.scorebox .score{{font-size:28px;font-weight:900;line-height:1.25;margin:18px 0}}
.scorebox .meta{{font-size:15px}}.rankings{{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-bottom:3px solid #222}}
.ranking{{padding:24px 20px 20px;border-right:1px solid #555}}.ranking:first-child{{padding-left:0}}.ranking:last-child{{border:0;padding-right:0}}
.ranking h3{{font-size:26px;margin:0 0 14px;border-bottom:2px solid #222;padding-bottom:9px}}ol{{list-style:none;margin:0;padding:0}}
.ranking li{{display:grid;grid-template-columns:18px 52px 28px 1fr auto;align-items:center;gap:6px;border-bottom:1px solid #aaa;padding:7px 0;font-family:"PingFang SC",sans-serif;font-size:14px}}
.portrait{{width:50px;height:50px;border-radius:8px;object-fit:cover;object-position:center 18%;image-rendering:auto}}.portrait.fallback{{display:grid;place-items:center;background:#d7d0c2;color:#555;font:700 11px Arial}}
.ranking li>b{{font:700 12px Arial;color:#777}}.shirt{{font:700 11px Arial;background:#222;color:#fff;text-align:center;padding:5px 2px}}
.ranking strong{{font:800 24px Arial}}.ranking small{{font:500 11px "PingFang SC";margin-left:3px}}
.feature,.match-review{{padding:22px 0;border-bottom:3px solid #222}}.feature h3,.match-review h3{{font-size:28px;margin:0 0 12px}}.feature-list{{display:grid;grid-template-columns:repeat(2,1fr);gap:0 24px}}.feature-row{{display:grid;grid-template-columns:38px 1fr auto;gap:10px;align-items:center;border-top:1px solid #999;padding:11px 0;font:17px "PingFang SC",sans-serif}}.feature-row>b{{font:800 15px Arial;color:#287baa}}.feature-row span small{{display:block;font-size:11px;color:#666;margin-top:3px}}.feature-row .record-holder{{font-style:normal;font-weight:800;color:#1f6f98}}.feature-row strong{{font:800 23px Arial;white-space:nowrap}}.feature-row strong small{{font:500 11px "PingFang SC";margin-left:3px}}.match-review{{background:#e3d6ba;padding:18px 20px;margin-top:0}}.match-review p{{font-size:20px;line-height:1.65;margin:0}}
.milestones{{padding:18px 0 19px;border-bottom:3px solid #222}}.milestone-head{{display:flex;align-items:end;justify-content:space-between;margin-bottom:13px}}.milestone-head h3{{font-size:27px;margin:0}}.milestone-head span{{font:700 12px Arial;letter-spacing:1.5px;color:#287baa}}
.milestone-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.milestone-card{{display:grid;grid-template-columns:54px 1fr;gap:11px;align-items:center;border:1px solid #777;padding:9px;background:#e9e4d9;min-height:72px}}.milestone-card img,.milestone-fallback{{width:52px;height:52px;border-radius:7px;object-fit:cover;object-position:center 18%}}.milestone-fallback{{display:grid;place-items:center;background:#d1cabd;font:700 11px Arial;color:#555}}.milestone-card time{{display:block;font:700 11px Arial;color:#287baa;margin-bottom:5px}}.milestone-card b{{display:block;font:700 15px/1.35 "PingFang SC",sans-serif}}.milestone-empty{{margin:0;font-size:15px}}
.bottom{{display:grid;grid-template-columns:1.2fr 1fr;gap:0;padding-top:22px}}.bottom section{{padding:0 28px 0 0}}
.bottom section+section{{border-left:1px solid #555;padding:0 0 0 28px}}.bottom h3{{font-size:27px;margin:0 0 10px}}
.statline{{display:flex;justify-content:space-between;border-top:1px solid #999;padding:8px 0;font:16px "PingFang SC"}}
.statline strong{{font:800 22px Arial}}footer{{margin-top:28px;border-top:2px solid #222;padding-top:13px;display:flex;justify-content:space-between;font:700 13px Arial;letter-spacing:1px}}
</style></head><body><main class="paper">
<header class="mast"><div class="disc"><img src="../assets/crest.jpg"></div><div class="brand"><h1>皇家农民工日报</h1><div class="date">{date_label}</div><div class="issue">第 {issue:03d} 期 · ROYAL FARMERS DAILY</div></div>
<aside class="brief"><span class="kicker">今日速览</span><b>{escape(brief_title)}</b><p>{escape(brief_text)}</p></aside></header>
<section class="headline"><h2>{escape(headline_title)}</h2><p>{escape(headline_subtitle)}</p></section>
<section class="lead"><article class="story"><span class="drop">{escape(story_drop)}</span>{escape(story_rest)}</article>
<div class="scorebox"><div class="label">最近赛果 · LATEST RESULT</div><div class="score">{escape(recent_result)}</div><div class="meta">{escape(latest.get("date", "—"))}　{escape(latest.get("venue", ""))}</div></div></section>
{main_content}
<div class="bottom"><section><h3>赛季火力速览</h3>
<div class="statline"><span>赛季射手王</span><strong>{escape(season_goals[0]["name"] if season_goals else "—")} · {escape(season_goals[0]["goals"] if season_goals else 0)} 球</strong></div>
<div class="statline"><span>赛季助攻王</span><strong>{escape(season_assists[0]["name"] if season_assists else "—")} · {escape(season_assists[0]["assists"] if season_assists else 0)} 助</strong></div>
<div class="statline"><span>俱乐部历史比赛</span><strong>{escape(data.get("MATCH_COUNT", 0))} 场</strong></div></section>
<section><h3>对外战绩</h3><div class="statline"><span>比赛</span><strong>{escape(current_record.get("played", 0))}</strong></div>
<div class="statline"><span>胜 / 平 / 负</span><strong>{escape(current_record.get("won", 0))} / {escape(current_record.get("drawn", 0))} / {escape(current_record.get("lost", 0))}</strong></div>
<div class="statline"><span>进球 / 失球</span><strong>{escape(current_record.get("gf", 0))} / {escape(current_record.get("ga", 0))}</strong></div></section></div>
<footer><span>ROYAL FARMERS FOOTBALL CLUB · SHANGHAI</span><span>数据源：球队比赛记录 / royalfarmers.club</span></footer>
</main></body></html>'''


def render_png(html_path: pathlib.Path, png_path: pathlib.Path) -> None:
    if not CHROME_PATH.exists():
        raise RuntimeError(f"找不到 Chrome：{CHROME_PATH}")
    subprocess.run(
        [str(CHROME_PATH), "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=2", "--window-size=1080,1680",
         f"--screenshot={png_path}", html_path.as_uri()],
        check=True, capture_output=True, text=True,
    )


def post_json(url: str, payload: dict) -> None:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status >= 300:
            raise RuntimeError(f"推送失败：HTTP {response.status}")
        body = json.loads(response.read() or b"{}")
        code = body.get("code", body.get("StatusCode", 0))
        if code not in (0, "0", None):
            raise RuntimeError(f"推送失败：{body}")


def keychain_value(reference: str) -> str:
    if not reference.startswith("keychain:"):
        return reference
    result = subprocess.run(
        ["security", "find-generic-password", "-s", reference.removeprefix("keychain:"), "-w"],
        check=True, capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip()


def load_feishu_config() -> dict:
    if not FEISHU_CONFIG_FILE.exists():
        return {}
    return json.loads(FEISHU_CONFIG_FILE.read_text(encoding="utf-8")).get("feishu", {})


def upload_feishu_image(image_path: pathlib.Path, config: dict) -> str:
    """复用家庭财富日报方案：上传 PNG 并返回飞书卡片可用的 image_key。"""
    app_id = keychain_value(config.get("app_id", ""))
    app_secret = keychain_value(config.get("app_secret", ""))
    if not app_id or not app_secret:
        raise ValueError("未配置飞书 app_id/app_secret，无法嵌入日报图片")
    token_response = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret}, timeout=20,
    )
    token_response.raise_for_status()
    token_data = token_response.json()
    token = token_data.get("tenant_access_token")
    if token_data.get("code") != 0 or not token:
        raise RuntimeError(f"飞书鉴权失败：{token_data.get('msg', 'unknown error')}")
    with image_path.open("rb") as image_file:
        response = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/images",
            headers={"Authorization": f"Bearer {token}"},
            data={"image_type": "message"},
            files={"image": (image_path.name, image_file, "image/png")}, timeout=60,
        )
    response.raise_for_status()
    upload_data = response.json()
    image_key = (upload_data.get("data") or {}).get("image_key")
    if upload_data.get("code") != 0 or not image_key:
        raise RuntimeError(f"飞书图片上传失败：{upload_data.get('msg', 'unknown error')}")
    return image_key


def send_email(png_path: pathlib.Path, report_date: dt.date) -> None:
    host, username, password, recipients = (os.getenv(k, "") for k in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "REPORT_EMAIL_TO"))
    if not all((host, username, password, recipients)):
        return
    message = email.message.EmailMessage()
    message["Subject"] = f"皇家农民工FC日报 · {report_date.isoformat()}"
    message["From"] = os.getenv("REPORT_EMAIL_FROM", username)
    message["To"] = recipients
    message.set_content(f"今日球队日报已生成。{f'在线版：{PUBLIC_REPORT_URL}' if PUBLIC_REPORT_URL else '请查看随信附带的日报长图。'}")
    message.add_attachment(png_path.read_bytes(), maintype="image", subtype="png", filename=png_path.name)
    port = int(os.getenv("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port) as client:
        client.login(username, password)
        client.send_message(message)


def send_webhooks(
    report_date: dt.date,
    data: dict,
    png_path: pathlib.Path,
    new_match: bool,
    editorial: dict[str, str],
) -> None:
    feishu_config = load_feishu_config()
    feishu = (os.getenv("FEISHU_WEBHOOK_URL", "") or os.getenv("LARK_WEBHOOK_URL", "")
              or keychain_value(feishu_config.get("webhook_url", "")))
    if feishu:
        image_key = upload_feishu_image(png_path, feishu_config)
        summary = (
            f'**{editorial["headline"]}**\n{editorial["deck"]}\n\n'
            f'{editorial["story"]}\n\n'
            f'**继续观察**\n{editorial["watch"]}\n\n'
            f'稿型：{editorial["templateName"]} · '
            f'{"本地大模型编辑稿" if editorial["source"].startswith("local:") else "严格数据规则降级稿"}'
        )
        post_json(feishu, {"msg_type": "interactive", "card": {"header": {"title": {"tag": "plain_text", "content": f"邮件报告｜皇家农民工FC日报 · {report_date.isoformat()}"}, "template": "blue"}, "elements": [{"tag": "img", "img_key": image_key, "alt": {"tag": "plain_text", "content": "皇家农民工FC日报"}, "mode": "fit_horizontal", "preview": True}, {"tag": "markdown", "content": summary}, {"tag": "note", "elements": [{"tag": "plain_text", "content": "数据与 royalfarmers.club 同源 · 每日自动更新"}]}]}})
        print("飞书日报图片上传并推送成功")
    wecom = os.getenv("WECOM_WEBHOOK_URL", "")
    if wecom:
        suffix = f"\n[打开完整日报]({PUBLIC_REPORT_URL})" if PUBLIC_REPORT_URL else ""
        topic = "新赛果、月度三榜与赛后点评已更新。" if new_match else "首页榜单轮换专题已更新。"
        post_json(wecom, {"msgtype": "markdown", "markdown": {"content": f"### 皇家农民工FC日报 · {report_date.isoformat()}\n{topic}{suffix}"}})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="日报日期（YYYY-MM-DD），默认今天")
    parser.add_argument("--no-send", action="store_true", help="只生成，不推送")
    args = parser.parse_args()
    report_date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    REPORT_DIR.mkdir(exist_ok=True)
    dated_html = REPORT_DIR / f"{report_date.isoformat()}.html"
    dated_png = REPORT_DIR / f"{report_date.isoformat()}.png"
    dated_scene_png = REPORT_DIR / f"{report_date.isoformat()}-scene.png"
    data = load_data()
    latest = data.get("FIXTURES", [{}])[0]
    new_match = is_new_fixture(latest, load_report_state())
    editorial = build_editorial(data, report_date, new_match)
    print(f'编辑稿型：{editorial["templateName"]} · {editorial["source"]}')
    editorial_json = json.dumps(editorial, ensure_ascii=False, indent=2)
    (REPORT_DIR / f"{report_date.isoformat()}-editorial.json").write_text(editorial_json, encoding="utf-8")
    (REPORT_DIR / "latest-editorial.json").write_text(editorial_json, encoding="utf-8")
    markup = render_html(data, report_date, new_match, editorial)
    dated_html.write_text(markup, encoding="utf-8")
    (REPORT_DIR / "latest.html").write_text(markup, encoding="utf-8")
    render_png(dated_html, dated_png)
    (REPORT_DIR / "latest.png").write_bytes(dated_png.read_bytes())
    configured_image_python = pathlib.Path(os.getenv("REPORT_IMAGE_PYTHON", str(DEFAULT_IMAGE_PYTHON)))
    image_python = configured_image_python if configured_image_python.exists() else pathlib.Path(sys.executable)
    subprocess.run(
        [str(image_python), str(PROJECT_DIR / "scripts" / "compose_report_scene.py"), str(dated_png), str(dated_scene_png)],
        check=True,
    )
    (REPORT_DIR / "latest-scene.png").write_bytes(dated_scene_png.read_bytes())
    if not args.no_send:
        send_email(dated_png, report_date)
        send_webhooks(report_date, data, dated_scene_png, new_match, editorial)
    save_report_state(latest)
    print(f"日报已生成：{dated_html}\n平面长图：{dated_png}\n真实场景图：{dated_scene_png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
