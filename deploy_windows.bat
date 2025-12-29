@echo off
chcp 65001 >nul
echo ========================================
echo   AI-CARE Lung 一鍵部署到 GitHub
echo ========================================
echo.

REM 設定變數（請修改這裡）
set REPO_NAME=aicare-lung-patient
set GITHUB_USERNAME=您的GitHub帳號

echo [1/5] 初始化 Git...
git init

echo [2/5] 添加所有檔案...
git add .

echo [3/5] 建立 commit...
git commit -m "Initial commit: AI-CARE Lung v2.0"

echo [4/5] 設定分支...
git branch -M main

echo.
echo ========================================
echo   請先到 GitHub 建立新的 Repository
echo   名稱: %REPO_NAME%
echo   設為 Public 或 Private
echo   不要勾選 "Add a README file"
echo ========================================
echo.
pause

echo [5/5] 推送到 GitHub...
git remote add origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git
git push -u origin main

echo.
echo ========================================
echo   完成！
echo.
echo   接下來請到 Streamlit Cloud 部署：
echo   1. 前往 https://share.streamlit.io/
echo   2. 點擊 New app
echo   3. 選擇 %REPO_NAME%
echo   4. Main file path: app.py
echo   5. Deploy!
echo ========================================
pause
