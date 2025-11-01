import {NextRequest, NextResponse} from 'next/server'
import {cookies, headers} from 'next/headers'
import {PaymentService} from '@/lib/payments/service'
import {createServerClient} from '@supabase/ssr'
import Stripe from 'stripe'

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const headersList = headers()
    const signature = headersList.get('stripe-signature')

    if (!signature) {
      return NextResponse.json(
        {error: 'Missing stripe-signature header'},
        {status: 400}
      )
    }

    // Verify webhook signature
    const event = PaymentService.verifyWebhookSignature(body, signature)

    // Handle the event
    await handleWebhookEvent(event)

    return NextResponse.json({received: true})

  } catch (error) {
    console.error('Webhook error:', error)
    return NextResponse.json(
      {error: 'Webhook handler failed'},
      {status: 400}
    )
  }
}

async function handleWebhookEvent(event: Stripe.Event) {
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookies().get(name)?.value
        },
      },
    }
  )

  switch (event.type) {
    case 'checkout.session.completed':
      await handleCheckoutSessionCompleted(event.data.object as Stripe.Checkout.Session, supabase)
      break

    case 'payment_intent.succeeded':
      await handlePaymentIntentSucceeded(event.data.object as Stripe.PaymentIntent, supabase)
      break

    case 'payment_intent.payment_failed':
      await handlePaymentIntentFailed(event.data.object as Stripe.PaymentIntent, supabase)
      break

    case 'customer.subscription.created':
      await handleSubscriptionCreated(event.data.object as Stripe.Subscription, supabase)
      break

    case 'customer.subscription.updated':
      await handleSubscriptionUpdated(event.data.object as Stripe.Subscription, supabase)
      break

    case 'customer.subscription.deleted':
      await handleSubscriptionDeleted(event.data.object as Stripe.Subscription, supabase)
      break

    case 'invoice.payment_succeeded':
      await handleInvoicePaymentSucceeded(event.data.object as Stripe.Invoice, supabase)
      break

    case 'invoice.payment_failed':
      await handleInvoicePaymentFailed(event.data.object as Stripe.Invoice, supabase)
      break

    default:
      console.log(`Unhandled event type: ${event.type}`)
  }
}

async function handleCheckoutSessionCompleted(session: Stripe.Checkout.Session, supabase: any) {
  const userId = session.metadata?.userId
  const planId = session.metadata?.planId

  if (!userId || !planId) {
    console.error('Missing userId or planId in session metadata')
    return
  }

  try {
    // Record the transaction
    await supabase.from('transactions').insert({
      id: session.id,
      user_id: userId,
      stripe_payment_intent_id: session.payment_intent,
      amount: session.amount_total ? session.amount_total / 100 : 0,
      currency: session.currency,
      status: 'succeeded',
      plan_id: planId,
      metadata: session.metadata,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    // If this is a subscription, it will be handled by subscription.created event
    // If this is a one-time payment, update user credits/plan
    if (session.mode === 'payment') {
      await handleOneTimePayment(userId, planId, supabase)
    }

    console.log(`Checkout session completed for user ${userId}, plan ${planId}`)
  } catch (error) {
    console.error('Error handling checkout session completed:', error)
  }
}

async function handlePaymentIntentSucceeded(paymentIntent: Stripe.PaymentIntent, supabase: any) {
  const userId = paymentIntent.metadata?.userId
  const planId = paymentIntent.metadata?.planId

  if (!userId || !planId) {
    console.error('Missing userId or planId in payment intent metadata')
    return
  }

  try {
    // Update transaction status
    await supabase.from('transactions')
      .update({
        status: 'succeeded',
        updated_at: new Date().toISOString(),
      })
      .eq('stripe_payment_intent_id', paymentIntent.id)

    console.log(`Payment intent succeeded for user ${userId}, plan ${planId}`)
  } catch (error) {
    console.error('Error handling payment intent succeeded:', error)
  }
}

async function handlePaymentIntentFailed(paymentIntent: Stripe.PaymentIntent, supabase: any) {
  try {
    // Update transaction status
    await supabase.from('transactions')
      .update({
        status: 'failed',
        updated_at: new Date().toISOString(),
      })
      .eq('stripe_payment_intent_id', paymentIntent.id)

    console.log(`Payment intent failed: ${paymentIntent.id}`)
  } catch (error) {
    console.error('Error handling payment intent failed:', error)
  }
}

async function handleSubscriptionCreated(subscription: Stripe.Subscription, supabase: any) {
  const userId = subscription.metadata?.userId
  const planId = subscription.metadata?.planId

  if (!userId || !planId) {
    console.error('Missing userId or planId in subscription metadata')
    return
  }

  try {
    // Create or update subscription record
    await supabase.from('subscriptions').upsert({
      user_id: userId,
      stripe_customer_id: subscription.customer,
      stripe_subscription_id: subscription.id,
      stripe_price_id: subscription.items.data[0]?.price.id,
      plan_id: planId,
      status: subscription.status,
      current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
      cancel_at_period_end: subscription.cancel_at_period_end,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })

    // Update user's plan
    await supabase.from('user_profiles')
      .update({
        current_plan: planId,
        subscription_status: subscription.status,
        updated_at: new Date().toISOString(),
      })
      .eq('user_id', userId)

    console.log(`Subscription created for user ${userId}, plan ${planId}`)
  } catch (error) {
    console.error('Error handling subscription created:', error)
  }
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription, supabase: any) {
  try {
    // Update subscription record
    await supabase.from('subscriptions')
      .update({
        status: subscription.status,
        current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
        current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
        cancel_at_period_end: subscription.cancel_at_period_end,
        updated_at: new Date().toISOString(),
      })
      .eq('stripe_subscription_id', subscription.id)

    console.log(`Subscription updated: ${subscription.id}`)
  } catch (error) {
    console.error('Error handling subscription updated:', error)
  }
}

async function handleSubscriptionDeleted(subscription: Stripe.Subscription, supabase: any) {
  try {
    // Update subscription status
    await supabase.from('subscriptions')
      .update({
        status: 'canceled',
        updated_at: new Date().toISOString(),
      })
      .eq('stripe_subscription_id', subscription.id)

    // Update user's plan to free tier
    const userId = subscription.metadata?.userId
    if (userId) {
      await supabase.from('user_profiles')
        .update({
          current_plan: 'starter',
          subscription_status: 'canceled',
          updated_at: new Date().toISOString(),
        })
        .eq('user_id', userId)
    }

    console.log(`Subscription deleted: ${subscription.id}`)
  } catch (error) {
    console.error('Error handling subscription deleted:', error)
  }
}

async function handleInvoicePaymentSucceeded(invoice: Stripe.Invoice, supabase: any) {
  console.log(`Invoice payment succeeded: ${invoice.id}`)
  // Handle successful recurring payments here
}

async function handleInvoicePaymentFailed(invoice: Stripe.Invoice, supabase: any) {
  console.log(`Invoice payment failed: ${invoice.id}`)
  // Handle failed recurring payments here
  // You might want to notify the user or update their subscription status
}

async function handleOneTimePayment(userId: string, planId: string, supabase: any) {
  // Handle one-time payments (credit packages)
  const {getPlanById} = await import('@/lib/payments/plans')
  const plan = getPlanById(planId)

  if (plan && plan.credits) {
    // Add credits to user account
    await supabase.rpc('add_user_credits', {
      user_id: userId,
      credits_to_add: plan.credits
    })
  }
}
