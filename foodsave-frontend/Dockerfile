# Base Node.js image
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Install dependencies only when needed (leveraging Docker cache)
FROM base AS deps
COPY package.json package-lock.json* ./

# Install dependencies with clean installation (ci is preferred for reproducible builds)
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build application (fail if build fails - no || true)
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

# Copy necessary files from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

# Create a non-root user and switch to it
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app/.next
USER nextjs

# Expose the listening port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]
