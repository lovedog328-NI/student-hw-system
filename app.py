import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection
import time

st.set_page_config(page_title="303作業登記-終極穩定版", layout="wide")

# --- 1. 學生名單 ---
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

# --- 2. 雲端核心邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def process_sort(df):
    if df is None or df.empty: return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
    df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
    df = df.sort_values(by=["作業名稱", "座號_int"], ascending=[True, True])
    return df.drop(columns=['座號_int']).reset_index(drop=True)

def load_data():
    try:
        # ttl=1 稍微留一點緩衝，避免過於頻繁的 API 請求被封鎖
        df_raw = conn.read(ttl=1)
        if not df_raw.empty:
            last_content = df_raw.iloc[-1, -1]
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            return process_sort(df)
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# 儲存函式：不使用 rerun，改用狀態更新
def sync_to_cloud(df):
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

# 初始化 Session State
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. UI 介面 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == "alice":
        st.sidebar.success("✅ 已解鎖")
    else:
        is_admin = False

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢 / 修改", "🛠️ 老師管理後台"])

# 定義按鈕點擊事件 (這是解決「不更新」的關鍵)
def update_status(idx, new_status):
    st.session_state.main_df.at[idx, "繳交狀態"] = new_status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    sync_to_cloud(st.session_state.main_df)
    st.toast(f"已更新為 {new_status}")

# --- 功能 A ---
if menu == "🔍 學生查詢 / 修改":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業狀況")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.success("✨ 作業全部交齊囉！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=update_status, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=update_status, args=(idx, "需訂正"))
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

# --- 功能 B ---
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請先輸入密碼。")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 座號補交", "📝 新增作業"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業：", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in m.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                    col2.button("已交", key=f"t1_d_{i}", on_click=update_status, args=(i, "已繳交"))
                    col3.button("訂正", key=f"t1_r_{i}", on_click=update_status, args=(i, "需訂正"))

        with t2:
            tsid = st.text_input("請輸入座號：", key="t2_sid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if not sm.empty:
                    st.write(f"學生：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ca, cb, cc = st.columns([3, 1, 1])
                        ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                        cb.button("✅ 已交", key=f"t2_d_{i}", on_click=update_status, args=(i, "已繳交"))
                        cc.button("✏️ 訂正", key=f"t2_r_{i}", on_click=update_status, args=(i, "需訂正"))

        with t3:
            st.subheader("📝 新增整班作業")
            hw_n = st.text_input("作業名稱：")
            if hw_n:
                if 'tmp' not in st.session_state or st.session_state.get('lhwn') != hw_n:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = hw_n
                
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']; cur = st.session_state.tmp[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']} ({cur})", key=f"t3_b_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "已繳交" if cur == "未繳交" else "需訂正" if cur == "已繳交" else "未繳交"
                        st.rerun()
                
                if st.button("🚀 確認發佈", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    st.session_state.main_df = process_sort(new_df)
                    sync_to_cloud(st.session_state.main_df)
                    st.success("已發佈並同步！")
                    time.sleep(1)
                    st.rerun()

        st.sidebar.divider()
        if st.sidebar.button("🔄 強制刷新雲端數據"):
            st.session_state.main_df = load_data()
            st.rerun()
