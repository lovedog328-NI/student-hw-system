import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection
import time

st.set_page_config(page_title="303作業登記-完美排序版", layout="wide")

# --- 1. 固定學生名單 (22位) ---
STUDENT_LIST = [
    {"座號": "1", "姓名": "王瑀淮"}, {"座號": "2", "姓名": "李祐嘉"},
    {"座號": "3", "姓名": "郭晁瑋"}, {"座號": "4", "姓名": "廖勇傑"},
    {"座號": "5", "姓名": "潘彥廷"}, {"座號": "6", "姓名": "郭家宇"},
    {"座號": "7", "姓名": "王悅芯"}, {"座號": "8", "姓名": "劉橙"},
    {"座號": "9", "姓名": "洪語緹"}, {"座號": "10", "姓名": "林祈平"},
    {"座號": "11", "姓名": "鄧安晴"}, {"座號": "12", "姓名": "蔣語桐"},
    {"座號": "13", "姓名": "邱薇瑀"}, {"座號": "14", "姓名": "鍾芮昕"},
    {"座號": "15", "姓名": "詹筠蓁"}, {"座號": "16", "姓名": "劉姝言"},
    {"座號": "17", "姓名": "范庭蓁"}, {"座號": "18", "姓名": "呂佳恩"},
    {"座號": "19", "姓名": "楊晨妤"}, {"座號": "20", "姓名": "劉芮安"},
    {"座號": "21", "姓名": "蔡芊芊"}, {"座號": "22", "姓名": "王楷晴"}
]

# --- 2. 雲端讀寫與排序核心 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def process_sort(df):
    """統一排序邏輯：作業名稱 -> 座號"""
    if df.empty: return df
    # 建立臨時排序列，確保座號是按數字排 (1, 2, 3...) 而非字串 (1, 10, 11...)
    df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
    # 先排作業名稱，再排座號
    df = df.sort_values(by=["作業名稱", "座號_int"], ascending=[True, True])
    return df.drop(columns=['座號_int'])

def load_data_api():
    try:
        df_raw = conn.read(ttl=0)
        if not df_raw.empty:
            last_content = df_raw.iloc[-1, -1]
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            return process_sort(df)
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_and_refresh(df):
    # 存檔前再次強制排序，確保雲端資料也是整齊的
    df_sorted = process_sort(df)
    st.session_state.main_df = df_sorted
    try:
        csv_str = df_sorted.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        st.cache_data.clear()
        return True
    except:
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data_api()

# --- 3. 介面設計 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == "alice":
        st.sidebar.success("✅ 老師模式已解鎖")
    else:
        is_admin = False

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢 / 修改", "🛠️ 老師管理後台"])

# --- 功能 A：查詢與即時修改 ---
if menu == "🔍 學生查詢 / 修改":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號查詢 (1-22)：", key="q_sid")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業狀況")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.
