#!/bin/bash
# GitHub 推送辅助脚本
# 在当前目录下执行此脚本，可将本地仓库推送到 GitHub

set -e

REPO_NAME="baozhong-ai-platform-training"
OWNER="guanwenjie928"

echo "========================================"
echo "GitHub 仓库推送脚本"
echo "========================================"
echo ""

# 1. 确保已登录 GitHub CLI
if ! gh auth status &>/dev/null; then
    echo "请先登录 GitHub CLI："
    echo "  gh auth login"
    echo ""
    exit 1
fi

# 2. 创建远程仓库（如果不存在）
if ! git remote get-url origin &>/dev/null; then
    echo "正在 GitHub 上创建仓库 ${REPO_NAME} ..."
    gh repo create "${REPO_NAME}" --public --source=. --remote=origin --push
    echo "仓库已创建并推送完成！"
else
    echo "远程仓库 origin 已存在"
    echo "正在推送到 GitHub ..."
    git push -u origin main
    echo "推送完成！"
fi

echo ""
echo "仓库地址: https://github.com/${OWNER}/${REPO_NAME}"
