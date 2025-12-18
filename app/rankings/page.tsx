"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/utils/supabase";
import { Trophy, Timer, TrendingUp, Users } from "lucide-react";
import Link from "next/link";

// 定义数据类型
interface PlayerStat {
  id: string;
  name: string;
  avatar_url: string;
  season: string;
  matches_played: number;
  avg_rating: number; // 数据库字段名
  goals: number;
  assists: number;
}

export default function LeaderboardPage() {
  const [stats, setStats] = useState<PlayerStat[]>([]);
  const [season, setSeason] = useState("2025");
  // 🔴 修复1: 这里把 'rating' 改成了 'avg_rating'
  const [filter, setFilter] = useState<"goals" | "assists" | "avg_rating" | "matches_played">("goals");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const { data, error } = await supabase
        .from("player_stats_view")
        .select("*");

      if (!error && data) {
        setStats(data as PlayerStat[]);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const processedData = () => {
    let filtered = stats;

    if (season !== "all") {
      filtered = stats.filter((s) => s.season === season);
    } else {
      // All-Time 聚合逻辑
      const aggMap = new Map<string, PlayerStat>();
      stats.forEach((s) => {
        if (!aggMap.has(s.id)) {
          aggMap.set(s.id, { ...s, matches_played: 0, goals: 0, assists: 0, avg_rating: 0 });
        }
        const p = aggMap.get(s.id)!;
        p.matches_played += s.matches_played;
        p.goals += s.goals;
        p.assists += s.assists;
        p.avg_rating = (p.avg_rating + s.avg_rating) / 2; 
      });
      filtered = Array.from(aggMap.values());
    }

    // 🔴 修复2: 强制转为 Number 进行计算，消除 TS 报错
    return filtered.sort((a, b) => Number(b[filter]) - Number(a[filter]));
  };

  const displayList = processedData();

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8">
      {/* 头部 */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 bg-gradient-to-r from-green-900 to-green-800 p-6 rounded-2xl text-white shadow-lg">
        <div className="flex items-center gap-3">
          <Trophy className="w-8 h-8 text-yellow-400" />
          <h1 className="text-2xl font-bold tracking-wider">HERO RANKINGS</h1>
        </div>
        <div className="mt-4 md:mt-0">
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
          // 🔴 修复3: Key 改为 avg_rating
          { key: "avg_rating", label: "评分", icon: TrendingUp },
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

      {/* 列表 */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden min-h-[400px]">
        {loading ? (
          <div className="p-10 text-center text-gray-400">Loading Data...</div>
        ) : displayList.length === 0 ? (
          <div className="p-10 text-center text-gray-400">本赛季暂无数据</div>
        ) : (
          displayList.map((player, index) => (
            <Link href={`/players/${player.id}`} key={player.id} className="block">
                <div className="flex items-center p-4 border-b border-gray-50 hover:bg-green-50/50 transition-colors group cursor-pointer">
                <div className={`w-8 h-8 flex items-center justify-center rounded-full mr-4 font-bold text-sm ${
                    index === 0 ? "bg-yellow-100 text-yellow-700" :
                    index === 1 ? "bg-gray-200 text-gray-700" :
                    index === 2 ? "bg-orange-100 text-orange-700" : "text-gray-400"
                }`}>
                    {index + 1}
                </div>

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

                <div className="text-right">
                    <div className="text-2xl font-black text-green-900 leading-none">
                    {/* 🔴 修复4: 显示逻辑适配 */}
                    {filter === 'avg_rating' ? Number(player.avg_rating).toFixed(2) : player[filter]}
                    </div>
                    <div className="text-[10px] text-gray-400 uppercase tracking-wider mt-1">
                    {filter === 'goals' && 'Goals'}
                    {filter === 'assists' && 'Assists'}
                    {filter === 'matches_played' && 'Matches'}
                    {filter === 'avg_rating' && 'Avg Rating'}
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