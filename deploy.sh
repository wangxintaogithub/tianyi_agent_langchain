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
# 切换到 SSH 协议（HTTPS 在国内容易 TLS 中断）
REMOTE_URL=$(git remote get-url origin)
if echo "$REMOTE_URL" | grep -q '^https://'; then
  SSH_URL=$(echo "$REMOTE_URL" | sed 's|https://github.com/|git@github.com:|')
  git remote set-url origin "$SSH_URL"
  echo "已将 remote 切换为 SSH: $SSH_URL"
fi
git config http.version HTTP/1.1
git config http.postBuffer 524288000
git config http.lowSpeedLimit 0
git config http.lowSpeedTime 999999
git pull

echo "===== 3. 清理旧 .env 文件 ====="
rm -f .env

echo "===== 4. 停止旧容器 ====="
docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true

echo "===== 5. 重新构建并启动 ====="
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "===== 6. 清理旧镜像 ====="
docker image prune -f

echo "===== 7. 检查容器状态 ====="
sleep 3
docker ps

echo "===== ✅ 部署完成 ====="
