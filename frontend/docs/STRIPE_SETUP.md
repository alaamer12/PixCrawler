# PixCrawler Stripe Integration Setup Guide

This guide will help you set up the complete Stripe payment system for PixCrawler, including subscriptions, one-time payments, and webhooks.

## 📋 Prerequisites

- Stripe account (free to create at [stripe.com](https://stripe.com))
- Supabase project with authentication set up
- Next.js application running

## 🚀 Quick Start

### 1. Stripe Account Setup

1. **Create a Stripe Account**
   - Go to [stripe.com](https://stripe.com) and sign up
   - Complete your account verification
   - Note your account ID for later

2. **Get API Keys**
   - Go to Developers → API Keys in your Stripe dashboard
   - Copy your **Publishable key** (starts with `pk_test_`)
   - Copy your **Secret key** (starts with `sk_test_`)

### 2. Environment Variables

Add these variables to your `.env.local` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Stripe Price IDs (create these in step 3)
STRIPE_PRO_PRICE_ID=price_your_pro_monthly_price_id
STRIPE_ENTERPRISE_PRICE_ID=price_your_enterprise_monthly_price_id
STRIPE_PAYG_PRICE_ID=price_your_pay_as_you_go_price_id
STRIPE_CREDITS_1000_PRICE_ID=price_your_1000_credits_price_id
STRIPE_CREDITS_5000_PRICE_ID=price_your_5000_credits_price_id
STRIPE_CREDITS_10000_PRICE_ID=price_your_10000_credits_price_id
```

### 3. Create Products and Prices in Stripe

#### A. Subscription Products

1. **Pro Plan ($29/month)**
   ```bash
   # Create product
   stripe products create \
     --name "PixCrawler Pro" \
     --description "Ideal for growing businesses and researchers"

   # Create price (replace prod_xxx with your product ID)
   stripe prices create \
     --product prod_xxx \
     --unit-amount 2900 \
     --currency usd \
     --recurring[interval]=month
   ```

2. **Enterprise Plan ($99/month)**
   ```bash
   # Create product
   stripe products create \
     --name "PixCrawler Enterprise" \
     --description "For large organizations with custom needs"

   # Create price
   stripe prices create \
     --product prod_xxx \
     --unit-amount 9900 \
     --currency usd \
     --recurring[interval]=month
   ```

#### B. One-Time Credit Packages

1. **1,000 Credits ($9)**
   ```bash
   stripe products create --name "1,000 Credits"
   stripe prices create --product prod_xxx --unit-amount 900 --currency usd
   ```

2. **5,000 Credits ($39)**
   ```bash
   stripe products create --name "5,000 Credits"
   stripe prices create --product prod_xxx --unit-amount 3900 --currency usd
   ```

3. **10,000 Credits ($69)**
   ```bash
   stripe products create --name "10,000 Credits"
   stripe prices create --product prod_xxx --unit-amount 6900 --currency usd
   ```

### 4. Database Schema

Add these tables to your Supabase database:

```sql
-- Subscriptions table
CREATE TABLE subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT NOT NULL,
  stripe_subscription_id TEXT UNIQUE NOT NULL,
  stripe_price_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  status TEXT NOT NULL,
  current_period_start TIMESTAMPTZ NOT NULL,
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions table
CREATE TABLE transactions (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_payment_intent_id TEXT,
  amount DECIMAL(10,2) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'usd',
  status TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add columns to user_profiles table
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS current_plan TEXT DEFAULT 'starter';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS subscription_status TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 1000;

-- Function to add credits
CREATE OR REPLACE FUNCTION add_user_credits(user_id UUID, credits_to_add INTEGER)
RETURNS VOID AS $$
BEGIN
  UPDATE user_profiles 
  SET credits = COALESCE(credits, 0) + credits_to_add,
      updated_at = NOW()
  WHERE user_profiles.user_id = add_user_credits.user_id;
END;
$$ LANGUAGE plpgsql;

-- Indexes for performance
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_stripe_payment_intent_id ON transactions(stripe_payment_intent_id);
```

### 5. Webhook Setup

1. **Create Webhook Endpoint**
   - Go to Developers → Webhooks in Stripe dashboard
   - Click "Add endpoint"
   - URL: `https://yourdomain.com/api/webhooks/stripe`
   - Select these events:
     - `checkout.session.completed`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

2. **Get Webhook Secret**
   - After creating the webhook, click on it
   - Copy the "Signing secret" (starts with `whsec_`)
   - Add it to your environment variables

### 6. Testing

#### Test Cards (Use in test mode)

```bash
# Successful payment
4242424242424242

# Declined payment
4000000000000002

# Requires authentication
4000002500003155

# Insufficient funds
4000000000009995
```

#### Test the Integration

1. **Start your development server**
   ```bash
   npm run dev
   ```

2. **Test the pricing page**
   - Go to `/pricing`
   - Try selecting different plans
   - Complete a test purchase

3. **Test webhooks locally**
   ```bash
   # Install Stripe CLI
   stripe listen --forward-to localhost:3000/api/webhooks/stripe
   
   # In another terminal, trigger test events
   stripe trigger checkout.session.completed
   ```

## 🔧 Configuration Options

### Customizing Plans

Edit `/lib/payments/plans.ts` to modify:
- Plan features
- Pricing
- Credit amounts
- Plan descriptions

### Webhook Events

Add custom webhook handlers in `/app/api/webhooks/stripe/route.ts`:

```typescript
case 'your.custom.event':
  await handleCustomEvent(event.data.object, supabase)
  break
```

## 📱 Usage in Components

### Pricing Grid
```tsx
import { PricingGrid } from '@/components/stripe'

export default function PricingPage() {
  return (
    <div>
      <h1>Choose Your Plan</h1>
      <PricingGrid currentPlan="starter" />
    </div>
  )
}
```

### Payment Success Page
```tsx
import { PaymentSuccess } from '@/components/stripe'

export default function SuccessPage() {
  return <PaymentSuccess />
}
```

### Payment Cancel Page
```tsx
import { PaymentCancel } from '@/components/stripe'

export default function CancelPage() {
  return <PaymentCancel />
}
```

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use different keys for development/production
   - Rotate keys regularly

2. **Webhook Security**
   - Always verify webhook signatures
   - Use HTTPS in production
   - Implement idempotency for webhook handlers

3. **Error Handling**
   - Log all payment errors
   - Implement retry logic for failed webhooks
   - Monitor payment failures

## 🚀 Production Deployment

### 1. Switch to Live Mode
- Get live API keys from Stripe dashboard
- Update environment variables
- Test with real payment methods

### 2. Update Webhook URLs
- Point webhooks to your production domain
- Update `NEXT_PUBLIC_APP_URL` environment variable

### 3. Enable Billing Portal
- Configure billing portal settings in Stripe dashboard
- Set up customer portal branding

## 📊 Monitoring and Analytics

### Stripe Dashboard
- Monitor payments and subscriptions
- View customer analytics
- Set up alerts for failed payments

### Application Monitoring
- Log payment events
- Monitor webhook delivery
- Track conversion rates

## 🆘 Troubleshooting

### Common Issues

1. **Webhook not receiving events**
   - Check webhook URL is correct
   - Verify webhook secret
   - Check firewall settings

2. **Payment fails silently**
   - Check Stripe logs
   - Verify API keys
   - Check error handling

3. **Database errors**
   - Verify table schema
   - Check foreign key constraints
   - Review RLS policies

### Debug Mode

Enable debug logging:
```bash
STRIPE_DEBUG=true npm run dev
```

## 📚 Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Webhook Testing](https://stripe.com/docs/webhooks/test)
- [Payment Methods](https://stripe.com/docs/payments/payment-methods)

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review Stripe logs
3. Check application logs
4. Contact support with error details

---

**🎉 Congratulations!** Your Stripe integration is now ready. Users can subscribe to plans, purchase credits, and manage their billing through the customer portal.