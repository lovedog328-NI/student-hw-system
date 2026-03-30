import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記-全功能穩定版", layout="wide")

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

# --- 2. 穩定讀寫核心 ---
def load_data_fallback():
    try:
        url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/gviz/tq?tqx=out:csv"
        # 增加時間戳記破解快取，確保讀到最新資料
        r = requests.get(f"{url}&cb={int(time.time())}", timeout=5)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                last_val = df_raw.iloc[-1, -1]
                df = pd.read_csv(io.StringIO(last_val), dtype={'座號': str})
                df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                # 按作業與座號自動排序
                df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                return df.reset_index(drop=True)
    except Exception as e:
        st.sidebar.error(f"連線失敗：{e}")
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_and_sync(df):
    st.session_state.main_df = df
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data_fallback()

# --- 3. 介面設計 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == "alice":
        st.sidebar.success("✅ 已解鎖")
    else:
        is_admin = False

menu = st.sidebar.selectbox("功能選單", ["🔍 查詢與修改", "🛠️ 管理後台"])

# 修改狀態的核心函數
def change_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_and_sync(st.session_state.main_df)

if menu == "🔍 查詢與修改":
    st.header("🔍 學生個人作業查詢")
    sid = st.text_input("輸入座號查詢 (1-22)：")
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
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    c2.write(f"`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=change_status, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=change_status, args=(idx, "需訂正"))
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 管理後台":
    if not is_admin:
        st.warning("請先輸入正確的管理密碼。")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 座號補交", "📝 新增作業"])
        
        with t1:
            st.subheader("📋 缺交名單管理")
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws), key="sel_hw_t1")
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 全班均已繳交！")
                else:
                    for i, r in m.iterrows():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        col1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                        col2.button("已交", key=f"t1_d_{i}", on_click=change_status, args=(i, "已繳交"))
                        col3.button("訂正", key=f"t1_r_{i}", on_click=change_status, args=(i, "需訂正"))
        
        with t2:
            st.subheader("🎯 依座號快速補交")
            tsid = st.text_input("輸入座號：", key="t2_sid_input")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if not sm.empty:
                    st.write(f"學生姓名：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ca, cb, cc = st.columns([3, 1, 1])
                        ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                        cb.button("已交", key=f"t2_d_{i}", on_click=change_status, args=(i, "已繳交"))
                        cc.button("訂正", key=f"t2_r_{i}", on_click=change_status, args=(i, "需訂正"))
                else:
                    st.info("該生目前無欠交紀錄。")

        with t3:
            st.subheader("📝 新增整班作業")
            if 'hw_input' not in st.session_state: st.session_state.hw_input = ""
            hw_n = st.text_input("新作業名稱：", value=st.session_state.hw_input)
            if hw_n:
                if 'tmp' not in st.session_state or st.session_state.get('lhwn') != hw_n:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = hw_n
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']; cur = st.session_state.tmp[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']} ({cur})", key=f"t3_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "已繳交" if cur == "未繳交" else "需訂正" if cur == "已繳交" else "未繳交"
                        st.rerun()
                if st.button("🚀 確認發佈並同步", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    if save_and_sync(new_df):
                        st.session_state.hw_input = ""; st.session_state.lhwn = ""
                        st.success("已成功發佈！")
                        time.sleep(1)
                        st.rerun()

        # --- 🗑️ 刪除功能區 (補回) ---
        st.divider()
        with st.expander("🗑️ 危險區域：刪除錯誤作業紀錄"):
            st.warning("⚠️ 刪除後將無法還原，請謹慎操作。")
            all_hws_list = st.session_state.main_df["作業名稱"].unique()
            target_hw = st.selectbox("請選擇要刪除的作業：", ["請選擇"] + list(all_hws_list), key="del_hw_sel")
            confirm_del = st.checkbox("我確定要永久刪除此作業的所有紀錄")
            
            if st.button("❌ 執行刪除", type="secondary", disabled=not confirm_del):
                if target_hw != "請選擇":
                    updated_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target_hw]
                    if save_and_sync(updated_df):
                        st.success(f"已刪除「{target_hw}」的所有紀錄")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("請先選擇一個作業名稱。")

        if st.sidebar.button("🔄 強制刷新數據"):
            st.session_state.main_df = load_data_fallback()
            st.rerun()
