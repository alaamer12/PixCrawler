# Resend Email Integration Guide

## Overview
PixCrawler uses Resend for handling contact form submissions. This guide explains how to set up and use the email service in different environments.

## Setup

### 1. Install Dependencies
```bash
bun install resend
```

### 2. Get Resend API Key
1. Sign up at [resend.com](https://resend.com)
2. Create an API key in your dashboard
3. Add the API key to your `.env.local` file

### 3. Environment Variables
Create a `.env.local` file in the `frontend` directory:

```env
# Resend Configuration
RESEND_API_KEY=re_your_actual_api_key_here
CONTACT_EMAIL=contact@pixcrawler.io
FROM_EMAIL=onboarding@resend.dev
```

**Important Notes:**
- `FROM_EMAIL`: Use `onboarding@resend.dev` for testing, or your verified domain for production
- `CONTACT_EMAIL`: Where contact form submissions will be sent
- Never commit `.env.local` to version control

## Development Environments

### Local Development (bun dev)
```bash
bun dev
```
- Uses Next.js dev server with Turbopack
- Resend API calls work normally
- Best for general development

### Vercel Dev Environment (npx vercel dev)
```bash
bun run dev:vercel
# or
npx vercel dev
```
- Simulates Vercel production environment
- Required for testing Resend integration locally
- Use this when testing email functionality

**Why Vercel Dev?**
Resend API calls may not work properly with the standard Next.js dev server due to how serverless functions are handled. The Vercel dev environment provides a more accurate simulation of the production environment.

## API Route

The contact form API is located at:
```
/app/api/contact/route.ts
```

### Request Format
```typescript
POST /api/contact
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Corp", // optional
  "subject": "General Inquiry",
  "message": "Hello, I have a question..."
}
```

### Response Format
```typescript
// Success
{
  "success": true,
  "message": "Message sent successfully",
  "emailId": "email_id_from_resend",
  "autoReplyId": "auto_reply_id_from_resend"
}

// Error
{
  "success": false,
  "error": "Error message"
}
```

## Email Templates

### Contact Email (to PixCrawler team)
- Professional table-based HTML layout
- Includes all form fields
- Reply-to set to user's email
- DEPI branding

### Auto-Reply (to user)
- Thank you message
- Response time expectations
- PixCrawler information
- DEPI initiative mention

## Testing

### Local Testing with Vercel Dev
1. Set up environment variables
2. Run `bun run dev:vercel`
3. Navigate to `http://localhost:3000/contact`
4. Submit the form
5. Check Resend dashboard for sent emails

### Production Testing
1. Deploy to Vercel
2. Ensure environment variables are set in Vercel dashboard
3. Test contact form on production URL

## Troubleshooting

### Emails Not Sending
1. **Check API Key**: Ensure `RESEND_API_KEY` is set correctly
2. **Use Vercel Dev**: Run `bun run dev:vercel` instead of `bun dev`
3. **Check Console**: Look for error messages in terminal
4. **Verify Domain**: For production, ensure your domain is verified in Resend

### Common Errors
- `RESEND_API_KEY is not set`: Add the key to `.env.local`
- `Invalid email format`: Check email validation in the form
- `Failed to send email`: Check Resend dashboard for API limits or issues

## Production Deployment

### Vercel Environment Variables
Add these in your Vercel project settings:
1. `RESEND_API_KEY` - Your production API key
2. `CONTACT_EMAIL` - Your business email
3. `FROM_EMAIL` - Your verified domain email (e.g., `noreply@pixcrawler.io`)

### Domain Verification
For production, verify your domain in Resend:
1. Go to Resend dashboard → Domains
2. Add your domain (e.g., `pixcrawler.io`)
3. Add DNS records as instructed
4. Update `FROM_EMAIL` to use your domain

## Best Practices

1. **Rate Limiting**: Implement rate limiting to prevent abuse
2. **Validation**: Always validate input on both client and server
3. **Error Handling**: Provide clear error messages to users
4. **Monitoring**: Check Resend dashboard regularly for delivery issues
5. **Testing**: Always test in Vercel dev environment before deploying

## Support

- Resend Documentation: https://resend.com/docs
- PixCrawler Contact: contact@pixcrawler.io
- DEPI Initiative: Digital Egypt Pioneers Initiative
