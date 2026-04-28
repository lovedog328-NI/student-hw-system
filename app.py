import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. 基本設定與 🎀 可愛手寫風 CSS ---
st.set_page_config(page_title="303作業登記-穩定手帳版", layout="wide")

st.markdown("""
<style>
/* ✨ 導入可愛手寫字體：Kalam (英文/數字) + 霞鶩文楷 (中文) */
@import url('https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&family=LXGW+WenKai+TC:wght@400;700&display=swap');

/* 全局字體替換，優先使用手寫體 */
html, body, [class*="css"], .stTextInput input, .stSelectbox div, button {
    font-family: 'Kalam', 'LXGW WenKai TC', 'Comic Sans MS', cursive, sans-serif !important;
}

/* 標題換上活潑的顏色 */
h1, h2, h3 { color: #FF7F50 !important; font-weight: 700 !important; }

/* 🎀 學生卡片變成軟綿綿的圓角 */
.student-card {
    border: 3px solid #FFE4E1;
    border-radius: 25px; 
    padding: 20px;
    margin-bottom: 20px;
    background: #FFF0F5; 
    box-shadow: 0 8px 15px rgba(255, 182, 193, 0.3);
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
    border-top: 8px solid #FFB6C1;
}
.student-card:hover { 
    transform: translateY(-5px) scale(1.02); 
    box-shadow: 0 15px 25px rgba(255, 182, 193, 0.5); 
}
.student-name { margin-top: 0; margin-bottom: 15px; font-size: 1.4rem; font-weight: 700; color: #DB7093; }

/* 🎀 標籤變手帳風虛線 */
.hw-tag-red { background-color: #FFE4E1; color: #FF69B4; padding: 8px 14px; border-radius: 25px; font-size: 1rem; font-weight: 700; display: inline-block; margin: 5px 5px 5px 0; border: 2px dashed #FFB6C1; }
.hw-tag-orange { background-color: #FFFACD; color: #FFA500; padding: 8px 14px; border-radius: 25px; font-size: 1rem; font-weight: 700; display: inline-block; margin: 5px 5px 5px 0; border: 2px dashed #FFD700; }

/* 🎀 全班交齊的慶祝框 */
.empty-state { text-align: center; padding: 60px; background-color: #E0FFFF; border-radius: 30px; border: 4px dashed #87CEEB; color: #4682B4; box-shadow: 0 10px 20px rgba(135,206,235,0.2); }

/* 🎀 放大的分頁標籤，圓潤化 */
button[data-baseweb="tab"] { font-size: 1.3rem !important; font-weight: 700 !important; padding: 1rem 1.5rem !important; border-radius: 20px 20px 0 0 !important; color: #FF7F50 !important;}
button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFF0F5 !important; border-bottom: 4px solid #FF69B4 !important; }

/* 🎀 按鈕變成圓滾滾的膠囊 */
.stButton > button { 
    font-size: 1.15rem !important; 
    font-weight: 700 !important; 
    padding: 0.6rem 1.5rem !important; 
    border-radius: 30px !important; 
    border: none !important;
    background-color: #FFB6C1 !important;
    color: white !important;
    box-shadow: 0 6px 10px rgba(255, 182, 193, 0.4) !important;
    transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}
.stButton > button:hover {
    background-color: #FF69B4 !important;
    transform: scale(1.08) !important;
    box-shadow: 0 8px 15px rgba(255, 105, 180, 0.5) !important;
}

/* 🎀 超醒目今日提醒框變軟萌 */
.today-alert { background-color: #FFF8DC; border-left: 12px solid #FFA07A; padding: 25px; border-radius: 20px; box-shadow: 0 8px 16px rgba(255, 160, 122, 0.2); margin-bottom: 30px; }
.today-alert h3 { margin-top: 0; color: #FF7F50; font-weight: 700;}
.today-alert ul { margin-bottom: 0; font-size: 1.3rem; color: #CD5C5C; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

st.title("📚 303 作業登記系統 ✨")

STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

SHEET_COLUMNS = {
    "Sheet1": ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"],
    "Salary": ["日期", "項目", "金額"],
    "Reminders": ["日期", "事項", "狀態"]
}

# --- 2. 核心資料與防錯邏輯 ---
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
    except: return s

def load_data(sheet_name="Sheet1"):
    expected_cols = SHEET_COLUMNS.get(sheet_name, [])
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            df = pd.DataFrame(columns=expected_cols)
        else:
            for col in expected_cols:
                if col not in df.columns: df[col] = ""
        df = df.fillna("")
        if not df.empty:
            df = df[~(df[expected_cols] == "").all(axis=1)]
        if sheet_name == "Sheet1" and not df.empty:
            df["座號"] = df["座號"].apply(force_int_str)
            df["成績"] = df["成績"].apply(clean_score)
            df = df[df["座號"] != ""]
            for s in STUDENT_LIST:
                df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df.reset_index(drop=True)
    except:
        return pd.DataFrame(columns=expected_cols)

def save_data_to_sheet(df, sheet_name):
    try:
        expected_cols = SHEET_COLUMNS.get(sheet_name, [])
        df_to_save = df.copy().fillna("")
        if df_to_save.empty:
            empty_row = {col: "" for col in expected_cols}
            df_to_save = pd.DataFrame([empty_row])
        else:
            if sheet_name == "Sheet1":
                df_to_save["座號"] = df_to_save["座號"].apply(force_int_str)
                df_to_save["成績"] = df_to_save["成績"].apply(clean_score)
        conn.update(worksheet=sheet_name, data=df_to_save)
        return True
    except Exception as e:
        st.error(f"存檔發生錯誤：{e}")
        return False

# --- 3. 系統暫存初始化 ---
if 'main_df' not in st.session_state: st.session_state.main_df = load_data("Sheet1")
if 'salary_df' not in st.session_state: st.session_state.salary_df = load_data("Salary")
if 'reminder_df' not in st.session_state: st.session_state.reminder_df = load_data("Reminders")
if 'has_unsaved' not in st.session_state: st.session_state.has_unsaved = False
if 'selected_hw_base' not in st.session_state: st.session_state.selected_hw_base = "請選擇"
if "main_menu" not in st.session_state: st.session_state.main_menu = "📊 班級公佈欄"

# 初始化輸入框變數 (防止重整時報錯)
if "new_rem_input" not in st.session_state: st.session_state.new_rem_input = ""
if "new_hw_input" not in st.session_state: st.session_state.new_hw_input = ""
if "remind_range_val" not in st.session_state: st.session_state.remind_range_val = [date.today(), date.today() + timedelta(days=2)]

# --- 4. Callbacks (不閃爍更新邏輯) ---
def clean_seat_input(val_str):
    res = []
    for s in val_str.replace("，", ",").split(","):
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
    st.session_state.has_unsaved = True
    st.session_state[input_key] = "" 

def update_single_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    st.session_state.has_unsaved = True

def update_score(idx, score_key):
    new_val = clean_score(st.session_state[score_key])
    if str(st.session_state.main_df.at[idx, "成績"]) != new_val:
        st.session_state.main_df.at[idx, "成績"] = new_val
        st.session_state.has_unsaved = True

def on_hw_select():
    sel_str = st.session_state.hw_sel_widget
    st.session_state.selected_hw_base = sel_str.split(" (")[0] if sel_str != "請選擇" else "請選擇"

# ✨ 新增 Callback：處理新增提醒
def add_reminder():
    text = st.session_state.new_rem_input.strip()
    if not text: return
    r_range = st.session_state.remind_range_val
    date_val = str(r_range[0]) if len(r_range) == 1 else f"{r_range[0]} to {r_range[1]}"
    new_r = pd.DataFrame([{"日期": date_val, "事項": text, "狀態": "待辦"}])
    st.session_state.reminder_df = pd.concat([st.session_state.reminder_df, new_r], ignore_index=True)
    st.session_state.has_unsaved = True
    st.session_state.new_rem_input = "" # 安全清空

# ✨ 新增 Callback：處理新增作業
def add_homework():
    nhw = st.session_state.new_hw_input.strip()
    if not nhw: return
    new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
    st.session_state.has_unsaved = True
    st.session_state.new_hw_input = "" # 安全清空

def update_rem_range():
    st.session_state.remind_range_val = st.session_state.temp_range

# --- 5. 側邊欄 ---
st.sidebar.title("⚙️ 選單與功能")

menu = st.sidebar.radio("請選擇功能：", ["📊 班級公佈欄", "🔍 個人查詢", "🛠️ 老師後台"], key="main_menu")

st.sidebar.divider()
pwd = st.sidebar.text_input("老師密碼 (管理員專用)", type="password")
is_admin = (pwd == "alice")

if is_admin:
    if st.session_state.has_unsaved:
        st.sidebar.error("🚨 資料尚未同步至雲端")
        if st.sidebar.button("💾 儲存並同步", type="primary", use_container_width=True):
            save_data_to_sheet(st.session_state.main_df, "Sheet1")
            save_data_to_sheet(st.session_state.salary_df, "Salary")
            save_data_to_sheet(st.session_state.reminder_df, "Reminders")
            st.session_state.has_unsaved = False
            st.sidebar.success("✅ 已存檔")
            st.rerun()
    else:
        st.sidebar.success("✔️ 雲端資料已同步")

if st.sidebar.button("🔄 重新載入最新資料"):
    st.session_state.main_df = load_data("Sheet1")
    st.session_state.salary_df = load_data("Salary")
    st.session_state.reminder_df = load_data("Reminders")
    st.session_state.has_unsaved = False
    st.rerun()

# --- 6. 主畫面 UI ---
if menu == "📊 班級公佈欄":
    st.markdown("### 🏆 目前全班未完成作業總覽")
    todo_df = st.session_state.main_df[st.session_state.main_df["繳交狀態"] != "已繳交"]
    
    if todo_df.empty:
        st.balloons()
        st.markdown("""<div class="empty-state"><h1>🎉 太棒了！</h1><h3>全班目前的作業皆已繳交完成！</h3><p>大家真的太棒啦 ✨</p></div>""", unsafe_allow_html=True)
    else:
        todo_sids = sorted(todo_df["座號"].unique(), key=lambda x: int(x))
        cols = st.columns(4)
        for idx, sid in enumerate(todo_sids):
            student_data = todo_df[todo_df["座號"] == sid]
            name = student_data.iloc[0]["姓名"]
            with cols[idx % 4]:
                tags_html = ""
                for _, row in student_data.iterrows():
                    css_class = "hw-tag-red" if row['繳交狀態'] == "需訂正" else "hw-tag-orange"
                    tags_html += f'<span class="{css_class}">{row["作業名稱"]} ({row["繳交狀態"]})</span>'
                st.markdown(f'<div class="student-card"><div class="student-name">👤 {sid}. {name}</div><div>{tags_html}</div></div>', unsafe_allow_html=True)

elif menu == "🔍 個人查詢":
    sid = st.text_input("輸入座號查詢您的作業 (1-22)：", placeholder="例如：5")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == force_int_str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的專屬待辦清單")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty: st.success("🎊 恭喜！你目前沒有任何欠交的作業喔！")
            else:
                for _, row in todo.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"📌 **{row['作業名稱']}**")
                    cb.markdown(f":{'red' if row['繳交狀態']=='需訂正' else 'orange'}[{row['繳交狀態']}]")

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 這是老師專屬的秘密基地，請在左側輸入密碼喔！ 🤫")
    else:
        today = date.today()
        if not st.session_state.reminder_df.empty:
            active_rems = []
            for _, r in st.session_state.reminder_df.iterrows():
                if r['狀態'] == "已完成": continue
                try:
                    if " to " in str(r['日期']):
                        start_s, end_s = str(r['日期']).split(" to ")
                        start_d = datetime.strptime(start_s, '%Y-%m-%d').date()
                        end_d = datetime.strptime(end_s, '%Y-%m-%d').date()
                        if start_d <= today <= end_d: active_rems.append(r['事項'])
                    elif str(r['日期']) == str(today):
                        active_rems.append(r['事項'])
                except: continue
            
            if active_rems:
                list_html = "".join([f"<li>📌 {item}</li>" for item in active_rems])
                st.markdown(f'<div class="today-alert"><h3>🚨 今日重要提醒</h3><ul>{list_html}</ul></div>', unsafe_allow_html=True)

        tab_remind, tab1, tab2, tab_line, tab3, tab_money = st.tabs(["📌 提醒", "📋 登記成績", "🎯 單生管理", "📲 LINE推播", "📝 新增作業", "💰 薪資紀錄"])
        
        with tab_remind:
            st.subheader("📌 提醒事項管理")
            
            # ✨ 使用 on_change 來安全記錄日期與文字輸入
            st.date_input("選擇提醒期間", st.session_state.remind_range_val, key="temp_range", on_change=update_rem_range)
            
            c_input, c_btn = st.columns([4, 1])
            with c_input:
                st.text_input("輸入待辦事項... (輸入完按 Enter 或右側按鈕)", key="new_rem_input", placeholder="例如：明天要收回條喔！", on_change=add_reminder)
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True) # 排版對齊
                st.button("➕ 新增", on_click=add_reminder)

            st.divider()
            if not st.session_state.reminder_df.empty:
                st.write("### 📝 待辦清單 (點擊勾選即可標記完成)")
                for idx, row in st.session_state.reminder_df.iterrows():
                    is_done = (row['狀態'] == "已完成")
                    col_check, col_text = st.columns([1, 15])
                    with col_check:
                        checked = st.checkbox("", value=is_done, key=f"rem_cb_{idx}")
                        if checked != is_done:
                            st.session_state.reminder_df.at[idx, "狀態"] = "已完成" if checked else "待辦"
                            st.session_state.has_unsaved = True
                            st.rerun()
                    with col_text:
                        if is_done: st.markdown(f"~~{row['事項']}~~ 💤 *(期間: {row['日期']})*")
                        else: st.markdown(f"**{row['事項']}** ✨ *(期間: {row['日期']})*")
                
                st.write("")
                if st.button("🧹 清空所有提醒"):
                    st.session_state.reminder_df = pd.DataFrame(columns=["日期", "事項", "狀態"])
                    st.session_state.has_unsaved = True; st.rerun()

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
                
                with c1: st.text_input("🟢 快速標記【已繳交】(Enter送出)", key=done_key, placeholder="例: 1,3,5", on_change=mark_fast, args=(target_hw, "已繳交", done_key))
                with c2: st.text_input("🔴 快速標記【需訂正】(Enter送出)", key=edit_key, placeholder="例: 12", on_change=mark_fast, args=(target_hw, "需訂正", edit_key))

                st.divider()
                
                m = st.session_state.main_df[st.session_state.main_df["作業名稱"] == target_hw]
                for i, r in m.iterrows():
                    ca, cb, cc, cd, ce = st.columns([1.2, 1.2, 1, 1, 1.2])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    cb.markdown(f":{'red' if r['繳交狀態']=='需訂正' else ('orange' if r['繳交狀態']=='未繳交' else 'green')}[**{r['繳交狀態']}**]")
                    cc.button("訂正", key=f"r_{target_hw}_{i}", on_click=update_single_status, args=(i, "需訂正"))
                    cd.button("已交", key=f"d_{target_hw}_{i}", on_click=update_single_status, args=(i, "已繳交"))
                    score_key = f"sc_{target_hw}_{i}"
                    ce.text_input("成績", value=str(r['成績']), key=score_key, label_visibility="collapsed", on_change=update_score, args=(i, score_key))

        with tab2:
            tsid = st.text_input("管理座號：", key="tsid_mgr", placeholder="輸入座號查詢...")
            if tsid:
                clean_tsid = force_int_str(tsid)
                sm = st.session_state.main_df[st.session_state.main_df["座號"] == clean_tsid]
                if not sm.empty:
                    st.markdown(f"#### 👤 學生：{sm.iloc[0]['姓名']}")
                    for i, r in sm.iterrows():
                        ra, rb, rc, rd = st.columns([3, 2, 1, 1])
                        ra.write(f"📌 {r['作業名稱']}")
                        rb.markdown(f":{'red' if r['繳交狀態']=='需訂正' else ('orange' if r['繳交狀態']=='未繳交' else 'green')}[**{r['繳交狀態']}**]")
                        rc.button("訂正", key=f"t2_r_{i}", on_click=update_single_status, args=(i, "需訂正"))
                        rd.button("已交", key=f"t2_d_{i}", on_click=update_single_status, args=(i, "已繳交"))

        with tab_line:
            st.markdown("#### 📋 快速複製：群組推播文字")
            todo_df = st.session_state.main_df[st.session_state.main_df["繳交狀態"] != "已繳交"]
            if todo_df.empty: st.success("🎉 目前無須催繳，大家都很棒！")
            else:
                copy_text = f"【作業缺交/訂正提醒】\n日期：{date.today().strftime('%m/%d')}\n------------------------\n"
                for sid in sorted(todo_df["座號"].unique(), key=lambda x: int(x)):
                    stu = todo_df[todo_df["座號"] == sid]
                    tasks = [f"{r['作業名稱']}({'未交' if r['繳交狀態']=='未繳交' else '訂正'})" for _, r in stu.iterrows()]
                    copy_text += f"{sid}.{stu.iloc[0]['姓名']}： " + "、".join(tasks) + "\n"
                copy_text += "------------------------\n麻煩家長協助叮嚀，謝謝！"
                st.text_area("在框框內點擊右鍵「全選」➜「複製」", copy_text, height=250)

        with tab3:
            # ✨ 使用 Callback 處理新增作業，安全清空
            st.text_input("輸入新作業名稱 (輸入完按 Enter)：", key="new_hw_input", placeholder="例如：國語習作 CH5", on_change=add_homework)
            if st.button("🚀 確認發佈", on_click=add_homework):
                pass # 邏輯已在 callback 中處理

        with tab_money:
            log_date = st.date_input("選擇上課日期", date.today())
            c1, c2, c3 = st.columns(3)
            def add_salary(item, amount):
                new_row = pd.DataFrame([{"日期": str(log_date), "項目": item, "金額": amount}])
                st.session_state.salary_df = pd.concat([st.session_state.salary_df, new_row], ignore_index=True)
                st.session_state.has_unsaved = True
            
            if c1.button("4點前課輔 ($405)"): add_salary("4點前課輔", 405); st.success(f"已記錄：{log_date} 4點前")
            if c2.button("4點後課輔 ($480)"): add_salary("4點後課輔", 480); st.success(f"已記錄：{log_date} 4點後")
            if c3.button("學扶 ($405)"): add_salary("學扶", 405); st.success(f"已記錄：{log_date} 學扶")
            
            if not st.session_state.salary_df.empty:
                st.divider()
                temp_df = st.session_state.salary_df.copy()
                temp_df["年月"] = temp_df["日期"].astype(str).str[:7]
                all_months = sorted(temp_df["年月"].unique(), reverse=True)
                curr_month_str = datetime.now().strftime("%Y-%m")
                if curr_month_str not in all_months: all_months.insert(0, curr_month_str)

                selected_month = st.selectbox("📅 選擇結算月份", all_months)
                m_df = temp_df[temp_df["年月"] == selected_month]

                total_sum = pd.to_numeric(m_df['金額'], errors='coerce').sum()
                cat_sum = m_df.groupby("項目")['金額'].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).to_dict()

                mc_tot, mc1, mc2, mc3 = st.columns(4)
                mc_tot.metric(f"💎 {selected_month} 總計", f"${total_sum:,}")
                mc1.metric("4點前", f"${cat_sum.get('4點前課輔', 0):,}")
                mc2.metric("4點後", f"${cat_sum.get('4點後課輔', 0):,}")
                mc3.metric("學扶", f"${cat_sum.get('學扶', 0):,}")

                st.dataframe(m_df[["日期", "項目", "金額"]].reset_index(drop=True), use_container_width=True)
                
                if st.button("🗑️ 刪除最新一筆紀錄"):
                    st.session_state.salary_df = st.session_state.salary_df.drop(st.session_state.salary_df.index[-1])
                    st.session_state.has_unsaved = True
                    st.rerun()

if is_admin:
    st.sidebar.divider()
    with st.sidebar.expander("🗑️ 快速清理作業 (危險區)"):
        target = st.selectbox("選取要刪除的作業", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
        if st.button("確認刪除") and target != "請選擇":
            st.session_state.main_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
            st.session_state.has_unsaved = True
            st.rerun()
