import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. 基本設定與 🎀 可愛手帳 & 圓胖數字風 CSS ---
st.set_page_config(page_title="303作業登記-穩定修復版", layout="wide")

st.markdown("""
<style>
/* ✨ 導入字體 */
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Kalam:wght@400;700&family=LXGW+WenKai+TC:wght@400;700&display=swap');

html, body, p, div, span, h1, h2, h3, h4, h5, h6, li, label, input, textarea, button, th, td, .stMarkdown {
    font-family: 'Fredoka One', 'Varela Round', 'Kalam', 'LXGW WenKai TC', 'Comic Sans MS', cursive !important;
}

/* 🛡️ 圖示保護 */
.material-symbols-rounded, .material-icons, [data-baseweb="icon"], svg {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}

/* 🎀 學生卡片樣式 */
.animal-card { background-color: #ffffff; border: 3px dashed #87CEEB; border-radius: 20px; padding: 15px; text-align: center; box-shadow: 0 4px 8px rgba(135, 206, 235, 0.2); margin-bottom: 15px; }
.animal-avatar { font-size: 3rem; }
.pt-badge { background-color: #FFFACD; border: 2px solid #FFD700; color: #DAA520; border-radius: 15px; padding: 4px 8px; font-weight: 900; font-size: 0.9rem; display: inline-block; }
.card-badge { background-color: #FFE4E1; border: 2px solid #FFB6C1; color: #CD5C5C; border-radius: 15px; padding: 4px 8px; font-weight: 900; font-size: 0.9rem; display: inline-block; }
.status-ok { background-color: #E0FFF0; color: #2E8B57; border-radius: 10px; padding: 6px 4px; font-size: 0.85rem; font-weight: bold; margin-top: 8px; border: 1px dashed #3CB371; line-height: 1.4; }
.status-bad { background-color: #FFF0F0; color: #DC143C; border-radius: 10px; padding: 6px 4px; font-size: 0.85rem; font-weight: bold; margin-top: 8px; border: 1px dashed #CD5C5C; line-height: 1.4; }

/* 貼紙牆按鈕 */
.sticker-btn > button { font-size: 3.5rem !important; padding: 15px 0 !important; background-color: #ffffff !important; border: 2px dashed #FFB6C1 !important; }
.sticker-btn > button:hover { transform: scale(1.1) !important; border: 2px solid #FF69B4 !important; }

[data-testid="stMetricValue"] { color: #FF69B4 !important; font-size: 2.0rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("📚 303 作業與榮譽系統 ✨")

STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

ANIMAL_EMOJIS = ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🦔", "🐸", "🐵", "🐧", "🐦", "🐥", "🦉", "🦄", "🐴", "🐢", "🐳", "🦦", "🦥", "🐘", "🦒", "🦘", "🐬", "🦖", "🦋", "🐝", "🐞"]

def get_animal_emoji(sid):
    try:
        if 'points_df' in st.session_state and not st.session_state.points_df.empty:
            mask = st.session_state.points_df["座號"].astype(str) == str(sid)
            if mask.any():
                avatar = str(st.session_state.points_df.loc[mask, "頭像"].values[0]).strip()
                if avatar and avatar in ANIMAL_EMOJIS: return avatar
        return ANIMAL_EMOJIS[(int(float(sid)) - 1) % len(ANIMAL_EMOJIS)]
    except: return "🐾"

SHEET_COLUMNS = {
    "Sheet1": ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期", "已給完美卡"],
    "Points": ["座號", "姓名", "總積點", "完美卡", "頭像", "懲罰結束日期"],
    "Salary": ["日期", "項目", "金額"], "Reminders": ["日期", "事項", "狀態"], "ContactBook": ["日期", "內容"], "Rules": ["規定名稱", "點數"]
}

conn = st.connection("gsheets", type=GSheetsConnection)

def force_int_str(val):
    try: return str(int(float(val)))
    except: return str(val).strip()

def clean_score(val):
    s = str(val).strip()
    if s in ["", "nan", "NaN", "None"]: return ""
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else str(f)
    except: return s

def load_data(sheet_name="Sheet1"):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        expected = SHEET_COLUMNS.get(sheet_name, [])
        if df is None or df.empty:
            df = pd.DataFrame(columns=expected)
        df = df.fillna("").astype(str).replace('nan', '')
        if "座號" in df.columns: df["座號"] = df["座號"].apply(force_int_str)
        return df.reset_index(drop=True)
    except: return pd.DataFrame(columns=SHEET_COLUMNS.get(sheet_name, []))

def save_data_to_sheet(df, sheet_name):
    try:
        df_to_save = df.copy().fillna("")
        if "座號" in df_to_save.columns: df_to_save["座號"] = df_to_save["座號"].apply(force_int_str)
        conn.update(worksheet=sheet_name, data=df_to_save)
        return True
    except: return False

# --- 初始化 ---
for key, s_name in [('main_df', 'Sheet1'), ('salary_df', 'Salary'), ('reminder_df', 'Reminders'), ('contact_df', 'ContactBook'), ('rules_df', 'Rules')]:
    if key not in st.session_state: st.session_state[key] = load_data(s_name)

if 'points_df' not in st.session_state:
    df = load_data("Points")
    if df.empty:
        df = pd.DataFrame([{"座號": s['座號'], "姓名": s['姓名'], "總積點": "0", "完美卡": "0", "頭像": "", "懲罰結束日期": ""} for s in STUDENT_LIST])
    st.session_state.points_df = df.astype(str)

if 'has_unsaved' not in st.session_state: st.session_state.has_unsaved = False
if 'selected_hw_base' not in st.session_state: st.session_state.selected_hw_base = "請選擇"
if "selected_point_sid" not in st.session_state: st.session_state.selected_point_sid = None

# --- 4. Callbacks (加入穩定性防護) ---

def mark_fast(hw_name, status, input_key, add_perfect=False):
    val = st.session_state[input_key]
    if not val: return
    sids = [force_int_str(s.strip()) for s in val.replace("，", ",").split(",") if s.strip()]
    for sid in sids:
        mask = (st.session_state.main_df["作業名稱"] == hw_name) & (st.session_state.main_df["座號"].astype(str) == str(sid))
        if mask.any():
            if add_perfect:
                try:
                    if st.session_state.main_df.loc[mask, "已給完美卡"].values[0] != "是":
                        p_mask = st.session_state.points_df['座號'].astype(str) == str(sid)
                        if p_mask.any():
                            p_idx = st.session_state.points_df.index[p_mask][0]
                            curr = int(float(st.session_state.points_df.at[p_idx, '完美卡'] or 0))
                            st.session_state.points_df.at[p_idx, '完美卡'] = str(curr + 1)
                            st.session_state.main_df.loc[mask, "已給完美卡"] = "是"
                except: pass
            st.session_state.main_df.loc[mask, "繳交狀態"] = status
            st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
    st.session_state.has_unsaved = True
    st.session_state[input_key] = ""

# ✨ 修正後的 update_score：加入索引存在檢查
def update_score(idx, score_key):
    # 🛡️ 安全檢查防線
    if idx not in st.session_state.main_df.index:
        return 
    
    new_val = clean_score(st.session_state[score_key])
    try:
        old_val = str(st.session_state.main_df.at[idx, "成績"])
        if old_val != new_val:
            st.session_state.main_df.at[idx, "成績"] = new_val
            st.session_state.has_unsaved = True
    except KeyError:
        pass

def update_single_status(idx, status):
    if idx in st.session_state.main_df.index:
        st.session_state.main_df.at[idx, "繳交狀態"] = status
        st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
        st.session_state.has_unsaved = True

def modify_points(sid, amount):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        curr = int(float(st.session_state.points_df.at[idx, '總積點'] or 0))
        st.session_state.points_df.at[idx, '總積點'] = str(curr + amount)
        st.session_state.has_unsaved = True

def modify_punishment(sid, days):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        if days == 0: st.session_state.points_df.at[idx, '懲罰結束日期'] = ""
        else:
            try: start = datetime.strptime(st.session_state.points_df.at[idx, '懲罰結束日期'], '%Y-%m-%d').date()
            except: start = date.today() - timedelta(days=1)
            if start < date.today(): start = date.today() - timedelta(days=1)
            st.session_state.points_df.at[idx, '懲罰結束日期'] = str(start + timedelta(days=days))
        st.session_state.has_unsaved = True

def set_new_avatar(sid, emoji):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        st.session_state.points_df.at[idx, '頭像'] = str(emoji)
        st.session_state.has_unsaved = True

def get_student_status(pt_row, main_df, sid):
    end_str = pt_row.get('懲罰結束日期', "")
    status_parts = []
    try:
        end_date = datetime.strptime(str(end_str), '%Y-%m-%d').date()
        if end_date >= date.today(): status_parts.append(f"🛑罰{(end_date - date.today()).days + 1}天禁下課")
    except: pass
    hw_df = main_df[main_df["座號"].astype(str) == str(sid)]
    n_sub = len(hw_df[hw_df["繳交狀態"] == "未繳交"])
    n_fix = len(hw_df[hw_df["繳交狀態"] == "需訂正"])
    if n_sub > 0: status_parts.append(f"🔴未交{n_sub}")
    if n_fix > 0: status_parts.append(f"🟠訂正{n_fix}")
    return (True, "🟢 可以下課") if not status_parts else (False, "\n".join(status_parts))

# --- UI 介面 ---
st.sidebar.title("⚙️ 選單")
menu = st.sidebar.radio("請選擇：", ["📖 榮譽榜", "🔍 作業查詢", "🛠️ 管理員後台"])
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if is_admin and st.session_state.has_unsaved:
    if st.sidebar.button("💾 儲存並同步", type="primary"):
        for k, s in [('main_df', 'Sheet1'), ('salary_df', 'Salary'), ('reminder_df', 'Reminders'), ('contact_df', 'ContactBook'), ('points_df', 'Points'), ('rules_df', 'Rules')]:
            save_data_to_sheet(st.session_state[k], s)
        st.session_state.has_unsaved = False
        st.rerun()

if menu == "📖 榮譽榜":
    st.subheader("🏆 303 榮譽榜")
    df = st.session_state.points_df.sort_values("座號", key=lambda x: pd.to_numeric(x))
    cols = st.columns(5)
    for i, row in df.iterrows():
        is_ok, txt = get_student_status(row, st.session_state.main_df, row["座號"])
        with cols[i % 5]:
            st.markdown(f'''<div class="animal-card">
                <div class="animal-avatar">{get_animal_emoji(row["座號"])}</div>
                <b>{row["座號"]}. {row["姓名"]}</b><br>
                <span class="pt-badge">⭐ {int(float(row["總積點"] or 0))}</span>
                <span class="card-badge">🎫 {int(float(row["完美卡"] or 0))}</span>
                <div class="{'status-ok' if is_ok else 'status-bad'}">{txt.replace('\n', '<br>')}</div>
            </div>''', unsafe_allow_html=True)

elif menu == "🔍 作業查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        sid = force_int_str(sid)
        st.markdown(f"### {get_animal_emoji(sid)} 座號 {sid} 的個人空間")
        with st.expander("🐾 更換頭像貼紙牆"):
            emoji_cols = st.columns(8)
            for i, emo in enumerate(ANIMAL_EMOJIS):
                with emoji_cols[i % 8]:
                    st.button(emo, key=f"emo_{sid}_{i}", on_click=set_new_avatar, args=(sid, emo))
        
        pts = st.session_state.points_df[st.session_state.points_df["座號"] == sid]
        if not pts.empty:
            c1, c2 = st.columns(2)
            c1.metric("🌟 積點", int(float(pts.iloc[0]['總積點'] or 0)))
            c2.metric("🎫 完美卡", int(float(pts.iloc[0]['完美卡'] or 0)))
        
        todo = st.session_state.main_df[(st.session_state.main_df["座號"] == sid) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
        if todo.empty: st.success("🎉 目前沒有欠交作業喔！")
        else: st.dataframe(todo[["作業名稱", "繳交狀態"]], use_container_width=True)

elif menu == "🛠️ 管理員後台":
    if not is_admin: st.warning("請在側邊欄輸入正確密碼")
    else:
        t1, t2, t3 = st.tabs(["📋 登記作業", "🌟 學生管理", "📝 新增作業"])
        with t1:
            hws = ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique())
            sel_hw = st.selectbox("選擇作業", hws)
            if sel_hw != "請選擇":
                c1, c2, c3 = st.columns(3)
                with c1: st.text_input("🌟 完美+1", key="f1", on_change=mark_fast, args=(sel_hw, "已繳交", "f1", True))
                with c2: st.text_input("🟢 已完成", key="f2", on_change=mark_fast, args=(sel_hw, "已繳交", "f2"))
                with c3: st.text_input("🔴 需訂正", key="f3", on_change=mark_fast, args=(sel_hw, "需訂正", "f3"))
                
                rows = st.session_state.main_df[st.session_state.main_df["作業名稱"] == sel_hw]
                for i, r in rows.iterrows():
                    ca, cb, cc, cd = st.columns([1, 1, 1, 1])
                    ca.write(f"{r['座號']}. {r['姓名']}")
                    cb.write(r['繳交狀態'])
                    cd.text_input("成績", value=r['成績'], key=f"s_{i}", on_change=update_score, args=(i, f"s_{i}"), label_visibility="collapsed")
                    with cc:
                        if st.button("已交", key=f"d_{i}"): update_single_status(i, "已繳交"); st.rerun()

        with t2:
            st.write("全班快速加分")
            ca, cb = st.columns(2)
            with ca:
                if st.button("全班 +1"):
                    for s in STUDENT_LIST: modify_points(s['座號'], 1)
                    st.rerun()
            tsid = st.text_input("個別管理座號：")
            if tsid:
                sid = force_int_str(tsid)
                st.markdown(f"#### 正在管理：{sid}")
                c1, c2, c3 = st.columns(3)
                with c1: st.button("罰 1 天禁下課", on_click=modify_punishment, args=(sid, 1))
                with c2: st.button("罰 3 天禁下課", on_click=modify_punishment, args=(sid, 3))
                with c3: st.button("解除懲罰", on_click=modify_punishment, args=(sid, 0))

        with t3:
            nhw = st.text_input("新作業名稱")
            if st.button("發佈作業") and nhw:
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today()), "已給完美卡": ""} for s in STUDENT_LIST]
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state.has_unsaved = True
                st.rerun()
