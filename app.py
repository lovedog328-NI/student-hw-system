import streamlit as st
import pandas as pd
import os
from datetime import date
import io

st.set_page_config(page_title="作業快速登記系統", layout="wide")

# --- 管理員設定 ---
ADMIN_PASSWORD = "alice" 
DATA_FILE = "homework_data.csv"

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

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, dtype={'座號': str})
    else:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

st.sidebar.title("🛠️ 選單")
menu = st.sidebar.selectbox("切換功能", ["學生查詢中心", "老師管理後台"])

# --- 學生查詢中心 ---
if menu == "學生查詢中心":
    st.header("🔍 學生個人查詢")
    search_id = st.text_input("輸入座號 (1-22)：")
    if search_id:
        result = df[df["座號"].astype(str) == str(search_id)]
        if not result.empty:
            st.success(f"你好，{result.iloc[0]['姓名']} 同學")
            show_all = st.checkbox("顯示所有紀錄", value=False)
            display_df = result if show_all else result[result["繳交狀態"].isin(["未繳交", "需訂正"])]
            if display_df.empty:
                st.balloons(); st.info("✨ 目前沒有待處理作業。")
            else:
                st.table(display_df[["作業名稱", "繳交狀態", "更新日期"]].sort_values(by="更新日期", ascending=False))
        else:
            st.info("尚無紀錄。")

# --- 老師管理後台 ---
elif menu == "老師管理後台":
    st.header("👨‍🏫 老師管理區")
    pwd_input = st.sidebar.text_input("管理員密碼", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        # --- A. 快速補交區 ---
        with st.expander("🎯 學生補交/訂正快速按鈕", expanded=True):
            check_sid = st.text_input("輸入學生座號：", key="quick_check")
            if check_sid:
                s_todo = df[(df["座號"].astype(str) == str(check_sid)) & (df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    st.write(f"學生：**{s_todo.iloc[0]['姓名']}**")
                    for idx, row in s_todo.iterrows():
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"📌 {row['作業名稱']} (目前：{row['繳交狀態']})")
                        if c2.button("✅ 點擊設為已完成", key=f"fix_{idx}"):
                            df.at[idx, "繳交狀態"] = "已繳交"
                            df.at[idx, "更新日期"] = str(date.today())
                            save_data(df); st.rerun()
                else:
                    st.info("該生無欠交或需訂正作業。")

        # --- B. 新增整班作業 (按鈕型) ---
        with st.expander("📝 新增整班作業登記 (按鈕切換)", expanded=False):
            hw_name = st.text_input("輸入新作業名稱")
            hw_date = st.date_input("日期", date.today())
            
            if hw_name:
                st.write("請點選『缺交』或『需訂正』的同學：")
                
                # 初始化這次作業的暫存狀態 (Session State)
                if 'temp_hw' not in st.session_state or st.session_state.get('last_hw') != hw_name:
                    st.session_state.temp_hw = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw = hw_name

                # 建立 22 個學生的按鈕矩陣
                for s in STUDENT_LIST:
                    sid = s['座號']
                    name = s['姓名']
                    current_status = st.session_state.temp_hw[sid]
                    
                    # 根據狀態決定顏色
                    btn_type = "secondary" if current_status == "已繳交" else "primary"
                    label = f"{sid}. {name}：【{current_status}】"
                    
                    if st.button(label, key=f"btn_hw_{sid}", use_container_width=True):
                        # 狀態循環切換
                        if current_status == "已繳交": st.session_state.temp_hw[sid] = "未繳交"
                        elif current_status == "未繳交": st.session_state.temp_hw[sid] = "需訂正"
                        else: st.session_state.temp_hw[sid] = "已繳交"
                        st.rerun()

                if st.button("💾 確認並儲存整班記錄", type="primary"):
                    new_rows = []
                    for s in STUDENT_LIST:
                        new_rows.append({
                            "座號": s['座號'], "姓名": s['姓名'], 
                            "作業名稱": hw_name, "繳交狀態": st.session_state.temp_hw[s['座號']], 
                            "更新日期": str(hw_date)
                        })
                    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                    save_data(df)
                    st.success("存檔成功！")
                    st.balloons()

        # --- C. 歷史總表 ---
        with st.expander("📊 歷史紀錄與刪除"):
            if not df.empty:
                all_edit = st.data_editor(df, num_rows="dynamic")
                if st.button("💾 儲存表格修改"):
                    save_data(all_edit); st.success("已更新！"); st.rerun()
                
                hw_list = df["作業名稱"].unique()
                target = st.selectbox("選取要刪除的整筆作業", hw_list)
                if st.button(f"❌ 確定刪除『{target}』"):
                    df = df[df["作業名稱"] != target]; save_data(df); st.rerun()