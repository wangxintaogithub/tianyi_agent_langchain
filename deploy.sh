#!/usr/bin/env bash
# ============================================================
# 部署脚本 - 在腾讯云服务器上执行
# 由 GitHub Actions CI 通过 SSH 调用
# ============================================================
set -euo pipefail

APP_DIR="/home/ubuntu/tianyi_agent_langchain"

echo "===== 1. 进入项目目录 ====="
cd "$APP_DIR" || { echo "❌ 目录 $APP_DIR 不存在"; exit 1; }

echo "===== 2. 拉取最新代码（配置 Git 兼容参数） ====="
git config http.version HTTP/1.1
git config http.postBuffer 524288000
git pull

echo "===== 3. 清理旧 .env 文件（Docker Compose 会自动读取） ====="
rm -f .env

echo "===== 4. 停止旧容器 ====="
docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true

echo "===== 5. 启动容器（镜像已由 CI 通过 SCP 传入） ====="
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "===== 6. 清理旧镜像 ====="
docker image prune -f

echo "===== 7. 检查容器状态 ====="
sleep 3
docker ps

echo "===== ✅ 部署完成 ====="
