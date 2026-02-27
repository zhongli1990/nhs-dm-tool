FROM node:20-alpine AS deps

WORKDIR /app/services/frontend
COPY services/frontend/package.json services/frontend/package-lock.json ./
RUN npm ci --production=false

# ---------- Build stage ----------
FROM node:20-alpine AS builder
ARG NEXT_PUBLIC_DM_API_BASE=http://localhost:9134
ARG DM_INTERNAL_API_BASE=http://backend:9134
ARG NEXT_PUBLIC_DMM_VERSION=0.2.4

WORKDIR /app

# Copy data files needed for server-side rendering at build time
COPY schemas/ /app/schemas/
COPY reports/ /app/reports/
COPY mock_data/ /app/mock_data/

WORKDIR /app/services/frontend
COPY services/frontend/ ./
COPY --from=deps /app/services/frontend/node_modules ./node_modules

ENV DM_DATA_ROOT=/app
ENV NEXT_PUBLIC_DM_API_BASE=${NEXT_PUBLIC_DM_API_BASE}
ENV DM_INTERNAL_API_BASE=${DM_INTERNAL_API_BASE}
ENV NEXT_PUBLIC_DMM_VERSION=${NEXT_PUBLIC_DMM_VERSION}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---------- Production stage ----------
FROM node:20-alpine AS runner
ARG NEXT_PUBLIC_DM_API_BASE=http://localhost:9134
ARG DM_INTERNAL_API_BASE=http://backend:9134
ARG NEXT_PUBLIC_DMM_VERSION=0.2.4

LABEL maintainer="OpenLI DMM <support@openli.local>"
LABEL description="OpenLI DMM Frontend - Next.js migration control plane"

RUN addgroup -g 1001 -S dmm && adduser -S dmm -u 1001 -G dmm

WORKDIR /app

# Copy data files for server-side rendering at runtime
COPY --from=builder /app/schemas/ /app/schemas/
COPY --from=builder /app/reports/ /app/reports/
COPY --from=builder /app/mock_data/ /app/mock_data/

WORKDIR /app/services/frontend

COPY --from=builder --chown=dmm:dmm /app/services/frontend/.next ./.next
COPY --from=builder --chown=dmm:dmm /app/services/frontend/node_modules ./node_modules
COPY --from=builder --chown=dmm:dmm /app/services/frontend/package.json ./package.json
COPY --from=builder --chown=dmm:dmm /app/services/frontend/next.config.mjs ./next.config.mjs

ENV NODE_ENV=production
ENV DM_DATA_ROOT=/app
ENV NEXT_PUBLIC_DM_API_BASE=${NEXT_PUBLIC_DM_API_BASE}
ENV DM_INTERNAL_API_BASE=${DM_INTERNAL_API_BASE}
ENV NEXT_PUBLIC_DMM_VERSION=${NEXT_PUBLIC_DMM_VERSION}
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

EXPOSE 3000

USER dmm

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["npm", "start"]
