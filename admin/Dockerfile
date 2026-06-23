# Moufida admin / observability SPA — build with Vite, serve static via nginx.
FROM node:20-slim AS build
WORKDIR /app
COPY admin/package.json ./
RUN npm install
COPY admin/ ./
RUN npm run build

FROM nginx:alpine
COPY admin/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3002
CMD ["nginx", "-g", "daemon off;"]
