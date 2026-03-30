import streamlit as st
import pandas as pd
import io
from datetime import date
import requests
import time
import random

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記", layout="wide")
st.title("📚 303 作業登記系統")

# --- 2. 學生名單 ---
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

# --- 3. 初始欠交清單 (備援) ---
DEF_DATA = [("19", "3/27聯絡簿", "未繳交"), ("4", "L2圈詞", "需訂正"), ("6", "L2圈詞", "未繳交")] # 縮減示範，請保留完整版

# --- 4. 強制同步邏輯 ---
def get_cloud_data():
    """使用禁用快取的 Header 強制抓取最新資料"""
    try:
        # 生成一個隨機數，讓 Google 認為這是一個全新的請求
        cache_buster = random.randint(1, 999999)
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&gid=0&cache={cache_buster}"
        
        # 設定 Headers 告訴伺服器不要使用快取
        headers = {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                content = str(df_raw.iloc[-1, -1])
                if "座號" in content:
                    return pd.read_csv(io.StringIO(content), dtype={'座號': str})
    except:
        pass
    return None

def save_to_cloud(df):
    csv_str = df.to_csv(index=False)
    try:
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        # 送出資料
        requests.post(url, data={eid: csv_str}, timeout=5)
        # 存檔後標記，讓本地暫存立即生效
        st.session_state.main_df = df
        st.session_state.last_sync = time.time()
        return True
    except:
        return False

# 初始化
if 'main_df' not in st.session_state:
    cloud_df = get_cloud_data()
    if cloud_df is not None:
        st.session_state.main_df = cloud_df
    else:
        # 這裡請接續之前的 init_df() 邏輯
        st.session_state.main_df = pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# --- 5. UI 介面 ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

# 🔍 同步狀態顯示
if st.sidebar.button("🔄 立即同步雲端資料"):
    with st.sidebar.status("正在同步...", expanded=False) as status:
        new_df = get_cloud_data()
        if new_df is not None:
            st.session_state.main_df = new_df
            status.update(label="✅ 同步成功！", state="complete")
            st.rerun()
        else:
            status.update(label="❌ 同步失敗，請稍後再試", state="error")

menu = st.sidebar.selectbox("選單", ["🔍 學生查詢", "🛠️ 老師後台"])

# ... (其餘學生查詢與老師後台邏輯，請沿用上一版的 update_status, t1, t2, t3) ...
