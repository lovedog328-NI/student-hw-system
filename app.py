import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-絲滑操作版", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

# --- 2. 核心資料與格式化邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def force_int_str(val):
    try: return str(int(float(val)))
    except: return str(val)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        df["座號"] = df["座號"].apply(force_int_str)
        df = df[df["座號"] != ""]
        for s in STUDENT_LIST:
            df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])

def save_data_core(df):
    try:
        if df.empty: return False
        df_to_save = df.copy().fillna("")
        df_to_save["座號"] = df_to_save["座號"].apply(force_int_str)
        conn.update(worksheet="Sheet1", data=df_to_save)
        return True
    except: return False

# --- 3. 系統暫存初始化 ---
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()
if 'has_unsaved_changes' not in st.session_state:
    st.session_state.has_unsaved_changes = False
if 'selected_hw_base' not in st.session_state:
    st.session_state.selected_hw_base = "請選擇"

# --- 4. Callbacks (背景更新邏輯，不閃畫面) ---

def clean_seat_input(val_str):
    raw_list = val_str.replace("，", ",").split(",")
    res = []
    for s in raw_list:
        s = s.strip()
        if s: res.append(force_int_str(s))
    return res

def mark_fast(hw_name, status, input_key):
    val = st.session_state[input_key]
    if not val: return
    sids = clean_seat_input(val)
    for sid in sids:
        mask = (st.session_state.main_df["作業名稱"] == hw_name) & (st.session_state.main_df["座號"] == sid)
        st.session_state.main_df.loc[mask, "繳交狀態"] = status
        st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
    st.session_state.has_unsaved_changes = True
    st.session_state[input_key] = "" # 自動清空輸入框

def update_single_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    st.session_state.has_unsaved_changes = True

def update_score(idx, score_key):
    new_val = st.session_state[score_key]
    if str(st.session_state.main_df.at[idx, "成績"]) != new_val:
        st.session_state.main_df.at[idx, "成績"] = new_val
        st.session_state.has_unsaved_changes = True

def on_hw_select():
    sel_str = st.session_state.hw_sel_widget
    st.session_state.selected_hw_base = sel_str.split(" (")[0] if sel_str != "請選擇" else "請選擇"

# --- 5. 側邊欄與存檔 ---
st.sidebar.title("⚙️ 管理選單")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if is_admin:
    if st.session_state.has_unsaved_changes:
        st.sidebar.error("🚨 資料尚未同步至雲端")
        if st.sidebar.button("💾 儲存並同步", type="primary", use_container_width=True):
            if save_data_core(st.session_state.main_df):
                st.session_state.has_unsaved_changes = False
                st.sidebar.success("✅ 已存檔")
                st.rerun()
    else:
        st.sidebar.success("✔️ 雲端資料已同步")

if st.sidebar.button("🔄 重新載入雲端"):
    st.session_state.main_df = load_data()
    st.session_state.has_unsaved_changes = False
    st.rerun()

# --- 6. 主畫面 UI ---
menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        clean_id = force_int_str(sid)
        res = st.session_state.main_df[st.session_state.main_df["座號"] == clean_id]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的待辦作業")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success("🎊 沒有欠作業喔！")
            else:
                for idx, row in todo.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"📌 **{row['作業名稱']}**")
                    color = "red" if row['繳交狀態'] == "需訂正" else "orange"
                    cb.markdown(f":{color}[{row['繳交狀態']}]")

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入老師密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 登記成績", "🎯 單生管理", "📝 新增作業"])
        
        with tab1:
            all_hws = list(st.session_state.main_df["作業名稱"].unique())
            hw_names = ["請選擇"] + all_hws
            hw_display = ["請選擇"] + [f"{hw} (欠 {len(st.session_state.main_df[(st.session_state.main_df['作業名稱'] == hw) & (st.session_state.main_df['繳交狀態'] != '已繳交')])} 人)" for hw in all_hws]
            
            # 尋找上次選中的作業 (絕對防跳頁機制)
            current_index = 0
            if st.session_state.selected_hw_base in hw_names:
                current_index = hw_names.index(st.session_state.selected_hw_base)
            
            st.selectbox("選擇作業項目", hw_display, index=current_index, key="hw_sel_widget", on_change=on_hw_select)
            
            target_hw = st.session_state.selected_hw_base
            if target_hw != "請選擇":
                st.markdown(f"### ⚡ 座號快填 - {target_hw}")
                c1, c2 = st.columns(2)
                done_key = f"fd_{target_hw}"
                edit_key = f"fe_{target_hw}"
                
                with c1:
                    st.text_input("🟢 快速標記【已繳交】(Enter送出)", key=done_key, placeholder="例: 1,3,5", on_change=mark_fast, args=(target_hw, "已繳交", done_key))
                with c2:
                    st.text_input("🔴 快速標記【需訂正】(Enter送出)", key=edit_key, placeholder="例: 12", on_change=mark_fast, args=(target_hw, "需訂正", edit_key))

                st.divider()
                st.info("💡 提醒：輸入座號後按下 Enter，清單會立即更新，輸入框也會自動清空。")
                
                m = st.session_state.main_df[st.session_state.main_df["作業名稱"] == target_hw]
                for i, r in m.iterrows():
                    ca, cb, cc, cd, ce = st.columns([1.2, 1.2, 1, 1, 1.2])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    color = "red" if r['繳交狀態'] == "需訂正" else ("orange" if r['繳交狀態'] == "未繳交" else "green")
                    cb.markdown(f":{color}[**{r['繳交狀態']}**]")
                    
                    cc.button("訂正", key=f"r_{target_hw}_{i}", on_click=update_single_status, args=(i, "需訂正"))
                    cd.button("已交", key=f"d_{target_hw}_{i}", on_click=update_single_status, args=(i, "已繳交"))
                    
                    score_key = f"sc_{target_hw}_{i}"
                    ce.text_input("成績", value=str(r['成績']), key=score_key, label_visibility="collapsed", placeholder="成績", on_change=update_score, args=(i, score_key))

        with tab3:
            st.subheader("📝 新增作業")
            nhw = st.text_input("作業名稱：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state.has_unsaved_changes = True
                st.rerun()

# 側邊欄清理功能
if is_admin:
    st.sidebar.divider()
    with st.sidebar.expander("🗑️ 快速清理作業"):
        target = st.selectbox("選取要刪除的作業", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
        if st.button("確認刪除") and target != "請選擇":
            st.session_state.main_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
            st.session_state.has_unsaved_changes = True
            st.rerun()
