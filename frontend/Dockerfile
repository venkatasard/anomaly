FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm install
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --chown=node:node --from=build /app/.next ./.next
COPY --chown=node:node --from=build /app/node_modules ./node_modules
COPY --chown=node:node --from=build /app/package.json ./
EXPOSE 3000
USER node
CMD ["npm","start"]
