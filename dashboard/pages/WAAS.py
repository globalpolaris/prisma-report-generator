import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime

st.set_page_config(page_title='Prisma Cloud Report Dashboard', page_icon=':bar_chart:', layout='wide')

@st.cache_data
def load_data():

    df = pd.read_excel(
        io='..\WAAS Reports\WAAS_Report_2024_11_07_22-18-24.xlsx',
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
    
    url_counts = df["URL"].value_counts().nlargest(5).sort_values(ascending=True)
    attack_counts = df["AttackType"].value_counts().nlargest(5).sort_values(ascending=True)
    filtered_attack = df[df["Effect"].isin(["alert"])]
    filtered_attack_count = filtered_attack["AttackType"].value_counts().nlargest(5).sort_values(ascending=True)
    attacker_ip = df["IPAddress"].value_counts().nlargest(5).sort_values(ascending=True)
    df['Time'] = pd.to_datetime(df['Time'], format="%d-%m-%Y %H:%M:%S")

    end_time = df['Time'].max()
    start_time = end_time - timedelta(days=3)
    df_last_3_days = df[(df["Time"] >= start_time) & (df["Time"] <= end_time)]
    print(df_last_3_days)
    attack_time = df_last_3_days.groupby([df['Time'].dt.floor('h'), 'AttackType']).size().reset_index(name='Count')
    attack_time.set_index(['Time', 'AttackType'], inplace=True)
    attack_time = attack_time.unstack().resample('15T').interpolate('linear').stack().reset_index()
    attack_time['Count'] = attack_time['Count'].round().astype(int)
    
    all_option = "Select All"
    attack_type_choices = [all_option] + attack_type_options
    image_choices = [all_option] + image_options

    attack_type = st.sidebar.multiselect("Attack Type:", options=attack_type_choices, default=[])
    image = st.sidebar.multiselect(
        "Image:",
        options=image_choices,
        default=[]
    )

    attack_type_condition = attack_type_options if all_option in attack_type or not attack_type else attack_type
    image_condition = image_options if all_option in image or not image else image

    df_selection = df.query(
        "Image in @image_condition and AttackType in @attack_type_condition"
    )

    
    
    return df_selection, url_counts, attack_counts, filtered_attack_count, attacker_ip, attack_time, attack_type_choices, image_choices

# Sidebar multiselects with "Select All" options



st.title("WAAS Events")
st.markdown(
    """
    ##### Data of WAAS Events recorded in Prisma Cloud CWP
    Use the **filter** sidebar to filter the data of the **WAAS Events Details** table.
    """
    
)

df = load_data()
df_selection, url_counts, attack_counts, filtered_attack_count, attacker_ip, attack_time, attack_type_choices, image_choices = process_data(df)



def plot_chart_most_attacks(url_counts):
    fig_url = px.bar(url_counts, x=url_counts.values, y=url_counts.index, 
            labels={'x': 'Number of Attacks', 'y': 'URL'},
            title='<b>Top 5 URLs with the Most Attacks</b>',
            orientation="h", template="plotly_white", text=url_counts.values)
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


left_col, right_col = st.columns(2)

def top_ban_attacks(filtered_attack_count):
    print(filtered_attack_count)
    fig_url = px.bar(filtered_attack_count, x=filtered_attack_count.values, y=filtered_attack_count.index, 
            labels={'x': 'Number of Events', 'y': 'Attack Type'},
            title='<b>Top 5 Ban/Prevent Attacks</b>',
            orientation="h", template="plotly_white", text=filtered_attack_count.values)
    return fig_url
def top_attacker(attacker_ip):
    fig_url = px.bar(attacker_ip, x=attacker_ip.values, y=attacker_ip.index, 
            labels={'x': 'Number of Events', 'y': 'Attack Type'},
            title='<b>Top 5 Attacker\'s IP</b>',
            orientation="h", template="plotly_white", text=attacker_ip.values)
    return fig_url

left_col, right_col = st.columns(2)
with left_col:
    st.plotly_chart(plot_chart_most_attacks(url_counts))
with right_col:
    st.plotly_chart(plot_chart_top_attack(attack_counts))

st.plotly_chart(attack_type_by_time(attack_time))

left_col, right_col = st.columns(2)
with left_col:
    st.plotly_chart(top_ban_attacks(filtered_attack_count))
with right_col:
    st.plotly_chart(top_attacker(attacker_ip))

st.subheader("WAAS Events Details")
st.dataframe(df_selection)


# st.title("Container Models")
# st.dataframe(df_selection)
