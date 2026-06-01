// Royal Farmers FC — Components
const { useState, useEffect, useRef } = React;
const { PLAYERS, GOALS26, ASSISTS26, APPS26, MATCH_COUNT, SEASONS, FIXTURES, HERO_BG, FEATURE_IMG, PLAYER_LOOKUP, MILESTONES, GOALS_ALL, ASSISTS_ALL, APPS_ALL, MONTHLY_GOALS, MONTHLY_ASSISTS, MONTHLY_APPS, MONTHLY_PERIOD, MONTHLY_HISTORY, RECORDS, STREAK_RECORDS, ALLSEASON_PLAYERS, RATINGS_ALL, RATINGS_2026, RATINGS_2025, RATINGS_2024, RATINGS_2023, RATINGS_2022, RATINGS_2021 } = window.RF_DATA;

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
function TopNav({ active, onNavigate }) {
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
  // 从 PLAYERS 构建位置查找表（花名册无位置字段，仅PLAYERS有）
  const posLookup = {};
  (PLAYERS || []).forEach(p => { if (p.pos) posLookup[p.name] = p.pos; });
  const findFull = (p) => PLAYERS.find(pl => pl.name === p.name) || p;

  // 直接使用已按值排序的 ALL 数组，不再依赖 PLAYERS（潘磊等不在PLAYERS中的球员也能上榜）
  const cols = [
    { title: "射手榜 · TOP SCORERS",  data: (GOALS_ALL    || []).slice(0, 5), key: "goals"   },
    { title: "助攻榜 · TOP ASSISTS",  data: (ASSISTS_ALL  || []).slice(0, 5), key: "assists" },
    { title: "出场榜 · APPEARANCES",  data: (APPS_ALL     || []).slice(0, 5), key: "apps"    },
    { title: "评分榜 · RATINGS",      data: (RATINGS_ALL  || []).slice(0, 5), key: "rating",
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
    { title: "出勤榜 · ATTENDANCE",   data: APPS26,           key: "apps",    sub: p => p.rate },
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
function Fixtures({ limit = 7 }) {
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
      {list.map((f, i) => {
        const hasDetail = f.homeScorers?.length || f.awayScorers?.length || f.homeAssists?.length || f.awayAssists?.length;
        return (
          <div className="fix-row" key={i}>
            <div className="fix-date">{f.date}</div>
            <div className="fix-team">{f.home}</div>
            <div className="fix-score-wrap">
              <span className={"fix-num " + (f.homeScore > f.awayScore ? "win" : f.homeScore < f.awayScore ? "loss" : "")}>{f.homeScore}</span>
              <span className="fix-dash">—</span>
              <span className={"fix-num " + (f.awayScore > f.homeScore ? "win" : f.awayScore < f.homeScore ? "loss" : "")}>{f.awayScore}</span>
              {!!hasDetail && (
                <div className="fix-score-drop">
                  <div className="fsd-side">
                    <div className="fsd-label">{f.home.replace("Royal Farmers", "RF")}</div>
                    <GoalList scorers={f.homeScorers} assists={f.homeAssists} />
                  </div>
                  <div className="fsd-sep" />
                  <div className="fsd-side">
                    <div className="fsd-label">{f.away.replace("Royal Farmers", "RF")}</div>
                    <GoalList scorers={f.awayScorers} assists={f.awayAssists} />
                  </div>
                </div>
              )}
            </div>
            <div className="fix-team is-away">{f.away}</div>
            <div className="fix-comp">{f.comp}</div>
            <div style={{ display: "flex", gap: "4px" }}>
              <a className="fix-watch" href={biliUrl(f.date, "录像")} target="_blank" rel="noopener">录像</a>
              <a className="fix-watch" href={biliUrl(f.date, "集锦")} target="_blank" rel="noopener">集锦</a>
            </div>
          </div>
        );
      })}
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
  const lineup = [
    { cn: "前锋",   en: "ST", name: "姜珂",   apps: 387, goals: 887,  assists: 1153, x: 33, y: 20, photo: "assets/players/10号姜珂.jpeg" },
    { cn: "前锋",   en: "ST", name: "盛建中", apps: 164, goals: 251,  assists: 96,   x: 67, y: 20, photo: null },
    { cn: "左前卫", en: "LM", name: "金辉",   apps: 321, goals: 539,  assists: 228,  x: 11, y: 44, photo: "assets/players/81号金辉.jpeg" },
    { cn: "中前卫", en: "CM", name: "张伟",   apps: 222, goals: 144,  assists: 83,   x: 36, y: 44, photo: "assets/players/17号张伟.jpeg" },
    { cn: "中前卫", en: "CM", name: "陶骏",   apps: 283, goals: 289,  assists: 259,  x: 64, y: 44, photo: "assets/players/6号陶骏.jpeg" },
    { cn: "右前卫", en: "RM", name: "潘磊",   apps: 171, goals: 335,  assists: 224,  x: 89, y: 44, photo: null },
    { cn: "左后卫", en: "LB", name: "老徐",   apps: 261, goals: 115,  assists: 137,  x: 14, y: 67, photo: null },
    { cn: "中卫",   en: "CB", name: "杨坤",   apps: 194, goals: 165,  assists: 156,  x: 37, y: 67, photo: null },
    { cn: "中卫",   en: "CB", name: "鲍梁剑", apps: 201, goals: 83,   assists: 63,   x: 63, y: 67, photo: "assets/players/22号鲍梁剑.jpeg" },
    { cn: "右后卫", en: "RB", name: "曹峰",   apps: 233, goals: 57,   assists: 62,   x: 86, y: 67, photo: null },
    { cn: "门将",   en: "GK", name: "麦超",   apps: 276, goals: 4,    assists: 6,    x: 50, y: 87, photo: "assets/players/22号麦超.jpeg" },
  ];
  const posColor = { GK: "#f59e0b", LB: "#60a5fa", CB: "#60a5fa", RB: "#60a5fa", LM: "#4ade80", CM: "#4ade80", RM: "#4ade80", ST: "#f87171" };
  return (
    <div className="pitch-wrap">
      <div className="pitch">
        <svg className="pitch-svg" viewBox="0 0 320 460" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="314" height="454" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="2"/>
          <line x1="3" y1="230" x2="317" y2="230" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <circle cx="160" cy="230" r="50" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <circle cx="160" cy="230" r="3.5" fill="rgba(255,255,255,0.5)"/>
          <rect x="72" y="3" width="176" height="82" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <rect x="112" y="3" width="96" height="30" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <circle cx="160" cy="63" r="3" fill="rgba(255,255,255,0.5)"/>
          <rect x="72" y="375" width="176" height="82" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <rect x="112" y="427" width="96" height="30" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
          <circle cx="160" cy="393" r="3" fill="rgba(255,255,255,0.5)"/>
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
  // 优先用 MONTHLY_HISTORY（多月轮播），fallback 单月数据
  const history = (MONTHLY_HISTORY && MONTHLY_HISTORY.length > 0)
    ? MONTHLY_HISTORY
    : [{ period: MONTHLY_PERIOD || "本月", goals: MONTHLY_GOALS || [], assists: MONTHLY_ASSISTS || [], apps: MONTHLY_APPS || [] }];

  const [idx, setIdx] = useState(0);
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const dragging    = useRef(false);

  const current = history[idx] || history[0];

  const PHOTO_MAP = {};
  (PLAYERS || []).forEach(p => { if (p.photo) PHOTO_MAP[p.name] = p.photo; });
  Object.values(PLAYER_LOOKUP || {}).forEach(p => { if (p.photo) PHOTO_MAP[p.name] = p.photo; });
  const allPlayers = [...(PLAYERS||[]), ...Object.values(PLAYER_LOOKUP||{})];
  function findPlayer(name) { return allPlayers.find(p => p.name === name) || null; }

  function goNext() { if (idx < history.length - 1) setIdx(idx + 1); }
  function goPrev() { if (idx > 0) setIdx(idx - 1); }

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
    if (Math.abs(diff) > 40) { diff > 0 ? goNext() : goPrev(); }
    dragging.current = false;
  }

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
          {(m.goals||[]).map((item, i) => <RankRow key={i} item={item} rank={i+1} valKey="goals" icon="⚽" />)}
        </div>
        <div className="mr-panel">
          <div className="mr-panel-title">👟 助攻榜</div>
          {(m.assists||[]).map((item, i) => <RankRow key={i} item={item} rank={i+1} valKey="assists" icon="👟" />)}
        </div>
        <div className="mr-panel">
          <div className="mr-panel-title">📅 出勤榜</div>
          {(m.apps||[]).map((item, i) => <RankRow key={i} item={item} rank={i+1} valKey="apps" icon="📅" />)}
        </div>
      </div>
    );
  }

  return (
    <section className="section mr-section">
      <div className="container">
        <div className="section__head">
          <div>
            <span className="section__eyebrow">MONTHLY CHART · 月度榜单</span>
            <h2 className="section__title">{current.period}榜单 <em>· Monthly Rankings</em></h2>
          </div>
          {history.length > 1 && (
            <div className="mr-nav">
              <button className="mr-nav-btn" onClick={goPrev} disabled={idx === 0}>‹</button>
              <span className="mr-nav-label">{idx + 1} / {history.length}</span>
              <button className="mr-nav-btn" onClick={goNext} disabled={idx === history.length - 1}>›</button>
            </div>
          )}
        </div>

        {/* 轮播容器 */}
        <div className="mr-carousel-wrap" onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}>
          <div className="mr-carousel-track" style={{ transform: `translateX(-${idx * 100}%)` }}>
            {history.map((m, i) => (
              <div className="mr-carousel-slide" key={i}>
                <MonthPanel m={m} />
              </div>
            ))}
          </div>
        </div>

        {/* 月份标签导航 */}
        {history.length > 1 && (
          <div className="mr-month-tabs">
            {history.map((m, i) => (
              <button
                key={i}
                className={`mr-month-tab ${i === idx ? 'mr-month-tab--active' : ''}`}
                onClick={() => setIdx(i)}
              >
                {m.period.replace('2026年', '').replace('年', '年')}
              </button>
            ))}
          </div>
        )}
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
function PlayerModal({ player, onClose }) {
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

Object.assign(window, {
  TopNav, Hero, StatStrip, FeaturedMatch, Rankings, Rankings2026, RankingsBySeason, Fixtures, AllFixtures, AllTimeRankings, BestXI, MonthlyRankings, PlayersCarousel, PlayerModal, Milestones, ClubRecords, Footer
});
