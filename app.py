import streamlit as st
import pandas as pd
import plotly.express as px
from database import init_user_db
from models import Issue, User
from ai_service import AIService
from datetime import datetime, date

# --- 系統標題設定 ---
st.set_page_config(page_title="AI 客服案件管理系統 (Multi-User)", layout="wide")

# 初始化 Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'ai_service' not in st.session_state:
    st.session_state['ai_service'] = AIService()

# 自定義 CSS
st.markdown("""
<style>
    .stExpander { border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; }
    .login-container { max-width: 400px; margin: 100px auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- 1. 登入/註冊邏輯 ---
if not st.session_state['logged_in']:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.header("🏢 AI 案件管理系統 - 登入")
    st.write("這是專屬資料庫模式，輸入名稱即自動建立或登入您的空間。")
    
    user_name = st.text_input("請輸入您的使用者名稱 (英文或數字)：", placeholder="例如: bob_pro")
    
    if st.button("🚀 登入 / 註冊"):
        if user_name.strip():
            # 初始化該使用者的專屬資料庫
            engine, Session = init_user_db(user_name.strip())
            st.session_state['username'] = user_name.strip()
            st.session_state['logged_in'] = True
            st.session_state['db_session'] = Session
            st.rerun()
        else:
            st.error("請輸入有效的使用者名稱。")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # 停止執行後續程式碼，直到登入

# --- 2. 登入後的邏輯 ---
username = st.session_state['username']
Session = st.session_state['db_session']
db = Session()
ai_service = st.session_state['ai_service']

# 彈出視窗定義 (查看原始訊息)
@st.dialog("原始訊息內容")
def show_raw_content_dialog(content):
    st.write(f"這是來自使用者 **{username}** 資料庫中的原始內容：")
    st.code(content, language="text", wrap_lines=True)

# 側邊欄導航與 BYOK
st.sidebar.title(f"👤 您好, {username}")
st.sidebar.write("---")

# 登出按鈕
if st.sidebar.button("🚪 登出系統"):
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.rerun()

st.sidebar.write("---")
page = st.sidebar.radio("📋 系統導航", ["📊 數據統計中心", "📥 AI 智慧新增", "📋 案件總覽表", "🧱 多維度看板系統"])

# BYOK 設定
st.sidebar.write("---")
st.sidebar.subheader("🔐 API 金鑰設定 (BYOK)")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", value="", key="gem_k")
groq_key = st.sidebar.text_input("Groq API Key", type="password", value="", key="grq_k")

if gemini_key or groq_key:
    ai_service.update_keys(gemini_key=gemini_key if gemini_key else None, 
                           groq_key=groq_key if groq_key else None)

ai_provider = st.sidebar.selectbox("🧠 AI 核心引擎", ["Gemini", "Groq (GPT-OSS 120B)"])
ai_service.set_provider("gemini" if "Gemini" in ai_provider else "groq")

# --- 頁面 1: 數據統計中心 ---
if page == "📊 數據統計中心":
    st.header(f"📊 {username} 的專屬營運中心")
    issues = db.query(Issue).all()
    if not issues:
        st.info("您的空間目前尚無案件，請前往「新增案件」開始體驗！")
    else:
        df = pd.DataFrame([i.to_dict() for i in issues])
        c1, c2, c3 = st.columns(3)
        c1.metric("您的總案件", len(issues))
        c2.metric("待處理", len([i for i in issues if i.status != "已解決"]))
        c3.success(f"用戶空間：{username}")
        
        st.divider()
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.subheader("📌 案件狀態佔比")
            st.plotly_chart(px.pie(df, names='status', hole=0.3), use_container_width=True)
        with r1c2:
            st.subheader("🎯 優先等級權重")
            st.plotly_chart(px.pie(df, names='priority', hole=0.3), use_container_width=True)

# --- 頁面 2: 新增案件 ---
elif page == "📥 AI 智慧新增":
    st.header(f"📥 {username} 的 AI 自動建模")
    col_input, col_form = st.columns([1, 1.2])
    
    with col_input:
        raw_input = st.text_area("✍️ 貼入對話原文：", height=400)
        if st.button("✨ 啟動 AI 深度解析"):
            if not ai_service.is_provider_ready():
                st.error("❌ 尚未輸入 API 金鑰，請於側邊欄輸入。")
            else:
                with st.spinner("AI 運算中..."):
                    analysis = ai_service.analyze_issue(raw_input)
                    if analysis: st.session_state['analysis_result'] = analysis
    
    with col_form:
        with st.form("pro_form"):
            res = st.session_state.get('analysis_result', None)
            customer = st.text_input("🏢 客戶單位", value=res.customer_name if res else "")
            prod = st.text_input("🆔 產品/序號", value=res.product_id if res else "")
            summary = st.text_area("📝 問題摘要", value=res.summary if res else "")
            
            c3, c4, c5 = st.columns(3)
            prio_val = res.priority if res and res.priority in ["高", "中", "低"] else "中"
            priority = c3.selectbox("🚩 優先等級", ["高", "中", "低"], index=["高", "中", "低"].index(prio_val))
            due = c4.date_input("🗓️ 預計結案日期", value=date.today())
            
            users = db.query(User).all()
            agent = c5.selectbox("👤 指派承辦人", [u.name for u in users])
            
            if st.form_submit_button("🚀 歸檔至您的資料庫"):
                target_user = db.query(User).filter(User.name == agent).first()
                new_issue = Issue(customer_name=customer, product_id=prod, summary=summary,
                                raw_content=raw_input, priority=priority, due_date=due,
                                status="待處理", agent_id=target_user.id)
                db.add(new_issue); db.commit()
                st.success("歸檔完成！"); st.session_state['analysis_result'] = None

# --- 其餘頁面維持現有邏輯，但都是操作 db (該使用者的 Session) ---
elif page == "📋 案件總覽表":
    st.header(f"📋 {username} 的案件清單")
    issues = db.query(Issue).all()
    if issues:
        df = pd.DataFrame([i.to_dict() for i in issues])
        event = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        selected_rows = event.get("selection", {}).get("rows", [])
        if selected_rows:
            selected_issue_id = df.iloc[selected_rows[0]]['id']
            target_issue = db.query(Issue).filter(Issue.id == int(selected_issue_id)).first()
            if st.button(f"🔍 查看 案件 #{selected_issue_id} 原始內容"):
                show_raw_content_dialog(target_issue.raw_content)
    else: st.info("目前無資料。")

elif page == "🧱 多維度看板系統":
    st.header(f"🧱 {username} 的看板管理")
    issues = db.query(Issue).all()
    if not issues: st.info("無資料。")
    else:
        cols = st.columns(3)
        statuses = ["待處理", "處理中", "已解決"]
        for i, s in enumerate(statuses):
            with cols[i]:
                st.markdown(f"### {s}")
                items = db.query(Issue).filter(Issue.status == s).all()
                for item in items:
                    with st.expander(f"{item.customer_name} ({item.priority})"):
                        st.write(f"摘要：{item.summary}")
                        if st.button("📄 查看原始內容", key=f"raw_{item.id}"):
                            show_raw_content_dialog(item.raw_content)
                        st.divider()
                        new_s = st.selectbox("調整狀態", statuses, index=statuses.index(s), key=f"kb_v_{item.id}")
                        if new_s != s:
                            item.status = new_s; db.commit(); st.rerun()

db.close()
