import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import random

# --- 1. 基本設定與 🎀 可愛手帳 & 圓胖數字風 CSS ---
st.set_page_config(page_title="303作業登記-穩定防護版", layout="wide")

st.markdown("""
<style>
/* ✨ 導入字體：Kalam (一般手寫), Fredoka One (圓胖數字專用), 霞鶩文楷 (中文) */
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Kalam:wght@400;700&family=LXGW+WenKai+TC:wght@400;700&display=swap');

/* ✨ 基礎字體設定：指定所有文字區塊套用可愛字體 */
html, body, p, div, span, h1, h2, h3, h4, h5, h6, li, label, input, textarea, button, th, td, .stMarkdown {
    font-family: 'Fredoka One', 'Varela Round', 'Kalam', 'LXGW WenKai TC', 'Comic Sans MS', cursive !important;
}

/* 🛡️ 終極圖示保護機制：將所有負責顯示圖示的元件徹底隔離，強制使用系統圖示字體 */
.material-symbols-rounded, 
.material-icons, 
[data-baseweb="icon"], 
[data-baseweb="icon"] *, 
[data-testid*="Icon"], 
[data-testid*="Icon"] *, 
[data-testid*="icon"], 
[data-testid*="icon"] *, 
svg, 
svg * {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}

/* ✨ 最大標題換上可愛的粉嫩藍色 */
h1 { color: #6495ED !important; font-weight: 700 !important; letter-spacing: 1px; }

/* 其他次標題維持活潑的珊瑚橘色 */
h2, h3, h4, h5, h6 { color: #FF7F50 !important; font-weight: 700 !important; letter-spacing: 1px; }

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
.student-card:hover { transform: translateY(-5px) scale(1.02); box-shadow: 0 15px 25px rgba(255, 182, 193, 0.5); }
.student-name { margin-top: 0; margin-bottom: 15px; font-size: 1.4rem; font-weight: 700; color: #DB7093; }

/* 🎀 標籤變手帳風虛線 */
.hw-tag-red { background-color: #FFE4E1; color: #FF69B4; padding: 8px 14px; border-radius: 25px; font-size: 1.1rem; font-weight: 700; display: inline-block; margin: 5px 5px 5px 0; border: 2px dashed #FFB6C1; }
.hw-tag-orange { background-color: #FFFACD; color: #FFA500; padding: 8px 14px; border-radius: 25px; font-size: 1.1rem; font-weight: 700; display: inline-block; margin: 5px 5px 5px 0; border: 2px dashed #FFD700; }
.hw-tag-blue { background-color: #E0F7FA; color: #008B8B; padding: 8px 14px; border-radius: 25px; font-size: 1.1rem; font-weight: 700; display: inline-block; margin: 5px 5px 5px 0; border: 2px dashed #00CED1; }

/* 🎀 放大的分頁標籤，圓潤化 */
button[data-baseweb="tab"] { font-size: 1.3rem !important; font-weight: 700 !important; padding: 1rem 1.5rem !important; border-radius: 20px 20px 0 0 !important; color: #FF7F50 !important;}
button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFF0F5 !important; border-bottom: 4px solid #FF69B4 !important; }

/* 🎀 按鈕變成圓滾滾的膠囊 */
.stButton > button { font-size: 1.2rem !important; font-weight: 700 !important; padding: 0.6rem 1.5rem !important; border-radius: 30px !important; border: none !important; background-color: #FFB6C1 !important; color: white !important; box-shadow: 0 6px 10px rgba(255, 182, 193, 0.4) !important; transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;}
.stButton > button:hover { background-color: #FF69B4 !important; transform: scale(1.08) !important; box-shadow: 0 8px 15px rgba(255, 105, 180, 0.5) !important; }

/* ✨ 針對小動物積點卡片專屬設計 */
.animal-card { background-color: #ffffff; border: 3px dashed #87CEEB; border-radius: 20px; padding: 15px; text-align: center; box-shadow: 0 4px 8px rgba(135, 206, 235, 0.2); margin-bottom: 15px; position: relative; }
.animal-avatar { font-size: 3rem; line-height: 1; margin-bottom: 5px; }
.animal-name { font-size: 1.2rem; font-weight: 900; color: #4682B4; margin-bottom: 8px; }
.pt-badge { background-color: #FFFACD; border: 2px solid #FFD700; color: #DAA520; border-radius: 15px; padding: 4px 8px; font-weight: 900; font-size: 0.9rem; display: inline-block; margin: 2px; }
.card-badge { background-color: #FFE4E1; border: 2px solid #FFB6C1; color: #CD5C5C; border-radius: 15px; padding: 4px 8px; font-weight: 900; font-size: 0.9rem; display: inline-block; margin: 2px; }

/* ✨ 狀態標籤樣式：增加行高，適應多行排版 */
.status-ok { background-color: #E0FFF0; color: #2E8B57; border-radius: 10px; padding: 6px 4px; font-size: 0.85rem; font-weight: bold; margin-top: 8px; border: 1px dashed #3CB371; line-height: 1.4; }
.status-bad { background-color: #FFF0F0; color: #DC143C; border-radius: 10px; padding: 6px 4px; font-size: 0.85rem; font-weight: bold; margin-top: 8px; border: 1px dashed #CD5C5C; line-height: 1.4; }

/* 針對積點按鈕設計的專屬樣式 */
.btn-add > button { background-color: #87CEEB !important; box-shadow: 0 6px 10px rgba(135, 206, 235, 0.4) !important; }
.btn-add > button:hover { background-color: #4682B4 !important; }
.btn-sub > button { background-color: #FFA07A !important; box-shadow: 0 6px 10px rgba(255, 160, 122, 0.4) !important; }
.btn-sub > button:hover { background-color: #CD5C5C !important; }
.btn-card > button { background-color: #FFD700 !important; color: #8B4500 !important; box-shadow: 0 6px 10px rgba(255, 215, 0, 0.4) !important; }
.btn-card > button:hover { background-color: #DAA520 !important; }
.btn-rule > button { background-color: #9370DB !important; box-shadow: 0 6px 10px rgba(147, 112, 219, 0.4) !important; }
.btn-rule > button:hover { background-color: #6A5ACD !important; }
.btn-all > button { background-color: #3CB371 !important; box-shadow: 0 6px 10px rgba(60, 179, 113, 0.4) !important; }
.btn-all > button:hover { background-color: #2E8B57 !important; }
.btn-punish > button { background-color: #696969 !important; box-shadow: 0 6px 10px rgba(105, 105, 105, 0.4) !important; }
.btn-punish > button:hover { background-color: #2F4F4F !important; }
.btn-free > button { background-color: #20B2AA !important; box-shadow: 0 6px 10px rgba(32, 178, 170, 0.4) !important; }
.btn-free > button:hover { background-color: #008080 !important; }

/* 貼紙牆專用的大按鈕 */
.sticker-btn > button { font-size: 3.5rem !important; padding: 15px 0 !important; background-color: #ffffff !important; border: 2px dashed #FFB6C1 !important; color: #000 !important; box-shadow: none !important;}
.sticker-btn > button:hover { background-color: #FFF0F5 !important; transform: scale(1.1) !important; border: 2px solid #FF69B4 !important; z-index: 1; }

.contact-book-box { background-color: #F0F8FF; border-left: 12px solid #87CEEB; padding: 25px; border-radius: 20px; box-shadow: 0 8px 16px rgba(135, 206, 235, 0.2); margin-top: 20px; }
.contact-book-box h3 { margin-top: 0; color: #4682B4; font-weight: 700;}
.contact-book-box p { font-size: 1.8rem; color: #4682B4; font-weight: 700; white-space: pre-wrap; line-height: 1.6;}

[data-testid="stMetricValue"] { color: #FF69B4 !important; font-size: 2.0rem !important; overflow: visible !important; white-space: normal !important; }
[data-testid="stMetricValue"] > div { overflow: visible !important; white-space: normal !important; }
[data-testid="stMetricLabel"] { font-size: 1.2rem !important; white-space: normal !important; }

/* ✨ 抽獎專屬大按鈕 */
.btn-lottery > button { background-color: #FFD700 !important; color: #8B4500 !important; font-size: 1.8rem !important; padding: 20px !important; border-radius: 40px !important; border: 4px dashed #FFA500 !important; box-shadow: 0 10px 20px rgba(255, 215, 0, 0.5) !important; width: 100%;}
.btn-lottery > button:hover { background-color: #FFA500 !important; color: #FFF !important; transform: scale(1.05) !important; }
</style>
""", unsafe_allow_html=True)

st.title("📚 303 作業與榮譽系統 ✨")

STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

ANIMAL_EMOJIS = [
    "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", 
    "🦔", "🐸", "🐵", "🐧", "🐦", "🐥", "🦉", "🦄", "🐴", "🐢", "🐳", "🦦", "🦥",
    "🐘", "🦏", "🦛", "🐊", "🐫", "🦒", "🦘", "🦡", "🐿️", "🦇", "🦭", "🐬", 
    "🐟", "🐠", "🐡", "🦈", "🐙", "🦋", "🐛", "🐝", "🐞", "🦚", "🦜", "🦢", 
    "🦩", "🦤", "🦖", "🦕", "🦝", "🦨", "🐕", "🐈", "🐓", "🦃"
]

# ✨ 預設獎品池
DEFAULT_PRIZES = [
    {"獎品名稱": "🍬 糖果一顆", "機率權重": "100"},
    {"獎品名稱": "📝 免寫一項小作業", "機率權重": "10"},
    {"獎品名稱": "⏱️ 下課提早 3 分鐘", "機率權重": "30"},
    {"獎品名稱": "👑 榮譽小幫手一次", "機率權重": "50"}
]

def get_animal_emoji(sid):
    try:
        if 'points_df' in st.session_state and not st.session_state.points_df.empty:
            mask = st.session_state.points_df["座號"].astype(str) == str(sid)
            if mask.any():
                avatar = str(st.session_state.points_df.loc[mask, "頭像"].values[0]).strip()
                if avatar and avatar in ANIMAL_EMOJIS:
                    return avatar
        index = (int(float(sid)) - 1) % len(ANIMAL_EMOJIS)
        return ANIMAL_EMOJIS[index]
    except:
        return "🐾"

SHEET_COLUMNS = {
    "Sheet1": ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期", "已給完美卡"],
    "Salary": ["日期", "項目", "金額"],
    "Reminders": ["日期", "事項", "狀態"],
    "ContactBook": ["日期", "內容"],
    "Points": ["座號", "姓名", "總積點", "完美卡", "頭像", "懲罰結束日期"],
    "Rules": ["規定名稱", "點數"],
    "Prizes": ["獎品名稱", "機率權重"],
    "LotteryLogs": ["時間", "座號", "姓名", "獲得獎品", "狀態"]
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
        df = conn.read(worksheet=sheet_name, ttl=30)
        if df is None or df.empty:
            return pd.DataFrame(columns=expected_cols)
            
        for col in expected_cols:
            if col not in df.columns: df[col] = ""
        
        df = df.fillna("")
        df = df.astype(str).replace('nan', '')
        
        if not df.empty:
            df = df[~(df[expected_cols] == "").all(axis=1)]
        
        if not df.empty and "座號" in df.columns:
            df["座號"] = df["座號"].apply(force_int_str)

        if sheet_name == "Sheet1" and not df.empty:
            df["成績"] = df["成績"].apply(clean_score)
            df = df[df["座號"] != ""]
            for s in STUDENT_LIST:
                df.loc[df["座號"] == s["座號"], "姓名"] = s["姓名"]
        return df.reset_index(drop=True)
    except Exception as e:
        return None

def save_data_to_sheet(df, sheet_name):
    try:
        expected_cols = SHEET_COLUMNS.get(sheet_name, [])
        df_to_save = df.copy().fillna("")
        if df_to_save.empty:
            empty_row = {col: "" for col in expected_cols}
            df_to_save = pd.DataFrame([empty_row])
        else:
            if "座號" in df_to_save.columns:
                df_to_save["座號"] = df_to_save["座號"].apply(force_int_str)
            if sheet_name == "Sheet1":
                df_to_save["成績"] = df_to_save["成績"].apply(clean_score)
        conn.update(worksheet=sheet_name, data=df_to_save)
        return True
    except Exception as e:
        st.error(f"存檔發生錯誤：{e}")
        return False

# --- 3. 系統暫存初始化 ---
for key, s_name in [('main_df', 'Sheet1'), ('salary_df', 'Salary'), ('reminder_df', 'Reminders'), ('contact_df', 'ContactBook'), ('rules_df', 'Rules'), ('prizes_df', 'Prizes'), ('lottery_df', 'LotteryLogs')]:
    if key not in st.session_state: 
        res = load_data(s_name)
        st.session_state[key] = res if res is not None else pd.DataFrame(columns=SHEET_COLUMNS[s_name])

if st.session_state.prizes_df.empty:
    st.session_state.prizes_df = pd.DataFrame(DEFAULT_PRIZES)

if 'points_df' not in st.session_state: 
    temp_pdf = load_data("Points")
    if temp_pdf is not None and temp_pdf.empty:
        new_pts = [{"座號": s['座號'], "姓名": s['姓名'], "總積點": "0", "完美卡": "0", "頭像": "", "懲罰結束日期": ""} for s in STUDENT_LIST]
        st.session_state.points_df = pd.DataFrame(new_pts).astype(str)
    elif temp_pdf is not None:
        if "完美卡" not in temp_pdf.columns: temp_pdf["完美卡"] = "0"
        if "頭像" not in temp_pdf.columns: temp_pdf["頭像"] = ""
        if "懲罰結束日期" not in temp_pdf.columns: temp_pdf["懲罰結束日期"] = ""
        st.session_state.points_df = temp_pdf.astype(str)
    else:
        new_pts = [{"座號": s['座號'], "姓名": s['姓名'], "總積點": "0", "完美卡": "0", "頭像": "", "懲罰結束日期": ""} for s in STUDENT_LIST]
        st.session_state.points_df = pd.DataFrame(new_pts).astype(str)

if 'has_unsaved' not in st.session_state: st.session_state.has_unsaved = False
if 'selected_hw_base' not in st.session_state: st.session_state.selected_hw_base = "請選擇"
if "main_menu" not in st.session_state: st.session_state.main_menu = "📖 班級榮譽榜"

if "new_rem_input" not in st.session_state: st.session_state.new_rem_input = ""
if "new_hw_input" not in st.session_state: st.session_state.new_hw_input = ""
if "remind_range_val" not in st.session_state: st.session_state.remind_range_val = [date.today(), date.today() + timedelta(days=2)]
if "selected_point_sid" not in st.session_state: st.session_state.selected_point_sid = None

if "new_rule_name" not in st.session_state: st.session_state.new_rule_name = ""
if "new_rule_pt" not in st.session_state: st.session_state.new_rule_pt = 1
if "new_prize_name" not in st.session_state: st.session_state.new_prize_name = ""
if "lucky_draw_result" not in st.session_state: st.session_state.lucky_draw_result = None

if "selected_lottery_sid" not in st.session_state: st.session_state.selected_lottery_sid = None

# --- 4. Callbacks (不閃爍更新邏輯) ---
def clean_seat_input(val_str):
    res = []
    for s in val_str.replace("，", ",").split(","):
        s = s.strip()
        if s: res.append(force_int_str(s))
    return res

def mark_fast(hw_name, status, input_key, add_perfect=False):
    val = st.session_state[input_key]
    if not val: return
    sids = clean_seat_input(val)
    for sid in sids:
        mask = (st.session_state.main_df["作業名稱"] == hw_name) & (st.session_state.main_df["座號"].astype(str) == str(sid))
        
        if add_perfect:
            try:
                already_given = st.session_state.main_df.loc[mask, "已給完美卡"].values[0] == "是"
            except:
                already_given = False

            if not already_given:
                p_mask = st.session_state.points_df['座號'].astype(str) == str(sid)
                if p_mask.any():
                    idx = st.session_state.points_df.index[p_mask][0]
                    st.session_state.points_df['完美卡'] = st.session_state.points_df['完美卡'].astype(str)
                    try: curr_card = int(float(st.session_state.points_df.at[idx, '完美卡'] or 0))
                    except: curr_card = 0
                    st.session_state.points_df.at[idx, '完美卡'] = str(curr_card + 1)
                
                st.session_state.main_df.loc[mask, "已給完美卡"] = "是"

        st.session_state.main_df.loc[mask, "繳交狀態"] = status
        st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
                
    st.session_state.has_unsaved = True
    st.session_state[input_key] = "" 

def update_single_status(idx, status):
    if idx in st.session_state.main_df.index:
        st.session_state.main_df.at[idx, "繳交狀態"] = status
        st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
        st.session_state.has_unsaved = True

def update_score(idx, score_key):
    if idx in st.session_state.main_df.index:
        new_val = clean_score(st.session_state[score_key])
        if str(st.session_state.main_df.at[idx, "成績"]) != new_val:
            st.session_state.main_df.at[idx, "成績"] = new_val
            st.session_state.has_unsaved = True

def modify_points(sid, amount):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        st.session_state.points_df['總積點'] = st.session_state.points_df['總積點'].astype(str)
        try: curr = int(float(st.session_state.points_df.at[idx, '總積點'] or 0))
        except: curr = 0
        st.session_state.points_df.at[idx, '總積點'] = str(curr + amount)
        st.session_state.has_unsaved = True

def modify_perfect_card(sid, amount):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        st.session_state.points_df['完美卡'] = st.session_state.points_df['完美卡'].astype(str)
        try: curr = int(float(st.session_state.points_df.at[idx, '完美卡'] or 0))
        except: curr = 0
        st.session_state.points_df.at[idx, '完美卡'] = str(max(0, curr + amount))
        st.session_state.has_unsaved = True

def handle_card_redeem(sid):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        st.session_state.points_df['完美卡'] = st.session_state.points_df['完美卡'].astype(str)
        try: curr = int(float(st.session_state.points_df.at[idx, '完美卡'] or 0))
        except: curr = 0
        
        if curr >= 1:
            st.session_state.points_df.at[idx, '完美卡'] = str(curr - 1)
            st.session_state.has_unsaved = True
            
            if not st.session_state.prizes_df.empty:
                prizes = st.session_state.prizes_df['獎品名稱'].tolist()
                try: weights = [int(float(w)) for w in st.session_state.prizes_df['機率權重']]
                except: weights = [1] * len(prizes)
                won_prize = random.choices(prizes, weights=weights, k=1)[0]
            else:
                won_prize = "🍬 神秘小禮物"
            
            stu_name = st.session_state.points_df.at[idx, '姓名']
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_log = pd.DataFrame([{"時間": now_str, "座號": str(sid), "姓名": stu_name, "獲得獎品": won_prize, "狀態": "未領取"}])
            st.session_state.lottery_df = pd.concat([st.session_state.lottery_df, new_log], ignore_index=True)
            
            st.session_state.lucky_draw_result = {
                "sid": str(sid),
                "prize": won_prize
            }
        else:
            st.session_state.lucky_draw_result = {"error": "哎呀！完美卡數量不足，無法兌換抽獎喔！"}

def add_prize():
    p_name = st.session_state.new_prize_name.strip()
    p_weight = st.session_state.new_prize_weight
    if p_name:
        new_p = pd.DataFrame([{"獎品名稱": p_name, "機率權重": str(p_weight)}])
        st.session_state.prizes_df = pd.concat([st.session_state.prizes_df, new_p], ignore_index=True)
        st.session_state.has_unsaved = True
        st.session_state.new_prize_name = "" 

def modify_all_points(amount):
    if not st.session_state.points_df.empty:
        st.session_state.points_df['總積點'] = st.session_state.points_df['總積點'].astype(str)
        for idx in st.session_state.points_df.index:
            try: curr = int(float(st.session_state.points_df.at[idx, '總積點'] or 0))
            except: curr = 0
            st.session_state.points_df.at[idx, '總積點'] = str(curr + amount)
        st.session_state.has_unsaved = True

def modify_punishment(sid, add_days):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        st.session_state.points_df['懲罰結束日期'] = st.session_state.points_df['懲罰結束日期'].astype(str)
        today = date.today()
        
        if add_days == 0:  
            st.session_state.points_df.at[idx, '懲罰結束日期'] = ""
        else:
            curr_str = st.session_state.points_df.at[idx, '懲罰結束日期']
            try:
                curr_end = datetime.strptime(str(curr_str), '%Y-%m-%d').date()
                if curr_end < today:
                    curr_end = today - timedelta(days=1)
            except:
                curr_end = today - timedelta(days=1)
                
            new_end = curr_end + timedelta(days=add_days)
            st.session_state.points_df.at[idx, '懲罰結束日期'] = str(new_end)
            
        st.session_state.has_unsaved = True

def set_new_avatar(sid, emoji):
    mask = st.session_state.points_df['座號'].astype(str) == str(sid)
    if mask.any():
        idx = st.session_state.points_df.index[mask][0]
        st.session_state.points_df['頭像'] = st.session_state.points_df['頭像'].astype(str)
        st.session_state.points_df.at[idx, '頭像'] = str(emoji)
        st.session_state.has_unsaved = True

def set_active_student(sid):
    st.session_state.lucky_draw_result = None
    if st.session_state.selected_point_sid == sid:
        st.session_state.selected_point_sid = None
    else:
        st.session_state.selected_point_sid = sid

def on_hw_select():
    sel_str = st.session_state.hw_sel_widget
    st.session_state.selected_hw_base = sel_str.split(" (")[0] if sel_str != "請選擇" else "請選擇"

def add_reminder():
    text = st.session_state.new_rem_input.strip()
    if not text: return
    r_range = st.session_state.remind_range_val
    date_val = str(r_range[0]) if len(r_range) == 1 else f"{r_range[0]} to {r_range[1]}"
    new_r = pd.DataFrame([{"日期": date_val, "事項": text, "狀態": "待辦"}])
    st.session_state.reminder_df = pd.concat([st.session_state.reminder_df, new_r], ignore_index=True)
    st.session_state.has_unsaved = True
    st.session_state.new_rem_input = "" 

def add_homework():
    nhw = st.session_state.new_hw_input.strip()
    if not nhw: return
    new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today()), "已給完美卡": ""} for s in STUDENT_LIST]
    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
    st.session_state.has_unsaved = True
    st.session_state.new_hw_input = "" 

def add_custom_rule():
    r_name = st.session_state.new_rule_name.strip()
    r_pt = st.session_state.new_rule_pt
    if r_name:
        new_r = pd.DataFrame([{"規定名稱": r_name, "點數": str(r_pt)}])
        st.session_state.rules_df = pd.concat([st.session_state.rules_df, new_r], ignore_index=True)
        st.session_state.has_unsaved = True
        st.session_state.new_rule_name = "" 

def update_rem_range():
    st.session_state.remind_range_val = st.session_state.temp_range

def get_student_status(pt_row, main_df, sid):
    end_str = pt_row.get('懲罰結束日期', "")
    is_punished = False
    punish_text = ""
    try:
        end_date = datetime.strptime(str(end_str), '%Y-%m-%d').date()
        today = date.today()
        if end_date >= today:
            days_left = (end_date - today).days + 1
            is_punished = True
            punish_text = f"🛑罰{days_left}天禁下課"
    except:
        pass
    
    hw_df = main_df[main_df["座號"].astype(str) == str(sid)]
    not_sub_count = len(hw_df[hw_df["繳交狀態"] == "未繳交"])
    need_fix_count = len(hw_df[hw_df["繳交狀態"] == "需訂正"])
    
    status_parts = []
    if is_punished:
        status_parts.append(punish_text)
    if not_sub_count > 0:
        status_parts.append(f"🔴未交{not_sub_count}")
    if need_fix_count > 0:
        status_parts.append(f"🟠訂正{need_fix_count}")
        
    if not status_parts:
        return True, "🟢 可以下課"
    else:
        return False, "\n".join(status_parts)

def safe_update_state(key, sheet_name):
    df = load_data(sheet_name)
    if df is not None:
        st.session_state[key] = df

def set_lottery_student(sid):
    st.session_state.lucky_draw_result = None
    if st.session_state.selected_lottery_sid == str(sid):
        st.session_state.selected_lottery_sid = None
    else:
        st.session_state.selected_lottery_sid = str(sid)

# --- 5. 側邊欄 ---
st.sidebar.title("⚙️ 選單與功能")

menu = st.sidebar.radio("請選擇功能：", ["📖 班級榮譽榜", "📊 作業待辦一覽", "📓 每日聯絡簿", "🔍 個人作業查詢", "👦 班長小幫手", "🛠️ 老師專屬後台", "🎁 抽獎兌換區"], key="main_menu")

st.sidebar.divider()
pwd = st.sidebar.text_input("輸入密碼 (老師/班長專用)", type="password")

is_admin = (pwd == "alice")
is_monitor = (pwd == "303")

if is_admin or is_monitor:
    if st.session_state.has_unsaved:
        st.sidebar.error("🚨 資料尚未同步至雲端")
        if st.sidebar.button("💾 儲存並同步", type="primary", use_container_width=True):
            save_data_to_sheet(st.session_state.main_df, "Sheet1")
            save_data_to_sheet(st.session_state.salary_df, "Salary")
            save_data_to_sheet(st.session_state.reminder_df, "Reminders")
            save_data_to_sheet(st.session_state.contact_df, "ContactBook")
            save_data_to_sheet(st.session_state.points_df, "Points")
            save_data_to_sheet(st.session_state.rules_df, "Rules")
            save_data_to_sheet(st.session_state.prizes_df, "Prizes")
            save_data_to_sheet(st.session_state.lottery_df, "LotteryLogs")
            
            st.session_state.has_unsaved = False
            st.sidebar.success("✅ 已存檔")
            st.rerun()
    else:
        st.sidebar.success("✔️ 雲端資料已同步")

st.sidebar.markdown("<br><p style='font-size:0.85rem; color:#888;'>💡 提醒：為避免被 Google 阻擋，請勿一分鐘內連按更新喔！</p>", unsafe_allow_html=True)
if st.sidebar.button("🔄 重新載入最新資料"):
    if st.session_state.has_unsaved:
        st.sidebar.warning("⚠️ 您有未儲存的資料！請先點擊上方「儲存並同步」，否則資料會遺失喔！")
    else:
        st.cache_data.clear()
        st.session_state.lucky_draw_result = None
        st.session_state.selected_lottery_sid = None
        
        test_pdf = load_data("Points")
        
        if test_pdf is None:
            st.sidebar.error("🚨 讀取失敗：操作太頻繁被系統阻擋，為了保護您的資料，請等待 1 分鐘後再重試！")
        else:
            safe_update_state('main_df', 'Sheet1')
            safe_update_state('salary_df', 'Salary')
            safe_update_state('reminder_df', 'Reminders')
            safe_update_state('contact_df', 'ContactBook')
            safe_update_state('rules_df', 'Rules')
            safe_update_state('lottery_df', 'LotteryLogs')
            
            p_df = load_data("Prizes")
            if p_df is not None:
                st.session_state.prizes_df = p_df if not p_df.empty else pd.DataFrame(DEFAULT_PRIZES)
            
            if test_pdf.empty:
                new_pts = [{"座號": s['座號'], "姓名": s['姓名'], "總積點": "0", "完美卡": "0", "頭像": "", "懲罰結束日期": ""} for s in STUDENT_LIST]
                test_pdf = pd.DataFrame(new_pts).astype(str)
            else:
                if "完美卡" not in test_pdf.columns: test_pdf["完美卡"] = "0"
                if "頭像" not in test_pdf.columns: test_pdf["頭像"] = ""
                if "懲罰結束日期" not in test_pdf.columns: test_pdf["懲罰結束日期"] = ""
            
            st.session_state.points_df = test_pdf.astype(str)
            st.session_state.has_unsaved = False
            st.rerun()

# --- 6. 主畫面 UI ---

if menu == "📖 班級榮譽榜":
    st.markdown("### 🏆 303 班級榮譽榜")
    st.write("看看大家今天收集了多少點數和完美卡呢？✨")
    
    sorted_pts = st.session_state.points_df.sort_values(by="座號", key=lambda x: pd.to_numeric(x, errors='coerce'))
    
    grid_cols = st.columns(5)
    for idx, row in sorted_pts.iterrows():
        sid = row["座號"]
        name = row["姓名"]
        try: pt = int(float(row["總積點"]))
        except: pt = 0
        try: card = int(float(row.get("完美卡", 0)))
        except: card = 0
        emoji = get_animal_emoji(sid)
        
        is_ok, status_text = get_student_status(row, st.session_state.main_df, sid)
        status_class = "status-ok" if is_ok else "status-bad"
        status_html = status_text.replace('\n', '<br>')
        
        with grid_cols[idx % 5]:
            st.markdown(f'''
            <div class="animal-card">
                <div class="animal-avatar">{emoji}</div>
                <div class="animal-name">{sid}. {name}</div>
                <div>
                    <span class="pt-badge">⭐ {pt} 點</span>
                    <span class="card-badge">🎫 {card} 張</span>
                </div>
                <div class="{status_class}">{status_html}</div>
            </div>
            ''', unsafe_allow_html=True)

elif menu == "📊 作業待辦一覽":
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
                    css_class = "hw-tag-red" if row['繳交狀態'] == "需訂正" else ("hw-tag-blue" if row['繳交狀態'] == "已繳交未改" else "hw-tag-orange")
                    tags_html += f'<span class="{css_class}">{row["作業名稱"]} ({row["繳交狀態"]})</span>'
                st.markdown(f'<div class="student-card"><div class="student-name">👤 {sid}. {name}</div><div>{tags_html}</div></div>', unsafe_allow_html=True)

elif menu == "📓 每日聯絡簿":
    st.markdown("### 📓 每日聯絡簿")
    st.write("家長與小朋友們，請在這裡查看每日的交代事項喔！")
    
    view_date = st.date_input("📅 選擇要查看的日期", date.today(), key="view_cb_date")
    view_date_str = str(view_date)

    content = "老師今天還沒有發佈聯絡簿內容喔！🌿"
    if not st.session_state.contact_df.empty:
        match = st.session_state.contact_df[st.session_state.contact_df["日期"] == view_date_str]
        if not match.empty and match.iloc[0]["內容"].strip():
            content = match.iloc[0]["內容"]

    st.markdown(f'''
    <div class="contact-book-box">
        <h3>📅 {view_date_str} 聯絡事項</h3>
        <p>{content}</p>
    </div>
    ''', unsafe_allow_html=True)

elif menu == "🔍 個人作業查詢":
    sid = st.text_input("輸入座號查詢您的作業 (1-22)：", placeholder="例如：5")
    if sid:
        clean_sid = force_int_str(sid)
        res = st.session_state.main_df[st.session_state.main_df["座號"].astype(str) == str(clean_sid)]
        
        if not res.empty:
            stu_name = res.iloc[0]['姓名']
            st.markdown(f"### 👤 {stu_name} 的專屬空間")
            
            curr_avatar = get_animal_emoji(clean_sid)
            st.markdown(f"<div style='font-size: 6rem; text-align: center; margin-bottom: 20px;'>{curr_avatar}</div>", unsafe_allow_html=True)
            
            with st.expander("🐾 點擊這裡打開貼紙簿，選擇新頭像！"):
                st.markdown('<div class="sticker-btn">', unsafe_allow_html=True)
                emoji_cols = st.columns(5)
                for i, emo in enumerate(ANIMAL_EMOJIS):
                    with emoji_cols[i % 5]:
                        st.button(emo, key=f"set_emo_{clean_sid}_{i}", on_click=set_new_avatar, args=(clean_sid, emo), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.divider()
            
            res_pt = st.session_state.points_df[st.session_state.points_df["座號"].astype(str) == str(clean_sid)]
            pts, cards = 0, 0
            is_ok, status_text = True, "🟢 可以下課"
            if not res_pt.empty:
                try: pts = int(float(res_pt.iloc[0]['總積點']))
                except: pts = 0
                try: cards = int(float(res_pt.iloc[0]['完美卡']))
                except: cards = 0
                
                is_ok, status_text = get_student_status(res_pt.iloc[0], st.session_state.main_df, clean_sid)
            
            status_disp = status_text.replace('\n', ' | ')
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("🌟 目前積點", f"{pts} 點")
            mc2.metric("🎫 完美卡數量", f"{cards} 張")
            mc3.metric("🚦 目前狀態", status_disp if not is_ok else "🟢 可以下課")
            st.divider()

            st.subheader(f"📋 專屬待辦清單")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty: 
                st.success("🎊 恭喜！你目前沒有任何欠交的作業喔！")
            else:
                for _, row in todo.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"📌 **{row['作業名稱']}**")
                    color = 'red' if row['繳交狀態'] == '需訂正' else ('blue' if row['繳交狀態'] == '已繳交未改' else ('orange' if row['繳交狀態'] == '未繳交' else 'green'))
                    cb.markdown(f":{color}[**{row['繳交狀態']}**]")

elif menu == "👦 班長小幫手":
    if not (is_admin or is_monitor):
        st.warning("⚠️ 這是班長專屬的秘密基地，請在左側輸入班長密碼喔！ 🤫")
    else:
        st.success("👦 歡迎班長！請在這裡協助老師收作業喔！")
        
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
            
            ungraded_key_m = f"fu_m_{target_hw}"
            st.text_input("🔵 快速標記【已交未改】(輸入座號後按 Enter 送出，例如: 1,3,5)", key=ungraded_key_m, on_change=mark_fast, args=(target_hw, "已繳交未改", ungraded_key_m, False))

            st.divider()
            
            m = st.session_state.main_df[st.session_state.main_df["作業名稱"] == target_hw]
            for i, r in m.iterrows():
                ca, cb, cc = st.columns([2, 1.5, 1])
                ca.write(f"**{r['座號']}. {r['姓名']}**")
                color = 'red' if r['繳交狀態'] == '需訂正' else ('blue' if r['繳交狀態'] == '已繳交未改' else ('orange' if r['繳交狀態'] == '未繳交' else 'green'))
                cb.markdown(f":{color}[**{r['繳交狀態']}**]")
                cc.button("收件 (未改)", key=f"u_m_{target_hw}_{i}", on_click=update_single_status, args=(i, "已繳交未改"), use_container_width=True)

elif menu == "🎁 抽獎兌換區":
    st.markdown("### 🎁 幸運大抽獎兌換區")
    st.write("🎉 歡迎來到抽獎中心！👉 **第一步：請點擊下方的頭像選擇要兌換的學生**")
    
    sorted_pts = st.session_state.points_df.sort_values(by="座號", key=lambda x: pd.to_numeric(x, errors='coerce'))
    grid_cols = st.columns(4)
    
    for idx, row in sorted_pts.iterrows():
        sid = row["座號"]
        name = row["姓名"]
        emoji = get_animal_emoji(sid)
        
        with grid_cols[idx % 4]:
            btn_text = f"{emoji} {sid}. {name}"
            btn_type = "primary" if st.session_state.selected_lottery_sid == str(sid) else "secondary"
            st.button(btn_text, key=f"lottery_stu_{sid}", on_click=set_lottery_student, args=(sid,), type=btn_type, use_container_width=True)
    
    st.divider()

    if st.session_state.selected_lottery_sid:
        sid = st.session_state.selected_lottery_sid
        name = next((s["姓名"] for s in STUDENT_LIST if str(s["座號"]) == str(sid)), "")
        emoji = get_animal_emoji(sid)
        
        stu_filter = st.session_state.points_df[st.session_state.points_df["座號"].astype(str) == str(sid)]
        if not stu_filter.empty:
            try: cards = int(float(stu_filter.iloc[0]['完美卡']))
            except: cards = 0
            
            st.markdown(f"#### 正在為 {emoji} **{name}** 進行兌換 ｜ 擁有的完美卡： **{cards}** 張")
            
            if cards >= 1:
                st.markdown('<div class="btn-lottery">', unsafe_allow_html=True)
                st.button("🎁 第二步：扣除 1 張完美卡並馬上抽獎！", on_click=handle_card_redeem, args=(sid,), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("哎呀！這名學生的完美卡數量不足，還不能抽獎喔！請繼續加油！")

        if st.session_state.lucky_draw_result:
            res = st.session_state.lucky_draw_result
            if res.get("sid") == str(sid) or "error" in res:
                if "error" in res:
                    st.error(res["error"])
                    if st.button("關閉提醒"):
                        st.session_state.lucky_draw_result = None
                        st.rerun()
                else:
                    st.balloons()
                    st.markdown(f'''
                    <div style="background: linear-gradient(135deg, #FFD700, #FF8C00); padding: 40px; border-radius: 20px; text-align: center; color: white; margin-top: 30px; box-shadow: 0 10px 30px rgba(255,140,0,0.6); animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);">
                        <h3 style="color: white !important; margin:0; font-size: 2rem;">🎉 恭喜！完美卡兌換成功！ 🎉</h3>
                        <p style="font-size: 1.5rem; margin-top: 10px;">獲得了：</p>
                        <h1 style="color: #fff !important; font-size: 4.5rem; margin: 20px 0; text-shadow: 3px 3px 6px rgba(0,0,0,0.3);">{res['prize']}</h1>
                    </div>
                    <style>
                    @keyframes popIn {{
                        0% {{ transform: scale(0.5); opacity: 0; }}
                        100% {{ transform: scale(1); opacity: 1; }}
                    }}
                    </style>
                    ''', unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # ✨ 復原為「純手動批次儲存」，移除自動存檔避免打架
                    if st.button("✅ 確認並關閉", key="close_draw", use_container_width=True):
                        st.session_state.lucky_draw_result = None
                        st.session_state.selected_lottery_sid = None
                        st.rerun()
    else:
        if st.session_state.lucky_draw_result is not None:
            st.session_state.lucky_draw_result = None

elif menu == "🛠️ 老師專屬後台":
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

        tab_remind, tab_points, tab_contact, tab1, tab2, tab_line, tab3, tab_money, tab_lottery = st.tabs(["📌 提醒", "🌟 點數與完美卡", "📖 聯絡簿", "📋 登記成績", "🎯 單生管理", "📲 LINE推播", "📝 新增作業", "💰 薪資", "🎁 抽獎管理"])
        
        with tab_remind:
            st.subheader("📌 提醒事項管理")
            st.date_input("選擇提醒期間", st.session_state.remind_range_val, key="temp_range", on_change=update_rem_range)
            
            c_input, c_btn = st.columns([4, 1])
            with c_input:
                st.text_input("輸入待辦事項... (輸入完按 Enter 或右側按鈕)", key="new_rem_input", placeholder="例如：明天要收回條喔！", on_change=add_reminder)
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True)
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

        with tab_points:
            st.subheader("🌟 點數與完美卡管理")
            
            with st.expander("📣 全班統一加減分 (一鍵套用全班)"):
                st.markdown('<div class="btn-all">', unsafe_allow_html=True)
                
                st.markdown('**✨ 全班快速加分**')
                st.markdown('<div class="btn-add">', unsafe_allow_html=True)
                ca1, ca2, ca3, ca4, ca5 = st.columns(5)
                ca1.button("➕ 1", on_click=modify_all_points, args=(1,), use_container_width=True, key="all_add_1")
                ca2.button("➕ 5", on_click=modify_all_points, args=(5,), use_container_width=True, key="all_add_5")
                ca3.button("➕ 10", on_click=modify_all_points, args=(10,), use_container_width=True, key="all_add_10")
                ca4.button("➕ 50", on_click=modify_all_points, args=(50,), use_container_width=True, key="all_add_50")
                ca5.button("➕ 100", on_click=modify_all_points, args=(100,), use_container_width=True, key="all_add_100")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('**🌧️ 全班快速扣分**')
                st.markdown('<div class="btn-sub">', unsafe_allow_html=True)
                cs1, cs2, cs3, cs4, cs5 = st.columns(5)
                cs1.button("➖ 1", on_click=modify_all_points, args=(-1,), use_container_width=True, key="all_sub_1")
                cs2.button("➖ 5", on_click=modify_all_points, args=(-5,), use_container_width=True, key="all_sub_5")
                cs3.button("➖ 10", on_click=modify_all_points, args=(-10,), use_container_width=True, key="all_sub_10")
                cs4.button("➖ 50", on_click=modify_all_points, args=(-50,), use_container_width=True, key="all_sub_50")
                cs5.button("➖ 100", on_click=modify_all_points, args=(-100,), use_container_width=True, key="all_sub_100")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("⚙️ 設定自訂班級規定 (加減分快速按鈕)"):
                rc1, rc2, rc3 = st.columns([2, 1, 1])
                rc1.text_input("規定名稱", placeholder="例：上課舉手發言", key="new_rule_name", on_change=add_custom_rule)
                rc2.number_input("點數", value=1, step=1, key="new_rule_pt", help="加分請輸入正數，扣分請輸入負數")
                
                rc3.markdown("<br>", unsafe_allow_html=True)
                rc3.button("➕ 新增規定", on_click=add_custom_rule)
                
                if not st.session_state.rules_df.empty:
                    st.markdown("#### 目前設定的規定：")
                    for i, r in st.session_state.rules_df.iterrows():
                        lc1, lc2 = st.columns([4, 1])
                        pt_val = int(float(r['點數'] or 0))
                        lc1.write(f"🔹 {r['規定名稱']} ({'+' if pt_val>0 else ''}{pt_val} 點)")
                        if lc2.button("刪除", key=f"del_r_{i}"):
                            st.session_state.rules_df = st.session_state.rules_df.drop(i).reset_index(drop=True)
                            st.session_state.has_unsaved = True
                            st.rerun()

            st.write("點選下方的學生卡片，就可以對「個別學生」進行操作喔！")
            
            sorted_pts = st.session_state.points_df.sort_values(by="座號", key=lambda x: pd.to_numeric(x, errors='coerce'))
            
            grid_cols = st.columns(4)
            for idx, row in sorted_pts.iterrows():
                sid = row["座號"]
                name = row["姓名"]
                try: pt = int(float(row["總積點"]))
                except: pt = 0
                try: card = int(float(row.get("完美卡", 0)))
                except: card = 0
                emoji = get_animal_emoji(sid)
                
                stu_filter = st.session_state.points_df[st.session_state.points_df["座號"].astype(str) == str(sid)]
                if not stu_filter.empty:
                    is_ok, _ = get_student_status(stu_filter.iloc[0], st.session_state.main_df, sid)
                else:
                    is_ok, _ = True, "🟢"
                    
                btn_status = "🟢" if is_ok else "🔴"
                
                with grid_cols[idx % 4]:
                    btn_text = f"{emoji} {sid}. {name} {btn_status}\n⭐{pt} | 🎫{card}"
                    st.button(btn_text, key=f"btn_stu_{sid}", on_click=set_active_student, args=(sid,), use_container_width=True)

            if st.session_state.selected_point_sid:
                st.divider()
                sel_sid = st.session_state.selected_point_sid
                
                stu_filter = st.session_state.points_df[st.session_state.points_df["座號"].astype(str) == str(sel_sid)]
                
                if not stu_filter.empty:
                    sel_row = stu_filter.iloc[0]
                    is_ok, status_text = get_student_status(sel_row, st.session_state.main_df, sel_sid)
                    
                    st.markdown(f"### 正在管理：{get_animal_emoji(sel_sid)} {sel_sid}. {sel_row['姓名']}  👉 {status_text.replace('\n', ' | ')}")
                    
                    if not st.session_state.rules_df.empty:
                        st.markdown("#### 📜 套用班級規定")
                        st.markdown('<div class="btn-rule">', unsafe_allow_html=True)
                        rule_cols = st.columns(4)
                        for i, r in st.session_state.rules_df.iterrows():
                            r_name = r['規定名稱']
                            r_pt = int(float(r['點數'] or 0))
                            btn_label = f"{r_name} ({'+' if r_pt>0 else ''}{r_pt})"
                            with rule_cols[i % 4]:
                                st.button(btn_label, key=f"apply_rule_{sel_sid}_{i}", on_click=modify_points, args=(sel_sid, r_pt), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("#### ⚡ 手動增減積點")
                    st.markdown('<div class="btn-add">', unsafe_allow_html=True)
                    a1, a2, a3, a4, a5 = st.columns(5)
                    a1.button("➕ 1", on_click=modify_points, args=(sel_sid, 1), use_container_width=True, key=f"add_1_{sel_sid}")
                    a2.button("➕ 5", on_click=modify_points, args=(sel_sid, 5), use_container_width=True, key=f"add_5_{sel_sid}")
                    a3.button("➕ 10", on_click=modify_points, args=(sel_sid, 10), use_container_width=True, key=f"add_10_{sel_sid}")
                    a4.button("➕ 50", on_click=modify_points, args=(sel_sid, 50), use_container_width=True, key=f"add_50_{sel_sid}")
                    a5.button("➕ 100", on_click=modify_points, args=(sel_sid, 100), use_container_width=True, key=f"add_100_{sel_sid}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="btn-sub">', unsafe_allow_html=True)
                    s1, s2, s3, s4, s5 = st.columns(5)
                    s1.button("➖ 1", on_click=modify_points, args=(sel_sid, -1), use_container_width=True, key=f"sub_1_{sel_sid}")
                    s2.button("➖ 5", on_click=modify_points, args=(sel_sid, -5), use_container_width=True, key=f"sub_5_{sel_sid}")
                    s3.button("➖ 10", on_click=modify_points, args=(sel_sid, -10), use_container_width=True, key=f"sub_10_{sel_sid}")
                    s4.button("➖ 50", on_click=modify_points, args=(sel_sid, -50), use_container_width=True, key=f"sub_50_{sel_sid}")
                    s5.button("➖ 100", on_click=modify_points, args=(sel_sid, -100), use_container_width=True, key=f"sub_100_{sel_sid}")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    st.markdown("#### 🎫 完美卡管理")
                    st.markdown('<div class="btn-card">', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    c1.button("➕ 獲得 1 張完美卡", on_click=modify_perfect_card, args=(sel_sid, 1), use_container_width=True, key=f"card_add_{sel_sid}")
                    c2.button("➖ 手動扣除 1 張 (修改用)", on_click=modify_perfect_card, args=(sel_sid, -1), use_container_width=True, key=f"card_sub_{sel_sid}")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown("#### 🛑 狀態與懲罰管理")
                    st.markdown('<div class="btn-punish">', unsafe_allow_html=True)
                    p1, p2, p3 = st.columns(3)
                    p1.button("➕ 罰 1 天禁下課", on_click=modify_punishment, args=(sel_sid, 1), use_container_width=True, key=f"punish_1_{sel_sid}")
                    p2.button("➕ 罰 3 天禁下課", on_click=modify_punishment, args=(sel_sid, 3), use_container_width=True, key=f"punish_3_{sel_sid}")
                    p3.button("➕ 罰 7 天禁下課", on_click=modify_punishment, args=(sel_sid, 7), use_container_width=True, key=f"punish_7_{sel_sid}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="btn-free">', unsafe_allow_html=True)
                    st.button("✅ 解除所有懲罰 (恢復自由)", on_click=modify_punishment, args=(sel_sid, 0), use_container_width=True, key=f"punish_0_{sel_sid}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.info("💡 操作完畢後，您可以點擊上方其他學生繼續修改，或是點選同一位學生來收起此面板。")
                else:
                    st.warning("⚠️ 哎呀！系統暫時找不到這位學生的資料。這可能是因為資料剛剛有更新。")
                    if st.button("🔄 點我重新整理"):
                        st.session_state.selected_point_sid = None
                        st.rerun()
            
            st.divider()
            with st.expander("⚠️ 危險操作區"):
                if st.button("🔄 將全班積點與完美卡歸零"):
                    st.session_state.points_df["總積點"] = "0"
                    st.session_state.points_df["完美卡"] = "0"
                    st.session_state.has_unsaved = True
                    st.session_state.selected_point_sid = None
                    st.rerun()

        with tab_contact:
            st.subheader("📖 編輯每日聯絡簿")
            cb_date = st.date_input("選擇聯絡簿日期", date.today(), key="edit_cb_date")
            cb_date_str = str(cb_date)

            existing_content = ""
            if not st.session_state.contact_df.empty:
                match = st.session_state.contact_df[st.session_state.contact_df["日期"] == cb_date_str]
                if not match.empty:
                    existing_content = match.iloc[0]["內容"]

            new_content = st.text_area("輸入聯絡簿內容 (支援多行文字)", value=existing_content, height=200, placeholder="1. 國語習作 CH5\n2. 明天記得帶彩色筆\n3. 發下學費單請家長簽收")

            if st.button("📝 儲存本日聯絡簿"):
                if not st.session_state.contact_df.empty and cb_date_str in st.session_state.contact_df["日期"].values:
                    idx = st.session_state.contact_df.index[st.session_state.contact_df["日期"] == cb_date_str].tolist()[0]
                    st.session_state.contact_df.at[idx, "內容"] = new_content
                else:
                    new_row = pd.DataFrame([{"日期": cb_date_str, "內容": new_content}])
                    st.session_state.contact_df = pd.concat([st.session_state.contact_df, new_row], ignore_index=True)

                st.session_state.has_unsaved = True
                st.success("聯絡簿已更新！記得點擊左側「💾 儲存並同步」寫入雲端喔！")

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
                c1, c2, c3, c4 = st.columns(4)
                perfect_key = f"fp_{target_hw}"
                done_key = f"fd_{target_hw}"
                ungraded_key = f"fu_{target_hw}"
                edit_key = f"fe_{target_hw}"
                
                with c1: 
                    st.text_input("🌟 完美+1，已完成", key=perfect_key, placeholder="例: 1,3", on_change=mark_fast, args=(target_hw, "已繳交", perfect_key, True))
                with c2: 
                    st.text_input("🟢 一般已繳交", key=done_key, placeholder="例: 2,4", on_change=mark_fast, args=(target_hw, "已繳交", done_key, False))
                with c3: 
                    st.text_input("🔵 已交未改", key=ungraded_key, placeholder="例: 5,6", on_change=mark_fast, args=(target_hw, "已繳交未改", ungraded_key, False))
                with c4: 
                    st.text_input("🔴 需訂正", key=edit_key, placeholder="例: 12", on_change=mark_fast, args=(target_hw, "需訂正", edit_key, False))

                st.divider()
                
                m = st.session_state.main_df[st.session_state.main_df["作業名稱"] == target_hw]
                for i, r in m.iterrows():
                    ca, cb, cc, cd, ce, cf = st.columns([1.2, 1.2, 0.8, 0.8, 0.8, 1.2])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    
                    color = 'red' if r['繳交狀態'] == '需訂正' else ('blue' if r['繳交狀態'] == '已繳交未改' else ('orange' if r['繳交狀態'] == '未繳交' else 'green'))
                    cb.markdown(f":{color}[**{r['繳交狀態']}**]")
                    
                    cc.button("訂正", key=f"r_{target_hw}_{i}", on_click=update_single_status, args=(i, "需訂正"))
                    cd.button("未改", key=f"u_{target_hw}_{i}", on_click=update_single_status, args=(i, "已繳交未改"))
                    ce.button("已交", key=f"d_{target_hw}_{i}", on_click=update_single_status, args=(i, "已繳交"))
                    
                    score_key = f"sc_{target_hw}_{i}"
                    cf.text_input("成績", value=str(r['成績']), key=score_key, label_visibility="collapsed", on_change=update_score, args=(i, score_key))

        with tab2:
            tsid = st.text_input("管理座號：", key="tsid_mgr", placeholder="輸入座號查詢...")
            if tsid:
                clean_tsid = force_int_str(tsid)
                sm = st.session_state.main_df[st.session_state.main_df["座號"].astype(str) == str(clean_tsid)]
                if not sm.empty:
                    st.markdown(f"#### 👤 學生：{sm.iloc[0]['姓名']}")
                    
                    hide_done = st.checkbox("👀 隱藏已繳交的作業", value=True, key="hide_done_cb")
                    if hide_done:
                        sm = sm[sm["繳交狀態"] != "已繳交"]
                        
                    if sm.empty:
                        st.success("🎉 太棒了！這位學生目前沒有欠交任何作業！")
                    else:
                        for i, r in sm.iterrows():
                            ra, rb, rc, rd, re = st.columns([2.5, 1.5, 0.8, 0.8, 0.8])
                            ra.write(f"📌 {r['作業名稱']}")
                            color = 'red' if r['繳交狀態'] == '需訂正' else ('blue' if r['繳交狀態'] == '已繳交未改' else ('orange' if r['繳交狀態'] == '未繳交' else 'green'))
                            rb.markdown(f":{color}[**{r['繳交狀態']}**]")
                            
                            rc.button("訂正", key=f"t2_r_{i}", on_click=update_single_status, args=(i, "需訂正"))
                            rd.button("未改", key=f"t2_u_{i}", on_click=update_single_status, args=(i, "已繳交未改"))
                            re.button("已交", key=f"t2_d_{i}", on_click=update_single_status, args=(i, "已繳交"))

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
            c_input, c_btn = st.columns([4, 1])
            with c_input:
                st.text_input("輸入新作業名稱 (輸入完按 Enter)：", key="new_hw_input", placeholder="例如：國語習作 CH5", on_change=add_homework)
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("🚀 確認發佈", on_click=add_homework)

        with tab_money:
            log_date = st.date_input("選擇上課日期", date.today())
            
            c1, c2, c3, c4 = st.columns(4)
            def add_salary(item, amount):
                new_row = pd.DataFrame([{"日期": str(log_date), "項目": item, "金額": amount}])
                st.session_state.salary_df = pd.concat([st.session_state.salary_df, new_row], ignore_index=True)
                st.session_state.has_unsaved = True
            
            if c1.button("4點前課輔 ($405)"): add_salary("4點前課輔", 405); st.success(f"已記錄：{log_date} 4點前")
            if c2.button("4點後課輔 ($480)"): add_salary("4點後課輔", 480); st.success(f"已記錄：{log_date} 4點後")
            if c3.button("學扶4點前 ($405)"): add_salary("學扶4點前", 405); st.success(f"已記錄：{log_date} 學扶4點前")
            if c4.button("學扶4點後 ($400)"): add_salary("學扶四點後", 400); st.success(f"已記錄：{log_date} 學扶4點後")
            
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
                
                cat_data = m_df.groupby("項目").agg(
                    節數=('項目', 'count'),
                    金額=('金額', lambda x: pd.to_numeric(x, errors='coerce').sum())
                ).to_dict('index')

                def get_metric_str(item_name):
                    data = cat_data.get(item_name, {'節數': 0, '金額': 0})
                    return f"{data['節數']}節 / ${data['金額']:,}"

                st.metric(f"💎 {selected_month} 總計金額", f"${total_sum:,}")
                
                m1, m2 = st.columns(2)
                m1.metric("4點前課輔", get_metric_str('4點前課輔'))
                m2.metric("4點後課輔", get_metric_str('4點後課輔'))
                
                m3, m4 = st.columns(2)
                m3.metric("學扶4點前", get_metric_str('學扶4點前'))
                m4.metric("學扶4點後", get_metric_str('學扶四點後'))

                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(m_df[["日期", "項目", "金額"]].reset_index(drop=True), use_container_width=True)
                
                if st.button("🗑️ 刪除最新一筆紀錄"):
                    st.session_state.salary_df = st.session_state.salary_df.drop(st.session_state.salary_df.index[-1])
                    st.session_state.has_unsaved = True
                    st.rerun()

        with tab_lottery:
            st.subheader("🎁 抽獎系統設定")
            st.write("您可以在這裡自由設定要給孩子們的獎品，並調整抽中的機率！")
            
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.text_input("新增獎品名稱", key="new_prize_name", placeholder="例：免死金牌")
            c2.number_input("機率權重", min_value=1, value=10, key="new_prize_weight", help="數字越大，越容易抽中喔！(例如100就比1容易抽中)")
            c3.markdown("<br>", unsafe_allow_html=True)
            c3.button("➕ 新增獎品", on_click=add_prize, use_container_width=True)

            st.divider()
            st.write("#### 🎯 目前獎品池與機率")
            if not st.session_state.prizes_df.empty:
                for i, r in st.session_state.prizes_df.iterrows():
                    ca, cb, cc = st.columns([3, 2, 1])
                    ca.write(f"🎁 **{r['獎品名稱']}**")
                    cb.write(f"權重: {r['機率權重']}")
                    if cc.button("刪除", key=f"del_prize_{i}"):
                        st.session_state.prizes_df = st.session_state.prizes_df.drop(i).reset_index(drop=True)
                        st.session_state.has_unsaved = True
                        st.rerun()
            else:
                st.info("目前沒有設定任何獎品喔！如果學生現在抽獎，只會抽到「🍬 神秘小禮物」。")

            st.divider()
            st.write("#### 📜 學生抽獎紀錄追蹤")
            if st.session_state.lottery_df.empty:
                st.info("目前還沒有學生進行過抽獎喔！")
            else:
                for i, r in reversed(list(st.session_state.lottery_df.iterrows())):
                    col1, col2 = st.columns([4, 1])
                    col1.markdown(f"🕒 {r['時間']} | **{r['座號']}. {r['姓名']}** 抽中：**{r['獲得獎品']}**")
                    
                    if r['狀態'] == "未領取":
                        if col2.button("⭕ 點此標記領取", key=f"claim_{i}", use_container_width=True):
                            st.session_state.lottery_df.at[i, "狀態"] = "已領取"
                            st.session_state.has_unsaved = True
                            st.rerun()
                    else:
                        col2.markdown("✅ :green[**已領取**]")
                            
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ 清空所有抽獎紀錄"):
                    st.session_state.lottery_df = pd.DataFrame(columns=["時間", "座號", "姓名", "獲得獎品", "狀態"])
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
