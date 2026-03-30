import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

# 1. 這是最優先執行的，確保標題一定會出現
st.set_page_config(page_title="303作業登記", layout="wide")
st.title("📚 303 作業登記系統 (診斷模式)")

# 2. 測試 Secrets 是否正常 (如果這行報錯，畫面就會變白)
try:
    TEST_URL = st.secrets["google_sync"]["form_url"]
    st.sidebar.success("✅ Secrets 讀取正常")
except Exception as e:
    st.error(f"❌ Secrets 設定有誤: {e}")
    st.stop() # 停止執行，避免畫面留白

# --- 3. 核心邏輯 (回溯搜尋版) ---
def load_data():
    try:
        # 強制破解快取抓取最新 CSV
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&t={int(time.time())}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            # 如果試算表是空的，我們會看到這一行
            if df_raw.empty:
                st.info("💡 目前雲端資料庫是空的，請先新增一筆作業。")
                return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
            
            # 從最後一列往前找
            for _, row in df_raw.iloc[::-1].iterrows():
                content = str(row.iloc[-1])
                if "座號" in content and "作業名稱" in content:
                    df = pd.read_csv(io.StringIO(content), dtype={'座號': str})
                    if not df.empty and "座號" in df.columns:
                        df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                        df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                        return df.reset_index(drop=True)
    except Exception as e:
        st.sidebar.error(f"⚠️ 雲端讀取超時或失敗: {e}")
        
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# 初始化 (這裡加上 st.spinner 讓你知道它在跑)
if 'main_df' not in st.session_state:
    with st.spinner('正在從雲端同步資料...'):
        st.session_state.main_df = load_data()

# --- 4. 其餘介面代碼 (請接續之前的選單與管理後台代碼) ---
# ... (這裡放你原本的 sidebar.selectbox 和 is_admin 邏輯)
