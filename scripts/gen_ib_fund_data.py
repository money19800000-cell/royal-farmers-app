#!/usr/bin/env python3
"""
gen_ib_fund_data.py
Generate ib-fund-data.js for the royalfarmers.club LP portal.

Run:
  /opt/homebrew/bin/python3.11 scripts/gen_ib_fund_data.py
"""

import csv
import json
from datetime import date
from pathlib import Path

BASE   = Path.home() / "Claude Code/numbers数据来源/option"
OUT    = Path(__file__).parent.parent / "ib-fund-data.js"


def read_csv(filename):
    p = BASE / filename
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def flt(v, default=0.0):
    try:
        s = str(v or "").strip()
        return float(s) if s else default
    except (ValueError, TypeError):
        return default


# ── 1. LP 统计（客户维度）─────────────────────────────────────────
lp_stats = []
for r in read_csv("沈菲的账户：私募-客户维度.csv"):
    name = (r.get("姓名") or "").strip()
    if not name:
        continue
    lp_stats.append({
        "name": name,
        "code": (r.get("编码") or "").strip(),
        "shares": flt(r.get("持仓份额")),
        "shareRatio": flt(r.get("持仓占比")),
        "marketValue": flt(r.get("持仓市值")),
        "totalPurchased": flt(r.get("累计申购")),
        "totalRedeemed": flt(r.get("累计赎回")),
        "totalDividend": flt(r.get("累计分红")),
        "netInvestment": flt(r.get("净申购额")),
        "pnl": flt(r.get("盈亏")),
        "pnlRate": flt(r.get("盈亏率")),
        "bondDividend": flt(r.get("美债派息")),
        "etfDividend": flt(r.get("ETF分红")),
        "futureOptionsIncome": flt(r.get("未来12个月期权收入")),
        "totalFutureIncome": flt(r.get("国债派息+ETF分红+期权预计收入")),
        "expectedYield": flt(r.get("预期年化收益率")),
    })

# ── 2. 出入金 ─────────────────────────────────────────────────────
transactions = []
for r in read_csv("沈菲的账户：私募-出入金.csv"):
    name = (r.get("客户名称") or "").strip()
    if not name:
        continue
    transactions.append({
        "date":   (r.get("日期") or "").strip(),
        "name":   name,
        "type":   (r.get("交易类型") or "").strip(),
        "amount": flt(r.get("金额")),
        "price":  (r.get("认购价格") or "").strip(),
        "shares": (r.get("份额") or "").strip(),
        "note":   (r.get("备注") or "").strip(),
    })

# ── 3. 月收益预测 ─────────────────────────────────────────────────
monthly_forecast = []
for r in read_csv("沈菲的账户：私募-月收益（最近12个月）.csv"):
    seq_s = (r.get("存续月") or "").strip()
    dt_s  = (r.get("时间") or "").strip()
    if not seq_s or not dt_s:
        continue
    try:
        seq = int(seq_s)
    except ValueError:
        continue
    monthly_forecast.append({
        "seq":            seq,
        "date":           dt_s,
        "expectedIncome": flt(r.get("预期收益")),
        "riskExposure":   flt(r.get("风险敞口")),
    })

# ── 4. 月末净值 ───────────────────────────────────────────────────
monthly_nav = []
for r in read_csv("沈菲的账户：私募-月末净值.csv"):
    dt_s = (r.get("时间") or "").strip()
    if not dt_s:
        continue
    chg = (r.get("涨跌") or "").strip()
    monthly_nav.append({
        "seq":    int(flt(r.get("序列"), 0)),
        "date":   dt_s[:7],
        "nav":    flt(r.get("净值(市值/净本金)")),
        "change": flt(chg) if chg and chg != "/" else None,
    })

# ── 5. 月度分红计划 ───────────────────────────────────────────────
div_rows = read_csv("沈菲的账户：私募-月度分红计划.csv")
div_items, total_div, total_div_cny = [], 0.0, 0.0
for r in div_rows:
    vals = list(r.values())
    name = (vals[0] if vals else "").strip()
    if name == "总分红":
        total_div     = flt(vals[1])
        total_div_cny = flt(vals[3])
        continue
    if not name:
        continue
    div_items.append({
        "name":      name,
        "amount":    flt(vals[1]),
        "ratio":     flt(vals[2]),
        "amountCNY": flt(vals[3]),
    })

# ── 6. 策略统计 ───────────────────────────────────────────────────
strategy_stats = []
labels_map = {"C": "备兑看涨 (Covered Call)", "P": "卖出看跌 (Cash-Secured Put)"}
for r in read_csv("沈菲的账户：私募-策略统计-IB（ShenFei）.csv"):
    s = (r.get("策略") or "").strip()
    if s not in ("C", "P"):
        continue
    strategy_stats.append({
        "strategy":      s,
        "label":         labels_map[s],
        "premium":       flt(r.get("策略权利金")),
        "premiumRatio":  flt(r.get("权利金比例")),
        "exposure":      flt(r.get("策略风险敞口")),
        "exposureRatio": flt(r.get("风险敞口占比")),
    })

# ── 7. 基金概览 ───────────────────────────────────────────────────
fund_overview = {}
for r in read_csv("概览-预计盈亏.csv"):
    if (r.get("账户") or "").strip() == "IB-Shen Fei":
        fund_overview = {
            "totalAssets":    flt(r.get("账户总资产")),
            "principal":      flt(r.get("实际本金")),
            "nav":            flt(r.get("净值化")),
            "bonds":          flt(r.get("国债")),
            "etf":            flt(r.get("ETF/个股")),
            "riskExposure":   flt(r.get("足额存续敞口")),
            "availableFunds": flt(r.get("可用资金")),
            "mtdReturn":      flt(r.get("6月平仓收益/本金")),
        }
        break

# ── 写入 ib-fund-data.js ──────────────────────────────────────────
data = {
    "generatedAt":     date.today().isoformat(),
    "fundOverview":    fund_overview,
    "lpStats":         lp_stats,
    "transactions":    transactions,
    "monthlyForecast": monthly_forecast,
    "monthlyNav":      monthly_nav,
    "dividendPlan":    {"items": div_items, "total": total_div, "totalCNY": total_div_cny},
    "strategyStats":   strategy_stats,
}

OUT.write_text(
    "// Auto-generated by gen_ib_fund_data.py — do not edit manually\n"
    f"window.IB_FUND_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n",
    encoding="utf-8",
)
print(f"✓ {OUT}")
print(f"  LPs: {len(lp_stats)}  Txns: {len(transactions)}  NAV: {len(monthly_nav)} months")
print(f"  NAV: {fund_overview.get('nav', 0):.4f}  本月总分红: ${total_div:.2f}")
