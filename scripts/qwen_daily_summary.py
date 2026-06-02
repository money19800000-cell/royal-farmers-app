#!/usr/bin/env python3
"""
Royal Farmers FC — Qwen 每日简报
调用本地 oMLX (localhost:8001) 生成数据变更摘要
仅当 oMLX 运行时才调用，失败时静默退出（不阻断主流程）
"""
import json
import sys
import os
import subprocess
import datetime

try:
    import requests
except ImportError:
    sys.exit(0)  # 静默退出，不阻断主流程

OMLX_URL    = "http://localhost:8001/v1/chat/completions"
DATA_JSX    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.jsx")
LOG_FILE    = "/Users/macstudio/Library/Logs/royal-farmers-daily.log"

def read_recent_fixtures(n=5) -> str:
    """从 data.jsx 提取最近 n 场比赛"""
    try:
        with open(DATA_JSX, encoding="utf-8") as f:
            src = f.read()
        import re
        m = re.search(r'const FIXTURES = \[(.*?)\];', src, re.DOTALL)
        if not m:
            return "暂无比赛数据"
        block = m.group(1)
        matches = re.findall(
            r'\{[^}]*date:\s*"([^"]+)"[^}]*home:\s*"([^"]+)"[^}]*homeScore:\s*(\d+)[^}]*awayScore:\s*(\d+)[^}]*away:\s*"([^"]+)"[^}]*result:\s*"([^"]+)"',
            block
        )[:n]
        lines = [f"{d}  {h} {hs}-{aws} {a} ({'胜' if r=='W' else '平' if r=='D' else '负'})" for d,h,hs,aws,a,r in matches]
        return "\n".join(lines) or "暂无比赛数据"
    except Exception:
        return "无法读取比赛数据"

def read_top_stats() -> str:
    """从 data.jsx 提取本赛季 Top3 进球/助攻"""
    try:
        with open(DATA_JSX, encoding="utf-8") as f:
            src = f.read()
        import re
        goals = re.findall(r'\{name:"([^"]+)",num:"([^"]*)",goals:(\d+)', src[:src.find("const ASSISTS26")])[:3]
        assists = re.findall(r'\{name:"([^"]+)",num:"([^"]*)",assists:(\d+)', src[src.find("const ASSISTS26"):src.find("const APPS26")])[:3]
        g_str = "  ".join(f"{n}({num}号){v}球" for n,num,v in goals)
        a_str = "  ".join(f"{n}({num}号){v}助" for n,num,v in assists)
        return f"射手榜: {g_str}\n助攻榜: {a_str}"
    except Exception:
        return "无法读取榜单数据"

def call_qwen(prompt: str) -> str:
    payload = {
        "model": "local",
        "messages": [
            {"role": "system", "content": "你是皇家农民FC球队的数据助手，用简洁的中文输出，不超过150字。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.5,
    }
    resp = requests.post(OMLX_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"   [{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Main ──
try:
    today = datetime.date.today().strftime("%Y年%m月%d日")
    fixtures_text = read_recent_fixtures(5)
    stats_text    = read_top_stats()

    prompt = (
        f"今日 {today}，请根据以下数据生成皇家农民FC每日简报（中文，简洁）：\n\n"
        f"【最近比赛】\n{fixtures_text}\n\n"
        f"【本赛季榜单（2026）】\n{stats_text}\n\n"
        f"请输出：1) 最近成绩总结 2) 当前积分形势 3) 一句激励语"
    )

    log("调用 Qwen 生成日报...")
    summary = call_qwen(prompt)
    log(f"Qwen 日报:\n{summary}")

    # 也写入单独的日报文件供查阅
    report_dir = "/Users/macstudio/Library/Logs"
    report_file = os.path.join(report_dir, f"royal-farmers-summary-{datetime.date.today()}.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"Royal Farmers FC 每日简报 — {today}\n{'='*40}\n{summary}\n")
    log(f"日报已保存: {report_file}")

except Exception as e:
    log(f"Qwen 日报失败（不阻断主流程）: {e}")
    sys.exit(0)
