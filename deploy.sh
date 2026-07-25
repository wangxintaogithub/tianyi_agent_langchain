#!/usr/bin/env bash
# ============================================================
# 部署脚本 - 在腾讯云服务器上执行
# 由 GitHub Actions CI 通过 SSH 调用
# ============================================================
set -euo pipefail

APP_DIR="/home/ubuntu/tianyi_agent_langchain"

echo "===== 1. 进入项目目录 ====="
cd "$APP_DIR" || { echo "❌ 目录 $APP_DIR 不存在"; exit 1; }

echo "===== 2. 拉取最新代码 ====="
git pull

echo "===== 3. 检查 .env 文件 ====="
if [ ! -f .env ]; then
  echo "❌ .env 文件不存在，请先通过 CI 传输"
  exit 1
fi
echo "✅ .env 文件存在"

echo "===== 4. 检查 Docker Compose ====="
docker compose version || docker-compose --version || { echo "❌ Docker Compose 不可用"; exit 1; }

echo "===== 5. 停止旧容器 ====="
docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true

echo "===== 6. 重新构建并启动 ====="
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "===== 7. 清理旧镜像 ====="
docker image prune -f

echo "===== 8. 检查容器状态 ====="
sleep 3
docker ps

echo "===== ✅ 部署完成 ====="
