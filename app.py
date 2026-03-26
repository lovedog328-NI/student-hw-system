import streamlit as st
import pandas as pd
import os
from datetime import date

# 檔案路徑
DATA_FILE = "homework_data.csv"

# --- 讀取資料 ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])

# --- 儲存資料 ---
def save_data(df_to_save):
    df_to_save.to_csv(DATA_FILE, index=False)
    # 這裡很關鍵：在本地開發時會存入硬碟，在雲端時會暫存於伺服器磁碟