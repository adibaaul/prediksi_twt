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
    
    if st.button("Simpan ke Database"):
        try:
            mydb = koneksi()
            cursor = mydb.cursor()
            df.columns = (df.columns
                            .str.strip()
                            .str.lower()
                            .str.replace(" ", "_"))

            if 'tanggal_masuk' in df.columns:
            df['tanggal_masuk'] = pd.to_datetime(df['tanggal_masuk'], errors='coerce').dt.strftime('%Y-%m-%d')

            # 4. Ganti SELURUH NaN/NaT menjadi None murni Python
            df = df.where(pd.notnull(df), None)
    
            # 5. Konversi dataframe ke list of tuples (Murni tipe data Python, bukan NumPy)
            data_values = [
                tuple(None if pd.isna(val) else val for val in row) 
                for row in df.itertuples(index=False)
            ]
    
            # 6. Susun query INSERT
            kolom = ", ".join([f"`{col}`" for col in df.columns])
            nilai = ", ".join(["%s"] * len(df.columns))
            query = f"INSERT INTO dataset ({kolom}) VALUES ({nilai})"
            
            # 7. Eksekusi
            cursor.executemany(query, data_values)
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
