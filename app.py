import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記-防錯強化版", layout="wide")

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

# --- 2. 核心邏輯：穩健讀寫 ---
def load_data():
    try:
        base_url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv"
        full_url = f"{base_url}&cachebust={int(time.time())}"
        r = requests.get(full_url, timeout=5)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                # 從最後一列往前找，直到找到包含「座號」字眼的正確資料
                for i in range(len(df_raw)-1, -1, -1):
                    last_cell = str(df_raw.iloc[i, -1])
                    if "座號" in last_cell and "姓名" in last_cell:
                        df = pd.read_csv(io.StringIO(last_cell), dtype={'座號': str})
                        # 確保必要的欄位都存在
                        if all(col in df.columns for col in ["座號", "作業名稱", "繳交狀態"]):
                            df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                            df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                            return df.reset_index(drop=True)
    except Exception as e:
        st.sidebar.error(f"讀取異常: {e}")
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

menu = st.sidebar.selectbox("切換功能", ["🔍 查詢與修改", "🛠️ 管理後台"])

# 狀態更新函式
def update_item(idx, status):
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
                st.success("✨ 作業全部交齊囉！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    c2.write(f"`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=update_item, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=update_item, args=(idx, "需訂正"))
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])
        else:
            st.info("尚無該座號的登記資料。")

elif menu == "🛠️ 管理後台":
    if not is_admin:
        st.warning("請在側邊欄輸入密碼。")
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
                    col2.button("已交", key=f"t1_d_{i}", on_click=update_item, args=(i, "已繳交"))
                    col3.button("訂正", key=f"t1_r_{i}", on_click=update_item, args=(i, "需訂正"))
        
        with t2:
            tsid = st.text_input("輸入座號補交：", key="t2_sid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in sm.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                    cb.button("已交", key=f"t2_d_{i}", on_click=update_item, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t2_r_{i}", on_click=update_item, args=(i, "需訂正"))

        with t3:
            if 'hw_name' not in st.session_state: st.session_state.hw_name = ""
            hw_n = st.text_input("新作業名稱：", value=st.session_state.hw_name)
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
                    new_rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    full_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    save_and_sync(full_df)
                    st.session_state.hw_name = ""; st.session_state.lhwn = ""
                    st.success("發佈成功！")
                    time.sleep(1)
                    st.rerun()

        st.divider()
        with st.expander("🗑️ 刪除紀錄"):
            target = st.selectbox("選擇要刪除的作業：", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("❌ 執行刪除") and target != "請選擇":
                save_and_sync(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target])
                st.rerun()

        if st.sidebar.button("🔄 強制刷新"):
            st.session_state.main_df = load_data()
            st.rerun()
