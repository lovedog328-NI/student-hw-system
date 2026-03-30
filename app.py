import streamlit as st
import pandas as pd
import io
from datetime import date
import requests
import time

# --- 1. 頁面配置 ---
st.set_page_config(page_title="303作業登記", layout="wide")
st.title("📚 303 作業登記系統")

# --- 2. 核心名單與 3/27 歷史紀錄 (永久備份) ---
STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate(["王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙", "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹筠蓁", "劉姝言", "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"], 1)]

RAW_BACKUP = """座號,姓名,作業名稱,繳交狀態,更新日期
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
1,王瑀淮,國乙本p.22-24,未繳交,2026-03-27
6,郭家宇,國乙本p.22-24,需訂正,2026-03-27
12,蔣語桐,國乙本p.22-24,需訂正,2026-03-27
19,楊晨妤,國乙本p.22-24,未繳交,2026-03-27
21,蔡芊芊,國乙本p.22-24,需訂正,2026-03-27
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
18,呂佳恩,數習p.18.19,需訂正,2026-03-27
19,楊晨妤,數習p.18.19,需訂正,2026-03-27
22,王楷晴,數習p.25,未繳交,2026-03-27
1,王瑀淮,數習p.34.35,未繳交,2026-03-27
2,李祐嘉,數習p.34.35,未繳交,2026-03-27
3,郭晁瑋,數習p.34.35,未繳交,2026-03-27
4,廖勇傑,數習p.34.35,未繳交,2026-03-27
6,郭家宇,數習p.34.35,未繳交,2026-03-27
8,劉橙,數習p.34.35,未繳交,2026-03-27
12,蔣語桐,數習p.34.35,未繳交,2026-03-27
14,鍾芮昕,數習p.34.35,未繳交,2026-03-27
18,呂佳恩,數習p.34.35,需訂正,2026-03-30
19,楊晨妤,數習p.34.35,未繳交,2026-03-27
21,蔡芊芊,數習p.34.35,未繳交,2026-03-27
22,王楷晴,數習p.34.35,未繳交,2026-03-27
1,王瑀淮,數課45.46,未繳交,2026-03-27
6,郭家宇,數課p.17.18,未繳交,2026-03-27
21,蔡芊芊,數重p.10,需訂正,2026-03-27
22,王楷晴,數重p.10,未繳交,2026-03-27
6,郭家宇,數重p.11,未繳交,2026-03-27
18,呂佳恩,數重p.11,需訂正,2026-03-27
19,楊晨妤,數重p.11,未繳交,2026-03-27
21,蔡芊芊,數重p.11,需訂正,2026-03-27
1,王瑀淮,數重p.12.13,未繳交,2026-03-27
4,廖勇傑,數重p.12.13,需訂正,2026-03-27
6,郭家宇,數重p.12.13,需訂正,2026-03-27
15,詹筠蓁,數重p.12.13,需訂正,2026-03-27
19,楊晨妤,數重p.12.13,未繳交,2026-03-27
21,蔡芊芊,數重p.12.13,需訂正,2026-03-27
21,蔡芊芊,數重p.5,未繳交,2026-03-27
22,王楷晴,數重p.8,需訂正,2026-03-27
22,王楷晴,甲本p.20-22,未繳交,2026-03-27"""

# --- 3. 核心功能 ---
def fetch_cloud():
    try:
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&gid=0&v={int(time.time())}"
        r = requests.get(url, timeout=5, headers={'Cache-Control': 'no-cache'})
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                last_content = str(df_raw.iloc[-1, -1])
                if "座號" in last_content:
                    new_df = pd.read_csv(io.StringIO(last_content), dtype={'座號': str})
                    if len(new_df) >= 22: return new_df
    except:
        pass
    return None

def save_to_cloud(df):
    csv_str = df.to_csv(index=False)
    try:
        url = st.secrets["google_sync"]["form_url"]
        eid = st.secrets["google_sync"]["entry_id"]
        requests.post(url, data={eid: csv_str}, timeout=5)
        st.session_state.main_df = df
        return True
    except:
        return False

# 初始化
if 'main_df' not in st.session_state:
    cloud_df = fetch_cloud()
    if cloud_df is not None:
        st.session_state.main_df = cloud_df
    else:
        st.session_state.main_df = pd.read_csv(io.StringIO(RAW_BACKUP), dtype={'座號': str})

# --- 4. UI 介面 ---
st.sidebar.title("🔐 管理權限")
pwd = st.sidebar.text_input("密碼", type="password")
is_admin = (pwd == "alice")

if is_admin:
    if st.sidebar.button("🔄 手動從雲端同步"):
        new_data = fetch_cloud()
        if new_data is not None:
            st.session_state.main_df = new_data
            st.sidebar.success("同步成功！")
            st.rerun()

menu = st.sidebar.selectbox("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

def update_val(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_to_cloud(st.session_state.main_df)

# --- 功能實現 ---
if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        df = st.session_state.main_df
        res = df[df["座號"] == str(sid)]
        if not res.empty:
            st.subheader(f"👤 {res.iloc[0]['姓名']} 的作業狀況")
            
            # 💡 判斷是否還有欠交或需訂正
            todo = res[res["繳交狀態"] != "已繳交"]
            
            if todo.empty:
                # 🎉 補回恭喜訊息
                st.success("✨ 太棒了！目前的作業全都交齊囉！請繼續保持！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    c1.write(f"📌 {row['作業名稱']} ({row['繳交狀態']})")
                    if is_admin:
                        c2.button("已交", key=f"q_{idx}", on_click=update_val, args=(idx, "已繳交"))
                        c3.button("需改", key=f"qr_{idx}", on_click=update_val, args=(idx, "需訂正"))
            
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("請先輸入密碼。")
    else:
        t1, t2, t3 = st.tabs(["缺交名單", "快速補交", "新增作業"])
        with t1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選作業項目", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty:
                    st.success("🎉 這項作業全班都交齊了！")
                for i, r in m.iterrows():
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.write(f"{r['座號']}. {r['姓名']}")
                    cb.button("已交", key=f"t1_{i}", on_click=update_val, args=(i, "已繳交"))
                    cc.button("需改", key=f"t1r_{i}", on_click=update_val, args=(i, "需訂正"))
        
        with t2:
            tsid = st.text_input("快速補交座號：")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"] == str(tsid)) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if sm.empty:
                    st.info("該生目前沒有欠交作業。")
                else:
                    for i, r in sm.iterrows():
                        ra, rb, rc = st.columns([3, 1, 1])
                        ra.write(f"📌 {r['作業名稱']}")
                        rb.button("已交", key=f"t2_{i}", on_click=update_val, args=(i, "已繳交"))
                        rc.button("需改", key=f"t2r_{i}", on_click=update_val, args=(i, "需訂正"))

        with t3:
            name = st.text_input("作業名稱：")
            if st.button("🚀 發佈新作業") and name:
                new_l = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":name, "繳交狀態":"未繳交", "更新日期":""} for s in STUDENT_LIST]
                new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_l)], ignore_index=True)
                if save_to_cloud(new_df):
                    st.success(f"已發佈 {name}")
                    time.sleep(1)
                    st.rerun()

        st.divider()
        with st.expander("🗑️ 刪除紀錄"):
            target = st.selectbox("選擇要刪除的作業：", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
            if st.button("確認永久刪除") and target != "請選擇":
                new_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
                save_to_cloud(new_df)
                st.rerun()
