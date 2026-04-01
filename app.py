import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-穩定版", layout="wide")
st.title("📚 303 作業登記系統 (雲端同步穩定版)")

# 固定學生名單
STUDENT_LIST = [
    {"座號": str(i), "姓名": n} for i, n in enumerate([
        "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
        "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言",
        "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
    ], 1)
]

# --- 2. 建立 Google Sheets 連接 ---
# 這裡使用官方連接器，雖然慢，但讀取的是整張表，非常安全
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """從 Google Sheets 讀取整張表，並進行清理"""
    try:
        # 使用最乾淨的網址
        url = "https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/edit"
        df = conn.read(
            spreadsheet=url,
            worksheet="Sheet1",
            ttl=0
        )
        
        # 檢查是否讀到空表
        if df is None or df.empty:
            return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
            
        # 清理並確保座號是字串
        df = df.dropna(how="all") # 刪除全空的列
        if not df.empty:
            df["座號"] = df["座號"].astype(str)
        return df
    except Exception as e:
        # 如果是初次建立或網路問題，回傳空表不崩潰
        st.sidebar.warning("💡 提示：若雲端無資料，請先由老師後台『新增作業』。")
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_data(df):
    """將目前的資料完整寫回 Google Sheets"""
    try:
        conn.update(
            # 請將程式碼中這兩處的網址改為：
spreadsheet="https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/edit"
            worksheet="Sheet1",
            data=df
        )
        st.cache_data.clear() # 清除快取
        return True
    except Exception as e:
        st.error(f"儲存失敗，請檢查網路: {e}")
        return False

# 初始化資料 (Session State)
if 'main_df' not in st.session_state:
    with st.spinner("正在安全讀取雲端資料庫..."):
        st.session_state.main_df = load_data()

# --- 3. 側邊欄控制 ---
st.sidebar.title("🔐 管理模式")
pwd = st.sidebar.text_input("輸入密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 強制同步雲端 (資料對不上時點我)"):
    st.session_state.main_df = load_data()
    st.rerun()

menu = st.sidebar.radio("切換功能", ["🔍 學生查詢區", "🛠️ 老師管理後台"])

# 更新函式
def update_status(idx, new_status):
    st.session_state.main_df.at[idx, "繳交狀態"] = new_status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    with st.spinner("正在同步至雲端..."):
        if save_data(st.session_state.main_df):
            st.toast("✅ 資料已安全存入雲端")
            time.sleep(0.5)
            st.rerun()

# --- 4. 介面實作 ---

# [學生查詢]
if menu == "🔍 學生查詢區":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        
        if res.empty:
            st.info("目前雲端尚無你的登記紀錄。")
        else:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的作業清單")
            unfilled = res[res["繳交狀態"] != "已繳交"]
            
            if unfilled.empty:
                st.balloons()
                st.success("🎊 恭喜！目前沒有欠交作業，太棒了！")
            else:
                for idx, row in unfilled.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=update_status, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=update_status, args=(idx, "需訂正"))
            
            with st.expander("查看已完成紀錄"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

# [老師後台]
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("⚠️ 請輸入正確密碼以進入管理模式。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        
        with tab1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 全班皆已交齊！")
                for i, r in m.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    cb.button("已交", key=f"t1_d_{i}", on_click=update_status, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t1_r_{i}", on_click=update_status, args=(i, "需訂正"))

        with tab3:
            st.subheader("新增班級作業")
            nhw = st.text_input("作業名稱 (例如：數習 p.42)：")
            if st.button("🚀 確認發佈 (預設全班未交)"):
                new_rows = []
                for s in STUDENT_LIST:
                    new_rows.append({
                        "座號": s['座號'], "姓名": s['姓名'],
                        "作業名稱": nhw, "繳交狀態": "未繳交",
                        "更新日期": str(date.today())
                    })
                new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                with st.spinner("正在建立全班紀錄，請勿關閉視窗..."):
                    if save_data(new_df):
                        st.session_state.main_df = new_df
                        st.success("發佈成功！")
                        st.rerun()

        st.sidebar.divider()
        with st.sidebar.expander("🗑️ 刪除舊作業"):
            target = st.selectbox("選擇刪除項", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("執行刪除"):
                new_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
                save_data(new_df)
                st.session_state.main_df = new_df
                st.rerun()
