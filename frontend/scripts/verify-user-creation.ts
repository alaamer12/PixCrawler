/**
 * Verify User Creation in Database
 * 
 * This script checks if the user was properly created after signup
 */

import { createClient } from '@supabase/supabase-js'
import { config } from 'dotenv'

config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function verifyUserCreation() {
    console.log('🔍 Verifying User Creation...\n')

    try {
        // Check auth.users
        const { data: authUsers, error: authError } = await supabase.auth.admin.listUsers()

        if (authError) {
            console.error('❌ Error fetching auth users:', authError.message)
            return false
        }

        console.log(`✅ Found ${authUsers.users.length} user(s) in auth.users:`)
        authUsers.users.forEach((user, index) => {
            console.log(`\n  User ${index + 1}:`)
            console.log(`    - ID: ${user.id}`)
            console.log(`    - Email: ${user.email}`)
            console.log(`    - Confirmed: ${user.email_confirmed_at ? 'Yes' : 'No'}`)
            console.log(`    - Created: ${new Date(user.created_at).toLocaleString()}`)
        })

        console.log('\n' + '='.repeat(60))

        // Check profiles table
        const { data: profiles, error: profileError } = await supabase
            .from('profiles')
            .select('*')

        if (profileError) {
            console.error('❌ Error fetching profiles:', profileError.message)
            return false
        }

        console.log(`\n✅ Found ${profiles.length} profile(s) in profiles table:`)
        profiles.forEach((profile, index) => {
            console.log(`\n  Profile ${index + 1}:`)
            console.log(`    - ID: ${profile.id}`)
            console.log(`    - Email: ${profile.email}`)
            console.log(`    - Full Name: ${profile.full_name || 'Not set'}`)
            console.log(`    - Role: ${profile.role}`)
            console.log(`    - Onboarding: ${profile.onboarding_completed ? 'Completed' : 'Pending'}`)
        })

        console.log('\n' + '='.repeat(60))

        // Check credit accounts
        const { data: creditAccounts, error: creditError } = await supabase
            .from('credit_accounts')
            .select('*')

        if (creditError) {
            console.error('❌ Error fetching credit accounts:', creditError.message)
            return false
        }

        console.log(`\n✅ Found ${creditAccounts.length} credit account(s):`)
        creditAccounts.forEach((account, index) => {
            console.log(`\n  Account ${index + 1}:`)
            console.log(`    - User ID: ${account.user_id}`)
            console.log(`    - Balance: ${account.current_balance} credits`)
            console.log(`    - Monthly Usage: ${account.monthly_usage}`)
        })

        console.log('\n' + '='.repeat(60))

        // Check notification preferences
        const { data: notifPrefs, error: notifError } = await supabase
            .from('notification_preferences')
            .select('*')

        if (notifError) {
            console.error('❌ Error fetching notification preferences:', notifError.message)
            return false
        }

        console.log(`\n✅ Found ${notifPrefs.length} notification preference(s):`)
        notifPrefs.forEach((pref, index) => {
            console.log(`\n  Preferences ${index + 1}:`)
            console.log(`    - User ID: ${pref.user_id}`)
            console.log(`    - Email: ${pref.email_enabled ? 'Enabled' : 'Disabled'}`)
            console.log(`    - Digest: ${pref.digest_frequency}`)
        })

        console.log('\n' + '='.repeat(60))
        console.log('\n🎉 Verification complete!')

        return true

    } catch (error: any) {
        console.error('❌ Unexpected error:', error.message)
        return false
    }
}

verifyUserCreation().then((success) => {
    process.exit(success ? 0 : 1)
})
