import { NextRequest, NextResponse } from 'next/server'

// Use environment variable for backend URL
// Development: http://127.0.0.1:8000
// Production: https://your-backend.azurewebsites.net
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    console.log('🔄 Proxying request to:', `${BACKEND_URL}/api/v1/simple-flow/start`)
    
    const body = await request.json()
    console.log('📤 Request body:', body)
    
    const response = await fetch(`${BACKEND_URL}/api/v1/simple-flow/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    console.log('📥 Backend response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Backend error:', errorText)
      return NextResponse.json(
        { error: `Backend error: ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('✅ Backend response data:', data)
    
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('❌ Proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to proxy request to backend' },
      { status: 500 }
    )
  }
}