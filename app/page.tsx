import Link from "next/link";
import { Trophy, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-green-900 flex flex-col items-center justify-center p-4 text-white">
      <div className="max-w-md w-full text-center space-y-8">
        
        {/* Logo / Title Area */}
        <div className="space-y-2">
          <div className="flex justify-center mb-4">
             <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-xl">
                <Trophy className="w-10 h-10 text-green-800" />
             </div>
          </div>
          <h1 className="text-4xl font-black tracking-tight">ROYAL FARMERS</h1>
          <p className="text-green-200">Team Data Center</p>
        </div>

        {/* Action Button */}
        <div className="bg-white/10 backdrop-blur-sm p-8 rounded-2xl border border-white/10 shadow-2xl">
          <p className="mb-6 text-green-100">
            Welcome to the official data hub. Check match reports, player stats, and season rankings.
          </p>
          
          <Link 
            href="/rankings" 
            className="group flex items-center justify-center gap-2 w-full bg-yellow-400 hover:bg-yellow-300 text-green-900 font-bold py-4 rounded-xl transition-all transform hover:scale-105"
          >
            <span>View Leaderboard</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="text-xs text-green-400/50">
          Powered by Next.js & Supabase
        </div>
      </div>
    </main>
  );
}