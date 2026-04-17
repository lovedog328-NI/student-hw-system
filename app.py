import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-座號快填版", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

# --- 2. 核心資料邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        if df is None or df.empty:
            return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])
        df["座號"] = pd.to_numeric(df["座號"], errors='coerce').fillna(0).astype(int).astype(str)
        df = df[df["座號"] != "0"]
        for s in STUDENT_LIST:
            df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])

def save_data(df):
    try:
        df = df.fillna("")
        conn.update(worksheet="Sheet1", data=df)
        return True
    except: return False

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. 局部更新元件 ---
@st.fragment
def status_buttons(idx, row_key, show_score=False):
    if show_score:
        c_status, c_score, c_edit, c_done = st.columns([1.2, 1, 1, 1])
    else:
        c_status, c_edit, c_done = st.columns([1.5, 1, 1])
    
    current_status = st.session_state.main_df.at[idx, "繳交狀態"]
    st_color = "red" if current_status == "需訂正" else ("orange" if current_status == "未繳交" else "green")
    c_status.markdown(f":{st_color}[**{current_status}**]")
    
    if show_score:
        raw_val = st.session_state.main_df.at[idx, "成績"]
        current_score = str(raw_val) if pd.notna(raw_val) and str(raw_val).strip() != "" else ""
        new_score = c_score.text_input("成績", value=current_score, key=f"score_{row_key}_{idx}", label_visibility="collapsed", placeholder="成績")
        if new_score != current_score:
            st.session_state.main_df.at[idx, "成績"] = new_score
            save_data(st.session_state.main_df)

    if c_edit.button("訂正", key=f"btn_r_{row_key}_{idx}"):
        st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
        st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
        save_data(st.session_state.main_df)
        st.rerun(scope="fragment")

    if c_done.button("已交", key=f"btn_d_{row_key}_{idx}"):
        st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
        st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
        save_data(st.session_state.main_df)
        st.rerun(scope="fragment")

# --- 4. UI 介面 ---
st.sidebar.title("⚙️ 管理選單")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 同步最新雲端資料"):
    st.session_state.main_df = load_data()
    st.rerun()

menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

# [學生查詢]
if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的待辦作業")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success(f"🎊 太棒了，{name}！目前沒有欠作業喔！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3 = st.columns([3, 2, 2])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    s_color = "red" if row['繳交狀態'] == "需訂正" else "orange"
                    c2.markdown(f":{s_color}[{row['繳交狀態']}]")
                    c3.caption(f"登記：{row['更新日期']}")

# [老師後台]
elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入正確密碼。")
    else:
        all_df = st.session_state.main_df
        all_hws = all_df["作業名稱"].unique()
        
        # 側邊欄清理區 (維持上一版邏輯)
        st.sidebar.divider()
        st.sidebar.subheader("🗑️ 快速清理")
        no_score_hws, has_score_hws = [], []
        for hw in all_hws:
            hw_data = all_df[all_df["作業名稱"] == hw]
            if len(hw_data[hw_data["繳交狀態"] != "已繳交"]) == 0:
                if hw_data[hw_data["成績"].apply(lambda x: str(x).strip() != "")].shape[0] > 0: has_score_hws.append(hw)
                else: no_score_hws.append(hw)
        if no_score_hws:
            if st.sidebar.button(f"🗑️ 批次刪除 {len(no_score_hws)} 項無成績作業"):
                st.session_state.main_df = all_df[~all_df["作業名稱"].isin(no_score_hws)]
                save_data(st.session_state.main_df)
                st.rerun()
        if has_score_hws:
            st.sidebar.error("⚠️ 偵測到含成績紀錄")
            if st.sidebar.checkbox("確定刪除含成績作業"):
                if st.sidebar.button(f"🔥 強制刪除 {len(has_score_hws)} 項"):
                    st.session_state.main_df = all_df[~all_df["作業名稱"].isin(has_score_hws)]
                    save_data(st.session_state.main_df)
                    st.rerun()

        tab1, tab2, tab3 = st.tabs(["📋 缺交與登記成績", "🎯 單生管理", "📝 新增作業"])
        
        with tab1:
            ongoing_hws = [(hw, len(all_df[(all_df["作業名稱"] == hw) & (all_df["繳交狀態"] != "已繳交")])) for hw in all_hws]
            sel = st.selectbox("選擇作業項目", ["請選擇"] + [f"{h} (欠 {c} 人)" for h, c in ongoing_hws])
            
            if sel != "請選擇":
                target_hw = sel.split(" (欠")[0]
                
                # ✨ 新功能：座號快速標記區 ✨
                st.markdown(f"### ⚡ 座號快填 - {target_hw}")
                q_col1, q_col2 = st.columns(2)
                
                with q_col1:
                    fast_done = st.text_input("🟢 輸入座號標記【已繳交】", key="fast_done", placeholder="例：1 或是 1,2,3")
                    if fast_done:
                        # 支援單個或多個座號輸入
                        sids = [s.strip() for s in fast_done.replace("，", ",").split(",")]
                        for sid in sids:
                            mask = (st.session_state.main_df["作業名稱"] == target_hw) & (st.session_state.main_df["座號"] == sid)
                            if any(mask):
                                st.session_state.main_df.loc[mask, "繳交狀態"] = "已繳交"
                                st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
                        save_data(st.session_state.main_df)
                        st.rerun()

                with q_col2:
                    fast_edit = st.text_input("🔴 輸入座號標記【需訂正】", key="fast_edit", placeholder="例：5")
                    if fast_edit:
                        sids = [s.strip() for s in fast_edit.replace("，", ",").split(",")]
                        for sid in sids:
                            mask = (st.session_state.main_df["作業名稱"] == target_hw) & (st.session_state.main_df["座號"] == sid)
                            if any(mask):
                                st.session_state.main_df.loc[mask, "繳交狀態"] = "需訂正"
                                st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
                        save_data(st.session_state.main_df)
                        st.rerun()
                
                st.divider()
                # 原始條列式清單 (方便對名字或打成績)
                m = all_df[all_df["作業名稱"] == target_hw]
                for i, r in m.iterrows():
                    ca, c_frag = st.columns([1.5, 6])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    with c_frag: status_buttons(i, "tab1", show_score=True)

        with tab2:
            tsid = st.text_input("座號管理：", key="tsid")
            if tsid:
                sm = all_df[(all_df["座號"] == str(tsid))]
                if not sm.empty:
                    name = sm.iloc[0]['姓名']
                    for i, r in sm.iterrows():
                        ra, r_frag = st.columns([2, 6])
                        ra.write(f"📌 {r['作業名稱']}")
                        with r_frag: status_buttons(i, "tab2", show_score=True)

        with tab3:
            st.subheader("📝 新增作業")
            nhw = st.text_input("作業名稱：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                save_data(st.session_state.main_df)
                st.success("發佈成功！"); st.rerun()
