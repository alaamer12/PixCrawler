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
  // STRIPE CONFIGURATION (Optional - for payments)
  // =============================================================================
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z
    .string()
    .startsWith('pk_', 'Stripe publishable key must start with pk_')
    .optional(),
  STRIPE_SECRET_KEY: z
    .string()
    .startsWith('sk_', 'Stripe secret key must start with sk_')
    .optional(),
  STRIPE_WEBHOOK_SECRET: z
    .string()
    .startsWith('whsec_', 'Stripe webhook secret must start with whsec_')
    .optional(),
  STRIPE_FREE_PRICE_ID: z
    .string()
    .startsWith('price_', 'Stripe price ID must start with price_')
    .optional(),
  STRIPE_PRO_PRICE_ID: z
    .string()
    .startsWith('price_', 'Stripe price ID must start with price_')
    .optional(),
  STRIPE_ENTERPRISE_PRICE_ID: z
    .string()
    .startsWith('price_', 'Stripe price ID must start with price_')
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
      
      // Stripe
      NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
      STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
      STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET,
      STRIPE_FREE_PRICE_ID: process.env.STRIPE_FREE_PRICE_ID,
      STRIPE_PRO_PRICE_ID: process.env.STRIPE_PRO_PRICE_ID,
      STRIPE_ENTERPRISE_PRICE_ID: process.env.STRIPE_ENTERPRISE_PRICE_ID,
      
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
