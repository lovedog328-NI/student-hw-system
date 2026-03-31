import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

# --- A. 系統基礎設定 ---
st.set_page_config(page_title="303作業登記系統", layout="wide", initial_sidebar_state="expanded")

# 固定學生名單
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

# --- B. 資料同步核心 ---
def load_latest_data():
    """從雲端讀取最後一筆紀錄，若失敗則載入初始歷史資料"""
    try:
        # 使用 export 網址並加上隨機參數破解不同設備的快取
        base_url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv"
        full_url = f"{base_url}&cachebust={int(time.time())}"
        r = requests.get(full_url, timeout=5)
        
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                # 倒序找尋最後一個有效的內容
                for i in range(len(df_raw)-1, -1, -1):
                    content = str(df_raw.iloc[i, -1])
                    if "座號" in content:
                        df = pd.read_csv(io.StringIO(content), dtype={'座號': str})
                        # 確保座號排序正確 (數字排序)
                        df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                        df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                        return df.reset_index(drop=True)
    except:
        pass
    
    # 若雲端無資料，回傳空表
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_and_sync(df):
    """將資料存入 Session 並同步推送到 Google Form"""
    st.session_state.main_df = df
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

# 初始化載入
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_latest_data()

# --- C. 側邊欄控制 ---
st.sidebar.title("🛠️ 系統選單")
menu = st.sidebar.radio("切換身份", ["🔍 學生查詢區", "🔐 老師管理後台"])

st.sidebar.divider()
st.sidebar.info("💡 不同設備若沒看到更新，請點下方按鈕：")
if st.sidebar.button("🔄 強制刷新雲端數據"):
    st.session_state.main_df = load_latest_data()
    st.rerun()

# 老師密碼驗證
is_admin = False
if menu == "🔐 老師管理後台":
    pwd = st.sidebar.text_input("輸入管理密碼", type="password")
    if pwd == "alice":
        is_admin = True
        st.sidebar.success("管理員已解鎖")
    elif pwd != "":
        st.sidebar.error("密碼錯誤")

# --- D. 主要介面邏輯 ---

# 通用更新函式
def update_item(idx, new_status):
    st.session_state.main_df.at[idx, "繳交狀態"] = new_status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_and_sync(st.session_state.main_df)

# [介面 1：學生查詢區]
if menu == "🔍 學生查詢區":
    st.header("🔍 個人欠交作業查詢")
    search_sid = st.text_input("請輸入座號 (1-22)：", placeholder="例如：1")
    
    if search_sid:
        df = st.session_state.main_df
        if df.empty:
            st.warning("目前雲端尚無作業登記紀錄。")
        else:
            personal_df = df[df["座號"].astype(str) == str(search_sid)]
            if personal_df.empty:
                st.info(f"座號 {search_sid} 目前無任何登記紀錄。")
            else:
                student_name = personal_df.iloc[0]['姓名']
                st.subheader(f"👤 學生姓名：{student_name}")
                
                # 篩選未完成項目
                unfilled = personal_df[personal_df["繳交狀態"] != "已繳交"]
                
                if unfilled.empty:
                    st.balloons()
                    st.success(f"🎊 恭喜 {student_name}！你目前沒有任何缺交或需訂正的作業，太棒了！")
                else:
                    st.error("🚩 以下是尚未完成的項目：")
                    for idx, row in unfilled.iterrows():
                        with st.container():
                            col_a, col_b = st.columns([4, 1])
                            col_a.write(f"📌 **{row['作業名稱']}**")
                            col_b.write(f"狀態：`{row['繳交狀態']}`")
                            st.divider()
                
                with st.expander("查看已完成作業清單"):
                    done = personal_df[personal_df["繳交狀態"] == "已繳交"]
                    if not done.empty:
                        st.table(done[["作業名稱", "更新日期"]])

# [介面 2：老師管理後台]
elif menu == "🔐 老師管理後台":
    if not is_admin:
        st.warning("⚠️ 此區域僅限老師存取，請在左側輸入密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交總覽", "🎯 快速補交", "📝 新增作業"])
        
        with tab1:
            st.subheader("📋 班級缺交狀況總覽")
            if st.session_state.main_df.empty:
                st.info("目前無資料")
            else:
                all_hws = st.session_state.main_df["作業名稱"].unique()
                sel_hw = st.selectbox("請選擇作業項目：", ["全部顯示"] + list(all_hws))
                
                display_df = st.session_state.main_df
                if sel_hw != "全部顯示":
                    display_df = display_df[display_df["作業名稱"] == sel_hw]
                
                missing = display_df[display_df["繳交狀態"] != "已繳交"]
                if missing.empty:
                    st.success("🎉 太棒了！此項目全班皆已完成。")
                else:
                    st.dataframe(missing[["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"]], use_container_width=True)

        with tab2:
            st.subheader("🎯 依座號快速處理補交")
            t2_sid = st.text_input("輸入座號：", key="t2_sid")
            if t2_sid:
                t2_df = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(t2_sid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if t2_df.empty:
                    st.success("該生目前沒有欠交作業！")
                else:
                    st.write(f"正在處理：**{t2_df.iloc[0]['姓名']}**")
                    for idx, row in t2_df.iterrows():
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"📌 {row['作業名稱']} (`{row['繳交狀態']}`)")
                        if c2.button("✅ 改為已交", key=f"done_{idx}"):
                            update_item(idx, "已繳交")
                            st.rerun()
                        if c3.button("✏️ 需訂正", key=f"fix_{idx}"):
                            update_item(idx, "需訂正")
                            st.rerun()

        with tab3:
            st.subheader("📝 新增整班作業登記")
            new_hw_name = st.text_input("輸入新作業名稱 (例如：數習 p.36)：")
            if new_hw_name:
                st.write("請點選目前『未繳交』的學生 (預設全班已交)：")
                # 建立暫存狀態
                if 'new_hw_status' not in st.session_state or st.session_state.get('current_hw') != new_hw_name:
                    st.session_state.new_hw_status = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.current_hw = new_hw_name
                
                cols = st.columns(4)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座号']
                    current_s = st.session_state.new_hw_status[sid]
                    btn_label = f"{sid}. {s['姓名']}\n({current_s})"
                    if cols[i % 4].button(btn_label, key=f"btn_{sid}", type="secondary" if current_s=="已繳交" else "primary"):
                        st.session_state.new_hw_status[sid] = "未繳交" if current_s == "已繳交" else "已繳交"
                        st.rerun()
                
                if st.button("🚀 確認發佈作業", type="primary", use_container_width=True):
                    new_entries = []
                    for s in STUDENT_LIST:
                        new_entries.append({
                            "座號": s['座號'],
                            "姓名": s['姓名'],
                            "作業名稱": new_hw_name,
                            "繳交狀態": st.session_state.new_hw_status[s['座號']],
                            "更新日期": str(date.today())
                        })
                    
                    combined_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_entries)], ignore_index=True)
                    if save_and_sync(combined_df):
                        st.success(f"✅ {new_hw_name} 登記成功！")
                        time.sleep(1)
                        st.rerun()

        st.sidebar.divider()
        with st.sidebar.expander("🗑️ 危險區域"):
            if is_admin and not st.session_state.main_df.empty:
                hw_to_del = st.selectbox("選擇要刪除的作業項目", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
                if st.button("❌ 永久刪除該項紀錄"):
                    if hw_to_del != "請選擇":
                        new_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != hw_to_del]
                        save_and_sync(new_df)
                        st.rerun()
