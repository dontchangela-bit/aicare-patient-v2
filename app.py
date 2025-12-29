"""
AI-CARE Lung 病人端應用程式 v2.0
================================
肺癌術後智慧照護系統 - 病人端介面

更新內容：
1. 分離儲存病人輸入 vs AI 回應
2. 新增開放式問題收集
3. 整合專家回應範本
4. 為未來 NLP 訓練準備資料

三軍總醫院 數位醫療中心
"""

import streamlit as st
from datetime import datetime, timedelta, date
import json
import uuid

# 匯入更新版模組
from models import (
    SymptomType, ReportMethod, MessageRole, MessageSource,
    SYMPTOM_DEFINITIONS, OPEN_ENDED_QUESTIONS, DEFAULT_ACHIEVEMENTS,
    generate_report_id, generate_session_id
)
from conversation_store import (
    conversation_store, log_patient_input, log_ai_response,
    log_open_ended_response
)
from expert_templates import (
    template_manager, get_expert_response, get_symptom_response
)

# ============================================
# 頁面配置
# ============================================
st.set_page_config(
    page_title="AI-CARE Lung 照護系統",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 自定義 CSS 樣式
# ============================================
st.markdown("""
<style>
/* 主題顏色 */
:root {
    --primary: #0891b2;
    --primary-light: #22d3ee;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --bg-card: #f8fafc;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
}

/* 隱藏 Streamlit 預設元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 主容器 */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 100%;
}

/* 歡迎卡片 */
.welcome-card {
    background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(8, 145, 178, 0.3);
}

.welcome-card h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    font-weight: 600;
}

.welcome-card p {
    margin: 0;
    opacity: 0.9;
    font-size: 0.95rem;
}

/* 狀態卡片 */
.status-card {
    background: white;
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.status-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.status-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.status-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0.25rem 0;
}

.status-label {
    font-size: 0.85rem;
    color: #64748b;
}

/* 回報按鈕 */
.report-button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border-radius: 16px;
    padding: 1.5rem;
    color: white;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
    margin: 1rem 0;
}

.report-button:hover {
    transform: scale(1.02);
    box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
}

.report-button-disabled {
    background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
    box-shadow: none;
}

/* 對話氣泡 */
.chat-bubble {
    padding: 1rem 1.25rem;
    border-radius: 16px;
    margin: 0.5rem 0;
    max-width: 85%;
    line-height: 1.5;
}

.chat-assistant {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #bae6fd;
    margin-right: auto;
}

.chat-user {
    background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
    color: white;
    margin-left: auto;
}

/* 開放式問題區 */
.open-question-card {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 2px solid #f59e0b;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.open-question-title {
    color: #92400e;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.open-question-hint {
    color: #b45309;
    font-size: 0.85rem;
    opacity: 0.8;
}

/* 資料收集提示 */
.data-notice {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 1rem;
    font-size: 0.85rem;
    color: #166534;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 症狀定義
# ============================================
SYMPTOMS = [
    {"id": "pain", "name": "疼痛", "icon": "🩹", "question": "今天傷口或胸部的疼痛程度如何？"},
    {"id": "fatigue", "name": "疲勞", "icon": "😮‍💨", "question": "今天感覺疲勞或虛弱嗎？"},
    {"id": "dyspnea", "name": "呼吸困難", "icon": "💨", "question": "今天呼吸順暢嗎？有沒有喘或胸悶？"},
    {"id": "cough", "name": "咳嗽", "icon": "🤧", "question": "今天咳嗽的情況如何？"},
    {"id": "sleep", "name": "睡眠", "icon": "😴", "question": "昨晚睡得好嗎？"},
    {"id": "appetite", "name": "食慾", "icon": "🍽️", "question": "今天胃口怎麼樣？"},
    {"id": "mood", "name": "心情", "icon": "💭", "question": "今天心情如何？有沒有焦慮或擔心？"}
]

SCORE_OPTIONS = {
    0: {"label": "完全沒有", "color": "#10b981"},
    1: {"label": "非常輕微", "color": "#22c55e"},
    2: {"label": "輕微", "color": "#84cc16"},
    3: {"label": "輕度", "color": "#a3e635"},
    4: {"label": "中等偏輕", "color": "#facc15"},
    5: {"label": "中等", "color": "#fbbf24"},
    6: {"label": "中等偏重", "color": "#f59e0b"},
    7: {"label": "明顯", "color": "#fb923c"},
    8: {"label": "嚴重", "color": "#f97316"},
    9: {"label": "非常嚴重", "color": "#ef4444"},
    10: {"label": "極度嚴重", "color": "#dc2626"}
}

# ============================================
# Session State 初始化
# ============================================
def init_session_state():
    """初始化 Session State"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_page = "home"
        
        # 模擬病人資料
        st.session_state.patient = {
            "id": "P001",
            "name": "王先生",
            "gender": "男",
            "age": 62,
            "surgery_date": (datetime.now() - timedelta(days=14)).date(),
            "post_op_day": 14,
            "surgery_type": "胸腔鏡右上肺葉切除術",
            "cancer_stage": "IA"
        }
        
        # 順從度資料
        st.session_state.compliance = {
            "current_streak": 7,
            "best_streak": 12,
            "total_completed": 12,
            "total_days": 14,
            "points": 180,
            "level": 3
        }
        
        # 今日回報狀態
        st.session_state.today_reported = False
        
        # 成就
        st.session_state.achievements = [
            {"id": "first_report", "name": "初次回報", "icon": "🌟", "unlocked": True, "date": "2024-12-15"},
            {"id": "streak_3", "name": "連續3天", "icon": "🌱", "unlocked": True, "date": "2024-12-18"},
            {"id": "streak_7", "name": "連續7天", "icon": "🔥", "unlocked": True, "date": "2024-12-22"},
            {"id": "streak_14", "name": "連續14天", "icon": "⭐", "unlocked": False, "date": None},
            {"id": "streak_21", "name": "連續21天", "icon": "🏅", "unlocked": False, "date": None},
            {"id": "first_description", "name": "詳細描述者", "icon": "✍️", "unlocked": False, "date": None},
        ]
        
        # 回報歷史
        st.session_state.report_history = {}
        
        # 對話相關
        st.session_state.chat_messages = []
        st.session_state.current_symptom_index = 0
        st.session_state.current_scores = {}
        st.session_state.current_descriptions = {}  # 新增：症狀描述
        st.session_state.open_ended_responses = []  # 新增：開放式回應
        
        # 對話會話
        st.session_state.conversation_session_id = None

init_session_state()

# ============================================
# 首頁
# ============================================
def render_home():
    """渲染首頁"""
    patient = st.session_state.patient
    compliance = st.session_state.compliance
    
    # 歡迎卡片
    st.markdown(f"""
    <div class="welcome-card">
        <h2>👋 {patient['name']}，您好！</h2>
        <p>今天是術後第 {patient['post_op_day']} 天 | {patient['surgery_type']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 狀態卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">🔥</div>
            <div class="status-value">{compliance['current_streak']}</div>
            <div class="status-label">連續完成天數</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rate = (compliance['total_completed'] / compliance['total_days'] * 100) if compliance['total_days'] > 0 else 0
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">📊</div>
            <div class="status-value">{rate:.0f}%</div>
            <div class="status-label">總完成率</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">⭐</div>
            <div class="status-value">{compliance['points']}</div>
            <div class="status-label">累積積分</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">🏆</div>
            <div class="status-value">Lv.{compliance['level']}</div>
            <div class="status-label">等級</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 今日回報按鈕
    if not st.session_state.today_reported:
        st.markdown("""
        <div class="report-button">
            <h3 style="margin:0; font-size: 1.25rem;">📝 開始今日症狀回報</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">預計 2-3 分鐘完成</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 AI 對話回報", use_container_width=True, type="primary"):
                # 開始新的對話會話
                session = conversation_store.start_session(
                    patient_id=st.session_state.patient["id"],
                    session_type="daily_report"
                )
                st.session_state.conversation_session_id = session.session_id
                st.session_state.current_page = "ai_chat"
                st.session_state.chat_messages = []
                st.session_state.current_symptom_index = 0
                st.session_state.current_scores = {}
                st.session_state.current_descriptions = {}
                st.session_state.open_ended_responses = []
                st.rerun()
        
        with col2:
            if st.button("📋 數位問卷回報", use_container_width=True):
                st.session_state.current_page = "questionnaire"
                st.rerun()
    else:
        st.markdown("""
        <div class="report-button report-button-disabled">
            <h3 style="margin:0; font-size: 1.25rem;">✅ 今日已完成回報</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">感謝您的配合！</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 成就展示
    st.markdown("### 🎖️ 我的成就")
    unlocked = [a for a in st.session_state.achievements if a["unlocked"]]
    if unlocked:
        cols = st.columns(len(unlocked))
        for i, achievement in enumerate(unlocked):
            with cols[i]:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem;">
                    <div style="font-size: 2rem;">{achievement['icon']}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">{achievement['name']}</div>
                </div>
                """, unsafe_allow_html=True)

# ============================================
# AI 對話回報（更新版）
# ============================================
def render_ai_chat():
    """渲染 AI 對話回報頁面（更新版：支援資料收集）"""
    
    st.markdown("### 💬 AI 對話回報")
    st.markdown("與 AI 助手對話，輕鬆完成今日症狀回報")
    
    # 資料收集提示
    st.markdown("""
    <div class="data-notice">
        💡 <strong>小提醒</strong>：您的回答將幫助我們更好地了解您的恢復狀況。
        除了分數外，也歡迎用文字描述您的感受！
    </div>
    """, unsafe_allow_html=True)
    
    # 返回按鈕
    if st.button("← 返回首頁"):
        # 結束會話（如果是中途離開）
        if st.session_state.conversation_session_id:
            conversation_store.end_session(
                st.session_state.conversation_session_id,
                completion_type="abandoned"
            )
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    # 開始對話
    if len(st.session_state.chat_messages) == 0:
        patient = st.session_state.patient
        
        # 嘗試使用專家範本
        context = {
            "patient_name": patient['name'],
            "post_op_day": patient['post_op_day']
        }
        
        welcome_msg, template_id, source = get_expert_response(
            category="greeting",
            context=context
        )
        
        if not welcome_msg:
            # 使用預設歡迎訊息
            welcome_msg = f"""
{patient['name']}您好！我是您的 AI 照護助手 🤖

今天是術後第 **{patient['post_op_day']} 天**，讓我們一起完成今日的症狀回報吧！

整個過程大約 2-3 分鐘，我會依序詢問您 7 個症狀的狀況。

準備好了嗎？讓我們開始吧！
"""
        
        # 記錄 AI 訊息
        log_ai_response(
            patient_id=patient["id"],
            content=welcome_msg,
            source=source if source else MessageSource.AI_GENERATED,
            template_id=template_id
        )
        
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": welcome_msg,
            "source": source.value if source else "ai_generated",
            "template_id": template_id
        })
        
        # 第一個問題
        symptom = SYMPTOMS[0]
        first_question = f"""
**{symptom['icon']} {symptom['name']}評估**

{symptom['question']}

請選擇 0-10 分：
- 0 分：完全沒有
- 1-3 分：輕微
- 4-6 分：中等
- 7-10 分：嚴重

💡 您也可以用文字描述症狀的感覺！
"""
        
        log_ai_response(
            patient_id=patient["id"],
            content=first_question,
            source=MessageSource.SYSTEM_AUTO
        )
        
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": first_question,
            "source": "system_auto"
        })
    
    # 顯示對話歷史
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "assistant":
                # 顯示訊息來源標籤
                source_label = ""
                if msg.get("source") == "expert_template":
                    source_label = " 🏥"
                
                st.markdown(f"""
                <div class="chat-bubble chat-assistant">
                    {msg['content'].replace(chr(10), '<br>')}{source_label}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-bubble chat-user">
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # 檢查是否完成所有症狀
    current_idx = st.session_state.current_symptom_index
    
    if current_idx < len(SYMPTOMS):
        current_symptom = SYMPTOMS[current_idx]
        
        # 快速回覆按鈕
        st.markdown("**請選擇分數：**")
        
        cols = st.columns(6)
        scores_row1 = [0, 1, 2, 3, 4, 5]
        scores_row2 = [6, 7, 8, 9, 10]
        
        for i, score in enumerate(scores_row1):
            with cols[i]:
                if st.button(f"{score}", key=f"score_{score}", use_container_width=True):
                    handle_score_selection(score, input_method="button")
        
        cols2 = st.columns(6)
        for i, score in enumerate(scores_row2):
            with cols2[i]:
                if st.button(f"{score}", key=f"score_{score}_2", use_container_width=True):
                    handle_score_selection(score, input_method="button")
        
        # 文字輸入（同時收集分數和描述）
        st.markdown("---")
        st.markdown("**或用文字回答：**")
        user_input = st.chat_input("輸入分數（0-10）或描述您的感受...")
        
        if user_input:
            handle_text_input(user_input, current_symptom)
    
    elif current_idx == len(SYMPTOMS):
        # 症狀回報完成，詢問開放式問題
        render_open_ended_questions()
    
    else:
        # 所有問題已完成
        if st.button("✅ 確認提交回報", type="primary", use_container_width=True):
            submit_report()


def handle_text_input(user_input: str, current_symptom: dict):
    """
    處理病人文字輸入
    
    這是收集自然語言資料的關鍵點
    """
    patient_id = st.session_state.patient["id"]
    
    # 記錄原始輸入（最重要！）
    log_patient_input(
        patient_id=patient_id,
        content=user_input,
        input_method="text",
        raw_input=user_input
    )
    
    # 嘗試解析分數
    score = parse_score_from_text(user_input)
    
    if score is not None:
        # 輸入包含分數
        # 檢查是否還有額外描述
        description = extract_description(user_input, score)
        
        if description:
            # 儲存症狀描述
            st.session_state.current_descriptions[current_symptom["id"]] = description
        
        handle_score_selection(score, input_method="text", raw_input=user_input)
    else:
        # 輸入是純文字描述，詢問分數
        st.session_state.current_descriptions[current_symptom["id"]] = user_input
        
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # 感謝描述並詢問分數
        response = f"""
謝謝您的描述！這對我們了解您的狀況很有幫助。

請問以 0-10 分來說，您今天的{current_symptom['name']}大約是幾分呢？
"""
        
        log_ai_response(
            patient_id=patient_id,
            content=response,
            source=MessageSource.SYSTEM_AUTO
        )
        
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response,
            "source": "system_auto"
        })
        
        st.rerun()


def parse_score_from_text(text: str) -> int:
    """從文字中解析分數"""
    import re
    
    # 嘗試找數字
    numbers = re.findall(r'\d+', text)
    
    if numbers:
        for num_str in numbers:
            num = int(num_str)
            if 0 <= num <= 10:
                return num
    
    # 嘗試解析文字描述
    text_lower = text.lower()
    
    if any(kw in text for kw in ["沒有", "完全沒有", "零", "不會"]):
        return 0
    elif any(kw in text for kw in ["非常嚴重", "極度", "劇烈"]):
        return 9
    elif any(kw in text for kw in ["很嚴重", "嚴重"]):
        return 8
    elif any(kw in text for kw in ["明顯", "很痛", "很喘", "很累"]):
        return 7
    elif any(kw in text for kw in ["中等", "普通", "還好"]):
        return 5
    elif any(kw in text for kw in ["輕微", "一點點", "有點"]):
        return 2
    
    return None


def extract_description(text: str, score: int) -> str:
    """從輸入中提取描述部分（排除分數）"""
    import re
    
    # 移除數字和「分」字
    description = re.sub(r'\d+\s*分?', '', text).strip()
    
    # 移除常見的非描述性詞
    remove_words = ["是", "的", "了", "吧", "呢", "啊"]
    for word in remove_words:
        if description == word:
            return ""
    
    return description if len(description) > 2 else ""


def handle_score_selection(score: int, input_method: str = "button", raw_input: str = None):
    """處理分數選擇（更新版）"""
    current_idx = st.session_state.current_symptom_index
    symptom = SYMPTOMS[current_idx]
    patient_id = st.session_state.patient["id"]
    
    # 記錄用戶回覆
    user_content = f"{score} 分"
    if raw_input:
        user_content = raw_input
    
    # 記錄病人輸入
    if input_method == "button":
        log_patient_input(
            patient_id=patient_id,
            content=user_content,
            input_method="button"
        )
    
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_content
    })
    
    # 儲存分數
    st.session_state.current_scores[symptom["id"]] = score
    
    # 生成回應 - 優先使用專家範本
    context = {"score": score}
    response, template_id, source = get_symptom_response(
        symptom_type=symptom["id"],
        score=score,
        context=context
    )
    
    if not response:
        # 使用預設回應
        option = SCORE_OPTIONS[score]
        
        if score <= 3:
            feedback = "很好，這個症狀控制得不錯！👍"
        elif score <= 6:
            feedback = "了解，這是中等程度的症狀，我們會持續關注。"
        else:
            feedback = "⚠️ 這個症狀比較明顯，個管師會特別關注您的狀況。"
        
        response = f"收到！{symptom['name']}：**{score} 分**（{option['label']}）\n\n{feedback}"
        source = MessageSource.AI_GENERATED
    
    # 檢查是否有描述
    if symptom["id"] in st.session_state.current_descriptions:
        description = st.session_state.current_descriptions[symptom["id"]]
        response += f"\n\n（已記錄您的描述：「{description[:50]}...」）" if len(description) > 50 else f"\n\n（已記錄您的描述：「{description}」）"
    
    # 下一個症狀
    next_idx = current_idx + 1
    st.session_state.current_symptom_index = next_idx
    
    if next_idx < len(SYMPTOMS):
        next_symptom = SYMPTOMS[next_idx]
        response += f"""

---

**{next_symptom['icon']} {next_symptom['name']}評估**

{next_symptom['question']}

💡 您也可以用文字描述症狀的感覺！
"""
    else:
        # 完成所有症狀
        response += f"""

---

🎉 **太棒了！您已完成所有症狀評分！**

以下是今日的回報摘要：
"""
        for s in SYMPTOMS:
            s_score = st.session_state.current_scores.get(s["id"], 0)
            desc = st.session_state.current_descriptions.get(s["id"], "")
            desc_text = f" ({desc[:20]}...)" if len(desc) > 20 else (f" ({desc})" if desc else "")
            response += f"\n- {s['icon']} {s['name']}：{s_score} 分{desc_text}"
        
        response += "\n\n接下來，我們想多了解一下您今天的整體狀況..."
    
    # 記錄 AI 回應
    log_ai_response(
        patient_id=patient_id,
        content=response,
        source=source,
        template_id=template_id
    )
    
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": response,
        "source": source.value if source else "ai_generated",
        "template_id": template_id
    })
    
    st.rerun()


def render_open_ended_questions():
    """渲染開放式問題"""
    patient_id = st.session_state.patient["id"]
    
    st.markdown("""
    <div class="open-question-card">
        <div class="open-question-title">✍️ 開放式問題（選填）</div>
        <div class="open-question-hint">
            您的回答對我們非常有價值！這些描述能幫助醫療團隊更好地了解您的恢復狀況。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 顯示開放式問題
    for i, question in enumerate(OPEN_ENDED_QUESTIONS[:2]):  # 先顯示前兩個問題
        st.markdown(f"**{question['question_text']}**")
        st.markdown(f"<small style='color: #64748b;'>{question['hint']}</small>", unsafe_allow_html=True)
        
        response = st.text_area(
            label=f"question_{i}",
            key=f"open_q_{question['question_id']}",
            label_visibility="collapsed",
            placeholder=question['hint'],
            height=80
        )
        
        if response:
            # 儲存開放式回應
            if question['question_id'] not in [r.get('question_id') for r in st.session_state.open_ended_responses]:
                st.session_state.open_ended_responses.append({
                    'question_id': question['question_id'],
                    'question_text': question['question_text'],
                    'category': question['category'],
                    'response': response
                })
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏭️ 跳過，直接提交", use_container_width=True):
            st.session_state.current_symptom_index = len(SYMPTOMS) + 1
            st.rerun()
    
    with col2:
        if st.button("✅ 完成並提交", type="primary", use_container_width=True):
            # 儲存開放式回應
            save_open_ended_responses()
            st.session_state.current_symptom_index = len(SYMPTOMS) + 1
            st.rerun()


def save_open_ended_responses():
    """儲存開放式回應"""
    patient_id = st.session_state.patient["id"]
    report_id = generate_report_id()
    
    for response_data in st.session_state.open_ended_responses:
        if response_data.get('response'):
            log_open_ended_response(
                patient_id=patient_id,
                report_id=report_id,
                question_id=response_data['question_id'],
                question_text=response_data['question_text'],
                question_category=response_data['category'],
                response_text=response_data['response']
            )


def submit_report():
    """提交回報（更新版）"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    patient_id = st.session_state.patient["id"]
    
    # 儲存開放式回應
    save_open_ended_responses()
    
    # 結束對話會話
    if st.session_state.conversation_session_id:
        conversation_store.end_session(
            st.session_state.conversation_session_id,
            completion_type="completed"
        )
    
    # 更新回報歷史
    st.session_state.report_history[today_str] = {
        "completed": True,
        "time": datetime.now().strftime("%H:%M"),
        "scores": st.session_state.current_scores.copy(),
        "descriptions": st.session_state.current_descriptions.copy(),
        "open_ended_count": len(st.session_state.open_ended_responses),
        "method": "ai_chat",
        "session_id": st.session_state.conversation_session_id
    }
    
    # 更新順從度
    st.session_state.today_reported = True
    st.session_state.compliance["current_streak"] += 1
    st.session_state.compliance["total_completed"] += 1
    
    # 檢查成就
    streak = st.session_state.compliance["current_streak"]
    
    # 連續天數成就
    if streak >= 14:
        for a in st.session_state.achievements:
            if a["id"] == "streak_14" and not a["unlocked"]:
                a["unlocked"] = True
                a["date"] = today_str
                st.balloons()
    
    # 詳細描述者成就
    if len(st.session_state.current_descriptions) > 0 or len(st.session_state.open_ended_responses) > 0:
        for a in st.session_state.achievements:
            if a["id"] == "first_description" and not a["unlocked"]:
                a["unlocked"] = True
                a["date"] = today_str
                st.toast("🎉 獲得新成就：詳細描述者！")
    
    # 計算積分
    points = 10  # 基本積分
    points += len(st.session_state.current_descriptions) * 2  # 描述加分
    points += len(st.session_state.open_ended_responses) * 5  # 開放式問題加分
    
    st.session_state.compliance["points"] += points
    
    # 顯示完成訊息
    st.success(f"✅ 回報已提交！獲得 {points} 積分")
    
    # 統計顯示
    stats = conversation_store.get_patient_stats(patient_id)
    st.info(f"📊 您今日提供了 {stats.get('total_messages', 0)} 則訊息，總共 {stats.get('total_words', 0)} 個字")
    
    if st.button("返回首頁"):
        st.session_state.current_page = "home"
        st.rerun()


# ============================================
# 資料匯出頁面（開發用）
# ============================================
def render_data_export():
    """資料匯出頁面（開發/研究用）"""
    st.markdown("### 📤 資料匯出（研究用）")
    
    st.warning("⚠️ 此功能僅供研究人員使用")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 對話資料")
        if st.button("匯出標註資料", use_container_width=True):
            data = conversation_store.export_for_annotation()
            st.json(data[:5])  # 只顯示前5筆
            st.download_button(
                "下載完整資料",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f"annotation_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("#### 開放式回應")
        if st.button("匯出開放式回應", use_container_width=True):
            data = conversation_store.export_open_ended_for_annotation()
            st.json(data[:5])
            st.download_button(
                "下載完整資料",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f"open_ended_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    st.markdown("---")
    
    st.markdown("#### 範本使用統計")
    stats = template_manager.get_usage_stats()
    st.json(stats)


# ============================================
# 側邊欄
# ============================================
def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.markdown("## 🫁 AI-CARE Lung")
        st.markdown("肺癌術後智慧照護系統")
        st.markdown("---")
        
        # 導航
        st.markdown("### 📱 功能選單")
        
        if st.button("🏠 首頁", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        
        if st.button("📊 歷史紀錄", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()
        
        if st.button("🎖️ 成就中心", use_container_width=True):
            st.session_state.current_page = "achievements"
            st.rerun()
        
        if st.button("📚 衛教資訊", use_container_width=True):
            st.session_state.current_page = "education"
            st.rerun()
        
        st.markdown("---")
        
        # 開發選項
        with st.expander("🔧 開發選項"):
            if st.button("📤 資料匯出", use_container_width=True):
                st.session_state.current_page = "data_export"
                st.rerun()
            
            if st.button("🔄 重置今日回報", use_container_width=True):
                st.session_state.today_reported = False
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.8rem; color: #64748b; text-align: center;">
            三軍總醫院<br>
            數位醫療中心<br>
            v2.0
        </div>
        """, unsafe_allow_html=True)


# ============================================
# 主程式
# ============================================
def main():
    """主程式"""
    render_sidebar()
    
    page = st.session_state.current_page
    
    if page == "home":
        render_home()
    elif page == "ai_chat":
        render_ai_chat()
    elif page == "data_export":
        render_data_export()
    else:
        render_home()


if __name__ == "__main__":
    main()
