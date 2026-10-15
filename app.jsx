// Unified application shell. Hash routes work on static hosting without rewrites.
const {useState,useEffect,useRef} = React;
const D = window.RF_DATA;
const CURRENT_YEAR = D.STATS_META.asOf.slice(0,4);
const PAGE_TITLES = {home:'俱乐部首页',match:'赛事中心',rankings:'赛季榜单',data:'数据中心',records:'队史纪录','all-rankings':'历史总榜','season-summary':'赛季总结','squad-roster':'球员名册',roster:'完整花名册','all-fixtures':'全部战报','external-stats':'对外战绩','bar-race':'榜单趋势','player-compare':'球员对比','attendance-heatmap':'出勤热力图','lineup-builder':'阵容编辑',analysis:'搭档与阵容',milestones:'里程碑','player-dna':'球员档案','record-ranking':'纪录 Top20'};
const ALL_PLAYERS = [...D.PLAYERS,...Object.values(D.PLAYER_LOOKUP)];
function routeFromLocation(){
  const raw=location.hash.slice(1).replace(/^\//,'');
  const [path,query='']=raw.split('?');
  const q=new URLSearchParams(query);
  return {page:PAGE_TITLES[path]?path:'home',season:D.SEASONS.includes(q.get('season'))?q.get('season'):CURRENT_YEAR,player:q.get('player')||'',record:q.get('record')||''};
}
function routeUrl(page,params={}){
  const q=new URLSearchParams(Object.entries(params).filter(([,v])=>v!==null&&v!==undefined&&v!==''));
  return '#/'+page+(q.size?'?'+q.toString():'');
}
function Section({title,kicker,children,action}){return <section className="section ui-section"><div className="container"><div className="section__head"><div><span className="section__eyebrow">{kicker}</span><h2 className="section__title">{title}</h2></div>{action}</div>{children}</div></section>;}
function App(){
  const [route,setRoute]=useState(routeFromLocation);
  const [searchOpen,setSearch]=useState(false);
  const [match,setMatch]=useState(null);
  const [copied,setCopied]=useState(false);
  const headingRef=useRef(null);
  const active=route.page, season=route.season;
  const player=ALL_PLAYERS.find(p=>p.name===route.player)||null;
  const selectedRecord=D.RECORDS.season.find(r=>r.label===route.record);
  function navigate(page,params={}){
    page=({squad:'squad-roster'})[page]||page;
    if(!PAGE_TITLES[page])page='home';
    const next=routeUrl(page,params);
    if(location.hash!==next)location.hash=next;
    setSearch(false);setMatch(null);
  }
  function showPlayer(p){if(p)navigate(active,{season,record:route.record,player:p.name});}
  function closePlayer(){navigate(active,{season,record:route.record});}
  function openRecord(record){navigate('record-ranking',{record:record.label});}
  useEffect(()=>{
    const change=()=>{setRoute(routeFromLocation());setCopied(false);};
    const shortcut=e=>{if((e.metaKey||e.ctrlKey)&&e.key==='k'){e.preventDefault();setSearch(v=>!v);}};
    window.addEventListener('hashchange',change);window.addEventListener('keydown',shortcut);
    return()=>{window.removeEventListener('hashchange',change);window.removeEventListener('keydown',shortcut);};
  },[]);
  useEffect(()=>{window.scrollTo({top:0,behavior:'instant'});headingRef.current?.focus({preventScroll:true});},[active,season,route.record]);
  useEffect(()=>{document.title=(route.player||route.record||PAGE_TITLES[active])+' · Royal Farmers FC';},[route]);
  async function share(){try{await navigator.clipboard.writeText(location.href);setCopied(true);}catch{setCopied(false);window.prompt('复制页面链接',location.href);}}
  const navGroup=['home','match','rankings','squad-roster','data'];
  const currentGroup=active==='home'?'home':['match','all-fixtures','external-stats'].includes(active)?'match':['rankings','all-rankings','season-summary','record-ranking','records'].includes(active)?'rankings':['squad-roster','roster','player-dna'].includes(active)?'squad-roster':'data';
  const navLabels=['首页','赛事','榜单','球员','更多'];
  const icons=['⌂','⚑','≡','♙','⋯'];
  const years=['总榜',...Object.keys(D.STATS_META.seasonMatchDays).sort().reverse()];
  const seasonControl=<label className="ui-season">查看赛季<select value={season} onChange={e=>navigate(active,{season:e.target.value})}>{years.map(y=><option key={y} value={y}>{y==='总榜'?'历史总榜':y+' 赛季'}</option>)}</select></label>;
  const rankingSection=<>{season==='总榜'?<Rankings onPlayerClick={showPlayer}/>:season===CURRENT_YEAR?<Rankings2026 onPlayerClick={showPlayer}/>:<RankingsBySeason year={season} onPlayerClick={showPlayer}/>}</>;
  const links=[['all-rankings','01','历史总榜','进球、助攻、出勤与评分的完整排名'],['records','02','队史纪录','生涯、赛季、单月与单场的高光时刻'],['season-summary','03','赛季总结','一个赛季的球队战绩和个人表现'],['external-stats','04','对外战绩','只统计外部两队友谊赛'],['attendance-heatmap','05','出勤日历','查看球员逐月出勤与赛季分布'],['bar-race','06','榜单趋势','探索历史趋势与排名变化示意'],['player-compare','07','球员对比','并排比较两名球员的数据'],['analysis','08','搭档与阵容','进球配合、助攻网络和组合表现'],['lineup-builder','09','阵容编辑','选择阵型，安排你的首发阵容'],['milestones','10','里程碑','重要节点、达成估算与历史最佳'],['roster','11','完整花名册','查询所有档案与各赛季汇总']];
  let content;
  if(active==='home')content=<>
    <header className="ui-hero" style={{'--hero-image':'url('+D.HERO_BG+')'}}><div className="container"><div className="ui-hero__copy"><span className="section__eyebrow">SHANGHAI · EST. 2020</span><h1>为农民工而战<span>FOR THE FARMERS.</span></h1><p>上海皇家农民工足球俱乐部<br/>一群热爱足球的人，每一次相聚都值得记录。</p><div className="ui-actions"><a className="ui-primary" href={routeUrl('match')}>查看最近比赛 ↗</a><a className="ui-secondary" href={routeUrl('squad-roster')}>认识我们的球员</a></div></div><div className="ui-hero__stamp">ROYAL<br/>FARMERS FC<span>上海 · 2020</span></div></div></header>
    <div className="container ui-numbers">{[[D.MATCH_COUNT,'累计比赛日'],[D.STATS_META.seasonMatchDays[CURRENT_YEAR],CURRENT_YEAR+' 比赛日'],[ALL_PLAYERS.length,'历史球员档案']].map(([value,label])=><div key={label}><strong>{value}</strong><span>{label}</span></div>)}<p>数据始于 2021 年<br/>更新于 {D.STATS_META.asOf.replace(/(\d{4})(\d{2})(\d{2})/,'$1.$2.$3')}</p></div>
    <Section title="最近一场" kicker="LATEST MATCH" action={<a className="section__cta" href={routeUrl('match')}>赛事中心 ↗</a>}><FeaturedMatch/></Section>
    <Milestones/>
    <Section title={CURRENT_YEAR+' · 赛季领跑者'} kicker="SEASON LEADERS" action={<a className="section__cta" href={routeUrl('rankings')}>全部榜单 ↗</a>}><div className="ui-leaders">{[['进球',D.GOALS26[0],'goals','球'],['助攻',D.ASSISTS26[0],'assists','次'],['出勤',D.APPS26[0],'apps','个比赛日']].map(([label,p,key,unit],i)=>p&&<button className="ui-leader" key={key} onClick={()=>showPlayer(p)}><span className="ui-leader__label">0{i+1} / {label}</span><strong>{p.name}</strong><span className="ui-leader__value">{p[key]}<small>{unit}</small></span><span className="ui-leader__foot">查看球员档案 ↗</span></button>)}</div></Section>
    <Section title="每一份热爱，都留下纪录" kicker="CLUB ARCHIVE" action={<a className="section__cta" href={routeUrl('records')}>全部队史纪录 ↗</a>}><div className="ui-records">{D.RECORDS.season.slice(0,3).map(r=><button key={r.label} onClick={()=>openRecord(r)}><span>{r.label} ↗</span><strong>{r.value}<small>{r.unit}</small></strong><p>{r.holder} · {r.ctx}</p></button>)}</div><a className="ui-data-banner" href={routeUrl('data')}><div><span className="section__eyebrow">THE NUMBERS BEHIND THE CLUB</span><h3>球队的故事，不止于比分。</h3><p>探索月度榜单、出勤、球员对比与更多历史数据。</p></div><span>进入数据中心 ↗</span></a></Section>
  </>;
  else if(active==='data')content=<Section title="从这里，读懂球队" kicker="EXPLORE THE CLUB"><div className="ui-hub">{links.map(([id,no,title,description])=><a key={id} href={routeUrl(id)}><span className="ui-hub__no">{no} ↗</span><h2>{title}</h2><p>{description}</p></a>)}</div></Section>;
  else if(active==='rankings')content=<><Section title={season==='总榜'?'历史总榜':season+' 赛季榜单'} kicker="RANKINGS" action={seasonControl}>{rankingSection}<div className="ui-actions"><a className="section__cta" href={routeUrl('all-rankings')}>完整历史排名 ↗</a><a className="section__cta" href={routeUrl('season-summary',{season:season==='总榜'?CURRENT_YEAR:season})}>赛季总结 ↗</a></div></Section><MonthlyRankings onPlayerClick={showPlayer}/></>;
  else if(active==='match')content=<><Section title="最近一场" kicker="MATCH DAY" action={<a href={routeUrl('external-stats')} className="section__cta">对外战绩 ↗</a>}><FeaturedMatch/></Section><Section title="最近战报" kicker="RECENT FIXTURES" action={<a className="section__cta" href={routeUrl('all-fixtures')}>全部战报 ↗</a>}><Fixtures onMatchClick={setMatch}/></Section></>;
  else if(active==='all-fixtures')content=<Section title="全部战报" kicker="MATCH ARCHIVE"><AllFixtures/></Section>;
  else if(active==='records')content=<ClubRecords key={route.record} initialTab={route.record||'season'} onRecordClick={openRecord}/>;
  else if(active==='record-ranking')content=selectedRecord?<ClubRecordRanking record={selectedRecord} onBack={()=>navigate('records')}/>:<Section title="未找到该纪录" kicker="CLUB RECORDS"><a href={routeUrl('records')}>返回队史纪录</a></Section>;
  else if(active==='all-rankings')content=<AllTimeRankings onNavigate={navigate}/>;
  else if(active==='season-summary')content=<SeasonSummary key={season} initYear={season==='总榜'?CURRENT_YEAR:season} onYearChange={year=>navigate('season-summary',{season:year})} onNavigate={navigate} onPlayerClick={showPlayer}/>;
  else if(active==='squad-roster')content=<SquadRoster onNavigate={navigate} onPlayerClick={showPlayer}/>;
  else if(active==='roster')content=<FullRoster onNavigate={navigate} onPlayerClick={showPlayer}/>;
  else if(active==='external-stats')content=<ExternalMatchStats onNavigate={navigate}/>;
  else if(active==='bar-race')content=<BarRaceChart onNavigate={navigate} onPlayerClick={showPlayer}/>;
  else if(active==='player-compare')content=<PlayerCompare onNavigate={navigate}/>;
  else if(active==='attendance-heatmap')content=<AttendanceHeatmap onNavigate={navigate}/>;
  else if(active==='lineup-builder')content=<LineupBuilder onNavigate={navigate}/>;
  else if(active==='analysis')content=<><GoldenPairs onPlayerClick={showPlayer}/><AssistNetwork onPlayerClick={showPlayer}/><LineupAnalytics onPlayerClick={showPlayer}/></>;
  else if(active==='milestones')content=<><Milestones/><MilestoneRecords/><Section title="历史最佳阵容" kicker="ALL-TIME XI"><BestXI/></Section></>;
  else if(active==='player-dna')content=<PlayerDNA player={player} onNavigate={navigate} onPlayerClick={p=>navigate('player-dna',{player:p.name})}/>;
  return <div className="ui-app"><a className="ui-skip" href="#main-content" onClick={e=>{e.preventDefault();document.getElementById('main-content')?.focus();}}>跳到主要内容</a>
    <nav className="ui-nav" aria-label="主导航"><div className="container"><a href={routeUrl('home')} className="ui-brand"><img src="assets/crest.jpg" alt="皇家农夫队徽"/><span>ROYAL FARMERS<small>上海皇家农民工足球俱乐部</small></span></a><div className="ui-desktop-nav">{navGroup.map((id,i)=><a key={id} href={routeUrl(id)} aria-current={currentGroup===id?'page':undefined}>{i===4?'数据中心':navLabels[i]}</a>)}</div><button className="ui-search" onClick={()=>setSearch(true)} aria-label="搜索球员">⌕ <span>搜索球员</span></button></div></nav>
    {active!=='home'&&<div className="container ui-pagebar"><div><a href={routeUrl('home')}>首页</a><span> / </span><h1 ref={headingRef} tabIndex={-1}>{route.record&&active==='record-ranking'?route.record:PAGE_TITLES[active]}</h1></div><button onClick={share} className="ui-share" aria-live="polite">{copied?'已复制链接 ✓':'复制页面链接 ↗'}</button></div>}
    <main id="main-content" tabIndex={-1} key={active}>{content}</main>
    <div className="container ui-scope"><details><summary>统计口径与数据说明</summary><p>2020 年成立，2021 年起有统计数据。球队场次与出勤按花名册已到日期列计数；战报对局和比赛日分别统计。对外战绩只计外部两队友谊赛，缺失比分不计胜平负。个人进球、助攻不包含乌龙或无法归属的记录。历史汇总与战报明细存在差异时分别保留，不补估。</p></details></div>
    <Footer/>
    <nav className="ui-bottom-nav" aria-label="手机导航">{navGroup.map((id,i)=><a key={id} href={routeUrl(id)} aria-current={currentGroup===id?'page':undefined}><span aria-hidden="true">{icons[i]}</span>{navLabels[i]}</a>)}</nav>
    <SearchOverlay open={searchOpen} onClose={()=>setSearch(false)} onPlayerClick={showPlayer}/>
    {active!=='player-dna'&&<PlayerModal player={player} onShareLink={share} shareLabel={copied?"已复制链接 ✓":"复制球员链接 ↗"} onClose={closePlayer} onPlayerClick={showPlayer} onOpenDNA={p=>navigate('player-dna',{player:p.name})}/>}
    <MatchDetailModal match={match} onClose={()=>setMatch(null)} onPlayerClick={p=>{setMatch(null);showPlayer(p);}}/>
  </div>;
}
ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
