import streamlit as st
from koneksi import koneksi



# --- APLIKASI STREAMLIT ---
st.title('Prediksi CAS INAP')
st.logo("asset/niagaa.png")

if 'sudah_login' not in st.session_state: st.session_state.sudah_login = False

if not st.session_state.sudah_login:
    with st.form('login_form'):
        user = st.text_input('Username')
        pwd = st.text_input('Password', type='password')
        if st.form_submit_button("Login"):
            query = "SELECT * FROM user WHERE username=%s AND password=%s"
            mydb = koneksi()
            mycursor = mydb.cursor()
            mycursor.execute(query, (user, pwd))
            result = mycursor.fetchone()
            if result:
                st.session_state.sudah_login = True
                st.session_state.username = result[1]  # Menyimpan username ke session state
                st.success('Login berhasil!')
                st.rerun() 
                mycursor.close()
                mydb.close()
            else: st.error('Salah password!')
            mycursor.close()
            mydb.close()
else:
    if st.sidebar.button("Logout"): 
        st.session_state.sudah_login = False; st.rerun()

    st.set_page_config(page_title="Prediksi Surcharge", page_icon=":bar_chart:", layout="wide")

    # Cukup panggil nama filenya langsung karena tidak di dalam folder apa pun
    halaman_project = st.Page("dashboard.py", title="Dashboard", icon="📁")
    halaman_dataset = st.Page("dataset.py", title="Dataset", icon="📂")
    halaman_tes = st.Page("casinap.py", title="Prediksi", icon="📊")
    halaman_training = st.Page("training.py", title="Training Model", icon="🧠")
    halaman_testing = st.Page("evaluasi.py", title="Testing Model", icon="🧪")
    halaman_riwayat = st.Page("riwayat.py", title="Riwayat Prediksi", icon="🎯")


    pg = st.navigation([halaman_project, halaman_dataset, halaman_training, halaman_testing, halaman_tes, halaman_riwayat])
    pg.run()
