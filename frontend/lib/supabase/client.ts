import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Export a function to create a new client instance
export function createClient() {
  return createBrowserClient(supabaseUrl, supabaseAnonKey)
}
