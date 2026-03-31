import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記系統", layout="wide")
st.title("📚 303 作業登記系統")

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

# --- 2. 救援資料庫 (使用清單格式，避免 CSV 解析錯誤) ---
def get_rescue_data():
    # 這裡放 3/31 所有的欠交/需訂正紀錄
    raw_list = [
        ["1", "3/27聯絡簿", "已繳交", "2026-03-27"],
        ["19", "3/27聯絡簿", "未繳交", "2026-03-27"],
        ["4", "L2圈詞", "需訂正", "2026-03-27"],
        ["6", "L2圈詞", "未繳交", "2026-03-27"],
        ["15", "L2圈詞", "未繳交", "2026-03-27"],
        ["21", "L2圈詞", "需訂正", "2026-03-27"],
        ["6", "L2生字造詞", "未繳交", "2026-03-27"],
        ["1", "L3圈詞", "需訂正", "2026-03-27"],
        ["2", "L3圈詞", "未繳交", "2026-03-27"],
        ["3", "L3圈詞", "未繳交", "2026-03-27"],
        ["4", "L3圈詞", "需訂正", "2026-03-27"],
        ["6", "L3圈詞", "未繳交", "2026-03-27"],
        ["19", "L3圈詞", "未繳交", "2026-03-27"],
        ["21", "L3圈詞", "未繳交", "2026-03-27"],
        ["6", "L3國卷", "需訂正", "2026-03-27"],
        ["14", "L3國卷", "需訂正", "2026-03-27"],
        ["21", "L3國卷", "需訂正", "2026-03-27"],
        ["21", "L3生字造詞", "需訂正", "2026-03-27"],
        ["1", "乙本p.25", "未繳交", "2026-03-27"],
        ["4", "乙本p.25", "未繳交", "2026-03-27"],
        ["12", "乙本p.25", "未繳交", "2026-03-27"],
        ["19", "乙本p.25", "未繳交", "2026-03-27"],
        ["21", "乙本p.25", "未繳交", "2026-03-27"],
        ["12", "乙本p.9-11", "未繳交", "2026-03-27"],
        ["6", "圈詞L1", "未繳交", "2026-03-27"],
        ["1", "國乙本p.22-24", "已繳交", "2026-03-31"],
        ["6", "國乙本p.22-24", "需訂正", "2026-03-27"],
        ["12", "國乙本p.22-24", "需訂正", "2026-03-27"],
        ["19", "國乙本p.22-24", "未繳交", "2026-03-27"],
        ["21", "國乙本p.22-24", "需訂正", "2026-03-27"],
        ["1", "國甲p.17.23.24", "已繳交", "2026-03-31"],
        ["21", "國甲p.17.23.24", "需訂正", "2026-03-27"],
        ["1", "國甲p.25.26", "需訂正", "2026-03-27"],
        ["18", "國甲p.25.26", "需訂正", "2026-03-27"],
        ["21", "國甲p.25.26", "需訂正", "2026-03-27"],
        ["1", "小日記1", "已繳交", "2026-03-31"],
        ["2", "小日記1", "未繳交", "2026-03-27"],
        ["2", "小日記2", "未繳交", "2026-03-27"],
        ["6", "小日記2", "未繳交", "2026-03-27"],
        ["14", "小日記2", "需訂正", "2026-03-27"],
        ["15", "小日記2", "需訂正", "2026-03-27"],
        ["18", "小日記2", "需訂正", "2026-03-27"],
        ["19", "小日記2", "需訂正", "2026-03-27"],
        ["21", "小日記2", "需訂正", "2026-03-27"],
        ["6", "成語25", "未繳交", "2026-03-27"],
        ["1", "成語p.26.27", "未繳交", "2026-03-27"],
        ["6", "成語p.26.27", "未繳交", "2026-03-27"],
        ["19", "成語p.26.27", "需訂正", "2026-03-27"],
        ["1", "成語p28", "未繳交", "2026-03-27"],
        ["6", "成語p28", "未繳交", "2026-03-27"],
        ["19", "成語p28", "未繳交", "2026-03-27"],
        ["1", "成語p29", "未繳交", "2026-03-27"],
        ["6", "成語p29", "未繳交", "2026-03-27"],
        ["19", "成語p29", "未繳交", "2026-03-27"],
        ["22", "成語p29", "未繳交", "2026-03-27"],
        ["1", "成語p30", "未繳交", "2026-03-27"],
        ["4", "成語p30", "未繳交", "2026-03-27"],
        ["6", "成語p30", "未繳交", "2026-03-27"],
        ["19", "成語p30", "未繳交", "2026-03-27"],
        ["21", "成語p30", "未繳交", "2026-03-27"],
        ["22", "成語p30", "未繳交", "2026-03-27"],
        ["6", "數卷(大)", "需訂正", "2026-03-27"],
        ["19", "數卷(大)", "需訂正", "2026-03-27"],
        ["14", "數卷1-3", "需訂正", "2026-03-27"],
        ["15", "數卷1-3", "需訂正", "2026-03-27"],
        ["18", "數卷1-3", "需訂正", "2026-03-27"],
        ["19", "數卷1-3", "需訂正", "2026-03-27"],
        ["21", "數卷1-3", "需訂正", "2026-03-27"],
        ["1", "數卷2-2", "需訂正", "2026-03-27"],
        ["3", "數卷2-2", "需訂正", "2026-03-27"],
        ["4", "數卷2-2", "需訂正", "2026-03-27"],
        ["6", "數卷2-2", "需訂正", "2026-03-27"],
        ["15", "數卷2-2", "需訂正", "2026-03-27"],
        ["1", "數學2-3", "未繳交", "2026-03-27"],
        ["4", "數學2-3", "需訂正", "2026-03-27"],
        ["6", "數學2-3", "未繳交", "2026-03-27"],
        ["14", "數學2-3", "需訂正", "2026-03-27"],
        ["15", "數學2-3", "未繳交", "2026-03-27"],
        ["18", "數學2-3", "需訂正", "2026-03-27"],
        ["19", "數學2-3", "需訂正", "2026-03-27"],
        ["14", "數習28.29", "需訂正", "2026-03-27"],
        ["19", "數習28.29", "需訂正", "2026-03-27"],
        ["21", "數習28.29", "需訂正", "2026-03-27"],
        ["18", "數習p.18.19", "需訂正", "2026-03-27"],
        ["19", "數習p.18.19", "需訂正", "2026-03-27"],
        ["22", "數習p.25", "未繳交", "2026-03-27"],
        ["1", "數習p.34.35", "未繳交", "2026-03-27"],
        ["2", "數習p.34.35", "已繳交", "2026-03-31"],
        ["3", "數習p.34.35", "未繳交", "2026-03-27"],
        ["4", "數習p.34.35", "未繳交", "2026-03-27"],
        ["6", "數習p.34.35", "未繳交", "2026-03-27"],
        ["8", "數習p.34.35", "已繳交", "2026-03-31"],
        ["12", "數習p.34.35", "未繳交", "2026-03-27"],
        ["14", "數習p.34.35", "已繳交", "2026-03-31"],
        ["18", "數習p.34.35", "需訂正", "2026-03-30"],
        ["19", "數習p.34.35", "未繳交", "2026-03-27"],
        ["21", "數習p.34.35", "未繳交", "2026-03-27"],
        ["22", "數習p.34.35", "未繳交", "2026-03-27"],
        ["1", "數課45.46", "未繳交", "2026-03-27"],
        ["6", "數課p.17.18", "未繳交", "2026-03-27"],
        ["21", "數重p.10", "需訂正", "2026-03-27"],
        ["22", "數重p.10", "未繳交", "2026-03-27"],
        ["6", "數重p.11", "未繳交", "2026-03-27"],
        ["18", "數重p.11", "需訂正", "2026-03-27"],
        ["19", "數重p.11", "未繳交", "2026-03-27"],
        ["21", "數重p.11", "需訂正", "2026-03-27"],
        ["1", "數重p.12.13", "未繳交", "2026-03-27"],
        ["4", "數重p.12.13", "需訂正", "2026-03-27"],
        ["6", "數重p.12.13", "需訂正", "2026-03-27"],
        ["15", "數重p.12.13", "需訂正", "2026-03-27"],
        ["19", "數重p.12.13", "未繳交", "2026-03-27"],
        ["21", "數重p.12.13", "需訂正", "2026-03-27"],
        ["21", "數重p.5", "未繳交", "2026-03-27"],
        ["22", "數重p.8", "需訂正", "2026-03-27"],
        ["22", "甲本p.20-22", "未繳交", "2026-03-27"],
        ["12", "國語習作P16-17", "未繳交", "2026-03-31"],
        ["11", "國甲32-34", "已繳交", "2026-03-31"],
        ["11", "成語32-33", "已繳交", "2026-03-31"]
    ]
    # 將有提到的轉為 DataFrame
    df_h = pd.DataFrame(raw_list, columns=["座號", "作業名稱", "繳交狀態", "更新日期"])
    
    # 建立完整名單 (處理那些「全班未交」或「全班需訂正」的 3/31 新作業)
    new_hws = [
        ("3/31聯絡簿", "未繳交"),
        ("國語習作P16-17", "需訂正"),
        ("L4生字造詞", "未繳交"),
        ("L4圈詞", "未繳交"),
        ("國甲32-34", "未繳交"),
        ("成語32-33", "未繳交"),
        ("數習38-39", "未繳交")
    ]
    
    # 3/31 數習 38-39 特殊名單 (已繳交的人)
    math_done = ["3","4","5","6","8","9","10","11","13","15","16","17","20","21","22"]
    
    final_rows = []
    name_map = {s['座號']: s['姓名'] for s in STUDENT_LIST}
    
    # 先處理舊的歷史資料中所有出現過的作業
    for hw in df_h["作業名稱"].unique():
        sub = df_h[df_h["作業名稱"] == hw]
        for s in STUDENT_LIST:
            sid = s['座號']
            match = sub[sub["座號"] == sid]
            if not match.empty:
                final_rows.append({"座號":sid, "姓名":name_map[sid], "作業名稱":hw, "繳交狀態":match.iloc[0]["繳交狀態"], "更新日期":match.iloc[0]["更新日期"]})
            else:
                # 歷史資料沒提到，且不是 3/31 的新作業，預設為已繳交
                if hw not in [n[0] for n in new_hws]:
                    final_rows.append({"座號":sid, "姓名":name_map[sid], "作業名稱":hw, "繳交狀態":"已繳交", "更新日期":"2026-03-30"})

    # 處理 3/31 的新作業
    for hw_name, default_status in new_hws:
        # 如果剛才歷史資料已經處理過這項作業了，就跳過
        if any(r['作業名稱'] == hw_name for r in final_rows):
            continue
            
        for s in STUDENT_LIST:
            sid = s['座號']
            status = default_status
            
            # 特殊邏輯：數習 38-39
            if hw_name == "數習38-39" and sid in math_done: status = "已繳交"
            # 特殊邏輯：L4 圈詞 1號已交
            if hw_name == "L4 圈詞" and sid == "1": status = "已繳交"
            
            final_rows.append({"座號":sid, "姓名":name_map[sid], "作業名稱":hw_name, "繳交狀態":status, "更新日期":"2026-03-31"})

    return pd.DataFrame(final_rows)

# --- 3. 核心資料邏輯 ---
def load_latest_data():
    try:
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&t={int(time.time())}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                for i in range(len(df_raw)-1, -1, -1):
                    content = str(df_raw.iloc[i, -1])
                    if "座號" in content and "作業名稱" in content:
                        df = pd.read_csv(io.StringIO(content), dtype={'座號': str})
                        df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                        return df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int']).reset_index(drop=True)
    except:
        pass
    return get_rescue_data()

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
    st.session_state.main_df = load_latest_data()

# --- 4. 介面與控制 ---
st.sidebar.title("⚙️ 系統選單")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")
menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🔐 老師後台"])

if st.sidebar.button("🔄 同步雲端資料"):
    st.session_state.main_df = load_latest_data()
    st.rerun()

def on_status_change(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_and_sync(st.session_state.main_df)

# --- 5. 介面實作 ---

if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的作業狀況")
            unfilled = res[res["繳交狀態"] != "已繳交"]
            if unfilled.empty:
                st.balloons()
                st.success(f"🎊 恭喜 {name}！目前所有作業皆已交齊，太棒了！")
            else:
                st.error("以下項目尚未完成：")
                for idx, row in unfilled.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=on_status_change, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=on_status_change, args=(idx, "需訂正"))
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🔐 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入老師密碼。")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 此項目全班已交齊！")
                else:
                    for i, r in m.iterrows():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        col1.write(f"**{r['座號']}. {r['姓名']}** ({r['繳交狀態']})")
                        col2.button("已交", key=f"t1_d_{i}", on_click=on_status_change, args=(i, "已繳交"))
                        col3.button("訂正", key=f"t1_r_{i}", on_click=on_status_change, args=(i, "需訂正"))

        with t2:
            tsid = st.text_input("輸入座號補交：", key="tsid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if sm.empty: st.success("該生目前無欠交項目。")
                else:
                    st.write(f"正在處理：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ca, cb, cc = st.columns([3, 1, 1])
                        ca.write(f"📌 {r['作業名稱']} ({r['繳交狀態']})")
                        cb.button("已交", key=f"t2_d_{i}", on_click=on_status_change, args=(i, "已繳交"))
                        cc.button("訂正", key=f"t2_r_{i}", on_click=on_status_change, args=(i, "需訂正"))

        with t3:
            st.subheader("新增整班作業")
            new_hw = st.text_input("新作業名稱 (預設未繳交)：")
            if new_hw:
                if 'tmp' not in st.session_state or st.session_state.get('lhwn') != new_hw:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = new_hw
                cols = st.columns(4)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']; cur = st.session_state.tmp[sid]
                    if cols[i%4].button(f"{sid}.{s['姓名']}\n({cur})", key=f"t3_{sid}", type="secondary" if cur=="未繳交" else "primary"):
                        if cur == "未繳交": st.session_state.tmp[sid] = "已繳交"
                        elif cur == "已繳交": st.session_state.tmp[sid] = "需訂正"
                        else: st.session_state.tmp[sid] = "未繳交"
                        st.rerun()
                if st.button("🚀 確認發佈", type="primary", use_container_width=True):
                    rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":new_hw, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    save_and_sync(pd.concat([st.session_state.main_df, pd.DataFrame(rows)], ignore_index=True))
                    st.success("發佈成功！"); time.sleep(1); st.rerun()

        st.sidebar.divider()
        if is_admin and not st.session_state.main_df.empty:
            with st.sidebar.expander("🗑️ 刪除紀錄"):
                target = st.selectbox("刪除作業項目", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
                if st.button("❌ 執行刪除") and target != "請選擇":
                    save_and_sync(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target])
                    st.rerun()
