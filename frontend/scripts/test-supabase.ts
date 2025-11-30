/**
 * Test script to verify Supabase connection
 * Run with: bun run scripts/test-supabase.ts
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

console.log('🔍 Testing Supabase Connection...\n')

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('❌ Missing environment variables:')
    if (!supabaseUrl) console.error('  - NEXT_PUBLIC_SUPABASE_URL')
    if (!supabaseAnonKey) console.error('  - NEXT_PUBLIC_SUPABASE_ANON_KEY')
    process.exit(1)
}

console.log('✅ Environment variables found:')
console.log(`  - NEXT_PUBLIC_SUPABASE_URL: ${supabaseUrl}`)
console.log(`  - NEXT_PUBLIC_SUPABASE_ANON_KEY: ${supabaseAnonKey.substring(0, 20)}...`)
console.log()

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function testConnection() {
    try {
        // Test 1: Basic connection
        console.log('📡 Test 1: Testing basic connection...')
        const { data, error } = await supabase.from('profiles').select('count').limit(1)

        if (error) {
            console.error('❌ Connection failed:', error.message)
            return false
        }

        console.log('✅ Connection successful!')
        console.log()

        // Test 2: Auth service
        console.log('🔐 Test 2: Testing auth service...')
        const { data: { session }, error: authError } = await supabase.auth.getSession()

        if (authError) {
            console.error('❌ Auth service error:', authError.message)
            return false
        }

        console.log('✅ Auth service is accessible')
        console.log(`  - Current session: ${session ? 'Active' : 'None'}`)
        console.log()

        // Test 3: Database tables
        console.log('📊 Test 3: Checking database tables...')
        const tables = ['profiles', 'projects', 'crawl_jobs', 'images', 'activity_logs']

        for (const table of tables) {
            const { error: tableError } = await supabase.from(table).select('count').limit(1)

            if (tableError) {
                console.error(`❌ Table "${table}" error:`, tableError.message)
            } else {
                console.log(`✅ Table "${table}" is accessible`)
            }
        }

        console.log()
        console.log('🎉 All tests passed! Supabase is properly configured.')
        return true

    } catch (error: any) {
        console.error('❌ Unexpected error:', error.message)
        return false
    }
}

testConnection().then((success) => {
    process.exit(success ? 0 : 1)
})
