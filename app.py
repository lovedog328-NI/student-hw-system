import streamlit as st
import pandas as pd
import io
from datetime import date
import requests
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-恢復版", layout="wide")
st.title("📚 303 作業登記系統 (資料已強制恢復)")

# --- 2. 固定學生名單 ---
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

# --- 3. 歷史欠交資料 (已清洗格式) ---
RAW_HISTORY = """座號,作業名稱,繳交狀態
1,3/27聯絡簿,已繳交
19,3/27聯絡簿,未繳交
4,L2圈詞,需訂正
6,L2圈詞,未繳交
15,L2圈詞,未繳交
21,L2圈詞,需訂正
6,L2生字造詞,未繳交
1,L3圈詞,需訂正
2,L3圈詞,未繳交
3,L3圈詞,未繳交
4,L3圈詞,需訂正
6,L3圈詞,未繳交
19,L3圈詞,未繳交
21,L3圈詞,未繳交
6,L3國卷,需訂正
14,L3國卷,需訂正
21,L3國卷,需訂正
21,L3生字造詞,需訂正
1,乙本p.25,未繳交
4,乙本p.25,未繳交
12,乙本p.25,未繳交
19,乙本p.25,未繳交
21,乙本p.25,未繳交
12,乙本p.9-11,未繳交
6,圈詞L1,未繳交
1,國乙本p.22~24,未繳交
6,國乙本p.22~24,需訂正
12,國乙本p.22~24,需訂正
19,國乙本p.22~24,未繳交
21,國乙本p.22~24,需訂正
1,國甲p.17.23.24,需訂正
21,國甲p.17.23.24,需訂正
1,國甲p.25.26,需訂正
18,國甲p.25.26,需訂正
21,國甲p.25.26,需訂正
1,小日記1,未繳交
2,小日記1,未繳交
2,小日記2,未繳交
6,小日記2,未繳交
14,小日記2,需訂正
15,小日記2,需訂正
18,小日記2,需訂正
19,小日記2,需訂正
21,小日記2,需訂正
6,成語25,未繳交
1,成語p.26.27,未繳交
6,成語p.26.27,未繳交
19,成語p.26.27,需訂正
1,成語p28,未繳交
6,成語p28,未繳交
19,成語p28,未繳交
1,成語p29,未繳交
6,成語p29,未繳交
19,成語p29,未繳交
22,成語p29,未繳交
1,成語p30,未繳交
4,成語p30,未繳交
6,成語p30,未繳交
19,成語p30,未繳交
21,成語p30,未繳交
22,成語p30,未繳交
6,數卷(大),需訂正
19,數卷(大),需訂正
14,數卷1-3,需訂正
15,數卷1-3,需訂正
18,數卷1-3,需訂正
19,數卷1-3,需訂正
21,數卷1-3,需訂正
1,數卷2-2,需訂正
3,數卷2-2,需訂正
4,數卷2-2,需訂正
6,數卷2-2,需訂正
15,數卷2-2,需訂正
1,數學2-3,未繳交
4,數學2-3,需訂正
6,數學2-3,未繳交
14,數學2-3,需訂正
15,數學2-3,未繳交
18,數學2-3,需訂正
19,數學2-3,需訂正
14,數習28.29,需訂正
19,數習28.29,需訂正
21,數習28.29,需訂正
18,數習p.18,19,需訂正
19,數習p.18,19,需訂正
22,數習p.25,未繳交
1,數習p.34,35,未繳交
2,數習p.34,35,未繳交
3,數習p.34,35,未繳交
4,數習p.34,35,未繳交
6,數習p.34,35,未繳交
8,數習p.34,35,未繳交
12,數習p.34,35,未繳交
14,數習p.34,35,未繳交
18,數習p.34,35,需訂正
19,數習p.34,35,未繳交
21,數習p.34,35,未繳交
22,數習p.34,35,未繳交
1,數課45.46,未繳交
6,數課p.17,18,未繳交
21,數重p.10,需訂正
22,數重p.10,未繳交
6,數重p.11,未繳交
18,數重p.11,需訂正
19,數重p.11,未繳交
21,數重p.11,需訂正
1,數重p.12~13,未繳交
4,數重p.12~13,需訂正
6,數重p.12~13,需訂正
15,數重p.12~13,需訂正
19,數重p.12~13,未繳交
21,數重p.12~13,需訂正
21,數重p.5,未繳交
22,數重p.8,需訂正
22,甲本p.20-22,未繳交"""

# --- 4. 生成資料庫邏輯 ---
def generate_initial_df():
    # 讀取欠交清單
    history_df = pd.read_csv(io.StringIO(RAW_HISTORY), dtype={'座號': str})
    hws = history_df['作業名稱'].unique()
    
    all_rows = []
    name_map = {s['座號']: s['姓名'] for s in STUDENT_LIST}
    
    for hw in hws:
        hw_subset = history_df[history_df['作業名稱'] == hw]
        for s in STUDENT_LIST:
            sid = s['座號']
            # 找是否有欠交紀錄
            match = hw_subset[hw_subset['座號'] == sid]
            if not match.empty:
                status = match.iloc[0]['繳交狀態']
            else:
                status = "已繳交"
            
            all_rows.append({
                "座號": sid,
                "姓名": name_map[sid],
                "作業名稱": hw,
                "繳交狀態": status,
                "更新日期": "2026-03-30"
            })
    return pd.DataFrame(all_rows)

# --- 5. 存取與 UI ---
if 'main_df' not in st.session_state:
    # 💡 這次直接在記憶體中生成，保證資料一定會出現
    st.session_state.main_df = generate_initial_df()

def save_to_cloud(df):
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
    except:
        pass

# 側邊欄
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")
menu = st.sidebar.selectbox("選單", ["🔍 學生查詢", "🛠️ 老師後台"])

def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_to_cloud(st.session_state.main_df)

if menu == "🔍 學生查詢":
    sid = st.text_input("座號：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty: st.success("🎉 作業全部交齊囉！")
            for idx, row in todo.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(f"📌 {row['作業名稱']}")
                c2.write(f"`{row['繳交狀態']}`")
                if is_admin:
                    c3.button("已交", key=f"q_{idx}", on_click=update_status, args=(idx, "已繳交"))
                    c4.button("訂正", key=f"qr_{idx}", on_click=update_status, args=(idx, "需訂正"))
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("請輸入密碼解鎖功能")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 快速補交", "📝 新增作業"])
        
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel_hw = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel_hw != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel_hw) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in m.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    cb.button("已交", key=f"t1_{i}", on_click=update_status, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t1r_{i}", on_click=update_status, args=(i, "需訂正"))

        with t3:
            st.subheader("📝 新增整班作業")
            new_hw = st.text_input("輸入名稱：")
            if new_hw:
                if st.button("🚀 點此發佈新作業"):
                    new_list = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":new_hw, "繳交狀態":"未繳交", "更新日期":str(date.today())} for s in STUDENT_LIST]
                    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_list)], ignore_index=True)
                    save_to_cloud(st.session_state.main_df)
                    st.success(f"已發佈 {new_hw}")
                    time.sleep(1); st.rerun()
