import streamlit as st
import pandas as pd
from koneksi import koneksi


uploaded_file = st.file_uploader("Unggah file DATASET Bongkaran", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    st.subheader("Preview Data Bongkaran")
    st.dataframe(df)
    df['TANGGAL MASUK'] = pd.to_datetime(df['TANGGAL MASUK']).dt.strftime('%Y-%m-%d')

    if st.button("Simpan ke Database"):
        try:
            mydb = koneksi()
            cursor = mydb.cursor()
            df.columns = (df.columns
                            .str.strip()
                            .str.lower()
                            .str.replace(" ", "_"))

            df_clean = df.where(pd.notnull(df), None)
            
            kolom = ", ".join([f"`{col}`" for col in df_clean.columns])
            nilai = ", ".join(["%s"] * len(df_clean.columns))
    
            query = f"INSERT INTO dataset ({kolom}) VALUES ({nilai})"
            
            # 6. Eksekusi simpan banyak data sekaligus
            cursor.executemany(query, df_clean.values.tolist())
            
            mydb.commit()
            st.success("Data berhasil disimpan ke database!")
        except Exception as e:  
            st.error(f"Terjadi kesalahan saat menyimpan data: {e}") 
        finally:
            cursor.close()
            mydb.close()

st.subheader("Data Bongkaran dari Database")
df = pd.read_sql("SELECT * FROM dataset", koneksi())
st.dataframe(df)

null_df = pd.DataFrame({
    "Kolom": df.columns,
    "Jumlah Missing Value": df.isnull().sum().values
})

st.subheader("Jumlah Missing Value")
st.dataframe(null_df, use_container_width=True)
