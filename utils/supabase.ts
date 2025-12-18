import { createClient } from '@supabase/supabase-js';

// ✅ 修复：给 URL 加上了单引号
const supabaseUrl = 'https://wsgfzetcmwbjxzkymldr.supabase.co'; 

// ✅ 保持：Key 已经有引号了，保持不变
const supabaseAnonKey = 'sb_publishable_ZcnWTZVc3T2cqdaWjawoyg_e_Sm5lu1';

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL 或 Key 为空，请检查 utils/supabase.ts");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);