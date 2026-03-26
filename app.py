import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="班級作業登記系統", layout="wide")

# --- 1. 管理員密碼 ---
ADMIN_PASSWORD = "alice" 

# --- 2. 班級名單 (22位) ---
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

# --- 3. 雲端同步核心 (共用記憶體) ---
@st.cache_resource
def get_db():
    # 初始化一個空的資料表
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# 取得目前的資料庫
if 'main_df' not in st.session_state:
    st.session_state.main_df = get_db()

# --- 4. 介面設計 ---
st.title("📚 班級作業登記系統")

st.sidebar.header("選單")
menu = st.sidebar.selectbox("切換功能", ["學生查詢", "老師後台"])

# --- 學生查詢 ---
if menu == "學生查詢":
    st.header("🔍 學生個人查詢")
    sid = st.text_input("輸入座號 (1-22)：")
    if sid:
        df = st.session_state.main_df
        # 篩選該生資料
        res = df[df["座號"].astype(str) == str(sid)]
        if not res.empty:
            st.success(f"你好，{res.iloc[0]['姓名']} 同學")
            # 預設隱藏已繳交的
            show_all = st.checkbox("顯示所有紀錄", value=False)
            display_df = res if show_all else res[res["繳交狀態"].isin(["未繳交", "需訂正"])]
            
            if display_df.empty:
                st.balloons()
                st.info("✨ 太棒了！目前沒有待處理作業。")
            else:
                st.table(display_df[["作業名稱", "繳交狀態", "更新日期"]])
        else:
            st.info("目前尚無你的紀錄。")

# --- 老師後台 ---
elif menu == "老師後台":
    st.header("👨‍🏫 老師管理中心")
    pwd = st.text_input("管理員密碼", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.success("解鎖成功")
        st.divider()

        # 區塊 A：快速更正 (最常用)
        with st.expander("🎯 學生補交/訂正快速按鈕", expanded=True):
            target_id = st.text_input("輸入座號：", key="target_id")
            if target_id:
                df = st.session_state.main_df
                s_todo = df[(df["座號"].astype(str) == str(target_id)) & (df["繳交狀態"] != "已繳交")]
                if not s_todo.empty:
                    st.write(f"學生：**{s_todo.iloc[0]['姓名']}**")
                    for idx, row in s_todo.iterrows():
                        col_t, col_b = st.columns([3, 1])
                        col_t.write(f"📌 {row['作業名稱']} ({row['繳交狀態']})")
                        if col_b.button(f"✅ 改為已完成", key=f"f_{idx}"):
                            st.session_state.main_df.at[idx, "繳交狀態"] = "已繳交"
                            st.session_state.main_df.at[idx, "更新日期"] = str(date.today())
                            st.toast("更新成功！")
                            st.rerun()
                else:
                    st.info("該生無缺交紀錄。")

        # 區塊 B：新增整班作業 (按鈕式)
        with st.expander("📝 新增整班作業登記", expanded=False):
            hw = st.text_input("作業名稱 (例如: 國語 L1)")
            if hw:
                # 初始化按鈕狀態
                if 'tmp_s' not in st.session_state or st.session_state.get('cur_hw') != hw:
                    st.session_state.tmp_s = {s['座號']: "已繳交" for s in STUDENT_LIST}
                    st.session_state.cur_hw = hw
                
                st.write("點選狀態切換：")
                cols = st.columns(2)
                for i, s in enumerate(STUDENT_LIST):
                    sid = s['座號']
                    curr = st.session_state.tmp_s[sid]
                    if cols[i%2].button(f"{sid}. {s['姓名']} ({curr})", key=f"b_{sid}", use_container_width=True):
                        st.session_state.tmp_s[sid] = "未繳交" if curr == "已繳交" else "需訂正" if curr == "未繳交" else "已繳交"
                        st.rerun()

                if st.button("🚀 儲存本次作業", type="primary"):
                    new_rows = [{"座號":s['座號'], "姓名":s['姓名'], "作業名稱":hw, "繳交狀態":st.session_state.tmp_s[s['座號']], "更新日期":str(date.today())} for s in STUDENT_LIST]
                    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.success("發布成功！")
                    st.balloons()
                    st.rerun()

        # 區塊 C：資料救援 (防止消失)
        with st.expander("💾 資料備份與還原"):
            st.subheader("1. 匯出備份 (每天下班按一次)")
            if not st.session_state.main_df.empty:
                output = io.BytesIO()
                st.session_state.main_df.to_excel(output, index=False, engine='openpyxl')
                st.download_button("📥 下載全班 Excel", data=output.getvalue(), file_name=f"作業紀錄_{date.today()}.xlsx")
            else:
                st.write("目前無資料。")
            
            st.divider()
            st.subheader("2. 重新匯入 (資料不見時用)")
            up = st.file_uploader("選取之前的 Excel 檔", type=["xlsx"])
            if up and st.button("✅ 確認還原所有資料"):
                st.session_state.main_df = pd.read_excel(up)
                st.success("還原成功！")
                st.rerun()

            st.divider()
            if st.button("⚠️ 清空資料庫"):
                st.session_state.main_df = pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
                st.rerun()
