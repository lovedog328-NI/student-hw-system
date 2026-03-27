import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

st.set_page_config(page_title="303作業登記系統-預設未交版", layout="wide")

# --- 1. 固定學生名單 (22位) ---
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
            df['座號_int'] = df['座號'].astype(int)
            df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
            return df
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_to_cloud(df):
    try:
        df['座號_int'] = df['座號'].astype(int)
        df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str})
        return True
    except:
        return False

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_from_cloud()

# --- 3. 側邊欄 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd != "alice":
        st.sidebar.warning("密碼錯誤")
        is_admin = False
    else:
        st.sidebar.success("✅ 老師模式已啟動")

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢與即時修改", "🛠️ 老師管理後台"])

# --- 功能 A：查詢與即時修改 ---
if menu == "🔍 學生查詢與即時修改":
    st.header("🔍 學生個人作業進度查詢")
    sid = st.text_input("輸入座號 (1-22)：", placeholder="例如: 10")
    
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 同學的作業狀況")
            todo = res[res["繳交狀態"] != "已繳交"]
            
            if todo.empty:
                st.balloons(); st.success("✨ 全部作業都交齊了，好棒！")
            else:
                st.warning(f"目前尚有 {len(todo)} 項作業待處理：")
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        if c3.button("已繳交", key=f"q_done_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df)
                            st.toast("已更新為已繳交"); time.sleep(0.5); st.rerun()
                        if c4.button("需訂正", key=f"q_rev_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df)
                            st.toast("已更新為需訂正"); time.sleep(0.5); st.rerun()
                    else:
                        c3.write(f"📅 {row['更新日期']}")
            
            with st.expander("查看已完成項目"):
                done = res[res["繳交狀態"] == "已繳交"]
                st.table(done[["作業名稱", "更新日期"]])
        else:
            st.info("尚無該座號的登記資料。")

# --- 功能 B：老師管理後台 ---
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請先在左側開啟『老師管理模式』並輸入正確密碼。")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單管理", "🎯 快速補交", "📝 新增作業"])

        with t1:
            st.subheader("各項作業缺交名單管理")
            if not st.session_state.main_df.empty:
                all_hws = st.session_state.main_df["作業名稱"].unique()
                sel_hw = st.selectbox("請選擇作業名稱：", all_hws)
                if sel_hw:
                    hw_data = st.session_state.main_df[st.session_state.main_df["作業名稱"] == sel_hw]
                    missing = hw_data[hw_data["繳交狀態"] != "已繳交"]
                    if missing.empty:
                        st.success("🎉 全班均已繳交完成！")
                    else:
                        st.error(f"待補交/訂正名單 (共 {len(missing)} 人)：")
                        for idx, r in missing.iterrows():
                            mc1, mc2, mc3 = st.columns([3, 1, 1])
                            mc1.markdown(f"**{r['座號']}號 {r['姓名']}** (`{r['繳交狀態']}`)")
                            if mc2.button("已繳交", key=f"list_done_{idx}"):
                                st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                                st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                                save_to_cloud(st.session_state.main_df)
                                st.rerun()
                            if mc3.button("需訂正", key=f"list_rev_{idx}"):
                                st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                                st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                                save_to_cloud(st.session_state.main_df)
                                st.rerun()
            else:
                st.info("目前無資料。")

        with t2:
            st.subheader("依座號快速補交")
            tid = st.text_input("輸入座號：", key="back_tid")
            if tid:
                df = st.session_state.main_df
                s_miss = df[(df["座號"].astype(str) == str(tid)) & (df["繳交狀態"] != "已繳交")]
                if not s_miss.empty:
                    st.write(f"學生：**{s_miss.iloc[0]['姓名']}**")
                    for idx, row in s_miss.iterrows():
                        col_a, col_b, col_c = st.columns([3, 1, 1])
                        col_a.write(f"📌 {row['作業名稱']} (`{row['繳交狀態']}`)")
                        if col_b.button("已交", key=f"bt_d_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df)
                            st.rerun()
                        if col_c.button("訂正", key=f"bt_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_to_cloud(st.session_state.main_df)
                            st.rerun()
                else:
                    st.info("該生目前無缺交紀錄。")

        with t3:
            st.subheader("新增整班作業登記")
            hw_name = st.text_input("新作業名稱 (如: 國 L5 卷)")
            if hw_name:
                # --- 修改處：預設狀態改為「未繳交」 ---
                if 'tmp_s' not in st.session_state or st.session_state.get('last_hwn') != hw_name:
                    st.session_state.tmp_s = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.last_hwn = hw_name
                
                st.info("💡 點擊學生按鈕可切換狀態：未繳交 -> 已繳交 -> 需訂正")
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    cur = st.session_state.tmp_s[sid]
                    # 點擊循環邏輯
                    if cols[i%3].button(f"{sid}.{s['姓名']} ({cur})", key=f"t3_{sid}", use_container_width=True):
                        if cur == "未繳交":
                            st.session_state.tmp_s[sid] = "已繳交"
                        elif cur == "已繳交":
                            st.session_state.tmp_s[sid] = "需訂正"
                        else:
                            st.session_state.tmp_s[sid] = "未繳交"
                        st.rerun()
                
                if st.button("🚀 確認發佈並儲存", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_name, "繳交狀態":st.session_state.tmp_s[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                    save_to_cloud(st.session_state.main_df)
                    st.success("發佈成功！")
                    st.rerun()

        st.divider()
        if st.button("🔄 從雲端重新讀取資料"):
            st.session_state.main_df = load_from_cloud()
            st.rerun()
