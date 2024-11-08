import streamlit as st

st.set_page_config(
    page_title="Prisma Cloud CWP",
    page_icon="👋",
)

st.write("# Welcome to Prisma Cloud CWP Dashboard! 👋")

st.markdown(
    """
    # Get Started

    _Please click one of the buttons below to generate the data required for the dashboard_

    **Notes:** 
    1. This action will fetch all the data from the Prisma Cloud API
    2. The data collection process will take approximately 1-5 minutes

    """
    
)
st.button("Generate WAAS Data", type="primary")
st.button("Generate Container Models Data", type="primary")

st.markdown(
    """
    # WAAS Events and Container Models Dashboard

This app provides an **interactive dashboard** for viewing and analyzing **WAAS (Web Application and API Security) events** and **Container Models** from **Prisma Cloud**. Users can explore detailed security events, identify **attack types**, and review associated container images directly from the Prisma Cloud data.

### How to Use
Navigate through the data using the **sidebar filters**:
- Use the **"Attack Type"** filter to select specific attack types or view all by choosing the **"Select All"** option.
- The **"Image"** filter allows you to view events linked to particular container images.

This streamlined interface helps **security teams** quickly focus on relevant events and models for **efficient monitoring and response**.
    
"""
    
)

st.sidebar.info("Select a page above.")