import { lemonSqueezySetup } from '@lemonsqueezy/lemonsqueezy.js'

// Initialize Lemon Squeezy SDK
lemonSqueezySetup({
    apiKey: process.env.LEMONSQUEEZY_API_KEY!,
    onError: (error) => {
        console.error('Lemon Squeezy Error:', error)
    },
})

// Lemon Squeezy configuration
export const LEMONSQUEEZY_CONFIG = {
    storeId: process.env.LEMONSQUEEZY_STORE_ID!,
    currency: 'usd',
    testMode: process.env.NODE_ENV === 'development',
}

// Export store ID for convenience
export const getStoreId = () => LEMONSQUEEZY_CONFIG.storeId
