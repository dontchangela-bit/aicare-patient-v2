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
# 數位問卷回報頁面
# ============================================
def render_questionnaire():
    """渲染數位問卷回報頁面"""
    st.markdown("### 📋 數位問卷回報")
    st.markdown("透過問卷快速完成今日症狀評估")
    
    # 返回按鈕
    if st.button("← 返回首頁"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    patient = st.session_state.patient
    
    st.markdown(f"""
    <div style="background: #f0f9ff; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
        <strong>👤 {patient['name']}</strong> | 術後第 {patient['post_op_day']} 天
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化問卷分數
    if "questionnaire_scores" not in st.session_state:
        st.session_state.questionnaire_scores = {}
    
    # 顯示所有症狀問題
    st.markdown("#### 請評估您今天的症狀（0-10分）")
    
    for symptom in SYMPTOMS:
        st.markdown(f"**{symptom['icon']} {symptom['name']}**")
        st.markdown(f"<small style='color: #64748b;'>{symptom['question']}</small>", unsafe_allow_html=True)
        
        score = st.slider(
            label=symptom['name'],
            min_value=0,
            max_value=10,
            value=st.session_state.questionnaire_scores.get(symptom['id'], 0),
            key=f"q_{symptom['id']}",
            label_visibility="collapsed"
        )
        st.session_state.questionnaire_scores[symptom['id']] = score
        
        # 顯示分數說明
        option = SCORE_OPTIONS[score]
        st.markdown(f"<span style='color: {option['color']}; font-weight: 500;'>{score} 分 - {option['label']}</span>", unsafe_allow_html=True)
        st.markdown("")
    
    st.markdown("---")
    
    # 額外描述
    st.markdown("#### ✍️ 其他想補充的（選填）")
    additional_notes = st.text_area(
        "其他描述",
        placeholder="如果有任何症狀想特別描述，或其他想告訴醫療團隊的事情...",
        label_visibility="collapsed",
        height=100
    )
    
    st.markdown("---")
    
    # 提交按鈕
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↩️ 清除重填", use_container_width=True):
            st.session_state.questionnaire_scores = {}
            st.rerun()
    
    with col2:
        if st.button("✅ 提交回報", type="primary", use_container_width=True):
            # 儲存回報
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            st.session_state.report_history[today_str] = {
                "completed": True,
                "time": datetime.now().strftime("%H:%M"),
                "scores": st.session_state.questionnaire_scores.copy(),
                "descriptions": {"additional": additional_notes} if additional_notes else {},
                "method": "questionnaire"
            }
            
            # 更新順從度
            st.session_state.today_reported = True
            st.session_state.compliance["current_streak"] += 1
            st.session_state.compliance["total_completed"] += 1
            st.session_state.compliance["points"] += 10
            
            st.success("✅ 問卷回報已提交！獲得 10 積分")
            st.balloons()
            
            # 清除問卷
            st.session_state.questionnaire_scores = {}
            
            if st.button("返回首頁", key="back_after_submit"):
                st.session_state.current_page = "home"
                st.rerun()


# ============================================
# 歷史紀錄頁面
# ============================================
def render_history():
    """渲染歷史紀錄頁面"""
    st.markdown("### 📊 歷史紀錄")
    st.markdown("查看您過去的症狀回報記錄")
    
    # 返回按鈕
    if st.button("← 返回首頁"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    history = st.session_state.report_history
    
    if not history:
        st.info("📭 目前還沒有回報記錄，完成今日回報後就會顯示在這裡！")
        
        # 顯示模擬數據
        st.markdown("#### 📅 模擬歷史數據預覽")
        
        # 生成模擬數據
        import random
        demo_data = []
        for i in range(7):
            day = datetime.now() - timedelta(days=i+1)
            demo_data.append({
                "date": day.strftime("%Y-%m-%d"),
                "weekday": ["一", "二", "三", "四", "五", "六", "日"][day.weekday()],
                "scores": {s["id"]: random.randint(0, 5) for s in SYMPTOMS}
            })
        
        # 顯示表格
        for record in demo_data:
            with st.expander(f"📅 {record['date']} (週{record['weekday']})"):
                cols = st.columns(len(SYMPTOMS))
                for i, symptom in enumerate(SYMPTOMS):
                    with cols[i]:
                        score = record['scores'][symptom['id']]
                        color = SCORE_OPTIONS[score]['color']
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem;">{symptom['icon']}</div>
                            <div style="color: {color}; font-weight: bold;">{score}分</div>
                            <div style="font-size: 0.75rem; color: #64748b;">{symptom['name']}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("<small style='color: #94a3b8;'>* 以上為模擬數據，僅供展示</small>", unsafe_allow_html=True)
        return
    
    # 顯示實際歷史記錄
    st.markdown("#### 📅 您的回報記錄")
    
    # 排序：最新的在前面
    sorted_dates = sorted(history.keys(), reverse=True)
    
    for date_str in sorted_dates:
        record = history[date_str]
        
        # 計算是哪一天
        record_date = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = ["一", "二", "三", "四", "五", "六", "日"][record_date.weekday()]
        
        # 計算平均分數
        scores = record.get('scores', {})
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        # 根據平均分數設定顏色
        if avg_score <= 3:
            status_color = "#10b981"
            status_text = "良好"
        elif avg_score <= 6:
            status_color = "#f59e0b"
            status_text = "普通"
        else:
            status_color = "#ef4444"
            status_text = "需關注"
        
        with st.expander(f"📅 {date_str} (週{weekday}) - {record.get('time', '')} | 狀態：{status_text}"):
            # 回報方式
            method = record.get('method', 'unknown')
            method_label = "💬 AI對話" if method == "ai_chat" else "📋 問卷" if method == "questionnaire" else "❓"
            st.markdown(f"**回報方式：** {method_label}")
            
            st.markdown("**各症狀評分：**")
            cols = st.columns(len(SYMPTOMS))
            for i, symptom in enumerate(SYMPTOMS):
                with cols[i]:
                    score = scores.get(symptom['id'], 0)
                    color = SCORE_OPTIONS[score]['color']
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem; background: #f8fafc; border-radius: 8px;">
                        <div style="font-size: 1.5rem;">{symptom['icon']}</div>
                        <div style="color: {color}; font-weight: bold; font-size: 1.25rem;">{score}</div>
                        <div style="font-size: 0.7rem; color: #64748b;">{symptom['name']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 顯示描述
            descriptions = record.get('descriptions', {})
            if descriptions:
                st.markdown("**補充描述：**")
                for key, desc in descriptions.items():
                    if desc:
                        st.markdown(f"- {desc}")
    
    # 統計摘要
    st.markdown("---")
    st.markdown("#### 📈 統計摘要")
    
    total_reports = len(history)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總回報次數", f"{total_reports} 次")
    with col2:
        compliance_rate = (st.session_state.compliance['total_completed'] / 
                          st.session_state.compliance['total_days'] * 100) if st.session_state.compliance['total_days'] > 0 else 0
        st.metric("完成率", f"{compliance_rate:.0f}%")
    with col3:
        st.metric("連續天數", f"{st.session_state.compliance['current_streak']} 天")


# ============================================
# 成就中心頁面
# ============================================
def render_achievements():
    """渲染成就中心頁面"""
    st.markdown("### 🎖️ 成就中心")
    st.markdown("查看您獲得的成就和進度")
    
    # 返回按鈕
    if st.button("← 返回首頁"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    # 等級資訊
    compliance = st.session_state.compliance
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%); 
                padding: 1.5rem; border-radius: 16px; color: white; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.9rem; opacity: 0.9;">目前等級</div>
                <div style="font-size: 2rem; font-weight: 700;">Lv.{compliance['level']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.9rem; opacity: 0.9;">累積積分</div>
                <div style="font-size: 2rem; font-weight: 700;">⭐ {compliance['points']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 等級進度條
    level_thresholds = [0, 50, 150, 300, 500, 800, 1200]
    current_level = compliance['level']
    current_points = compliance['points']
    
    if current_level < len(level_thresholds):
        prev_threshold = level_thresholds[current_level - 1] if current_level > 0 else 0
        next_threshold = level_thresholds[current_level] if current_level < len(level_thresholds) else level_thresholds[-1]
        progress = (current_points - prev_threshold) / (next_threshold - prev_threshold) if next_threshold > prev_threshold else 1
        
        st.markdown(f"**升級進度：** {current_points} / {next_threshold} 積分")
        st.progress(min(progress, 1.0))
        st.markdown(f"<small style='color: #64748b;'>還需 {max(0, next_threshold - current_points)} 積分升到 Lv.{current_level + 1}</small>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 成就列表
    st.markdown("#### 🏆 成就列表")
    
    achievements = st.session_state.achievements
    
    # 已解鎖的成就
    unlocked = [a for a in achievements if a["unlocked"]]
    locked = [a for a in achievements if not a["unlocked"]]
    
    if unlocked:
        st.markdown("**✨ 已獲得**")
        cols = st.columns(3)
        for i, achievement in enumerate(unlocked):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                            padding: 1rem; border-radius: 12px; text-align: center; margin-bottom: 1rem;
                            border: 2px solid #f59e0b;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{achievement['icon']}</div>
                    <div style="font-weight: 600; color: #92400e;">{achievement['name']}</div>
                    <div style="font-size: 0.75rem; color: #b45309;">獲得於 {achievement['date']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    if locked:
        st.markdown("**🔒 未解鎖**")
        cols = st.columns(3)
        for i, achievement in enumerate(locked):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background: #f1f5f9; padding: 1rem; border-radius: 12px; 
                            text-align: center; margin-bottom: 1rem; opacity: 0.7;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem; filter: grayscale(100%);">{achievement['icon']}</div>
                    <div style="font-weight: 600; color: #64748b;">{achievement['name']}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">繼續努力！</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 積分說明
    st.markdown("---")
    st.markdown("#### 📝 積分規則")
    st.markdown("""
    | 行為 | 積分 |
    |------|------|
    | 完成每日回報 | +10 |
    | 填寫症狀描述 | +2 (每個) |
    | 回答開放式問題 | +5 (每題) |
    | 連續7天回報 | +30 |
    | 連續14天回報 | +50 |
    | 連續21天回報 | +80 |
    """)


# ============================================
# 衛教資訊頁面
# ============================================
def render_education():
    """渲染衛教資訊頁面"""
    st.markdown("### 📚 衛教資訊")
    st.markdown("肺癌術後照護相關知識")
    
    # 返回按鈕
    if st.button("← 返回首頁"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    # 衛教文章分類
    categories = [
        {
            "id": "recovery",
            "name": "🏥 術後恢復",
            "articles": [
                {
                    "title": "肺葉切除術後注意事項",
                    "summary": "了解術後傷口護理、活動限制和復原時程",
                    "content": """
### 肺葉切除術後注意事項

#### 傷口照護
- 保持傷口乾燥清潔
- 手術後約7-10天可拆線
- 若傷口有紅腫、滲液或發燒，請立即就醫

#### 活動建議
- 術後第一週：輕度活動，避免提重物
- 術後第二週：可逐漸增加活動量
- 術後一個月：可恢復大部分日常活動
- 完全恢復：約需2-3個月

#### 注意事項
- 避免用力咳嗽或打噴嚏時壓迫傷口
- 保持規律的深呼吸練習
- 遵照醫囑服用藥物
"""
                },
                {
                    "title": "呼吸復健運動",
                    "summary": "簡單有效的呼吸訓練方法",
                    "content": """
### 呼吸復健運動

#### 腹式呼吸
1. 平躺或坐著，放鬆肩膀
2. 一手放在胸部，一手放在腹部
3. 用鼻子緩慢吸氣，讓腹部隆起
4. 用嘴巴緩慢吐氣，腹部自然下降
5. 每次練習10-15次，每天3-4次

#### 縮唇呼吸
1. 用鼻子吸氣
2. 像吹蠟燭一樣，嘴唇縮成小圓形
3. 緩慢吐氣，吐氣時間是吸氣的2倍
4. 適合在活動時使用

#### 肺活量訓練
- 使用誘發性肺量計（Incentive Spirometer）
- 每小時練習10次
- 目標：達到術前的80%以上
"""
                }
            ]
        },
        {
            "id": "symptoms",
            "name": "🩺 症狀管理",
            "articles": [
                {
                    "title": "術後疼痛管理",
                    "summary": "如何有效控制術後疼痛",
                    "content": """
### 術後疼痛管理

#### 常見疼痛類型
- **傷口痛**：手術切口處的疼痛，通常2-3週會明顯改善
- **胸壁痛**：肋間神經受影響，可能持續較長時間
- **肩膀痛**：橫隔膜刺激造成的轉移痛

#### 止痛方法
1. **藥物治療**
   - 按時服用止痛藥，不要等到很痛才吃
   - 常用藥物：Acetaminophen、NSAIDs、弱效鴉片類

2. **非藥物方法**
   - 冰敷：術後48小時內可減輕腫脹
   - 熱敷：48小時後可促進血液循環
   - 放鬆技巧：深呼吸、冥想

#### 何時需要就醫
- 疼痛評分持續 > 7分
- 止痛藥無法控制
- 伴隨發燒、傷口異常
"""
                },
                {
                    "title": "呼吸困難處理",
                    "summary": "活動時喘氣的應對方法",
                    "content": """
### 呼吸困難處理

#### 為什麼會喘？
肺部手術後，肺容量會暫時減少，身體需要時間適應。

#### 日常應對
1. **活動前**
   - 先做幾次深呼吸
   - 準備好隨時可以休息

2. **活動中**
   - 採用縮唇呼吸
   - 調整活動節奏，「走走停停」
   - 避免憋氣

3. **活動後**
   - 坐下休息，前傾姿勢有助呼吸
   - 等呼吸平穩後再繼續

#### 警示症狀
若出現以下情況，請立即就醫：
- 休息時也很喘
- 嘴唇或指甲發紫
- 胸悶、胸痛
- 意識改變
"""
                }
            ]
        },
        {
            "id": "lifestyle",
            "name": "🌿 生活調適",
            "articles": [
                {
                    "title": "營養與飲食建議",
                    "summary": "促進術後恢復的飲食原則",
                    "content": """
### 營養與飲食建議

#### 高蛋白飲食
- **目標**：每公斤體重 1.2-1.5 克蛋白質
- **來源**：魚、雞肉、蛋、豆腐、牛奶

#### 維生素補充
- **維生素C**：促進傷口癒合（柑橘、奇異果）
- **維生素A**：幫助黏膜修復（紅蘿蔔、南瓜）
- **鋅**：增強免疫力（牡蠣、堅果）

#### 飲食注意
- 少量多餐，避免過飽影響呼吸
- 多喝水，幫助痰液稀釋
- 避免刺激性食物
- 戒菸戒酒

#### 食慾不佳時
- 選擇喜歡的食物
- 調整用餐環境
- 必要時使用營養補充品
"""
                },
                {
                    "title": "情緒調適與心理支持",
                    "summary": "面對術後情緒變化的方法",
                    "content": """
### 情緒調適與心理支持

#### 常見情緒反應
術後出現以下情緒是正常的：
- 焦慮：擔心恢復、復發
- 沮喪：活動受限、角色改變
- 恐懼：對未來的不確定感
- 憤怒：「為什麼是我？」

#### 調適方法
1. **接納情緒**
   - 允許自己有負面情緒
   - 找人傾訴

2. **維持社交**
   - 與家人朋友保持聯繫
   - 加入病友團體

3. **規律作息**
   - 固定睡眠時間
   - 適度活動

4. **放鬆技巧**
   - 深呼吸練習
   - 正念冥想
   - 聽音樂、閱讀

#### 何時尋求專業協助
- 情緒低落超過兩週
- 失眠嚴重
- 有自傷想法
"""
                }
            ]
        }
    ]
    
    # 選擇分類
    selected_category = st.selectbox(
        "選擇分類",
        options=[c["id"] for c in categories],
        format_func=lambda x: next(c["name"] for c in categories if c["id"] == x),
        label_visibility="collapsed"
    )
    
    # 顯示該分類的文章
    category = next(c for c in categories if c["id"] == selected_category)
    
    st.markdown(f"#### {category['name']}")
    
    for article in category["articles"]:
        with st.expander(f"📄 {article['title']}"):
            st.markdown(f"*{article['summary']}*")
            st.markdown("---")
            st.markdown(article["content"])
    
    # 緊急聯絡資訊
    st.markdown("---")
    st.markdown("#### 🆘 緊急聯絡")
    st.markdown("""
    <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 1rem; border-radius: 12px;">
        <strong style="color: #dc2626;">如有以下情況，請立即就醫：</strong>
        <ul style="margin: 0.5rem 0; color: #991b1b;">
            <li>呼吸困難加劇</li>
            <li>發燒超過38.5°C</li>
            <li>咳血或痰中帶血</li>
            <li>傷口紅腫流膿</li>
            <li>劇烈胸痛</li>
        </ul>
        <div style="margin-top: 0.5rem;">
            <strong>三軍總醫院急診：</strong> 02-8792-3311<br>
            <strong>胸腔外科門診：</strong> 02-8792-7000
        </div>
    </div>
    """, unsafe_allow_html=True)


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
    elif page == "questionnaire":
        render_questionnaire()
    elif page == "history":
        render_history()
    elif page == "achievements":
        render_achievements()
    elif page == "education":
        render_education()
    elif page == "data_export":
        render_data_export()
    else:
        render_home()


if __name__ == "__main__":
    main()
