import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記系統", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單 (確保 key 是 '座號')
STUDENT_LIST = [
    {"座號": "1", "姓名": "王瑀淮"}, {"座號": "2", "姓名": "李祐嘉"}, {"座號": "3", "姓名": "郭晁瑋"},
    {"座號": "4", "姓名": "廖勇傑"}, {"座號": "5", "姓名": "潘彥廷"}, {"座號": "6", "姓名": "郭家宇"},
    {"座號": "7", "姓名": "王悅芯"}, {"座號": "8", "姓名": "劉橙"}, {"座號": "9", "姓名": "洪語緹"},
    {"座號": "10", "姓名": "林祈平"}, {"座號": "11", "姓名": "鄧安晴"}, {"座號": "12", "姓名": "蔣語桐"},
    {"座號": "13", "姓名": "邱薇瑀"}, {"座號": "14", "姓名": "鍾芮昕"}, {"座號": "15", "姓名": "詹筠蓁"},
    {"座號": "16", "姓名": "劉姝言"}, {"座號": "17", "姓名": "范庭蓁"}, {"座號": "18", "姓名": "呂佳恩"},
    {"座號": "19", "姓名": "楊晨妤"}, {"座號": "20", "姓名": "劉芮安"}, {"座號": "21", "姓名": "蔡芊芊"},
    {"座號": "22", "姓名": "王楷晴"}
]

# --- 2. 核心讀取與同步邏輯 ---
def load_latest_data():
    """從雲端讀取最後一筆紀錄，並增加 cache busting 確保跨設備同步"""
    try:
        # 加上隨機參數防止不同手機抓到舊快取
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&cb={int(time.time())}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                # 由下往上掃描最後一格
                for i in range(len(df_raw)-1, -1, -1):
                    content = str(df_raw.iloc[i, -1])
                    if "座號" in content:
                        df = pd.read_csv(io.StringIO(content), dtype={'座號': str})
                        # 補齊姓名
                        name_map = {s['座號']: s['姓名'] for s in STUDENT_LIST}
                        df['姓名'] = df['座號'].map(name_map)
                        # 排序
                        df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                        df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                        return df.reset_index(drop=True)
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_and_sync(df):
    """更新 UI 並發送到雲端"""
    st.session_state.main_df = df
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

# 初始化資料
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_latest_data()

# --- 3. 介面選單 ---
st.sidebar.title("🛠️ 選單")
menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🔐 老師後台"])

# 密碼解鎖邏輯
is_admin = False
pwd = st.sidebar.text_input("老師管理密碼", type="password")
if pwd == "alice":
    is_admin = True
    st.sidebar.success("✅ 管理權限已解鎖")

if st.sidebar.button("🔄 刷新雲端資料"):
    st.session_state.main_df = load_latest_data()
    st.rerun()

# 更新狀態回呼
def on_update(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_and_sync(st.session_state.main_df)

# --- 4. 功能實作 ---

if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if res.empty:
            st.info("目前沒有你的登記紀錄。")
        else:
            name = res.iloc[0]['姓名']
            todo = res[res["繳交狀態"] != "已繳交"]
            
            if todo.empty:
                st.balloons()
                st.success(f"🎊 恭喜 {name}！你目前沒有任何缺交或需訂正的作業，太棒了！")
            else:
                st.error(f"👤 {name}，你還有以下項目需要處理：")
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=on_update, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=on_update, args=(idx, "需訂正"))
            
            with st.expander("查看已完成紀錄"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🔐 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入正確密碼以進入後台。")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業項目", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 此項作業已全班交齊！")
                else:
                    for i, r in m.iterrows():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        col1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                        col2.button("已交", key=f"t1_d_{i}", on_click=on_update, args=(i, "已繳交"))
                        col3.button("訂正", key=f"t1_r_{i}", on_click=on_update, args=(i, "需訂正"))
        
        with t2:
            tsid = st.text_input("輸入座號快速補交：", key="tsid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if sm.empty: st.success("該生目前無欠交。")
                else:
                    st.write(f"正在處理：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ca, cb, cc = st.columns([3, 1, 1])
                        ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                        cb.button("已交", key=f"t2_d_{i}", on_click=on_update, args=(i, "已繳交"))
                        cc.button("訂正", key=f"t2_r_{i}", on_click=on_update, args=(i, "需訂正"))

        with t3:
            st.subheader("新增整班作業")
            new_hw = st.text_input("新作業名稱 (例如: 數習 p.40)：")
            if new_hw:
                if 'tmp_status' not in st.session_state or st.session_state.get('last_hw') != new_hw:
                    st.session_state.tmp_status = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw = new_hw
                
                st.write("請點選「未繳交」的學生：")
                cols = st.columns(4)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    cur = st.session_state.tmp_status[sid]
                    if cols[i%4].button(f"{sid}.{s['姓名']}\n({cur})", key=f"btn_{sid}", type="primary" if cur=="未繳交" else "secondary"):
                        st.session_state.tmp_status[sid] = "未繳交" if cur == "已繳交" else "已繳交"
                        st.rerun()
                
                if st.button("🚀 確認發佈作業", type="primary", use_container_width=True):
                    new_rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":new_hw, "繳交狀態":st.session_state.tmp_status[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    if save_and_sync(new_df):
                        st.success("登記成功！")
                        time.sleep(1)
                        st.rerun()

        st.sidebar.divider()
        if is_admin and not st.session_state.main_df.empty:
            with st.sidebar.expander("🗑️ 刪除紀錄"):
                target = st.selectbox("刪除作業項目", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
                if st.button("執行刪除") and target != "請選擇":
                    save_and_sync(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target])
                    st.rerun()
