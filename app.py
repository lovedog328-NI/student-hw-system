import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定與精美 CSS 樣式 ---
st.set_page_config(page_title="303作業登記-精美公佈欄", layout="wide")

# ✨ 植入精美卡片的 CSS 樣式
st.markdown("""
<style>
.student-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    background: var(--background-color);
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border-top: 4px solid #4CAF50;
}
.student-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.1);
}
.student-name {
    margin-top: 0;
    margin-bottom: 12px;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-color);
}
.hw-tag-red {
    background-color: rgba(211, 47, 47, 0.1);
    color: #d32f2f;
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: bold;
    display: inline-block;
    margin: 4px 4px 4px 0;
    border: 1px solid rgba(211, 47, 47, 0.2);
}
.hw-tag-orange {
    background-color: rgba(230, 81, 0, 0.1);
    color: #e65100;
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: bold;
    display: inline-block;
    margin: 4px 4px 4px 0;
    border: 1px solid rgba(230, 81, 0, 0.2);
}
.empty-state {
    text-align: center;
    padding: 50px;
    background-color: rgba(76, 175, 80, 0.1);
    border-radius: 15px;
    border: 2px dashed #4CAF50;
    color: #2E7D32;
}
</style>
""", unsafe_allow_html=True)

st.title("📚 303 作業登記系統")

# 固定學生名單
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

# --- 2. 核心資料與格式化邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def force_int_str(val):
    try: return str(int(float(val)))
    except: return str(val).strip()

def clean_score(val):
    s = str(val).strip()
    if s in ["", "nan", "NaN", "None"]: return ""
    try:
        f = float(s)
        if f.is_integer(): return str(int(f))
        return str(f)
    except:
        return s

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        df["座號"] = df["座號"].apply(force_int_str)
        df["成績"] = df["成績"].apply(clean_score)
        df = df[df["座號"] != ""]
        for s in STUDENT_LIST:
            df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])

def save_data_core(df):
    try:
        if df.empty: return False
        df_to_save = df.copy().fillna("")
        df_to_save["座號"] = df_to_save["座號"].apply(force_int_str)
        df_to_save["成績"] = df_to_save["成績"].apply(clean_score)
        conn.update(worksheet="Sheet1", data=df_to_save)
        return True
    except: return False

# --- 3. 系統暫存初始化 ---
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()
if 'has_unsaved_changes' not in st.session_state:
    st.session_state.has_unsaved_changes = False
if 'selected_hw_base' not in st.session_state:
    st.session_state.selected_hw_base = "請選擇"

# --- 4. Callbacks ---
def clean_seat_input(val_str):
    raw_list = val_str.replace("，", ",").split(",")
    res = []
    for s in raw_list:
        s = s.strip()
        if s: res.append(force_int_str(s))
    return res

def mark_fast(hw_name, status, input_key):
    val = st.session_state[input_key]
    if not val: return
    sids = clean_seat_input(val)
    for sid in sids:
        mask = (st.session_state.main_df["作業名稱"] == hw_name) & (st.session_state.main_df["座號"] == sid)
        st.session_state.main_df.loc[mask, "繳交狀態"] = status
        st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
    st.session_state.has_unsaved_changes = True
    st.session_state[input_key] = "" 

def update_single_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    st.session_state.has_unsaved_changes = True

def update_score(idx, score_key):
    new_val = clean_score(st.session_state[score_key])
    if str(st.session_state.main_df.at[idx, "成績"]) != new_val:
        st.session_state.main_df.at[idx, "成績"] = new_val
        st.session_state.has_unsaved_changes = True

def on_hw_select():
    sel_str = st.session_state.hw_sel_widget
    st.session_state.selected_hw_base = sel_str.split(" (")[0] if sel_str != "請選擇" else "請選擇"

# --- 5. 側邊欄與存檔 ---
st.sidebar.title("⚙️ 選單與功能")

# ✨ 改為三個選單，把公佈欄放在公開區域
menu = st.sidebar.radio("請選擇功能：", ["📊 班級公佈欄", "🔍 個人查詢", "🛠️ 老師後台"])

st.sidebar.divider()
pwd = st.sidebar.text_input("老師密碼 (管理員專用)", type="password")
is_admin = (pwd == "alice")

if is_admin:
    if st.session_state.has_unsaved_changes:
        st.sidebar.error("🚨 資料尚未同步至雲端")
        if st.sidebar.button("💾 儲存並同步", type="primary", use_container_width=True):
            if save_data_core(st.session_state.main_df):
                st.session_state.has_unsaved_changes = False
                st.sidebar.success("✅ 已存檔")
                st.rerun()
    else:
        st.sidebar.success("✔️ 雲端資料已同步")

if st.sidebar.button("🔄 重新載入最新資料"):
    st.session_state.main_df = load_data()
    st.session_state.has_unsaved_changes = False
    st.rerun()

# --- 6. 主畫面 UI ---

# [分頁 1：班級公佈欄 (學生/家長皆可看)]
if menu == "📊 班級公佈欄":
    st.markdown("### 🏆 目前全班未完成作業總覽")
    st.caption(f"最後更新日期：{date.today().strftime('%Y-%m-%d')}")
    
    todo_df = st.session_state.main_df[st.session_state.main_df["繳交狀態"] != "已繳交"]
    
    if todo_df.empty:
        st.balloons()
        st.markdown("""
        <div class="empty-state">
            <h1>🎉 太棒了！</h1>
            <h3>全班目前的作業皆已繳交完成！</h3>
            <p>請繼續保持這個好習慣喔！</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        todo_sids = sorted
