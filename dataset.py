import streamlit as st
import pandas as pd
import numpy as np
from koneksi import koneksi

uploaded_file = st.file_uploader("Unggah file DATASET Bongkaran", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.xlsx'):
        df_upload = pd.read_excel(uploaded_file)
    else:
        df_upload = pd.read_csv(uploaded_file)
        
    st.subheader("Preview Data Bongkaran")
    st.dataframe(df_upload)
    
    if 'TANGGAL MASUK' in df_upload.columns:
        df_upload['TANGGAL MASUK'] = pd.to_datetime(df_upload['TANGGAL MASUK'], errors='coerce').dt.strftime('%Y-%m-%d')

    if st.button("Simpan ke Database"):
        try:
            mydb = koneksi()
            cursor = mydb.cursor()
            
            df_upload.columns = (df_upload.columns
                                .str.strip()
                                .str.lower()
                                .str.replace(" ", "_"))

            if 'id_dataset' in df_upload.columns:
                df_upload = df_upload.drop(columns=['id_dataset'])

            data_to_insert = [
                tuple(None if (pd.isna(val) or val is None) else val for val in row)
                for row in df_upload.itertuples(index=False)
            ]

            kolom = ", ".join([f"`{col}`" for col in df_upload.columns])
            nilai = ", ".join(["%s"] * len(df_upload.columns))
            query = f"INSERT INTO dataset ({kolom}) VALUES ({nilai})"
            
            cursor.executemany(query, data_to_insert)
            mydb.commit()
            
            st.success("Data berhasil disimpan ke database!")
            st.rerun()
            
        except Exception as e:  
            st.error(f"Terjadi kesalahan saat menyimpan data: {e}") 
        finally:
            cursor.close()
            mydb.close()

st.subheader("Data Bongkaran dari Database")
try:
    conn = koneksi()
    df_db = pd.read_sql("SELECT * FROM dataset", conn)
    conn.close()
    
    st.dataframe(df_db)

    null_df = pd.DataFrame({
        "Kolom": df_db.columns,
        "Jumlah Missing Value": df_db.isnull().sum().values
    })

    st.subheader("Jumlah Missing Value")
    st.dataframe(null_df, use_container_width=True)

except Exception as e:
    st.warning("Gagal mengambil data dari database atau database masih kosong.")
