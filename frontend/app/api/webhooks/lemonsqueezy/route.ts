import { NextRequest, NextResponse } from 'next/server'
import { cookies, headers } from 'next/headers'
import { PaymentService } from '@/lib/payments/service'
import { createServerClient } from '@supabase/ssr'

/**
 * Lemon Squeezy Webhook Handler
 * Handles payment events from Lemon Squeezy
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const headersList = await headers()
    const signature = headersList.get('x-signature')
    const eventName = headersList.get('x-event-name')

    if (!signature) {
      return NextResponse.json(
        { error: 'Missing x-signature header' },
        { status: 400 }
      )
    }

    // Verify webhook signature
    const event = PaymentService.verifyWebhookSignature(body, signature)

    // Handle the event
    await handleWebhookEvent(eventName!, event)

    return NextResponse.json({ received: true })

  } catch (error) {
    console.error('Webhook error:', error)
    return NextResponse.json(
      { error: 'Webhook handler failed' },
      { status: 400 }
    )
  }
}

async function handleWebhookEvent(eventName: string, event: any) {
  const cookieStore = await cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    }
  )

  switch (eventName) {
    case 'order_created':
      await handleOrderCreated(event.data, supabase)
      break

    case 'subscription_created':
      await handleSubscriptionCreated(event.data, supabase)
      break

    case 'subscription_updated':
      await handleSubscriptionUpdated(event.data, supabase)
      break

    case 'subscription_cancelled':
      await handleSubscriptionCancelled(event.data, supabase)
      break

    case 'subscription_payment_success':
      await handleSubscriptionPaymentSuccess(event.data, supabase)
      break

    case 'subscription_payment_failed':
      await handleSubscriptionPaymentFailed(event.data, supabase)
      break

    default:
      console.log(`Unhandled event type: ${eventName}`)
  }
}

async function handleOrderCreated(order: any, supabase: any) {
  const customData = order.attributes.first_order_item?.product?.custom_data || {}
  const userId = customData.userId
  const planId = customData.planId

  if (!userId || !planId) {
    console.error('Missing userId or planId in order custom data')
    return
  }

  try {
    // Record the transaction
    await supabase.from('transactions').insert({
      id: order.id,
      user_id: userId,
      lemonsqueezy_order_id: order.id,
      amount: parseFloat(order.attributes.total) / 100,
      currency: order.attributes.currency,
      status: order.attributes.status === 'paid' ? 'paid' : 'pending',
      plan_id: planId,
      metadata: customData,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    // If this is a one-time payment (not subscription), update user credits/plan
    if (!order.attributes.first_subscription_item) {
      await handleOneTimePayment(userId, planId, supabase)
    }

    console.log(`Order created for user ${userId}, plan ${planId}`)
  } catch (error) {
    console.error('Error handling order created:', error)
  }
}

async function handleSubscriptionCreated(subscription: any, supabase: any) {
  const customData = subscription.attributes.custom_data || {}
  const userId = customData.userId
  const planId = customData.planId

  if (!userId || !planId) {
    console.error('Missing userId or planId in subscription custom data')
    return
  }

  try {
    // Create or update subscription record
    await supabase.from('subscriptions').upsert({
      user_id: userId,
      lemonsqueezy_customer_id: subscription.attributes.customer_id.toString(),
      lemonsqueezy_subscription_id: subscription.id,
      lemonsqueezy_variant_id: subscription.attributes.variant_id.toString(),
      plan_id: planId,
      status: subscription.attributes.status,
      current_period_start: new Date(subscription.attributes.renews_at).toISOString(),
      current_period_end: new Date(subscription.attributes.ends_at || subscription.attributes.renews_at).toISOString(),
      cancel_at_period_end: subscription.attributes.cancelled,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    // Update user's plan
    await supabase.from('profiles')
      .update({
        current_plan: planId,
        subscription_status: subscription.attributes.status,
        updated_at: new Date().toISOString(),
      })
      .eq('user_id', userId)

    console.log(`Subscription created for user ${userId}, plan ${planId}`)
  } catch (error) {
    console.error('Error handling subscription created:', error)
  }
}

async function handleSubscriptionUpdated(subscription: any, supabase: any) {
  try {
    // Update subscription record
    await supabase.from('subscriptions')
      .update({
        status: subscription.attributes.status,
        current_period_start: new Date(subscription.attributes.renews_at).toISOString(),
        current_period_end: new Date(subscription.attributes.ends_at || subscription.attributes.renews_at).toISOString(),
        cancel_at_period_end: subscription.attributes.cancelled,
        lemonsqueezy_variant_id: subscription.attributes.variant_id.toString(),
        updated_at: new Date().toISOString(),
      })
      .eq('lemonsqueezy_subscription_id', subscription.id)

    console.log(`Subscription updated: ${subscription.id}`)
  } catch (error) {
    console.error('Error handling subscription updated:', error)
  }
}

async function handleSubscriptionCancelled(subscription: any, supabase: any) {
  try {
    // Update subscription status
    await supabase.from('subscriptions')
      .update({
        status: 'cancelled',
        cancel_at_period_end: true,
        updated_at: new Date().toISOString(),
      })
      .eq('lemonsqueezy_subscription_id', subscription.id)

    // Update user's plan to free tier
    const customData = subscription.attributes.custom_data || {}
    const userId = customData.userId
    if (userId) {
      await supabase.from('profiles')
        .update({
          current_plan: 'starter',
          subscription_status: 'cancelled',
          updated_at: new Date().toISOString(),
        })
        .eq('user_id', userId)
    }

    console.log(`Subscription cancelled: ${subscription.id}`)
  } catch (error) {
    console.error('Error handling subscription cancelled:', error)
  }
}

async function handleSubscriptionPaymentSuccess(subscription: any, supabase: any) {
  console.log(`Subscription payment succeeded: ${subscription.id}`)
  // Handle successful recurring payments here
  // You might want to update credits or extend access
}

async function handleSubscriptionPaymentFailed(subscription: any, supabase: any) {
  console.log(`Subscription payment failed: ${subscription.id}`)
  // Handle failed recurring payments here
  // You might want to notify the user or update their subscription status

  try {
    await supabase.from('subscriptions')
      .update({
        status: 'past_due',
        updated_at: new Date().toISOString(),
      })
      .eq('lemonsqueezy_subscription_id', subscription.id)
  } catch (error) {
    console.error('Error handling subscription payment failed:', error)
  }
}

async function handleOneTimePayment(userId: string, planId: string, supabase: any) {
  // Handle one-time payments (credit packages)
  const { getPlanById } = await import('@/lib/payments/plans')
  const plan = getPlanById(planId)

  if (plan && plan.credits) {
    // Add credits to user account
    await supabase.rpc('add_user_credits', {
      user_id: userId,
      credits_to_add: plan.credits
    })
  }
}
