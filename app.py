import streamlit as st
import pandas as pd
import io
from datetime import date, datetime
import requests
import time

# --- 1. 頁面配置 ---
st.set_page_config(page_title="303作業登記", layout="wide")

# --- 2. 核心名單與歷史備份 (防空機制) ---
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate(["王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙", "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言", "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"], 1)]

# 這是當雲端完全沒資料時，用來救火的初始資料
def get_backup_df():
    # 這裡放入您之前提供的那串 3/27 紀錄 (精簡版示範)
    data = [("19", "3/27聯絡簿", "未繳交"), ("4", "L2圈詞", "需訂正"), ("6", "L2圈詞", "未繳交")]
    rows = []
    name_map = {s['座號']: s['姓名'] for s in STUDENT_LIST}
    for sid, hw, status in data:
        rows.append({"座號": sid, "姓名": name_map[sid], "作業名稱": hw, "繳交狀態": status, "更新日期": "03/27"})
    return pd.DataFrame(rows)

# --- 3. 強化版雲端抓取 ---
def fetch_data():
    try:
        # 使用隨機參數破解快取
        ts = datetime.now().strftime("%H%M%S")
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&gid=0&v={ts}"
        r = requests.get(url, timeout=5, headers={'Cache-Control': 'no-cache'})
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                last_csv = str(df_raw.iloc[-1, -1])
                if "座號" in last_csv:
                    df = pd.read_csv(io.StringIO(last_csv), dtype={'座號': str})
                    if len(df) > 10: return df # 至少要有10筆才算有效資料
    except:
        pass
    return None

def push_data(df):
    try:
        csv_str = df.to_csv(index=False)
        requests.post(st.secrets["google_sync"]["form_url"], data={st.secrets["google_sync"]["entry_id"]: csv_str}, timeout=5)
        st.session_state.main_df = df
        st.session_state.last_sync = time.time()
        return True
    except:
        return False

# --- 4. 初始化 ---
if 'main_df' not in st.session_state:
    cloud = fetch_data()
    st.session_state.main_df = cloud if cloud is not None else get_backup_df()
    st.session_state.last_sync = time.time()

# --- 5. UI 介面 ---
st.title("📚 303 作業登記系統")
st.sidebar.title("🔐 管理")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

# 每 5 分鐘自動背景同步一次 (減少重整頻率)
if time.time() - st.session_state.get('last_sync', 0) > 300:
    new_data = fetch_data()
    if new_data is not None: st.session_state.main_df = new_data
    st.session_state.last_sync = time.time()

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

def update_val(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = date.today().strftime("%m/%d")
    push_data(st.session_state.main_df)

if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號：", placeholder="1-22")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']}")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty: st.success("🎉 全部交齊囉！")
            for i, r in todo.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"📌 {r['作業名稱']}")
                c2.write(f"`{r['繳交狀態']}`")
                if is_admin:
                    c3.button("已交", key=f"q_{i}", on_click=update_val, args=(i, "已繳交"))
        else:
            st.warning("目前無此座號資料，請稍後再試或點選側邊欄同步。")
            if st.sidebar.button("🔄 立即修復資料"):
                st.session_state.main_df = fetch_data() or get_backup_df()
                st.rerun()

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.info("請輸入密碼解鎖後台功能。")
    else:
        t1, t2, t3 = st.tabs(["缺交清單", "快速登記", "新增作業"])
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", hws)
            m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
            for i, r in m.iterrows():
                ca, cb = st.columns([3, 1])
                ca.write(f"{r['座號']}. {r['姓名']}")
                cb.button("已繳", key=f"t1_{i}", on_click=update_val, args=(i, "已繳交"))
        with t3:
            name = st.text_input("新增作業名稱：")
            if st.button("🚀 確認發佈") and name:
                new_list = []
                for s in STUDENT_LIST:
                    new_list.append({"座號": s['座號'], "姓名": s['姓名'], "作業名稱": name, "繳交狀態": "未繳交", "更新日期": ""})
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_list)], ignore_index=True)
                push_data(st.session_state.main_df)
                st.success(f"已發佈 {name}")
                time.sleep(1)
                st.rerun()
