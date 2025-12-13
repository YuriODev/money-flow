# =============================================================================
# Money Flow Frontend - Multi-stage Docker Build
# =============================================================================
# Optimized Next.js production build with minimal image size
#
# Build stages:
#   1. base - Alpine Node.js base image
#   2. deps - Install dependencies
#   3. builder - Build the Next.js application
#   4. runner - Production runtime image
#
# Usage:
#   docker build -t money-flow-frontend .
#   docker run -p 3000:3000 money-flow-frontend
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base - Alpine Node.js base image
# -----------------------------------------------------------------------------
FROM node:20-alpine AS base

# -----------------------------------------------------------------------------
# Stage 2: Dependencies - Install npm packages
# -----------------------------------------------------------------------------
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production=false

# -----------------------------------------------------------------------------
# Stage 3: Development - For local development
# -----------------------------------------------------------------------------
FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

CMD ["npm", "run", "dev"]

# -----------------------------------------------------------------------------
# Stage 4: Builder - Build the production application
# -----------------------------------------------------------------------------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments for environment variables
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 5: Runner - Production runtime image
# -----------------------------------------------------------------------------
FROM base AS runner
WORKDIR /app

# Security: Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Security: Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only necessary files for production
COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next && chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Security: Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run the application
CMD ["node", "server.js"]
