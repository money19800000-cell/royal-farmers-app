"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/utils/supabase";
import { Calendar, Users, Trophy, Plus, Save, CheckCircle, Search } from "lucide-react";

// 类型定义
interface Player {
  id: string;
  name: string;
  avatar_url: string;
}

interface GoalEvent {
  scorerId: string;
  assistId: string | null;
  type: "goal" | "own_goal";
}

export default function MatchUploadPage() {
  // --- 1. 状态管理 ---
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  
  // 比赛信息
  const [matchDate, setMatchDate] = useState(new Date().toISOString().split('T')[0]);
  const [season, setSeason] = useState("2025");
  const [matchType, setMatchType] = useState("对外友谊赛（三队）");
  const [opponent, setOpponent] = useState("");
  const [scoreHome, setScoreHome] = useState(0);
  const [scoreAway, setScoreAway] = useState(0);

  // 出勤与评分 { [playerId]: rating }
  // 注意：只有在 map 里的才算出场
  const [attendance, setAttendance] = useState<Record<string, string>>({});
  
  // 进球事件
  const [events, setEvents] = useState<GoalEvent[]>([]);

  // 搜索过滤
  const [searchTerm, setSearchTerm] = useState("");

  // --- 2. 初始化加载球员 ---
  useEffect(() => {
    const fetchPlayers = async () => {
      const { data } = await supabase.from("players").select("id, name, avatar_url").order("name");
      if (data) setPlayers(data);
      setLoading(false);
    };
    fetchPlayers();
  }, []);

  // --- 3. 逻辑处理函数 ---

  // 切换球员出场状态
  const togglePlayer = (id: string) => {
    setAttendance(prev => {
      const newMap = { ...prev };
      if (newMap[id] !== undefined) {
        delete newMap[id]; // 取消选中
      } else {
        newMap[id] = "6.0"; // 默认评分 6.0
      }
      return newMap;
    });
  };

  // 修改评分
  const updateRating = (id: string, val: string) => {
    setAttendance(prev => ({ ...prev, [id]: val }));
  };

  // 添加进球事件
  const addEvent = () => {
    setEvents([...events, { scorerId: "", assistId: null, type: "goal" }]);
  };

  // 更新进球事件
  const updateEvent = (index: number, field: keyof GoalEvent, value: any) => {
    const newEvents = [...events];
    newEvents[index] = { ...newEvents[index], [field]: value };
    setEvents(newEvents);
  };

  // 删除事件
  const removeEvent = (index: number) => {
    setEvents(events.filter((_, i) => i !== index));
  };

  // --- 4. 提交保存 (核心逻辑) ---
  const handleSubmit = async () => {
    if (!matchDate || Object.keys(attendance).length === 0) {
      alert("请填写日期并至少选择一名球员");
      return;
    }
    setSubmitting(true);

    try {
      // A. 创建比赛 ID (YYYYMMDD-1 格式，或者自动生成)
      // 这里为了简单和兼容，我们用时间戳+随机数生成一个唯一ID，或者沿用之前的 text ID 逻辑
      // 为了方便，这里我们生成一个基于日期的 ID: 20251218-RANDOM
      const cleanDate = matchDate.replaceAll("-", "").substring(2); // 251218
      const randomPart = Math.floor(Math.random() * 1000);
      const newMatchId = `${cleanDate}-${randomPart}`;

      // B. 插入 Matches 表
      const { error: matchError } = await supabase.from("matches").insert({
        id: newMatchId,
        date: matchDate,
        season: season,
        type: matchType,
        home_team: "Royal Farmers", // 默认主队
        away_team: opponent || "Unknown",
        score_home: scoreHome,
        score_away: scoreAway
      });
      if (matchError) throw matchError;

      // C. 插入 Participation (出勤与评分)
      const participationData = Object.entries(attendance).map(([pId, rating]) => ({
        match_id: newMatchId,
        player_id: pId,
        rating: parseFloat(rating)
      }));
      
      if (participationData.length > 0) {
        const { error: partError } = await supabase.from("match_participation").insert(participationData);
        if (partError) throw partError;
      }

      // D. 插入 Events (进球助攻)
      const eventsData = events
        .filter(e => e.scorerId) // 过滤掉没选人的无效行
        .map(e => ({
          match_id: newMatchId,
          scorer_id: e.scorerId,
          assist_id: e.assistId === "none" ? null : e.assistId,
          event_type: e.type
        }));

      if (eventsData.length > 0) {
        const { error: eventError } = await supabase.from("match_events").insert(eventsData);
        if (eventError) throw eventError;
      }

      alert("🎉 比赛报告上传成功！");
      // 重置表单或跳转
      window.location.href = "/rankings";

    } catch (error: any) {
      console.error(error);
      alert("上传失败: " + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  // 筛选出场球员（用于进球下拉菜单）
  const playingPlayers = players.filter(p => attendance[p.id] !== undefined);

  if (loading) return <div className="p-10 text-center">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 pb-20">
      
      {/* 标题 */}
      <div className="flex items-center gap-3 text-green-900 border-b border-green-100 pb-4">
        <Save className="w-8 h-8" />
        <h1 className="text-2xl font-black">上传比赛报告</h1>
      </div>

      {/* 1. 比赛基本信息 Card */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
        <h2 className="font-bold flex items-center gap-2 text-gray-700">
          <Calendar className="w-5 h-5 text-green-600" /> 比赛信息
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-gray-400 mb-1">日期</label>
            <input type="date" value={matchDate} onChange={e => setMatchDate(e.target.value)} className="w-full border rounded p-2 outline-green-500" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-400 mb-1">赛季</label>
            <select value={season} onChange={e => setSeason(e.target.value)} className="w-full border rounded p-2 outline-green-500">
              <option value="2025">2025</option>
              <option value="2024">2024</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-400 mb-1">比赛性质</label>
            <input type="text" value={matchType} onChange={e => setMatchType(e.target.value)} className="w-full border rounded p-2 outline-green-500" />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 items-end">
           <div className="col-span-1">
             <label className="block text-xs font-bold text-gray-400 mb-1">对手名称</label>
             <input type="text" placeholder="例如: 蓝队 / 曼联" value={opponent} onChange={e => setOpponent(e.target.value)} className="w-full border rounded p-2 outline-green-500" />
           </div>
           <div className="col-span-2 flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-xs font-bold text-gray-400 mb-1">我方进球</label>
                <input type="number" value={scoreHome} onChange={e => setScoreHome(Number(e.target.value))} className="w-full border rounded p-2 font-mono text-center font-bold text-green-700" />
              </div>
              <span className="font-bold text-gray-300 text-xl pb-2">:</span>
              <div className="flex-1">
                <label className="block text-xs font-bold text-gray-400 mb-1">对手进球</label>
                <input type="number" value={scoreAway} onChange={e => setScoreAway(Number(e.target.value))} className="w-full border rounded p-2 font-mono text-center font-bold text-red-700" />
              </div>
           </div>
        </div>
      </div>

      {/* 2. 出场与评分 Card */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold flex items-center gap-2 text-gray-700">
            <Users className="w-5 h-5 text-green-600" /> 出场阵容 & 评分
            </h2>
            <div className="text-sm text-gray-500">
                已选: <span className="font-bold text-green-700">{Object.keys(attendance).length}</span> 人
            </div>
        </div>

        {/* 搜索框 */}
        <div className="mb-4 relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input 
                type="text" 
                placeholder="搜索球员..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border rounded-lg bg-gray-50 text-sm focus:outline-green-500"
            />
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-[400px] overflow-y-auto p-1">
            {players
                .filter(p => p.name.includes(searchTerm))
                .map(player => {
                const isSelected = attendance[player.id] !== undefined;
                return (
                    <div 
                        key={player.id} 
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected ? "bg-green-50 border-green-500 ring-1 ring-green-500" : "bg-white border-gray-200 hover:border-green-300"}`}
                        onClick={() => togglePlayer(player.id)}
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected ? "bg-green-600 border-green-600" : "border-gray-300"}`}>
                                {isSelected && <CheckCircle className="w-3 h-3 text-white" />}
                            </div>
                            <span className={`text-sm font-bold truncate ${isSelected ? "text-green-900" : "text-gray-700"}`}>{player.name}</span>
                        </div>
                        
                        {isSelected && (
                            <div className="mt-2 animate-in fade-in zoom-in duration-200" onClick={e => e.stopPropagation()}>
                                <label className="text-[10px] text-green-600 font-bold">评分</label>
                                <input 
                                    type="number" 
                                    step="0.01" // 支持两位小数
                                    value={attendance[player.id]} 
                                    onChange={(e) => updateRating(player.id, e.target.value)}
                                    className="w-full border border-green-200 rounded px-2 py-1 text-sm font-mono focus:ring-2 focus:ring-green-200 outline-none"
                                />
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
      </div>

      {/* 3. 进球事件 Card */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
        <div className="flex justify-between items-center">
            <h2 className="font-bold flex items-center gap-2 text-gray-700">
                <Trophy className="w-5 h-5 text-yellow-500" /> 进球/助攻记录
            </h2>
            <button onClick={addEvent} className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded flex items-center gap-1 transition">
                <Plus className="w-3 h-3" /> 添加进球
            </button>
        </div>

        {events.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm border-2 border-dashed rounded-lg">
                暂无进球记录，点击右上角添加
            </div>
        ) : (
            <div className="space-y-3">
                {events.map((event, idx) => (
                    <div key={idx} className="flex flex-col md:flex-row gap-2 items-center bg-gray-50 p-3 rounded border border-gray-200">
                        <span className="font-mono text-gray-400 text-xs mr-2">#{idx + 1}</span>
                        
                        {/* 进球者 */}
                        <div className="flex-1 w-full">
                            <select 
                                value={event.scorerId} 
                                onChange={e => updateEvent(idx, 'scorerId', e.target.value)}
                                className="w-full p-2 text-sm border rounded"
                            >
                                <option value="">-- 进球者 --</option>
                                <option value="own_goal">乌龙球 (Own Goal)</option>
                                {playingPlayers.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        {/* 助攻者 */}
                        <div className="flex-1 w-full">
                            <select 
                                value={event.assistId || "none"} 
                                onChange={e => updateEvent(idx, 'assistId', e.target.value)}
                                disabled={event.scorerId === 'own_goal'}
                                className="w-full p-2 text-sm border rounded disabled:bg-gray-100 disabled:text-gray-300"
                            >
                                <option value="none">-- 无助攻 --</option>
                                {playingPlayers.filter(p => p.id !== event.scorerId).map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        {/* 删除按钮 */}
                        <button onClick={() => removeEvent(idx)} className="text-red-400 hover:text-red-600 p-2">
                            ×
                        </button>
                    </div>
                ))}
            </div>
        )}
      </div>

      {/* 底部提交栏 */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-2xl md:pl-64 z-50">
         <div className="max-w-4xl mx-auto flex justify-between items-center">
            <div className="text-sm text-gray-500">
                确认无误后点击上传
            </div>
            <button 
                onClick={handleSubmit} 
                disabled={submitting}
                className={`px-8 py-3 rounded-xl font-bold text-white shadow-lg transition-all ${submitting ? "bg-gray-400" : "bg-gradient-to-r from-green-700 to-green-600 hover:scale-105"}`}
            >
                {submitting ? "正在写入数据库..." : "🚀 提交报告"}
            </button>
         </div>
      </div>

    </div>
  );
}