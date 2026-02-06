# ========================================
# Stage 1: Dependencies
# ========================================
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# ========================================
# Stage 2: Builder
# ========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies)
RUN npm ci

# Copy source code
COPY . .

# Build Next.js application
RUN npm run build

# ========================================
# Stage 3: Runner (Production)
# ========================================
FROM node:20-alpine AS runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from deps stage
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy necessary files from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package*.json ./
COPY --from=builder --chown=nextjs:nodejs /app/next.config.mjs ./
COPY --from=builder --chown=nextjs:nodejs /app/server.js ./

# Copy additional necessary files
COPY --from=builder --chown=nextjs:nodejs /app/app ./app
COPY --from=builder --chown=nextjs:nodejs /app/components ./components

# Create logs directory
RUN mkdir -p logs && chown -R nextjs:nodejs logs

# Create boards.json if it doesn't exist
RUN touch boards.json && chown nextjs:nodejs boards.json

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start the application
CMD ["npm", "start"]
