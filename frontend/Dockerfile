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
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
