# streamlit run "c:\Users\caroline.tullier\OneDrive - West Point\26-2\SE370 - Computer Aided Sys Eng\Course Project\project\interactiveplot1_stfolium.py"

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title= 'Risk to Iranian Travelers', layout= 'wide')

def interpret_goldstein(value):
    if pd.isna(value):
        return 'No Goldstein score available'
    if value <= -7:
        return 'Violent conflict or highly conflictual action'
    if value <= -4:
        return 'Non-violent conflict, pressure, threat, or coercion'
    if value < 0:
        return 'Mild conflict, disagreement, rejection, or protest'
    if value == 0:
        return 'Neutral action or statement'
    if value <= 2:
        return 'Mild cooperation or positive diplomatic contact'
    if value <= 6:
        return 'Material cooperation, aid, or practical support'
    return 'Strong cooperation or major cooperative agreement'

@st.cache_data
def read_data():
    df = pd.read_csv(
        'course.project.data.clean.csv',
        usecols=[
            'SQLDATE',
            'EventCode',
            'GoldsteinScale',
            'QuadClass',
            'Actor1Name',
            'Actor1CountryCode',
            'Actor1Geo_FullName',
            'Actor1Geo_CountryCode',
            'Actor2Name',
            'Actor2CountryCode',
            'Actor2Geo_FullName',
            'Actor2Geo_CountryCode',
            'ActionGeo_FullName',
            'ActionGeo_CountryCode',
            'ActionGeo_Lat',
            'ActionGeo_Long',
            'SOURCEURL'
        ]
    )
    df = df.rename(columns={
        'ActionGeo_Lat': 'lat',
        'ActionGeo_Long': 'lon',
        'ActionGeo_FullName': 'location',
        'ActionGeo_CountryCode': 'country_code',
        'SQLDATE': 'date',
        'EventCode': 'event_code',
        'QuadClass': 'quad_class',
        'Actor1Name': 'actor1_name',
        'Actor1CountryCode': 'actor1_country_code',
        'Actor1Geo_FullName': 'actor1_geo',
        'Actor1Geo_CountryCode': 'actor1_geo_country_code',
        'Actor2Name': 'actor2_name',
        'Actor2CountryCode': 'actor2_country_code',
        'Actor2Geo_FullName': 'actor2_geo',
        'Actor2Geo_CountryCode': 'actor2_geo_country_code'
    })

    df['lat'] = pd.to_numeric(df['lat'], errors= 'coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors= 'coerce')
    df['GoldsteinScale'] = pd.to_numeric(df['GoldsteinScale'], errors= 'coerce')
    df['quad_class'] = pd.to_numeric(df['quad_class'], errors= 'coerce')

    df = df.dropna(subset=['lat', 'lon'])
    df['action_in_iran'] = (
        df['country_code'].astype('string').eq('IR')
        | df['location'].astype('string').str.contains('Iran', case=False, na=False)
    )
    df['iran_actor_involved'] = (
        df['actor1_country_code'].astype('string').eq('IRN')
        | df['actor2_country_code'].astype('string').eq('IRN')
        | df['actor1_geo_country_code'].astype('string').eq('IR')
        | df['actor2_geo_country_code'].astype('string').eq('IR')
        | df['actor1_name'].astype('string').str.contains('Iran', case=False, na=False)
        | df['actor2_name'].astype('string').str.contains('Iran', case=False, na=False)
        | df['actor1_geo'].astype('string').str.contains('Iran', case=False, na=False)
        | df['actor2_geo'].astype('string').str.contains('Iran', case=False, na=False)
    )
    df['iran_related'] = df['action_in_iran'] | df['iran_actor_involved']
    df['conflict_related'] = (df['GoldsteinScale'] < 0) | df['quad_class'].isin([3, 4])
    df['goldstein_interpretation'] = df['GoldsteinScale'].apply(interpret_goldstein)
    return df

def filter_iran_focus(data, focus_choice):
    if focus_choice == 'Events located in Iran':
        return data[data['action_in_iran']]
    if focus_choice == 'Events involving Iran anywhere':
        return data[data['iran_related']]
    if focus_choice == 'Conflict events involving Iran':
        return data[data['iran_related'] & data['conflict_related']]
    return data

def build_streamlit_1():
    data = read_data()
    st.title('Risk to Iranian Travelers')
    st.write('This map displays Iran-focused conflict-related event locations.')

    st.sidebar.header('Map Settings')

    focus_choice = st.sidebar.selectbox(
        'Iran focus',
        [
            'Conflict events involving Iran',
            'Events involving Iran anywhere',
            'Events located in Iran',
            'All events'
        ]
    )
    data = filter_iran_focus(data, focus_choice)

    all_data = read_data()
    st.sidebar.write(f"Located in Iran: {all_data['action_in_iran'].sum():,}")
    st.sidebar.write(f"Involving Iran: {all_data['iran_related'].sum():,}")
    st.sidebar.write(f"Conflict involving Iran: {(all_data['iran_related'] & all_data['conflict_related']).sum():,}")

    zoom_level = st.sidebar.slider('Zoom level', min_value= 4, max_value= 10, value= 5)

    tile_choice = st.sidebar.selectbox(
        'Basemap style',
        ['CartoDB Positron', 'CartoDB dark_matter']
    )

    if data.empty:
        st.warning('No valid events found for the selected Iran focus.')
        return

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
    
    if focus_choice != 'All events':
        center_lat = 32.4279
        center_lon = 53.6880
    else:
        center_lat = plot_data['lat'].mean()
        center_lon = plot_data['lon'].mean()

    map = folium.Map(
        location= [center_lat, center_lon], 
        zoom_start= zoom_level, 
        tiles= tile_choice
        )

    for _, row in plot_data.iterrows():
        goldstein = row.get('GoldsteinScale')
        interpretation = row.get('goldstein_interpretation', interpret_goldstein(goldstein))
        popup_text = (
            f"<b>Goldstein scale:</b> {goldstein}<br>"
            f"<b>Interpretation:</b> {interpretation}<br>"
            f"<b>Location:</b> {row.get('location', 'Unknown')}<br>"
            f"<b>Actor 1:</b> {row.get('actor1_name', 'Unknown')}<br>"
            f"<b>Actor 2:</b> {row.get('actor2_name', 'Unknown')}"
        )
        tooltip_text = f"Goldstein {goldstein}: {interpretation}"

        folium.CircleMarker(location=[row['lat'], row['lon']],
                            radius=3,
                            popup= folium.Popup(popup_text, max_width=300),
                            tooltip= tooltip_text,
                            fill=True
                            ).add_to(map)
        
    # Display summary
    st.subheader("Map Summary")
    st.write(f"Displaying {len(plot_data)} events")
    st.write(f"Selected focus: {focus_choice}")
    st.write(f"Events matching selected focus: {len(data):,}")
    st.write(f"Map center: ({center_lat:.2f}, {center_lon:.2f})")
    st.write(f"Initial zoom level: {zoom_level}")

    # Display map
    st.subheader("Interactive Map")
    st.caption("Hover over a point for the Goldstein interpretation, or click it for the full popup.")
    st_folium(map, width=1200, height=650)

    # Optional data preview
    if show_table:
        st.subheader("Data Preview")
        st.dataframe(plot_data.head(20))

build_streamlit_1()
