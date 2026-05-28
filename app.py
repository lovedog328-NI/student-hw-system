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
