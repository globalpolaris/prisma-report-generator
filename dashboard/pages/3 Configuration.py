import streamlit as st
import os

st.set_page_config(page_title='Set Environment Variable', page_icon=':bar_chart:', layout='wide')
st.write("Configure **Console Path** and **Token** from this page.")

curr_console_path = os.environ.get('CONSOLE_PATH')
console_path = st.text_input("Console Path", curr_console_path)
token = st.text_input("Token", placeholder="Base64 Authentication Token")

if st.button("Set Environment Variable"):
    # Set the environment variable
    os.environ["CONSOLE_PATH"] = console_path
    os.environ["TOKEN"] = token
    st.success("Environment variables 'Console Path' and 'Token' have been set.")