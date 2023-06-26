import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap, MarkerCluster
import streamlit as st
from streamlit_folium import folium_static


@st.cache_data
def data_cleanup(csv):
    df = pd.read_csv(csv_f)
    df['obs_yr'] = (pd.to_datetime(df['observed_on'])).dt.year
    df = df.loc[df['obs_yr']>=2018]
    df = df.loc[~df['scientific_name'].isin(['Ursinae','Ursidae'])]
    df['obs_yr'] = df['obs_yr'].astype(str)
    df.loc[df['common_name'].str.contains('Black'), 'common_name'] = 'Black Bear'
    df=df[['obs_yr','common_name','latitude','longitude','image_url']]
    
    return df


def create_map(df):
    m= folium.Map(location=[54.1,-124.2], 
                  zoom_start=5)
    
    marker_cluster = MarkerCluster(name='Bear Observations').add_to(m)
    heat_data= []
    
    for idx, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        obs_yr = row['obs_yr']
        common_name = row['common_name']
        popup_html = f"<b>Observation Year</b>: {obs_yr}<br><b>Common Name</b>: {common_name}"
        popup = folium.Popup(popup_html, max_width=400)
        folium.Marker([lat, lon], popup=popup).add_to(marker_cluster)
        
        lat_long = [lat, lon]
        heat_data.append(lat_long)
        
    HeatMap(heat_data, 
            min_opacity= 0.4,
            blur= 20).add_to(folium.FeatureGroup(name='Heatmap of Bear Observations').add_to(m))
    
    #minimap = MiniMap(position="bottomleft")
    #m.add_child(minimap)
    
    folium.LayerControl().add_to(m)
    
    return m


if __name__==__name__:

    #---------------Page Settings-------------#
    st.set_page_config(page_title='Bear Observations in BC',
                       page_icon='🐻',
                       layout= 'wide')

    #---------------Some CSS styling-----------------#    
    st_style = """
            <style>
            .stApp {margin-top: -100px;}
            
            h1 {font-size: 50px;}
            h2 {font-size: 25px;}
            h3 {font-size: 18px;}

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
    st.markdown(st_style, unsafe_allow_html=True)
    
    #---------------Prepare inputs----------------#
    csv_f= 'bear_observations_bc.csv'
    df= data_cleanup(csv_f)
    
    df_counts = df.groupby(['obs_yr', 'common_name']).size().reset_index(name='count')
    df_counts.sort_values('obs_yr',inplace=True)
    
 
    #------------Setup Sidebar (Filters)------------#
    st.sidebar.header('Please Filter here:')
    
    min_year= int(df_counts['obs_yr'].min())
    max_year= int(df_counts['obs_yr'].max())
    
    start_year, end_year = st.sidebar.slider(
        "Select Observation Years", 
         min_value= min_year, 
         max_value= max_year,
         value=(min_year, max_year),
         step= 1)
    
    sbsp= st.sidebar.multiselect(
        "Select Bear Subspecies",
        options= df_counts['common_name'].unique(),
        default= df_counts['common_name'].unique())
    
    df_counts['obs_yr'] = df_counts['obs_yr'].astype(int)
    df_sel = df_counts.loc[(df_counts['common_name'].isin(sbsp)) &
                           ((df_counts['obs_yr']>= start_year) &
                            (df_counts['obs_yr']<= end_year))]
    
    #------------------Main Page--------------------#
    st.title('Bear Observations in BC')  
    
    col1, col2 = st.columns(2)
    
     #----Col1----#
    total_obs = df_sel['count'].sum()
    with col1:
        st.subheader('Total number of observations:')
        st.subheader(f'{total_obs}')
        
     #----Col2----#
    black_df = df_sel.loc[df_sel['common_name']=='Black Bear']
    black_obs = black_df['count'].sum()
    pct_black = int((black_obs/total_obs)*100)
    with col2:
        st.subheader('Percent of Black Bear observations:')  
        st.subheader(f'{pct_black} %')
             
    st.divider()
    
    col3, col4 = st.columns([0.45,0.55])      
    
    #----Col3----#

    df['obs_yr'] = df['obs_yr'].astype(int)
    df_sel_m = df.loc[(df['common_name'].isin(sbsp)) &
                     ((df['obs_yr']>= start_year) &
                     (df['obs_yr']<= end_year))]
    m = create_map(df_sel_m)
    with col3:
        st.header('Spatial distribution of Observations')
        folium_static(m, width=450,height=550)

     #----Col4----#
    
    plot= px.line(df_sel, x='obs_yr', y='count', color='common_name', markers=True,
                  color_discrete_sequence=px.colors.qualitative.Plotly)
    with col4:
        st.header('Observations by Year and Subspecies')
        st.plotly_chart(plot,use_container_width=True)