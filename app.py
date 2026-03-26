import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="雲端作業登記系統", layout="wide")

# --- 基礎設定 ---
ADMIN_PASSWORD = "alice"
# 固定學生名單 (22位)
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

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def load_cloud_data():
    try:
        # 讀取雲端資料
        return conn.read(ttl=0) # ttl=0 確保每次都抓最新
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

df = load_cloud_data()

st.title("☁️ 雲端作業快速登記系統")
menu = st.sidebar.selectbox("功能選單", ["學生查詢中心", "老師管理後台"])

# --- 學生查詢中心 ---
if menu == "學生查詢中心":
    st.header("🔍 學生個人查詢")
    search_id = st.text_input("輸入座號查詢 (1-22)：")
    if search_id:
        result = df[df["座號"].astype(str) == str(search_id)]
        if not result.empty:
            st.success(f"你好，{result.iloc[0]['姓名']} 同學")
            show_all = st.checkbox("顯示所有紀錄", value=False)
            display_df = result if show_all else result[result["繳交狀態"].isin(["未繳交", "需訂正"])]
            if display_df.empty:
                st.balloons(); st.info("✨ 目前沒有待處理作業。")
            else:
                st.table(display_df[["作業名稱", "繳交狀態", "更新日期"]])
        else:
            st.info("目前尚無你的繳交紀錄。")

# --- 老師管理後台 ---
elif menu == "老師管理後台":
    st.header("👨‍🏫 老師雲端管理")
    pwd_input = st.sidebar.text_input("管理員密碼", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        # 1. 快速補交區
        with st.expander("🎯 學生補交/訂正快速按鈕", expanded=True):
            check_sid = st.text_input("輸入學生座號：")
            if check_sid:
                s_todo = df[(df["座號"].astype(str) == str(check_sid)) & (df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    for idx, row in s_todo.iterrows():
                        if st.button(f"✅ 完成：{row['作業名稱']}", key=f"fix_{idx}"):
                            df.at[idx, "繳交狀態"] = "已繳交"
                            df.at[idx, "更新日期"] = str(date.today())
                            conn.update(data=df) # 同步到雲端
                            st.success("已更新至雲端！")
                            st.rerun()
                else:
                    st.info("該生無欠交作業。")

        # 2. 新增整班作業 (按鈕式)
        with st.expander("📝 新增整班作業"):
            hw_name = st.text_input("作業名稱")
            if hw_name:
                if 'temp_hw' not in st.session_state:
                    st.session_state.temp_hw = {s['座號']: "已繳交" for s in STUDENT_LIST}
                
                cols = st.columns(2)
                for i, s in enumerate(STUDENT_LIST):
                    sid, name = s['座號'], s['姓名']
                    current = st.session_state.temp_hw[sid]
                    btn_label = f"{sid}. {name} ({current})"
                    if cols[i % 2].button(btn_label, key=f"btn_{sid}", use_container_width=True):
                        st.session_state.temp_hw[sid] = "未繳交" if current == "已繳交" else "需訂正" if current == "未繳交" else "已繳交"
                        st.rerun()

                if st.button("💾 儲存並同步至雲端", type="primary"):
                    new_data = []
                    for s in STUDENT_LIST:
                        new_data.append({"座號": s['座號'], "姓名": s['姓名'], "作業名稱": hw_name, "繳交狀態": st.session_state.temp_hw[s['座號']], "更新日期": str(date.today())})
                    updated_df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("雲端同步成功！")
                    st.balloons()