# Multi-stage build dla aplikacji Next.js
FROM node:18-alpine AS base

# Instalacja zależności tylko gdy potrzebne
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Kopiowanie plików package
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Etap budowania
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build aplikacji
RUN npm run build

# Etap produkcyjny
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Kopiowanie plików publicznych
COPY --from=builder /app/public ./public

# Kopiowanie plików buildowanych
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
