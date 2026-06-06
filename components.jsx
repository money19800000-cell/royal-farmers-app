// Royal Farmers FC — Components
const { useState, useEffect, useRef, useMemo } = React;
const { PLAYERS, GOALS26, ASSISTS26, APPS26, MATCH_COUNT, SEASONS, FIXTURES, HERO_BG, FEATURE_IMG, PLAYER_LOOKUP, MILESTONES, GOALS_ALL, ASSISTS_ALL, APPS_ALL, MONTHLY_GOALS, MONTHLY_ASSISTS, MONTHLY_APPS, MONTHLY_PERIOD, MONTHLY_HISTORY, RECORDS, STREAK_RECORDS, ALLSEASON_PLAYERS, RATINGS_ALL, RATINGS_2026, RATINGS_2025, RATINGS_2024, RATINGS_2023, RATINGS_2022, RATINGS_2021, PLAYER_STREAKS, PLAYER_HONORS, GOLDEN_PAIRS, SEASON_MATCH_STATS, LINEUP_STATS, LINEUP_ALL, MATCH_DATA, PLAYER_CHEMISTRY } = window.RF_DATA;

function weightedRating(seasons) {
  if (!seasons || seasons.length === 0) return null;
  const valid = seasons.filter(s => s.apps > 0 && s.rating != null);
  if (valid.length === 0) return null;
  const totalApps = valid.reduce((a, s) => a + s.apps, 0);
  if (totalApps === 0) return null;
  return valid.reduce((a, s) => a + s.apps * s.rating, 0) / totalApps;
}

function GoalList({ scorers, assists }) {
  if (!scorers || scorers.length === 0) return <div className="fsd-nil">—</div>;
  return scorers.map((name, i) => {
    const assist = assists && assists[i] ? assists[i] : null;
    return (
      <div key={i} className="fsd-goal-row">
        <span className="fsd-ico">⚽</span>
        <span className="fsd-gname">{name}</span>
        {assist && <>
          <span className="fsd-ico fsd-ico--assist">👟</span>
          <span className="fsd-gname fsd-gname--assist">{assist}</span>
        </>}
      </div>
    );
  });
}

// ---------- COUNT-UP ----------
function CountUp({ to, duration = 1200, suffix = "" }) {
  const [n, setN] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        const start = performance.now();
        const tick = (t) => {
          const p = Math.min(1, (t - start) / duration);
          const eased = 1 - Math.pow(1 - p, 3);
          setN(Math.round(eased * to));
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
        obs.disconnect();
      }
    }, { threshold: 0.4 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [to, duration]);
  return <span ref={ref}>{n.toLocaleString()}{suffix}</span>;
}

// ---------- TOP NAV ----------
function TopNav({ active, onNavigate, onSearch }) {
  const links = [
    { id: "home",  label: "首页" },
    { id: "match", label: "赛事" },
    { id: "squad", label: "球员" },
    { id: "stats", label: "数据" },
  ];
  return (
    <nav className="nav">
      <a className="nav__brand" href="#" onClick={(e) => { e.preventDefault(); onNavigate("home"); }}>
        <img src="assets/crest.jpg" alt="Royal Farmers FC" />
        <div>
          <div className="word">ROYAL <em>FARMERS</em> FC</div>
          <span className="sub">上海皇家农民工 · since 2020</span>
        </div>
      </a>
      <div className="nav__links">
        {links.map(l => (
          l.id === "stats"
            ? <a key={l.id} className="nav__link" href="datacenter.html">{l.label}</a>
            : <button key={l.id} className={"nav__link " + (active === l.id ? "is-active" : "")} onClick={() => onNavigate(l.id)}>{l.label}</button>
        ))}
        {onSearch && (
          <button className="nav__search-btn" onClick={onSearch} title="搜索球员 (⌘K)">
            🔍 <span>搜索</span> <kbd>⌘K</kbd>
          </button>
        )}
        <button className="nav__cta" onClick={() => onNavigate("squad")}>名册 · Roster</button>
      </div>
    </nav>
  );
}

// ---------- HERO ----------
function Hero({ activeSeason, onSeasonChange }) {
  return (
    <header className="hero" id="section-home">
      <div className="hero__bg" style={{ backgroundImage: `url(${HERO_BG})` }} />
      <div className="hero__scrim" />
      <div className="hero__content">
        <div className="hero__copy">
          <div className="hero__eyebrow">EST. 2020 · 上海 · 皇家农民工</div>
          <h1 className="hero__title">
            FOR THE<br/>FARMERS <em>· 为农民工而战</em>
          </h1>
          <p className="hero__sub">
            上海皇家农民工足球俱乐部，聚焦周四、周六的晚20:00-22:00，黄浦区台地花园球场。一个只属于中年人的快乐足球俱乐部。
          </p>
        </div>
      </div>
      <div className="hero__tabs">
        {SEASONS.map(s => (
          <button
            key={s}
            className={"hero__tab " + (s === activeSeason ? "is-active" : "")}
            onClick={() => onSeasonChange(s)}
          >
            {s === "总榜" ? "总榜 · ALL TIME" : `赛季 ${s}`}
          </button>
        ))}
      </div>
    </header>
  );
}

// ---------- KPI STRIP ----------
function StatStrip() {
  const totals = PLAYERS.reduce((acc, p) => ({
    goals:   acc.goals   + p.goals,
    assists: acc.assists + p.assists,
  }), { goals: 0, assists: 0 });
  const tiles = [
    { lbl: "现役球员 · Squad",   num: PLAYERS.length, sub: "ACTIVE ROSTER",    accent: false },
    { lbl: "比赛场次 · Matches", num: MATCH_COUNT,     sub: "ACROSS 6 SEASONS", accent: false },
    { lbl: "总进球 · Goals",     num: totals.goals,   sub: "ALL COMPETITIONS", accent: true  },
    { lbl: "总助攻 · Assists",   num: totals.assists, sub: "ALL COMPETITIONS", accent: false },
  ];
  return (
    <div className="kpis">
      {tiles.map((t, i) => (
        <div key={i} className={"kpi " + (t.accent ? "kpi--accent" : "")}>
          <div className="kpi__lbl">{t.lbl}</div>
          <div className="kpi__num"><CountUp to={t.num} /></div>
          <div className="kpi__sub">{t.sub}</div>
        </div>
      ))}
    </div>
  );
}

// ---------- FEATURED MATCH ----------
function FeaturedMatch() {
  const m = FIXTURES[0];
  const resultLabel = m.result === "W" ? "胜 · WIN" : m.result === "L" ? "负 · LOSS" : "平 · DRAW";
  return (
    <div className="feature">
      <div className="feature__img" style={{ backgroundImage: `url(${FEATURE_IMG})` }}>
        <span className="feature__live">{resultLabel}</span>
      </div>
      <div className="feature__body">
        <div className="feature__eyebrow">最新比赛 · LATEST · {m.date}</div>
        <div className="feature__teams">
          <div className="feature__team">{m.home}</div>
          <div className="feature__team is-away">{m.away}</div>
        </div>
        <div className="feature__score">{m.homeScore} <em>—</em> {m.awayScore}</div>
        <div className="feature__meta">
          <div>赛事<b>{m.comp}</b></div>
          <div>场地<b>台地花园球场</b></div>
        </div>
      </div>
    </div>
  );
}

// ---------- RANKINGS (ALL TIME) ----------
function Rankings({ onPlayerClick }) {
  const posLookup = {};
  (PLAYERS || []).forEach(p => { if (p.pos) posLookup[p.name] = p.pos; });
  Object.values(PLAYER_LOOKUP || {}).forEach(p => { if (p.pos && !posLookup[p.name]) posLookup[p.name] = p.pos; });
  const findFull = (p) => PLAYERS.find(pl => pl.name === p.name) || p;

  const cols = [
    { title: "射手榜 · TOP SCORERS",  data: (GOALS_ALL    || []).slice(0, 10), key: "goals"   },
    { title: "助攻榜 · TOP ASSISTS",  data: (ASSISTS_ALL  || []).slice(0, 10), key: "assists" },
    { title: "出场榜 · APPEARANCES",  data: (APPS_ALL     || []).slice(0, 10), key: "apps"    },
    { title: "评分榜 · RATINGS",      data: (RATINGS_ALL  || []).slice(0, 10), key: "rating",
      sub: p => `${p.apps}场`, fmt: p => p.rating.toFixed(2) },
  ];
  return (
    <div className="rankings">
      {cols.map(c => (
        <div className="rank-col" key={c.key}>
          <h3>{c.title}</h3>
          <div className="rank-list">
            {c.data.map((p, i) => (
              <div className="rank-row" key={i + p.name} onClick={() => onPlayerClick(findFull(p))}>
                <div className="rank-no">{i + 1}</div>
                <div className="rank-name">{p.num ? `${p.num}号${p.name}` : p.name}<span>{c.sub ? c.sub(p) : (posLookup[p.name] || '—')}</span></div>
                <div className="rank-value">{c.fmt ? c.fmt(p) : p[c.key]}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------- RANKINGS 2026 ----------
function Rankings2026({ onPlayerClick }) {
  const cols = [
    { title: "射手榜 · TOP SCORERS",  data: GOALS26,          key: "goals",   sub: p => `${p.apps}场` },
    { title: "助攻榜 · TOP ASSISTS",  data: ASSISTS26,        key: "assists", sub: p => `${p.apps}场` },
    { title: "出勤榜 · ATTENDANCE",   data: APPS26,           key: "apps",    sub: p => p.pct },
    { title: "评分榜 · RATINGS",      data: (RATINGS_2026||[]).slice(0,10), key: "rating",
      sub: p => `${p.apps}场`, fmt: p => p.rating.toFixed(2) },
  ];
  const findPlayer = (p) => PLAYERS.find(pl => pl.name === p.name) || { ...p, num: 0, pos: "—" };
  return (
    <div className="rankings">
      {cols.map(c => (
        <div className="rank-col" key={c.key}>
          <h3>{c.title}</h3>
          <div className="rank-list">
            {c.data.map((p, i) => (
              <div className="rank-row" key={i + p.name} onClick={() => onPlayerClick(findPlayer(p))}>
                <div className="rank-no">{i + 1}</div>
                <div className="rank-name">{p.num ? `${p.num}号${p.name}` : p.name}<span>{c.sub(p)}</span></div>
                <div className="rank-value">{c.fmt ? c.fmt(p) : p[c.key]}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------- RANKINGS BY SEASON (2025 and older) ----------
function RankingsBySeason({ year, onPlayerClick }) {
  const allPlayers = [...PLAYERS, ...Object.values(PLAYER_LOOKUP || {})];
  const getSeason = (p) => (p.seasons || []).find(s => s.year === year) || { apps: 0, goals: 0, assists: 0, rating: null };
  const top = (key, n = 10) => allPlayers
    .map(p => ({ ...p, _s: getSeason(p) }))
    .filter(p => p._s[key] > 0)
    .sort((a, b) => b._s[key] - a._s[key])
    .slice(0, n);
  const findFull = (p) => PLAYERS.find(pl => pl.name === p.name) || (PLAYER_LOOKUP && PLAYER_LOOKUP[p.name]) || p;
  const ratingsMap = {
    '2025': RATINGS_2025, '2024': RATINGS_2024, '2023': RATINGS_2023,
    '2022': RATINGS_2022, '2021': RATINGS_2021,
  };
  const ratingsData = (ratingsMap[year] || []).slice(0, 10);

  const cols = [
    { title: "射手榜 · TOP SCORERS", key: "goals",   sub: p => `${p._s.apps}场` },
    { title: "助攻榜 · TOP ASSISTS", key: "assists", sub: p => `${p._s.apps}场` },
    { title: "出场榜 · APPEARANCES", key: "apps",    sub: p => `${p._s.goals}球` },
    { title: "评分榜 · RATINGS",     key: "_rating", sub: p => `${p.apps}场`,
      data: ratingsData, fmt: p => p.rating.toFixed(2) },
  ];
  return (
    <div className="rankings">
      {cols.map(c => {
        const rows = c.data ? c.data : top(c.key);
        return (
          <div className="rank-col" key={c.key}>
            <h3>{c.title}</h3>
            <div className="rank-list">
              {rows.map((p, i) => (
                <div className="rank-row" key={i + p.name} onClick={() => onPlayerClick(findFull(p))}>
                  <div className="rank-no">{i + 1}</div>
                  <div className="rank-name">{p.num ? `${p.num}号${p.name}` : p.name}<span>{c.sub(p)}</span></div>
                  <div className="rank-value">{c.fmt ? c.fmt(p) : (p._s ? p._s[c.key] : p[c.key])}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------- BILIBILI ----------
const BILI_SPACE = "https://space.bilibili.com/2037584148";

// ---------- FIXTURES ----------
function Fixtures({ limit = 7, onMatchClick }) {
  function biliUrl(date, type) {
    const d = date.replace(/\./g, "");
    return `${BILI_SPACE}/search/video?keyword=${encodeURIComponent(d + type)}`;
  }
  const list = FIXTURES.slice(0, limit);
  return (
    <div className="fixtures">
      <div className="fix-row is-head">
        <div>日期 · DATE</div>
        <div>主队 · HOME</div>
        <div></div>
        <div style={{ textAlign: "right" }}>客队 · AWAY</div>
        <div>赛事 · COMP</div>
        <div></div>
      </div>
      {list.map((f, i) => (
        <div className="fix-row" key={i} onClick={() => onMatchClick && onMatchClick(f)}
          title="点击查看比赛详情">
          <div className="fix-date">{f.date}</div>
          <div className="fix-team">{f.home}</div>
          <div className="fix-score-wrap">
            <span className={"fix-num " + (f.homeScore > f.awayScore ? "win" : f.homeScore < f.awayScore ? "loss" : "")}>{f.homeScore}</span>
            <span className="fix-dash">—</span>
            <span className={"fix-num " + (f.awayScore > f.homeScore ? "win" : f.awayScore < f.homeScore ? "loss" : "")}>{f.awayScore}</span>
          </div>
          <div className="fix-team is-away">{f.away}</div>
          <div className="fix-comp">{f.comp}</div>
          <div style={{ display: "flex", gap: "4px" }} onClick={e => e.stopPropagation()}>
            <a className="fix-watch" href={biliUrl(f.date, "录像")} target="_blank" rel="noopener">录像</a>
            <a className="fix-watch" href={biliUrl(f.date, "集锦")} target="_blank" rel="noopener">集锦</a>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------- ALL FIXTURES ----------
function AllFixtures() {
  return (
    <div className="all-fixtures">
      {FIXTURES.map((f, i) => {
        const hasDetail = f.homeScorers?.length || f.awayScorers?.length || f.homeAssists?.length || f.awayAssists?.length;
        return (
          <div className="afix-match" key={i}>
            <div className="afix-meta">
              <span className={"fix-result " + f.result}>{f.result === "W" ? "胜" : f.result === "D" ? "平" : "负"}</span>
              <span className="afix-comp">{f.comp}</span>
              {f.venue && <><span className="afix-dot">·</span><span className="afix-venue">📍 {f.venue}</span></>}
            </div>
            <div className="afix-main">
              <div className="fix-date">{f.date}</div>
              <div className="fix-team">{f.home}</div>
              <div className="fix-score-wrap">
                <span className={"fix-num " + (f.homeScore > f.awayScore ? "win" : f.homeScore < f.awayScore ? "loss" : "")}>{f.homeScore}</span>
                <span className="fix-dash">—</span>
                <span className={"fix-num " + (f.awayScore > f.homeScore ? "win" : f.awayScore < f.homeScore ? "loss" : "")}>{f.awayScore}</span>
              </div>
              <div className="fix-team is-away">{f.away}</div>
            </div>
            {!!hasDetail && (
              <div className="afix-detail">
                <div className="afix-detail-side">
                  <GoalList scorers={f.homeScorers} assists={f.homeAssists} />
                </div>
                <div className="afix-detail-sep" />
                <div className="afix-detail-side">
                  <GoalList scorers={f.awayScorers} assists={f.awayAssists} />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ---------- BEST XI ----------
function BestXI() {
  // 横向球场：x = 左(守门)→右(进攻)，y = 上→下（球场宽度方向）
  const lineup = [
    { cn: "前锋",   en: "ST", name: "姜珂",   apps: 392, goals: 906,  assists: 1171, x: 79, y: 36, photo: "assets/players/10号姜珂.jpeg" },
    { cn: "前锋",   en: "ST", name: "盛建中", apps: 164, goals: 251,  assists: 96,   x: 79, y: 64, photo: null },
    { cn: "左前卫", en: "LM", name: "金辉",   apps: 327, goals: 546,  assists: 234,  x: 56, y: 10, photo: "assets/players/81号金辉.jpeg" },
    { cn: "中前卫", en: "CM", name: "张伟",   apps: 224, goals: 147,  assists: 84,   x: 55, y: 36, photo: "assets/players/17号张伟.jpeg" },
    { cn: "中前卫", en: "CM", name: "陶骏",   apps: 283, goals: 289,  assists: 259,  x: 55, y: 64, photo: "assets/players/6号陶骏.jpeg" },
    { cn: "右前卫", en: "RM", name: "潘磊",   apps: 175, goals: 347,  assists: 229,  x: 56, y: 90, photo: null },
    { cn: "左后卫", en: "LB", name: "老徐",   apps: 262, goals: 115,  assists: 137,  x: 30, y: 10, photo: null },
    { cn: "中卫",   en: "CB", name: "杨坤",   apps: 196, goals: 167,  assists: 159,  x: 30, y: 36, photo: null },
    { cn: "中卫",   en: "CB", name: "鲍梁剑", apps: 202, goals: 84,   assists: 63,   x: 30, y: 64, photo: "assets/players/22号鲍梁剑.jpeg" },
    { cn: "右后卫", en: "RB", name: "曹峰",   apps: 233, goals: 57,   assists: 62,   x: 30, y: 90, photo: null },
    { cn: "门将",   en: "GK", name: "麦超",   apps: 278, goals: 4,    assists: 6,    x: 9,  y: 50, photo: "assets/players/22号麦超.jpeg" },
  ];
  const posColor = { GK: "#f59e0b", LB: "#60a5fa", CB: "#60a5fa", RB: "#60a5fa", LM: "#4ade80", CM: "#4ade80", RM: "#4ade80", ST: "#f87171" };
  return (
    <div className="pitch-wrap">
      <div className="pitch">
        {/* 横向球场 viewBox: 460宽 × 320高 */}
        <svg className="pitch-svg" viewBox="0 0 460 320" xmlns="http://www.w3.org/2000/svg">
          {/* 外框 */}
          <rect x="3" y="3" width="454" height="314" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="2"/>
          {/* 中线 */}
          <line x1="230" y1="3" x2="230" y2="317" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          {/* 中圈 */}
          <circle cx="230" cy="160" r="50" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <circle cx="230" cy="160" r="3.5" fill="rgba(255,255,255,0.5)"/>
          {/* 左侧禁区 */}
          <rect x="3" y="72" width="82" height="176" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          {/* 左侧小禁区 */}
          <rect x="3" y="112" width="30" height="96" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          {/* 左点球点 */}
          <circle cx="63" cy="160" r="3" fill="rgba(255,255,255,0.5)"/>
          {/* 右侧禁区 */}
          <rect x="375" y="72" width="82" height="176" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          {/* 右侧小禁区 */}
          <rect x="427" y="112" width="30" height="96" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          {/* 右点球点 */}
          <circle cx="393" cy="160" r="3" fill="rgba(255,255,255,0.5)"/>
        </svg>
        {lineup.map((p, i) => (
          <div key={i} className="pt" style={{ left: `${p.x}%`, top: `${p.y}%` }}>
            <div className="pt__badge" style={{ "--pt-color": posColor[p.en] }}>
              {p.photo ? <img src={p.photo} alt={p.name} /> : <span>{p.name[0]}</span>}
            </div>
            <div className="pt__name">{p.name}</div>
            <div className="pt__posl">{p.cn}</div>
            <div className="pt__tip">
              <div className="ptt-head">{p.name}<span className="ptt-pos">{p.cn}</span></div>
              <div className="ptt-stats">出场 <b>{p.apps}</b> · 进球 <b>{p.goals}</b> · 助攻 <b>{p.assists}</b></div>
            </div>
          </div>
        ))}
      </div>
      <div className="pitch-legend">
        {[["#f87171","前锋"],["#4ade80","中场"],["#60a5fa","后卫"],["#f59e0b","门将"]].map(([c,l]) => (
          <div key={l} className="pitch-legend-item"><span style={{background:c}}></span>{l}</div>
        ))}
      </div>
    </div>
  );
}

// ---------- MONTHLY RANKINGS ----------
function MonthlyRankings({ onPlayerClick }) {
  // ── 数据准备 ──
  const history = (MONTHLY_HISTORY && MONTHLY_HISTORY.length > 0)
    ? MONTHLY_HISTORY
    : [{ period: MONTHLY_PERIOD || "本月", goals: MONTHLY_GOALS || [], assists: MONTHLY_ASSISTS || [], apps: MONTHLY_APPS || [] }];

  // 按年分组，每年内按月降序（最新在前）
  const byYear = {};
  history.forEach(m => {
    const mt = m.period.match(/(\d{4})年(\d+)月/);
    if (!mt) return;
    const yr = mt[1], mo = parseInt(mt[2]);
    if (!byYear[yr]) byYear[yr] = [];
    byYear[yr].push({ ...m, _mo: mo });
  });
  Object.values(byYear).forEach(arr => arr.sort((a, b) => b._mo - a._mo));
  const years = Object.keys(byYear).sort((a, b) => b - a); // 降序，最新年在前

  const [selYear, setSelYear]   = useState(years[0] || '2026');
  const [selMoIdx, setSelMoIdx] = useState(0);

  const monthsInYear = byYear[selYear] || [];
  const current = monthsInYear[selMoIdx] || monthsInYear[0];

  function handleYearClick(yr) {
    setSelYear(yr);
    setSelMoIdx(0);
  }

  // ── 滑动支持 ──
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const dragging    = useRef(false);

  function onTouchStart(e) {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
    dragging.current = false;
  }
  function onTouchMove(e) {
    const dx = Math.abs(e.touches[0].clientX - touchStartX.current);
    const dy = Math.abs(e.touches[0].clientY - touchStartY.current);
    if (dx > dy && dx > 8) { dragging.current = true; e.preventDefault(); }
  }
  function onTouchEnd(e) {
    if (!dragging.current) return;
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) {
      if (diff > 0 && selMoIdx < monthsInYear.length - 1) setSelMoIdx(selMoIdx + 1);
      if (diff < 0 && selMoIdx > 0)                       setSelMoIdx(selMoIdx - 1);
    }
    dragging.current = false;
  }

  // ── 辅助 ──
  const PHOTO_MAP = {};
  (PLAYERS || []).forEach(p => { if (p.photo) PHOTO_MAP[p.name] = p.photo; });
  Object.values(PLAYER_LOOKUP || {}).forEach(p => { if (p.photo) PHOTO_MAP[p.name] = p.photo; });
  const allPlayers = [...(PLAYERS||[]), ...Object.values(PLAYER_LOOKUP||{})];
  function findPlayer(name) { return allPlayers.find(p => p.name === name) || null; }

  function RankRow({ item, rank, valKey, icon }) {
    const p = findPlayer(item.name);
    const photo = PHOTO_MAP[item.name];
    const val = item[valKey];
    const medalColor = rank === 1 ? "var(--rf-gold)" : rank === 2 ? "#c0c0c0" : rank === 3 ? "#cd7f32" : "var(--rf-fg-3)";
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    return (
      <div className={`mr-row ${p ? "mr-row--clickable" : ""}`} onClick={() => { if (p && onPlayerClick) onPlayerClick(p); }}>
        <div className="mr-rank" style={{ color: medalColor }}>{medal}</div>
        <div className="mr-avatar">
          {photo ? <img src={photo} alt={item.name} /> : <span className="mr-initials">{item.name[0]}</span>}
        </div>
        <div className="mr-info">
          <span className="mr-name">{item.num ? `${item.num}号${item.name}` : item.name}</span>
        </div>
        <div className="mr-val" style={{ color: rank <= 3 ? medalColor : "var(--rf-fg)" }}>{icon} {val}</div>
      </div>
    );
  }

  function MonthPanel({ m }) {
    return (
      <div className="mr-grid">
        <div className="mr-panel">
          <div className="mr-panel-title">⚽ 射手榜</div>
          {(m.goals||[]).length > 0
            ? (m.goals||[]).map((item, i) => <RankRow key={i} item={item} rank={i+1} valKey="goals" icon="⚽" />)
            : <div className="mr-empty">暂无数据</div>}
        </div>
        <div className="mr-panel">
          <div className="mr-panel-title">👟 助攻榜</div>
          {(m.assists||[]).length > 0
            ? (m.assists||[]).map((item, i) => <RankRow key={i} item={item} rank={i+1} valKey="assists" icon="👟" />)
            : <div className="mr-empty">暂无数据</div>}
        </div>
        <div className="mr-panel">
          <div className="mr-panel-title">📅 出勤榜</div>
          {(m.apps||[]).length > 0
            ? (m.apps||[]).map((item, i) => <RankRow key={i} item={item} rank={i+1} valKey="apps" icon="📅" />)
            : <div className="mr-empty">暂无数据</div>}
        </div>
      </div>
    );
  }

  return (
    <section className="section mr-section">
      <div className="container">
        {/* 标题 */}
        <div className="section__head">
          <div>
            <span className="section__eyebrow">MONTHLY CHART · 月度榜单</span>
            <h2 className="section__title">
              {current ? current.period + '榜单' : '月度榜单'} <em>· Monthly Rankings</em>
            </h2>
          </div>
        </div>

        {/* 第一级：年份切换 */}
        <div className="mr-year-tabs">
          {years.map(yr => (
            <button
              key={yr}
              className={`mr-year-tab ${yr === selYear ? 'mr-year-tab--active' : ''}`}
              onClick={() => handleYearClick(yr)}
            >{yr}</button>
          ))}
        </div>

        {/* 第二级：月份切换（仅显示该年有数据的月份） */}
        <div className="mr-month-tabs">
          {monthsInYear.map((m, i) => (
            <button
              key={i}
              className={`mr-month-tab ${i === selMoIdx ? 'mr-month-tab--active' : ''}`}
              onClick={() => setSelMoIdx(i)}
            >{m._mo}月</button>
          ))}
        </div>

        {/* 内容轮播（仅当年月份） */}
        <div className="mr-carousel-wrap" onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}>
          <div className="mr-carousel-track" style={{ transform: `translateX(-${selMoIdx * 100}%)` }}>
            {monthsInYear.map((m, i) => (
              <div className="mr-carousel-slide" key={i}>
                <MonthPanel m={m} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------- PLAYER CAROUSEL (8-per-page, auto-scroll) ----------
function PlayersCarousel({ onPlayerClick }) {
  const allWithPhotos = [
    ...PLAYERS,
    ...Object.values(PLAYER_LOOKUP || {}),
  ].filter(p => p.photo)
   .filter((p, i, arr) => arr.findIndex(x => x.name === p.name) === i);

  const PER_PAGE = 8;
  const pages = [];
  for (let i = 0; i < allWithPhotos.length; i += PER_PAGE) {
    pages.push(allWithPhotos.slice(i, i + PER_PAGE));
  }

  const [page, setPage] = useState(0);
  const timerRef = useRef(null);

  function goTo(idx) {
    setPage(idx);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setPage(p => (p + 1) % pages.length), 4500);
  }

  useEffect(() => {
    timerRef.current = setInterval(() => setPage(p => (p + 1) % pages.length), 4500);
    return () => clearInterval(timerRef.current);
  }, [pages.length]);

  function PlayerCard({ p }) {
    return (
      <div className="player-card player-card--photo" onClick={() => onPlayerClick(p)}>
        <div className="player-card__photo">
          <img src={p.photo} alt={p.name} loading="lazy" />
          {p.num ? <div className="player-card__photo-badge">{p.num}号</div> : null}
        </div>
        <div className="player-card__info">
          <div className="player-card__name">{p.name}</div>
          <div className="player-card__pos">{p.pos} · {p.nation}</div>
          <div className="player-card__stats">
            <div><span>出场</span><b>{p.apps}</b></div>
            <div><span>进球</span><b>{p.goals}</b></div>
            <div><span>助攻</span><b>{p.assists}</b></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pc-wrap">
      <div className="pc-viewport">
        <div className="pc-track" style={{ transform: `translateX(${-page * 100}%)` }}>
          {pages.map((pg, pi) => (
            <div key={pi} className="pc-page">
              {pg.map(p => <PlayerCard key={p.name} p={p} />)}
            </div>
          ))}
        </div>
      </div>
      <div className="pc-dots">
        {pages.map((_, i) => (
          <button key={i} className={"pc-dot" + (i === page ? " is-active" : "")} onClick={() => goTo(i)} aria-label={`第${i+1}页`} />
        ))}
      </div>
    </div>
  );
}

// ---------- PLAYER MODAL — Full Profile ----------
function PlayerModal({ player, onClose, onPlayerClick }) {
  const [videos, setVideos] = useState(null); // null=loading, []=fallback, [{bvid,title,pic}]=loaded

  // Keyboard + scroll lock
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = player ? "hidden" : "";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose, player]);

  // Fetch latest videos from Bilibili via JSONP when player changes
  useEffect(() => {
    if (!player) { setVideos(null); return; }
    setVideos(null); // show loading
    const pname = player.name;
    const cbKey = "_biliCb" + Date.now();
    const el = document.createElement("script");
    const tid = setTimeout(() => { cleanup(); setVideos([]); }, 7000);

    function cleanup() {
      clearTimeout(tid);
      delete window[cbKey];
      if (el.parentNode) el.parentNode.removeChild(el);
    }

    window[cbKey] = (res) => {
      cleanup();
      const vlist = res && res.data && res.data.list && res.data.list.vlist;
      if (Array.isArray(vlist) && vlist.length > 0) {
        setVideos(vlist.slice(0, 4).map(v => ({
          bvid:  v.bvid,
          title: v.title,
          pic:   (v.pic || "").replace(/^http:/, "https:"),
        })));
      } else {
        setVideos([]);
      }
    };

    el.src = `https://api.bilibili.com/x/space/arc/search?mid=2037584148&keyword=${encodeURIComponent(pname)}&order=pubdate&pn=1&ps=4&jsonp=jsonp&callback=${cbKey}`;
    el.onerror = () => { cleanup(); setVideos([]); };
    document.head.appendChild(el);
    return cleanup;
  }, [player && player.name]);

  if (!player) return null;

  // Find full player data
  const full = PLAYERS.find(p => p.name === player.name)
             || (PLAYER_LOOKUP && PLAYER_LOOKUP[player.name])
             || player;
  const seasons = (full.seasons || []).filter(s => s.apps > 0 || s.goals > 0 || s.assists > 0);
  const hasSeasons = seasons.length > 0;

  const fmt  = (v) => v != null ? v : "—";
  const fmtR = (v) => v != null ? Number(v).toFixed(2) : "—";
  const pname = full.name || player.name;
  const bUrl  = `${BILI_SPACE}/search/video?keyword=${encodeURIComponent(pname)}`;

  return (
    <div className="modal profile-modal" onClick={onClose}>
      <div className="profile-panel" onClick={e => e.stopPropagation()}>

        {/* ── HEADER ── */}
        <div className="profile-head">
          {full.photo
            ? <div className="profile-photo"><img src={full.photo} alt={full.name} /></div>
            : <div className="profile-num-badge">#{full.num || player.num || "?"}</div>
          }
          <div className="profile-identity">
            <div className="profile-jersey">#{full.num || player.num || "?"}</div>
            <h2 className="profile-name">{pname}</h2>
            <div className="profile-meta">
              <span>{full.pos || player.pos || "—"}</span>
              <span>·</span>
              <span>{full.nation || player.nation || "中国"}</span>
              {(full.birth || player.birth) && (full.birth || player.birth) !== "—"
                ? <><span>·</span><span>Born {full.birth || player.birth}</span></>
                : null}
            </div>
          </div>
          <button className="profile-close" onClick={onClose}>×</button>
        </div>

        {/* ── SEASON TABLE ── */}
        <div className="profile-body">
          {hasSeasons ? (
            <div className="profile-stats">
              <div className="profile-section-title">赛季数据 · Season Stats</div>
              <table className="season-table">
                <thead>
                  <tr>
                    <th>赛季</th><th>出场</th><th>进球</th><th>助攻</th><th>评分</th>
                  </tr>
                </thead>
                <tbody>
                  {seasons.map(s => (
                    <tr key={s.year} className={s.year === "2026" ? "season-row--current" : ""}>
                      <td className="season-year">{s.year}</td>
                      <td>{fmt(s.apps)}</td>
                      <td className={s.goals > 0 ? "stat-highlight" : ""}>{fmt(s.goals)}</td>
                      <td>{fmt(s.assists)}</td>
                      <td className="stat-dim">{fmtR(s.rating)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="season-total">
                    <td>总计</td>
                    <td>{fmt(full.apps)}</td>
                    <td>{fmt(full.goals)}</td>
                    <td>{fmt(full.assists)}</td>
                    <td className="stat-dim">{fmtR(weightedRating(full.seasons))}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          ) : (
            <div className="profile-stats">
              <div className="profile-section-title">职业生涯 · Career</div>
              <div className="profile-career-kpis">
                <div className="career-kpi"><span>出场</span><b>{fmt(full.apps || player.apps)}</b></div>
                <div className="career-kpi"><span>进球</span><b>{fmt(full.goals || player.goals)}</b></div>
                <div className="career-kpi"><span>助攻</span><b>{fmt(full.assists || player.assists)}</b></div>
              </div>
            </div>
          )}

          {/* ── 成长曲线 ── */}
          {seasons.length >= 2 && <PlayerGrowthChart seasons={seasons} />}

          {/* ── 个人记录 ── */}
          {(() => {
            const ps = PLAYER_STREAKS && PLAYER_STREAKS[pname];
            if (!ps) return null;
            const items = [
              ps.apps     && { icon: "🏃", label: "连续出场", count: ps.apps.count,     from: ps.apps.from,     to: ps.apps.to,     dim: false },
              ps.win      && { icon: "🏆", label: "连续获胜", count: ps.win.count,      from: ps.win.from,      to: ps.win.to,      dim: false },
              ps.unbeaten && { icon: "🛡️", label: "连续不败", count: ps.unbeaten.count, from: ps.unbeaten.from, to: ps.unbeaten.to, dim: false },
              ps.nowin    && { icon: "📉", label: "连续不胜", count: ps.nowin.count,    from: ps.nowin.from,    to: ps.nowin.to,    dim: true  },
              ps.goal     && { icon: "⚽", label: "连续进球", count: ps.goal.count,     from: ps.goal.from,     to: ps.goal.to,     dim: false },
              ps.assist   && { icon: "👟", label: "连续助攻", count: ps.assist.count,   from: ps.assist.from,   to: ps.assist.to,   dim: false },
            ].filter(Boolean);
            if (!items.length) return null;
            return (
              <div className="profile-streaks">
                <div className="profile-section-title">个人记录 · Personal Records</div>
                <div className="pstreak-list">
                  {items.map((it, i) => (
                    <div key={i} className={`pstreak-row${it.dim ? " pstreak-row--dim" : ""}`}>
                      <span className="pstreak-icon">{it.icon}</span>
                      <span className="pstreak-label">{it.label}</span>
                      <span className="pstreak-count">{it.count} 场</span>
                      <span className="pstreak-date">{it.from} — {it.to}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* ── 个人荣誉 ── */}
          {(() => {
            const ph = PLAYER_HONORS && PLAYER_HONORS[pname];
            if (!ph || !ph.length) return null;
            return (
              <div className="profile-honors">
                <div className="profile-section-title">个人荣誉 · Honours</div>
                <div className="phonor-list">
                  {ph.map((h, i) => (
                    <div key={i} className="phonor-row">
                      <span className="phonor-badge">🏅</span>
                      <span className="phonor-text">{h.period} {h.award}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* ── 球队化学反应 ── */}
          {(() => {
            const chem = PLAYER_CHEMISTRY && PLAYER_CHEMISTRY[pname];
            if (!chem) return null;
            const allPlayers = [...(PLAYERS||[]), ...Object.values(PLAYER_LOOKUP||{})];
            const findP = name => allPlayers.find(p => p.name === name) || null;
            const rows = [
              chem.a2me  && { icon: '🎯', label: '助攻我最多', name: chem.a2me.name,  sub: `${chem.a2me.count} 次` },
              chem.me2a  && { icon: '👟', label: '我助攻最多', name: chem.me2a.name,  sub: `${chem.me2a.count} 次` },
              chem.bestP && { icon: '🔥', label: '共同出场胜率最高', name: chem.bestP.name, sub: `${(chem.bestP.rate*100).toFixed(0)}% · ${chem.bestP.apps}场` },
              chem.worstP && { icon: '❄️', label: '共同出场胜率最低', name: chem.worstP.name, sub: `${(chem.worstP.rate*100).toFixed(0)}% · ${chem.worstP.apps}场` },
            ].filter(Boolean);
            if (!rows.length) return null;
            return (
              <div className="profile-streaks">
                <div className="profile-section-title">化学反应 · Chemistry</div>
                <div className="pstreak-list">
                  {rows.map((row, i) => {
                    const p = findP(row.name);
                    const canNav = !!(p && onPlayerClick);
                    return (
                      <div key={i} className="pstreak-row"
                        style={{cursor: canNav ? 'pointer' : 'default'}}
                        onClick={() => { if (canNav) { onPlayerClick(p); } }}>
                        <span className="pstreak-icon">{row.icon}</span>
                        <span className="pstreak-label">{row.label}</span>
                        <span className="pstreak-count"
                          style={{color: canNav ? 'var(--rf-gold)' : 'var(--rf-fg)', fontWeight:700,
                                  textDecoration: canNav ? 'underline dotted' : 'none'}}>
                          {row.name}
                        </span>
                        <span className="pstreak-date">{row.sub}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* ── VIDEOS ── */}
          <div className="profile-videos">
            <div className="profile-section-title">精彩视频 · HIGHLIGHTS</div>

            {videos === null && (
              <div className="pvid-loading">
                <span className="pvid-spinner" />
                搜索「{pname}」视频中…
              </div>
            )}

            {videos !== null && videos.length > 0 && (
              <div className="pvid-grid">
                {videos.map(v => (
                  <a key={v.bvid}
                     className="pvid-card"
                     href={`https://www.bilibili.com/video/${v.bvid}`}
                     target="_blank" rel="noopener">
                    <div className="pvid-thumb">
                      {v.pic
                        ? <img src={v.pic} alt={v.title} />
                        : <span className="pvid-bilibili">B</span>
                      }
                      <span className="pvid-play-btn">▶</span>
                    </div>
                    <div className="pvid-info">
                      <div className="pvid-name">{v.title}</div>
                      <div className="pvid-tag">{v.bvid}</div>
                    </div>
                  </a>
                ))}
              </div>
            )}

            {videos !== null && videos.length === 0 && (
              <div className="pvid-grid">
                {["精彩时刻","进球集锦","助攻集锦","全场回顾"].map((label, i) => (
                  <a key={i} className="pvid-card" href={bUrl} target="_blank" rel="noopener">
                    <div className="pvid-thumb">
                      <span className="pvid-bilibili">B</span>
                      <span className="pvid-play-btn">▶</span>
                    </div>
                    <div className="pvid-info">
                      <div className="pvid-name">{pname}</div>
                      <div className="pvid-tag">{label}</div>
                    </div>
                  </a>
                ))}
              </div>
            )}

            <a className="pvid-more" href={bUrl} target="_blank" rel="noopener">
              在 B 站搜索「{pname}」的全部视频 →
            </a>
          </div>

        </div>
      </div>
    </div>
  );
}

// ---------- ALL-TIME RANKINGS ----------
function AllTimeRankings({ onNavigate }) {
  const [tab, setTab] = useState("goals");
  const tabs = [
    { key: "goals",   label: "⚽ 历史射手榜" },
    { key: "assists", label: "👟 历史助攻榜" },
    { key: "apps",    label: "🏃 历史出场榜" },
    { key: "rating",  label: "⭐ 历史评分榜" },
  ];
  const lists = {
    goals:   (GOALS_ALL   || []),
    assists: (ASSISTS_ALL  || []),
    apps:    (APPS_ALL     || []),
    rating:  (RATINGS_ALL  || []),
  };
  const current = lists[tab];
  return (
    <section className="section" style={{ paddingTop: "24px" }}>
      <div className="container">
        <div className="section__head">
          <div>
            <span className="section__eyebrow">CLUB HISTORY · 俱乐部历史</span>
            <h2 className="section__title">历史榜单 <em>· All-Time Records</em></h2>
          </div>
          <button className="section__cta" onClick={() => onNavigate("home")}>← 返回首页</button>
        </div>
        <div className="atr-tabs">
          {tabs.map(t => (
            <button key={t.key} className={`atr-tab ${tab===t.key?"atr-tab--active":""}`} onClick={() => setTab(t.key)}>{t.label}</button>
          ))}
        </div>
        <div className="atr-table-wrap">
          <table className="season-table atr-table">
            <thead>
              <tr>
                <th style={{width:"40px"}}>排名</th>
                <th style={{textAlign:"left"}}>球员</th>
                <th>号码</th>
                {tab==="goals"   && <><th>进球</th><th>出场</th><th>进球率</th></>}
                {tab==="assists" && <><th>助攻</th><th>出场</th><th>助攻率</th></>}
                {tab==="apps"    && <><th>出场</th><th>总场次</th><th>出场率</th></>}
                {tab==="rating"  && <><th>平均评分</th><th>出场</th><th>门槛</th></>}
              </tr>
            </thead>
            <tbody>
              {current.map((item, i) => {
                const rankLabel = i===0?"🥇":i===1?"🥈":i===2?"🥉":i+1;
                const rankColor = i===0?"var(--rf-gold)":i<3?"var(--rf-fg-2)":"var(--rf-fg-4)";
                const rankW = i<3?700:400;
                const rate = tab==="apps"
                  ? (item.pct || "—")
                  : item.apps > 0 ? (( (item.goals??item.assists??0) / item.apps)).toFixed(2) : "—";
                return (
                  <tr key={i} className={i < 3 ? "atr-row--podium" : ""}>
                    <td style={{textAlign:"center",color:rankColor,fontWeight:rankW}}>{rankLabel}</td>
                    <td style={{textAlign:"left",color:"var(--rf-fg)",fontWeight:rankW}}>{item.name}</td>
                    <td style={{color:"var(--rf-fg-3)"}}>{item.num||"—"}</td>
                    {tab==="goals"   && <><td className="stat-highlight">{item.goals}</td><td>{item.apps}</td><td className="stat-dim">{rate}</td></>}
                    {tab==="assists" && <><td className="stat-highlight">{item.assists}</td><td>{item.apps}</td><td className="stat-dim">{rate}</td></>}
                    {tab==="apps"    && <><td className="stat-highlight">{item.apps}</td><td className="stat-dim">{item.total??480}</td><td className="stat-dim">{item.pct}</td></>}
                    {tab==="rating"  && <><td className="stat-highlight">{item.rating != null ? item.rating.toFixed(2) : "—"}</td><td>{item.apps}</td><td className="stat-dim">&gt;120场</td></>}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

// ---------- MILESTONES ----------
function Milestones() {
  const [showAll, setShowAll] = useState(false);
  const trackRef = useRef(null);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const scrollLeft = useRef(0);

  const all = (MILESTONES || []).slice().reverse(); // newest first, for vertical modal
  const recent = (MILESTONES || []).slice(-18);     // last 18 in chrono order: oldest→left, newest→right

  // Type → icon + colour
  function typeStyle(type) {
    if (type.includes("goals"))   return { icon: "⚽", color: "var(--rf-gold)" };
    if (type.includes("assists")) return { icon: "👟", color: "#60c8ff" };
    return                               { icon: "🏃", color: "#7ddf8e" };
  }
  function formatDate(dateStr) {
    const [y, m, d] = dateStr.split("-");
    return `${y}年${parseInt(m)}月${parseInt(d)}日`;
  }
  function photoSrc(photo) {
    return photo || null;  // photo already contains full "assets/players/..." path
  }

  /* scroll to right end on mount so newest (rightmost) is visible */
  useEffect(() => {
    if (trackRef.current) {
      trackRef.current.scrollLeft = trackRef.current.scrollWidth;
    }
  }, []);

  /* drag-to-scroll */
  function onMouseDown(e) {
    isDragging.current = true;
    startX.current = e.pageX - trackRef.current.offsetLeft;
    scrollLeft.current = trackRef.current.scrollLeft;
    trackRef.current.style.cursor = "grabbing";
  }
  function onMouseMove(e) {
    if (!isDragging.current) return;
    e.preventDefault();
    const x = e.pageX - trackRef.current.offsetLeft;
    trackRef.current.scrollLeft = scrollLeft.current - (x - startX.current);
  }
  function onMouseUp() {
    isDragging.current = false;
    if (trackRef.current) trackRef.current.style.cursor = "grab";
  }

  function MilestoneCard({ m }) {
    const { icon, color } = typeStyle(m.type);
    const src = photoSrc(m.photo);
    return (
      <div className="ms-card">
        <div className="ms-label" style={{ color }}>{icon} {m.label}</div>
        <div className="ms-avatar">
          {src
            ? <img src={src} alt={m.name} />
            : <span className="ms-avatar-initials">{m.name[0]}</span>}
        </div>
        <div className="ms-axis-dot" style={{ background: color }} />
        <div className="ms-date">{formatDate(m.date)}</div>
      </div>
    );
  }

  return (
    <section className="section ms-section">
      <div className="container">
      <div className="section__head">
        <div>
          <span className="section__eyebrow">CLUB HISTORY · 俱乐部历史</span>
          <h2 className="section__title">里程碑 <em>· Milestones</em></h2>
        </div>
        <button className="ms-more-btn" onClick={() => setShowAll(true)}>更多 →</button>
      </div>

      {/* Horizontal drag timeline */}
      <div className="ms-timeline-wrap">
        <div className="ms-axis-line" />
        <div
          className="ms-track"
          ref={trackRef}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
        >
          {recent.map((m, i) => <MilestoneCard key={i} m={m} />)}
        </div>
        <div className="ms-hint">拖动查看更早里程碑 →</div>
      </div>

      </div>{/* /container */}

      {/* Full vertical timeline modal */}
      {showAll && (
        <div className="ms-modal" onClick={e => { if (e.target.classList.contains("ms-modal")) setShowAll(false); }}>
          <div className="ms-modal-panel">
            <div className="ms-modal-head">
              <span>全部里程碑 · ALL MILESTONES</span>
              <button className="ms-modal-close" onClick={() => setShowAll(false)}>✕</button>
            </div>
            <div className="ms-modal-body">
              {all.map((m, i) => {
                const { icon, color } = typeStyle(m.type);
                const src = photoSrc(m.photo);
                const isLeft = i % 2 === 0; // even → content left, date right; odd → date left, content right
                const content = (
                  <div className={`ms-vitem-content ${isLeft ? "ms-vitem-content--l" : "ms-vitem-content--r"}`}>
                    {!!src && <img className="ms-vitem-photo" src={src} alt={m.name} />}
                    <div className="ms-vitem-label" style={{ color }}>{icon} {m.label}</div>
                  </div>
                );
                const dateEl = (
                  <div className={`ms-vitem-datecell ${isLeft ? "ms-vitem-datecell--r" : "ms-vitem-datecell--l"}`}>
                    {formatDate(m.date)}
                  </div>
                );
                return (
                  <div className="ms-vitem" key={i}>
                    {isLeft ? content : dateEl}
                    <div className="ms-vitem-spine">
                      <div className="ms-vitem-dot" style={{ background: color }} />
                      {!!(i < all.length - 1) && <div className="ms-vitem-line" />}
                    </div>
                    {isLeft ? dateEl : content}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

// ---------- FOOTER ----------
function Footer() {
  return (
    <footer className="footer">
      <div className="footer__crest">♛</div>
      <p>ROYAL FARMERS FC · <em>上海皇家农民工足球俱乐部</em></p>
      <p>FOR THE FARMERS · 为农民工而战 · 2020 — 2026</p>
      <p style={{ marginTop: "16px" }}>
        <a href="datacenter.html" style={{ color: "var(--rf-fg-3)", fontSize: "11px", letterSpacing: "0.12em", textDecoration: "none" }}>
          数据中心 → DATA CENTRE
        </a>
      </p>
    </footer>
  );
}

// ---------- CLUB RECORDS 队史纪录 ----------
function ClubRecords() {
  const [tab, setTab] = useState("career");
  const R = RECORDS || {};
  const tabs = [
    { key: "career", label: "🏆 生涯纪录" },
    { key: "season", label: "📅 赛季之最" },
    { key: "match",  label: "⚡ 单场之最" },
    { key: "club",   label: "🏟️ 俱乐部" },
    { key: "streak",    label: "🔥 连续纪录" },
    { key: "allseason", label: "🎖️ 全勤元老" },
  ];
  const isStreak    = tab === "streak";
  const isAllSeason = tab === "allseason";
  const current     = isStreak ? (STREAK_RECORDS || []) : (R[tab] || []);

  return (
    <section className="section cr-section">
      <div className="container">
        <div className="section__head">
          <div>
            <span className="section__eyebrow">CLUB HISTORY · 队史留名</span>
            <h2 className="section__title">队史纪录 <em>· Club Records</em></h2>
          </div>
        </div>

        {/* Tabs */}
        <div className="cr-tabs">
          {tabs.map(t => (
            <button key={t.key}
              className={"cr-tab" + (tab === t.key ? " cr-tab--active" : "")}
              onClick={() => setTab(t.key)}>
              {t.label}
            </button>
          ))}
        </div>

        {/* 全勤元老名录 */}
        {isAllSeason ? (
          <div className="as-section">
            <div className="as-subtitle">六个赛季（2021—2026）从未缺席 · 共 {(ALLSEASON_PLAYERS||[]).length} 人</div>
            <div className="as-grid">
              {(ALLSEASON_PLAYERS || []).map((p, i) => (
                <div key={i} className="as-card">
                  {p.photo
                    ? <img src={p.photo} alt={p.name} className="as-card__photo" />
                    : <div className="as-card__avatar">{p.num || p.name[0]}</div>
                  }
                  <div className="as-card__name">{p.num ? `${p.num}号` : ''}{p.name}</div>
                  <div className="as-card__total">{p.total}场</div>
                  <div className="as-card__bars">
                    {['21','22','23','24','25','26'].map((yr, j) => {
                      const maxApps = Math.max(...(ALLSEASON_PLAYERS||[]).map(x => x.apps[j]));
                      const pct = maxApps > 0 ? Math.round(p.apps[j] / maxApps * 100) : 0;
                      return (
                        <div key={yr} className="as-bar-wrap" title={`20${yr}: ${p.apps[j]}场`}>
                          <div className="as-bar" style={{height: pct + '%'}}></div>
                          <div className="as-bar-label">{yr}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
        /* 普通纪录卡片网格 */
        <div className="cr-grid">
          {current.map((rec, i) => (
            <div key={i} className={"cr-card" + (i === 0 ? " cr-card--gold" : i === 1 ? " cr-card--silver" : i === 2 ? " cr-card--bronze" : "")}>
              <div className="cr-card__icon">{rec.icon}</div>
              <div className="cr-card__label">{rec.label}</div>
              <div className="cr-card__value">
                {rec.value}<span className="cr-card__unit">{rec.unit}</span>
              </div>
              {rec.holder && (
                <div className="cr-card__holder">
                  {rec.photo
                    ? <img src={rec.photo} alt={rec.holder} className="cr-card__photo" />
                    : <div className="cr-card__avatar">{rec.holder[0]}</div>
                  }
                  <span>{rec.num ? `${rec.num}号${rec.holder}` : rec.holder}</span>
                </div>
              )}
              {isStreak && rec.from && (
                <div className="cr-card__daterange">{rec.from} — {rec.to}</div>
              )}
              <div className="cr-card__ctx">{rec.ctx}</div>
            </div>
          ))}
        </div>
        )}
      </div>
    </section>
  );
}

// ════════════════════════════════════════════════════
// PLAYER GROWTH CHART · 球员成长曲线
// ════════════════════════════════════════════════════
function PlayerGrowthChart({ seasons }) {
  const data = (seasons || []).filter(s => (s.apps || 0) > 0);
  if (data.length < 2) return null;

  const W = 320, H = 140;
  const PAD = { t: 16, r: 38, b: 26, l: 36 };
  const cW = W - PAD.l - PAD.r;
  const cH = H - PAD.t - PAD.b;
  const n = data.length;

  const xPos = i => PAD.l + (n < 2 ? cW / 2 : (i / (n - 1)) * cW);
  const maxGA = Math.max(...data.map(s => Math.max(s.goals || 0, s.assists || 0)), 1);
  const yGA   = v => PAD.t + cH - ((v || 0) / maxGA) * cH;
  const ratVals = data.map(s => s.rating).filter(r => r != null);
  const maxR  = Math.max(...ratVals, 3);
  const yR    = v => PAD.t + cH - ((v || 0) / maxR) * cH;

  const pathOf = pts => pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const gPath  = pathOf(data.map((s, i) => [xPos(i), yGA(s.goals || 0)]));
  const aPath  = pathOf(data.map((s, i) => [xPos(i), yGA(s.assists || 0)]));
  const rPts   = data.map((s, i) => s.rating != null ? [xPos(i), yR(s.rating)] : null).filter(Boolean);
  const rPath  = pathOf(rPts);

  const gaTicks = [0, Math.round(maxGA / 2), maxGA];
  const rTick2  = (maxR / 2).toFixed(1);

  return (
    <div className="pgc-wrap">
      <div className="profile-section-title">成长曲线 · Growth Chart</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="pgc-svg">
        {/* Grid */}
        {[0, 0.5, 1].map((t, gi) => (
          <line key={gi}
            x1={PAD.l} x2={W - PAD.r}
            y1={PAD.t + cH * (1 - t)} y2={PAD.t + cH * (1 - t)}
            stroke="#374151" strokeWidth="0.5" />
        ))}
        {/* Left Y (G/A) */}
        {gaTicks.map((v, i) => (
          <text key={i} x={PAD.l - 5} y={yGA(v) + 4} textAnchor="end" fontSize="8.5" fill="#6b7280">{v}</text>
        ))}
        {/* Right Y (Rating) */}
        {[0, rTick2, maxR.toFixed(1)].map((v, i) => (
          <text key={i} x={W - PAD.r + 5} y={yR(parseFloat(v)) + 4} textAnchor="start" fontSize="8.5" fill="#d97706">{v}</text>
        ))}
        {/* Assist line */}
        <path d={aPath} fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinejoin="round" />
        {/* Goals line */}
        <path d={gPath} fill="none" stroke="#f87171" strokeWidth="2" strokeLinejoin="round" />
        {/* Rating dashed */}
        {rPts.length >= 2 && (
          <path d={rPath} fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4,2.5" strokeLinejoin="round" />
        )}
        {/* Dots + year labels */}
        {data.map((s, i) => (
          <g key={s.year}>
            <circle cx={xPos(i)} cy={yGA(s.goals || 0)}    r="3.5" fill="#f87171" stroke="#1f2937" strokeWidth="1.2" />
            <circle cx={xPos(i)} cy={yGA(s.assists || 0)}  r="3.5" fill="#60a5fa" stroke="#1f2937" strokeWidth="1.2" />
            {s.rating != null && (
              <circle cx={xPos(i)} cy={yR(s.rating)} r="3" fill="#f59e0b" stroke="#1f2937" strokeWidth="1.2" />
            )}
            <text x={xPos(i)} y={H - 7} textAnchor="middle" fontSize="9" fill="#9ca3af">{s.year}</text>
          </g>
        ))}
      </svg>
      <div className="pgc-legend">
        <span><span style={{color:'#f87171',fontWeight:700}}>●</span> 进球</span>
        <span><span style={{color:'#60a5fa',fontWeight:700}}>●</span> 助攻</span>
        <span><span style={{color:'#f59e0b',fontWeight:700}}>- -</span> 场均评分</span>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════
// GOLDEN PAIRS · 黄金搭档（全榜 + 各赛季）
// ════════════════════════════════════════════════════
function GoldenPairs({ onPlayerClick }) {
  const GP_TABS = ['总榜', '2026', '2025', '2024', '2023', '2022', '2021'];
  const [tab, setTab] = useState('总榜');

  const allP = useMemo(() => [...(PLAYERS || []), ...Object.values(PLAYER_LOOKUP || {})], []);
  const findP = name => allP.find(p => p.name === name) || null;

  // 从预计算数据 GOLDEN_PAIRS 取当前 tab 数据
  const pairs = useMemo(() => {
    if (!GOLDEN_PAIRS) return [];
    const key = tab === '总榜' ? 'all' : tab;
    return GOLDEN_PAIRS[key] || [];
  }, [tab]);

  if (!GOLDEN_PAIRS) return null;

  const renderAvatar = (name, photo, num) => {
    const p = findP(name);
    const src = photo || (p && p.photo);
    return (
      <div className="gp-avatar" title={name} onClick={() => p && onPlayerClick(p)}>
        {src
          ? <img src={src} alt={name} />
          : <span>{name.slice(0, 1)}</span>}
      </div>
    );
  };

  return (
    <section className="section" id="section-pairs">
      <div className="container">
        <div className="section__head">
          <div>
            <span className="section__eyebrow">DREAM PARTNERS · 进球搭档</span>
            <h2 className="section__title">黄金搭档 <em>· Golden Pairs</em></h2>
          </div>
        </div>

        {/* 赛季 tabs */}
        <div className="atr-tabs" style={{marginBottom:'20px'}}>
          {GP_TABS.map(t => (
            <button key={t}
              className={'atr-tab' + (tab === t ? ' atr-tab--active' : '')}
              onClick={() => setTab(t)}>
              {t === '总榜' ? '总榜 · ALL TIME' : t + ' 赛季'}
            </button>
          ))}
        </div>

        {pairs.length === 0 ? (
          <div style={{color:'var(--rf-fg-3)',fontSize:'13px',padding:'20px 0'}}>暂无数据</div>
        ) : (
          <div className="gp-grid">
            {pairs.map((pair, idx) => (
              <div key={idx} className="gp-card">
                <div className="gp-rank">#{idx + 1}</div>
                <div className="gp-avatars">
                  {renderAvatar(pair.scorer, pair.sPhoto, pair.sNum)}
                  <div className="gp-arrow">⚽</div>
                  {renderAvatar(pair.ast, pair.aPhoto, pair.aNum)}
                </div>
                <div className="gp-names">
                  <span className="gp-scorer">{pair.scorer}</span>
                  <span className="gp-assist-label">👟 传球来自</span>{' '}
                  <span className="gp-assistant">{pair.ast}</span>
                </div>
                <div className="gp-count">{pair.count}<span className="gp-count-sub"> 次</span></div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

// ════════════════════════════════════════════════════
// GLOBAL SEARCH · 全局搜索
// ════════════════════════════════════════════════════
function SearchOverlay({ open, onClose, onPlayerClick }) {
  const [q, setQ] = useState('');
  const inputRef  = useRef(null);

  const allP = useMemo(() =>
    [...(PLAYERS || []), ...Object.values(PLAYER_LOOKUP || {})]
      .filter((p, i, arr) => arr.findIndex(x => x.name === p.name) === i)
  , []);

  const results = useMemo(() => {
    const t = q.trim();
    if (!t) return [];
    return allP.filter(p => p.name.includes(t)).slice(0, 8);
  }, [q, allP]);

  useEffect(() => {
    if (open) { setQ(''); setTimeout(() => inputRef.current && inputRef.current.focus(), 60); }
  }, [open]);

  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!open) return null;

  const pick = p => { onPlayerClick(p); onClose(); };

  const handleKey = e => {
    if (e.key === 'Enter' && results.length > 0) pick(results[0]);
  };

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-panel" onClick={e => e.stopPropagation()}>
        <div className="search-input-wrap">
          <span className="search-input-icon">🔍</span>
          <input
            ref={inputRef}
            className="search-input"
            placeholder="搜索球员姓名…"
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={handleKey}
            autoComplete="off"
          />
          <kbd className="search-esc" onClick={onClose}>ESC</kbd>
        </div>

        {q.trim().length === 0 && (
          <div className="search-hint">
            支持 {allP.length} 名注册球员 · 输入名字搜索 · <kbd style={{background:'#374151',border:'1px solid #4b5563',borderRadius:'3px',padding:'1px 5px',fontSize:'11px'}}>Enter</kbd> 直接打开
          </div>
        )}

        {q.trim().length > 0 && results.length === 0 && (
          <div className="search-empty">没有找到「{q}」</div>
        )}

        {results.length > 0 && (
          <div className="search-results">
            {results.map((p, i) => (
              <div key={i} className="search-item" onClick={() => pick(p)}>
                <div className="search-item-photo">
                  {p.photo
                    ? <img src={p.photo} alt={p.name} />
                    : <span>#{p.num || '?'}</span>}
                </div>
                <div className="search-item-info">
                  <div className="search-item-name">{p.name}</div>
                  <div className="search-item-meta">
                    {p.num ? `#${p.num} · ` : ''}{p.pos || '—'}
                  </div>
                </div>
                <div className="search-item-stats">
                  <span>{(p.apps || 0).toLocaleString()} 场</span>
                  <span>{(p.goals || 0)} 球</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════
// SEASON SUMMARY · 赛季总结（支持全部赛季）
// ════════════════════════════════════════════════════
const RATINGS_MAP = {
  '2026': RATINGS_2026, '2025': RATINGS_2025, '2024': RATINGS_2024,
  '2023': RATINGS_2023, '2022': RATINGS_2022, '2021': RATINGS_2021,
};
const SS_YEARS = ['2026','2025','2024','2023','2022','2021'];

function SeasonSummary({ onNavigate, onPlayerClick, initYear }) {
  const [year, setYear] = useState(initYear || '2026');

  const allP = useMemo(() =>
    [...(PLAYERS || []), ...Object.values(PLAYER_LOOKUP || {})]
      .filter((p, i, arr) => arr.findIndex(x => x.name === p.name) === i)
  , []);
  const findP = name => allP.find(p => p.name === name) || null;

  // ── 战绩 KPI（来自预计算 SEASON_MATCH_STATS）──
  const ms = (SEASON_MATCH_STATS || {})[year] || {};
  const matchStats = {
    total: ms.total || 0,
    w: ms.w || 0, d: ms.d || 0, l: ms.l || 0,
    gf: ms.gf || 0, ga: ms.ga || 0,
    avgGF: ms.avgGF || '—',
  };

  // ── 三王（从 PLAYERS+PLAYER_LOOKUP seasons 动态计算）──
  const kings = useMemo(() => {
    const sdata = allP
      .map(p => {
        const s = (p.seasons || []).find(s => s.year === year);
        return s && s.apps > 0
          ? { name: p.name, num: p.num, photo: p.photo || null,
              goals: s.goals || 0, assists: s.assists || 0, apps: s.apps || 0 }
          : null;
      })
      .filter(Boolean);
    const top = (arr, key) => [...arr].sort((a, b) => b[key] - a[key])[0];
    return {
      goals:   top(sdata, 'goals'),
      assists: top(sdata, 'assists'),
      apps:    top(sdata, 'apps'),
    };
  }, [year, allP]);

  // ── 评分最佳11人 ──
  const rat = useMemo(() => (RATINGS_MAP[year] || []).slice(0, 11), [year]);

  // ── 里程碑 ──
  const milestones = useMemo(() =>
    (MILESTONES || []).filter(m => m.date && m.date.startsWith(year))
  , [year]);

  // ── 最大胜场（仅 2026 有 FIXTURES 详情）──
  const bigWins = useMemo(() => {
    if (year !== '2026') return [];
    return (FIXTURES || [])
      .filter(m => {
        const hRF = (m.home || '').includes('Royal Farmers');
        const aRF = (m.away || '').includes('Royal Farmers');
        return (hRF || aRF) && !(hRF && aRF);
      })
      .map(m => {
        const hRF = (m.home || '').includes('Royal Farmers');
        const rf = hRF ? (m.homeScore||0) : (m.awayScore||0);
        const op = hRF ? (m.awayScore||0) : (m.homeScore||0);
        return { date:m.date, rf, op, margin:rf-op, opp: hRF?(m.away||'?'):(m.home||'?') };
      })
      .filter(x => x.margin > 0)
      .sort((a, b) => b.margin - a.margin)
      .slice(0, 3);
  }, [year]);

  // ── 新面孔（第一个有效赛季 = 当前年份）──
  const newcomers = useMemo(() =>
    allP.filter(p => {
      const active = (p.seasons || []).filter(s => (s.apps||0) > 0 || (s.goals||0) > 0);
      if (!active.length) return false;
      const firstYr = active.reduce((mn, s) => s.year < mn ? s.year : mn, active[0].year);
      return firstYr === year;
    }).slice(0, 12)
  , [year, allP]);

  const KING_DEF = [
    { key:'goals',   icon:'⚽', label:'金靴 Golden Boot',  fmt: d => `${d.goals} 球`   },
    { key:'assists', icon:'👟', label:'金助 Golden Glove', fmt: d => `${d.assists} 次` },
    { key:'apps',    icon:'🏃', label:'出勤王 Iron Man',   fmt: d => `${d.apps} 场`    },
  ];

  return (
    <div className="ss-page">
      <div className="container">
        <div className="ss-nav">
          <button className="section__cta" onClick={() => onNavigate('home')}>← 返回首页</button>
        </div>

        <div className="ss-header">
          <span className="section__eyebrow">SEASON IN REVIEW · 赛季回顾</span>
          <h1 className="ss-title">{year} 赛季总结 <em>· Season Review</em></h1>
        </div>

        {/* 赛季切换 tabs */}
        <div className="atr-tabs" style={{marginBottom:'28px'}}>
          {SS_YEARS.map(y => (
            <button key={y}
              className={'atr-tab' + (y === year ? ' atr-tab--active' : '')}
              onClick={() => setYear(y)}>
              {y}
            </button>
          ))}
        </div>

        {/* KPI 快报 */}
        <div className="ss-kpi-row">
          <div className="ss-kpi"><b>{matchStats.total}</b><span>外部对战</span></div>
          <div className="ss-kpi ss-kpi--win"><b>{matchStats.w}</b><span>胜</span></div>
          <div className="ss-kpi ss-kpi--draw"><b>{matchStats.d}</b><span>平</span></div>
          <div className="ss-kpi ss-kpi--loss"><b>{matchStats.l}</b><span>负</span></div>
          <div className="ss-kpi"><b>{matchStats.gf}</b><span>进球</span></div>
          <div className="ss-kpi"><b>{matchStats.avgGF}</b><span>场均进</span></div>
        </div>

        {/* 赛季三王 */}
        <div className="ss-section">
          <div className="ss-section-title">⚽ 赛季三王 · Season Awards</div>
          <div className="ss-three-kings">
            {KING_DEF.map(def => {
              const d = kings[def.key];
              if (!d) return null;
              const p = findP(d.name);
              return (
                <div key={def.key} className="ss-king-card" onClick={() => p && onPlayerClick(p)}>
                  <div className="ss-king-icon">{def.icon}</div>
                  <div className="ss-king-label">{def.label}</div>
                  {(d.photo || (p && p.photo)) &&
                    <img className="ss-king-photo" src={d.photo || p.photo} alt={d.name} />}
                  <div className="ss-king-name">#{d.num || '?'} {d.name}</div>
                  <div className="ss-king-val">{def.fmt(d)}</div>
                </div>
              );
            })}
          </div>
          <p className="ss-note">* 仅统计 PLAYERS 和 PLAYER_LOOKUP 中有逐赛季数据的球员</p>
        </div>

        {/* 评分最佳11人 */}
        {rat.length > 0 && (
          <div className="ss-section">
            <div className="ss-section-title">⭐ 评分最佳11人 · Season Best XI</div>
            <div className="ss-xi-list">
              {rat.map((r, i) => {
                const p = findP(r.name);
                return (
                  <div key={i} className="ss-xi-row" onClick={() => p && onPlayerClick(p)}>
                    <span className="ss-xi-rank">{i + 1}</span>
                    {r.photo
                      ? <img className="ss-xi-photo" src={r.photo} alt={r.name} />
                      : <div className="ss-xi-photo" style={{background:'#374151',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'12px',color:'#9ca3af'}}>#{r.num}</div>
                    }
                    <div className="ss-xi-info">
                      <span className="ss-xi-name">#{r.num} {r.name}</span>
                      <span className="ss-xi-apps">{r.apps} 场</span>
                    </div>
                    <div className="ss-xi-rating">{Number(r.rating).toFixed(2)}</div>
                  </div>
                );
              })}
            </div>
            <p className="ss-note">* 出场场次 ≥ 赛季总场次 × 25% 方可入选</p>
          </div>
        )}

        {/* 最大胜场（仅2026）*/}
        {bigWins.length > 0 && (
          <div className="ss-section">
            <div className="ss-section-title">💪 最大胜场 · Biggest Wins</div>
            <div className="ss-wins-list">
              {bigWins.map((w, i) => (
                <div key={i} className="ss-win-row">
                  <span className="ss-win-date">{w.date}</span>
                  <span className="ss-win-score">{w.rf} — {w.op}</span>
                  <span className="ss-win-opp">vs {w.opp}</span>
                  <span className="ss-win-margin">+{w.margin}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 赛季里程碑 */}
        {milestones.length > 0 && (
          <div className="ss-section">
            <div className="ss-section-title">🏅 赛季里程碑 · Season Milestones</div>
            <div className="ss-milestone-list">
              {milestones.map((m, i) => (
                <div key={i} className="ss-milestone-row">
                  <span className="ss-ms-date">{m.date}</span>
                  <span className="ss-ms-label">{m.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 赛季新面孔 */}
        {newcomers.length > 0 && (
          <div className="ss-section">
            <div className="ss-section-title">✨ 赛季新面孔 · New Faces</div>
            <div className="ss-newcomers">
              {newcomers.map((p, i) => (
                <div key={i} className="ss-newcomer" onClick={() => onPlayerClick(p)}>
                  {p.photo
                    ? <img src={p.photo} alt={p.name} />
                    : <div className="ss-newcomer-initial">{p.name.slice(0, 1)}</div>}
                  <span>{p.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════
// MATCH DETAIL MODAL · 比赛详情弹窗
// ════════════════════════════════════════════════════
function MatchDetailModal({ match, onClose, onPlayerClick }) {
  useEffect(() => {
    const h = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', h);
    document.body.style.overflow = match ? 'hidden' : '';
    return () => { window.removeEventListener('keydown', h); document.body.style.overflow = ''; };
  }, [match, onClose]);

  if (!match) return null;

  const allP = [...(PLAYERS||[]), ...Object.values(PLAYER_LOOKUP||{})];
  const findP = name => allP.find(p => p.name === name) || null;
  const pickPlayer = name => { const p = findP(name); if (p) { onPlayerClick(p); onClose(); } };

  const { home='', away='', homeScore=0, awayScore=0, date='', comp='', venue='',
          result='', homeScorers=[], homeAssists=[], awayScorers=[], awayAssists=[] } = match;

  const resultLabel = { W:'胜', D:'平', L:'负' }[result] || '';
  const resultCls   = { W:'mdetail-result-badge--w', D:'mdetail-result-badge--d', L:'mdetail-result-badge--l' }[result] || '';

  const GoalList = ({ scorers, assists }) => {
    if (!scorers.length) return <div className="mdetail-nil">—</div>;
    return scorers.map((sc, i) => {
      const ast = assists[i] || '';
      const showAst = ast && ast !== '?' && ast !== '/';
      return (
        <div key={i} className="mdetail-goal-row">
          <span className="mdetail-goal-ico">⚽</span>
          <span className="mdetail-goal-name" onClick={() => pickPlayer(sc)}>{sc}</span>
          {showAst && <>
            <span style={{color:'var(--rf-fg-3)',fontSize:'10px'}}>👟</span>
            <span className="mdetail-assist-name" onClick={() => pickPlayer(ast)}>{ast}</span>
          </>}
        </div>
      );
    });
  };

  return (
    <div className="mdetail-overlay" onClick={onClose}>
      <div className="mdetail-panel" onClick={e => e.stopPropagation()}>
        <div className="mdetail-head">
          <div className="mdetail-meta">
            <span>{date}</span>
            <span>{comp}</span>
            {venue && <span>📍 {venue}</span>}
          </div>
          <button className="mdetail-close" onClick={onClose}>×</button>
        </div>

        <div className="mdetail-score-row">
          <div className="mdetail-team">
            <div className="mdetail-team-name">{home}</div>
            {result && <div className={`mdetail-result-badge ${resultCls}`}>{resultLabel}</div>}
          </div>
          <div className="mdetail-score">
            {homeScore}<span className="mdetail-score-sep"> — </span>{awayScore}
          </div>
          <div className="mdetail-team">
            <div className="mdetail-team-name">{away}</div>
          </div>
        </div>

        <div className="mdetail-goals">
          <div className="mdetail-side">
            <div className="mdetail-side-title">{home} · 进球</div>
            <GoalList scorers={homeScorers} assists={homeAssists} />
          </div>
          <div className="mdetail-side" style={{borderLeft:'1px solid var(--rf-line)'}}>
            <div className="mdetail-side-title">{away} · 进球</div>
            <GoalList scorers={awayScorers} assists={awayAssists} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════
// PLAYER COMPARE · 球员对比
// ════════════════════════════════════════════════════
function PlayerCompare({ onNavigate, initP1, initP2 }) {
  const [p1, setP1] = useState(initP1 || null);
  const [p2, setP2] = useState(initP2 || null);
  const [picking, setPicking] = useState(null); // 'p1' | 'p2' | null
  const [q, setQ] = useState('');
  const searchRef = useRef(null);

  const allP = useMemo(() =>
    [...(PLAYERS||[]), ...Object.values(PLAYER_LOOKUP||{})]
      .filter((p, i, arr) => arr.findIndex(x => x.name === p.name) === i)
  , []);

  const results = useMemo(() => {
    const t = q.trim();
    if (!t) return [];
    return allP.filter(p => p.name.includes(t)).slice(0, 6);
  }, [q, allP]);

  useEffect(() => {
    if (picking && searchRef.current) { setQ(''); setTimeout(() => searchRef.current?.focus(), 60); }
  }, [picking]);

  const pick = (p) => {
    if (picking === 'p1') setP1(p);
    if (picking === 'p2') setP2(p);
    setPicking(null);
  };

  // ── 雷达图数据 ──
  const DIMS = [
    { key:'goals',   label:'进球',   get: p => p.goals   || 0 },
    { key:'assists', label:'助攻',   get: p => p.assists  || 0 },
    { key:'apps',    label:'出场',   get: p => p.apps     || 0 },
    { key:'rating',  label:'评分',   get: p => { const r = weightedRating(p.seasons); return r != null ? r : 0; } },
    { key:'gpg',     label:'进球/场', get: p => p.apps > 0 ? p.goals/p.apps : 0 },
    { key:'apg',     label:'助攻/场', get: p => p.apps > 0 ? p.assists/p.apps : 0 },
  ];

  const maxPerDim = useMemo(() =>
    DIMS.map(d => Math.max(...allP.map(p => d.get(p)), 0.01))
  , [allP]);

  const normalize = (p, dimIdx) => Math.min(1, DIMS[dimIdx].get(p) / maxPerDim[dimIdx]);

  // SVG hexagonal radar
  const RadarChart = ({ player1, player2 }) => {
    if (!player1 && !player2) return null;
    const R = 110, cx = 140, cy = 130;
    const angle = i => (Math.PI * 2 * i / 6) - Math.PI / 2;
    const pt = (i, r) => [cx + Math.cos(angle(i)) * r, cy + Math.sin(angle(i)) * r];

    const hexPts = DIMS.map((_, i) => pt(i, R).join(',')).join(' ');

    const playerPoly = p => DIMS.map((_, i) => pt(i, normalize(p, i) * R).join(',')).join(' ');

    const COLORS = ['#f87171','#60a5fa'];

    return (
      <div className="pc-radar-wrap">
        <svg viewBox="0 0 280 260" className="pc-radar-svg">
          {/* Grid rings */}
          {[0.25,0.5,0.75,1].map((r, gi) => (
            <polygon key={gi}
              points={DIMS.map((_,i) => pt(i, R*r).join(',')).join(' ')}
              fill="none" stroke="#374151" strokeWidth={gi===3?1:0.5} />
          ))}
          {/* Axes */}
          {DIMS.map((d, i) => {
            const [x,y] = pt(i, R);
            const [lx,ly] = pt(i, R+22);
            return (
              <g key={i}>
                <line x1={cx} y1={cy} x2={x} y2={y} stroke="#374151" strokeWidth="0.5"/>
                <text x={lx} y={ly} textAnchor="middle" dominantBaseline="central"
                  fontSize="10" fill="#6b7280" fontWeight="600">{d.label}</text>
              </g>
            );
          })}
          {/* Player polygons */}
          {[player2, player1].map((p, pi) => p ? (
            <polygon key={pi} points={playerPoly(p)}
              fill={COLORS[1-pi]} fillOpacity="0.25"
              stroke={COLORS[1-pi]} strokeWidth="2" strokeLinejoin="round"/>
          ) : null)}
          {/* Player dots */}
          {[player1, player2].map((p, pi) => p
            ? DIMS.map((_, i) => { const [x,y] = pt(i, normalize(p, i)*R); return (
              <circle key={i} cx={x} cy={y} r="4" fill={COLORS[pi]} stroke="#1f2937" strokeWidth="1.5"/>
            ); }) : null
          )}
        </svg>
        {/* Legend */}
        {(player1 || player2) && (
          <div style={{display:'flex',gap:'16px',justifyContent:'center',fontSize:'12px',marginTop:'-4px'}}>
            {player1 && <span><span style={{color:'#f87171',fontWeight:700}}>●</span> {player1.name}</span>}
            {player2 && <span><span style={{color:'#60a5fa',fontWeight:700}}>●</span> {player2.name}</span>}
          </div>
        )}
      </div>
    );
  };

  // 各维度对比行
  const StatRow = ({ label, v1, v2, fmt = v => v }) => {
    const best = v1 > v2 ? 'p1' : v2 > v1 ? 'p2' : null;
    const max = Math.max(v1, v2, 0.01);
    return (
      <div className="pc-stat-row">
        <div className={`pc-stat-val pc-stat-val--p1 ${best==='p1'?'pc-stat-val--best':''}`}>{p1 ? fmt(v1) : '—'}</div>
        <div className="pc-stat-label">{label}</div>
        <div className={`pc-stat-val pc-stat-val--p2 ${best==='p2'?'pc-stat-val--best':''}`}>{p2 ? fmt(v2) : '—'}</div>
      </div>
    );
  };

  // 逐赛季对比表
  const allYears = useMemo(() => {
    const ys = new Set();
    [(p1||{}).seasons||[], (p2||{}).seasons||[]].forEach(ss => ss.forEach(s => ys.add(s.year)));
    return [...ys].sort((a,b) => b.localeCompare(a));
  }, [p1, p2]);

  const getSeason = (p, yr) => (p?.seasons||[]).find(s => s.year === yr);

  // 内联选球员 panel（不能定义为子组件，否则每次 q 变化都会 unmount/remount 导致 IME 输入报错）
  const renderSelector = (p, slot) => (
    <div className={`pc-selector ${p?'pc-selector--filled':''}`} onClick={() => setPicking(slot)}>
      {p ? (
        <>
          {p.photo
            ? <img className="pc-selector-photo" src={p.photo} alt={p.name}/>
            : <div className="pc-selector-num-badge">#{p.num||'?'}</div>}
          <div className="pc-selector-name">{p.name}</div>
          <div className="pc-selector-meta">#{p.num} · {p.pos||'—'} · {p.apps||0}场</div>
          <span className="pc-selector-change">更换球员</span>
        </>
      ) : (
        <div className="pc-selector-prompt">
          <div style={{fontSize:'28px',marginBottom:'6px'}}>＋</div>
          <div>点击选择{slot==='p1'?'球员一':'球员二'}</div>
        </div>
      )}
    </div>
  );

  return (
    <div className="pc-page">
      {/* 搜索面板：内联 JSX 而非子组件，避免 q 变化时 unmount/remount 破坏 IME 输入 */}
      {picking && (
        <div className="search-overlay" onClick={() => setPicking(null)}>
          <div className="search-panel" onClick={e => e.stopPropagation()}>
            <div className="search-input-wrap">
              <span className="search-input-icon">🔍</span>
              <input ref={searchRef} className="search-input"
                placeholder={`选择${picking==='p1'?'球员一':'球员二'}…`}
                value={q} onChange={e => setQ(e.target.value)} autoComplete="off" />
              <kbd className="search-esc" onClick={() => setPicking(null)}>ESC</kbd>
            </div>
            {q && results.length === 0 && <div className="search-empty">没有找到「{q}」</div>}
            {!q && <div className="search-hint">输入名字搜索球员</div>}
            {results.length > 0 && (
              <div className="search-results">
                {results.map((p, i) => (
                  <div key={i} className="search-item" onClick={() => pick(p)}>
                    <div className="search-item-photo">
                      {p.photo ? <img src={p.photo} alt={p.name}/> : <span>#{p.num||'?'}</span>}
                    </div>
                    <div className="search-item-info">
                      <div className="search-item-name">{p.name}</div>
                      <div className="search-item-meta">{p.num?`#${p.num} · `:''}{p.pos||'—'}</div>
                    </div>
                    <div className="search-item-stats">
                      <span>{p.apps||0} 场</span><span>{p.goals||0} 球</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      <div className="container">
        <div className="pc-nav">
          <button className="section__cta" onClick={() => onNavigate('home')}>← 返回首页</button>
        </div>
        <div className="pc-header">
          <span className="section__eyebrow">PLAYER COMPARISON · 球员对比</span>
          <h1 className="pc-title">球员对比 <em>· Head to Head</em></h1>
        </div>

        {/* 选择球员 */}
        <div className="pc-selectors">
          {renderSelector(p1, 'p1')}
          {renderSelector(p2, 'p2')}
        </div>

        {/* 雷达图 */}
        {(p1 || p2) && <RadarChart player1={p1} player2={p2} />}

        {/* 核心数据对比 */}
        {(p1 || p2) && (
          <div className="pc-stats-section">
            <div className="pc-stats-title">生涯核心数据 · Career Stats</div>
            <StatRow label="进球" v1={p1?.goals||0} v2={p2?.goals||0} />
            <StatRow label="助攻" v1={p1?.assists||0} v2={p2?.assists||0} />
            <StatRow label="出场" v1={p1?.apps||0} v2={p2?.apps||0} />
            <StatRow label="场均进球" v1={p1?.apps>0?(p1.goals/p1.apps):0} v2={p2?.apps>0?(p2.goals/p2.apps):0} fmt={v=>v.toFixed(2)} />
            <StatRow label="场均助攻" v1={p1?.apps>0?(p1.assists/p1.apps):0} v2={p2?.apps>0?(p2.assists/p2.apps):0} fmt={v=>v.toFixed(2)} />
            <StatRow label="生涯评分" v1={weightedRating(p1?.seasons)||0} v2={weightedRating(p2?.seasons)||0} fmt={v=>v.toFixed(2)} />
          </div>
        )}

        {/* 逐赛季对比 */}
        {(p1 || p2) && allYears.length > 0 && (
          <div className="pc-stats-section">
            <div className="pc-stats-title">逐赛季对比 · Season by Season</div>
            <div style={{overflowX:'auto'}}>
              <table className="pc-season-table">
                <thead>
                  <tr>
                    <th>赛季</th>
                    <th>{p1?.name||'—'} G</th>
                    <th>{p2?.name||'—'} G</th>
                    <th>{p1?.name||'—'} A</th>
                    <th>{p2?.name||'—'} A</th>
                    <th>{p1?.name||'—'} 评分</th>
                    <th>{p2?.name||'—'} 评分</th>
                  </tr>
                </thead>
                <tbody>
                  {allYears.map(yr => {
                    const s1 = getSeason(p1, yr);
                    const s2 = getSeason(p2, yr);
                    const g1 = s1?.goals||0, g2 = s2?.goals||0;
                    const a1 = s1?.assists||0, a2 = s2?.assists||0;
                    const r1 = s1?.rating, r2 = s2?.rating;
                    return (
                      <tr key={yr}>
                        <td className="pc-td-year">{yr}</td>
                        <td className={g1>g2?'pc-td-best':''}>{s1?g1:'—'}</td>
                        <td className={g2>g1?'pc-td-best':''}>{s2?g2:'—'}</td>
                        <td className={a1>a2?'pc-td-best':''}>{s1?a1:'—'}</td>
                        <td className={a2>a1?'pc-td-best':''}>{s2?a2:'—'}</td>
                        <td className={r1!=null&&r2!=null&&r1>r2?'pc-td-best':''}>{r1!=null?r1.toFixed(2):'—'}</td>
                        <td className={r2!=null&&r1!=null&&r2>r1?'pc-td-best':''}>{r2!=null?r2.toFixed(2):'—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!p1 && !p2 && (
          <div style={{textAlign:'center',padding:'40px 20px',color:'var(--rf-fg-3)',fontSize:'14px'}}>
            选择两位球员开始对比 · 支持 {allP.length} 名注册球员
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════
// BEST COMBOS · 最佳组合（主榜 + 自由组合）
// ════════════════════════════════════════════════════
function LineupAnalytics({ onPlayerClick }) {
  const [tab,  setTab]  = useState('rank');   // 'rank' | 'free'
  const [sort, setSort] = useState('rate');   // 'apps' | 'rate'

  // 自由组合状态：最多3人
  const [combo, setCombo] = useState([]);     // [{name, photo, num}, ...]
  const [freeQ, setFreeQ] = useState('');
  const freeInputRef = useRef(null);

  const allP = useMemo(() => [...(PLAYERS||[]), ...Object.values(PLAYER_LOOKUP||{})], []);
  const findP = name => allP.find(p => p.name === name) || null;
  const fmtRate = r => (r * 100).toFixed(0) + '%';

  // 主榜排序
  const sorted = useMemo(() => {
    if (!LINEUP_STATS) return [];
    return [...LINEUP_STATS].sort((a, b) => sort === 'apps' ? b.apps - a.apps : b.rate - a.rate);
  }, [sort]);

  // 自由组合搜索候选
  const freeCandidates = useMemo(() => {
    const t = freeQ.trim();
    if (!t) return [];
    return allP.filter(p => p.name.includes(t) && !combo.find(c => c.name === p.name)).slice(0, 6);
  }, [freeQ, combo, allP]);

  // 自由组合：计算2人或3人的共同出场统计
  const comboStats = useMemo(() => {
    if (combo.length < 2) return null;
    const names = combo.map(c => c.name);

    if (names.length === 2) {
      // 2人：从 LINEUP_ALL 直接查
      if (!LINEUP_ALL) return null;
      const [a, b] = [names[0], names[1]].sort();
      const key = `${a}|${b}`;
      return LINEUP_ALL[key] || null;
    }

    if (names.length === 3) {
      // 3人：从 MATCH_DATA 字符串逐场计算
      // ⚠️ 三人同一天都有出场分数，仅说明三人都出勤了——不代表同队！
      // 内部三队赛/对内两队赛中，三人很可能被分到不同队，各自分数不同。
      // 只有"三人当天分数完全相同"才能确认三人同队，此时才计入"共同出场"，
      // 分数=3 才计入"共同获胜"。
      if (!MATCH_DATA) return null;
      const [s1, s2, s3] = names.map(n => MATCH_DATA[n] || '');
      if (!s1 || !s2 || !s3) return null;
      const len = Math.min(s1.length, s2.length, s3.length);
      let apps = 0, wins = 0;
      for (let i = 0; i < len; i++) {
        const c1 = s1[i], c2 = s2[i], c3 = s3[i];
        if (c1 !== ' ' && c1 === c2 && c2 === c3) {
          apps++;
          if (c1 === '3') wins++;
        }
      }
      return apps > 0 ? { apps, wins, rate: wins / apps } : null;
    }
    return null;
  }, [combo]);

  const addToCombo = p => {
    if (combo.length >= 3 || combo.find(c => c.name === p.name)) return;
    setCombo(prev => [...prev, { name: p.name, photo: p.photo || null, num: p.num || '' }]);
    setFreeQ('');
  };
  const removeFromCombo = name => setCombo(prev => prev.filter(c => c.name !== name));

  const renderAvatar = (name, ph, num, removable) => (
    <div key={name} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:'4px'}}>
      <div className="lu-avatar" style={{width:'52px',height:'52px',position:'relative',cursor: removable ? 'pointer' : undefined}}
        title={removable ? '点击移除' : undefined}
        onClick={() => { if (removable) { removeFromCombo(name); return; } const p = findP(name); if (p) onPlayerClick(p); }}>
        {ph ? <img src={ph} alt={name}/> : <span style={{fontSize:'16px'}}>{name.slice(0,1)}</span>}
        {removable && (
          <span style={{position:'absolute',top:'-6px',right:'-6px',width:'18px',height:'18px',
                    borderRadius:'50%',background:'#374151',border:'1px solid #4b5563',
                    color:'#9ca3af',fontSize:'12px',pointerEvents:'none',display:'flex',
                    alignItems:'center',justifyContent:'center',lineHeight:1}}>×</span>
        )}
      </div>
      <span style={{fontSize:'11px',color:'var(--rf-fg-2)',fontWeight:600,maxWidth:'56px',
                    textAlign:'center',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
        {name}
      </span>
    </div>
  );

  return (
    <section className="section" id="section-lineup">
      <div className="container">
        <div className="section__head">
          <div>
            <span className="section__eyebrow">BEST COMBOS · 组合分析</span>
            <h2 className="section__title">最佳组合 <em>· Best Combos</em></h2>
          </div>
        </div>

        {/* 主 tabs */}
        <div className="atr-tabs" style={{marginBottom:'20px'}}>
          <button className={`atr-tab ${tab==='rank'?'atr-tab--active':''}`} onClick={() => setTab('rank')}>榜单 · Rankings</button>
          <button className={`atr-tab ${tab==='free'?'atr-tab--active':''}`} onClick={() => setTab('free')}>自由组合 · Free Combo</button>
        </div>

        {/* ── 榜单 tab ── */}
        {tab === 'rank' && (
          <>
            <div className="lu-controls">
              <button className={`lu-sort-btn ${sort==='rate'?'lu-sort-btn--active':''}`} onClick={() => setSort('rate')}>按胜率 ↓</button>
              <button className={`lu-sort-btn ${sort==='apps'?'lu-sort-btn--active':''}`} onClick={() => setSort('apps')}>按共同出场 ↓</button>
            </div>
            <div className="lu-grid">
              {sorted.slice(0, 12).map((row, idx) => {
                const getSrc = (ph, name) => ph || findP(name)?.photo || null;
                const renderAv = (name, src) => (
                  <div className="lu-avatar" onClick={() => { const p=findP(name); if(p) onPlayerClick(p); }}>
                    {src ? <img src={src} alt={name}/> : <span>{name.slice(0,1)}</span>}
                  </div>
                );
                return (
                  <div key={idx} className="lu-card">
                    <div className="lu-rank">#{idx+1}</div>
                    <div className="lu-avatars">
                      {renderAv(row.p1, getSrc(row.p1ph, row.p1))}
                      <div className="lu-plus">+</div>
                      {renderAv(row.p2, getSrc(row.p2ph, row.p2))}
                    </div>
                    <div className="lu-names">
                      <span>{row.p1}</span><em>+</em><span>{row.p2}</span>
                    </div>
                    <div className="lu-win-rate">{fmtRate(row.rate)}</div>
                    <div className="lu-apps">{row.apps} 场 · {row.wins} 胜</div>
                  </div>
                );
              })}
            </div>
            <p style={{fontSize:'11px',color:'var(--rf-fg-3)',marginTop:'12px'}}>
              * 仅统计可确认"同队出场"的场次（当天两人战绩分数一致）≥ 20 场方可入榜；内部赛中双方分到不同队的场次不计入
            </p>
          </>
        )}

        {/* ── 自由组合 tab ── */}
        {tab === 'free' && (
          <div>
            {/* 已选球员 + 搜索 */}
            <div style={{display:'flex',alignItems:'flex-end',gap:'16px',flexWrap:'wrap',marginBottom:'20px'}}>
              <div style={{display:'flex',gap:'12px',alignItems:'flex-end'}}>
                {combo.map(c => renderAvatar(c.name, c.photo, c.num, true))}
                {combo.length < 3 && (
                  <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:'4px'}}>
                    <div className="pc-selector" style={{width:'52px',height:'52px',borderRadius:'50%',
                      minHeight:'unset',padding:'0',fontSize:'22px',cursor:'text'}}
                      onClick={() => freeInputRef.current?.focus()}>
                      ＋
                    </div>
                    <span style={{fontSize:'10px',color:'var(--rf-fg-3)'}}>添加</span>
                  </div>
                )}
              </div>
              {combo.length < 3 && (
                <div className="lu-search-wrap" style={{flex:'1',minWidth:'180px',maxWidth:'280px'}}>
                  <span className="lu-search-icon">🔍</span>
                  <input ref={freeInputRef} className="lu-search-input"
                    placeholder={`搜索第 ${combo.length+1} 名球员…`}
                    value={freeQ} onChange={e => setFreeQ(e.target.value)} />
                </div>
              )}
              {combo.length > 0 && (
                <button className="lu-sort-btn" onClick={() => { setCombo([]); setFreeQ(''); }}>清空</button>
              )}
            </div>

            {/* 候选结果 */}
            {freeCandidates.length > 0 && (
              <div style={{background:'var(--rf-graphite-2)',border:'1px solid var(--rf-line-strong)',
                          borderRadius:'var(--rf-r)',marginBottom:'16px',overflow:'hidden'}}>
                {freeCandidates.map((p, i) => (
                  <div key={i} className="search-item" style={{padding:'8px 14px'}}
                    onClick={() => addToCombo(p)}>
                    <div className="search-item-photo">
                      {p.photo ? <img src={p.photo} alt={p.name}/> : <span>#{p.num||'?'}</span>}
                    </div>
                    <div className="search-item-info">
                      <div className="search-item-name">{p.name}</div>
                      <div className="search-item-meta">{p.num?`#${p.num} · `:''}{p.pos||'—'}</div>
                    </div>
                    <div className="search-item-stats">
                      <span>{p.apps||0} 场</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 组合统计结果 */}
            {combo.length >= 2 && (
              <div style={{background:'var(--rf-graphite-2)',border:'1px solid var(--rf-gold)',
                          borderRadius:'var(--rf-r)',padding:'24px',textAlign:'center',marginTop:'8px'}}>
                <div style={{fontSize:'12px',color:'var(--rf-fg-3)',marginBottom:'8px',letterSpacing:'0.08em',textTransform:'uppercase'}}>
                  {combo.map(c=>c.name).join(' + ')} · 同队出场统计
                </div>
                {comboStats ? (
                  <>
                    <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'16px',marginBottom:'12px'}}>
                      <div><b style={{fontSize:'36px',fontWeight:900,color:'var(--rf-gold)',letterSpacing:'-0.04em',display:'block'}}>{comboStats.apps}</b><span style={{fontSize:'11px',color:'var(--rf-fg-3)',fontWeight:700,textTransform:'uppercase'}}>同队出场</span></div>
                      <div><b style={{fontSize:'36px',fontWeight:900,color:'#4ade80',letterSpacing:'-0.04em',display:'block'}}>{comboStats.wins}</b><span style={{fontSize:'11px',color:'var(--rf-fg-3)',fontWeight:700,textTransform:'uppercase'}}>共同获胜</span></div>
                      <div><b style={{fontSize:'36px',fontWeight:900,color:'var(--rf-gold)',letterSpacing:'-0.04em',display:'block'}}>{fmtRate(comboStats.rate)}</b><span style={{fontSize:'11px',color:'var(--rf-fg-3)',fontWeight:700,textTransform:'uppercase'}}>胜率</span></div>
                    </div>
                    <p style={{fontSize:'11px',color:'var(--rf-fg-3)',margin:0}}>
                      仅统计可确认"同队"的场次（当天所有选中球员战绩分数一致）；分数不同代表分属不同队，不计入
                      {combo.length === 3 ? ' · 3人组合数据来自逐场名单实时计算' : ''}
                    </p>
                  </>
                ) : (
                  <div style={{color:'var(--rf-fg-3)',fontSize:'13px',padding:'8px 0'}}>
                    可确认同队出场不足 {20} 场，暂无统计数据
                  </div>
                )}
              </div>
            )}

            {combo.length === 0 && (
              <div style={{textAlign:'center',padding:'32px',color:'var(--rf-fg-3)',fontSize:'13px',
                          background:'var(--rf-graphite-2)',borderRadius:'var(--rf-r)',border:'1px dashed var(--rf-line-strong)'}}>
                搜索并选择 2–3 名球员，即时计算"同队出场"胜率<br/>
                <span style={{fontSize:'11px',opacity:0.6}}>支持 {(MATCH_DATA ? Object.keys(MATCH_DATA).length : 0)} 名球员 · 仅统计可确认同队的场次 · 门槛 ≥ 20 场</span>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

Object.assign(window, {
  TopNav, Hero, StatStrip, FeaturedMatch, Rankings, Rankings2026, RankingsBySeason, Fixtures, AllFixtures, AllTimeRankings, BestXI, MonthlyRankings, PlayersCarousel, PlayerModal, Milestones, ClubRecords, Footer,
  PlayerGrowthChart, GoldenPairs, SearchOverlay, SeasonSummary,
  MatchDetailModal, PlayerCompare, LineupAnalytics,
});
