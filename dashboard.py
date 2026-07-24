import streamlit as st
from koneksi import koneksi

mydb = koneksi()
cursor = mydb.cursor()

cursor.execute("SELECT  COUNT(*) FROM dataset")
jumlah_dataset = cursor.fetchone()[0]

cursor.execute("SELECT  COUNT(*) FROM training")
jumlah_training = cursor.fetchone()[0]

cursor.execute("SELECT  COUNT(*)     FROM testing")
jumlah_testing = cursor.fetchone()[0]




st.write("Selamat Datang!", st.session_state.username)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.metric("📂 Dataset", jumlah_dataset)

with col2:
    with st.container(border=True):
        st.metric("🧠 Training", jumlah_training)

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.metric("🧪 Testing", jumlah_testing)

with col4:
    with st.container(border=True):
        st.metric("📈 Model", "KNN, Random Forest")