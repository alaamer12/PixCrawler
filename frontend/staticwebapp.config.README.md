# Azure Static Web App Configuration

This document explains the `staticwebapp.config.json` configuration for deploying PixCrawler frontend to Azure Static Web Apps.

## Overview

The `staticwebapp.config.json` file configures routing, security headers, caching, and other deployment settings for Azure Static Web Apps.

## Configuration Sections

### 1. Routes

Routes define how requests are handled and what headers are applied.

#### Backend API Proxy (`/backend-api/*`)
```json
{
  "route": "/backend-api/*",
  "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  "allowedRoles": ["anonymous", "authenticated"]
}
```
- **Purpose**: Proxy requests to the FastAPI backend
- **Usage**: Configure your backend API URL in Azure Static Web App settings
- **Note**: In production, set `NEXT_PUBLIC_API_URL` to point to your backend (e.g., `https://pixcrawler-api.azurewebsites.net`)

#### Next.js API Routes (`/api/*`)
```json
{
  "route": "/api/*",
  "rewrite": "/api/*",
  "allowedRoles": ["anonymous", "authenticated"]
}
```
- **Purpose**: Handle Next.js API routes (contact form, notifications, etc.)
- **Usage**: These are serverless functions within the Next.js app

#### Static Assets (`/_next/static/*`)
```json
{
  "route": "/_next/static/*",
  "headers": {
    "cache-control": "public, max-age=31536000, immutable"
  }
}
```
- **Purpose**: Aggressive caching for Next.js static assets
- **Cache Duration**: 1 year (31536000 seconds)
- **Immutable**: Assets never change (content-hashed filenames)

#### Images (`/images/*`)
```json
{
  "route": "/images/*",
  "headers": {
    "cache-control": "public, max-age=86400"
  }
}
```
- **Purpose**: Cache public images
- **Cache Duration**: 24 hours (86400 seconds)

#### Favicon
```json
{
  "route": "/favicon.ico",
  "headers": {
    "cache-control": "public, max-age=86400"
  }
}
```
- **Purpose**: Cache favicon
- **Cache Duration**: 24 hours

#### All Other Routes (`/*`)
```json
{
  "route": "/*",
  "headers": {
    "cache-control": "public, max-age=0, must-revalidate"
  }
}
```
- **Purpose**: No caching for HTML pages (always revalidate)
- **Reason**: Ensures users get the latest version of the app

### 2. Navigation Fallback (SPA Routing)

```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/api/*", "/_next/*", "/images/*", "/backend-api/*", "/*.{js,css,png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}"]
  }
}
```

- **Purpose**: Enable client-side routing for Next.js
- **Behavior**: All routes (except excluded patterns) fallback to `index.html`
- **Excluded**: API routes, static assets, backend API, file extensions
- **Example**: `/dashboard/projects` → serves `index.html`, Next.js handles routing

### 3. Response Overrides (Custom Error Pages)

```json
{
  "responseOverrides": {
    "404": {
      "rewrite": "/404.html",
      "statusCode": 404
    },
    "500": {
      "rewrite": "/500.html",
      "statusCode": 500
    }
  }
}
```

- **404 Not Found**: Custom 404 page (Next.js generates this)
- **500 Server Error**: Custom 500 page (Next.js generates this)
- **Note**: Create custom error pages in `app/404.tsx` and `app/500.tsx`

### 4. Global Headers (Security)

#### X-Content-Type-Options
```
X-Content-Type-Options: nosniff
```
- **Purpose**: Prevent MIME type sniffing
- **Security**: Prevents browsers from interpreting files as a different MIME type

#### X-Frame-Options
```
X-Frame-Options: DENY
```
- **Purpose**: Prevent clickjacking attacks
- **Security**: Prevents the site from being embedded in iframes

#### X-XSS-Protection
```
X-XSS-Protection: 1; mode=block
```
- **Purpose**: Enable browser XSS protection
- **Security**: Blocks pages when XSS attack is detected

#### Referrer-Policy
```
Referrer-Policy: strict-origin-when-cross-origin
```
- **Purpose**: Control referrer information
- **Security**: Only send origin when crossing origins

#### Permissions-Policy
```
Permissions-Policy: camera=(), microphone=(), geolocation=()
```
- **Purpose**: Disable unnecessary browser features
- **Security**: Prevents unauthorized access to camera, microphone, geolocation

#### Content-Security-Policy (CSP)
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline' https://js.stripe.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https: blob:; connect-src 'self' https://*.supabase.co https://api.stripe.com wss://*.supabase.co; frame-src 'self' https://js.stripe.com; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;
```

**Breakdown:**
- `default-src 'self'`: Only load resources from same origin by default
- `script-src`: Allow scripts from self, Stripe, CDN (with eval/inline for Next.js)
- `style-src`: Allow styles from self, Google Fonts (with inline for Tailwind)
- `font-src`: Allow fonts from self, Google Fonts
- `img-src`: Allow images from self, data URIs, HTTPS, blobs
- `connect-src`: Allow connections to self, Supabase, Stripe
- `frame-src`: Allow iframes from self, Stripe
- `object-src 'none'`: Disallow plugins (Flash, etc.)
- `base-uri 'self'`: Restrict base tag to same origin
- `form-action 'self'`: Forms can only submit to same origin
- `frame-ancestors 'none'`: Prevent embedding (same as X-Frame-Options)
- `upgrade-insecure-requests`: Upgrade HTTP to HTTPS

**Note**: Adjust CSP if you add new third-party services.

### 5. MIME Types

```json
{
  "mimeTypes": {
    ".json": "application/json",
    ".js": "text/javascript",
    ".css": "text/css",
    ".html": "text/html",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".eot": "application/vnd.ms-fontobject"
  }
}
```

- **Purpose**: Ensure correct MIME types for file extensions
- **Reason**: Prevents MIME type mismatches that can cause loading issues

### 6. Platform

```json
{
  "platform": {
    "apiRuntime": "node:18"
  }
}
```

- **Purpose**: Specify Node.js runtime version for API routes
- **Version**: Node.js 18 (matches project requirements)

## Deployment Instructions

### Prerequisites

1. Azure account with Static Web Apps enabled
2. GitHub repository connected to Azure Static Web Apps
3. Backend API deployed (Azure App Service or other)

### Step 1: Configure Environment Variables

In Azure Portal → Static Web App → Configuration, add:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-production-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_supabase_anon_key
NEXT_PUBLIC_API_URL=https://pixcrawler-api.azurewebsites.net
NEXT_PUBLIC_APP_URL=https://pixcrawler.io
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
CONTACT_EMAIL=contact@pixcrawler.io
FROM_EMAIL=noreply@pixcrawler.io
NODE_ENV=production
```

### Step 2: Configure Build Settings

In Azure Portal → Static Web App → Configuration:

- **App location**: `/frontend`
- **API location**: (leave empty if no Azure Functions)
- **Output location**: `.next`
- **Build command**: `bun run build` (or `npm run build`)
- **Install command**: `bun install` (or `npm install`)

### Step 3: Configure Backend API Proxy (Optional)

If using Azure Static Web Apps managed functions:

1. Create `api` folder in frontend directory
2. Add Azure Functions for backend proxy
3. Update `staticwebapp.config.json` routes

**Alternative**: Use `NEXT_PUBLIC_API_URL` to point directly to backend (recommended).

### Step 4: Deploy

```bash
# Option 1: Automatic deployment via GitHub Actions
# Push to main branch, Azure Static Web Apps will auto-deploy

# Option 2: Manual deployment via Azure CLI
az staticwebapp create \
  --name pixcrawler-frontend \
  --resource-group pixcrawler-rg \
  --source https://github.com/your-org/pixcrawler \
  --location "East US 2" \
  --branch main \
  --app-location "/frontend" \
  --output-location ".next" \
  --login-with-github
```

### Step 5: Configure Custom Domain (Optional)

1. Go to Azure Portal → Static Web App → Custom domains
2. Add your custom domain (e.g., `pixcrawler.io`)
3. Update DNS records as instructed
4. Update `NEXT_PUBLIC_APP_URL` to match custom domain

### Step 6: Verify Deployment

1. Check deployment logs in Azure Portal
2. Visit your Static Web App URL
3. Test API connectivity to backend
4. Verify security headers (use securityheaders.com)
5. Test error pages (404, 500)
6. Verify caching headers (use browser DevTools)

## Troubleshooting

### Issue: 404 on Client-Side Routes

**Cause**: Navigation fallback not working

**Solution**: Verify `navigationFallback` is configured correctly and excludes API routes.

### Issue: API Requests Failing

**Cause**: CORS or backend API URL misconfigured

**Solution**: 
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check backend CORS configuration allows your frontend domain
3. Verify backend is running and accessible

### Issue: CSP Violations

**Cause**: Third-party scripts/styles blocked by CSP

**Solution**: Update `Content-Security-Policy` to allow the required domains.

### Issue: Static Assets Not Caching

**Cause**: Cache headers not applied

**Solution**: Verify route order in `staticwebapp.config.json` (more specific routes first).

### Issue: Custom Error Pages Not Showing

**Cause**: Error pages not generated by Next.js

**Solution**: Create `app/404.tsx` and `app/500.tsx` pages.

## Security Best Practices

1. **HTTPS Only**: Always use HTTPS in production (Azure Static Web Apps provides this)
2. **Environment Variables**: Never commit secrets to git
3. **CSP**: Keep Content-Security-Policy strict, only allow necessary domains
4. **CORS**: Configure backend to only allow your frontend domain
5. **Rate Limiting**: Enable rate limiting in backend API
6. **Monitoring**: Set up Azure Monitor for error tracking

## Performance Optimization

1. **Static Assets**: Aggressively cached (1 year)
2. **Images**: Cached for 24 hours
3. **HTML**: No caching (always fresh)
4. **CDN**: Azure Static Web Apps uses Azure CDN automatically
5. **Compression**: Gzip/Brotli enabled by default

## References

- [Azure Static Web Apps Configuration](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Security Headers](https://securityheaders.com/)
