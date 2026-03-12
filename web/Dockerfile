FROM node:22-alpine AS builder
WORKDIR /app

# Copy workspace config first (better layer caching)
COPY package.json yarn.lock .yarnrc.yml turbo.json ./

# Copy package manifests before source (layer cache for yarn install)
COPY packages/tsconfig/package.json packages/tsconfig/
COPY packages/types/package.json     packages/types/
COPY packages/utils/package.json     packages/utils/
COPY packages/api/package.json       packages/api/
COPY packages/ui/package.json        packages/ui/
COPY apps/wps-web/package.json       apps/wps-web/

RUN yarn install --immutable

# Copy all source
COPY packages/ packages/
COPY apps/wps-web/ apps/wps-web/

RUN yarn turbo build

FROM nginx:alpine
COPY --from=builder /app/apps/wps-web/build /usr/share/nginx/html
