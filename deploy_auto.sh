#!/bin/bash
# ============================================
# AI-CARE Lung 全自動部署腳本
# 需要安裝 GitHub CLI (gh)
# ============================================

echo "========================================"
echo "  AI-CARE Lung 全自動部署"
echo "========================================"
echo ""

# 設定變數
REPO_NAME="aicare-lung-patient"
REPO_DESC="AI-CARE Lung 肺癌術後智慧照護系統 - 病人端"

# 檢查 gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ 請先安裝 GitHub CLI"
    echo ""
    echo "安裝方式："
    echo "  Mac:     brew install gh"
    echo "  Windows: winget install GitHub.cli"
    echo "  Linux:   https://github.com/cli/cli#installation"
    echo ""
    exit 1
fi

# 檢查是否已登入
if ! gh auth status &> /dev/null; then
    echo "📝 請先登入 GitHub..."
    gh auth login
fi

echo "[1/4] 初始化 Git..."
git init
git add .
git commit -m "Initial commit: AI-CARE Lung v2.0"
git branch -M main

echo "[2/4] 在 GitHub 建立 Repository..."
gh repo create $REPO_NAME --public --description "$REPO_DESC" --source=. --remote=origin --push

echo "[3/4] 推送完成！"

echo "[4/4] 取得 Streamlit 部署連結..."
GITHUB_USER=$(gh api user -q .login)
echo ""
echo "========================================"
echo "  ✅ 部署完成！"
echo ""
echo "  GitHub Repo:"
echo "  https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "  Streamlit Cloud 部署："
echo "  1. 前往 https://share.streamlit.io/"
echo "  2. 點擊 New app"
echo "  3. 選擇 $REPO_NAME"
echo "  4. Main file path: app.py"
echo "  5. Deploy!"
echo "========================================"
