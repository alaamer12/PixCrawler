import {NextRequest, NextResponse} from 'next/server'
import {Resend} from 'resend'

// Lazy initialization of Resend to avoid build-time errors when API key is not set
// NOTE: This can be buggy - ensure RESEND_API_KEY is set in production
let resend: Resend | null = null
function getResend() {
  if (!resend && process.env.RESEND_API_KEY) {
    resend = new Resend(process.env.RESEND_API_KEY)
  }
  return resend
}

interface ContactFormData {
  name: string
  email: string
  company?: string
  subject: string
  message: string
}

export async function POST(request: NextRequest) {
  try {
    const body: ContactFormData = await request.json()
    const {name, email, company, subject, message} = body

    // Validate required fields
    if (!name || !email || !subject || !message) {
      return NextResponse.json(
        {success: false, error: 'Missing required fields'},
        {status: 400}
      )
    }

    // Validate email format_
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        {success: false, error: 'Invalid email format_'},
        {status: 400}
      )
    }

    // Get configuration from environment
    const CONTACT_EMAIL = process.env.CONTACT_EMAIL || 'contact@pixcrawler.io'
    const FROM_EMAIL = process.env.FROM_EMAIL || 'onboarding@resend.dev'

    // Create professional email template
    const emailHtml = createContactEmailTemplate({
      name,
      email,
      company,
      subject,
      message
    })

    const autoReplyHtml = createAutoReplyTemplate({name})

    // Get Resend instance
    const resendClient = getResend()
    if (!resendClient) {
      return NextResponse.json(
        {error: 'Email service not configured'},
        {status: 503}
      )
    }

    // Send email to PixCrawler team
    const emailResponse = await resendClient.emails.send({
      from: FROM_EMAIL,
      to: CONTACT_EMAIL,
      subject: `[PixCrawler Contact] ${subject} - ${name}`,
      html: emailHtml,
      replyTo: email
    })

    // Send auto-reply to user
    const autoReplyResponse = await resendClient.emails.send({
      from: FROM_EMAIL,
      to: email,
      subject: 'Thank you for contacting PixCrawler',
      html: autoReplyHtml
    })

    return NextResponse.json({
      success: true,
      message: 'Message sent successfully',
      emailId: emailResponse.data?.id,
      autoReplyId: autoReplyResponse.data?.id
    })
  } catch (error) {
    console.error('Contact form error:', error)
    return NextResponse.json(
      {success: false, error: 'Failed to send message'},
      {status: 500}
    )
  }
}

// Professional email template for PixCrawler team
function createContactEmailTemplate({
                                      name,
                                      email,
                                      company,
                                      subject,
                                      message
                                    }: ContactFormData) {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
          <tr>
            <td align="center">
              <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

                <!-- Header -->
                <tr>
                  <td style="padding: 32px 32px 24px; border-bottom: 3px solid #3b82f6;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1e293b;">New Contact Form Submission</h1>
                    <p style="margin: 8px 0 0; font-size: 14px; color: #64748b;">PixCrawler Contact Form</p>
                  </td>
                </tr>

                <!-- Contact Information -->
                <tr>
                  <td style="padding: 24px 32px;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding: 12px 16px; background-color: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 4px;">
                          <h2 style="margin: 0 0 12px; font-size: 16px; font-weight: 600; color: #1e293b;">Contact Details</h2>
                          <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                              <td style="padding: 4px 0; font-size: 14px; color: #475569;">
                                <strong style="color: #1e293b;">Name:</strong> ${name}
                              </td>
                            </tr>
                            <tr>
                              <td style="padding: 4px 0; font-size: 14px; color: #475569;">
                                <strong style="color: #1e293b;">Email:</strong> <a href="mailto:${email}" style="color: #3b82f6; text-decoration: none;">${email}</a>
                              </td>
                            </tr>
                            ${company ? `
                            <tr>
                              <td style="padding: 4px 0; font-size: 14px; color: #475569;">
                                <strong style="color: #1e293b;">Company:</strong> ${company}
                              </td>
                            </tr>
                            ` : ''}
                            <tr>
                              <td style="padding: 4px 0; font-size: 14px; color: #475569;">
                                <strong style="color: #1e293b;">Subject:</strong> ${subject}
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Message Content -->
                <tr>
                  <td style="padding: 0 32px 24px;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding: 16px; background-color: #f8fafc; border-radius: 4px; border-left: 4px solid #10b981;">
                          <h2 style="margin: 0 0 12px; font-size: 16px; font-weight: 600; color: #1e293b;">Message</h2>
                          <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #475569; white-space: pre-wrap;">${message}</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="padding: 24px 32px; border-top: 1px solid #e2e8f0; background-color: #f8fafc;">
                    <p style="margin: 0; font-size: 12px; color: #64748b; text-align: center;">
                      Submitted on ${new Date().toLocaleString('en-US', {
    dateStyle: 'long',
    timeStyle: 'short'
  })}
                    </p>
                    <p style="margin: 8px 0 0; font-size: 12px; color: #64748b; text-align: center;">
                      PixCrawler - DEPI Initiative
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
  `
}

// Professional auto-reply template
function createAutoReplyTemplate({name}: { name: string }) {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
          <tr>
            <td align="center">
              <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

                <!-- Header -->
                <tr>
                  <td style="padding: 32px 32px 24px; border-bottom: 3px solid #3b82f6;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1e293b;">Thank You for Contacting PixCrawler</h1>
                    <p style="margin: 8px 0 0; font-size: 14px; color: #64748b;">We've received your message</p>
                  </td>
                </tr>

                <!-- Content -->
                <tr>
                  <td style="padding: 32px;">
                    <p style="margin: 0 0 16px; font-size: 16px; color: #1e293b;">Hi ${name},</p>

                    <p style="margin: 0 0 16px; font-size: 14px; line-height: 1.6; color: #475569;">
                      Thank you for reaching out to PixCrawler. We've received your message and our team will review it shortly.
                    </p>

                    <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #475569;">
                      We typically respond within 24 hours during business days. If your inquiry is urgent, please mention that in your message.
                    </p>

                    <!-- Info Box -->
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding: 16px; background-color: #eff6ff; border-radius: 4px; border-left: 4px solid #3b82f6;">
                          <p style="margin: 0 0 8px; font-size: 14px; font-weight: 600; color: #1e40af;">About PixCrawler</p>
                          <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #1e40af;">
                            PixCrawler is an automated image dataset builder developed under the Digital Egypt Pioneers Initiative (DEPI),
                            transforming keywords into organized, validated, ML-ready datasets.
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="padding: 24px 32px; border-top: 1px solid #e2e8f0; background-color: #f8fafc;">
                    <p style="margin: 0 0 8px; font-size: 14px; color: #1e293b; font-weight: 600; text-align: center;">
                      PixCrawler Team
                    </p>
                    <p style="margin: 0 0 4px; font-size: 12px; color: #64748b; text-align: center;">
                      Developed under DEPI (Digital Egypt Pioneers Initiative)
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #64748b; text-align: center;">
                      <a href="mailto:contact@pixcrawler.io" style="color: #3b82f6; text-decoration: none;">contact@pixcrawler.io</a>
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
  `
}
