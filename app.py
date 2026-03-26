import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="班級作業登記系統", layout="wide")

# --- 1. 管理員密碼 ---
ADMIN_PASSWORD = "alice" 

# --- 2. 班級名單 (22位) ---
STUDENT_LIST = [
    {"座號": "1", "姓名": "王瑀淮"}, {"座號": "2", "姓名": "李祐嘉"},
    {"座號": "3", "姓名": "郭晁瑋"}, {"座號": "4", "姓名": "廖勇傑"},
    {"座號": "5", "姓名": "潘彥廷"}, {"座號": "6", "姓名": "郭家宇"},
    {"座號": "7", "姓名": "王悅芯"}, {"座號": "8", "姓名": "劉橙"},
    {"座號": "9", "姓名": "洪語緹"}, {"座號": "10", "姓名": "林祈平"},
    {"座號": "11", "姓名": "鄧安晴"}, {"座號": "12", "姓名": "蔣語桐"},
    {"座號": "13", "姓名": "邱薇瑀"}, {"座號": "14", "姓名": "鍾芮昕"},
    {"座號": "15", "姓名": "詹筠蓁"}, {"座號": "16", "姓名": "劉姝言"},
    {"座號": "17", "姓名": "范庭蓁"}, {"座號": "18", "姓名": "呂佳恩"},
    {"座號": "19", "姓名": "楊晨妤"}, {"座號": "20", "姓名": "劉芮安"},
    {"座號": "21", "姓名": "蔡芊芊"}, {"座號": "22", "姓名": "王楷晴"}
]

# --- 3. 雲端同步核心 (共用記憶體) ---
@st.cache_resource
def get_db():
    # 初始化一個空的資料表
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# 取得目前的資料庫
if 'main_df' not in st.session_state:
    st.session_state.main_df = get_db()

# --- 4. 介面設計 ---
st.title("📚 班級作業登記系統")

st.sidebar.header("選單")
menu = st.sidebar.selectbox("切換功能", ["學生查詢", "老師後台"])

# --- 學生查詢 ---
if menu == "學生查詢":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號 (1-22)：")
    if sid:
        df = st.session_state.main_df
        # 篩選該生資料
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.success(f"你好，{res.iloc[0]['姓名']} 同學")
            # 預設隱藏已繳交的
            show_all = st.checkbox("顯示所有紀錄", value=False)
            display_df = res if show_all else res[res["繳交狀態"].isin(["未繳交", "需訂正"])]
            
            if display_df.empty:
                st.balloons()
                st.info("✨ 太棒了！目前沒有待處理作業。")
            else:
                st.table(display_df[["作業名稱", "繳交狀態", "更新日期"]])
        else:
            st.info("目前尚無你的紀錄。")

# --- 老師後台 ---
elif menu == "老師後台":
