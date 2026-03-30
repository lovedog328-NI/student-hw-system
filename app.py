import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection
import time

st.set_page_config(page_title="303作業登記-全功能回歸", layout="wide")

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

# --- 2. API 連線與儲存核心 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_api():
    try:
        df_raw = conn.read(ttl=0)
        if not df_raw.empty:
            last_content = df_raw.iloc[-1, -1]
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            df['座號_int'] = df['座號'].astype(int)
            return df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
    except Exception as e:
        st.sidebar.error(f"連線讀取中... 若持續報錯請檢查權限")
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_all(df):
    st.session_state.main_df = df
    try:
        df_sorted = df.copy()
        df_sorted['座號_int'] = df_sorted['座號'].astype(int)
        df_sorted = df_sorted.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
        csv_str = df_sorted.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data_api()

# --- 3. 介面設計 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == "alice":
        st.sidebar.success("✅ 已解鎖")
    else:
        is_admin = False

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢 / 修改", "🛠️ 老師管理後台"])

# --- 功能 A：查詢與即時修改 ---
if menu == "🔍 學生查詢 / 修改":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號 (1-22)：", key="query_sid")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業狀況")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success("✨ 全部交齊！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"`{row['繳交狀態']}`")
                    if is_admin:
                        if c3.button("已交", key=f"q_d_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_all(st.session_state.main_df); st.rerun()
                        if c4.button("訂正", key=f"q_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_all(st.session_state.main_df); st.rerun()
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

# --- 功能 B：老師管理後台 ---
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請先輸入密碼以進行管理")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])

        with t1:
            st.subheader("各項作業缺交名單 (直接點擊修改)")
            all_hws = st.session_state.main_df["作業名稱"].unique()
            sel_hw = st.selectbox("選擇作業：", ["請選擇"] + list(all_hws))
            if sel_hw != "請選擇":
                missing = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel_hw) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if missing.empty: st.success("🎉 交齊了")
                else:
                    for idx, r in missing.iterrows():
                        mc1, mc2, mc3 = st.columns([3, 1, 1])
                        mc1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                        if mc2.button("已交", key=f"ld_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            save_all(st.session_state.main_df); st.rerun()
                        if mc3.button("訂正", key=f"lr_{idx}"):
                            st.session_
