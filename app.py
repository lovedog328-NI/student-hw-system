import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-穩定版", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單
STUDENT_LIST = [
    {"座號": str(i), "姓名": n} for i, n in enumerate([
        "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
        "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言",
        "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
    ], 1)
]

# 姓名對照表
NAME_MAP = {s['座號']: s['姓名'] for s in STUDENT_LIST}

# --- 2. 救援資料庫邏輯 (修正欄位數量不符的問題) ---
def get_internal_backup():
    # 原始資料只有 4 欄
    backup_list = [
        ["4", "L2圈詞", "需訂正", "2026-03-27"], ["6", "L2圈詞", "未繳交", "2026-03-27"],
        ["15", "L2圈詞", "未繳交", "2026-03-27"], ["21", "L2圈詞", "需訂正", "2026-03-27"],
        ["6", "L2生字造詞", "未繳交", "2026-03-27"], ["1", "L3圈詞", "需訂正", "2026-03-27"],
        ["2", "L3圈詞", "未繳交", "2026-03-27"], ["3", "L3圈詞", "未繳交", "2026-03-27"],
        ["4", "L3圈詞", "需訂正", "2026-03-27"], ["6", "L3圈詞", "未繳交", "2026-03-27"],
        ["19", "L3圈詞", "未繳交", "2026-03-27"], ["21", "L3圈詞", "需訂正", "2026-04-01"],
        ["6", "L3國卷", "需訂正", "2026-03-27"], ["14", "L3國卷", "需訂正", "2026-03-27"],
        ["21", "L3國卷", "需訂正", "2026-03-27"], ["21", "L3生字造詞", "需訂正", "2026-03-27"],
        ["1", "乙本p.25", "未繳交", "2026-03-27"], ["4", "乙本p.25", "未繳交", "2026-03-27"],
        ["12", "乙本p.25", "未繳交", "2026-03-27"], ["19", "乙本p.25", "未繳交", "2026-03-27"],
        ["21", "乙本p.25", "未繳交", "2026-03-27"], ["12", "乙本p.9-11", "未繳交", "2026-03-27"],
        ["6", "圈詞L1", "未繳交", "2026-03-27"], ["6", "國乙本p.22-24", "需訂正", "2026-03-27"],
        ["12", "國乙本p.22-24", "需訂正", "2026-03-27"], ["19", "國乙本p.22-24", "未繳交", "2026-03-27"],
        ["21", "國乙本p.22-24", "需訂正", "2026-03-27"], ["21", "國甲p.17.23.24", "需訂正", "2026-03-27"],
        ["1", "國甲p.25.26", "需訂正", "2026-03-27"], ["18", "國甲p.25.26", "需訂正", "2026-03-27"],
        ["21", "國甲p.25.26", "需訂正", "2026-03-27"], ["2", "小日記1", "未繳交", "2026-03-27"],
        ["2", "小日記2", "未繳交", "2026-03-27"], ["6", "小日記2", "未繳交", "2026-03-27"],
        ["14", "小日記2", "需訂正", "2026-03-27"], ["15", "小日記2", "需訂正", "2026-03-27"],
        ["19", "小日記2", "需訂正", "2026-03-27"], ["21", "小日記2", "需訂正", "2026-03-27"],
        ["6", "成語25", "未繳交", "2026-03-27"], ["6", "成語p.26.27", "未繳交", "2026-03-27"],
        ["19", "成語p.26.27", "需訂正", "2026-03-27"], ["6", "成語p28", "未繳交", "2026-03-27"],
        ["1", "成語p29", "需訂正", "2026-04-01"], ["6", "成語p29", "未繳交", "2026-03-27"],
        ["19", "成語p29", "需訂正", "2026-04-01"], ["22", "成語p29", "未繳交", "2026-03-27"],
        ["4", "成語p30", "未繳交", "2026-03-27"], ["6", "成語p30", "未繳交", "2026-03-27"],
        ["22", "成語p30", "未繳交", "2026-03-27"], ["6", "數卷(大)", "需訂正", "2026-03-27"],
        ["19", "數卷(大)", "需訂正", "2026-03-27"], ["14", "數卷1-3", "需訂正", "2026-03-27"],
        ["15", "數卷1-3", "需訂正", "2026-03-27"], ["18", "數卷1-3", "需訂正", "2026-03-27"],
        ["19", "數卷1-3", "需訂正", "2026-03-27"], ["21", "數卷1-3", "需訂正", "2026-03-27"],
        ["1", "數卷2-2", "需訂正", "2026-03-27"], ["3", "數卷2-2", "需訂正", "2026-03-27"],
        ["4", "數卷2-2", "需訂正", "2026-03-27"], ["6", "數卷2-2", "需訂正", "2026-03-27"],
        ["15", "數卷2-2", "需訂正", "2026-03-27"], ["1", "數學2-3", "未繳交", "2026-03-27"],
        ["4", "數學2-3", "需訂正", "2026-03-27"], ["6", "數學2-3", "未繳交", "2026-03-27"],
        ["14", "數學2-3", "需訂正", "2026-03-27"], ["15", "數學2-3", "未繳交", "2026-03-27"],
        ["18", "數學2-3", "需訂正", "2026-03-27"], ["19", "數學2-3", "需訂正", "2026-03-27"],
        ["14", "數習28.29", "需訂正", "2026-03-27"], ["19", "數習28.29", "需訂正", "2026-03-27"],
        ["21", "數習28.29", "需訂正", "2026-03-27"], ["18", "數習p.18.19", "需訂正", "2026-03-27"],
        ["19", "數習p.18.19", "需訂正", "2026-03-27"], ["1", "數習p.34.35", "需訂正", "2026-04-01"],
        ["3", "數習p.34.35", "未繳交", "2026-03-27"], ["12", "數習p.34.35", "未繳交", "2026-03-27"],
        ["18", "數習p.34.35", "需訂正", "2026-03-30"], ["19", "數習p.34.35", "未繳交", "2026-03-27"],
        ["21", "數習p.34.35", "未繳交", "2026-03-27"], ["22", "數習p.34.35", "未繳交", "2026-03-27"],
        ["1", "數課45.46", "未繳交", "2026-03-27"], ["6", "數課p.17.18", "未繳交", "2026-03-27"],
        ["21", "數重p.10", "需訂正", "2026-03-27"], ["22", "數重p.10", "未繳交", "2026-03-27"],
        ["6", "數重p.11", "未繳交", "2026-03-27"], ["18", "數重p.11", "需訂正", "2026-03-27"],
        ["19", "數重p.11", "未繳交", "2026-03-27"], ["21", "數重p.11", "需訂正", "2026-03-27"],
        ["1", "數重p.12.13", "未繳交", "2026-03-27"], ["4", "數重p.12.13", "需訂正", "2026-03-27"],
        ["6", "數重p.12.13", "需訂正", "2026-03-27"], ["15", "數重p.12.13", "需訂正", "2026-03-27"],
        ["19", "數重p.12.13", "未繳交", "2026-03-27"], ["21", "數重p.12.13", "需訂正", "2026-03-27"],
        ["21", "數重p.5", "未繳交", "2026-03-27"], ["22", "數重p.8", "需訂正", "2026-03-27"],
        ["22", "甲本p.20-22", "未繳交", "2026-03-27"], ["14", "3/31聯絡簿", "未繳交", "2026-03-31"],
        ["19", "成語32-33", "需訂正", "2026-04-01"], ["12", "數習38-39", "未繳交", "2026-03-31"],
        ["14", "數習38-39", "未繳交", "2026-03-31"], ["19", "數習38-39", "未繳交", "2026-03-31"],
        ["5", "成語34", "需訂正", "2026-04-01"], ["6", "成語34", "未繳交", "2026-04-01"],
        ["11", "成語34", "需訂正", "2026-04-01"], ["14", "成語34", "未繳交", "2026-04-01"],
        ["1", "數習41", "未繳交", "2026-04-01"], ["5", "數習41", "需訂正", "2026-04-01"],
        ["6", "數習41", "需訂正", "2026-04-01"], ["8", "數習41", "未繳交", "2026-04-01"],
        ["14", "數習41", "未繳交", "2026-04-01"], ["19", "數習41", "未繳交", "2026-04-01"]
    ]
    # 先建立基礎 DataFrame (只有 4 欄)
    base_df = pd.DataFrame(backup_list, columns=["座號", "作業名稱", "繳交狀態", "更新日期"])
    
    # 全班生成邏輯
    new_batch = [
        ("3/31聯絡簿", "未繳交"), ("國語習作P16-17", "需訂正"), ("L4生字造詞", "未繳交"),
        ("L4圈詞", "未繳交"), ("國甲32-34", "未繳交"), ("成語32-33", "未繳交")
    ]
    
    final_rows = []
    
    # 1. 處理基礎欠交資料
    existing_hws = base_df["作業名稱"].unique()
    for hw in existing_hws:
        hw_sub = base_df[base_df["作業名稱"] == hw]
        for s in STUDENT_LIST:
            sid = s['座號']
            match = hw_sub[hw_sub["座號"] == sid]
            if not match.empty:
                # 補齊姓名
                final_rows.append({"座號":sid, "姓名":NAME_MAP[sid], "作業名稱":hw, "繳交狀態":match.iloc[0]["繳交狀態"], "更新日期":match.iloc[0]["更新日期"]})
            else:
                final_rows.append({"座號":sid, "姓名":NAME_MAP[sid], "作業名稱":hw, "繳交狀態":"已繳交", "更新日期":"2026-03-31"})

    # 2. 處理新批次
    for hw_name, default_status in new_batch:
        if hw_name in existing_hws: continue
        for s in STUDENT_LIST:
            sid = s['座號']
            status = default_status
            if hw_name == "L4圈詞" and sid == "21": status = "需訂正"
            final_rows.append({"座號":sid, "姓名":NAME_MAP[sid], "作業名稱":hw_name, "繳交狀態":status, "更新日期":"2026-04-01"})

    return pd.DataFrame(final_rows)

# --- 3. 讀寫邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    rescue_df = get_internal_backup()
    try:
        url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/edit"
        cloud_df = conn.read(spreadsheet=url, worksheet="Sheet1", ttl=0)
        
        # 如果雲端沒資料或欄位不對，啟動救援
        if cloud_df is None or len(cloud_df) < 5 or "座號" not in cloud_df.columns:
            return rescue_df
            
        cloud_df["座號"] = cloud_df["座號"].astype(str)
        return cloud_df
    except:
        return rescue_df

def save_data(df):
    try:
        url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/edit"
        conn.update(spreadsheet=url, worksheet="Sheet1", data=df)
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 4. UI 介面 ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 同步雲端/重置資料"):
    st.session_state.main_df = load_data()
    st.rerun()

menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

def update_status(idx, new_status):
    st.session_state.main_df.at[idx, "繳交狀態"] = new_status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    with st.spinner("同步中..."):
        if save_data(st.session_state.main_df):
            st.toast("✅ 已更新")
            time.sleep(0.5)
            st.rerun()

# [查詢區]
if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的作業狀況")
            unfilled = res[res["繳交狀態"] != "已繳交"]
            if unfilled.empty:
                st.balloons()
                st.success("🎊 太棒了！作業全部交齊囉！")
            else:
                for idx, row in unfilled.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    c2.write(f"`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=update_status, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=update_status, args=(idx, "需訂正"))
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

# [後台區]
elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("請輸入正確密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        with tab1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("全班皆已交齊！")
                for i, r in m.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    cb.button("已交", key=f"t1_d_{i}", on_click=update_status, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t1_r_{i}", on_click=update_status, args=(i, "需訂正"))
        with tab2:
            tsid = st.text_input("輸入座號補交：", key="tsid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"] == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if sm.empty: st.success("目前無欠交。")
                else:
                    st.write(f"正在處理：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ra, rb, rc = st.columns([3, 1, 1])
                        ra.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                        rb.button("已交", key=f"t2_d_{i}", on_click=update_status, args=(i, "已繳交"))
                        rc.button("訂正", key=f"t2_r_{i}", on_click=update_status, args=(i, "需訂正"))
        with tab3:
            st.subheader("新增整班作業")
            nhw = st.text_input("作業名稱：")
            if st.button("🚀 確認發佈 (預設全班未交)"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "更新日期": str(date.today())} for s in STUDENT_LIST]
                new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                if save_data(new_df):
                    st.session_state.main_df = new_df
                    st.success("發佈成功！")
                    st.rerun()

        st.sidebar.divider()
        with st.sidebar.expander("🗑️ 刪除紀錄"):
            target = st.selectbox("選擇刪除項", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("執行刪除") and target != "請選擇":
                new_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
                if save_data(new_df):
                    st.session_state.main_df = new_df
                    st.rerun()
