# --- Admin Frontend React Dockerfile ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_BACKEND_API_URL
ARG VITE_PROXY_TARGET
ENV VITE_BACKEND_API_URL=$VITE_BACKEND_API_URL
ENV VITE_PROXY_TARGET=$VITE_PROXY_TARGET
RUN npm run build

FROM node:20-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 4000
CMD ["npm", "run", "dev"]

FROM nginx:alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 4000
CMD ["nginx", "-g", "daemon off;"]
