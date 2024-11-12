import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title='Container Model', page_icon=':lab_coat:', layout='wide')

df = pd.read_excel(
    io='..\Container Model Reports\Container_Model_Report_2024_11_07_16-17-29.xlsx',
    engine='openpyxl',
)

df.index += 1
st.title("Container Models")
st.markdown(
    """
    ##### Data of Container Models recorded in Prisma Cloud CWP
    Use the **filter** sidebar to filter the data
    """
    
)
st.dataframe(df)