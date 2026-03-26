import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="作業快速登記系統", layout="wide")
@st.cache_resource
def get_global_data():
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
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

st.sidebar.header("控制面板")
menu = st.sidebar.selectbox("切換功能", ["學生查詢中心", "老師管理後台"])

# --- 學生查詢中心 ---
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
                st.info("✨ 目前沒有待處理作業，太棒了！")
            else:
                st.table(display_df[["作業名稱", "繳交狀態", "更新日期"]].sort_values(by="更新日期", ascending=False))
        else:
            st.info("目前尚無你的繳交紀錄。")

# --- 老師管理後台 ---
elif menu == "老師管理後台":
    st.header("👨‍🏫 老師管理區")
    pwd_input = st.text_input("請輸入管理員密碼", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        st.success("身分驗證成功")
        st.divider()

        # A. 快速補交/訂正
        with st.expander("🎯 學生補交/訂正快速按鈕", expanded=True):
            check_sid = st.text_input("輸入座號快速補交：", key="quick_check")
            if check_sid:
                master_df = st.session_state.global_df
                s_todo = master_df[(master_df["座號"].astype(str) == str(check_sid)) & (master_df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    st.write(f"學生：**{s_todo.iloc[0]['姓名']}** 的待辦項目")
                    for idx, row in s_todo.iterrows():
                        col_t, col_b = st.columns([3, 1])
                        col_t.write(f"📌 {row['作業名稱']} ({row['繳交狀態']})")
                        if col_b.button(f"✅ 已完成", key=f"fix_{idx}"):
                            st.session_state.global_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.global_df.at[idx, "更新日期"] = str(date.today())
                            st.toast("更新成功！")
                            st.rerun()
                else:
                    st.info("該生目前無欠交紀錄。")

        # B. 新增整班作業
        with st.expander("📝 新增整班作業登記", expanded=False):
            hw_name = st.text_input("作業名稱 (例如: 數學習作 L1)")
            if hw_name:
                if 'temp_status' not in st.session_state or st.session_state.get('last_hw_name') != hw_name:
                    st.session_state.temp_status = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw_name = hw_name
                
                cols = st.columns(2)
                for i, s in enumerate(STUDENT_LIST):
                    sid, name = s['座號'], s['姓名']
                    curr = st.session_state.temp_status[sid]
                    if cols[i%2].button(f"{sid}. {name} ({curr})", key=f"bt_{sid}", use_container_width=True):
                        st.session_state.temp_status[sid] = "未繳交" if curr == "已繳交" else "需訂正" if curr == "未繳交" else "已繳交"
                        st.rerun()

                if st.button("🚀 儲存並發布", type="primary"):
                    new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": hw_name, "繳交狀態": st.session_state.temp_status[s['座號']], "更新日期": str(date.today())} for s in STUDENT_LIST]
                    st.session_state.global_df = pd.concat([st.session_state.global_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.balloons(); st.success("存檔成功！"); st.rerun()

        # C. 修正與刪除
        with st.expander("✏️ 單項紀錄修正與刪除", expanded=False):
            edit_sid = st.text_input("輸入座號以管理該生紀錄：", key="edit_sid")
            if edit_sid:
                student_all = st.session_state.global_df[st.session_state.global_df["座號"].astype(str) == str(edit_sid)]
                if not student_all.empty:
                    edited_df = st.data_editor(student_all, num_rows="dynamic", use_container_width=True)
                    if st.button("💾 確認修正該生資料"):
                        other_df = st.session_state.global_df[st.session_state.global_df["座號"].astype(str) != str(edit_sid)]
                        st.session_state.global_df = pd.concat([other_df, edited_df], ignore_index=True)
                        st.success("更新成功！"); st.rerun()

        # D. 匯入與備份 (新增功能)
        with st.expander("📥 資料匯入與備份管理", expanded=False):
            col_down, col_up = st.columns(2)
            
            with col_down:
                st.subheader("1. 匯出備份")
                if not st.session_state.global_df.empty:
                    towrite = io.BytesIO()
                    st.session_state.global_df.to_excel(towrite, index=False, engine='openpyxl')
                    st.download_button("📥 下載 Excel 總表", data=towrite.getvalue(), file_name=f"作業紀錄_{date.today()}.xlsx")
                else:
                    st.write("目前無資料可導出")

            with col_up:
                st.subheader("2. 匯入舊紀錄")
                uploaded_file = st.file_uploader("選擇之前的 Excel 或 CSV 檔案", type=["xlsx", "csv"])
                if uploaded_file is not None:
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            import_df = pd.read_csv(uploaded_file)
                        else:
                            import_df = pd.read_excel(uploaded_file)
                        
                        if st.button("✅ 確認覆蓋並匯入資料"):
                            st.session_state.global_df = import_df
                            st.success("資料匯入成功！")
                            st.rerun()
                    except Exception as e:
                        st.error(f"檔案讀取失敗: {e}")

            st.divider()
            if st.button("⚠️ 清空伺服器所有資料 (清空前請先下載備份)"):
                st.session_state.global_df = pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
                st.rerun()
