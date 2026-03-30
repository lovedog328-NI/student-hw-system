import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection
import time

st.set_page_config(page_title="303作業登記-API極速版", layout="wide")

# --- 1. 固定學生名單 ---
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

# --- 2. API 連線核心 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # ttl=0 代表不使用快取，每次都抓最新；若想更快可改為 ttl=60
        df_raw = conn.read(ttl=0)
        if not df_raw.empty:
            # 取得最後一格的 JSON 數據
            last_json = df_raw.iloc[-1, -1]
            df = pd.read_csv(io.StringIO(last_json), dtype={'座號': str})
            df['座號_int'] = df['座號'].astype(int)
            return df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
    except Exception as e:
        st.sidebar.error(f"連線中... {e}")
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_data(df):
    st.session_state.main_df = df
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. 介面邏輯 (保留您要求的所有功能) ---
# (為了縮短回應，此處省略與前版本相同的 UI 代碼，請將 UI 部分與上述 save_data 邏輯結合)
