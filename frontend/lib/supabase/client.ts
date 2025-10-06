import {createClient as createSupabaseClient} from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createSupabaseClient(supabaseUrl, supabaseAnonKey)

// Export a function to create a new client instance
export function createClient() {
  return createSupabaseClient(supabaseUrl, supabaseAnonKey)
}
