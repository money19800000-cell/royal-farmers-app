#!/usr/bin/env python3
"""皇家农民工 FC 日报编辑台：按专业足球报纸稿型选择主题并调用本地模型。"""

from __future__ import annotations

import collections
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import requests


CONFIG_FILE = Path(os.getenv("FOOTBALL_EDITORIAL_CONFIG", "/Users/macstudio/.claude/www/scripts/email_report_config.json"))

TEMPLATES: list[dict[str, str]] = [
    {"id": "scoring_race", "name": "射手竞争", "brief": "以榜首与追赶者的差距为钩子，解释竞争态势；先结论，再列两组数字，最后指出下一观察点。"},
    {"id": "creator_profile", "name": "组织核心", "brief": "聚焦助攻与参与度，用具体产出写人物价值；不把助攻数虚构成传球、控球或战术数据。"},
    {"id": "attendance_culture", "name": "铁人出勤", "brief": "从出场稳定性写球队文化和可靠性，比较榜首与次席，但不推断伤病或体能原因。"},
    {"id": "partnership", "name": "黄金搭档", "brief": "以进球者—助攻者连线次数为核心，写长期默契；区分相关性与战术因果。"},
    {"id": "lineup_chemistry", "name": "阵容化学", "brief": "围绕共同出场、胜率和样本量解读组合，主动提醒小样本，不夸大因果。"},
    {"id": "record_history", "name": "纪录史册", "brief": "把纪录放进队史坐标，说明数字的长期分量，兼具档案感和人物感。"},
    {"id": "milestone", "name": "里程碑", "brief": "当天有新里程碑就写新事件，否则回顾最近三项；突出日期、人物、门槛与历史意义。"},
]

MATCH_TEMPLATE = {"id": "match_report", "name": "赛后战报", "brief": "标题点出决定性人物或比分性质；导语先报赛果；正文按赛果—关键贡献者—数据影响—后续观察推进。"}


def _top_names(items: list[dict[str, Any]], field: str, limit: int = 5) -> list[dict[str, Any]]:
    return [{"name": item.get("name"), "num": item.get("num"), field: item.get(field)} for item in items[:limit]]


def _match_fact(fixture: dict[str, Any]) -> dict[str, Any]:
    scorer_counts = collections.Counter(name for name in [*fixture.get("homeScorers", []), *fixture.get("awayScorers", [])] if name)
    assist_counts = collections.Counter(name for name in [*fixture.get("homeAssists", []), *fixture.get("awayAssists", [])] if name and name not in {"？", "?", "/"})
    return {
        "date": fixture.get("date"), "home": fixture.get("home"), "homeScore": fixture.get("homeScore"),
        "awayScore": fixture.get("awayScore"), "away": fixture.get("away"), "competition": fixture.get("comp"),
        "venue": fixture.get("venue"), "topScorers": scorer_counts.most_common(5), "topAssists": assist_counts.most_common(5),
    }


def select_template(report_date: dt.date, new_match: bool) -> dict[str, str]:
    if new_match:
        return MATCH_TEMPLATE
    issue = (report_date - dt.date(report_date.year, 1, 1)).days + 1
    return TEMPLATES[(issue - 1) % len(TEMPLATES)]


def build_fact_pack(data: dict[str, Any], report_date: dt.date, template: dict[str, str]) -> dict[str, Any]:
    milestones = [item for item in data.get("MILESTONES", []) if item.get("date") and item["date"] <= report_date.isoformat()]
    records = data.get("RECORDS", {})
    flat_records = [item for group in records.values() for item in group] if isinstance(records, dict) else []
    common = {
        "reportDate": report_date.isoformat(),
        "selectedDesk": template["name"],
    }
    # 只把当日稿型需要的事实交给模型，避免将不同榜单的数字错接到同一人物或组合上。
    selected: dict[str, Any] = {
        "match_report": {
            "latestMatch": _match_fact((data.get("FIXTURES") or [{}])[0]),
            "monthlyPeriod": data.get("MONTHLY_PERIOD"),
            "monthlyGoals": _top_names(data.get("MONTHLY_GOALS", []), "goals"),
            "monthlyAssists": _top_names(data.get("MONTHLY_ASSISTS", []), "assists"),
        },
        "scoring_race": {"monthlyPeriod": data.get("MONTHLY_PERIOD"), "monthlyGoals": _top_names(data.get("MONTHLY_GOALS", []), "goals")},
        "creator_profile": {"monthlyPeriod": data.get("MONTHLY_PERIOD"), "monthlyAssists": _top_names(data.get("MONTHLY_ASSISTS", []), "assists")},
        "attendance_culture": {"monthlyPeriod": data.get("MONTHLY_PERIOD"), "monthlyApps": _top_names(data.get("MONTHLY_APPS", []), "apps")},
        "partnership": {"goldenPairs": data.get("GOLDEN_PAIRS", {}).get("all", [])[:5]},
        "lineup_chemistry": {"lineups": data.get("LINEUP_STATS", [])[:5]},
        "record_history": {"records": flat_records[:8], "matchCount": data.get("MATCH_COUNT")},
        "milestone": {"recentMilestones": sorted(milestones, key=lambda item: item.get("date", ""), reverse=True)[:3]},
    }[template["id"]]
    return {**common, **selected}


def _config() -> dict[str, Any]:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _model_candidates(config: dict[str, Any]) -> list[tuple[str, str, str]]:
    candidates = [
        (str(config.get("analysis_base_url", "http://127.0.0.1:8001")), str(config.get("analysis_model", "")), str(config.get("analysis_api_key", ""))),
        (str(config.get("anthropic_base_url", "http://127.0.0.1:18000")), str(config.get("anthropic_model", "")), str(config.get("anthropic_api_key", ""))),
    ]
    return [(base.rstrip("/"), model, key) for base, model, key in candidates if model]


def _parse_json(raw: str) -> dict[str, str]:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        result = json.loads(cleaned[start:end + 1]) if start >= 0 and end > start else {}
    return {key: str(result.get(key, "")).strip() for key in ("headline", "deck", "story", "watch")}


def _valid_editorial(editorial: dict[str, str]) -> bool:
    """拦截超出数据集能力边界的文本；这些指标当前都没有采集。"""
    combined = "".join(editorial.values())
    unsupported_terms = ("xG", "预期进球", "射门", "控球", "阵型", "跑动", "分钟", "逼抢", "失误率", "机会质量", "战术")
    return (
        all(editorial.values())
        and len(editorial["headline"]) <= 22
        and len(editorial["deck"]) <= 42
        and 70 <= len(editorial["story"]) <= 150
        and len(editorial["watch"]) <= 32
        and not any(term.lower() in combined.lower() for term in unsupported_terms)
    )


def _call_local_model(template: dict[str, str], facts: dict[str, Any]) -> tuple[dict[str, str] | None, str]:
    system = (
        "你是《皇家农民工足球报》资深主编。写法吸收专业足球媒体的编辑原则，但不得模仿或复刻任何具体作者措辞："
        "标题用人物/动作/后果构成；导语先给新闻结论；正文只选2至4个关键数字形成证据链；结尾给下一观察点。"
        "必须严格区分事实与推断。只能使用FACTS里的数据；没有射门、控球、xG、阵型、跑动和分钟信息时，绝对不得提及或猜测。"
        "本数据集没有战术数据，因此story和watch都不得使用‘战术’、‘逼抢’、‘失误率’或其他未采集指标。"
        "不写套话、加油口号、营销文案，不使用‘王者归来’‘火力全开’等空泛陈词。中文要像专业足球报纸，克制、具体、有现场感。"
    )
    user = (
        f"今日稿型：{template['name']}\n稿型结构：{template['brief']}\n"
        "请输出严格JSON：headline（18字内）、deck（34字内）、story（90至125个汉字）、watch（24字内）。"
        "story先结论后证据，至少准确引用两个数字；数据不支持的判断要写成‘仍需观察’，不能补造。\n"
        f"FACTS={json.dumps(facts, ensure_ascii=False, separators=(',', ':'))}"
    )
    for base_url, model, api_key in _model_candidates(_config()):
        try:
            headers = {"Content-Type": "application/json"}
            if api_key and not api_key.startswith("keychain:"):
                headers["Authorization"] = f"Bearer {api_key}"
            response = requests.post(
                f"{base_url}/v1/chat/completions", headers=headers,
                json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                      "temperature": 0.35, "max_tokens": 500, "stream": False,
                      "chat_template_kwargs": {"enable_thinking": False}}, timeout=120,
            )
            response.raise_for_status()
            editorial = _parse_json(response.json()["choices"][0]["message"]["content"])
            if _valid_editorial(editorial):
                return editorial, f"local:{model}"
        except Exception:
            continue
    return None, "fallback"


def _leader(items: list[dict[str, Any]], field: str) -> tuple[str, int]:
    return (str(items[0].get("name", "—")), int(items[0].get(field, 0) or 0)) if items else ("—", 0)


def fallback_editorial(template: dict[str, str], facts: dict[str, Any]) -> dict[str, str]:
    template_id = template["id"]
    if template_id == "match_report":
        match = facts["latestMatch"]
        scorers = match.get("topScorers", [])
        hero = scorers[0][0] if scorers else "进攻端"
        contribution = scorers[0][1] if scorers else 0
        score = f'{match.get("home")} {match.get("homeScore")}比{match.get("awayScore")} {match.get("away")}'
        return {"headline": f"{hero}写下最新赛果", "deck": score, "story": f"最新一场的结论先写在比分上：{score}。{hero}以{contribution}个进球成为记录中最突出的终结点。结果已经落定，但仅凭进球与助攻表还不足以推断控球和战术过程；真正值得继续观察的，是这场数据将如何改变月度榜单的距离。", "watch": "关注月榜差距是否继续收窄"}
    if template_id == "scoring_race":
        first, goals = _leader(facts["monthlyGoals"], "goals"); second, second_goals = _leader(facts["monthlyGoals"][1:], "goals")
        return {"headline": f"{first}守住月度杆位", "deck": f"{goals}球领跑，身后差距为{goals-second_goals}球", "story": f"本月射手榜的主动权仍在{first}脚下：{goals}球让他占据榜首，{second}以{second_goals}球紧随其后，两人的距离只有{goals-second_goals}球。数字说明竞争尚未结束，却不能单独解释机会质量。下一场谁先改变比分，谁就可能改变整个月的叙事。", "watch": "下一场首个进球可能重排榜首"}
    if template_id == "creator_profile":
        first, assists = _leader(facts["monthlyAssists"], "assists"); second, second_assists = _leader(facts["monthlyAssists"][1:], "assists")
        return {"headline": f"{first}掌握最后一传", "deck": f"{assists}次助攻建立月度领先", "story": f"当进球之外需要寻找进攻脉络，{first}的{assists}次助攻是最清楚的线索。第二名{second}目前为{second_assists}次，榜首优势达到{assists-second_assists}次。助攻无法还原全部组织过程，却足以说明谁最频繁地把队友送到终点。", "watch": "观察助攻优势能否转化为长期领先"}
    if template_id == "attendance_culture":
        first, apps = _leader(facts["monthlyApps"], "apps"); second, second_apps = _leader(facts["monthlyApps"][1:], "apps")
        return {"headline": f"{first}以出勤定义可靠", "deck": f"本月{apps}场，稳定本身就是价值", "story": f"出勤榜没有进球榜醒目，却最接近一支业余球队的日常底色。{first}本月出场{apps}次，{second}为{second_apps}次。这里不推断伤病或体能，只确认一件事：持续到场让阵容选择拥有稳定起点，也让每一项累计数据获得可信的时间基础。", "watch": "月底出勤榜将检验持续性"}
    if template_id == "partnership" and facts["goldenPairs"]:
        pair = facts["goldenPairs"][0]
        return {"headline": "一条连线沉淀成默契", "deck": f'{pair.get("scorer")}与{pair.get("ast")}已完成{pair.get("count")}次连接', "story": f'{pair.get("scorer")}作为终结者、{pair.get("ast")}作为助攻者，两人的组合已经记录{pair.get("count")}次直接连线。这是长期合作的强信号，但不是全部战术答案：数据没有描述无球跑动和传球之前的过程。它证明的是重复成功，以及彼此选择在时间中的累积。', "watch": "下一次连线将继续抬高队史门槛"}
    if template_id == "lineup_chemistry" and facts["lineups"]:
        item = facts["lineups"][0]
        rate = float(item.get("rate", 0) or 0)
        return {"headline": "组合胜率需要样本作证", "deck": f'{item.get("p1")}与{item.get("p2")}共同出场{item.get("apps", 0)}场', "story": f'{item.get("p1")}与{item.get("p2")}共同出场{item.get("apps", 0)}场，记录胜率为{rate:.1%}。这个数字提供了阵容效果的入口，却不能直接等同于因果：对手、队友和比赛环境都未被单独控制。专业解读的重点不是夸大一个百分比，而是等待样本继续增长后再判断稳定性。', "watch": "样本扩大后再检验组合含金量"}
    if template_id == "record_history" and facts["records"]:
        item = facts["records"][0]
        return {"headline": "纪录把当下写进队史", "deck": f'{item.get("label")}：{item.get("value")}{item.get("unit", "")}', "story": f'{item.get("label")}目前定格在{item.get("value")}{item.get("unit", "")}，保持者是{item.get("holder") or "皇家农民工FC"}。纪录的价值不只在数字够大，更在于它跨越比赛和赛季，提供了衡量后来者的坐标。当天的榜单会变化，队史门槛则负责记住长期积累。', "watch": "关注最接近纪录的下一位挑战者"}
    milestone = (facts["recentMilestones"] or [{}])[0]
    return {"headline": "最近的里程碑仍有回声", "deck": str(milestone.get("label", "队史继续累积")), "story": f'{milestone.get("date", "近期")}，{milestone.get("label", "球队写下新的里程碑")}。里程碑把漫长累计压缩成一个清晰刻度，也让普通比赛获得历史位置。若今天没有新事件，回看最近三项不是填补版面，而是提醒每个整数门槛都来自此前一次次真实出场。', "watch": "下一项整数门槛正在接近"}


def build_editorial(data: dict[str, Any], report_date: dt.date, new_match: bool) -> dict[str, str]:
    template = select_template(report_date, new_match)
    facts = build_fact_pack(data, report_date, template)
    editorial, source = _call_local_model(template, facts)
    if editorial is None:
        editorial = fallback_editorial(template, facts)
    return {**editorial, "templateId": template["id"], "templateName": template["name"], "source": source}
