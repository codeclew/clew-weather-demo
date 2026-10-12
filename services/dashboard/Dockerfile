FROM node:24.21.0-bookworm-slim AS build
WORKDIR /app/services/dashboard
COPY services/dashboard/package*.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY services/dashboard/tsconfig.json ./
COPY services/dashboard/src ./src
RUN npm run build
FROM node:24.21.0-bookworm-slim
WORKDIR /app/services/dashboard
COPY --from=build /app/services/dashboard/node_modules ./node_modules
COPY --from=build /app/services/dashboard/package.json ./package.json
COPY --from=build /app/services/dashboard/dist ./dist
COPY services/dashboard/public ./public
COPY contracts /app/contracts
CMD ["node","dist/main.js"]
