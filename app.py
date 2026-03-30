import streamlit as st
import pandas as pd
import requests
import io
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-正式版", layout="wide")
st.title("📚 303 作業登記系統")

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

# --- 3. 歷史資料注入 (這保證你的舊資料一定會出現) ---
RAW_HISTORY = """座號,姓名,作業名稱,繳交狀態,更新日期
1,王瑀淮,3/27聯絡簿,已繳交,2026-03-27
19,楊晨妤,3/27聯絡簿,未繳交,2026-03-27
4,廖勇傑,L2圈詞,需訂正,2026-03-27
6,郭家宇,L2圈詞,未繳交,2026-03-27
15,詹筠蓁,L2圈詞,未繳交,2026-03-27
21,蔡芊芊,L2圈詞,需訂正,2026-03-27
6,郭家宇,L2生字造詞,未繳交,2026-03-27
1,王瑀淮,L3圈詞,需訂正,2026-03-27
2,李祐嘉,L3圈詞,未繳交,2026-03-27
3,郭晁瑋,L3圈詞,未繳交,2026-03-27
4,廖勇傑,L3圈詞,需訂正,2026-03-27
6,郭家宇,L3圈詞,未繳交,2026-03-27
19,楊晨妤,L3圈詞,未繳交,2026-03-27
21,蔡芊芊,L3圈詞,未繳交,2026-03-27
6,郭家宇,L3國卷,需訂正,2026-03-27
14,鍾芮昕,L3國卷,需訂正,2026-03-27
21,蔡芊芊,L3國卷,需訂正,2026-03-27
21,蔡芊芊,L3生字造詞,需訂正,2026-03-27
1,王瑀淮,乙本p.25,未繳交,2026-03-27
4,廖勇傑,乙本p.25,未繳交,2026-03-27
12,蔣語桐,乙本p.25,未繳交,2026-03-27
19,楊晨妤,乙本p.25,未繳交,2026-03-27
21,蔡芊芊,乙本p.25,未繳交,2026-03-27
12,蔣語桐,乙本p.9-11,未繳交,2026-03-27
6,郭家宇,圈詞L1,未繳交,2026-03-27
1,王瑀淮,國乙本p.22~24,未繳交,2026-03-27
6,郭家宇,國乙本p.22~24,需訂正,2026-03-27
12,蔣語桐,國乙本p.22~24,需訂正,2026-03-27
19,楊晨妤,國乙本p.22~24,未繳交,2026-03-27
21,蔡芊芊,國乙本p.22~24,需訂正,2026-03-27
1,王瑀淮,國甲p.17.23.24,需訂正,2026-03-27
21,蔡芊芊,國甲p.17.23.24,需訂正,2026-03-27
1,王瑀淮,國甲p.25.26,需訂正,2026-03-27
18,呂佳恩,國甲p.25.26,需訂正,2026-03-27
21,蔡芊芊,國甲p.25.26,需訂正,2026-03-27
1,王瑀淮,小日記1,未繳交,2026-03-27
2,李祐嘉,小日記1,未繳交,2026-03-27
2,李祐嘉,小日記2,未繳交,2026-03-27
6,郭家宇,小日記2,未繳交,2026-03-27
14,鍾芮昕,小日記2,需訂正,2026-03-27
15,詹筠蓁,小日記2,需訂正,2026-03-27
18,呂佳恩,小日記2,需訂正,2026-03-27
19,楊晨妤,小日記2,需訂正,2026-03-27
21,蔡芊芊,小日記2,需訂正,2026-03-27
6,郭家宇,成語25,未繳交,2026-03-27
1,王瑀淮,成語p.26.27,未繳交,2026-03-27
6,郭家宇,成語p.26.27,未繳交,2026-03-27
19,楊晨妤,成語p.26.27,需訂正,2026-03-27
1,王瑀淮,成語p28,未繳交,2026-03-27
6,郭家宇,成語p28,未繳交,2026-03-27
19,楊晨妤,成語p28,未繳交,2026-03-27
1,王瑀淮,成語p29,未繳交,2026-03-27
6,郭家宇,成語p29,未繳交,2026-03-27
19,楊晨妤,成語p29,未繳交,2026-03-27
22,王楷晴,成語p29,未繳交,2026-03-27
1,王瑀淮,成語p30,未繳交,2026-03-27
4,廖勇傑,成語p30,未繳交,2026-03-27
6,郭家宇,成語p30,未繳交,2026-03-27
19,楊晨妤,成語p30,未繳交,2026-03-27
21,蔡芊芊,成語p30,未繳交,2026-03-27
22,王楷晴,成語p30,未繳交,2026-03-27
6,郭家宇,數卷(大),需訂正,2026-03-27
19,楊晨妤,數卷(大),需訂正,2026-03-27
14,鍾芮昕,數卷1-3,需訂正,2026-03-27
15,詹筠蓁,數卷1-3,需訂正,2026-03-27
18,呂佳恩,數卷1-3,需訂正,2026-03-27
19,楊晨妤,數卷1-3,需訂正,2026-03-27
21,蔡芊芊,數卷1-3,需訂正,2026-03-27
1,王瑀淮,數卷2-2,需訂正,2026-03-27
3,郭晁瑋,數卷2-2,需訂正,2026-03-27
4,廖勇傑,數卷2-2,需訂正,2026-03-27
6,郭家宇,數卷2-2,需訂正,2026-03-27
15,詹筠蓁,數卷2-2,需訂正,2026-03-27
1,王瑀淮,數學2-3,未繳交,2026-03-27
4,廖勇傑,數學2-3,需訂正,2026-03-27
6,郭家宇,數學2-3,未繳交,2026-03-27
14,鍾芮昕,數學2-3,需訂正,2026-03-27
15,詹筠蓁,數學2-3,未繳交,2026-03-27
18,呂佳恩,數學2-3,需訂正,2026-03-27
19,楊晨妤,數學2-3,需訂正,2026-03-27
14,鍾芮昕,數習28.29,需訂正,2026-03-27
19,楊晨妤,數習28.29,需訂正,2026-03-27
21,蔡芊芊,數習28.29,需訂正,2026-03-27
18,呂佳恩,"數習p.18,19",需訂正,2026-03-27
19,楊晨妤,"數習p.18,19",需訂正,2026-03-27
22,王楷晴,數習p.25,未繳交,2026-03-27
1,王瑀淮,"數習p.34,35",未繳交,2026-03-27
2,李祐嘉,"數習p.34,35",未繳交,2026-03-27
3,郭晁瑋,"數習p.34,35",未繳交,2026-03-27
4,廖勇傑,"數習p.34,35",未繳交,2026-03-27
6,郭家宇,"數習p.34,35",未繳交,2026-03-27
8,劉橙,"數習p.34,35",未繳交,2026-03-27
12,蔣語桐,"數習p.34,35",未繳交,2026-03-27
14,鍾芮昕,"數習p.34,35",未繳交,2026-03-27
18,呂佳恩,"數習p.34,35",需訂正,2026-03-30
19,楊晨妤,"數習p.34,35",未繳交,2026-03-27
21,蔡芊芊,"數習p.34,35",未繳交,2026-03-27
22,王楷晴,"數習p.34,35",未繳交,2026-03-27
1,王瑀淮,數課45.46,未繳交,2026-03-27
6,郭家宇,"數課p.17,18",未繳交,2026-03-27
21,蔡芊芊,數重p.10,需訂正,2026-03-27
22,王楷晴,數重p.10,未繳交,2026-03-27
6,郭家宇,數重p.11,未繳交,2026-03-27
18,呂佳恩,數重p.11,需訂正,2026-03-27
19,楊晨妤,數重p.11,未繳交,2026-03-27
21,蔡芊芊,數重p.11,需訂正,2026-03-27
1,王瑀淮,數重p.12~13,未繳交,2026-03-27
4,廖勇傑,數重p.12~13,需訂正,2026-03-27
6,郭家宇,數重p.12~13,需訂正,2026-03-27
15,詹筠蓁,數重p.12~13,需訂正,2026-03-27
19,楊晨妤,數重p.12~13,未繳交,2026-03-27
21,蔡芊芊,數重p.12~13,需訂正,2026-03-27
21,蔡芊芊,數重p.5,未繳交,2026-03-27
22,王楷晴,數重p.8,需訂正,2026-03-27
22,王楷晴,甲本p.20-22,未繳交,2026-03-27"""

# --- 4. 核心邏輯 ---
def load_data():
    try:
        # 嘗試讀取雲端
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&t={int(time.time())}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                for _, row in df_raw.iloc[::-1].iterrows():
                    content = str(row.iloc[-1])
                    if "座號" in content:
                        df = pd.read_csv(io.StringIO(content), dtype={'座號': str})
                        return df.reset_index(drop=True)
    except:
        pass
    
    # 💡 如果雲端沒資料，就讀取上面那串「救援歷史」
    # 為了節省空間，救援歷史只列出「未完成」和「需訂正」的，其餘設為已繳交
    history_df = pd.read_csv(io.StringIO(RAW_HISTORY), dtype={'座號': str})
    
    # 構建完整名單 (將不在歷史清單中的人自動補齊為已繳交)
    full_data = []
    hws = history_df['作業名稱'].unique()
    for hw in hws:
        hw_subset = history_df[history_df['作業名稱'] == hw]
        for s in STUDENT_LIST:
            sid = s['座號']
            match = hw_subset[hw_subset['座號'] == sid]
            if not match.empty:
                full_data.append(match.iloc[0].to_dict())
            else:
                full_data.append({"座號":sid, "姓名":s['姓名'], "作業名稱":hw, "繳交狀態":"已繳交", "更新日期":"2026-03-27"})
    
    return pd.DataFrame(full_data)

def save_all(df):
    st.session_state.main_df = df
    try:
        csv_str = df.to_csv(index=False)
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        return True
    except:
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 5. UI 介面 ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")
menu = st.sidebar.selectbox("切換功能", ["🔍 查詢", "🛠️ 後台"])

def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_all(st.session_state.main_df)

if menu == "🔍 查詢":
    sid = st.text_input("座號：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty: st.success("🎉 全部交齊了！")
            for idx, row in todo.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(f"📌 {row['作業名稱']}")
                c2.write(f"`{row['繳交狀態']}`")
                if is_admin:
                    c3.button("已交", key=f"q_{idx}", on_click=update_status, args=(idx, "已繳交"))
                    c4.button("訂正", key=f"q_r_{idx}", on_click=update_status, args=(idx, "需訂正"))
            with st.expander("已完成"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 後台":
    if not is_admin:
        st.warning("請輸入密碼")
    else:
        t1, t2, t3 = st.tabs(["📋 缺交名單", "🎯 補交", "📝 新作業"])
        with t3:
            hw_n = st.text_input("新作業名稱：")
            if hw_n:
                if 'tmp' not in st.session_state or st.session_state.get('lhwn') != hw_n:
                    st.session_state.tmp = {s['座號']: "未繳交" for s in STUDENT_LIST}
                    st.session_state.lhwn = hw_n
                cols = st.columns(3)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']; cur = st.session_state.tmp[sid]
                    if cols[i%3].button(f"{sid}.{s['姓名']} ({cur})", key=f"t3_{sid}", use_container_width=True):
                        st.session_state.tmp[sid] = "已繳交" if cur == "未繳交" else "需訂正" if cur == "已繳交" else "未繳交"
                        st.rerun()
                if st.button("🚀 確認發佈", type="primary", use_container_width=True):
                    new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw_n, "繳交狀態":st.session_state.tmp[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    save_all(pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True))
                    st.success("發佈成功！"); time.sleep(1); st.rerun()
        # 補交與缺交名單邏輯維持...
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                for i, r in m.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    cb.button("已交", key=f"t1_{i}", on_click=update_status, args=(i, "已繳交"))
                    cc.button("訂正", key=f"t1_r_{i}", on_click=update_status, args=(i, "需訂正"))
