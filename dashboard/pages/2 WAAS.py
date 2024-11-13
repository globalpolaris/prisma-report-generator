import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime
import urllib.parse, os

st.set_page_config(page_title='Prisma Cloud Report Dashboard', page_icon=':bar_chart:', layout='wide')

if "filename" in st.query_params:
    filename = st.query_params["filename"]
    
    if os.path.exists(filename):
        @st.cache_data
        def load_data():

            df = pd.read_excel(
                io=filename,
                engine='openpyxl',
            )
            df.index += 1
            return df

        # --- SIDEBAR ---

        st.sidebar.header("Filter")
        # url = st.sidebar.multiselect(
        #     "Select URL:",
        #     options=df["URL"].unique(),
        #     # default=df["URL"].unique(),
        # )
        # Get unique values and add "Select All" option

        def process_data(df):
            attack_type_options = df["AttackType"].unique().tolist()
            image_options = df["Image"].unique().tolist() 
                      
            all_option = "Select All"
            attack_type_choices = [all_option] + attack_type_options
            image_choices = [all_option] + image_options

            # attack_type = st.sidebar.multiselect("Attack Type:", options=attack_type_choices, default=[])
            image = st.sidebar.multiselect(
                "Image:",
                options=image_choices,
                default=[]
            )

            # attack_type_condition = attack_type_options if all_option in attack_type or not attack_type else attack_type
            image_condition = image_options if all_option in image or not image else image

            df_selection = df.query(
                "Image in @image_condition"
            )
            image_attack_counts = df["Image"].value_counts().head(5).sort_values(ascending=True)
            
            ## Filter by Image->URL->Path
            # if image_condition != image_options:
            filtered_by_image = df[df["Image"].isin(image_condition)]
            host_options = filtered_by_image["Host"].unique().tolist()
            host = st.sidebar.multiselect("Host:", options=[all_option] + host_options, default=[])
            host_condition = host_options if all_option in host or not host else host
            
            filtered_by_host = filtered_by_image[filtered_by_image["Host"].isin(host_condition)]
            path_options = filtered_by_host["Path"].unique().tolist()
            path = st.sidebar.multiselect("Path:", options=[all_option] + path_options, default=[])
            path_condition = path_options if all_option in path or not path else path
            
            df_selection = df_selection.query("Host in @host_condition and Path in @path_condition")
            
            host_counts = df_selection["Host"].value_counts().nlargest(5).sort_values(ascending=True)
            
            
            #DF SELECTION
            attack_counts = df_selection["AttackType"].value_counts().nlargest(5).sort_values(ascending=True)
            filtered_attack = df_selection[df_selection["Effect"].isin(["alert","ban","prevent"])]
            filtered_attack_count = filtered_attack["AttackType"].value_counts().nlargest(5).sort_values(ascending=True)
            attacker_ip = df_selection["IPAddress"].value_counts().nlargest(5).sort_values(ascending=True)
            
            unique_attack_counts = df_selection.groupby('Host')['AttackType'].nunique()
            max_unique_attacks_host = unique_attack_counts.idxmax()
            max_unique_attacks_count = unique_attack_counts.max()
            top_5_host_unique_attacks = unique_attack_counts.nlargest(5).sort_values(ascending=True)
            
            df_selection['Time'] = pd.to_datetime(df_selection['Time'], format="%d-%m-%Y %H:%M:%S")
            end_time = df_selection['Time'].max()
            start_time = end_time - timedelta(days=3)
            df_last_3_days = df_selection[(df_selection["Time"] >= start_time) & (df_selection["Time"] <= end_time)]
            # print(df_last_3_days)
            attack_time = df_last_3_days.groupby([df_selection['Time'].dt.floor('h'), 'AttackType']).size().reset_index(name='Count')
            attack_time.set_index(['Time', 'AttackType'], inplace=True)
            attack_time = attack_time.unstack().resample('15min').interpolate('linear').stack().reset_index()
            attack_time['Count'] = attack_time['Count'].round().astype(int)
            
            return (image_attack_counts, top_5_host_unique_attacks, max_unique_attacks_host, max_unique_attacks_count,
            unique_attack_counts, df_selection, host_counts, attack_counts, filtered_attack_count, 
            attacker_ip, attack_time, attack_type_choices, image_choices)

        # Sidebar multiselects with "Select All" options



        st.title("WAAS Events")
        st.markdown(
            """
            ##### Data of WAAS Events recorded in Prisma Cloud CWP
            Use the **filter** sidebar to filter the data of the **WAAS Events Details** table.
            """
            
        )

        df = load_data()
        images, top_5_host_unique_attacks, max_unique_attacks_url,max_unique_attacks_count, unique_attack_counts, df_selection, host_counts, attack_counts, filtered_attack_count, attacker_ip, attack_time, attack_type_choices, image_choices = process_data(df)
        # def plot_chart_top_url_distinct_attack(url_distinct):
            
            

        def plot_chart_most_attacks(host_counts):
            fig_url = px.bar(host_counts, x=host_counts.values, y=host_counts.index, 
                    labels={'x': 'Number of Attacks', 'y': 'URL'},
                    title='<b>Top 5 Hosts with the Most Attacks</b>',
                    orientation="h", template="plotly_white", text=host_counts.values)
            return fig_url

        def plot_chart_top_attack(attack_counts):
            fig_url = px.bar(attack_counts, x=attack_counts.values, y=attack_counts.index, 
                    labels={'x': 'Number of Events', 'y': 'Attack Type'},
                    title='<b>Top 5 Attack Types</b>',
                    orientation="h", template="plotly_white", text=attack_counts.values)
            return fig_url

        def attack_type_by_time(attack_time):
            fig = go.Figure()

            for attack_type in attack_time['AttackType'].unique():
                df_attack = attack_time[attack_time['AttackType'] == attack_type]
                fig.add_trace(
                    go.Scatter(
                        x=df_attack['Time'],
                        y=df_attack['Count'],
                        mode='lines',
                        name=attack_type,
                        stackgroup='one',  # enables stacking
                        line_shape='spline',  # makes it smooth
                        fill='tonexty'
                    )
                )

            # Update layout
            fig.update_layout(
                title="Smoothed Attack Type Frequency Over the Last 3 Days (Spline)",
                xaxis_title="Time",
                yaxis_title="Number of Attacks",
                legend_title="Attack Type"
            )

            return fig

        # fig = px.area(attack_time, x="Time", y="Count", color="AttackType", title="Attack Type Distribution Over Time", labels={"Time": "Time", "Count": "Number of Attacks", "AttackType": "Type of Attack"})

        def display_top_url_unique_attacks(urls):
            fig_url = px.bar(urls, x=urls.values, y=urls.index, 
                    labels={'x': 'Number of Attacks', 'y': 'Attack Type'},
                    title='<b>Top 5 Hosts with Most Unique Attacks</b>',
                    orientation="h", template="plotly_white", text=urls.values)
            return fig_url
        left_col, right_col = st.columns(2)

        def top_ban_attacks(filtered_attack_count):
            # print(filtered_attack_count)
            fig_url = px.bar(filtered_attack_count, x=filtered_attack_count.values, y=filtered_attack_count.index, 
                    labels={'x': 'Number of Events', 'y': 'Attack Type'},
                    title='<b>Top 5 Ban/Prevent/Alert Attacks</b>',
                    orientation="h", template="plotly_white", text=filtered_attack_count.values)
            return fig_url
        def top_attacker(attacker_ip):
            fig_url = px.bar(attacker_ip, x=attacker_ip.values, y=attacker_ip.index, 
                    labels={'x': 'Number of Events', 'y': 'Attack Type'},
                    title='<b>Top 5 Attacker\'s IP</b>',
                    orientation="h", template="plotly_white", text=attacker_ip.values)
            return fig_url
        def show_image_attack_count(image_attack_counts):
            fig = px.bar(
                image_attack_counts,
                x=image_attack_counts.values,
                y=image_attack_counts.index,
                labels={'x': 'Number of Attacks', 'y': 'Image'},
                title='<b>Top Images by Attack Count</b>',
                orientation="h",  # Horizontal orientation
                template="plotly_white",
                text=image_attack_counts.values
            )
            return fig
        st.plotly_chart(display_top_url_unique_attacks(top_5_host_unique_attacks))
        left_col, right_col = st.columns(2)
        with left_col:
            st.plotly_chart(plot_chart_most_attacks(host_counts))
        with right_col:
            st.plotly_chart(plot_chart_top_attack(attack_counts))

        st.plotly_chart(attack_type_by_time(attack_time))

        left_col, right_col = st.columns(2)
        with left_col:
            st.plotly_chart(top_ban_attacks(filtered_attack_count))
        with right_col:
            st.plotly_chart(top_attacker(attacker_ip))

        
        st.plotly_chart(show_image_attack_count(images))
        
        st.subheader("WAAS Events Details")
        st.dataframe(df_selection)

        # print("Unique attacks url: ")
        # print(top_5_url_unique_attacks)
        # print("Max attacks: ")
        # print(max_unique_attacks_count)
        # print("Unique attacks counts: ")
        # print(unique_attack_counts)
        # st.title("Container Models")
        # st.dataframe(df_selection)
    else:
        st.warning("File does not exist.")
else:
    st.warning("No filename provided. Please go back to the Home Page to generate data.")