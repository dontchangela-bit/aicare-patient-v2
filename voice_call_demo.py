"""
AI-CARE Lung - AI 語音電話 Demo 模組
=====================================
模擬 Bland AI 語音電話機器人主動撥打給病人的體驗

三軍總醫院 數位醫療中心
"""

import streamlit as st
import time
from datetime import datetime

# ============================================
# AI 語音電話對話流程 (基於 MDASI-LC)
# ============================================
VOICE_CALL_STEPS = [
    {
        "id": "incoming_call",
        "type": "system",
        "content": "📞 來電中...",
        "subtitle": "三軍總醫院 健康小助手",
        "wait_action": "接聽"
    },
    {
        "id": "greeting",
        "type": "ai",
        "content": "{patient_name}您好，我是三軍總醫院的健康小助手小安。今天是您手術後第{post_op_day}天，想關心一下您的狀況。現在方便聊幾分鐘嗎？",
        "expected_responses": ["好，可以", "方便", "沒問題"],
        "quick_replies": ["好，可以", "方便，請說", "沒問題"]
    },
    {
        "id": "overall",
        "type": "ai",
        "symptom": "overall",
        "content": "太好了！首先想請問您，今天整體感覺怎麼樣？如果用 0 到 10 分來說，0 分是完全沒有不舒服，10 分是非常不舒服，您會給幾分呢？",
        "score_question": True,
        "icon": "💪"
    },
    {
        "id": "pain",
        "type": "ai",
        "symptom": "pain",
        "content": "了解。那傷口或其他地方有疼痛嗎？疼痛程度大概幾分？",
        "score_question": True,
        "icon": "🩹",
        "alert_threshold": 7
    },
    {
        "id": "dyspnea",
        "type": "ai",
        "symptom": "dyspnea",
        "content": "呼吸方面呢？有沒有喘或呼吸困難的感覺？",
        "score_question": True,
        "icon": "💨",
        "alert_threshold": 6,
        "follow_up": "是休息時也會喘，還是活動的時候比較明顯？"
    },
    {
        "id": "fatigue",
        "type": "ai",
        "symptom": "fatigue",
        "content": "那精神和體力方面呢？會不會很容易累或疲勞？",
        "score_question": True,
        "icon": "😮‍💨"
    },
    {
        "id": "cough",
        "type": "ai",
        "symptom": "cough",
        "content": "咳嗽的情況如何？有咳嗽嗎？咳得多不多？",
        "score_question": True,
        "icon": "🤧",
        "follow_up": "咳嗽有痰嗎？痰是什麼顏色的？"
    },
    {
        "id": "sleep_appetite",
        "type": "ai",
        "symptom": "sleep_appetite",
        "content": "睡眠和食慾方面呢？晚上睡得好嗎？吃得下東西嗎？",
        "multi_choice": True,
        "options": {
            "sleep": ["睡得好", "還可以", "睡不好"],
            "appetite": ["吃得下", "普通", "沒胃口"]
        },
        "icon": "😴"
    },
    {
        "id": "safety_check",
        "type": "ai",
        "content": "最後想確認一下，有沒有發燒？傷口有沒有紅腫、流膿或異常分泌物？",
        "safety_check": True,
        "icon": "🔍",
        "critical_flags": ["fever", "wound_infection", "blood_in_sputum"]
    },
    {
        "id": "additional",
        "type": "ai",
        "content": "還有沒有其他想告訴醫療團隊的事情，或是有什麼問題想問的？",
        "open_ended": True,
        "icon": "💭"
    },
    {
        "id": "closing",
        "type": "ai",
        "content": "好的，謝謝{patient_name}今天的回報。我幫您整理一下：{summary}。這些資訊我會回報給醫療團隊，{follow_up_action}。祝您今天順心，有任何問題隨時打給我們！",
        "closing": True,
        "icon": "👋"
    }
]

# 預設的模擬回答（用於自動播放 Demo）
DEMO_RESPONSES = {
    "overall": {"score": 4, "text": "大概4分吧，還可以"},
    "pain": {"score": 5, "text": "傷口有點痛，5分左右"},
    "dyspnea": {"score": 3, "text": "走路的時候會有點喘，大概3分"},
    "fatigue": {"score": 4, "text": "容易累，4分"},
    "cough": {"score": 2, "text": "偶爾咳一下，2分，沒有痰"},
    "sleep_appetite": {"sleep": "還可以", "appetite": "吃得下"},
    "safety_check": {"fever": False, "wound_issue": False},
    "additional": "目前沒有其他問題，謝謝關心"
}


def get_voice_call_css():
    """取得語音電話 Demo 的 CSS 樣式"""
    return """
    <style>
    /* 來電動畫 */
    @keyframes pulse-ring {
        0% { transform: scale(0.8); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.5; }
        100% { transform: scale(0.8); opacity: 1; }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px) rotate(-5deg); }
        75% { transform: translateX(5px) rotate(5deg); }
    }
    
    @keyframes voice-wave {
        0%, 100% { height: 8px; }
        50% { height: 24px; }
    }
    
    .incoming-call-card {
        background: linear-gradient(135deg, #00897B 0%, #004D40 100%);
        border-radius: 24px;
        padding: 2.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 20px 60px rgba(0, 137, 123, 0.4);
        max-width: 380px;
        margin: 2rem auto;
    }
    
    .call-icon {
        font-size: 4rem;
        animation: shake 0.5s ease-in-out infinite;
        margin-bottom: 1rem;
    }
    
    .pulse-ring {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.5rem;
        animation: pulse-ring 1.5s ease-out infinite;
    }
    
    .caller-name {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .caller-subtitle {
        font-size: 0.95rem;
        opacity: 0.85;
    }
    
    /* 通話中介面 */
    .call-active-card {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 24px;
        padding: 2rem;
        color: white;
        max-width: 420px;
        margin: 1rem auto;
    }
    
    .call-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    
    .call-timer {
        font-size: 1.1rem;
        color: #4ade80;
        font-family: monospace;
    }
    
    .call-status {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    
    /* 語音波形動畫 */
    .voice-wave-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        height: 40px;
        margin: 1rem 0;
    }
    
    .voice-wave-bar {
        width: 4px;
        background: linear-gradient(180deg, #00897B, #4ade80);
        border-radius: 2px;
        animation: voice-wave 0.5s ease-in-out infinite;
    }
    
    .voice-wave-bar:nth-child(1) { animation-delay: 0s; height: 12px; }
    .voice-wave-bar:nth-child(2) { animation-delay: 0.1s; height: 20px; }
    .voice-wave-bar:nth-child(3) { animation-delay: 0.2s; height: 28px; }
    .voice-wave-bar:nth-child(4) { animation-delay: 0.15s; height: 16px; }
    .voice-wave-bar:nth-child(5) { animation-delay: 0.25s; height: 24px; }
    .voice-wave-bar:nth-child(6) { animation-delay: 0.1s; height: 20px; }
    .voice-wave-bar:nth-child(7) { animation-delay: 0.3s; height: 12px; }
    
    /* 對話氣泡（電話版） */
    .voice-bubble {
        padding: 1rem 1.25rem;
        border-radius: 16px;
        margin: 0.75rem 0;
        max-width: 90%;
        line-height: 1.6;
        position: relative;
    }
    
    .voice-bubble-ai {
        background: linear-gradient(135deg, #E0F2F1 0%, #B2DFDB 100%);
        color: #004D40;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    
    .voice-bubble-ai::before {
        content: "🤖 小安";
        display: block;
        font-size: 0.75rem;
        font-weight: 600;
        color: #00695C;
        margin-bottom: 0.25rem;
    }
    
    .voice-bubble-patient {
        background: linear-gradient(135deg, #00897B 0%, #00695C 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .voice-bubble-patient::before {
        content: "👤 您";
        display: block;
        font-size: 0.75rem;
        font-weight: 600;
        opacity: 0.85;
        margin-bottom: 0.25rem;
    }
    
    /* 快速回覆按鈕 */
    .quick-reply-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 1rem 0;
        justify-content: center;
    }
    
    .quick-reply-btn {
        background: rgba(0, 137, 123, 0.15);
        border: 1px solid #00897B;
        color: #00897B;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .quick-reply-btn:hover {
        background: #00897B;
        color: white;
    }
    
    /* 分數選擇器 */
    .score-selector {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        margin: 1rem 0;
    }
    
    .score-btn {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        border: 2px solid #e2e8f0;
        background: white;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .score-btn:hover {
        transform: scale(1.1);
    }
    
    .score-btn.low { border-color: #10b981; color: #10b981; }
    .score-btn.low:hover { background: #10b981; color: white; }
    
    .score-btn.medium { border-color: #f59e0b; color: #f59e0b; }
    .score-btn.medium:hover { background: #f59e0b; color: white; }
    
    .score-btn.high { border-color: #ef4444; color: #ef4444; }
    .score-btn.high:hover { background: #ef4444; color: white; }
    
    /* 通話結束報告 */
    .call-report-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    .report-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .alert-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .alert-green { background: #dcfce7; color: #166534; }
    .alert-yellow { background: #fef3c7; color: #92400e; }
    .alert-red { background: #fee2e2; color: #991b1b; }
    
    .symptom-summary-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin: 1rem 0;
    }
    
    .symptom-summary-item {
        background: #f8fafc;
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
    }
    
    .symptom-score {
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .symptom-name {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    /* 掛斷按鈕 */
    .end-call-btn {
        background: #ef4444;
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 30px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin: 1rem auto;
        transition: all 0.2s;
    }
    
    .end-call-btn:hover {
        background: #dc2626;
        transform: scale(1.05);
    }
    </style>
    """


def init_voice_call_state():
    """初始化語音電話 Demo 的 Session State"""
    if "voice_call_step" not in st.session_state:
        st.session_state.voice_call_step = 0
    if "voice_call_messages" not in st.session_state:
        st.session_state.voice_call_messages = []
    if "voice_call_scores" not in st.session_state:
        st.session_state.voice_call_scores = {}
    if "voice_call_started" not in st.session_state:
        st.session_state.voice_call_started = False
    if "voice_call_ended" not in st.session_state:
        st.session_state.voice_call_ended = False
    if "voice_call_start_time" not in st.session_state:
        st.session_state.voice_call_start_time = None
    if "safety_flags" not in st.session_state:
        st.session_state.safety_flags = {"fever": False, "wound_issue": False}


def calculate_alert_level(scores, safety_flags):
    """計算警示等級"""
    # 紅燈條件
    if safety_flags.get("fever") or safety_flags.get("wound_issue"):
        return "red", "🔴 紅燈警示"
    if scores.get("pain", 0) >= 7:
        return "red", "🔴 紅燈警示"
    if scores.get("dyspnea", 0) >= 6:
        return "red", "🔴 紅燈警示"
    if scores.get("overall", 0) >= 8:
        return "red", "🔴 紅燈警示"
    
    # 黃燈條件
    if scores.get("pain", 0) >= 4:
        return "yellow", "🟡 黃燈提醒"
    if scores.get("dyspnea", 0) >= 4:
        return "yellow", "🟡 黃燈提醒"
    if scores.get("overall", 0) >= 5:
        return "yellow", "🟡 黃燈提醒"
    
    # 綠燈
    return "green", "🟢 狀況良好"


def get_follow_up_action(alert_level):
    """取得後續行動說明"""
    actions = {
        "green": "您恢復得很好，繼續保持！明天同一時間我們再聊",
        "yellow": "我們會持續關注您的狀況，如有需要個管師會主動聯繫您",
        "red": "個管師會在 30 分鐘內主動聯繫您，請保持電話暢通"
    }
    return actions.get(alert_level, "")


def render_incoming_call(patient):
    """渲染來電畫面"""
    st.markdown(f"""
    <div class="incoming-call-card">
        <div class="pulse-ring">
            <div class="call-icon">📞</div>
        </div>
        <div class="caller-name">三軍總醫院</div>
        <div class="caller-subtitle">🏥 健康小助手 小安</div>
        <div style="margin-top: 1.5rem; font-size: 0.9rem; opacity: 0.8;">
            術後第 {patient['post_op_day']} 天 每日關懷電話
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📞 接聽", type="primary", use_container_width=True, key="answer_call"):
            st.session_state.voice_call_started = True
            st.session_state.voice_call_start_time = datetime.now()
            st.session_state.voice_call_step = 1  # 跳到問候語
            st.rerun()
        
        if st.button("❌ 拒接", use_container_width=True, key="decline_call"):
            st.session_state.current_page = "home"
            st.rerun()


def render_voice_wave():
    """渲染語音波形動畫"""
    st.markdown("""
    <div class="voice-wave-container">
        <div class="voice-wave-bar"></div>
        <div class="voice-wave-bar"></div>
        <div class="voice-wave-bar"></div>
        <div class="voice-wave-bar"></div>
        <div class="voice-wave-bar"></div>
        <div class="voice-wave-bar"></div>
        <div class="voice-wave-bar"></div>
    </div>
    """, unsafe_allow_html=True)


def render_call_timer():
    """渲染通話計時器"""
    if st.session_state.voice_call_start_time:
        elapsed = datetime.now() - st.session_state.voice_call_start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        return f"{minutes:02d}:{seconds:02d}"
    return "00:00"


def render_active_call(patient):
    """渲染通話中畫面"""
    current_step = st.session_state.voice_call_step
    
    # 通話頭部
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #00897B, #004D40); 
                    border-radius: 16px; color: white; margin-bottom: 1rem;">
            <div style="font-size: 0.85rem; opacity: 0.8;">🔊 通話中</div>
            <div style="font-size: 1.25rem; font-weight: 600; margin: 0.5rem 0;">🤖 健康小助手 小安</div>
            <div style="font-size: 0.9rem; color: #4ade80;">⏱️ {render_call_timer()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 語音波形
    render_voice_wave()
    
    # 對話記錄
    st.markdown("---")
    
    # 顯示歷史對話
    for msg in st.session_state.voice_call_messages:
        if msg["role"] == "ai":
            st.markdown(f"""
            <div class="voice-bubble voice-bubble-ai">
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="voice-bubble voice-bubble-patient">
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # 處理當前步驟
    if current_step < len(VOICE_CALL_STEPS):
        step = VOICE_CALL_STEPS[current_step]
        
        # 替換變數
        content = step["content"].format(
            patient_name=patient["name"],
            post_op_day=patient["post_op_day"],
            summary=generate_summary(),
            follow_up_action=get_follow_up_action(calculate_alert_level(
                st.session_state.voice_call_scores, 
                st.session_state.safety_flags
            )[0])
        )
        
        # 顯示當前 AI 訊息（如果還沒加入歷史）
        if not any(m.get("step_id") == step["id"] and m["role"] == "ai" for m in st.session_state.voice_call_messages):
            st.session_state.voice_call_messages.append({
                "role": "ai",
                "content": content,
                "step_id": step["id"]
            })
            st.rerun()
        
        # 根據步驟類型顯示互動元素
        if step.get("score_question"):
            render_score_input(step)
        elif step.get("multi_choice"):
            render_multi_choice(step)
        elif step.get("safety_check"):
            render_safety_check(step)
        elif step.get("open_ended"):
            render_open_ended(step)
        elif step.get("closing"):
            render_closing(step, patient)
        elif step.get("quick_replies"):
            render_quick_replies(step)
    
    # 掛斷按鈕
    st.markdown("---")
    if st.button("📵 結束通話", use_container_width=True, key="end_call"):
        st.session_state.voice_call_ended = True
        st.rerun()


def render_score_input(step):
    """渲染分數輸入"""
    st.markdown(f"**{step.get('icon', '📊')} 請選擇 0-10 分：**")
    
    cols = st.columns(11)
    for i, col in enumerate(cols):
        with col:
            # 根據分數設定顏色類別
            if i <= 3:
                color_class = "low"
            elif i <= 6:
                color_class = "medium"
            else:
                color_class = "high"
            
            if st.button(str(i), key=f"score_{step['id']}_{i}", use_container_width=True):
                symptom_id = step.get("symptom", step["id"])
                st.session_state.voice_call_scores[symptom_id] = i
                
                # 加入病人回應
                response_text = f"{i} 分"
                if i <= 2:
                    response_text += "，還好"
                elif i <= 5:
                    response_text += "，有一點"
                else:
                    response_text += "，比較嚴重"
                
                st.session_state.voice_call_messages.append({
                    "role": "patient",
                    "content": response_text,
                    "step_id": step["id"]
                })
                
                # 進入下一步
                st.session_state.voice_call_step += 1
                st.rerun()
    
    # 分數說明
    st.caption("0 = 完全沒有 ｜ 1-3 = 輕微 ｜ 4-6 = 中等 ｜ 7-10 = 嚴重")


def render_multi_choice(step):
    """渲染多選題（睡眠/食慾）"""
    st.markdown("**請選擇：**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("😴 **睡眠狀況**")
        sleep_options = ["睡得好", "還可以", "睡不好"]
        for opt in sleep_options:
            if st.button(opt, key=f"sleep_{opt}", use_container_width=True):
                st.session_state.voice_call_scores["sleep"] = opt
                check_and_advance_multi_choice(step)
    
    with col2:
        st.markdown("🍽️ **食慾狀況**")
        appetite_options = ["吃得下", "普通", "沒胃口"]
        for opt in appetite_options:
            if st.button(opt, key=f"appetite_{opt}", use_container_width=True):
                st.session_state.voice_call_scores["appetite"] = opt
                check_and_advance_multi_choice(step)


def check_and_advance_multi_choice(step):
    """檢查多選題是否完成並前進"""
    if "sleep" in st.session_state.voice_call_scores and "appetite" in st.session_state.voice_call_scores:
        response = f"睡眠{st.session_state.voice_call_scores['sleep']}，食慾{st.session_state.voice_call_scores['appetite']}"
        st.session_state.voice_call_messages.append({
            "role": "patient",
            "content": response,
            "step_id": step["id"]
        })
        st.session_state.voice_call_step += 1
    st.rerun()


def render_safety_check(step):
    """渲染安全檢查問題"""
    st.markdown("**🔍 安全確認：**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fever = st.radio(
            "🌡️ 有沒有發燒？",
            ["沒有發燒", "有發燒"],
            key="fever_check",
            horizontal=True
        )
    
    with col2:
        wound = st.radio(
            "🩹 傷口有異常嗎？",
            ["傷口正常", "有紅腫/流膿"],
            key="wound_check",
            horizontal=True
        )
    
    if st.button("確認", type="primary", key="confirm_safety", use_container_width=True):
        st.session_state.safety_flags["fever"] = (fever == "有發燒")
        st.session_state.safety_flags["wound_issue"] = (wound == "有紅腫/流膿")
        
        response_parts = []
        if fever == "沒有發燒":
            response_parts.append("沒有發燒")
        else:
            response_parts.append("有點發燒")
        
        if wound == "傷口正常":
            response_parts.append("傷口看起來正常")
        else:
            response_parts.append("傷口有點紅腫")
        
        st.session_state.voice_call_messages.append({
            "role": "patient",
            "content": "，".join(response_parts),
            "step_id": step["id"]
        })
        st.session_state.voice_call_step += 1
        st.rerun()


def render_open_ended(step):
    """渲染開放式問題"""
    response = st.text_input(
        "💬 請說...",
        placeholder="沒有的話可以直接點「繼續」",
        key="open_ended_input"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("沒有其他問題", use_container_width=True, key="no_question"):
            st.session_state.voice_call_messages.append({
                "role": "patient",
                "content": "目前沒有其他問題，謝謝",
                "step_id": step["id"]
            })
            st.session_state.voice_call_step += 1
            st.rerun()
    
    with col2:
        if st.button("送出", type="primary", use_container_width=True, key="submit_question"):
            if response:
                st.session_state.voice_call_messages.append({
                    "role": "patient",
                    "content": response,
                    "step_id": step["id"]
                })
            else:
                st.session_state.voice_call_messages.append({
                    "role": "patient",
                    "content": "沒有其他問題",
                    "step_id": step["id"]
                })
            st.session_state.voice_call_step += 1
            st.rerun()


def render_quick_replies(step):
    """渲染快速回覆按鈕"""
    st.markdown("**請回應：**")
    
    cols = st.columns(len(step["quick_replies"]))
    for i, reply in enumerate(step["quick_replies"]):
        with cols[i]:
            if st.button(reply, key=f"quick_{step['id']}_{i}", use_container_width=True):
                st.session_state.voice_call_messages.append({
                    "role": "patient",
                    "content": reply,
                    "step_id": step["id"]
                })
                st.session_state.voice_call_step += 1
                st.rerun()


def render_closing(step, patient):
    """渲染結束語"""
    st.markdown("---")
    
    if st.button("📵 結束通話", type="primary", use_container_width=True, key="finish_call"):
        st.session_state.voice_call_ended = True
        st.rerun()


def generate_summary():
    """生成症狀摘要"""
    scores = st.session_state.voice_call_scores
    parts = []
    
    if "overall" in scores:
        parts.append(f"整體{scores['overall']}分")
    if "pain" in scores:
        parts.append(f"疼痛{scores['pain']}分")
    if "dyspnea" in scores:
        parts.append(f"呼吸困難{scores['dyspnea']}分")
    if "fatigue" in scores:
        parts.append(f"疲勞{scores['fatigue']}分")
    if "cough" in scores:
        parts.append(f"咳嗽{scores['cough']}分")
    
    return "、".join(parts) if parts else "狀況良好"


def render_call_report(patient):
    """渲染通話結束報告"""
    scores = st.session_state.voice_call_scores
    alert_level, alert_text = calculate_alert_level(scores, st.session_state.safety_flags)
    
    # 計算通話時長
    if st.session_state.voice_call_start_time:
        duration = datetime.now() - st.session_state.voice_call_start_time
        duration_str = f"{int(duration.total_seconds() // 60)}:{int(duration.total_seconds() % 60):02d}"
    else:
        duration_str = "3:42"
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div style="font-size: 4rem;">📞</div>
        <h2 style="color: #1e293b; margin: 0.5rem 0;">通話已結束</h2>
        <p style="color: #64748b;">感謝您的配合！</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 警示等級
    alert_class = f"alert-{alert_level}"
    st.markdown(f"""
    <div class="call-report-card">
        <div class="report-header">
            <div>
                <div style="font-weight: 600; color: #1e293b;">📋 症狀追蹤報告</div>
                <div style="font-size: 0.85rem; color: #64748b;">
                    {datetime.now().strftime('%Y-%m-%d %H:%M')} | 通話時長 {duration_str}
                </div>
            </div>
            <div class="alert-badge {alert_class}">{alert_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 症狀分數摘要
    st.markdown("#### 📊 症狀評估")
    
    col1, col2, col3 = st.columns(3)
    symptom_display = [
        ("overall", "💪 整體", col1),
        ("pain", "🩹 疼痛", col2),
        ("dyspnea", "💨 呼吸", col3),
        ("fatigue", "😮‍💨 疲勞", col1),
        ("cough", "🤧 咳嗽", col2),
    ]
    
    for symptom_id, label, col in symptom_display:
        score = scores.get(symptom_id, 0)
        if score <= 3:
            color = "#10b981"
        elif score <= 6:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        
        with col:
            st.markdown(f"""
            <div style="background: #f8fafc; border-radius: 12px; padding: 1rem; text-align: center; margin-bottom: 0.5rem;">
                <div style="font-size: 1.75rem; font-weight: 700; color: {color};">{score}</div>
                <div style="font-size: 0.85rem; color: #64748b;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 其他資訊
    with col3:
        sleep_status = scores.get("sleep", "未回答")
        appetite_status = scores.get("appetite", "未回答")
        st.markdown(f"""
        <div style="background: #f8fafc; border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 0.9rem;">😴 {sleep_status}</div>
            <div style="font-size: 0.9rem;">🍽️ {appetite_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 安全檢查結果
    st.markdown("#### 🔍 安全檢查")
    safety_col1, safety_col2 = st.columns(2)
    
    with safety_col1:
        fever_status = "⚠️ 有發燒" if st.session_state.safety_flags.get("fever") else "✅ 無發燒"
        fever_color = "#ef4444" if st.session_state.safety_flags.get("fever") else "#10b981"
        st.markdown(f"""
        <div style="background: #f8fafc; border-radius: 12px; padding: 1rem; text-align: center;">
            <span style="color: {fever_color}; font-weight: 600;">{fever_status}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with safety_col2:
        wound_status = "⚠️ 傷口異常" if st.session_state.safety_flags.get("wound_issue") else "✅ 傷口正常"
        wound_color = "#ef4444" if st.session_state.safety_flags.get("wound_issue") else "#10b981"
        st.markdown(f"""
        <div style="background: #f8fafc; border-radius: 12px; padding: 1rem; text-align: center;">
            <span style="color: {wound_color}; font-weight: 600;">{wound_status}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # 後續行動
    st.markdown("#### 📌 後續行動")
    follow_up = get_follow_up_action(alert_level)
    
    if alert_level == "red":
        st.error(f"🚨 {follow_up}")
    elif alert_level == "yellow":
        st.warning(f"⚠️ {follow_up}")
    else:
        st.success(f"✅ {follow_up}")
    
    # 資料同步說明
    st.info("📤 此次通話內容已自動儲存並同步至醫療團隊後台")
    
    st.markdown("---")
    
    # 返回按鈕
    if st.button("🏠 返回首頁", type="primary", use_container_width=True):
        # 重置狀態
        st.session_state.voice_call_step = 0
        st.session_state.voice_call_messages = []
        st.session_state.voice_call_scores = {}
        st.session_state.voice_call_started = False
        st.session_state.voice_call_ended = False
        st.session_state.voice_call_start_time = None
        st.session_state.safety_flags = {"fever": False, "wound_issue": False}
        st.session_state.today_reported = True  # 標記今日已完成回報
        st.session_state.current_page = "home"
        st.rerun()


def render_voice_call_demo():
    """主要渲染函數：AI 語音電話 Demo"""
    
    # 載入 CSS
    st.markdown(get_voice_call_css(), unsafe_allow_html=True)
    
    # 初始化狀態
    init_voice_call_state()
    
    patient = st.session_state.patient
    
    # 頁面標題
    st.markdown("### 📞 AI 語音電話 Demo")
    st.markdown("體驗 AI 語音機器人主動撥打電話追蹤症狀的流程")
    
    # Demo 說明
    if not st.session_state.voice_call_started:
        st.markdown("""
        <div style="background: #E0F2F1; border: 1px solid #00897B; border-radius: 12px; 
                    padding: 1rem; margin: 1rem 0; font-size: 0.9rem;">
            <strong>💡 Demo 說明：</strong><br>
            這是模擬 <strong>Bland AI</strong> 語音電話機器人的互動體驗。<br>
            實際系統會在每日固定時間（如 09:00）自動撥打電話給病人，<br>
            透過自然語言對話收集症狀資訊，並即時回報給醫療團隊。
        </div>
        """, unsafe_allow_html=True)
    
    # 返回按鈕（非通話中顯示）
    if not st.session_state.voice_call_started:
        if st.button("← 返回首頁", key="back_to_home"):
            st.session_state.current_page = "home"
            st.rerun()
        st.markdown("---")
    
    # 根據狀態渲染不同畫面
    if st.session_state.voice_call_ended:
        # 通話結束，顯示報告
        render_call_report(patient)
    elif not st.session_state.voice_call_started:
        # 來電畫面
        render_incoming_call(patient)
    else:
        # 通話中
        render_active_call(patient)
