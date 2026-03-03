import streamlit as st
import pandas as pd
import plotly.express as px
from database import init_db, SessionLocal
from models import Issue, User
from ai_service import AIService
from datetime import datetime, date

# --- 初始化 ---
st.set_page_config(page_title="AI 客服案件管理系統 (BYOK)", layout="wide")
init_db()

# 在 session_state 中保持 AIService 實例，確保切換頁面時狀態不丟失
if 'ai_service' not in st.session_state:
    st.session_state['ai_service'] = AIService()
ai_service = st.session_state['ai_service']

# 自定義 CSS
st.markdown("""
<style>
    .stExpander { border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; }
    .overdue-badge { color: white; background-color: #ff4b4b; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
    .key-info { background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4b4b; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# --- 彈出視窗定義 ---
@st.dialog("原始訊息內容")
def show_raw_content_dialog(content):
    st.write("這是在 AI 解析之前的原始輸入內容：")
    st.code(content, language="text", wrap_lines=True)

# --- 側邊欄：BYOK 金鑰管理與導航 ---
st.sidebar.title("🛠️ AI 客服案件管理系統")
st.sidebar.write("---")

# 1. 導航選單
page = st.sidebar.radio("📋 系統導航", ["📊 數據統計中心", "📥 AI 智慧新增", "📋 案件總覽表", "🧱 多維度看板系統"])

st.sidebar.write("---")
st.sidebar.subheader("🔐 API 金鑰設定 (BYOK)")
st.sidebar.markdown("""
<div class="key-info">
<b>安全性說明：</b><br>
本系統採用「用後即焚」模式。您的 API Key 僅儲存於當前瀏覽器的記憶體中。
<br><b>重新整理網頁後金鑰將自動清除。</b>
</div>
""", unsafe_allow_html=True)

# 2. 金鑰輸入框
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder="輸入你的 Gemini Key")
groq_key = st.sidebar.text_input("Groq API Key", type="password", placeholder="輸入你的 Groq Key")

# 即時更新 AI Service 狀態
if gemini_key or groq_key:
    ai_service.update_keys(gemini_key=gemini_key if gemini_key else None, 
                           groq_key=groq_key if groq_key else None)

# 3. 引擎切換
ai_provider = st.sidebar.selectbox("🧠 AI 核心引擎切換", ["Gemini", "Groq (GPT-OSS 120B)"])
ai_service.set_provider("gemini" if "Gemini" in ai_provider else "groq")

# 4. 狀態檢查顯示
if ai_service.is_provider_ready():
    st.sidebar.success(f"✅ {ai_provider} 已就緒")
else:
    st.sidebar.warning(f"⚠️ {ai_provider} 尚未驗證金鑰")

st.sidebar.write("---")
st.sidebar.info(f"📅 今日：{date.today()}")

db = SessionLocal()

# --- 共用功能：金鑰檢查攔截器 ---
def check_key_before_action():
    if not ai_service.is_provider_ready():
        st.error(f"❌ 無法執行：尚未輸入 {ai_provider} 的 API 金鑰！")
        st.info("💡 請在左側側邊欄的「API 金鑰設定」中輸入您的金鑰後再試。")
        return False
    return True

# --- 頁面 1: 數據統計中心 ---
if page == "📊 數據統計中心":
    st.header("📊 企業數據洞察中心")
    issues = db.query(Issue).all()
    if not issues:
        st.info("目前尚無案件資料。")
    else:
        df = pd.DataFrame([i.to_dict() for i in issues])
        total_cnt = len(issues)
        unresolved = [i for i in issues if i.status != "已解決"]
        overdue_cnt = len([i for i in unresolved if i.due_date and i.due_date < date.today()])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("總案件", f"{total_cnt} 筆")
        c2.metric("待辦中", f"{len(unresolved)} 筆")
        c3.error(f"🚨 逾期：{overdue_cnt} 筆")
        c4.success(f"✅ 完成率：{(total_cnt-len(unresolved))/total_cnt*100:.1f}%")
        
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
    st.header("📥 AI 文字自動建模 (BYOK 模式)")
    col_input, col_form = st.columns([1, 1.2])
    
    with col_input:
        raw_input = st.text_area("✍️ 貼入對話原文：", height=400, placeholder="貼入 Line/Email 內容...")
        if st.button("✨ 啟動 AI 深度解析"):
            if check_key_before_action():
                if raw_input.strip():
                    with st.spinner(f"正在使用 {ai_provider} 進行解析..."):
                        analysis = ai_service.analyze_issue(raw_input)
                        if analysis: st.session_state['analysis_result'] = analysis
                        else: st.error("AI 解析失敗，請檢查金鑰是否正確或配額已達上限。")
    
    with col_form:
        with st.form("pro_form"):
            res = st.session_state.get('analysis_result', None)
            customer = st.text_input("🏢 客戶單位", value=res.customer_name if res else "")
            prod = st.text_input("🆔 產品/序號", value=res.product_id if res else "")
            summary = st.text_area("📝 問題核心摘要", value=res.summary if res else "", height=100)
            
            c3, c4, c5 = st.columns(3)
            prio_val = res.priority if res and res.priority in ["高", "中", "低"] else "中"
            priority = c3.selectbox("🚩 優先等級", ["高", "中", "低"], index=["高", "中", "低"].index(prio_val))
            due = c4.date_input("🗓️ 預計結案日期", value=date.today())
            users = db.query(User).all()
            agent = c5.selectbox("👤 指派承辦人", [u.name for u in users])
            
            if st.form_submit_button("🚀 歸檔案件"):
                target_user = db.query(User).filter(User.name == agent).first()
                new_issue = Issue(customer_name=customer, product_id=prod, summary=summary,
                                raw_content=raw_input, priority=priority, due_date=due,
                                status="待處理", agent_id=target_user.id)
                db.add(new_issue); db.commit()
                st.success("歸檔成功！"); st.session_state['analysis_result'] = None

# --- 頁面 3: 案件總覽表 ---
elif page == "📋 案件總覽表":
    st.header("📋 全系統案件數據")
    issues = db.query(Issue).all()
    if issues:
        df = pd.DataFrame([i.to_dict() for i in issues])
        event = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        selected_rows = event.get("selection", {}).get("rows", [])
        if selected_rows:
            selected_idx = selected_rows[0]
            selected_issue_id = df.iloc[selected_idx]['id']
            target_issue = db.query(Issue).filter(Issue.id == int(selected_issue_id)).first()
            if st.button(f"🔍 查看 案件 #{selected_issue_id} 的原始訊息"):
                show_raw_content_dialog(target_issue.raw_content)
    else: st.info("尚無數據。")

# --- 頁面 4: 看板系統 ---
elif page == "🧱 多維度看板系統":
    st.header("🧱 多維度流程管理看板")
    f_c1, f_c2 = st.columns(2)
    users = db.query(User).all()
    sel_agent = f_c1.selectbox("👤 按負責人", ["全部"] + [u.name for u in users])
    sel_prio = f_c2.multiselect("🚩 按優先級", ["高", "中", "低"], default=["高", "中", "低"])
    
    st.divider()
    cols = st.columns(3)
    statuses = ["待處理", "處理中", "已解決"]
    for i, s in enumerate(statuses):
        with cols[i]:
            st.markdown(f"### {s}")
            query = db.query(Issue).filter(Issue.status == s)
            if sel_agent != "全部": query = query.join(User).filter(User.name == sel_agent)
            query = query.filter(Issue.priority.in_(sel_prio))
            items = query.all()
            for item in items:
                with st.expander(f"{item.customer_name} ({item.priority})"):
                    st.write(f"**摘要：** {item.summary}")
                    if st.button("📄 查看原始內容", key=f"raw_{item.id}"):
                        show_raw_content_dialog(item.raw_content)
                    st.divider()
                    new_s = st.selectbox("調整狀態", statuses, index=statuses.index(s), key=f"kb_v4_{item.id}")
                    if new_s != s:
                        item.status = new_s; db.commit(); st.rerun()

db.close()
