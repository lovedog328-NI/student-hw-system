import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-薪資與提醒版", layout="wide")
st.title("📚 303 作業登記系統")

STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

# --- 2. 核心資料邏輯 (支援多工作表) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name="Sheet1"):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.fillna("")
    except:
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except:
        return False

# 初始化 Session State
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data("Sheet1")
if 'salary_df' not in st.session_state:
    st.session_state.salary_df = load_data("Salary")
if 'reminder_df' not in st.session_state:
    st.session_state.reminder_df = load_data("Reminders")
if 'has_unsaved' not in st.session_state:
    st.session_state.has_unsaved = False
if 'selected_hw_base' not in st.session_state:
    st.session_state.selected_hw_base = "請選擇"

# --- 3. 側邊欄與存檔 ---
st.sidebar.title("⚙️ 選單與管理")
menu = st.sidebar.radio("請選擇功能：", ["📊 班級公佈欄", "🔍 個人查詢", "🛠️ 老師後台"])

st.sidebar.divider()
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if is_admin and st.session_state.has_unsaved:
    st.sidebar.error("🚨 內容已變更，請儲存！")
    if st.sidebar.button("💾 儲存所有變更至雲端", type="primary", use_container_width=True):
        save_data_to_sheet(st.session_state.main_df, "Sheet1")
        save_data_to_sheet(st.session_state.salary_df, "Salary")
        save_data_to_sheet(st.session_state.reminder_df, "Reminders")
        st.session_state.has_unsaved = False
        st.sidebar.success("✅ 全數存檔成功")
        st.rerun()

# --- 4. Callbacks ---
def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    st.session_state.has_unsaved = True

# --- 5. 主畫面 UI ---

if menu == "📊 班級公佈欄":
    st.markdown("### 🏆 目前全班未完成作業總覽")
    todo_df = st.session_state.main_df[st.session_state.main_df["繳交狀態"] != "已繳交"]
    if todo_df.empty:
        st.success("🎉 全班皆已繳交完成！")
    else:
        todo_sids = sorted(todo_df["座號"].unique(), key=lambda x: int(float(x)))
        cols = st.columns(4)
        for idx, sid in enumerate(todo_sids):
            student_data = todo_df[todo_df["座號"] == sid]
            name = student_data.iloc[0]["姓名"]
            with cols[idx % 4]:
                st.info(f"👤 {sid}. {name}")
                for _, row in student_data.iterrows():
                    color = "red" if row['繳交狀態'] == "需訂正" else "orange"
                    st.caption(f"- {row['作業名稱']} (:{color}[{row['繳交狀態']}])")

elif menu == "🔍 個人查詢":
    sid = st.text_input("輸入座號 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的待辦清單")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty: st.success("🎊 恭喜！沒有欠交作業。")
            else:
                for _, row in todo.iterrows():
                    st.write(f"📌 **{row['作業名稱']}** (:{'red' if row['繳交狀態']=='需訂正' else 'orange'}[{row['繳交狀態']}])")

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入老師密碼。")
    else:
        # 顯示當日提醒
        today_str = str(date.today())
        today_reminders = st.session_state.reminder_df[st.session_state.reminder_df["日期"] == today_str]
        if not today_reminders.empty:
            st.warning("📅 **今日提醒事項：**")
            for _, r in today_reminders.iterrows():
                st.write(f"- {r['事項']}")
            st.divider()

        tab_money, tab_remind, tab_hw, tab_new = st.tabs(["💰 薪資紀錄", "📌 提醒事項", "📋 登記成績", "📝 新增作業"])

        with tab_money:
            st.subheader("💰 薪資紀錄與計算")
            log_date = st.date_input("選擇上課日期", date.today())
            
            c1, c2, c3 = st.columns(3)
            if c1.button("4點前課輔 ($405)"):
                new_row = pd.DataFrame([{"日期": str(log_date), "項目": "4點前課輔", "金額": 405}])
                st.session_state.salary_df = pd.concat([st.session_state.salary_df, new_row], ignore_index=True)
                st.session_state.has_unsaved = True
                st.success(f"已記錄：{log_date} 4點前課輔")

            if c2.button("4點後課輔 ($480)"):
                new_row = pd.DataFrame([{"日期": str(log_date), "項目": "4點後課輔", "金額": 480}])
                st.session_state.salary_df = pd.concat([st.session_state.salary_df, new_row], ignore_index=True)
                st.session_state.has_unsaved = True
                st.success(f"已記錄：{log_date} 4點後課輔")

            if c3.button("學扶 ($405)"):
                new_row = pd.DataFrame([{"日期": str(log_date), "項目": "學扶", "金額": 405}])
                st.session_state.salary_df = pd.concat([st.session_state.salary_df, new_row], ignore_index=True)
                st.session_state.has_unsaved = True
                st.success(f"已記錄：{log_date} 學扶")

            st.divider()
            # 統計當月
            if not st.session_state.salary_df.empty:
                current_month = datetime.now().strftime("%Y-%m")
                st.session_state.salary_df["日期"] = st.session_state.salary_df["日期"].astype(str)
                month_df = st.session_state.salary_df[st.session_state.salary_df["日期"].str.contains(current_month)]
                
                total = pd.to_numeric(month_df["金額"]).sum()
                st.metric(f"📅 {current_month} 累計薪資", f"${total:,}")
                st.dataframe(month_df, use_container_width=True)
                
                if st.button("🗑️ 刪除最後一筆紀錄"):
                    st.session_state.salary_df = st.session_state.salary_df.drop(st.session_state.salary_df.index[-1])
                    st.session_state.has_unsaved = True
                    st.rerun()

        with tab_remind:
            st.subheader("📌 提醒事項管理")
            r_date = st.date_input("提醒日期", date.today(), key="remind_date")
            r_text = st.text_input("要做的事情...", placeholder="例如：收回條、帶健保卡")
            if st.button("➕ 新增提醒"):
                if r_text:
                    new_r = pd.DataFrame([{"日期": str(r_date), "事項": r_text, "狀態": "待辦"}])
                    st.session_state.reminder_df = pd.concat([st.session_state.reminder_df, new_r], ignore_index=True)
                    st.session_state.has_unsaved = True
                    st.success("提醒已排定")
                    st.rerun()

            st.divider()
            st.write("🗓️ 未來所有提醒：")
            st.dataframe(st.session_state.reminder_df.sort_values("日期"), use_container_width=True)
            if st.button("🧹 清空所有提醒"):
                st.session_state.reminder_df = pd.DataFrame(columns=["日期", "事項", "狀態"])
                st.session_state.has_unsaved = True
                st.rerun()

        with tab_hw:
            # (保留原本的作業登記邏輯，此處略過節省空間，請繼續使用原本 tab1 的程式碼)
            all_hws = list(st.session_state.main_df["作業名稱"].unique())
            hw_sel = st.selectbox("選擇作業", ["請選擇"] + all_hws)
            if hw_sel != "請選擇":
                m = st.session_state.main_df[st.session_state.main_df["作業名稱"] == hw_sel]
                for i, r in m.iterrows():
                    ca, cb, cc, cd = st.columns([2, 2, 1, 1])
                    ca.write(f"{r['座號']}. {r['姓名']}")
                    cb.write(f"狀態：{r['繳交狀態']}")
                    if cc.button("需訂正", key=f"r_{i}"): update_status(i, "需訂正"); st.rerun()
                    if cd.button("已繳交", key=f"d_{i}"): update_status(i, "已繳交"); st.rerun()

        with tab_new:
            st.subheader("📝 新增作業")
            new_hw_name = st.text_input("作業名稱")
            if st.button("🚀 發佈新作業"):
                new_data = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": new_hw_name, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_data)], ignore_index=True)
                st.session_state.has_unsaved = True
                st.success(f"已新增作業：{new_hw_name}")
