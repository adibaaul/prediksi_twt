import streamlit as st
import pandas as pd
import numpy as np
import pickle


###################################
#1. SETTING HALAMAN
###################################

st.set_page_config(page_title="Prediksi Cas Inap", layout="wide")

st.title("Sistem Prediksi Cas Inap")
st.write("Silahkan input file CSV")

@st.cache_resource
def load_model():
    with open('model_knn.pkl', 'rb') as f:
        model_knn = pickle.load(f)
    with open('model_rf.pkl', 'rb') as f:
        model_rf = pickle.load(f)
    with open('kolom_fitur.pkl', 'rb') as f:
        kolom_fitur = pickle.load(f)
    return model_knn, model_rf, kolom_fitur

try:
    model_knn, model_rf, kolom_fitur = load_model()
except FileNotFoundError:
    st.error("KACAWWWWWWWWWWW")
    st.stop()


####################################
#2. PROSES EKSTRAK DAN ENCODING
####################################
query = ""

def proses_encoded(file_csv):
    df_baru = pd.read_csv(file_csv)
    df = df_baru.copy()

    #hapus spasi, strip, huruf kecil
    df['CUSTOMER'] = df['CUSTOMER'].astype(str).str.lower().str.strip()
    df['BARANG'] = df['BARANG'].astype(str).str.lower().str.strip()
    df['VENDOR'] = df['VENDOR'].astype(str).str.lower().str.strip()

    #ekstrak bulan dan hari
    df['TANGGAL MASUK'] = pd.to_datetime(df['TANGGAL MASUK'])
    df['BULAN'] = df['TANGGAL MASUK'].dt.month
    df['HARI'] = df['TANGGAL MASUK'].dt.dayofweek

    #ubah ke numerik
    df['TRUCKING'] = df['TRUCKING'].astype(str)
    df['TRUCKING'] = df['TRUCKING'].str.replace(',000', '', regex=False).str.strip()
    df['TRUCKING'] = pd.to_numeric(df['TRUCKING'], errors='coerce').fillna(0)

    #ekstrak fitur musiman jagung
    df_jagung = df[df['BARANG'] == "jagung"].copy()

    tren_jagung = df_jagung.groupby('BULAN').size().reset_index(name='total_bongkar')

    rata_bongkar = tren_jagung['total_bongkar'].mean()
    bulan_panen = tren_jagung[tren_jagung['total_bongkar']> rata_bongkar]['BULAN'].tolist()

    def panen(row):
        if row['BARANG'] == "jagung" and row['BULAN'] in bulan_panen:
            return 1
        else:
            return 0
        
    df['PANEN'] = df.apply(panen, axis=1)

    df_encoded_baru = pd.get_dummies(df, columns=['CUSTOMER', 'BARANG'], 
                            prefix=['customer', 'barang'], dtype=int)

    X_baru = df_encoded_baru.reindex(columns=kolom_fitur, fill_value=0)
    return df_baru, X_baru

#==========================================
#3. KOMPONEN UNGGAH FILE
#==========================================

file_terinput = st.file_uploader("pilih file csv terbaru", type=["csv"])

if 'tombol_aktif' not in st.session_state:
    st.session_state['tombol_aktif'] = None

if 'file_sebelumnya' not in st.session_state:
    st.session_state['file_sebelumnya'] = None

if file_terinput is not None:

    if file_terinput != st.session_state['file_sebelumnya']:
        st.session_state['tombol_aktif'] = None
        st.session_state['file_sebelumnya'] = file_terinput
        st.rerun()

    st.write("---")
    st.write("**Klik Tombol di Bawah untuk Mulai Prediksi:**")
    
    #membuat 2 tombol berjejer horizontal menggunakan kolom
    col1, col2 = st.columns(2)

    with col1:
        if st.button("K-Nearest Neighbor", use_container_width=True):
            st.session_state['tombol_aktif'] = "knn_regresi"
    with col2:
        if st.button("Random Forest", use_container_width=True):
            st.session_state['tombol_aktif'] = "rf_regresi"
    st.write("---")

# ==========================================
# 4. HASIL TAMPILAN
# ==========================================
    if st.session_state['tombol_aktif'] == "knn_regresi":
        with st.spinner("Menghitung Menggunakan KNN Regresi..."):
            df_asal, X_data = proses_encoded(file_terinput)
            pred = model_knn.predict(X_data)
            df_asal['TWT'] = pred
            kondisi = [
                (df_asal['TWT']>=72),
                (df_asal['TWT']>=48),
                (df_asal['TWT']>=24)
            ]
            pilihan_pengali = [
                df_asal['TRUCKING'] * 2.0,
                df_asal['TRUCKING'] * 1,
                df_asal['TRUCKING'] * 0.5
            ]
            df_asal['Prediksi Biaya Cas Inap'] = np.select(kondisi, pilihan_pengali, default=0)

            st.subheader("Tabel Hasil Prediksi Kargo (K-Nearest Neighbor)")
            st.dataframe(df_asal, use_container_width=True)
        
    elif st.session_state['tombol_aktif'] == "rf_regresi":
        with st.spinner("Menghitung Menggunakan Random Forest Regresi..."):
            df_asal, X_data = proses_encoded(file_terinput)
            pred = model_rf.predict(X_data)
            df_asal['TWT'] = pred
            kondisi = [
                (df_asal['TWT']>=72),
                (df_asal['TWT']>=48),
                (df_asal['TWT']>=24)
            ]
            pilihan_pengali = [
                df_asal['TRUCKING'] * 2.0,
                df_asal['TRUCKING'] * 1,
                df_asal['TRUCKING'] * 0.5
            ]
            df_asal['Prediksi Biaya Cas Inap'] = np.select(kondisi, pilihan_pengali, default=0)


            st.subheader("Tabel Hasil Prediksi Kargo (Random Forest)")
            st.dataframe(df_asal, use_container_width=True)

    else:
        st.error("Kolom 'TRUCKING' tidak ditemukan di dalam file CSV!") 
