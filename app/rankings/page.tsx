"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/utils/supabase";
import { Trophy, Medal, Timer, TrendingUp, Users } from "lucide-react";
import Link from "next/link";

// 定义数据类型 (对应 Supabase View)
interface PlayerStat {
  id: string;
  name: string;
  avatar_url: string;
  season: string;
  matches_played: number;
  avg_rating: number;
  goals: number;
  assists: number;
}

export default function LeaderboardPage() {
  const [stats, setStats] = useState<PlayerStat[]>([]);
  const [season, setSeason] = useState("2025"); // 默认赛季
  const [filter, setFilter] = useState<"goals" | "assists" | "rating" | "matches_played">("goals");
  const [loading, setLoading] = useState(true);

  // 获取数据
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      // 查询视图 player_stats_view
      const { data, error } = await supabase
        .from("player_stats_view")
        .select("*");

      if (!error && data) {
        setStats(data as PlayerStat[]);
      } else {
        console.error("Error fetching data:", error);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  // 数据处理：筛选 + 排序 + 聚合(如果是All-Time)
  const processedData = () => {
    let filtered = stats;

    // 1. 赛季筛选
    if (season !== "all") {
      filtered = stats.filter((s) => s.season === season);
    } else {
      // 聚合 All-Time 数据 (合并同一个人的多条赛季记录)
      const aggMap = new Map<string, PlayerStat>();
      stats.forEach((s) => {
        if (!aggMap.has(s.id)) {
          aggMap.set(s.id, { ...s, matches_played: 0, goals: 0, assists: 0, avg_rating: 0 });
        }
        const p = aggMap.get(s.id)!;
        p.matches_played += s.matches_played;
        p.goals += s.goals;
        p.assists += s.assists;
        // 重新加权计算评分 (简单平均)
        p.avg_rating = (p.avg_rating + s.avg_rating) / 2; 
      });
      filtered = Array.from(aggMap.values());
    }

    // 2. 排序
    return filtered.sort((a, b) => b[filter] - a[filter]);
  };

  const displayList = processedData();

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8">
      {/* 头部控制区 */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 bg-gradient-to-r from-green-900 to-green-800 p-6 rounded-2xl text-white shadow-lg">
        <div className="flex items-center gap-3">
          <Trophy className="w-8 h-8 text-yellow-400" />
          <h1 className="text-2xl font-bold tracking-wider">HERO RANKINGS</h1>
        </div>
        
        <div className="mt-4 md:mt-0 flex gap-4">
          <select 
            value={season} 
            onChange={(e) => setSeason(e.target.value)}
            className="bg-green-700 text-white px-4 py-2 rounded-lg border border-green-600 outline-none font-mono"
          >
            <option value="2025">Season 2025</option>
            <option value="2024">Season 2024</option>
            <option value="all">All-Time Hall of Fame</option>
          </select>
        </div>
      </div>

      {/* 筛选 Tab */}
      <div className="grid grid-cols-4 gap-2 mb-6 bg-white p-2 rounded-xl shadow-sm border border-gray-100">
        {[
          { key: "goals", label: "进球", icon: Trophy },
          { key: "assists", label: "助攻", icon: Users },
          { key: "matches_played", label: "出勤", icon: Timer },
          { key: "rating", label: "评分", icon: TrendingUp },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key as any)}
            className={`flex flex-col items-center py-3 rounded-lg transition-all ${
              filter === tab.key 
                ? "bg-green-50 text-green-800 font-bold border-green-200 border" 
                : "text-gray-400 hover:bg-gray-50"
            }`}
          >
            <tab.icon className="w-5 h-5 mb-1" />
            <span className="text-xs md:text-sm">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 列表区域 */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden min-h-[400px]">
        {loading ? (
          <div className="p-10 text-center text-gray-400">Loading Data...</div>
        ) : displayList.length === 0 ? (
          <div className="p-10 text-center text-gray-400">本赛季暂无数据</div>
        ) : (
          displayList.map((player, index) => (
            <Link href={`/players/${player.id}`} key={player.id} className="block">
                <div className="flex items-center p-4 border-b border-gray-50 hover:bg-green-50/50 transition-colors group cursor-pointer">
                {/* 排名 */}
                <div className={`w-8 h-8 flex items-center justify-center rounded-full mr-4 font-bold text-sm ${
                    index === 0 ? "bg-yellow-100 text-yellow-700" :
                    index === 1 ? "bg-gray-200 text-gray-700" :
                    index === 2 ? "bg-orange-100 text-orange-700" : "text-gray-400"
                }`}>
                    {index + 1}
                </div>

                {/* 头像与名字 */}
                <div className="flex items-center flex-1">
                    <img 
                    src={player.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${player.name}`} 
                    className="w-10 h-10 rounded-full border-2 border-white shadow-sm bg-gray-100" 
                    alt={player.name}
                    />
                    <div className="ml-3">
                    <div className="font-bold text-gray-800 group-hover:text-green-800 transition">{player.name}</div>
                    <div className="text-xs text-gray-400 font-mono">Royal Farmers FC</div>
                    </div>
                </div>

                {/* 数据大字展示 */}
                <div className="text-right">
                    <div className="text-2xl font-black text-green-900 leading-none">
                    {filter === 'rating' ? Number(player.avg_rating).toFixed(1) : player[filter]}
                    </div>
                    <div className="text-[10px] text-gray-400 uppercase tracking-wider mt-1">
                    {filter === 'goals' && 'Goals'}
                    {filter === 'assists' && 'Assists'}
                    {filter === 'matches_played' && 'Matches'}
                    {filter === 'rating' && 'Avg Rating'}
                    </div>
                </div>
                </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}