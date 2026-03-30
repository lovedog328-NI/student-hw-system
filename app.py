import streamlit as st
import pandas as pd
import io
from datetime import date, datetime
import requests
import time
import random

# --- 1. 頁面配置 ---
st.set_page_config(page_title="303作業登記", layout="wide")

# --- 2. 核心名單 (保險備份) ---
STUDENT_LIST = [
    {"座號": str(i), "姓名": name} for i, name in enumerate([
        "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
        "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言",
        "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
    ], 1)
]

# --- 3. 雲端抓取 (加入資料驗證) ---
def fetch_cloud_data():
    try:
        # 強制避開快取
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&gid=0&upd={timestamp}"
        
        r = requests.get(url, timeout=5, headers={'Cache-Control': 'no-cache'})
        
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                last_csv_content = str(df_raw.iloc[-1, -1])
                if "座號" in last_csv_content:
                    new_df = pd.read_csv(io.StringIO(last_csv_content), dtype={'座號': str})
                    # 🔍 關鍵驗證：如果抓到的資料行數太少，代表是不完整的資料，拒絕回傳
                    if len(new_df) >= 22: 
                        return new_df
    except:
        pass
    return None

def push_to_cloud(df):
    csv_str = df.to_csv(index=False)
    try:
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        st.session_state.main_df = df # 立即更新本地，防止消失
        st.session_state.last_sync_time = time.time()
        return True
    except:
        return False

# --- 4. 初始化 (確保初始一定有料) ---
if 'main_df' not in st.session_state or st.session_state.main_df is None:
    with st.spinner("正在喚醒資料庫..."):
        cloud_data = fetch_cloud_data()
        if cloud_data is not None:
            st.session_state.main_df = cloud_data
        else:
            # 如果雲端完全沒資料，建立一個基礎空白表
            st.session_state.main_df = pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
    st.session_state.last_sync_time = time.time()

# --- 5. UI 與同步邏輯 ---
st.title("📚 303 作業登記系統")
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

# 顯示同步狀態
if is_admin:
    st.sidebar.success("已開啟管理模式")
    if st.sidebar.button("🔄 手動即時同步雲端"):
        new_data = fetch_cloud_data()
        if new_data is not None:
            st.session_state.main_df = new_data
            st.sidebar.info("同步成功！")
            st.rerun()
        else:
            st.sidebar.warning("雲端暫無更新或資料不完整")

# 定時自動重整 (延長到 120 秒，減少衝突)
if time.time() - st.session_state.get('last_sync_time', 0) > 120:
    new_data = fetch_cloud_data()
    if new_data is not None:
        st.session_state.main_df = new_data
    st.session_state.last_sync_time = time.time()
    st.rerun()

menu = st.sidebar.selectbox("切換功能", ["🔍 查詢作業", "🛠️ 老師後台"])

def update_val(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = date.today().strftime("%m/%d")
    push_to_cloud(st.session_state.main_df)

# --- 功能實現 ---
if menu == "🔍 查詢作業":
    sid = st.text_input("請輸入座號：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.success("✨ 目前沒有欠交作業。")
            for i, r in todo.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"📌 {r['作業名稱']}")
                c2.write(f"`{r['繳交狀態']}`")
                if is_admin:
                    c3.button("設為已交", key=f"q_{i}", on_click=update_val, args=(i, "已繳交"))
        else:
            st.info("查無資料。請確認老師是否已新增作業。")

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("請輸入密碼解鎖後台")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 快速登記", "📝 新增作業"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in m.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"{r['座號']}. {r['姓名']}")
                    cb.button("已繳", key=f"t1_{i}", on_click=update_val, args=(i, "已繳交"))

        with t3:
            st.subheader("新增整班作業")
            name = st.text_input("作業名稱：")
            if st.button("🚀 發佈新作業") and name:
                new_rows = []
                for s in STUDENT_LIST:
                    new_rows.append({"座號": s['座號'], "姓名": s['姓名'], "作業名稱": name, "繳交狀態": "未繳交", "更新日期": ""})
                updated_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                push_to_cloud(updated_df)
                st.success(f"已發佈 {name}！")
                time.sleep(1)
                st.rerun()

        st.divider()
        with st.expander("🗑️ 刪除紀錄"):
            target = st.selectbox("選取要刪除的作業：", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("確認永久刪除") and target != "請選擇":
                new_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
                push_to_cloud(new_df)
                st.rerun()

# 頁面定時重刷，確保畫面活躍
time.sleep(2)
st.rerun()
