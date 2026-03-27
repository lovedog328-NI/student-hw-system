import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記系統-進階管理版", layout="wide")

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

# --- 2. 雲端讀寫核心 (帶自動排序) ---
def load_from_cloud():
    try:
        csv_url = st.secrets["google_sync"]["sheet_csv_url"]
        df_raw = pd.read_csv(f"{csv_url}&cache_bust={time.time()}")
        if len(df_raw) > 0:
            last_content = df_raw.iloc[-1, -1] 
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            # --- 自動排序邏輯 ---
            # 先按「作業名稱」排序，再按「座號」排序，讓相同作業排在一起
            df = df.sort_values(by=["作業名稱", "座號"], ascending=[True, True])
            return df
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_to_cloud(df):
    try:
        # 存檔前也排一次序，確保雲端備份整齊
        df = df.sort_values(by=["作業名稱", "座號"], ascending=[True, True])
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str})
        return True
    except:
        return False

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_from_cloud()

# --- 3. 介面 ---
st.title("🍎 303作業登記 (自動排序版)")

menu = st.sidebar.selectbox("切換功能", ["學生查詢", "老師管理後台"])

if menu == "學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.success(f"你好，{res.iloc[0]['姓名']} 同學")
            display = res[res["繳交狀態"] != "已繳交"]
            if display.empty:
                st.balloons(); st.info("✨ 全部作業都交齊囉！")
            else:
                st.write("📋 待處理作業：")
                st.table(display[["作業名稱", "繳交狀態", "更新日期"]])
        else:
            st.info("尚無紀錄。")

elif menu == "老師管理後台":
    pwd = st.text_input("管理員密碼", type="password")
    if pwd == "alice":
        st.success("身分驗證成功")

        # --- 新功能：作業缺交名單快速看 ---
        with st.expander("🔍 快速查看作業缺交名單", expanded=True):
            if not st.session_state.main_df.empty:
                all_hw = st.session_state.main_df["作業名稱"].unique()
                target_hw = st.selectbox("選擇作業名稱：", all_hw)
                
                if target_hw:
                    hw_data = st.session_state.main_df[st.session_state.main_df["作業名稱"] == target_hw]
                    # 篩選未繳交與需訂正
                    missing = hw_data[hw_data["繳交狀態"] != "已繳交"]
                    
                    if missing.empty:
                        st.balloons(); st.success(f"🎊 太讚了！『{target_hw}』全班都交齊了！")
                    else:
                        st.warning(f"以下為『{target_hw}』尚未完成的名單：")
                        # 整理成好讀的字串
                        missing_list = [f"{row['座號']}.{row['姓名']}({row['繳交狀態']})" for _, row in missing.iterrows()]
                        st.write("、".join(missing_list))
                        
                        # 進階：顯示未交總人數
                        st.info(f"目前尚有 **{len(missing)}** 人未完成。")
            else:
                st.info("目前尚無任何作業紀錄。")

        # --- A. 快速補交 ---
        with st.expander("🎯 學生補交/訂正快速按鈕"):
            tid = st.text_input("輸入座號快速補交：", key="tid")
            if tid:
                df = st.session_state.main_df
                s_todo = df[(df["座號"].astype(str) == str(tid)) & (df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    st.write(f"學生：**{s_todo.iloc[0]['姓名']}**")
                    for idx, row in s_todo.iterrows():
                        if st.button(f"✅ 完成：{row['作業名稱']}", key=f"f_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df)
                            st.toast("同步成功！")
                            st.rerun()
                else:
                    st.info("該生目前沒有欠交作業。")

        # --- B. 新增整班作業 ---
        with st.expander("📝 新增整班作業登記"):
            hw = st.text_input("輸入作業名稱 (例如: 國 L2)")
            if hw:
                if 'tmp' not in st.session_state or st.session_state.get('last_hw') != hw:
                    st.session_state.tmp = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw = hw
                
                st.write("點選切換：灰色=已交 / 藍色=未交 / 深藍=訂正")
                cols = st.columns(2)
                for i, s in enumerate(STUDENT_LIST):
                    sid, name = s['座號'], s['姓名']
                    curr = st.session_state.tmp[sid]
                    if cols[i%2].button(f"{sid}. {name} ({curr})", key=f"b_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "未繳交" if curr == "已繳交" else "需訂正" if curr == "未繳交" else "已繳交"
                        st.rerun()

                if st.button("💾 確定儲存並同步至雲端", type="primary"):
                    new_rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    # 合併並自動排序
                    updated_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.session_state.main_df = updated_df
                    if save_to_cloud(updated_df):
                        st.success("✅ 儲存成功！資料已同步。")
                        st.balloons()
                    st.rerun()

        # --- C. 管理歷史紀錄 ---
        with st.expander("📊 歷史總表管理"):
            st.write("所有紀錄已自動依『作業名稱』分類排序：")
            st.dataframe(st.session_state.main_df, use_container_width=True)
            if st.button("🔄 強制刷新雲端資料"):
                st.session_state.main_df = load_from_cloud()
                st.rerun()
