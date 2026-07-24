import streamlit as st
import pandas as pd
from koneksi import koneksi

st.subheader("Riwayat Prediksi")
query = """SELECT d.id_prediksi,
        d.customer,
        d.barang,
        d.vendor,
        d.tanggal_masuk,
        d.trucking,
        t.hasil_durasi,
        t.hasil_cas_inap FROM riwayat t JOIN data_baru d ON t.id_prediksi = d.id_prediksi ORDER BY t.id_riwayat DESC"""

try:
    conn = koneksi()
    df = pd.read_sql(query, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada riwayat prediksi yang tersimpan.")

except Exception as e:
  st.error(f"Gagal mengambil data riwayat: {e}")