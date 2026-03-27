import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記-極速版", layout="wide")

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

# --- 2. 雲端讀寫核心 (加速優化版) ---
def load_from_cloud():
    try:
        csv_url = st.secrets["google_sync"]["sheet_csv_url"]
        # 使用時間戳記強制 Google 重新生成最新的 CSV 資料
        df_raw = pd.read_csv(f"{csv_url}&t={int(time.time())}")
        if not df_raw.empty:
            last_content = df_raw.iloc[-1, -1] 
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            df['座號_int'] = df['座號'].astype(int)
            df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
            return df
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_to_cloud_and_local(df):
    # 1. 先更新本地 Session State，讓畫面「秒變」
    st.session_state.main_df = df
    # 2. 背景傳送到 Google 表單
    try:
        df_sorted = df.copy()
        df_sorted['座號_int'] = df_sorted['座號'].astype(int)
        df_sorted = df_sorted.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
        csv_str = df_sorted.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5) # 設定超時避免卡住
        return True
    except:
        return False

# 首次載入
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_from_cloud()

# --- 3. 介面 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd != "alice":
        is_admin = False
    else:
        st.sidebar.success("✅ 已解鎖")

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢 / 修改", "🛠️ 老師管理後台"])

# --- 功能 A：查詢與即時修改 (加速感最強) ---
if menu == "🔍 學生查詢 / 修改":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號 (1-22)：", key="query_sid")
    
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業清單")
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
                            save_to_cloud_and_local(st.session_state.main_df)
                            st.rerun() # 立即重刷本地畫面
                        if c4.button("訂正", key=f"q_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud_and_local(st.session_state.main_df)
                            st.rerun()
            with st.expander("已完成"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

# --- 功能 B：老師管理後台 ---
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請先輸入密碼")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])

        with t1:
            all_hws = st.session_state.main_df["作業名稱"].unique()
            sel_hw = st.selectbox("選擇作業名稱：", all_hws)
            if sel_hw:
                missing = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel_hw) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if missing.empty:
                    st.success("🎉 交齊了")
                else:
                    for idx, r in missing.iterrows():
                        mc1, mc2, mc3 = st.columns([3, 1, 1])
                        mc1.markdown(f"**{r['座號']}. {r['姓名']}** (`{r['繳交狀態']}`)")
                        if mc2.button("已交", key=f"ld_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            save_to_cloud_and_local(st.session_state.main_df)
                            st.rerun()
                        if mc3.button("訂正", key=f"lr_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            save_to_cloud_and_local(st.session_state.main_df)
                            st.rerun()

        with t3:
            hw_n = st.text_input("新作業名稱")
            if hw_n:
                if 'tmp' not in st.session_state or st.session_state.get('lhwn') != hw_n:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = hw_n
                
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    curr = st.session_state.tmp[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']}\n({curr})", key=f"t3_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "已繳交" if curr == "未繳交" else "需訂正" if curr == "已繳交" else "未繳交"
                        st.rerun()
                
                if st.button("🚀 儲存同步", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    updated = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    save_to_cloud_and_local(updated)
                    st.success("儲存成功")
                    st.rerun()

        st.sidebar.divider()
        if st.sidebar.button("🔄 強制刷新雲端資料"):
            st.session_state.main_df = load_from_cloud()
            st.rerun()
