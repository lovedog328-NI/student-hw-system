import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-專業版", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate(["王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙", "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言", "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"], 1)]
NAME_MAP = {s['座號']: s['姓名'] for s in STUDENT_LIST}

# --- 2. 救援資料庫邏輯 ---
def get_rescue_df():
    backup_data = [
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
        ["6", "成語25", "未繳交", "2026-03-27"], ["1", "成語p29", "需訂正", "2026-04-01"],
        ["19", "成語p29", "需訂正", "2026-04-01"], ["18", "數習p.34.35", "需訂正", "2026-03-30"],
        ["19", "成語32-33", "需訂正", "2026-04-01"], ["5", "成語34", "需訂正", "2026-04-01"],
        ["11", "成語34", "需訂正", "2026-04-01"], ["5", "數習41", "需訂正", "2026-04-01"],
        ["6", "數習41", "需訂正", "2026-04-01"]
    ]
    base_df = pd.DataFrame(backup_data, columns=["座號", "作業名稱", "繳交狀態", "更新日期"])
    new_hws = [("3/31聯絡簿", "未繳交"), ("國語習作P16-17", "需訂正"), ("L4生字造詞", "未繳交"), ("L4圈詞", "未繳交"), ("國甲32-34", "未繳交"), ("成語32-33", "未繳交"), ("數習38-39", "未繳交"), ("成語34", "未繳交"), ("數習41", "未繳交")]
    
    final_rows = []
    existing_hws = base_df["作業名稱"].unique().tolist()
    for nhw, _ in new_hws:
        if nhw not in existing_hws: existing_hws.append(nhw)

    for hw in existing_hws:
        hw_sub = base_df[base_df["作業名稱"] == hw]
        for s in STUDENT_LIST:
            sid = s['座號']
            match = hw_sub[hw_sub["座號"] == sid]
            if not match.empty:
                final_rows.append({"座號":sid, "姓名":NAME_MAP[sid], "作業名稱":hw, "繳交狀態":match.iloc[0]["繳交狀態"], "更新日期":match.iloc[0]["更新日期"]})
            else:
                status = "已繳交"
                for nhw, nstatus in new_hws:
                    if hw == nhw: status = nstatus
                final_rows.append({"座號":sid, "姓名":NAME_MAP[sid], "作業名稱":hw, "繳交狀態":status, "更新日期":"2026-04-01"})
    return pd.DataFrame(final_rows)

# --- 3. 讀寫邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    rescue_df = get_rescue_df()
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty or len(df) < 5:
            return rescue_df
        df["座號"] = pd.to_numeric(df["座號"], errors='coerce').fillna(0).astype(int).astype(str)
        df = df[df["座號"] != "0"]
        return df
    except:
        return rescue_df

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        return True
    except Exception as e:
        st.error(f"雲端儲存失敗: {e}")
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 4. UI ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 同步雲端/恢復初始資料"):
    st.session_state.main_df = load_data()
    st.rerun()

menu = st.sidebar.radio("功能", ["🔍 學生查詢", "🛠️ 老師後台"])

def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    with st.spinner("同步雲端中..."):
        save_data(st.session_state.main_df)
    st.toast(f"✅ 已更新狀態為：{status}")

# --- 5. 介面實作 ---
if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業狀況")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success("🎊 全部交齊囉！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    # 根據狀態顯示不同顏色
                    state_color = "red" if row['繳交狀態'] == "未繳交" else "orange"
                    c2.markdown(f":{state_color}[**{row['繳交狀態']}**]")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=update_status, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=update_status, args=(idx, "需訂正"))
            with st.expander("已完成紀錄"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("請輸入密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        with tab1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 此項作業已全班交齊！")
                for i, r in m.iterrows():
                    ca, cb, cc, cd = st.columns([2, 1.5, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    # ✨ 這裡加入了狀態顯示
                    state_color = "red" if r['繳交狀態'] == "未繳交" else "orange"
                    cb.markdown(f"目前狀態：:{state_color}[**{r['繳交狀態']}**]")
                    cb.caption(f"最後更新：{r['更新日期']}")
                    cd.button("已交", key=f"t1_d_{i}", on_click=update_status, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t1_r_{i}", on_click=update_status, args=(i, "需訂正"))
        with tab2:
            tsid = st.text_input("座號快速補交：")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"] == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if sm.empty: st.success("該生目前無欠交。")
                else:
                    st.write(f"正在處理：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ra, rb, rc, rd = st.columns([3, 2, 1, 1])
                        ra.write(f"📌 {r['作業名稱']}")
                        # ✨ 這裡也加入了狀態顯示
                        state_color = "red" if r['繳交狀態'] == "未繳交" else "orange"
                        rb.markdown(f":{state_color}[**{r['繳交狀態']}**]")
                        rd.button("已交", key=f"t2_d_{i}", on_click=update_status, args=(i, "已繳交"))
                        rc.button("訂正", key=f"t2_r_{i}", on_click=update_status, args=(i, "需訂正"))
        with tab3:
            nhw = st.text_input("新增作業名稱：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "更新日期": str(date.today())} for s in STUDENT_LIST]
                new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                if save_data(new_df):
                    st.session_state.main_df = new_df
                    st.success("發佈成功！"); st.rerun()

        st.sidebar.divider()
        if st.sidebar.button("🗑️ 刪除這項作業紀錄"):
            target = st.selectbox("選取要刪除的作業", list(st.session_state.main_df["作業名稱"].unique()))
            if save_data(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]):
                st.rerun()
