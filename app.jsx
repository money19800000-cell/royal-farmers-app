// Marketing site — Royal Farmers FC
const { useState } = React;

function scrollTo(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  else window.scrollTo({ top: 0, behavior: "smooth" });
}

function App() {
  const [active, setActive] = useState("home");
  const [season, setSeason] = useState("总榜");
  const [player, setPlayer] = useState(null);

  function onNavigate(id) {
    setActive(id);
    if (id === "all-fixtures" || id === "all-rankings") { window.scrollTo({ top: 0, behavior: "smooth" }); return; }
    if (id === "home")  { setActive("home"); window.scrollTo({ top: 0, behavior: "smooth" }); return; }
    if (id === "match") scrollTo("section-match");
    if (id === "squad") scrollTo("section-squad");
  }

  if (active === "all-fixtures") {
    return (
      <>
        <TopNav active={active} onNavigate={onNavigate} />
        <section className="section" style={{ paddingTop: "24px" }}><div className="container">
          <div className="section__head"><div>
            <span className="section__eyebrow">ALL MATCHES · 全部赛程</span>
            <h2 className="section__title">全部赛程 <em>· All Matches</em></h2>
          </div><button className="section__cta" onClick={() => onNavigate("match")}>← 返回赛程</button></div>
          <AllFixtures />
        </div></section>
        <Footer />
        <PlayerModal player={player} onClose={() => setPlayer(null)} />
      </>
    );
  }

  if (active === "all-rankings") {
    return (
      <>
        <TopNav active={active} onNavigate={onNavigate} />
        <AllTimeRankings onNavigate={onNavigate} />
        <Footer />
      </>
    );
  }

  return (
    <>
      <TopNav active={active} onNavigate={onNavigate} />
      <Hero activeSeason={season} onSeasonChange={s => { setSeason(s); scrollTo("section-rankings"); }} />

      <section className="section" id="section-rankings"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">SEASON RANKINGS · 赛季榜单</span>
          <h2 className="section__title">
            {season === "总榜" ? "总榜" : season + "赛季"}
            {" "}<em>· Season Rankings</em>
          </h2>
        </div><button className="section__cta" onClick={() => onNavigate("all-rankings")}>完整数据 →</button></div>
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
        <Fixtures />
      </div></section>

      <section className="section" id="section-squad"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">SQUAD · 名册</span>
          <h2 className="section__title">优秀农民工 <em>· SUPER FARMER</em></h2>
        </div><button className="section__cta" onClick={() => onNavigate("squad")}>查看全部 →</button></div>
        <PlayersCarousel onPlayerClick={setPlayer} />
      </div></section>

      <section className="section" id="section-bestxi"><div className="container">
        <div className="section__head"><div>
          <span className="section__eyebrow">ALL-TIME XI · 历史最佳</span>
          <h2 className="section__title">历史最佳阵容 <em>· 4-4-2</em></h2>
        </div></div>
        <BestXI />
      </div></section>

      <Footer />
      <PlayerModal player={player} onClose={() => setPlayer(null)} />
    </>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
