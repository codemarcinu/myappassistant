# Multi-stage build dla aplikacji Next.js
FROM node:18-alpine AS base

# Instalacja wget dla health check
RUN apk add --no-cache wget

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

# Sprawdzenie wersji Next.js
RUN npm list next

# Build aplikacji z dodatkowymi logami
RUN npm run build

# Sprawdzenie struktury plików po buildzie
RUN ls -la /app/.next

# Etap produkcyjny
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Kopiowanie plików publicznych
COPY --from=builder /app/public ./public

# Kopiowanie plików buildowanych - poprawiona struktura dla standalone
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Sprawdzenie czy plik server.js istnieje
RUN ls -la /app/

USER nextjs

EXPOSE 3000

# Health check dla frontendu
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
