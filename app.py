import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="作業快速登記系統", layout="wide")

# --- 1. 管理員密碼 ---
ADMIN_PASSWORD = "alice" 

# --- 2. 固定學生名單 (22位) ---
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

# --- 3. 跨裝置同步核心 ---
@st.cache_resource
def get_global_data():
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

if 'global_df' not in st.session_state:
    st.session_state.global_df = get_global_data()

# --- 4. 介面開始 ---
st.title("📚 學生作業快速登記系統")

# 側邊欄
st.sidebar.header("控制面板")
menu = st.sidebar.selectbox("切換功能", ["學生查詢中心", "老師管理後台"])

# --- 學生查詢中心介面 ---
if menu == "學生查詢中心":
    st.header("🔍 學生個人查詢")
    search_id = st.text_input("輸入座號查詢 (1-22)：")
    if search_id:
        current_df = st.session_state.global_df
        result = current_df[current_df["座號"].astype(str) == str(search_id)]
        if not result.empty:
            st.success(f"你好，{result.iloc[0]['姓名']} 同學")
            show_all = st.checkbox("顯示所有紀錄", value=False)
            display_df = result if show_all else result[result["繳交狀態"].isin(["未繳交", "需訂正"])]
            if display_df.empty:
                st.balloons()
                st.info("✨ 目前沒有待處理作業。")
            else:
                st.table(display_df[["作業名稱", "繳交狀態", "更新日期"]])
        else:
            st.info("目前尚無你的繳交紀錄。")

# --- 老師管理後台介面 ---
elif menu == "老師管理後台":
    st.header("👨‍🏫 老師管理區")
    # 將密碼框放在主畫面明顯處，確保老師能看到
    pwd_input = st.text_input("請輸入管理員密碼以開啟功能", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        st.success("身分驗證成功，功能已解鎖！")
        st.divider()

        # A. 快速補交/訂正按鈕
        with st.expander("🎯 學生補交/訂正快速按鈕", expanded=True):
            check_sid = st.text_input("輸入要更正的學生座號：", key="quick_check")
            if check_sid:
                # 取得最新資料
                master_df = st.session_state.global_df
                s_todo = master_df[(master_df["座號"].astype(str) == str(check_sid)) & (master_df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    st.write(f"學生：**{s_todo.iloc[0]['姓名']}**")
                    for idx, row in s_todo.iterrows():
                        col_text, col_btn = st.columns([3, 1])
                        col_text.write(f"📌 {row['作業名稱']} ({row['繳交狀態']})")
                        if col_btn.button(f"✅ 設為已完成", key=f"fix_{idx}"):
                            st.session_state.global_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.global_df.at[idx, "更新日期"] = str(date.today())
                            st.rerun()
                else:
                    st.info("該生目前無欠交或需訂正作業。")

        # B. 新增整班作業
        with st.expander("📝 新增整班作業登記", expanded=False):
            hw_name = st.text_input("輸入新作業名稱 (例如: 國語 L1)")
            if hw_name:
                if 'temp_status' not in st.session_state or st.session_state.get('last_hw_name') != hw_name:
                    st.session_state.temp_status = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw_name = hw_name
                
                st.write("點選切換狀態：")
                cols = st.columns(2)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    curr = st.session_state.temp_status[sid]
                    if cols[i%2].button(f"{sid}. {s['姓名']} ({curr})", key=f"bt_{sid}", use_container_width=True):
                        if curr == "已繳交": st.session_state.temp_status[sid] = "未繳交"
                        elif curr == "未繳交": st.session_state.temp_status[sid] = "需訂正"
                        else: st.session_state.temp_status[sid] = "已繳交"
                        st.rerun()

                if st.button("💾 儲存並發布給全班", type="primary"):
                    new_records = []
                    for s in STUDENT_LIST:
                        new_records.append({
                            "座號": s['座號'], "姓名": s['姓名'], 
                            "作業名稱": hw_name, "繳交狀態": st.session_state.temp_status[s['座號']], 
                            "更新日期": str(date.today())
                        })
                    st.session_state.global_df = pd.concat([st.session_state.global_df, pd.DataFrame(new_records)], ignore_index=True)
                    st.success("同步成功！")
                    st.rerun()

        # C. 歷史總表與下載
        with st.expander("📊 歷史紀錄與備份"):
            if not st.session_state.global_df.empty:
                st.data_editor(st.session_state.global_df, use_container_width=True)
                towrite = io.BytesIO()
                st.session_state.global_df.to_excel(towrite, index=False, engine='openpyxl')
                st.download_button("📥 下載 Excel 備份", data=towrite.getvalue(), file_name="作業紀錄備份.xlsx")
                
                if st.button("⚠️ 清空所有資料庫"):
                    st.session_state.global_df = pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
                    st.rerun()
            else:
                st.info("目前尚無紀錄。")
    
    elif pwd_input == "":
        st.info("請輸入密碼以顯示老師管理功能。")
    else:
        st.error("密碼錯誤，請重新輸入。")