import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記系統-即時修改版", layout="wide")

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
        df_raw = pd.read_csv(f"{csv_url}&cache_bust={time.time()}")
        if len(df_raw) > 0:
            last_content = df_raw.iloc[-1, -1] 
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            df = df.sort_values(by=["作業名稱", "座號"])
            return df
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_to_cloud(df):
    try:
        df = df.sort_values(by=["作業名稱", "座號"])
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str})
        return True
    except:
        return False

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_from_cloud()

# --- 3. 介面設計 ---
st.title("📚 303 作業登記與即時修改")

# 側邊欄：老師身分標記（用來決定是否顯示修改按鈕）
is_admin = st.sidebar.checkbox("老師管理模式 (開啟後可直接修改狀態)")
if is_admin:
    pwd = st.sidebar.text_input("輸入管理密碼", type="password")
    if pwd != "alice":
        st.sidebar.warning("密碼錯誤，僅供查詢")
        is_admin = False

menu = st.sidebar.selectbox("切換功能", ["學生查詢 / 即時補交", "老師管理後台"])

# --- 功能 A：查詢與即時修改 ---
if menu == "學生查詢 / 即時補交":
    st.header("🔍 學生作業進度")
    sid = st.text_input("輸入座號 (1-22)：", placeholder="例如: 5")
    
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 同學的作業清單")
            
            # 篩選未完成的作業
            todo = res[res["繳交狀態"] != "已繳交"]
            
            if todo.empty:
                st.balloons()
                st.success("✨ 太棒了！目前沒有欠交的作業。")
            else:
                st.warning(f"還有 {len(todo)} 項作業待處理：")
                
                # 建立即時修改列表
                for idx, row in todo.iterrows():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    col1.write(f"📌 **{row['作業名稱']}**")
                    col2.write(f"狀態：`{row['繳交狀態']}`")
                    
                    # 如果是管理模式，顯示修改按鈕
                    if is_admin:
                        if col3.button(f"✅ 改為已完成", key=f"edit_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df)
                            st.toast(f"已更新 {name} 的 {row['作業名稱']}")
                            time.sleep(1)
                            st.rerun()
                    else:
                        col3.write(f"📅 {row['更新日期']}")
            
            # 顯示已完成作業（摺疊區）
            with st.expander("查看已完成作業"):
                done = res[res["繳交狀態"] == "已繳交"]
                st.table(done[["作業名稱", "更新日期"]])
        else:
            st.info("目前尚無此座號的登記紀錄。")

# --- 功能 B：老師管理後台 ---
elif menu == "老師管理後台":
    if is_admin:
        st.header("👨‍🏫 全班進度管理")
        
        # 1. 缺交名單摘要
        with st.expander("🔍 快速查看各項作業缺交名單", expanded=True):
            if not st.session_state.main_df.empty:
                all_hw = st.session_state.main_df["作業名稱"].unique()
                target_hw = st.selectbox("選擇作業：", all_hw)
                missing = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == target_hw) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if missing.empty:
                    st.success("全班均已繳交！")
                else:
                    st.write("、".join([f"{r['座號']}.{r['姓名']}({r['繳交狀態']})" for _, r in missing.iterrows()]))
            else:
                st.info("尚無紀錄")

        # 2. 新增作業
        with st.expander("📝 新增整班作業"):
            hw_name = st.text_input("新作業名稱 (如: 數習 P.10)")
            if hw_name:
                if 'temp_status' not in st.session_state or st.session_state.get('last_hw_name') != hw_name:
                    st.session_state.temp_status = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.last_hw_name = hw_name
                
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    curr = st.session_state.temp_status[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']}\n({curr})", key=f"btn_{sid}", use_container_width=True):
                        st.session_state.temp_status[sid] = "未繳交" if curr == "已繳交" else "需訂正" if curr == "未繳交" else "已繳交"
                        st.rerun()
                
                if st.button("🚀 儲存並同步到雲端", type="primary", use_container_width=True):
                    new_data = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_name, "繳交狀態":st.session_state.temp_status[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_data)], ignore_index=True)
                    save_to_cloud(st.session_state.main_df)
                    st.success("存檔成功！")
                    st.rerun()
    else:
        st.warning("請先在左側開啟『老師管理模式』並輸入正確密碼。")
