/**
 * Test Login Flow
 * 
 * This script tests the login functionality directly
 */

import { createClient } from '@supabase/supabase-js'
import { config } from 'dotenv'

config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function testLogin() {
    console.log('🔐 Testing Login Flow...\n')

    const testEmail = 'finaltest@gmail.com'
    const testPassword = 'TestPassword123!'

    try {
        console.log(`Attempting to login with: ${testEmail}`)

        const { data, error } = await supabase.auth.signInWithPassword({
            email: testEmail,
            password: testPassword,
        })

        if (error) {
            console.error('❌ Login failed!')
            console.error('Error:', error.message)
            console.error('Status:', error.status)
            console.error('Code:', error.code)
            return false
        }

        if (data.user) {
            console.log('✅ Login successful!')
            console.log('\nUser Details:')
            console.log(`  - ID: ${data.user.id}`)
            console.log(`  - Email: ${data.user.email}`)
            console.log(`  - Email Confirmed: ${data.user.email_confirmed_at ? 'Yes' : 'No'}`)
            console.log(`  - Created: ${new Date(data.user.created_at!).toLocaleString()}`)

            if (data.session) {
                console.log('\n✅ Session created!')
                console.log(`  - Access Token: ${data.session.access_token.substring(0, 20)}...`)
                console.log(`  - Expires: ${new Date(data.session.expires_at! * 1000).toLocaleString()}`)
            }

            return true
        }

        console.error('❌ No user returned')
        return false

    } catch (err: any) {
        console.error('❌ Unexpected error:', err.message)
        return false
    }
}

testLogin().then((success) => {
    process.exit(success ? 0 : 1)
})
