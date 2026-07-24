import streamlit as st
import pandas as pd
from koneksi import koneksi

mydb = koneksi()
cursor = mydb.cursor()

cursor.execute("SELECT  COUNT(*) FROM dataset")
jumlah_dataset = cursor.fetchone()[0]

cursor.execute("SELECT  COUNT(*) FROM data_baru")
jumlah_training = cursor.fetchone()[0]

cursor.execute("SELECT  COUNT(*)     FROM riwayat")
jumlah_testing = cursor.fetchone()[0]




st.write("Selamat Datang!", st.session_state.username)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.metric("📂 Dataset", jumlah_dataset)

with col2:
    with st.container(border=True):
        st.metric("🧠 Data Baru", jumlah_training)

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.metric("🧪 Riwayat Prediksi", jumlah_testing)

with col4:
    with st.container(border=True):
        st.metric("📈 Model", "KNN, Random Forest")

data = {
    'OWNER' : ['A', 'B', 'C'],
    'CUSTOMER': ['A', 'B', 'C'],
    'LOKASI': ['Jakarta', 'Bandung', 'Surabaya'],
    'NO CONTAINER': ['ABC123', 'DEF456', 'GHI789'],
    'TIPE CONTAINER': ['20', '40', '20'],
    'BARANG': ['jagung', 'beras', 'gula'],
    'VENDOR': ['X', 'Y', 'Z'],
    'TANGGAL': ['2024-01-01', '2024-02-01', '2024-03-01'],
    'SHIFT' : ['1', '1,', '2'],
    'TRUCKING': [1000, 2000, 1500]
}


df = pd.DataFrame(data)

st.write("Selamat Datang!")
st.write("File CSV yang diunggah harus memiliki format seperti tabel di bawah ini. Pastikan kolom-kolomnya sesuai dengan contoh agar prediksi dapat dilakukan dengan benar.")

st.write("Contoh Format File CSV")
st.dataframe(df)

st.write("Catatan penting:")
st.write("1. File bisa berformat CSV atau EXCEL")
st.write("2. Pastikan semua kolom-kolom yang sesuai dengan contoh di atas")
st.write("3. Format Tanggal harus YY/MM/DD")

