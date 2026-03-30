import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記-穩定救援版", layout="wide")

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

# --- 2. 穩定讀寫邏輯 ---
def load_data_fallback():
    try:
        # 直接使用 gviz 接口，這比 API 穩定且不需要權限
        url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/gviz/tq?tqx=out:csv"
        # 加上隨機數破解 Google 緩存
        r = requests.get(f"{url}&cb={int(time.time())}", timeout=5)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                # 抓取最後一列的 JSON 資料
                last_val = df_raw.iloc[-1, -1]
                df = pd.read_csv(io.StringIO(last_val), dtype={'座號': str})
                # 排序
                df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"連線失敗：{e}")
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

# 修改狀態的函數
def change_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_and_sync(st.session_state.main_df)

if menu == "🔍 查詢與修改":
    sid = st.text_input("座號 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業")
            for idx, row in res[res["繳交狀態"] != "已繳交"].iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(f"📌 {row['作業名稱']}")
                c2.write(f"`{row['繳交狀態']}`")
                if is_admin:
                    c3.button("已交", key=f"q_d_{idx}", on_click=change_status, args=(idx, "已繳交"))
                    c4.button("訂正", key=f"q_r_{idx}", on_click=change_status, args=(idx, "需訂正"))
            with st.expander("已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 管理後台":
    if not is_admin:
        st.warning("請先登入")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 座號補交", "📝 新增作業"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in m.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                    col2.button("已交", key=f"t1_d_{i}", on_click=change_status, args=(i, "已繳交"))
                    col3.button("訂正", key=f"t1_r_{i}", on_click=change_status, args=(i, "需訂正"))
        
        with t2:
            tsid = st.text_input("輸入座號補交：")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in sm.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                    cb.button("已交", key=f"t2_d_{i}", on_click=change_status, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t2_r_{i}", on_click=change_status, args=(i, "需訂正"))

        with t3:
            hw_n = st.text_input("新作業名稱：")
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
                if st.button("🚀 確認發佈", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    save_and_sync(new_df)
                    st.success("已同步至雲端！")
                    time.sleep(1)
                    st.rerun()

        st.sidebar.divider()
        if st.sidebar.button("🔄 強制刷新數據"):
            st.session_state.main_df = load_data_fallback()
            st.rerun()
