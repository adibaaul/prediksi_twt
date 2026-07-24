import streamlit as st
import pickle
from koneksi import koneksi
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error

query = """SELECT d.* FROM testing t JOIN dataset d ON t.id_dataset = d.id_dataset"""
df_test = pd.read_sql(query, koneksi())
st.subheader("Data Testing")
st.dataframe(df_test)

def preprocess_data(df):
    kolom_fitur = ['id_dataset', 'customer', 'barang', 'vendor', 'tanggal_masuk', 'shift_masuk', 'trucking', 'durasi']
    df_ml = df[kolom_fitur].copy()
    df_ml = df_ml.dropna(subset=['trucking', 'barang'])
    id_dataset = df_ml['id_dataset']
    df_ml = df_ml.drop(columns=['id_dataset'])

    #hapus spasi, strip, huruf kecil
    df_ml['customer'] = df_ml['customer'].astype(str).str.lower().str.strip()
    df_ml['barang'] = df_ml['barang'].astype(str).str.lower().str.strip()
    df_ml['vendor'] = df_ml['vendor'].astype(str).str.lower().str.strip()

        #ekstrak bulan dan hari
    df_ml['tanggal_masuk'] = pd.to_datetime(df_ml['tanggal_masuk'])
    df_ml['bulan'] = df_ml['tanggal_masuk'].dt.month
    df_ml['hari'] = df_ml['tanggal_masuk'].dt.dayofweek

        #ubah ke numerik
    df_ml['trucking'] = df_ml['trucking'].astype(str)
    df_ml['trucking'] = df_ml['trucking'].str.replace(',000', '', regex=False).str.strip()
    df_ml['trucking'] = pd.to_numeric(df_ml['trucking'], errors='coerce').fillna(0)

        #ekstrak fitur musiman jagung
    with open('bulan_panen.pkl', 'rb') as f:
        bulan_panen = pickle.load(f)

    def panen(row):
        if row['barang'] == "jagung" and row['bulan'] in bulan_panen:
            return 1
        else:
            return 0
            
    df_ml['panen'] = df_ml.apply(panen, axis=1)

    return df_ml, id_dataset
    
def encoding(df_ml):
    df_encoded = pd.get_dummies(df_ml, columns=['customer', 'barang'], 
                            prefix=['customer', 'barang'], dtype=int)
    return df_encoded

def evaluasi_model(model_knn, model_rf, X_test, y_test):

    prediksi_knn = model_knn.predict(X_test)
    prediksi_rf = model_rf.predict(X_test)

    hasil = {
        "KNN": {
            "MAE": mean_absolute_error(y_test, prediksi_knn)
        },
        "Random Forest": {
            "MAE": mean_absolute_error(y_test, prediksi_rf)
        }
    }

    return hasil

df_preprocessed, id_dataset = preprocess_data(df_test)
df_encoded = encoding(df_preprocessed)
st.session_state.encoded_df = df_encoded
st.session_state.id_dataset = id_dataset


col1, col2 = st.columns(2)

with col1:
    if st.button("K-Nearest Neighbor", use_container_width=True):
        st.session_state['tombol_aktif'] = "knn_regresi"
with col2:
    if st.button("Random Forest", use_container_width=True):
        st.session_state['tombol_aktif'] = "rf_regresi"
st.write("---")

if st.session_state['tombol_aktif'] == "knn_regresi":
    with st.spinner("Melakukan prediksi dengan K-Nearest Neighbors..."):
        # Load model KNN
        with open('model_knn.pkl', 'rb') as file:
            model_knn = pickle.load(file)

        # Ambil data testing yang sudah di-preprocess
        with open('kolom_fitur.pkl', 'rb') as file:
            kolom_fitur2 = pickle.load(file)
            X_test = st.session_state.encoded_df.reindex(columns=kolom_fitur2, fill_value=0)    
            y_test = st.session_state.encoded_df['durasi']

            # Lakukan prediksi
            y_pred = model_knn.predict(X_test)
            

            # Tampilkan hasil prediksi
            df_test['trucking'] = pd.to_numeric(df_test['trucking'], errors = 'coerce')
            hasil_prediksi_1 = df_test[[
                'customer',
                'barang',
                'vendor',
                'tanggal_masuk',
                'shift_masuk',
                'trucking'
            ]].copy()
            hasil_prediksi_1['durasi_1_aktual'] = y_test
            hasil_prediksi_1['durasi_1_prediksi'] = y_pred
            #cek apakah aktual dan prediksi mengalami cas inao
            kondisi = [
                (hasil_prediksi_1['durasi_1_prediksi']>=72),
                (hasil_prediksi_1['durasi_1_prediksi']>=48),
                (hasil_prediksi_1['durasi_1_prediksi']>=24)
            ]
            pilihan_pengali = [
                df_test['trucking'] * 2.0,
                df_test['trucking'] * 1,
                df_test['trucking'] * 0.5
            ]
            hasil_prediksi_1['Prediksi Biaya Cas Inap'] = np.select(kondisi, pilihan_pengali, default=0)
            hasil_prediksi_1['cas inap riil'] = df_test['cas_inap']
            aktual_cas = hasil_prediksi_1['cas inap riil'] > 0
            pred_cas = hasil_prediksi_1['Prediksi Biaya Cas Inap'] >0
            kondisi_cm = [
                (~aktual_cas & ~pred_cas),
                (aktual_cas & pred_cas),
                (~aktual_cas & pred_cas),
                (aktual_cas & ~pred_cas)
            ]
            pilihan_cm = ['TN', 'TP', 'FP', 'FN'
            ]
            hasil_prediksi_1['Confussion Matriks'] = np.select(kondisi_cm, pilihan_cm, default='-')
            
            st.subheader("Hasil Prediksi K-Nearest Neighbors")
            st.dataframe(hasil_prediksi_1)

elif st.session_state['tombol_aktif'] == "rf_regresi":
    with st.spinner("Melakukan prediksi dengan Random Forest..."):
            # Load model Random Forest
        with open('model_rf.pkl', 'rb') as file:
            model_rf = pickle.load(file)

            # Ambil data testing yang sudah di-preprocess
        with open('kolom_fitur.pkl', 'rb') as file:
            kolom_fitur2 = pickle.load(file)
            X_test = st.session_state.encoded_df.reindex(columns=kolom_fitur2, fill_value=0)    
            y_test = st.session_state.encoded_df['durasi']
            # Lakukan prediksi
            y_pred = model_rf.predict(X_test)

            # Tampilkan hasil prediksi
            df_test['trucking'] = pd.to_numeric(df_test['trucking'], errors = 'coerce')
            hasil_prediksi = df_test[[
                'id_dataset',
                'customer',
                'barang',
                'vendor',
                'tanggal_masuk',
                'shift_masuk',
                'trucking'
            ]].copy()
            hasil_prediksi['durasi_1_aktual'] = y_test
            hasil_prediksi['durasi_1_prediksi'] = y_pred
            kondisi = [
                (hasil_prediksi['durasi_1_prediksi']>=72),
                (hasil_prediksi['durasi_1_prediksi']>=48),
                (hasil_prediksi['durasi_1_prediksi']>=24)
            ]
            pilihan_pengali = [
                df_test['trucking'] * 2.0,
                df_test['trucking'] * 1,
                df_test['trucking'] * 0.5
            ]
            hasil_prediksi['selisih'] = hasil_prediksi['durasi_1_aktual'] - hasil_prediksi['durasi_1_prediksi']
            hasil_prediksi['Prediksi Biaya Cas Inap'] = np.select(kondisi, pilihan_pengali, default=0)
            hasil_prediksi['cas inap riil'] = df_test['cas_inap']
            aktual_cas = hasil_prediksi['cas inap riil'] > 0
            pred_cas = hasil_prediksi['Prediksi Biaya Cas Inap'] >0
            kondisi_cm = [
                (~aktual_cas & ~pred_cas),
                (aktual_cas & pred_cas),
                (~aktual_cas & pred_cas),
                (aktual_cas & ~pred_cas)
            ]
            pilihan_cm = ['TN', 'TP', 'FP', 'FN'
            ]
            hasil_prediksi['Confussion Matriks'] = np.select(kondisi_cm, pilihan_cm, default='-')
            
            st.subheader("Hasil Prediksi Random Forest  ")
            st.dataframe(hasil_prediksi)

col1, col2 = st.columns(2)
with col1:
    if st.button("Hasil Evaluasi", use_container_width=True):
        st.session_state['tombol_aktif'] = "evaluasi"
st.write("---")

if st.session_state['tombol_aktif'] == "evaluasi":
    with st.spinner("Melakukan evaluasi model..."):
        # Load model KNN dan Random Forest
        with open('model_knn.pkl', 'rb') as file:
            model_knn = pickle.load(file)
        with open('model_rf.pkl', 'rb') as file:
            model_rf = pickle.load(file)
        with open('kolom_fitur.pkl', 'rb') as file:
            kolom_fitur2 = pickle.load(file)
        X_test = st.session_state.encoded_df.reindex(columns=kolom_fitur2, fill_value=0)    
        y_test = st.session_state.encoded_df['durasi']

        # Ambil data testing yang sudah di-preprocess
        prediksi_knn = model_knn.predict(X_test)
        prediksi_rf = model_rf.predict(X_test)

        def hitung_cm(y_aktual_durasi, y_pred_durasi, df_trucking, cas_inap_riil):
            # Hitung estimasi biaya berdasarkan durasi prediksi
            kondisi = [
                (y_pred_durasi >= 72),
                (y_pred_durasi >= 48),
                (y_pred_durasi >= 24)
            ]
            pilihan_pengali = [
                df_trucking * 2.0,
                df_trucking * 1.0,
                df_trucking * 0.5
            ]
            pred_biaya = np.select(kondisi, pilihan_pengali, default=0)
            
            # Cek status biner (Apakah ada biaya > 0)
            aktual_cas = cas_inap_riil > 0
            pred_cas = pred_biaya > 0
            
            # Hitung jumlah masing-masing kuadran
            tn = int(((~aktual_cas) & (~pred_cas)).sum())
            tp = int((aktual_cas & pred_cas).sum())
            fp = int(((~aktual_cas) & pred_cas).sum())
            fn = int((aktual_cas & (~pred_cas)).sum())
            
            return tn, tp, fp, fn

        # Hitung untuk KNN
        tn_knn, tp_knn, fp_knn, fn_knn = hitung_cm(
            y_test, prediksi_knn, df_test['trucking'], df_test['cas_inap']
        )
        
        # Hitung untuk Random Forest
        tn_rf, tp_rf, fp_rf, fn_rf = hitung_cm(
            y_test, prediksi_rf, df_test['trucking'], df_test['cas_inap']
        )

        hasil = {
            "KNN": {
                "MAE": mean_absolute_error(y_test, prediksi_knn),
                "Benar Tidak Cas Inap": tn_knn,
                "Benar Kena Cas Inap": tp_knn,
                "Salah Prediksi: Kena padahal Tidak": fp_knn,
                "Salah Prediksi: Tidak padahal Kena": fn_knn
            },
            "Random Forest": {
                "MAE": mean_absolute_error(y_test, prediksi_rf),
                "Benar Tidak Cas Inap": tn_rf,
                "Benar Kena Cas Inap": tp_rf,
                "Salah Prediksi: Kena padahal Tidak": fp_rf,
                "Salah Prediksi: Tidak padahal Kena": fn_rf
            }
        }
        st.subheader("Hasil Evaluasi Model")
        st.dataframe(pd.DataFrame(hasil))


