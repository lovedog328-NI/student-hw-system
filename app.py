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
    {"座號": str(i), "姓名": name} for i, name in enumerate([
        "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
        "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言",
        "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
    ], 1)
]

# --- 3. 初始備援資料 (精簡版) ---
def get_init_df():
    # 這裡放你最原始的那份 3/27 資料清單 (為了節省篇幅，建議先放空表或核心幾筆)
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# --- 4. 強化同步邏輯 ---
def fetch_cloud():
    """強制抓取最新雲端 CSV"""
    try:
        cb = random.randint(1, 999999)
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&gid=0&cache={cb}"
        r = requests.get(url, timeout=5, headers={'Cache-Control': 'no-cache'})
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                last_content = str(df_raw.iloc[-1, -1])
                if "座號" in last_content:
                    return pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
    except:
        pass
    return None

def sync_to_cloud(df):
    """將資料推送到雲端"""
    csv_str = df.to_csv(index=False)
    try:
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        st.session_state.main_df = df # 更新本地
        return True
    except:
        return False

# 初始化：僅在第一次啟動時抓雲端
if 'main_df' not in st.session_state:
    cloud = fetch_cloud()
    st.session_state.main_df = cloud if cloud is not None else get_init_df()

# --- 5. UI 介面 ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

# 🔄 真正的同步按鈕：這會把雲端跟本地合併
if st.sidebar.button("🔄 同步並刷新資料"):
    with st.spinner("同步中..."):
        new_cloud = fetch_cloud()
        if new_cloud is not None:
            # 合併策略：以作業名稱+座號為基準，取更新日期較晚的
            combined = pd.concat([st.session_state.main_df, new_cloud]).drop_duplicates(
                subset=['座號', '作業名稱'], keep='last'
            )
            st.session_state.main_df = combined
            st.success("同步完成！")
            st.rerun()

menu = st.sidebar.selectbox("選單", ["🔍 查詢", "🛠️ 後台"])

def update_val(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    sync_to_cloud(st.session_state.main_df)

if menu == "🔍 查詢":
    sid = st.text_input("輸入座號：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']}")
            todo = res[res["繳交狀態"] != "已繳交"]
            for idx, row in todo.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"📌 {row['作業名稱']} ({row['繳交狀態']})")
                if is_admin:
                    c2.button("已交", key=f"q_{idx}", on_click=update_val, args=(idx, "已繳交"))
                    c3.button("訂正", key=f"qr_{idx}", on_click=update_val, args=(idx, "需訂正"))
            with st.expander("已完成"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])
        else:
            st.info("查無資料，請確認是否已由老師新增作業。")

elif menu == "🛠️ 後台":
    if not is_admin:
        st.warning("請輸入密碼")
    else:
        t1, t2, t3 = st.tabs(["缺交", "補交", "新增"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in m.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    cb.button("已交", key=f"t1_{i}", on_click=update_val, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t1r_{i}", on_click=update_val, args=(i, "需訂正"))

        with t2:
            tsid = st.text_input("補交座號：", key="tsid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"] == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in sm.iterrows():
                    ra, rb, rc = st.columns([3, 1, 1])
                    ra.write(f"📌 {r['作業名稱']}")
                    rb.button("已交", key=f"t2_{i}", on_click=update_val, args=(i, "已繳交"))
                    rc.button("訂正", key=f"t2r_{i}", on_click=update_val, args=(i, "需訂正"))

        with t3:
            st.subheader("📝 新增整班作業")
            new_n = st.text_input("名稱：")
            if st.button("🚀 點此發佈") and new_n:
                # 檢查是否已存在同名作業
                if new_n in st.session_state.main_df["作業名稱"].values:
                    st.error("作業名稱重複！")
                else:
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":new_n, "繳交狀態":"未繳交", "更新日期":str(date.today())} for s in STUDENT_LIST]
                    new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    if sync_to_cloud(new_df):
                        st.success(f"已發佈 {new_n}，正在同步至雲端...")
                        time.sleep(2) # 給 Google 一點寫入時間
                        st.rerun()

        st.divider()
        with st.expander("🗑️ 刪除作業"):
            target = st.selectbox("選取：", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("確認刪除") and target != "請選擇":
                sync_to_cloud(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target])
                st.rerun()
