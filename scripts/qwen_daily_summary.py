#!/usr/bin/env python3
"""
Royal Farmers FC — Qwen 每日简报
调用本地 oMLX (localhost:8001) 生成数据变更摘要
仅当 oMLX 运行时才调用，失败时静默退出（不阻断主流程）
"""
import json
import sys
import os
import datetime
import urllib.request
import urllib.error

OMLX_URL  = "http://127.0.0.1:8001/v1/chat/completions"
OMLX_KEY  = "jiangke2001"
MODEL     = "Qwen3.5-122B-A10B-4bit"
DATA_JSX  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.jsx")
LOG_FILE  = "/Users/macstudio/Library/Logs/royal-farmers-daily.log"


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"   [{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def omlx_alive() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:8001/v1/models")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        return False


def ask_qwen(prompt: str, max_tokens: int = 300) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(
        OMLX_URL, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OMLX_KEY}",
        }
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read())
        return d["choices"][0]["message"]["content"].strip()


def read_recent_fixtures(n: int = 5) -> str:
    try:
        import re
        with open(DATA_JSX, encoding="utf-8") as f:
            src = f.read()
        m = re.search(r'const FIXTURES = \[(.*?)\];', src, re.DOTALL)
        if not m:
            return "暂无比赛数据"
        block = m.group(1)
        matches = re.findall(
            r'date:\s*"([^"]+)"[^}]*home:\s*"([^"]+)"[^}]*homeScore:\s*(\d+)'
            r'[^}]*awayScore:\s*(\d+)[^}]*away:\s*"([^"]+)"[^}]*result:\s*"([^"]+)"',
            block
        )[:n]
        lines = []
        for d, h, hs, aws, a, r in matches:
            result = "胜" if r == "W" else ("平" if r == "D" else "负")
            lines.append(f"{d}  {h} {hs}:{aws} {a}（{result}）")
        return "\n".join(lines) or "暂无比赛数据"
    except Exception:
        return "无法读取比赛数据"


def read_top_stats() -> str:
    try:
        import re
        with open(DATA_JSX, encoding="utf-8") as f:
            src = f.read()
        goals = re.findall(
            r'\{name:"([^"]+)",num:"([^"]*)",goals:(\d+)', src[:src.find("const ASSISTS26")]
        )[:3]
        assists = re.findall(
            r'\{name:"([^"]+)",num:"([^"]*)",assists:(\d+)',
            src[src.find("const ASSISTS26"):src.find("const APPS26")]
        )[:3]
        g_str = "  ".join(f"{n}({num}号){v}球" for n, num, v in goals)
        a_str = "  ".join(f"{n}({num}号){v}助" for n, num, v in assists)
        return f"射手榜: {g_str}\n助攻榜: {a_str}"
    except Exception:
        return "无法读取榜单数据"


# ── Main ──────────────────────────────────────────────────────────────────────
if not omlx_alive():
    log("oMLX 未运行，跳过 Qwen 日报")
    sys.exit(0)

try:
    today          = datetime.date.today().strftime("%Y年%m月%d日")
    fixtures_text  = read_recent_fixtures(5)
    stats_text     = read_top_stats()

    prompt = (
        f"今日 {today}，请根据以下数据生成皇家农民FC每日简报，"
        f"中文，简洁，不超过150字：\n\n"
        f"【最近5场比赛】\n{fixtures_text}\n\n"
        f"【2026赛季榜单 Top3】\n{stats_text}\n\n"
        f"请输出：1) 近期成绩总结 2) 当前榜单亮点 3) 一句激励语"
    )

    log("调用 Qwen 生成日报...")
    summary = ask_qwen(prompt)
    log(f"Qwen 日报:\n{summary}")

    # 保存日报文件
    report_file = f"/Users/macstudio/Library/Logs/royal-farmers-summary-{datetime.date.today()}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"Royal Farmers FC 每日简报 — {today}\n{'='*40}\n{summary}\n")
    log(f"日报已保存: {report_file}")

except Exception as e:
    log(f"Qwen 日报失败（不阻断主流程）: {e}")
    sys.exit(0)
