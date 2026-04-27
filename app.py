import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定與精美 CSS 樣式 ---
st.set_page_config(page_title="303作業登記-精美公佈欄", layout="wide")

# ✨ 植入精美卡片的 CSS 樣式
st.markdown("""
<style>
.student-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    background: var(--background-color);
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border-top: 4px solid #4CAF50;
}
.student-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.1);
}
.student-name {
    margin-top: 0;
    margin-bottom: 12px;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-color);
}
.hw-tag-red {
    background-color: rgba(211, 47, 47, 0.1);
    color: #d32f2f;
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: bold;
    display: inline-block;
    margin: 4px 4px 4px 0;
    border: 1px solid rgba(211, 47, 47, 0.2);
}
.hw-tag-orange {
    background-color: rgba(230, 81, 0, 0.1);
    color: #e65100;
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: bold;
    display: inline-block;
    margin: 4px 4px 4px 0;
    border: 1px solid rgba(230, 81, 0, 0.2);
}
.empty-state {
    text-align: center;
    padding: 50px;
    background-color: rgba(76, 175, 80, 0.1);
    border-radius: 15px;
    border: 2px dashed #4CAF50;
    color: #2E7D32;
}
</style>
""", unsafe_allow_html=True)

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
    except: return str(val).strip()

def clean_score(val):
    s = str(val).strip()
    if s in ["", "nan", "NaN", "None"]: return ""
    try:
        f = float(s)
        if f.is_integer(): return str(int(f))
        return str(f)
    except:
        return s

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        df["座號"] = df["座號"].apply(force_int_str)
        df["成績"] = df["成績"].apply(clean_score)
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
        df_to_save["成績"] = df_to_save["成績"].apply(clean_score)
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

# --- 4. Callbacks ---
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
    st.session_state[input_key] = "" 

def update_single_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    st.session_state.has_unsaved_changes = True

def update_score(idx, score_key):
    new_val = clean_score(st.session_state[score_key])
    if str(st.session_state.main_df.at[idx, "成績"]) != new_val:
        st.session_state.main_df.at[idx, "成績"] = new_val
        st.session_state.has_unsaved_changes = True

def on_hw_select():
    sel_str = st.session_state.hw_sel_widget
    st.session_state.selected_hw_base = sel_str.split(" (")[0] if sel_str != "請選擇" else "請選擇"

# --- 5. 側邊欄與存檔 ---
st.sidebar.title("⚙️ 選單與功能")

# ✨ 改為三個選單，把公佈欄放在公開區域
menu = st.sidebar.radio("請選擇功能：", ["📊 班級公佈欄", "🔍 個人查詢", "🛠️ 老師後台"])

st.sidebar.divider()
pwd = st.sidebar.text_input("老師密碼 (管理員專用)", type="password")
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

if st.sidebar.button("🔄 重新載入最新資料"):
    st.session_state.main_df = load_data()
    st.session_state.has_unsaved_changes = False
    st.rerun()

# --- 6. 主畫面 UI ---

# [分頁 1：班級公佈欄 (學生/家長皆可看)]
if menu == "📊 班級公佈欄":
    st.markdown("### 🏆 目前全班未完成作業總覽")
    st.caption(f"最後更新日期：{date.today().strftime('%Y-%m-%d')}")
    
    todo_df = st.session_state.main_df[st.session_state.main_df["繳交狀態"] != "已繳交"]
    
    if todo_df.empty:
        st.balloons()
        st.markdown("""
        <div class="empty-state">
            <h1>🎉 太棒了！</h1>
            <h3>全班目前的作業皆已繳交完成！</h3>
            <p>請繼續保持這個好習慣喔！</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        todo_sids = sorted(todo_df["座號"].unique(), key=lambda x: int(x))
        cols = st.columns(4) # 一排 4 張卡片
        
        for idx, sid in enumerate(todo_sids):
            student_data = todo_df[todo_df["座號"] == sid]
            name = student_data.iloc[0]["姓名"]
            
            # 生成精美 HTML 卡片
            with cols[idx % 4]:
                tags_html = ""
                for _, row in student_data.iterrows():
                    hw_name = row['作業名稱']
                    status = row['繳交狀態']
                    css_class = "hw-tag-red" if status == "需訂正" else "hw-tag-orange"
                    tags_html += f'<span class="{css_class}">{hw_name} ({status})</span>'
                
                card_html = f"""
                <div class="student-card">
                    <div class="student-name">👤 {sid}. {name}</div>
                    <div>{tags_html}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

# [分頁 2：個人查詢]
elif menu == "🔍 個人查詢":
    sid = st.text_input("輸入座號查詢您的作業 (1-22)：", placeholder="例如：5")
    if sid:
        clean_id = force_int_str(sid)
        res = st.session_state.main_df[st.session_state.main_df["座號"] == clean_id]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的專屬待辦清單")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success("🎊 恭喜！你目前沒有任何欠交的作業喔！")
            else:
                for idx, row in todo.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"📌 **{row['作業名稱']}**")
                    color = "red" if row['繳交狀態'] == "需訂正" else "orange"
                    cb.markdown(f":{color}[{row['繳交狀態']}]")

# [分頁 3：老師後台]
elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 這是專屬老師的管理區域，請在左側輸入正確密碼。")
    else:
        # 將 LINE 推播獨立成一個小分頁
        tab_line, tab1, tab2, tab3 = st.tabs(["📲 LINE 推播", "📋 登記成績", "🎯 單生管理", "📝 新增作業"])
        
        with tab_line:
            st.markdown("#### 📋 快速複製：群組推播文字")
            st.info("此區文字會自動抓取公佈欄的資料，方便您直接複製貼上到班級 LINE 群組。")
            todo_df = st.session_state.main_df[st.session_state.main_df["繳交狀態"] != "已繳交"]
            
            if todo_df.empty:
                st.success("目前全班皆已繳齊，無須催繳！")
            else:
                copy_text = f"【作業缺交/訂正提醒】\n日期：{date.today().strftime('%m/%d')}\n------------------------\n"
                todo_sids = sorted(todo_df["座號"].unique(), key=lambda x: int(x))
                
                for sid in todo_sids:
                    student_data = todo_df[todo_df["座號"] == sid]
                    name = student_data.iloc[0]["姓名"]
                    tasks_for_copy = []
                    for _, row in student_data.iterrows():
                        short_status = "未交" if row['繳交狀態'] == "未繳交" else "訂正"
                        tasks_for_copy.append(f"{row['作業名稱']}({short_status})")
                    copy_text += f"{sid}.{name}： " + "、".join(tasks_for_copy) + "\n"
                
                copy_text += "------------------------\n麻煩家長協助叮嚀，謝謝！"
                st.text_area("在框框內點擊右鍵「全選」➜「複製」", copy_text, height=250)

        with tab1:
            all_hws = list(st.session_state.main_df["作業名稱"].unique())
            hw_names = ["請選擇"] + all_hws
            hw_display = ["請選擇"] + [f"{hw} (欠 {len(st.session_state.main_df[(st.session_state.main_df['作業名稱'] == hw) & (st.session_state.main_df['繳交狀態'] != '已繳交')])} 人)" for hw in all_hws]
            
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

        with tab2:
            tsid = st.text_input("管理座號：", key="tsid_mgr")
            if tsid:
                clean_tsid = force_int_str(tsid)
                sm = st.session_state.main_df[st.session_state.main_df["座號"] == clean_tsid]
                if not sm.empty:
                    name = sm.iloc[0]['姓名']
                    st.markdown(f"#### 👤 管理對象：{name}")
                    for i, r in sm.iterrows():
                        ra, rb, rc, rd = st.columns([3, 2, 1, 1])
                        ra.write(f"📌 {r['作業名稱']}")
                        color = "red" if r['繳交狀態'] == "需訂正" else ("orange" if r['繳交狀態'] == "未繳交" else "green")
                        rb.markdown(f":{color}[**{r['繳交狀態']}**]")
                        
                        rc.button("訂正", key=f"t2_r_{i}", on_click=update_single_status, args=(i, "需訂正"))
                        rd.button("已交", key=f"t2_d_{i}", on_click=update_single_status, args=(i, "已繳交"))
                else:
                    st.info("找不到該座號的資料，請確認輸入是否正確。")

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
