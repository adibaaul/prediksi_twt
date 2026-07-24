import streamlit as st
import pandas as pd
import numpy as np
import pickle
from koneksi import koneksi


###################################
#1. SETTING HALAMAN
###################################

st.set_page_config(page_title="Prediksi Cas Inap", layout="wide")

st.title("Sistem Prediksi Cas Inap")
st.write("Silahkan input file CSV")

@st.cache_resource
def load_model():
    with open('model_rf.pkl', 'rb') as f:
        model_rf = pickle.load(f)
    with open('kolom_fitur.pkl', 'rb') as f:
        kolom_fitur = pickle.load(f)
    return model_rf, kolom_fitur

try:
    model_rf, kolom_fitur = load_model()
except FileNotFoundError:
    st.error("KACAWWWWWWWWWWW")
    st.stop()


####################################
#2. FUNGSI SIMPAN RIWAYAT KE DB
####################################
def simpan_riwayat_ke_db(df_hasil, kolom_durasi_pred, kolom_biaya_casinap):
  """Fungsi untuk menyimpan hasil prediksi ke tabel 'riwayat'

  Tabel riwayat diasumsikan memiliki struktur:
  (id_riwayat INT AUTO_INCREMENT PRIMARY KEY, id_prediksi VARCHAR/INT,
  hasil_durasi FLOAT, hasil_cas_inap DOUBLE)
  """
  try:
    mydb = koneksi()
    cursor = mydb.cursor()

    # Siapkan data yang akan diinsert
    # id_riwayat biasanya AUTO_INCREMENT di MySQL, jadi cukup insert id_prediksi, durasi, dan biaya
    data_riwayat = []
    for idx, row in df_hasil.iterrows():
      # Pastikan id_prediksi ada, jika tidak gunakan index
      id_pred = row.get("id_prediksi", idx + 1)
      durasi = float(row[kolom_durasi_pred])
      cas_inap = float(row[kolom_biaya_casinap])
      data_riwayat.append((id_pred, durasi, cas_inap))

    query = """
            INSERT INTO riwayat (id_prediksi, hasil_durasi, hasil_cas_inap) 
            VALUES (%s, %s, %s)
        """
    cursor.executemany(query, data_riwayat)
    mydb.commit()

    st.success(
        f"✅ Berhasil menyimpan {len(data_riwayat)} baris hasil prediksi ke"
        " tabel riwayat!"
    )
  except Exception as e:
    st.error(f"❌ Gagal menyimpan riwayat ke database: {e}")
  finally:
    if "cursor" in locals():
      cursor.close()
    if "mydb" in locals():
      mydb.close()

####################################
#2. PROSES PROCESSING DATA
####################################

def get_max_id_prediksi():
    try:
        mydb = koneksi()
        cursor = mydb.cursor()
        cursor.execute("SELECT MAX(id_prediksi) FROM riwayat")
        result = cursor.fetchone()
        max_id = result[0] if result[0] is not None else 0
        return max_id
    except Exception as e:
        return 0
    finally:
        if "cursor" in locals():
            cursor.close()
        if "mydb" in locals():
            mydb.close()
            
def preprocess_data(df):
  # Buat copy agar tidak mengubah dataframe asli secara tak sengaja
  df_ml = df.copy()

  # Bersihkan nama kolom
  df_ml.columns = (
      df_ml.columns.str.strip().str.lower().str.replace(" ", "_")
  )

  # Penanganan missing values
  if "trucking" in df_ml.columns and "vendor" in df_ml.columns:
    df_ml = df_ml.dropna(subset=["trucking", "vendor"])

  # Ambil id_prediksi jika ada
      if "id_prediksi" in df_ml.columns:
        id_prediksi = df_ml["id_prediksi"]
      else:
        # Ambil ID terakhir di database (misal: 9)
        last_id = get_max_id_prediksi()
        
        # Buat urutan baru melanjutkan last_id (misal: 10, 11, 12, dst.)
        id_prediksi = pd.Series(range(last_id + 1, last_id + 1 + len(df_ml)))
        
        # Simpan ke dataframe agar terikat ke setiap baris
        df_ml["id_prediksi"] = id_prediksi

  # Hapus spasi & ubah ke lowercase
  if "customer" in df_ml.columns:
    df_ml["customer"] = (
        df_ml["customer"].astype(str).str.lower().str.strip()
    )
  if "barang" in df_ml.columns:
    df_ml["barang"] = df_ml["barang"].astype(str).str.lower().str.strip()

  # Ekstrak bulan dan hari dari tanggal_masuk
  if "tanggal_masuk" in df_ml.columns:
    df_ml["tanggal_masuk"] = pd.to_datetime(df_ml["tanggal_masuk"])
    df_ml["bulan"] = df_ml["tanggal_masuk"].dt.month
    df_ml["hari"] = df_ml["tanggal_masuk"].dt.dayofweek

  # Ubah trucking ke numerik
  if "trucking" in df_ml.columns:
    df_ml["trucking"] = df_ml["trucking"].astype(str)
    df_ml["trucking"] = (
        df_ml["trucking"].str.replace(",000", "", regex=False).str.strip()
    )
    df_ml["trucking"] = pd.to_numeric(
        df_ml["trucking"], errors="coerce"
    ).fillna(0)

  # Feature engineering musiman panen jagung
  try:
    with open("bulan_panen.pkl", "rb") as f:
      bulan_panen = pickle.load(f)
  except FileNotFoundError:
    bulan_panen = []

  def panen(row):
    if (
        "barang" in row
        and row["barang"] == "jagung"
        and "bulan" in row
        and row["bulan"] in bulan_panen
    ):
      return 1
    return 0

  df_ml["panen"] = df_ml.apply(panen, axis=1)

  return df_ml, id_prediksi


def encoding(df_ml):
  cols_to_encode = [
      col for col in ["customer", "barang"] if col in df_ml.columns
  ]
  df_encoded = pd.get_dummies(
      df_ml, columns=cols_to_encode, prefix=cols_to_encode, dtype=int
  )
  return df_encoded

#==========================================
#3. KOMPONEN UNGGAH FILE
#==========================================

uploaded_file = st.file_uploader(
    "Unggah file DATASET Bongkaran", type=["xlsx", "csv"]
)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    st.subheader("Preview Data Bongkaran")
    st.dataframe(df)

    # 1. Simpan Dataset Awal ke Database (tabel data_baru)
    if st.button("Simpan Dataset ke DB (data_baru)"):
        try:
            df_save = df.copy()
            if "TANGGAL MASUK" in df_save.columns:
                df_save["TANGGAL MASUK"] = pd.to_datetime(
                    df_save["TANGGAL MASUK"], errors='coerce'
                ).dt.strftime("%Y-%m-%d")

            df_save.columns = (
                df_save.columns.str.strip().str.lower().str.replace(" ", "_")
            )

            # Konversi NaN ke None murni Python agar aman
            data_to_insert = [
                tuple(None if pd.isna(val) else val for val in row)
                for row in df_save.itertuples(index=False)
            ]

            mydb = koneksi()
            cursor = mydb.cursor()
            kolom = ", ".join([f"`{col}`" for col in df_save.columns])
            nilai = ", ".join(["%s"] * len(df_save.columns))

            query = f"INSERT INTO data_baru ({kolom}) VALUES ({nilai})"
            cursor.executemany(query, data_to_insert)
            mydb.commit()
            st.success("✅ Data berhasil disimpan ke tabel data_baru!")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat menyimpan data: {e}")
        finally:
            if "cursor" in locals():
                cursor.close()
            if "mydb" in locals():
                mydb.close()

    st.write("---")
    
    # -------------------------------------------------------------
    # TOMBOL EKSPLISIT UNTUK MEMULAI PREDIKSI
    # (Preprocessing HANYA berjalan jika tombol ini diklik)
    # -------------------------------------------------------------
    if st.button("🚀 Jalankan Prediksi Random Forest", use_container_width=True):
        with st.spinner("Memproses data & melakukan prediksi..."):
            # Preprocessing & Encoding baru dipanggil di SINI:
            df_preprocessed, id_prediksi = preprocess_data(df)
            df_encoded = encoding(df_preprocessed)

            # Reindex fitur
            X_test = df_encoded.reindex(columns=kolom_fitur, fill_value=0)
            y_pred = model_rf.predict(X_test)

            # Buat dataframe hasil prediksi
            df_preprocessed["durasi_1_prediksi"] = y_pred

            # Hitung Biaya Cas Inap
            trucking_val = pd.to_numeric(
                df_preprocessed.get("trucking", 0), errors="coerce"
            ).fillna(0)
            
            kondisi = [
                (df_preprocessed["durasi_1_prediksi"] >= 72),
                (df_preprocessed["durasi_1_prediksi"] >= 48),
                (df_preprocessed["durasi_1_prediksi"] >= 24),
            ]
            pilihan_pengali = [
                trucking_val * 2.0,
                trucking_val * 1.0,
                trucking_val * 0.5,
            ]
            df_preprocessed["Prediksi Biaya Cas Inap"] = np.select(
                kondisi, pilihan_pengali, default=0
            )

            if "durasi_1_aktual" in df_preprocessed.columns:
                df_preprocessed["selisih"] = (
                    df_preprocessed["durasi_1_aktual"]
                    - df_preprocessed["durasi_1_prediksi"]
                )

            # Simpan hasil sementara ke session_state agar tampil di layar
            st.session_state["df_hasil_prediksi"] = df_preprocessed

    # -------------------------------------------------------------
    # TAMPILKAN HASIL PREDIKSI & TOMBOL SIMPAN KE RIWAYAT
    # -------------------------------------------------------------
    if "df_hasil_prediksi" in st.session_state:
        st.subheader("Hasil Prediksi Random Forest")
        st.dataframe(st.session_state["df_hasil_prediksi"])

        # Tombol simpan berdiri sendiri dan TIDAK akan auto-save
        if st.button("💾 Simpan Hasil Ini ke Tabel Riwayat", type="primary"):
            simpan_riwayat_ke_db(
                st.session_state["df_hasil_prediksi"],
                kolom_durasi_pred="durasi_1_prediksi",
                kolom_biaya_casinap="Prediksi Biaya Cas Inap",
            )
