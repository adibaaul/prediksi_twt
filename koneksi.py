import mysql.connector
import streamlit as st

def koneksi():
    db_config = st.secrets["database"]
    mydb = mysql.connector.connect(
        host=db_config["host"],
        port=int(db_config["port"]),
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        ssl_disabled = False,
    )
    return mydb
