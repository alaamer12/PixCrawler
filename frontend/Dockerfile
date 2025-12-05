# ============================================================================
# Stage 1: Dependencies
# ============================================================================
FROM node:18-alpine AS deps

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json bun.lockb* package-lock.json* yarn.lock* pnpm-lock.yaml* ./

RUN \
    if [ -f bun.lockb ]; then \
    npm install -g bun && bun install --frozen-lockfile; \
    elif [ -f yarn.lock ]; then \
    yarn --frozen-lockfile; \
    elif [ -f package-lock.json ]; then \
    npm ci; \
    elif [ -f pnpm-lock.yaml ]; then \
    npm install -g pnpm && pnpm install --frozen-lockfile; \
    else \
    echo "No lockfile found. Running npm install..."; \
    npm install; \
    fi

# ============================================================================
# Stage 2: Builder
# ============================================================================
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Generate image manifest
RUN node scripts/generateImageManifest.js || echo "Image manifest generation skipped"

# Build Next.js application
RUN \
    if [ -f bun.lockb ]; then \
    npm install -g bun && bun run build; \
    else \
    npm run build; \
    fi

# ============================================================================
# Stage 3: Runner
# ============================================================================
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set correct permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start Next.js server
CMD ["node", "server.js"]
