FROM node:20-slim AS builder

WORKDIR /app

# 安装bun
RUN npm install -g bun

# 复制依赖文件
COPY package.json bun.lock* ./

# 安装依赖
RUN bun install

# 复制源代码
COPY . .

# 构建
RUN bun run build

# 生产阶段
FROM caddy:2-alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/caddy

# 复制Caddy配置
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]
