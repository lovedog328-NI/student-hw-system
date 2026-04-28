import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-進階提醒版", layout="wide")

# --- 2. 核心資料邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name="Sheet1"):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.fillna("")
    except:
        return pd.DataFrame()

# 初始化 Session State (增加選單記憶 key)
if 'main_df' not in st.session_state: st.session_state.main_df = load_data("Sheet1")
if 'salary_df' not in st.session_state: st.session_state.salary_df = load_data("Salary")
if 'reminder_df' not in st.session_state: st.session_state.reminder_df = load_data("Reminders")
if 'has_unsaved' not in st.session_state: st.session_state.has_unsaved = False
if 'selected_hw_base' not in st.session_state: st.session_state.selected_hw_base = "請選擇"

# --- 3. 側邊欄 ---
st.sidebar.title("⚙️ 管理選單")

# ✨ 修正頁面跳轉：使用 key 並確保 state 被保存
menu_options = ["📊 班級公佈欄", "🔍 個人查詢", "🛠️ 老師後台"]
if "main_menu" not in st.session_state:
    st.session_state.main_menu = menu_options[0]

menu = st.sidebar.radio("請選擇功能：", menu_options, key="main_menu")

st.sidebar.divider()
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

# 存檔邏輯
if is_admin and st.session_state.has_unsaved:
    st.sidebar.error("🚨 內容已變更，請儲存！")
    if st.sidebar.button("💾 儲存所有變更", type="primary", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.main_df.fillna(""))
        conn.update(worksheet="Salary", data=st.session_state.salary_df.fillna(""))
        conn.update(worksheet="Reminders", data=st.session_state.reminder_df.fillna(""))
        st.session_state.has_unsaved = False
        st.sidebar.success("✅ 同步成功")
        st.rerun()

# --- 4. 老師後台內容 ---
if menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入老師密碼。")
    else:
        # ✨ 今日提醒顯示 (包含期間判斷)
        today = date.today()
        if not st.session_state.reminder_df.empty:
            active_rems = []
            for _, r in st.session_state.reminder_df.iterrows():
                try:
                    # 處理區間日期 (格式可能為 '2023-10-01 to 2023-10-05')
                    if " to " in str(r['日期']):
                        start_s, end_s = str(r['日期']).split(" to ")
                        start_d = datetime.strptime(start_s, '%Y-%m-%d').date()
                        end_d = datetime.strptime(end_s, '%Y-%m-%d').date()
                        if start_d <= today <= end_d and r['狀態'] != "已完成":
                            active_rems.append(r['事項'])
                    elif str(r['日期']) == str(today) and r['狀態'] != "已完成":
                        active_rems.append(r['事項'])
                except: continue
            
            if active_rems:
                st.warning(f"📅 **今日提醒：** " + " | ".join(active_rems))
                st.divider()

        tab_hw, tab_money, tab_remind, tab_new = st.tabs(["📋 登記成績", "💰 薪資紀錄", "📌 提醒事項", "📝 新增作業"])

        with tab_remind:
            st.subheader("📌 提醒事項 (支援區間與勾選)")
            
            # ✨ 改進：日期區間選擇
            r_range = st.date_input("選擇提醒期間", [date.today(), date.today() + timedelta(days=2)])
            r_text = st.text_input("輸入待辦事項...")
            
            if st.button("➕ 新增提醒紀錄"):
                if r_text:
                    # 如果選的是區間，存成字串 "YYYY-MM-DD to YYYY-MM-DD"
                    date_val = str(r_range[0]) if len(r_range) == 1 else f"{r_range[0]} to {r_range[1]}"
                    new_r = pd.DataFrame([{"日期": date_val, "事項": r_text, "狀態": "待辦"}])
                    st.session_state.reminder_df = pd.concat([st.session_state.reminder_df, new_r], ignore_index=True)
                    st.session_state.has_unsaved = True
                    st.rerun()

            st.divider()
            # ✨ 改進：可勾選清單
            if not st.session_state.reminder_df.empty:
                st.write("### 📝 待辦清單 (點擊勾選即可標記完成)")
                for idx, row in st.session_state.reminder_df.iterrows():
                    # 只顯示待辦或讓已完成的變淡
                    is_done = (row['狀態'] == "已完成")
                    col_check, col_text = st.columns([1, 10])
                    
                    with col_check:
                        # 使用 checkbox，如果勾選則更新狀態
                        checked = st.checkbox("", value=is_done, key=f"rem_{idx}")
                        if checked != is_done:
                            st.session_state.reminder_df.at[idx, "狀態"] = "已完成" if checked else "待辦"
                            st.session_state.has_unsaved = True
                            st.rerun()
                    
                    with col_text:
                        display_text = f"~~{row['事項']}~~ (完成)" if is_done else f"**{row['事項']}**"
                        st.markdown(f"{display_text}  \n*{row['日期']}*")

        with tab_hw:
            # (此處維持您原本的作業登記邏輯，加入作業選擇記憶以防止跳頁)
            all_hws = list(st.session_state.main_df["作業名稱"].unique())
            sel_hw = st.selectbox("選擇作業", ["請選擇"] + all_hws, key="hw_selector")
            # 登記邏輯... (其餘部分同前次版本)

# [其餘公佈欄與查詢頁面維持原樣]
