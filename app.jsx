// Marketing site — Royal Farmers FC
const { useState, useEffect } = React;

// 注意：不能命名为 scrollTo，否则会覆盖 window.scrollTo 导致无限递归
function scrollSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  else window.scrollTo({ top: 0, behavior: "smooth" });
}

function App() {
  const [active, setActive]       = useState("home");
  const [season, setSeason]       = useState("总榜");
  const [player, setPlayer]       = useState(null);
  const [searchOpen, setSearch]   = useState(false);
  const [matchDetail, setMatch]   = useState(null);
  const [compareP1, setCmpP1]     = useState(null);
  const [compareP2, setCmpP2]     = useState(null);

  // ⌘K / Ctrl+K 全局快捷键
  useEffect(() => {
    const h = e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearch(s => !s);
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  function onNavigate(id) {
    setActive(id);
    if (["all-fixtures","all-rankings","season-summary","player-compare"].includes(id)) {
      window.scrollTo({ top: 0, behavior: "smooth" }); return;
    }
    if (id === "home")  { setActive("home"); window.scrollTo({ top: 0, behavior: "smooth" }); return; }
    if (id === "match") scrollSection("section-match");
    if (id === "squad") scrollSection("section-squad");
  }

  if (active === "all-fixtures") {
    return (
      <>
        <TopNav active={active} onNavigate={onNavigate} onSearch={() => setSearch(true)} />
        <section className="section" style={{ paddingTop: "24px" }}><div className="container">
          <div className="section__head"><div>
            <span className="section__eyebrow">ALL MATCHES · 全部赛程</span>
            <h2 className="section__title">全部赛程 <em>· All Matches</em></h2>
          </div><button className="section__cta" onClick={() => onNavigate("match")}>← 返回赛程</button></div>
          <AllFixtures />
        </div></section>
        <Footer />
        <PlayerModal player={player} onClose={() => setPlayer(null)} />
        <SearchOverlay open={searchOpen} onClose={() => setSearch(false)} onPlayerClick={setPlayer} />
      </>
    );
  }

  if (active === "all-rankings") {
    return (
      <>
        <TopNav active={active} onNavigate={onNavigate} onSearch={() => setSearch(true)} />
        <AllTimeRankings onNavigate={onNavigate} />
        <Footer />
        <SearchOverlay open={searchOpen} onClose={() => setSearch(false)} onPlayerClick={setPlayer} />
      </>
    );
  }

  if (active === "player-compare") {
    return (
      <>
        <TopNav active={active} onNavigate={onNavigate} onSearch={() => setSearch(true)} />
        <PlayerCompare onNavigate={onNavigate} initP1={compareP1} initP2={compareP2} />
        <Footer />
        <SearchOverlay open={searchOpen} onClose={() => setSearch(false)} onPlayerClick={setPlayer} />
      </>
    );
  }

  if (active === "season-summary") {
    return (
      <>
        <TopNav active={active} onNavigate={onNavigate} onSearch={() => setSearch(true)} />
        <SeasonSummary onNavigate={onNavigate} onPlayerClick={setPlayer} initYear={season !== '总榜' ? season : '2026'} />
        <Footer />
        <PlayerModal player={player} onClose={() => setPlayer(null)} />
        <SearchOverlay open={searchOpen} onClose={() => setSearch(false)} onPlayerClick={setPlayer} />
      </>
    );
  }

  return (
    <>
      <TopNav active={active} onNavigate={onNavigate} onSearch={() => setSearch(true)} />
      <Hero activeSeason={season} onSeasonChange={s => { setSeason(s); scrollSection("section-rankings"); }} />

      <section className="section" id="section-rankings"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">SEASON RANKINGS · 赛季榜单</span>
          <h2 className="section__title">
            {season === "总榜" ? "总榜" : season + "赛季"}
            {" "}<em>· Season Rankings</em>
          </h2>
        </div>
        <div style={{display:'flex',gap:'8px',alignItems:'center',flexWrap:'wrap'}}>
          {season !== "总榜" && (
            <button className="section__cta" style={{background:'var(--rf-gold)',color:'#000',borderColor:'var(--rf-gold)'}}
              onClick={() => onNavigate("season-summary")}>赛季总结 ✦</button>
          )}
          <button className="section__cta"
            onClick={() => { setCmpP1(null); setCmpP2(null); onNavigate("player-compare"); }}>
            ⚔ 球员对比
          </button>
          <button className="section__cta" onClick={() => onNavigate("all-rankings")}>完整数据 →</button>
        </div>
        </div>
        {season === "总榜" && <Rankings onPlayerClick={setPlayer} />}
        {season === "2026" && <Rankings2026 onPlayerClick={setPlayer} />}
        {["2025","2024","2023","2022","2021"].includes(season) && <RankingsBySeason year={season} onPlayerClick={setPlayer} />}
      </div></section>

      <Milestones />

      <ClubRecords />

      <MonthlyRankings onPlayerClick={setPlayer} />

      <section className="section"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">MATCH CENTER · 赛事中心</span>
          <h2 className="section__title">最近一场 <em>· Match Day</em></h2>
        </div><button className="section__cta" onClick={() => onNavigate("all-fixtures")}>所有比赛 →</button></div>
        <FeaturedMatch />
      </div></section>

      <section className="section" id="section-match"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">FIXTURES · 赛程</span>
          <h2 className="section__title">最近 7 场 <em>· Recent Form</em></h2>
        </div><button className="section__cta" onClick={() => onNavigate("all-fixtures")}>全部赛程 →</button></div>
        <Fixtures onMatchClick={setMatch} />
      </div></section>

      <section className="section" id="section-squad"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">SQUAD · 名册</span>
          <h2 className="section__title">优秀农民工 <em>· SUPER FARMER</em></h2>
        </div><button className="section__cta" onClick={() => onNavigate("squad")}>查看全部 →</button></div>
        <PlayersCarousel onPlayerClick={setPlayer} />
      </div></section>

      <GoldenPairs onPlayerClick={setPlayer} />

      <LineupAnalytics onPlayerClick={setPlayer} />

      <section className="section" id="section-bestxi"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">ALL-TIME XI · 历史最佳</span>
          <h2 className="section__title">历史最佳阵容 <em>· 4-4-2</em></h2>
        </div></div>
        <BestXI />
      </div></section>

      <Footer />
      <PlayerModal player={player} onClose={() => setPlayer(null)} />
      <SearchOverlay open={searchOpen} onClose={() => setSearch(false)} onPlayerClick={setPlayer} />
      <MatchDetailModal match={matchDetail} onClose={() => setMatch(null)} onPlayerClick={p => { setMatch(null); setPlayer(p); }} />
    </>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
