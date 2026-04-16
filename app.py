import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-正向鼓勵版", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單 (詹荺蓁 已更正)
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]
NAME_MAP = {s['座號']: s['姓名'] for s in STUDENT_LIST}

# --- 2. 核心資料邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns:
                df[col] = ""
        
        if df is None or df.empty:
            return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])
            
        df["座號"] = pd.to_numeric(df["座號"], errors='coerce').fillna(0).astype(int).astype(str)
        df = df[df["座號"] != "0"]
        # 同步姓名修正
        for s in STUDENT_LIST:
            df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        return True
    except:
        return False

# 初始化資料
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. 局部更新元件 (僅限管理員看見成績) ---
@st.fragment
def status_buttons(idx, row_key, show_score=False):
    if show_score:
        c_status, c_score, c_edit, c_done = st.columns([1.2, 1, 1, 1])
    else:
        c_status, c_edit, c_done = st.columns([1.5, 1, 1])
    
    current_status = st.session_state.main_df.at[idx, "繳交狀態"]
    color = "red" if current_status == "未繳交" else "orange"
    c_status.markdown(f":{color}[**{current_status}**]")
    
    if show_score:
        current_score = str(st.session_state.main_df.at[idx, "成績"]) if not pd.isna(st.session_state.main_df.at[idx, "成績"]) else ""
        new_score = c_score.text_input("成績", value=current_score, key=f"score_{row_key}_{idx}", label_visibility="collapsed", placeholder="分數")
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

# [學生查詢介面]
if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的作業狀況")
            
            # 找出尚未完成的作業 (未繳交 或 需訂正)
            todo = res[res["繳交狀態"] != "已繳交"]
            
            if todo.empty:
                # ✨ 全部交齊的華麗慶祝
                st.balloons()
                st.success(f"🎊 太棒了，{name}！你目前沒有欠任何作業喔！")
                st.info("繼續保持良好的學習習慣！")
            else:
                # 還有欠交時的顯示
                st.warning(f"注意：還有 {len(todo)} 項作業需要處理喔！")
                student_view_df = res[["作業名稱", "繳交狀態", "更新日期"]].copy()
                st.table(student_view_df)
            
            if is_admin:
                st.divider()
                st.write("🔧 管理員快速操作：")
                manage_list = res[res["繳交狀態"] != "已繳交"]
                for idx, row in manage_list.iterrows():
                    ca, cb = st.columns([2, 5])
                    ca.write(f"📌 {row['作業名稱']}")
                    with cb: status_buttons(idx, "query", show_score=True)

# [老師後台介面]
elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入正確密碼。")
    else:
        all_df = st.session_state.main_df
        all_hws = all_df["作業名稱"].unique()
        ongoing_hws = [(hw, len(all_df[(all_df["作業名稱"] == hw) & (all_df["繳交狀態"] != "已繳交")])) for hw in all_hws]

        tab1, tab2, tab3 = st.tabs(["📋 缺交與登記成績", "🎯 單生補交與通知單", "📝 新增作業"])
        
        with tab1:
            sel = st.selectbox("選擇作業項目", ["請選擇"] + [f"{h} (欠 {c} 人)" for h, c in ongoing_hws if c > 0])
            if sel != "請選擇":
                target_hw = sel.split(" (欠")[0]
                m = all_df[all_df["作業名稱"] == target_hw]
                for i, r in m.iterrows():
                    ca, c_frag = st.columns([1.5, 6])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    with c_frag:
                        status_buttons(i, "tab1", show_score=True)

        with tab2:
            tsid = st.text_input("輸入座號 (1-22)：", key="tsid")
            if tsid:
                sm = all_df[(all_df["座號"] == str(tsid))]
                if not sm.empty:
                    name = sm.iloc[0]['姓名']
                    st.write(f"正在管理：**{name}**")
                    for i, r in sm.iterrows():
                        ra, r_frag = st.columns([2, 6])
                        ra.write(f"📌 {r['作業名稱']}")
                        with r_frag:
                            status_buttons(i, "tab2", show_score=True)
                    
                    st.divider()
                    st.markdown("### 🖨️ 欠交清單")
                    clean_text = f"【作業催繳通知單】\n日期：{date.today().strftime('%m/%d')}\n座號：{tsid}  姓名：{name}\n--------------------\n"
                    todo_list = sm[sm["繳交狀態"] != "已繳交"]
                    for _, row in todo_list.iterrows():
                        mark = "未交" if row['繳交狀態'] == "未繳交" else "訂正"
                        clean_text += f"□ {row['作業名稱']} ({mark})\n"
                    clean_text += f"□ ________________\n--------------------\n家長簽名：___________"
                    st.text_area("複製通知文字", clean_text, height=150)

        with tab3:
            st.subheader("📝 新增作業")
            nhw = st.text_input("作業名稱：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                save_data(st.session_state.main_df)
                st.success("發佈成功！")
                st.rerun()
