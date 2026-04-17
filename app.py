import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 基本設定 ---
st.set_page_config(page_title="303作業登記-穩定緩衝版", layout="wide")
st.title("📚 303 作業登記系統 (緩衝模式)")

STUDENT_LIST = [{"座號": str(i), "姓名": n} for i, n in enumerate([
    "王瑀淮", "李祐嘉", "郭晁瑋", "廖勇傑", "潘彥廷", "郭家宇", "王悅芯", "劉橙",
    "洪語緹", "林祈平", "鄧安晴", "蔣語桐", "邱薇瑀", "鍾芮昕", "詹荺蓁", "劉姝言",
    "范庭蓁", "呂佳恩", "楊晨妤", "劉芮安", "蔡芊芊", "王楷晴"
], 1)]

# --- 2. 核心資料邏輯 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])
        # 確保欄位完整
        for col in ["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"]:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        df["座號"] = df["座號"].astype(str)
        return df
    except:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "成績", "更新日期"])

def save_to_cloud():
    if save_data_core(st.session_state.main_df):
        st.success("✅ 雲端資料同步成功！")
        st.session_state.has_unsaved_changes = False
    else:
        st.error("❌ 同步失敗，請檢查網路！")

def save_data_core(df):
    try:
        # 安全檢查：若 df 為空則不存檔，防止誤刪
        if df.empty and not load_data().empty:
            st.warning("偵測到異常清空，系統攔截存檔指令。")
            return False
        conn.update(worksheet="Sheet1", data=df)
        return True
    except: return False

# 初始化
if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()
if 'has_unsaved_changes' not in st.session_state:
    st.session_state.has_unsaved_changes = False

# --- 3. 局部更新元件 (零跳轉區) ---
@st.fragment
def quick_entry_area(target_hw):
    st.subheader(f"⚡ 快速輸入 - {target_hw}")
    c1, c2 = st.columns(2)
    
    with c1:
        sid_done = st.text_input("🟢 標記【已繳交】座號", key=f"f_done_{target_hw}", placeholder="例: 1,3,5")
        if sid_done:
            sids = [s.strip() for s in sid_done.replace("，", ",").split(",") if s.strip()]
            for sid in sids:
                mask = (st.session_state.main_df["作業名稱"] == target_hw) & (st.session_state.main_df["座號"] == sid)
                if any(mask):
                    st.session_state.main_df.loc[mask, "繳交狀態"] = "已繳交"
                    st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
            st.session_state.has_unsaved_changes = True
            st.rerun(scope="fragment") # 僅刷新快填區，不跳頁

    with c2:
        sid_edit = st.text_input("🔴 標記【需訂正】座號", key=f"f_edit_{target_hw}", placeholder="例: 12")
        if sid_edit:
            sids = [s.strip() for s in sid_edit.replace("，", ",").split(",") if s.strip()]
            for sid in sids:
                mask = (st.session_state.main_df["作業名稱"] == target_hw) & (st.session_state.main_df["座號"] == sid)
                if any(mask):
                    st.session_state.main_df.loc[mask, "繳交狀態"] = "需訂正"
                    st.session_state.main_df.loc[mask, "更新日期"] = str(date.today())
            st.session_state.has_unsaved_changes = True
            st.rerun(scope="fragment")

# --- 4. UI 介面 ---
st.sidebar.title("⚙️ 管理選單")
pwd = st.sidebar.text_input("老師密碼", type="password")
is_admin = (pwd == "alice")

if st.sidebar.button("🔄 重新載入雲端資料"):
    st.session_state.main_df = load_data()
    st.session_state.has_unsaved_changes = False
    st.rerun()

if st.session_state.has_unsaved_changes:
    st.sidebar.warning("⚠️ 內容已變更，請點選下方按鈕儲存至雲端。")
    if st.sidebar.button("💾 儲存並同步至雲端", type="primary"):
        save_to_cloud()

menu = st.sidebar.radio("切換功能", ["🔍 學生查詢", "🛠️ 老師後台"])

if menu == "🔍 學生查詢":
    sid = st.text_input("輸入座號查詢 (1-22)：")
    if sid:
        res = st.session_state.main_df[st.session_state.main_df["座號"] == str(sid)]
        if not res.empty:
            name = res.iloc[0]['姓名']
            st.subheader(f"👤 {name} 的待辦作業")
            todo = res[res["繳交狀態"] != "已繳交"]
            if todo.empty:
                st.balloons(); st.success(f"🎊 太棒了，{name}！目前沒有欠作業喔！")
            else:
                for idx, row in todo.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"📌 **{row['作業名稱']}**")
                    color = "red" if row['繳交狀態'] == "需訂正" else "orange"
                    cb.markdown(f":{color}[{row['繳交狀態']}]")

elif menu == "🛠️ 老師後台":
    if not is_admin:
        st.warning("⚠️ 請輸入密碼。")
    else:
        tab1, tab2, tab3 = st.tabs(["📋 缺交與登記成績", "🎯 單生管理", "📝 新增作業"])
        
        with tab1:
            all_hws = st.session_state.main_df["作業名稱"].unique()
            sel = st.selectbox("選擇作業項目", ["請選擇"] + list(all_hws))
            
            if sel != "請選擇":
                # ✨ 快速輸入區 (不跳頁)
                quick_entry_area(sel)
                
                st.divider()
                # 列表顯示 (包含成績登記)
                m = st.session_state.main_df[st.session_state.main_df["作業名稱"] == sel]
                for i, r in m.iterrows():
                    ca, cb, cc, cd = st.columns([1.5, 1.5, 2, 1])
                    ca.write(f"**{r['座號']}. {r['姓名']}**")
                    color = "red" if r['繳交狀態'] == "需訂正" else ("orange" if r['繳交狀態'] == "未繳交" else "green")
                    cb.markdown(f":{color}[**{r['繳交狀態']}**]")
                    
                    # 打分數 (僅變更暫存)
                    sc = cc.text_input("成績", value=str(r['成績']), key=f"sc_{sel}_{i}", label_visibility="collapsed")
                    if sc != str(r['成績']):
                        st.session_state.main_df.at[i, "成績"] = sc
                        st.session_state.has_unsaved_changes = True
                    
                    if cd.button("已交/訂正", key=f"sw_{sel}_{i}"):
                        new_s = "已繳交" if r['繳交狀態'] != "已繳交" else "需訂正"
                        st.session_state.main_df.at[i, "繳交狀態"] = new_s
                        st.session_state.has_unsaved_changes = True
                        st.rerun()

        with tab3:
            st.subheader("📝 新增作業")
            nhw = st.text_input("作業名稱：")
            if st.button("🚀 確認發佈"):
                new_rows = [{"座號": s['座號'], "姓名": s['姓名'], "作業名稱": nhw, "繳交狀態": "未繳交", "成績": "", "更新日期": str(date.today())} for s in STUDENT_LIST]
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state.has_unsaved_changes = True
                st.success("已加入暫存名單，請記得點選左側『儲存並同步』。")

# 側邊欄刪除功能
if is_admin:
    with st.sidebar.expander("🗑️ 危險區域 (刪除作業)"):
        target = st.selectbox("選取要刪除的作業", ["請選擇"] + list(st.session_state.main_df["作業名稱"].unique()))
        if st.button("確認從緩衝刪除") and target != "請選擇":
            st.session_state.main_df = st.session_state.main_df[st.session_state.main_df["作業名稱"] != target]
            st.session_state.has_unsaved_changes = True
