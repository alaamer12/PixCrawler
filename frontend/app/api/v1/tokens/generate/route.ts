import { NextRequest, NextResponse } from 'next/server'

// Use environment variable for backend URL
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    console.log('🔑 Proxying token request to:', `${BACKEND_URL}/api/v1/tokens/generate`)
    
    // TODO: Add authentication headers from Supabase session
    const response = await fetch(`${BACKEND_URL}/api/v1/tokens/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // TODO: Add Authorization header with Supabase JWT
      },
    })

    console.log('📥 Token response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Token generation error:', errorText)
      return NextResponse.json(
        { error: `Token generation failed: ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('✅ Token generated successfully')
    
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('❌ Token generation proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to generate token' },
      { status: 500 }
    )
  }
}