# AI-CARE Lung 病人端 v2.0

肺癌術後智慧照護系統 - 病人端介面

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

## 🚀 部署到 Streamlit Cloud

### 步驟 1：上傳到 GitHub

```bash
# 建立新的 GitHub repo，然後：
git init
git add .
git commit -m "Initial commit: AI-CARE Lung v2.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/aicare-lung-patient.git
git push -u origin main
```

### 步驟 2：連接 Streamlit Cloud

1. 前往 [share.streamlit.io](https://share.streamlit.io/)
2. 點擊 **New app**
3. 選擇您的 GitHub repo
4. Main file path: `app.py`
5. 點擊 **Deploy!**

### 步驟 3：完成！

部署完成後會得到一個網址，例如：
```
https://aicare-lung-patient.streamlit.app
```

---

## 📁 檔案結構

```
aicare-lung-patient/
├── .streamlit/
│   └── config.toml        # Streamlit 設定
├── app.py                 # 主程式
├── models.py              # 資料模型
├── conversation_store.py  # 對話儲存模組
├── expert_templates.py    # 專家回應範本
├── requirements.txt       # 相依套件
├── .gitignore
└── README.md
```

---

## ✨ v2.0 新功能

| 功能 | 說明 |
|------|------|
| **分離儲存** | 病人輸入 vs AI 回應分開儲存 |
| **開放式問題** | 收集自然語言描述 |
| **專家範本** | 護理師撰寫的標準回應 |
| **資料匯出** | JSON 格式供標註使用 |

---

## 🖥️ 本地執行

```bash
# 安裝套件
pip install -r requirements.txt

# 執行
streamlit run app.py
```

---

## 📊 資料收集重點

| 資料類型 | 訓練價值 |
|---------|:--------:|
| 病人文字輸入 | ⭐⭐⭐⭐⭐ |
| 開放式回答 | ⭐⭐⭐⭐⭐ |
| 專家範本回應 | ⭐⭐⭐⭐ |
| 按鈕點擊 | ⭐⭐ |
| AI 生成回應 | ⭐ |

---

## ⚠️ 注意事項

- 目前為 **Demo 模式**，使用模擬病人資料
- 資料儲存在記憶體中，重啟會清除
- 預設範本需經護理師審核後正式啟用

---

## 📞 聯絡

三軍總醫院 數位醫療中心

---

## License

MIT License
