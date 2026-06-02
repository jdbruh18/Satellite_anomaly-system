### Build stage
FROM node:18-alpine AS build
WORKDIR /app
ARG VITE_API_BASE
ENV VITE_API_BASE=${VITE_API_BASE}
COPY package.json package-lock.json* ./
COPY src ./src
COPY index.html ./
RUN npm install --no-audit --no-fund
RUN npm run build

### Production stage
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["/bin/sh", "-c", "nginx -g 'daemon off;' "]
