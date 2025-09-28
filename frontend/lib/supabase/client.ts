import { createClient as createSupabaseClient } from '@supabase/supabase-js';
import type { Database } from './database.types';

export const createClient = () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
  
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase environment variables');
  }
  
  return createSupabaseClient<Database>(supabaseUrl, supabaseAnonKey);
};

export const supabase = createClient();
