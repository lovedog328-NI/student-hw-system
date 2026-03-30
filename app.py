import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection
import time

st.set_page_config(page_title="303作業登記-全功能完整版", layout="wide")

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
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_api():
    try:
        # 使用 API 讀取最新內容
        df_raw = conn.read(ttl=0)
        if not df_raw.empty:
            last_content = df_raw.iloc[-1, -1]
            df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
            df['座號_int'] = df['座號'].astype(int)
            # 自動按作業名稱與座號排序
            return df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
    except:
        pass
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_all(df):
    st.session_state.main_df = df
    try:
        df_sorted = df.copy()
        df_sorted['座號_int'] = df_sorted['座號'].astype(int)
        df_sorted = df_sorted.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
        csv_str = df_sorted.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

# 初始化資料
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data_api()

# --- 3. 側邊欄 ---
st.sidebar.title("🔐 管理權限")
is_admin = st.sidebar.checkbox("開啟老師管理模式")
if is_admin:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == "alice":
        st.sidebar.success("✅ 老師模式已啟動")
    else:
        is_admin = False

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢 / 即時修改", "🛠️ 老師管理後台"])

# --- 功能 A：查詢與即時修改 ---
if menu == "🔍 學生查詢 / 即時修改":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號查詢 (1-22)：", key="q_sid")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業清單")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success("✨ 作業全部交齊囉！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
                    c1.write(f"📌 **{row['作業名稱']}**")
                    c2.write(f"狀態：`{row['繳交狀態']}`")
                    if is_admin:
                        if c3.button("已交", key=f"q_d_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_all(st.session_state.main_df); st.rerun()
                        if c4.button("訂正", key=f"q_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_all(st.session_state.main_df); st.rerun()
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])
        else:
            st.info("尚無該座號的登記資料。")

# --- 功能 B：老師管理後台 (三大分頁) ---
elif menu == "🛠️ 老師管理後台":
    if not is_admin:
        st.warning("請先在側邊欄輸入正確密碼。")
    else:
        # 確保這裡的三個 Tab 名稱正確且邏輯完整
        tab1, tab2, tab3 = st.tabs(["📋 缺交名單管理", "🎯 座號快速補交", "📝 新增整班作業"])

        # Tab 1: 缺交名單
        with tab1:
            st.subheader("📋 作業缺交名單 (直接點擊修改)")
            all_hws = st.session_state.main_df["作業名稱"].unique()
            sel_hw = st.selectbox("請選擇作業：", ["請選擇"] + list(all_hws), key="t1_sel_hw")
            if sel_hw != "請選擇":
                hw_data = st.session_state.main_df[st.session_state.main_df["作業名稱"] == sel_hw]
                missing = hw_data[hw_data["繳交狀態"] != "已繳交"]
                if missing.empty:
                    st.success("🎉 全班均已繳交完成！")
                else:
                    st.error(f"待處理名單 ({len(missing)} 人)：")
                    for idx, r in missing.iterrows():
                        mc1, mc2, mc3 = st.columns([3, 1, 1])
                        mc1.markdown(f"**{r['座號']}號 {r['姓名']}** (`{r['繳交狀態']}`)")
                        if mc2.button("已繳交", key=f"t1_d_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            save_all(st.session_state.main_df); st.rerun()
                        if mc3.button("需訂正", key=f"t1_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            save_all(st.session_state.main_df); st.rerun()

        # Tab 2: 快速補交 (這是您之前說沒看見的部分)
        with tab2:
            st.subheader("🎯 依座號快速補交作業")
            target_sid = st.text_input("請輸入學生座號：", key="t2_sid_input")
            if target_sid:
                s_miss_data = st.session_state.main_df[(st.session_state.main_df["座號"].astype(str) == str(target_sid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if not s_miss_data.empty:
                    st.write(f"學生姓名：**{s_miss_data.iloc[0]['姓名']}**")
                    for idx, row in s_miss_data.iterrows():
                        bc1, bc2, bc3 = st.columns([3, 1, 1])
                        bc1.write(f"📌 {row['作業名稱']} (`{row['繳交狀態']}`)")
                        if bc2.button("✅ 已交", key=f"t2_d_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_all(st.session_state.main_df); st.rerun()
                        if bc3.button("✏️ 訂正", key=f"t2_r_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "需訂正"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            save_all(st.session_state.main_df); st.rerun()
                else:
                    st.info("該生目前沒有欠交作業紀錄。")

        # Tab 3: 新增作業
        with tab3:
            st.subheader("📝 新增整班作業登記")
            if 'hw_input_val' not in st.session_state: st.session_state.hw_input_val = ""
            new_hw_name = st.text_input("新作業名稱：", value=st.session_state.hw_input_val)
            if new_hw_name:
                if 'tmp' not in st.session_state or st.session_state.lhwn != new_hw_name:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = new_hw_name
                
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']; cur = st.session_state.tmp[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']} ({cur})", key=f"t3_btn_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "已繳交" if cur == "未繳交" else "需訂正" if cur == "已繳交" else "未繳交"
                        st.rerun()
                
                if st.button("🚀 確定發佈並同步雲端", type="primary", use_container_width=True):
                    new_rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":new_hw_name, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    updated_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    if save_all(updated_df):
                        st.session_state.hw_input_val = ""; st.session_state.lhwn = ""
                        st.success("發佈成功！"); st.balloons(); time.sleep(1); st.rerun()

        # 底部功能
        st.divider()
        with st.expander("🗑️ 危險區域：刪除錯誤作業"):
            del_hw_list = st.session_state.main_df["作業名稱"].unique()
            target_del = st.selectbox("選擇要刪除的作業：", ["請選擇"] + list(del_hw_list))
            confirm_del = st.checkbox("我確定要永久刪除此項作業紀錄")
            if st.button("❌ 刪除") and confirm_del and target_del != "請選擇":
                save_all(st.session_state.main_df[st.session_state.main_df["作業名稱"] != target_del]); st.rerun()

        if st.sidebar.button("🔄 強制刷新數據"):
            st.session_state.main_df = load_data_api(); st.rerun()
