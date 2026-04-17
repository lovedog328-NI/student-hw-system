import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-資料安全版", layout="wide")
st.title("📚 303 作業登記系統")

STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

# --- 2. 核心資料邏輯 (強化安全機制) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        # 補齊欄位
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        # 修正座號格式
        df["座號"] = pd.to_numeric(df["座號"], errors='coerce').fillna(0).astype(int).astype(str)
        df = df[df["座號"] != "0"]
        # 強制修正姓名
        for s in STUDENT_LIST:
            df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df
    except Exception as e:
        st.error(f"連線雲端失敗，請重新整理頁面。錯誤代碼: {e}")
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])

def save_data(df):
    try:
        df = df.fillna("")
        conn.update(worksheet="Sheet1", data=df)
        # 更新後立刻反映到 session_state
        st.session_state.main_df = df
        return True
    except Exception as e:
        st.error(f"資料存檔失敗，請確認網路連線！錯誤: {e}")
        return False

# 初始化與同步
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. 核心功能函數 ---
def update_student_status(target_hw, sid_input, new_status):
    if not sid_input: return
    # 支援多號碼輸入，轉為半形
    sids = [s.strip() for s in sid_input.replace("，", ",").split(",") if s.strip()]
    temp_df = st.session_state.main_df.copy()
    updated = False
    for sid in sids:
        mask = (temp_df["作業名稱"] == target_hw) & (temp_df["座號"] == sid)
        if any(mask):
            temp_df.loc[mask, "繳交狀態"] = new_status
            temp_df.loc[mask, "更新日期"] = str(date.today())
            updated = True
    if updated:
        save_data(temp_df)
        st.rerun()

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
        st.warning("⚠️ 請輸入密碼以進行管理。")
    else:
        all_df = st.session_state.main_df
        all_hws = all_df["作業名稱"].unique()
        
        # 側邊欄清理功能 (穩定版)
        st.sidebar.divider()
        st.sidebar.subheader("🗑️ 快速清理")
        no_score_hws, has_score_hws = [], []
        for hw in all_hws:
            hw_data = all_df[all_df["作業名稱"] == hw]
            if len(hw_data[hw_data["繳交狀態"] != "已繳交"]) == 0:
                if hw_data[hw_data["成績"].apply(lambda x: str(x).strip() != "")].shape[0] > 0: has_score_hws.append(hw)
                else: no_score_hws.append(hw)
        
        if no_score_hws:
            if st.sidebar.button(f"🗑️ 批次刪除 {len(no_score_hws)} 項作業"):
                new_df = all_df[~all_df["作業名稱"].isin(no_score_hws)]
                save_data(new_df); st.rerun()
        if has_score_hws:
            st.sidebar.error("⚠️ 偵測到含成績紀錄")
            if st.sidebar.checkbox("確定刪除含成績紀錄"):
                if st.sidebar.button(f"🔥 強制刪除 {len(has_score_hws)} 項"):
                    new_df = all_df[~all_df["作業名稱"].isin(has_score_hws)]
                    save_data(new_df); st.rerun()

        tab1, tab2, tab3 = st.tabs(["📋 缺交與登記成績", "🎯 單生管理", "📝 新增作業"])
        
        with tab1:
            ongoing_hws = [(hw, len(all_df[(all_df["作業名稱"] == hw) & (all_df["繳交狀態"] != "已繳交")])) for hw in all_hws]
            sel = st.selectbox("選擇作業項目", ["請選擇"] + [f"{h} (欠 {c} 人)" for h, c in ongoing_hws])
            
            if sel != "請選擇":
                target_hw = sel.split(" (欠")[0]
                st.markdown(f"### ⚡ 座號快填 - {target_hw}")
                
                # 使用 Columns 搭配 text_input，不使用 fragment 以防資料遺失
                c_done, c_edit = st.columns(2)
                with c_done:
                    sid_done = st.text_input("🟢 標記【已繳交】座號 (Enter 送出)", key="f_done")
                    if sid_done: update_student_status(target_hw, sid_done, "已繳交")
                with c_edit:
                    sid_edit = st.text_input("🔴 標記【需訂正】座號 (Enter 送出)", key="f_edit")
                    if sid_edit: update_student_status(target_hw, sid_edit, "需訂正")
                
                st.divider()
                # 列表顯示
                m = all_df[all_df["作業名稱"] == target_hw]
                for i, r in m.iterrows():
                    ca, cb, cc, cd, ce = st.columns([1.5, 1.5, 1, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    color = "red" if r['繳交狀態'] == "需訂正" else ("orange" if r['繳交狀態'] == "未繳交" else "green")
                    cb.markdown(f":{color}[**{r['繳交狀態']}**]")
                    
                    # 成績登記
                    sc = ce.text_input("成績", value=str(r['成績']), key=f"sc_{target_hw}_{i}", label_visibility="collapsed")
                    if sc != str(r['成績']):
                        all_df.at[i, "成績"] = sc
                        save_data(all_df)
                    
                    if cc.button("訂正", key=f"r_{target_hw}_{i}"):
                        all_df.at[i, "繳交狀態"] = "需訂正"
                        all_df.at[i, "更新日期"] = str(date.today())
                        save_data(all_df); st.rerun()
                    if cd.button("已交", key=f"d_{target_hw}_{i}"):
                        all_df.at[i, "繳交狀態"] = "已繳交"
                        all_df.at[i, "更新日期"] = str(date.today())
                        save_data(all_df); st.rerun()

        with tab2:
            tsid = st.text_input("座號管理：", key="tsid_mgr")
            if tsid:
                sm = all_df[all_df["座號"] == str(tsid)]
                if not sm.empty:
                    st.write(f"管理對象：**{sm.iloc[0]['姓名']}**")
                    for i, r in sm.iterrows():
                        ra, rb, rc, rd = st.columns([3, 2, 1, 1])
                        ra.write(f"📌 {r['作業名稱']}")
                        color = "red" if r['繳交狀態'] == "需訂正" else ("orange" if r['繳交狀態'] == "未繳交" else "green")
                        rb.markdown(f":{color}[**{r['繳交狀態']}**]")
                        if rc.button("訂正", key=f"tab2_r_{i}"):
                            all_df.at[i, "繳交狀態"] = "需訂正"; save_data(all_df); st.rerun()
                        if rd.button("已交", key=f"tab2_d_{i}"):
                            all_df.at[i, "繳交狀態"] = "已繳交"; save_data(all_df); st.rerun()

        with tab3:
            st.subheader("📝 新增作業")
            nhw = st.text_input("作業名稱：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
                new_df = pd.concat([all_df, pd.DataFrame(new_rows)], ignore_index=True)
                save_data(new_df); st.success("發佈成功！"); st.rerun()
