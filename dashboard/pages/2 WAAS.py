import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime
import export_pdf
import urllib.parse, os

st.set_page_config(page_title='Prisma Cloud Report Dashboard', page_icon=':bar_chart:', layout='wide')
if st.button("Clear Cache"):
    st.cache_data.clear()

if "filename" in st.query_params:
    filename = st.query_params["filename"]
    
    if os.path.exists(filename):
        # @st.cache_data
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
            namespace_options = df["Namespace"].unique().tolist()
                      
            all_option = "Select All"
            attack_type_choices = [all_option] + attack_type_options
            image_choices = [all_option] + image_options
            namespace_choices = [all_option] + namespace_options
            attack_type = st.sidebar.multiselect("Attack Type:", options=attack_type_choices, default=[])
            namespace = st.sidebar.multiselect(
                "Namespace:",
                options=namespace_choices,
                default=[]
            )

            attack_type_condition = attack_type_options if all_option in attack_type or not attack_type else attack_type
            # image_condition = image_options if all_option in image or not image else image
            namespace_condition = namespace_options if all_option in namespace or not namespace else namespace

            
            
            image_attack_counts = df["Image"].value_counts().head(5).sort_values(ascending=True)
            
            ## Filter by Image->URL->Path
            # if image_condition != image_options:
            filtered_by_image = df[df["Namespace"].isin(namespace_condition)]
            host_options = filtered_by_image["Host"].unique().tolist()
            host = st.sidebar.multiselect("Host:", options=[all_option] + host_options, default=[])
            host_condition = host_options if all_option in host or not host else host
            
            filtered_by_host = filtered_by_image[filtered_by_image["Host"].isin(host_condition)]
            path_options = filtered_by_host["Path"].unique().tolist()
            path = st.sidebar.multiselect("Path:", options=[all_option] + path_options, default=[])
            path_condition = path_options if all_option in path or not path else path
            
            # Check if filters are applied
            filters = {
                "Attack Type": attack_type if attack_type else "All",
                "Namespace": namespace if namespace else "All",
                "Host": host if host else "All",
                "Path": path if path else "All",
            }   
            
            # df_selection = df_selection.query("Host in @host_condition and Path in @path_condition")
            df_selection = df.query(
                "Namespace in @namespace_condition and Host in @host_condition and Path in @path_condition and AttackType in @attack_type_condition"
            )
            if df_selection.empty:
                st.warning("No data available for the selected filters. Please adjust your filters.")
                return None, None, None, None, None, None, None, None, None, None, None, None, None, None
            host_counts = df_selection["Host"].value_counts().nlargest(5).sort_values(ascending=True)
            
            
            #DF SELECTION
            attack_counts = df_selection["AttackType"].value_counts().nlargest(5).sort_values(ascending=True)
            filtered_attack = df_selection[df_selection["Effect"].isin(["alert","ban","prevent"])]
            filtered_attack_count = filtered_attack["AttackType"].value_counts().nlargest(5).sort_values(ascending=True)
            attacker_ip = df_selection["IPAddress"].value_counts().nlargest(5).sort_values(ascending=True)
            
            unique_attack_counts = df_selection.groupby('Host')['AttackType'].nunique()
            
            if not unique_attack_counts.empty:
                max_unique_attacks_host = unique_attack_counts.idxmax()
                max_unique_attacks_count = unique_attack_counts.max()
                top_5_host_unique_attacks = unique_attack_counts.nlargest(5).sort_values(ascending=True)
                max_unique_attacks_host = unique_attack_counts.idxmax()
                max_unique_attacks_count = unique_attack_counts.max()
            else:
                max_unique_attacks_host = None
                max_unique_attacks_count = None
                top_5_host_unique_attacks = pd.Series()
           
            
            if not pd.api.types.is_datetime64_any_dtype(df_selection['Time']):
                df_selection['Time'] = pd.to_datetime(df_selection['Time'], format="%d-%m-%Y %H:%M:%S")
            end_time = df_selection['Time'].max()
            start_time = end_time - timedelta(days=3)
            df_last_3_days = df_selection[(df_selection["Time"] >= start_time) & (df_selection["Time"] <= end_time)]
            
            if not df_last_3_days.empty:
                attack_time = df_last_3_days.groupby([df_selection['Time'].dt.floor('h'), 'AttackType']).size().reset_index(name='Count')
                attack_time.set_index(['Time', 'AttackType'], inplace=True)
                attack_time = attack_time.unstack().resample('15min').interpolate('linear').stack().reset_index()
                attack_time['Count'] = attack_time['Count'].round().astype(int)
            else:
                attack_time = pd.DataFrame(columns=['Time', 'AttackType', 'Count'])           
                
            
            return (filters, image_attack_counts, top_5_host_unique_attacks, max_unique_attacks_host, max_unique_attacks_count,
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
        
        filters, images, top_5_host_unique_attacks, max_unique_attacks_url,max_unique_attacks_count, unique_attack_counts, df_selection, host_counts, attack_counts, filtered_attack_count, attacker_ip, attack_time, attack_type_choices, image_choices = process_data(df)
        # def plot_chart_top_url_distinct_attack(url_distinct):
        
            

        def plot_chart_most_attacks(host_counts):
            if host_counts is not None:
                fig_url = px.bar(host_counts, x=host_counts.values, y=host_counts.index, 
                        labels={'x': 'Number of Attacks', 'y': 'URL'},
                        title='<b>Top 5 Hosts with the Most Attacks</b>',
                        orientation="h", template="plotly_white", text=host_counts.values)
                return fig_url
            else:
                return None
        def plot_chart_top_attack(attack_counts):
            if attack_counts is not None:
                fig_url = px.bar(attack_counts, x=attack_counts.values, y=attack_counts.index, 
                        labels={'x': 'Number of Events', 'y': 'Attack Type'},
                        title='<b>Top 5 Attack Types</b>',
                        orientation="h", template="plotly_white", text=attack_counts.values)
                return fig_url
            return attack_counts

        def attack_type_by_time(attack_time):
            if attack_time is not None:
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
                    title="Attack Type Frequency Over the Last 3 Days (Spline)",
                    xaxis_title="Time",
                    yaxis_title="Number of Attacks",
                    legend_title="Attack Type",
                    template="plotly",
                    xaxis=dict(type="date")
                )

                return fig
            return None
        # fig = px.area(attack_time, x="Time", y="Count", color="AttackType", title="Attack Type Distribution Over Time", labels={"Time": "Time", "Count": "Number of Attacks", "AttackType": "Type of Attack"})

        def display_top_url_unique_attacks(urls):
            if urls is not None:
                fig_url = px.bar(urls, x=urls.values, y=urls.index, 
                        labels={'x': 'Number of Attacks', 'y': 'Attack Type'},
                        title='<b>Top 5 Hosts with Most Unique Attacks</b>',
                        orientation="h", template="plotly_white", text=urls.values)
                return fig_url
            else:
                return None
        left_col, right_col = st.columns(2)

        def top_ban_attacks(filtered_attack_count):
            # print(filtered_attack_count)
            if filtered_attack_count is not None:
                fig_url = px.bar(filtered_attack_count, x=filtered_attack_count.values, y=filtered_attack_count.index, 
                        labels={'x': 'Number of Events', 'y': 'Attack Type'},
                        title='<b>Top 5 Ban/Prevent/Alert Attacks</b>',
                        orientation="h", template="plotly_white", text=filtered_attack_count.values)
                return fig_url
            return filtered_attack_count
        def top_attacker(attacker_ip):
            if attacker_ip is not None:
                fig_url = px.bar(attacker_ip, x=attacker_ip.values, y=attacker_ip.index, 
                        labels={'x': 'Number of Events', 'y': 'Attack Type'},
                        title='<b>Top 5 Attacker\'s IP</b>',
                        orientation="h", template="plotly_white", text=attacker_ip.values)
                return fig_url
            return attacker_ip
        def show_image_attack_count(image_attack_counts):
            if image_attack_counts is not None:
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
            return image_attack_counts
        
        most_attack = plot_chart_most_attacks(host_counts)
        top_attack = plot_chart_top_attack(attack_counts)
        attack_time = attack_type_by_time(attack_time)
        top_url_unique_attacks = display_top_url_unique_attacks(top_5_host_unique_attacks)
        top_ban = top_ban_attacks(filtered_attack_count)
        top_attacker_ip = top_attacker(attacker_ip)
        image_attack_count = show_image_attack_count(images)
        
        if top_url_unique_attacks is not None:
            st.plotly_chart(top_url_unique_attacks)
        left_col, right_col = st.columns(2)
        with left_col:
            if most_attack is not None:
                st.plotly_chart(most_attack)
        with right_col:
            if top_attack is not None:
                st.plotly_chart(top_attack)

        if attack_time is not None:
            st.plotly_chart(attack_time)

        left_col, right_col = st.columns(2)
        with left_col:
            if top_ban is not None:
                st.plotly_chart(top_ban)
        with right_col:
            if top_attacker_ip is not None:
                st.plotly_chart(top_attacker_ip)

        if image_attack_count is not None:
            st.plotly_chart(image_attack_count)
        
        if df_selection is not None:
            st.subheader("WAAS Events Details")
            st.dataframe(df_selection)
        
        if st.button("Export to PDF"):
            fig_list = [most_attack,top_attack,attack_time,top_url_unique_attacks,top_ban,top_attacker_ip,image_attack_count]
            pdf_data = export_pdf.generate_pdf(fig_list, filters)
            if pdf_data:
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name=f"WAAS Events Report - {datetime.now().strftime('%A, %d %B %Y')}",
                    mime="application/pdf",
                )
            else:
                st.error("Failed to generate PDF. Please check the logs.")
        
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