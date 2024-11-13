import streamlit as st
import db, time
import importlib.util, os

module_name = 'prisma_report_generator'
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'prisma_report_generator.py'))
spec = importlib.util.spec_from_file_location(module_name, module_path)
parent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent_module)

st.set_page_config(
    page_title="Prisma Cloud CWP",
    page_icon="👋",
)

st.write("# Welcome to Prisma Cloud CWP Dashboard! 👋")

st.markdown(
    """
    
    ### **Before you get started**
    **1. Click the button below to initialize the database**
    
    _You only need to perform this once_
            
    """
)
if st.button("Initialize Database", type="secondary"):
    with st.spinner("Initializing database..."):
        db_res = db.create_db()
        if db_res is not None:
            st.error("Failed to initialize database: {}".format(db_res))
        else:
            st.success("Database initialized successfully!")

st.markdown(
    """
    **2. Configure the environment variables**
    
    Click the button below to configure the environment variables
    """
)

st.link_button("Configure Environment Variable", url="/Configuration")

st.markdown(
    """
    
    
    
    """
    
)
st.write("# WAAS Events")
st.write()
st.write("#### 1. Generate WAAS Data")
st.write("Before you can access the WAAS page, please generate the data if no data is on the list of reports.")
if st.button("Generate WAAS Data", type="primary"):
    console_path = os.environ.get('CONSOLE_PATH')
    token = os.environ.get('TOKEN')
    if console_path is None or console_path == "" or token is None or token == "":
        st.error("Missing environment variable")
    else:
        with st.spinner("Generating WAAS data..."):
            status_code = parent_module.generate_waas_report()
            print("Status Code: ", status_code)
            if status_code != 200 and status_code is not None:
                st.error("Failed to generate WAAS data: {} - Check the environment variable configuration.".format(status_code))
            else:
                success = st.success("WAAS data generated successfully!")
                time.sleep(3)
                success.empty()
        
st.write("#### 2. View WAAS Report")
st.write("Click **'View'** to view the data analysis or click **'Download'** to download the Excel file.")
st.write("Only displaying 5 most recent reports.")
st.markdown(
    """
    
    """
    
)

@st.dialog("Delete Report?")
def delete_report(filename):
    st.write("**{}** will be deleted permanently.".format(filename))

    if st.button("Delete"):
        db.delete_file(data["fullpath"])
        os.remove(data["fullpath"])
        st.rerun()
        
data_report_waas = []
data_filename = db.get_files()
if len(data_filename) == 0:
    st.write("No WAAS data found. Click **Generate WAAS Data** button above.")
else:
    for file in data_filename:
        index, filename, timestamp = file
        fullpath = filename
        if "\\" in filename:
            filename = filename.split('\\')[1]
        elif "/" in filename:
            filename = filename.split('/')[1]
        
        new_data = {
            "filename": filename,
            "timestamp": timestamp,
            "fullpath": fullpath
        }
        data_report_waas.append(new_data)
    if len(data_report_waas) > 5:
        data_report_waas = data_report_waas[-5:]
    for idx, data in enumerate(data_report_waas):
        left_col, right_col = st.columns(2)
        with open(data["fullpath"], "rb") as f:
                    file_data = f.read()
        with left_col:
            st.write("**{}**\n{}".format(data["filename"], data["timestamp"]))
        with right_col:
            view_col, download_col, del_col = st.columns(3)
            with view_col:
                st.link_button("View", url="/WAAS?filename={}".format(data["fullpath"]))
            with download_col:
                
                st.download_button("Download", data=file_data, file_name=data["filename"], mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with del_col:
                if st.button("Delete", key=data["fullpath"]):
                    delete_report(data["filename"])
                        
