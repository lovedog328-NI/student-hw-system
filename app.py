def load_data():
    try:
        # 強制破解快取抓取最新 CSV
        url = f"https://docs.google.com/spreadsheets/d/1cZCffUUh3lczFtEq8l49fb4rkPJnEBo0CyZx8TV4OMo/export?format=csv&t={int(time.time())}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 200:
            df_raw = pd.read_csv(io.StringIO(r.text))
            if not df_raw.empty:
                # 從最後一列往前找（最多找 5 筆），確保抓到正確格式
                # df_raw.iloc[::-1] 會將表格倒序排列
                for _, row in df_raw.iloc[::-1].iterrows():
                    # 檢查最後一格是否包含 CSV 特徵
                    content = str(row.iloc[-1])
                    if "座號" in content and "作業名稱" in content:
                        df = pd.read_csv(io.StringIO(content), dtype={'座號': str})
                        # 再次確認關鍵欄位是否存在
                        if not df.empty and "座號" in df.columns:
                            # 數位化座號並排序
                            df['座號_int'] = pd.to_numeric(df['座號'], errors='coerce')
                            df = df.sort_values(by=["作業名稱", "座號_int"]).drop(columns=['座號_int'])
                            return df.reset_index(drop=True)
                            
    except Exception as e:
        st.sidebar.error(f"讀取失敗: {e}")
        
    # 如果都失敗，回傳空表
    return pd.DataFrame(columns=["座號", "姓名", "作業名稱", "繳交狀態", "更新日期"])
