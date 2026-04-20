# streamlit run "c:\Users\caroline.tullier\OneDrive - West Point\26-2\SE370 - Computer Aided Sys Eng\Course Project\project\st_folium_visualize1.py"

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title= 'Risk to Iranian Travelers', layout= 'wide')

@st.cache_data
def read_data():
    df = pd.read_csv(
        'course.project.data.clean.csv',
        usecols=[
            'SQLDATE',
            'EventCode',
            'GoldsteinScale',
            'ActionGeo_FullName',
            'ActionGeo_Lat',
            'ActionGeo_Long',
            'SOURCEURL'
        ]
    )
    df = df.rename(columns={
        'ActionGeo_Lat': 'lat',
        'ActionGeo_Long': 'lon',
        'ActionGeo_FullName': 'location',
        'SQLDATE': 'date',
        'EventCode': 'event_code'
    })

    df['lat'] = pd.to_numeric(df['lat'], errors= 'coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors= 'coerce')

    df = df.dropna(subset=['lat', 'lon'])
    return df

def build_streamlit_1():
    data = read_data()
    st.title('Risk to Iranian Travelers')
    st.write('This map displays conflict-related event locations')

    st.sidebar.header('Map Settings')

    zoom_level = st.sidebar.slider('Zoom level', min_value= 4, max_value= 10, value= 6)

    tile_choice = st.sidebar.selectbox(
        'Basemap style',
        ['CartoDB Positron', 'CartoDB dark_matter']
    )

    max_points = min(len(data), 3000)
    point_limit = st.sidebar.slider(
        'Number of events to display',
        min_value= 1,
        max_value= max_points,
        value= min(max_points, 500),
        step= 100 if max_points >= 100 else 1
    )

    show_table = st.sidebar.checkbox('Show data table', value= True)

    plot_data = data.head(point_limit)

    if plot_data.empty:
        st.warning('No valid coordinates found.')
        return
    
    # Center map on the selected points so the map matches the current display.
    center_lat = plot_data['lat'].mean()
    center_lon = plot_data['lon'].mean()

    map = folium.Map(
        location= [center_lat, center_lon], 
        zoom_start= zoom_level, 
        tiles= tile_choice
        )

    for _, row in plot_data.iterrows():
        popup_text = (
            f"Location: {row.get('location', 'Unknown')}<br>"
            f"Date: {row.get('date', 'Unknown')}<br>"
            f"Event code: {row.get('event_code', 'Unknown')}<br>"
            f"Goldstein scale: {row.get('GoldsteinScale', 'Unknown')}<br>"
            f"Latitude: {row['lat']}<br>"
            f"Longitude: {row['lon']}"
        )

        folium.CircleMarker(location=[row['lat'], row['lon']],
                            radius=3,
                            popup= popup_text,
                            fill=True
                            ).add_to(map)
        
    # Display summary
    st.subheader("Map Summary")
    st.write(f"Displaying {len(plot_data)} events")
    st.write(f"Map center: ({center_lat:.2f}, {center_lon:.2f})")
    st.write(f"Initial zoom level: {zoom_level}")

    # Display map
    st.subheader("Interactive Map")
    st_folium(map, width=1200, height=650)

    # Optional data preview
    if show_table:
        st.subheader("Data Preview")
        st.dataframe(plot_data.head(20))

build_streamlit_1()
