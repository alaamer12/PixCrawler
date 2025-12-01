import { z } from 'zod'

/**
 * Environment variable validation schema
 * Ensures all required environment variables are present and valid at runtime
 */
const envSchema = z.object({
  // =============================================================================
  // SUPABASE CONFIGURATION (Required)
  // =============================================================================
  NEXT_PUBLIC_SUPABASE_URL: z
    .string()
    .url('Invalid Supabase URL - must be a valid URL (e.g., https://xxx.supabase.co)'),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z
    .string()
    .min(1, 'Supabase anon key is required - get this from your Supabase project settings'),

  // =============================================================================
  // DATABASE CONFIGURATION (Optional)
  // =============================================================================
  POSTGRES_URL: z
    .string()
    .url('Invalid PostgreSQL URL - must be a valid connection string')
    .optional(),

  // =============================================================================
  // API CONFIGURATION (Required)
  // =============================================================================
  NEXT_PUBLIC_API_URL: z
    .string()
    .url('Invalid API URL - must be a valid URL (e.g., http://localhost:8000/api/v1 or https://api.pixcrawler.io/api/v1)')
    .default('http://localhost:8000/api/v1'),

  // =============================================================================
  // APPLICATION CONFIGURATION (Required)
  // =============================================================================
  NEXT_PUBLIC_APP_URL: z
    .string()
    .url('Invalid App URL - must be a valid URL (e.g., http://localhost:3000 or https://pixcrawler.io)')
    .default('http://localhost:3000'),

  // =============================================================================
  // LEMON SQUEEZY CONFIGURATION (Optional - for payments)
  // =============================================================================
  LEMONSQUEEZY_API_KEY: z
    .string()
    .min(1, 'Lemon Squeezy API key is required')
    .optional(),
  LEMONSQUEEZY_STORE_ID: z
    .string()
    .min(1, 'Lemon Squeezy store ID is required')
    .optional(),
  LEMONSQUEEZY_WEBHOOK_SECRET: z
    .string()
    .min(1, 'Lemon Squeezy webhook secret is required')
    .optional(),
  LEMONSQUEEZY_PAYG_VARIANT_ID: z
    .string()
    .min(1, 'Lemon Squeezy Pay-as-you-go variant ID is required')
    .optional(),
  LEMONSQUEEZY_CREDITS_1000_VARIANT_ID: z
    .string()
    .min(1, 'Lemon Squeezy 1000 credits variant ID is required')
    .optional(),
  LEMONSQUEEZY_CREDITS_5000_VARIANT_ID: z
    .string()
    .min(1, 'Lemon Squeezy 5000 credits variant ID is required')
    .optional(),
  LEMONSQUEEZY_CREDITS_10000_VARIANT_ID: z
    .string()
    .min(1, 'Lemon Squeezy 10000 credits variant ID is required')
    .optional(),

  // =============================================================================
  // RESEND EMAIL CONFIGURATION (Optional - for transactional emails)
  // =============================================================================
  RESEND_API_KEY: z
    .string()
    .startsWith('re_', 'Resend API key must start with re_')
    .optional(),
  CONTACT_EMAIL: z
    .string()
    .email('Invalid contact email address')
    .optional(),
  FROM_EMAIL: z
    .string()
    .email('Invalid from email address')
    .optional(),

  // =============================================================================
  // NODE ENVIRONMENT
  // =============================================================================
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
})

/**
 * Validates and parses environment variables
 * Throws an error with detailed messages if validation fails
 */
function validateEnv() {
  try {
    return envSchema.parse({
      // Supabase
      NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
      NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,

      // Database
      POSTGRES_URL: process.env.POSTGRES_URL,

      // API
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,

      // Application
      NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,

      // Lemon Squeezy
      LEMONSQUEEZY_API_KEY: process.env.LEMONSQUEEZY_API_KEY,
      LEMONSQUEEZY_STORE_ID: process.env.LEMONSQUEEZY_STORE_ID,
      LEMONSQUEEZY_WEBHOOK_SECRET: process.env.LEMONSQUEEZY_WEBHOOK_SECRET,
      LEMONSQUEEZY_HOBBY_VARIANT_ID: process.env.LEMONSQUEEZY_HOBBY_VARIANT_ID,
      LEMONSQUEEZY_PRO_VARIANT_ID: process.env.LEMONSQUEEZY_PRO_VARIANT_ID,
      LEMONSQUEEZY_ENTERPRISE_VARIANT_ID: process.env.LEMONSQUEEZY_ENTERPRISE_VARIANT_ID,
      LEMONSQUEEZY_PAYG_VARIANT_ID: process.env.LEMONSQUEEZY_PAYG_VARIANT_ID,
      LEMONSQUEEZY_CREDITS_1000_VARIANT_ID: process.env.LEMONSQUEEZY_CREDITS_1000_VARIANT_ID,
      LEMONSQUEEZY_CREDITS_5000_VARIANT_ID: process.env.LEMONSQUEEZY_CREDITS_5000_VARIANT_ID,
      LEMONSQUEEZY_CREDITS_10000_VARIANT_ID: process.env.LEMONSQUEEZY_CREDITS_10000_VARIANT_ID,

      // Resend
      RESEND_API_KEY: process.env.RESEND_API_KEY,
      CONTACT_EMAIL: process.env.CONTACT_EMAIL,
      FROM_EMAIL: process.env.FROM_EMAIL,

      // Node environment
      NODE_ENV: process.env.NODE_ENV,
    })
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map((err) => {
        const field = err.path.join('.')
        const message = err.message
        return `  • ${field}: ${message}`
      }).join('\n')

      throw new Error(
        `❌ Environment variable validation failed:\n\n${errorMessages}\n\n` +
        `Please check your .env file and ensure all required variables are set correctly.\n` +
        `See .env.example for reference.`
      )
    }
    throw error
  }
}

// Validate on module load
export const env = validateEnv()

// Type-safe environment variables
export type Env = z.infer<typeof envSchema>
