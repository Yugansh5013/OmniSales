# ── Stage 1: Install dependencies ──
FROM node:20-alpine AS deps
WORKDIR /app
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci --ignore-scripts

# ── Stage 2: Build ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY dashboard/ .

# NEXT_PUBLIC_* vars are baked at build time.
# This is the URL the BROWSER uses to reach the API gateway.
# When running via docker-compose, port 8000 is mapped to localhost.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Enable standalone output for minimal Docker image
RUN echo "const nextConfig = { output: 'standalone', reactCompiler: true }; export default nextConfig;" > next.config.mjs && \
    rm -f next.config.ts

RUN npm run build

# ── Stage 3: Production runner ──
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy standalone server + static assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
