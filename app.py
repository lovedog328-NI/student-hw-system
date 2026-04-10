import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import time

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-專業版", layout="wide")
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
            return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
        df["座號"] = pd.to_numeric(df["座號"], errors='coerce').fillna(0).astype(int).astype(str)
        df = df[df["座號"] != "0"]
        return df
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

def save_data(df):
    try:
        conn.update(worksheet="Sheet1", data=df)
        return True
    except:
        return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

# --- 3. UI 介面控制 ---
st.sidebar.title("⚙️ 管理選單")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 同步最新雲端資料"):
    st.session_state.main_df = load_data()
    st.rerun()

menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

def update_status(idx, status):
    st.session_state.main_df.at[idx, "繳交狀態"] = status
    st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
    save_data(st.session_state.main_df)
    st.toast(f"✅ 已更新")

# --- 4. 介面實作 ---

if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的作業狀況")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success("🎊 全部交齊囉！")
            else:
                for idx, row in todo.iterrows():
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"📌 {row['作業名稱']}")
                    color = "red" if row['繳交狀態'] == "未繳交" else "orange"
                    c2.markdown(f":{color}[**{row['繳交狀態']}**]")
            with st.expander("查看已完成項目"):
                st.table(res[res["繳交狀態"] == "已繳交"][["作業名稱", "更新日期"]])

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入正確密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交總覽", "🎯 補交與列印單據", "📝 新增作業"])
        
        with tab1:
            hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業項目", ["請選擇"] + list(hws))
            if sel != "請選擇":
                m = st.session_state.main_df[(st.session_state.main_df["作業名稱"] == sel) & (st.session_state.main_df["繳交狀態"] != "已繳交")]
                if m.empty: st.success("🎉 此項作業已全班交齊！")
                for i, r in m.iterrows():
                    ca, cb, cc, cd = st.columns([2, 1.5, 1, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    color = "red" if r['繳交狀態'] == "未繳交" else "orange"
                    cb.markdown(f":{color}[**{r['繳交狀態']}**]")
                    cc.button("已交", key=f"t1_d_{i}", on_click=update_status, args=(i, "已繳交"))
                    cd.button("訂正", key=f"t1_r_{i}", on_click=update_status, args=(i, "需訂正"))

        with tab2:
            st.subheader("🎯 學生個別補交與通知單")
            tsid = st.text_input("輸入座號 (1-22)：", key="tsid")
            if tsid:
                sm = st.session_state.main_df[(st.session_state.main_df["座號"] == str(tsid))]
                if not sm.empty:
                    name = sm.iloc[0]['姓名']
                    todo = sm[sm["繳交狀態"] != "已繳交"]
                    
                    if todo.empty:
                        st.success(f"✅ {name} 目前沒有欠交項目。")
                    else:
                        st.write(f"正在處理：**{name}** 的欠交清單")
                        for i, r in todo.iterrows():
                            ra, rb, rc, rd = st.columns([3, 2, 1, 1])
                            ra.write(f"📌 {r['作業名稱']}")
                            color = "red" if r['繳交狀態'] == "未繳交" else "orange"
                            rb.markdown(f":{color}[**{r['繳交狀態']}**]")
                            rc.button("已交", key=f"t2_d_{i}", on_click=update_status, args=(i, "已繳交"))
                            rd.button("訂正", key=f"t2_r_{i}", on_click=update_status, args=(i, "需訂正"))
                        
                        # --- 🖨️ 聯絡簿印章範本格式 ---
                        st.divider()
                        st.markdown("### 🖨️ 聯絡簿通知單 (適合貼入 Word)")
                        
                        stamp_text = f"┌──────────────────┐\n"
                        stamp_text += f"│  303 作業催繳通知 ({date.today().strftime('%m/%d')})  │\n"
                        stamp_text += f"├──────────────────┤\n"
                        stamp_text += f"│ 座號：{tsid.ljust(2)} 姓名：{name.ljust(5)}  │\n"
                        stamp_text += f"│                                  │\n"
                        for _, row in todo.iterrows():
                            hw_cut = row['作業名稱'][:10] # 避免作業標題太長爆格
                            status_mark = "未" if row['繳交狀態'] == "未繳交" else "訂"
                            stamp_text += f"│ □ {hw_cut.ljust(10)} ({status_mark})      │\n"
                        
                        # 補齊空白行，讓印章大小固定美觀
                        if len(todo) < 4:
                            for _ in range(4 - len(todo)):
                                stamp_text += f"│ □ ________________      │\n"
                                
                        stamp_text += f"│                                  │\n"
                        stamp_text += f"│ 家長簽名：_______________        │\n"
                        stamp_text += f"└──────────────────┘"
                        
                        st.code(stamp_text, language="text")
                        st.caption("💡 點擊右上角圖示即可複製，直接貼入 Word 表格中。建議使用『新細明體』或『微軟正黑體』對齊效果最佳。")

        with tab3:
            st.subheader("📝 新增整班作業項目")
            nhw = st.text_input("新增名稱 (例如：國習 L8)：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "更新日期": str(date.today())} for s in STUDENT_LIST]
                new_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                if save_data(new_df):
                    st.session_state.main_df = new_df
                    st.success("發佈成功！"); st.rerun()
        # ... (其餘刪除邏輯保持不變)
