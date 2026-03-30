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
                st.balloons(); st.success("✨ 作業全部交齊囉！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        if c3.button("已交", key=f"q_d_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_and_refresh(st.session_state.main_df); st.rerun()
                        if c4.button("訂正", key=f"q_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_and_refresh(st.session_state.main_df); st.rerun()
            with st.expander("查看已完成項目"):
                # 已完成的部分同樣會按作業名稱排好
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

# --- 功能 B：老師管理後台 ---
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請先輸入密碼。")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 座號補交", "📝 新增作業"])

        with t1:
            st.subheader("📋 缺交名單 (按座號排序)")
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業：", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 全班交齊")
                else:
                    for i, r in m.iterrows():
                        col_1, col_2, col_3 = st.columns([3, 1, 1])
                        col_1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                        if col_2.button("已交", key=f"t1_d_{i}"):
                            st.session_state.main_df.at[i, "繳交狀態"] = "已繳交"
                            save_and_refresh(st.session_state.main_df); st.rerun()
                        if col_3.button("訂正", key=f"t1_r_{i}"):
                            st.session_state.main_df.at[i, "繳交狀態"] = "需訂正"
                            save_and_refresh(st.session_state.main_df); st.rerun()

        with t2:
            st.subheader("🎯 依座號快速補交")
            tsid = st.text_input("請輸入座號：", key="t2_sid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if not sm.empty:
                    st.write(f"學生：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ca, cb, cc = st.columns([3, 1, 1])
                        ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                        if cb.button("✅ 已交", key=f"t2_d_{i}"):
                            st.session_state.main_df.at[i, "繳交狀態"] = "已繳交"
                            save_and_refresh(st.session_state.main_df); st.rerun()
                        if cc.button("✏️ 訂正", key=f"t2_r_{i}"):
                            st.session_state.main_df.at[i, "繳交狀態"] = "需訂正"
                            save_and_refresh(st.session_state.main_df); st.rerun()

        with t3:
            st.subheader("📝 新增整班作業")
            if 'hw_val' not in st.session_state: st.session_state.hw_val = ""
            hw_n = st.text_input("作業名稱 (例如：國習 L1)：", value=st.session_state.hw_val)
            if hw_n:
                if 'tmp' not in st.session_state or st.session_state.lhwn != hw_n:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = hw_n
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']; cur = st.session_state.tmp[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']} ({cur})", key=f"t3_b_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "已繳交" if cur == "未繳交" else "需訂正" if cur == "已繳交" else "未繳交"
                        st.rerun()
                if st.button("🚀 確認發佈並同步", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    up = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    if save_and_refresh(up):
                        st.session_state.hw_val = ""; st.session_state.lhwn = ""
                        st.success("發佈成功！"); st.rerun()

        st.divider()
        with st.expander("🗑️ 刪除錯誤作業"):
            dels = st.session_state.main_df["作業名稱"].unique()
            target = st.selectbox("選擇要刪除的作業：", ["請選擇"] + list(dels))
            confirm = st.checkbox("確認永久刪除")
            if st.button("❌ 執行刪除") and confirm and target != "請選擇":
                save_and_refresh(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]); st.rerun()

        if st.sidebar.button("🔄 強制刷新數據"):
            st.cache_data.clear()
            st.session_state.main_df = load_data_api()
            st.rerun()
