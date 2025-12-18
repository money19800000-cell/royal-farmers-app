"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { supabase } from "@/utils/supabase";

export default function PlayerProfile() {
  const { id } = useParams();
  const [player, setPlayer] = useState<any>(null);
  const [stats, setStats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlayer = async () => {
      if (!id) return;
      
      // 1. 获取基本信息
      const { data: pData } = await supabase
        .from("players")
        .select("*")
        .eq("id", id)
        .single();
      
      // 2. 获取统计数据 (视图)
      const { data: sData } = await supabase
        .from("player_stats_view")
        .select("*")
        .eq("id", id)
        .order("season", { ascending: false }); // 最近赛季在最前

      setPlayer(pData);
      setStats(sData || []);
      setLoading(false);
    };

    fetchPlayer();
  }, [id]);

  if (loading) return <div className="p-20 text-center text-gray-500">Loading Profile...</div>;
  if (!player) return <div className="p-20 text-center text-red-500">Player Not Found</div>;

  // 计算生涯总量
  const totalMatches = stats.reduce((acc, curr) => acc + curr.matches_played, 0);
  const totalGoals = stats.reduce((acc, curr) => acc + curr.goals, 0);
  const totalAssists = stats.reduce((acc, curr) => acc + curr.assists, 0);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8">
      
      {/* 上半部分：左侧卡片 + 右侧图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* 左侧：球员卡片 (仿FIFA/设计图风格) */}
        <div className="lg:col-span-1 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden relative">
            <div className="h-32 bg-gradient-to-b from-green-800 to-green-600"></div>
            <div className="px-6 pb-6 relative">
                {/* 头像 */}
                <div className="-mt-16 mb-4">
                    <img 
                        src={player.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${player.name}`} 
                        className="w-32 h-32 rounded-full border-4 border-white shadow-md bg-white object-cover"
                    />
                </div>
                
                <h1 className="text-3xl font-black text-gray-900 mb-1">{player.name}</h1>
                <p className="text-green-700 font-bold mb-6">ROYAL FARMERS FC</p>

                {/* 属性列表 */}
                <div className="space-y-3 text-sm">
                    <div className="flex justify-between border-b border-gray-100 pb-2">
                        <span className="text-gray-400 font-bold">籍贯</span>
                        <span className="font-semibold text-gray-700">{player.hometown || "Unknown"}</span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100 pb-2">
                        <span className="text-gray-400 font-bold">位置</span>
                        <span className="font-semibold text-gray-700">{player.position || "未定"}</span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100 pb-2">
                        <span className="text-gray-400 font-bold">号码</span>
                        <span className="font-mono font-black text-green-800 text-lg">#{player.number || "?"}</span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100 pb-2">
                        <span className="text-gray-400 font-bold">生涯出场</span>
                        <span className="font-semibold text-gray-700">{totalMatches}</span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100 pb-2">
                        <span className="text-gray-400 font-bold">生涯进球</span>
                        <span className="font-semibold text-gray-700">{totalGoals}</span>
                    </div>
                </div>
            </div>
        </div>

        {/* 右侧：数据图表 (使用CSS Bar模拟设计图效果) */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-lg border border-gray-100 p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <span className="w-2 h-6 bg-green-600 rounded-sm"></span>
                赛季表现趋势
            </h3>

            <div className="space-y-6">
                {stats.map((s) => (
                    <div key={s.season} className="flex items-center gap-4 text-xs md:text-sm">
                        <div className="w-16 font-bold text-gray-500 shrink-0">{s.season}赛季</div>
                        <div className="flex-1 space-y-1">
                            {/* 出场条 */}
                            <div className="flex items-center">
                                <div className="h-6 bg-green-400 rounded-r text-white px-2 flex items-center text-xs font-bold" 
                                     style={{ width: `${Math.min(s.matches_played * 3, 100)}%` }}>
                                     {s.matches_played}场
                                </div>
                            </div>
                            {/* 进球条 */}
                            <div className="flex items-center">
                                <div className="h-6 bg-green-700 rounded-r text-white px-2 flex items-center text-xs font-bold" 
                                     style={{ width: `${Math.min(s.goals * 5, 100)}%` }}>
                                     {s.goals}球
                                </div>
                            </div>
                            {/* 助攻条 */}
                            <div className="flex items-center">
                                <div className="h-6 bg-green-900 rounded-r text-white px-2 flex items-center text-xs font-bold" 
                                     style={{ width: `${Math.min(s.assists * 5, 100)}%` }}>
                                     {s.assists}助
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
      </div>

      {/* 下半部分：详细数据表 */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="p-4 bg-gray-50 border-b border-gray-200">
            <h3 className="font-bold text-gray-700">生涯详细数据</h3>
        </div>
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
                <thead className="bg-gray-100 text-gray-500 uppercase font-bold text-xs">
                    <tr>
                        <th className="px-6 py-3">赛季</th>
                        <th className="px-6 py-3 text-right">出场</th>
                        <th className="px-6 py-3 text-right">进球</th>
                        <th className="px-6 py-3 text-right">场均进球</th>
                        <th className="px-6 py-3 text-right">助攻</th>
                        <th className="px-6 py-3 text-right">场均评分</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {stats.map((s) => (
                        <tr key={s.season} className="hover:bg-green-50 transition">
                            <td className="px-6 py-4 font-bold text-green-900">{s.season}</td>
                            <td className="px-6 py-4 text-right font-mono text-gray-700">{s.matches_played}</td>
                            <td className="px-6 py-4 text-right font-mono text-gray-700">{s.goals}</td>
                            <td className="px-6 py-4 text-right font-mono text-gray-500">
                                {(s.matches_played > 0 ? (s.goals / s.matches_played) : 0).toFixed(2)}
                            </td>
                            <td className="px-6 py-4 text-right font-mono text-gray-700">{s.assists}</td>
                            <td className="px-6 py-4 text-right">
                                <span className="inline-block px-2 py-1 bg-yellow-100 text-yellow-800 rounded font-bold text-xs">
                                    {Number(s.avg_rating).toFixed(2)}
                                </span>
                            </td>
                        </tr>
                    ))}
                    {/* 合计行 */}
                    <tr className="bg-green-50 font-bold border-t-2 border-green-100">
                        <td className="px-6 py-4 text-green-800">总计 (Total)</td>
                        <td className="px-6 py-4 text-right text-green-800">{totalMatches}</td>
                        <td className="px-6 py-4 text-right text-green-800">{totalGoals}</td>
                        <td className="px-6 py-4 text-right text-green-800">-</td>
                        <td className="px-6 py-4 text-right text-green-800">{totalAssists}</td>
                        <td className="px-6 py-4 text-right text-green-800">-</td>
                    </tr>
                </tbody>
            </table>
        </div>
      </div>

    </div>
  );
}