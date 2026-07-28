import streamlit as st
import pickle
from koneksi import koneksi
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

mydb = koneksi()
cursor = mydb.cursor()

cursor.execute("SELECT  COUNT(*) FROM dataset")
jumlah_dataset = cursor.fetchone()[0]



col1, col2 = st.columns(2)

col1.metric("📂 Dataset", jumlah_dataset)
st.subheader("Data Bongkaran dari Database")
df = pd.read_sql("SELECT * FROM dataset", koneksi())
st.dataframe(df)

def preprocess_data(df):
    kolom_fitur = ['id_dataset', 'customer', 'barang', 'tanggal_masuk', 'shift_masuk', 'trucking', 'durasi']
    df_ml = df[kolom_fitur].copy()
    df_ml = df_ml.dropna(subset=['trucking', 'barang'])
    id_dataset = df_ml['id_dataset']
    df_ml = df_ml.drop(columns=['id_dataset'])

    #hapus spasi, strip, huruf kecil
    df_ml['customer'] = df_ml['customer'].astype(str).str.lower().str.strip()
    df_ml['barang'] = df_ml['barang'].astype(str).str.lower().str.strip()

        #ekstrak bulan dan hari
    df_ml['tanggal_masuk'] = pd.to_datetime(df_ml['tanggal_masuk'])
    df_ml['bulan'] = df_ml['tanggal_masuk'].dt.month
    df_ml['hari'] = df_ml['tanggal_masuk'].dt.dayofweek

        #ubah ke numerik
    df_ml['trucking'] = df_ml['trucking'].astype(str)
    df_ml['trucking'] = df_ml['trucking'].str.replace(',000', '', regex=False).str.strip()
    df_ml['trucking'] = pd.to_numeric(df_ml['trucking'], errors='coerce').fillna(0)

        #ekstrak fitur musiman jagung
    df_jagung = df_ml[df_ml['barang'] == "jagung"].copy()

    tren_jagung = df_jagung.groupby('bulan').size().reset_index(name='total_bongkar')

    rata_bongkar = tren_jagung['total_bongkar'].mean()
    bulan_panen = tren_jagung[tren_jagung['total_bongkar']> rata_bongkar]['bulan'].tolist()

    def panen(row):
        if row['barang'] == "jagung" and row['bulan'] in bulan_panen:
            return 1
        else:
            return 0
            
    df_ml['panen'] = df_ml.apply(panen, axis=1)

    return df_ml, id_dataset, bulan_panen
    
def encoding(df_ml):
    df_encoded = pd.get_dummies(df_ml, columns=['customer', 'barang'], 
                            prefix=['customer', 'barang'], dtype=int)
    return df_encoded

col1, col2 = st.columns(2)

with col1:
    if st.button("Preprocessing Data", use_container_width=True):
        st.session_state['tombol_aktif'] = "preprocessing"
with col2:
    if st.button("Data Training", use_container_width=True):
        st.session_state['tombol_aktif'] = "trainig"
st.write("---")

if st.session_state['tombol_aktif'] == "preprocessing":
    st.write("Data Preprocessing sedang dilakukan...")
    # Lakukan preprocessing data di sini
    df_preprocessed, id_dataset, bulan_panen = preprocess_data(df)
    df_encoded = encoding(df_preprocessed)
    st.session_state.encoded_df = df_encoded
    st.session_state.id_dataset = id_dataset
    st.session_state.pre_done = True

    with open('bulan_panen.pkl', 'wb') as f:
            pickle.dump(bulan_panen, f)

    st.dataframe(df_encoded)
    st.success("Data Preprocessing selesai!")
    
elif st.session_state['tombol_aktif'] == "preprocessing":
    querrry = """SELECT d.* FROM testing t JOIN dataset d ON t.id_dataset = d.id_dataset"""
    df_train = pd.read_sql(querrry, koneksi())
    st.subheader("Data Training")
    st.dataframe(df_train)

if st.session_state.get("pre_done", False):
    if st.button("SPLIT DATASET"):
        st.write("Data Splitting sedang dilakukan...")
        # Lakukan splitting data di sini
        from sklearn.model_selection import train_test_split

        kolom_fitur2 = (
            ['bulan', 'hari', 'panen', 'shift_masuk'] +
            [col for col in st.session_state.encoded_df.columns if 'customer' in col] +
            [col for col in st.session_state.encoded_df.columns if 'barang' in col]
        )
        X = st.session_state.encoded_df[kolom_fitur2]
        y = st.session_state.encoded_df["durasi"]
        id_dataset = st.session_state.id_dataset

        X_train, X_test, y_train, y_test, id_training, id_testing = train_test_split(X, y, id_dataset, test_size=0.2, random_state=42)


        st.session_state.X_train = X_train
        st.session_state.X_test = X_test
        st.session_state.y_train = y_train
        st.session_state.y_test = y_test
        st.session_state.id_training = id_training
        st.session_state.id_testing = id_testing
        st.session_state.kolom_fitur2 = kolom_fitur2
        st.session_state.split = True

        with open('kolom_fitur.pkl', 'wb') as f:
            pickle.dump(kolom_fitur2, f)

        cursor.execute("DELETE FROM training")
        cursor.execute("DELETE FROM testing")

        # Masukkan ID data training
        for id_data in id_training:
            cursor.execute(
                """
                INSERT INTO training (id_dataset)
                VALUES (%s)
                """,
                (int(id_data),)
            )

        # Masukkan ID data testing
        for id_data in id_testing:
            cursor.execute(
                """
                INSERT INTO testing (id_dataset)
                VALUES (%s)
                """,
                (int(id_data),)
            )

        # Simpan perubahan
        mydb.commit()

        st.success("Data Splitting selesai!")

        #query = """SELECT d.* FROM training t JOIN dataset d ON t.id_dataset = d.id_dataset"""

        st.subheader("Data Training")
        st.dataframe(X_train)

if st.session_state.get("split", False):
    if st.button("TRAINING MODEL"):
        st.write("Training model sedang dilakukan...")
        # Lakukan training model di sini
        X_train = st.session_state.X_train
        y_train = st.session_state.y_train
        model_knn =  KNeighborsRegressor(n_neighbors=9)
        model_knn.fit(X_train, y_train)

        model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
        model_rf.fit(X_train, y_train)

        with open('model_knn.pkl', 'wb') as f:
            pickle.dump(model_knn, f)

        with open('model_rf.pkl', 'wb') as f:
            pickle.dump(model_rf, f)
                
        st.success("Training model selesai!")
