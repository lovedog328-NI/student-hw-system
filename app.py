import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-家長通知版", layout="wide")
st.title("📚 303 作業登記系統")

# 固定學生名單
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate(["王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙", "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言", "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"], 1)]
NAME_MAP = {s['座號']: s['姓名'] for s in STUDENT_LIST}

# --- 2. 核心資料邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty:
            st.warning("雲端目前無資料，請先至後台新增作業。")
            return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
        # 修復座號格式
        df["座號"] = pd.to_numeric(df["座號"], errors='coerce').fillna(0).astype(int).astype(str)
        df = df[df["座號"] != "0"]
        return df
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        return True
    except Exception as e:
        st.error(f"雲端儲存失敗: {e}")
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. UI 介面 ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 同步最新資料"):
    st.session_state.main_df = load_data()
    st.rerun()

menu = st.sidebar.radio("功能", ["🔍 學生查詢與列印", "🛠️ 老師管理後台"])

def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_data(st.session_state.main_df)
    st.toast(f"✅ 已更新")

# --- 4. 介面實作 ---

if menu == "🔍 學生查詢與列印":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的作業狀況")
            
            # 整理積欠作業
            todo = res[res["繳交狀態"] != "已繳交"]
            
            if todo.empty:
                st.balloons()
                st.success(f"🎊 恭喜 {name}！目前沒有任何缺交作業，家長很放心！")
            else:
                # 顯示目前積欠
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    color = "red" if row['繳交狀態'] == "未繳交" else "orange"
                    c2.markdown(f"狀態：:{color}[**{row['繳交狀態']}**]")
                    if is_admin:
                        c3.button("已交", key=f"q_d_{idx}", on_click=update_status, args=(idx, "已繳交"))
                        c4.button("訂正", key=f"q_r_{idx}", on_click=update_status, args=(idx, "需訂正"))

                # --- 🖨️ 自動整理成列印清單 ---
                st.divider()
                st.subheader("🖨️ 家長通知單生成器")
                
                # 準備要印出的表格內容
                print_df = todo[["作業名稱", "繳交狀態", "更新日期"]].copy()
                print_df.columns = ["積欠項目", "目前狀態", "最後檢查日期"]
                
                # 產生文字版清單（方便家長閱讀）
                report_text = f"【303班 作業催繳通知單】\n"
                report_text += f"學生姓名：{name}  座號：{sid}\n"
                report_text += f"製表日期：{date.today()}\n"
                report_text += "-"*30 + "\n"
                for _, row in print_df.iterrows():
                    report_text += f"□ {row['積欠項目']} ({row['目前狀態']})\n"
                report_text += "-"*30 + "\n"
                report_text += "請家長督促孩子完成後，於聯絡簿簽名。謝謝配合！"

                st.text_area("預覽通知單內容", report_text, height=200)
                
                # 提供下載按鈕
                st.download_button(
                    label="📥 下載通知單 (TXT檔)",
                    data=report_text,
                    file_name=f"303班_{sid}_{name}_作業通知單.txt",
                    mime="text/plain"
                )

elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請輸入正確密碼。")
    else:
        # (後台代碼保持不變...)
        tab1, tab2, tab3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        # ... (這裡省略重複的後台代碼，您可以直接沿用之前的版本)
