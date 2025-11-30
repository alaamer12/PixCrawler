
import { createClient } from '@supabase/supabase-js'
import { config } from 'dotenv'

config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY! // Need service role to bypass RLS if needed, or just use anon if RLS allows reading own profile (but we are script)

// Use service role key if available, otherwise anon (might fail RLS if not logged in)
// Actually, to check profile for a specific user without logging in as them, we need service role.
// Assuming the user has a service role key in env, or we can sign in.
// Let's try signing in first as it's safer/easier if we don't have service key handy in .env (though backend usually does).
// The user's .env might not have SERVICE_ROLE_KEY exposed to frontend.
// Let's try signing in as the user again.

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function checkProfile() {
    console.log('🔍 Checking User Profile...\n')

    const testEmail = 'finaltest@gmail.com'
    const testPassword = 'TestPassword123!'

    // 1. Sign In
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email: testEmail,
        password: testPassword,
    })

    if (authError) {
        console.error('❌ Login failed:', authError.message)
        return
    }

    const userId = authData.user.id
    console.log(`✅ Logged in as ${userId}`)

    // 2. Fetch Profile
    const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single()

    if (profileError) {
        console.error('❌ Failed to fetch profile:', profileError.message)
        console.error('   Hint: Profile might not exist or RLS blocks it.')
    } else {
        console.log('✅ Profile found:')
        console.log(profile)
        console.log(`   Onboarding Completed: ${profile.onboarding_completed}`)
    }
}

checkProfile()
