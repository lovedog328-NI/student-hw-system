import streamlit as st
import pandas as pd
import io
from datetime import date, datetime
import requests
import time
import random

# --- 1. 頁面配置 ---
st.set_page_config(page_title="303作業登記", layout="wide")

# --- 2. 核心常數與名單 ---
STUDENT_LIST = [
    {"座號": str(i), "姓名": name} for i, name in enumerate([
        "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
        "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言",
        "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
    ], 1)
]

# --- 3. 雲端抓取函數 (強化避開快取) ---
def fetch_cloud_data():
    try:
        # 使用精確到微秒的時間戳作為隨機序號，徹底避開快取
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&gid=0&upd={timestamp}"
        
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache', 'Expires': '0'}
        r = requests.get(url, headers=headers, timeout=5)
        
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                # 抓取最後一格儲存的完整 CSV 字串
                last_csv_content = str(df_raw.iloc[-1, -1])
                if "座號" in last_csv_content:
                    return pd.read_csv(io.StringIO(last_csv_content), dtype={'座號': str})
    except Exception as e:
        st.sidebar.error(f"同步異常: {e}")
    return None

def push_to_cloud(df):
    csv_str = df.to_csv(index=False)
    try:
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        st.session_state.main_df = df # 立即更新本地記憶體
        st.session_state.last_update_time = time.time()
        return True
    except:
        return False

# --- 4. 初始化數據 ---
if 'main_df' not in st.session_state:
    with st.spinner("首次啟動，正在抓取資料..."):
        initial_data = fetch_cloud_data()
        if initial_data is not None:
            st.session_state.main_df = initial_data
        else:
            # 建立初始空表
            st.session_state.main_df = pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
    st.session_state.last_update_time = time.time()

# --- 5. 自動倒數刷新邏輯 (每一分鐘刷新一次) ---
refresh_rate = 60 # 秒
time_passed = time.time() - st.session_state.last_update_time
time_remaining = max(0, refresh_rate - int(time_passed))

# 在側邊欄顯示倒數
st.sidebar.markdown(f"### ⏳ 自動同步倒數: `{time_remaining}` 秒")
if time_remaining <= 0:
    new_data = fetch_cloud_data()
    if new_data is not None:
        st.session_state.main_df = new_data
    st.session_state.last_update_time = time.time()
    st.rerun()

# --- 6. UI 介面 ---
st.title("📚 303 作業登記系統")
st.sidebar.title("🔐 管理員")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if is_admin:
    st.sidebar.success("管理模式已開啟")
    if st.sidebar.button("🔄 手動即時同步"):
        st.session_state.main_df = fetch_cloud_data()
        st.session_state.last_update_time = time.time()
        st.rerun()

menu = st.sidebar.selectbox("切換功能", ["🔍 查詢作業", "🛠️ 老師後台"])

def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = date.today().strftime("%m/%d")
    push_to_cloud(st.session_state.main_df)

# --- 功能區 ---
if menu == "🔍 查詢作業":
    sid = st.text_input("請輸入座號：", placeholder="例如: 5")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的清單")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.success("✨ 太棒了！目前沒有欠交作業。")
            else:
                for i, r in todo.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"📌 **{r['作業名稱']}**")
                    c2.info(r['繳交狀態'])
                    if is_admin:
                        c3.button("設為已交", key=f"q_{i}", on_click=update_status, args=(i, "已繳交"))
            
            with st.expander("查看已繳交項目"):
                st.write(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])
        else:
            st.info("查無此座號的作業紀錄。")

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("請先輸入密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交名單", "🎯 快速登記", "📝 新增作業"])
        
        with tab1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel_hw = st.selectbox("選擇作業項目", ["請選擇"] + list(hws))
            if sel_hw != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel_hw) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                st.write(f"共有 {len(m)} 人未完成")
                for i, r in m.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"座號 {r['座號']}: {r['姓名']}")
                    cb.button("已繳交", key=f"t1_{i}", on_click=update_status, args=(i, "已繳交"))

        with tab2:
            tsid = st.text_input("座號快速補交：", key="tsid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"] == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in sm.iterrows():
                    ra, rb = st.columns([4, 1])
                    ra.write(f"作業: {r['作業名稱']}")
                    rb.button("完成", key=f"t2_{i}", on_click=update_status, args=(i, "已繳交"))

        with tab3:
            st.subheader("發佈新作業")
            new_name = st.text_input("請輸入新作業名稱 (例如: 數習 P.50)：")
            if st.button("🚀 確認發佈"):
                if new_name and new_name not in st.session_state.main_df["作業名稱"].values:
                    # 建立新名單
                    new_rows = []
                    today_str = date.today().strftime("%m/%d")
                    for s in STUDENT_LIST:
                        new_rows.append({"座號": s['座號'], "姓名": s['姓名'], "作業名稱": new_name, "繳交狀態": "未繳交", "更新日期": today_str})
                    
                    updated_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    if push_to_cloud(updated_df):
                        st.success(f"已發佈 {new_name}！系統將自動同步...")
                        time.sleep(1.5)
                        st.rerun()
                else:
                    st.error("名稱重複或為空值。")

        st.divider()
        with st.expander("🗑️ 刪除舊作業紀錄"):
            target = st.selectbox("選取要刪除的作業：", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("確認永久刪除") and target != "請選擇":
                new_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
                push_to_cloud(new_df)
                st.rerun()

# --- 7. 自動定時器 (隱藏在底部，強制 Streamlit 定時重刷) ---
time.sleep(1) # 避免過度消耗 CPU
st.rerun()
