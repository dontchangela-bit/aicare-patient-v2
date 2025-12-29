# AI-CARE Lung 病人端 v2.1

肺癌術後智慧照護系統 - 病人端介面

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

## 🆕 v2.1 新功能

- ✅ **病人註冊/登入系統**
- ✅ **Google Sheet 雲端資料庫**
- ✅ **多用戶支援**
- ✅ **資料雲端同步**
- ✅ **Demo 體驗模式**

---

## 🚀 快速開始

### 方式 1：Demo 模式（無需設定）

直接部署到 Streamlit Cloud，使用 Demo 模式體驗功能。

### 方式 2：完整功能（需設定 Google Sheet）

詳見 [GOOGLE_SHEET_SETUP.md](GOOGLE_SHEET_SETUP.md)

---

## 📁 檔案結構

```
aicare-lung-patient/
├── .streamlit/
│   ├── config.toml           # Streamlit 設定
│   └── secrets.toml          # 憑證設定（需自行建立）
├── app.py                    # 主程式
├── google_sheet_db.py        # Google Sheet 資料庫模組
├── models.py                 # 資料模型
├── conversation_store.py     # 對話儲存模組
├── expert_templates.py       # 專家回應範本
├── requirements.txt          # 相依套件
├── secrets.toml.example      # 憑證範例
├── GOOGLE_SHEET_SETUP.md     # Google Sheet 設定指南
└── README.md
```

---

## 🔧 功能列表

| 功能 | 說明 |
|------|------|
| 🔐 病人登入/註冊 | 使用病歷號碼和密碼 |
| 💬 AI 對話回報 | 對話式症狀回報 |
| 📋 數位問卷回報 | 快速問卷式回報 |
| 📊 歷史紀錄 | 查看過去回報 |
| 🎖️ 成就系統 | 遊戲化激勵 |
| 📚 衛教資訊 | 術後照護知識 |
| 🎮 Demo 模式 | 無需登入體驗 |

---

## 🖥️ 本地執行

```bash
# 安裝套件
pip install -r requirements.txt

# 執行
streamlit run app.py
```

---

## ☁️ Streamlit Cloud 部署

1. 將程式碼推送到 GitHub
2. 前往 [share.streamlit.io](https://share.streamlit.io/)
3. 連結您的 GitHub repo
4. Main file path: `app.py`
5. 設定 Secrets（如需使用 Google Sheet）
6. Deploy!

---

## 📞 聯絡

三軍總醫院 數位醫療中心

---

## License

MIT License
