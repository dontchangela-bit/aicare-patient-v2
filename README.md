# AI-CARE Lung 病人端 v2.2

肺癌術後智慧照護系統 - 病人端介面

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

## 🆕 v2.2 新功能

- ✅ **AI 語音電話 Demo** - 模擬 Bland AI 語音機器人主動撥打電話
- ✅ 基於 MDASI-LC 的對話式症狀評估
- ✅ 即時警示等級判定（紅/黃/綠燈）
- ✅ 完整對話流程體驗

## 📱 三種回報方式

| 方式 | 說明 | 適用場景 |
|------|------|----------|
| 💬 **AI 對話回報** | 文字對話式症狀回報 | 喜歡打字的用戶 |
| 📋 **數位問卷回報** | 快速問卷式回報 | 快速完成回報 |
| 📞 **AI 語音電話** | 模擬語音電話追蹤 | 體驗被動接聽 Demo |

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
├── voice_call_demo.py        # AI 語音電話 Demo 模組 ⭐ 新增
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
| 📞 AI 語音電話 | 模擬 Bland AI 語音電話 ⭐ |
| 📊 歷史紀錄 | 查看過去回報 |
| 🎖️ 成就系統 | 遊戲化激勵 |
| 📚 衛教資訊 | 術後照護知識 |
| 🎮 Demo 模式 | 無需登入體驗 |

---

## 📞 AI 語音電話功能說明

### 功能特色

1. **來電模擬**：模擬手機來電畫面，顯示來電者資訊
2. **語音對話**：基於 MDASI-LC 量表的結構化對話流程
3. **即時評估**：通話結束後顯示症狀評估報告
4. **警示機制**：自動判定紅/黃/綠燈警示等級

### 對話流程

```
來電接聽 → 問候確認 → 整體評估 → 疼痛評估 → 
呼吸評估 → 疲勞評估 → 咳嗽評估 → 睡眠食慾 → 
安全檢查 → 其他問題 → 總結道別 → 報告生成
```

### 警示規則

| 等級 | 條件 | 行動 |
|------|------|------|
| 🔴 紅燈 | 疼痛≥7, 呼吸困難≥6, 發燒, 傷口異常 | 30分鐘內聯繫 |
| 🟡 黃燈 | 疼痛4-6, 呼吸困難4-5, 整體5-7 | 當日追蹤 |
| 🟢 綠燈 | 所有症狀<4 | 常規監控 |

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

## 🔮 未來規劃

- [ ] 整合 Bland AI 真實語音通話
- [ ] LINE Bot 整合
- [ ] 多中心部署支援
- [ ] 個管師後台系統

---

## 📞 聯絡

三軍總醫院 數位醫療中心

---

## License

MIT License
