import streamlit as st
import pandas as pd
import requests
import io
from datetime import date

st.set_page_config(page_title="303作業登記系統-永久版", layout="wide")

# --- 1. 固定名單 ---
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

# --- 2. 雲端讀寫核心 ---
def load_from_cloud():
    try:
        csv_url = st.secrets["google_sync"]["sheet_csv_url"]
        raw_data = pd.read_csv(csv_url)
        # 取得最後一筆回覆的 json_data 欄位內容
        last_content = raw_data.iloc[-1, -1] 
        return pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
    except Exception as e:
        # 如果雲端沒資料或讀取失敗，回傳空表
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_to_cloud(df):
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str})
        return True
    except:
        return False

# 初始化載入
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_from_cloud()

# --- 3. 介面開始 ---
st.title("🍎 303作業登記 (永久存檔版)")
menu = st.sidebar.selectbox("切換功能", ["學生查詢", "老師後台"])

# --- 學生查詢介面 ---
if menu == "學生查詢":
    sid = st.text_input("輸入座號 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.success(f"你好，{res.iloc[0]['姓名']} 同學")
            show_all = st.checkbox("顯示所有紀錄", value=False)
            display = res if show_all else res[res["繳交狀態"].isin(["未繳交", "需訂正"])]
            if display.empty:
                st.balloons(); st.info("✨ 目前沒有待處理作業！")
            else:
                st.table(display[["作業名稱", "繳交狀態", "更新日期"]])
        else:
            st.info("尚無紀錄。")

# --- 老師管理介面 ---
elif menu == "老師後台":
    pwd = st.text_input("管理員密碼", type="password")
    if pwd == "alice":
        st.success("解鎖成功")
        
        # A. 快速補交
        with st.expander("🎯 學生補交快速按鈕", expanded=True):
            tid = st.text_input("輸入座號：", key="tid")
            if tid:
                df = st.session_state.main_df
                s_todo = df[(df["座號"].astype(str) == str(tid)) & (df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    st.write(f"學生：**{s_todo.iloc[0]['姓名']}**")
                    for idx, row in s_todo.iterrows():
                        if st.button(f"✅ 完成：{row['作業名稱']}", key=f"f_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df) # 同步到雲端
                            st.toast("已同步至雲端！")
                            st.rerun()
                else:
                    st.info("目前無缺交紀錄。")

        # B. 新增整班作業
        with st.expander("📝 新增整班作業", expanded=False):
            hw = st.text_input("作業名稱 (例如: 數習 L1)")
            if hw:
                if 'tmp' not in st.session_state or st.session_state.get('last_hw') != hw:
                    st.session_state.tmp = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw = hw
                
                cols = st.columns(2)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    curr = st.session_state.tmp[sid]
                    if cols[i%2].button(f"{sid}. {s['姓名']} ({curr})", key=f"b_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "未繳交" if curr == "已繳交" else "需訂正" if curr == "未繳交" else "已繳交"
                        st.rerun()

                if st.button("🚀 確定儲存並同步雲端", type="primary"):
                    new_rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    updated_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.session_state.main_df = updated_df
                    if save_to_cloud(updated_df):
                        st.balloons(); st.success("雲端儲存成功！")
                    st.rerun()

        # C. 備份
        with st.expander("📊 歷史總表與手動備份"):
            st.dataframe(st.session_state.main_df, use_container_width=True)
            if st.button("🔄 從雲端重新讀取"):
                st.session_state.main_df = load_from_cloud()
                st.rerun()
