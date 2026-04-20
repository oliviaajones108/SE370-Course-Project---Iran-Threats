# streamlit run "c:\Users\caroline.tullier\OneDrive - West Point\26-2\SE370 - Computer Aided Sys Eng\Course Project\project\interactiveplot2_stfolium.py"

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title='Risk to Iranian Travelers - Event Codes', layout='wide')

CAMEO_ROOT_INTERPRETATIONS = {
    '01': 'Make public statement',
    '02': 'Appeal',
    '03': 'Express intent to cooperate',
    '04': 'Consult',
    '05': 'Engage in diplomatic cooperation',
    '06': 'Engage in material cooperation',
    '07': 'Provide aid',
    '08': 'Yield',
    '09': 'Investigate',
    '10': 'Demand',
    '11': 'Disapprove',
    '12': 'Reject',
    '13': 'Threaten',
    '14': 'Protest',
    '15': 'Exhibit military posture',
    '16': 'Reduce relations',
    '17': 'Coerce',
    '18': 'Assault',
    '19': 'Fight',
    '20': 'Use unconventional mass violence',
}

CAMEO_EVENT_INTERPRETATIONS = {
    '010': 'Make statement',
    '011': 'Decline comment',
    '012': 'Make pessimistic comment',
    '013': 'Make optimistic comment',
    '014': 'Consider policy option',
    '015': 'Acknowledge or claim responsibility',
    '016': 'Deny responsibility',
    '017': 'Engage in symbolic act',
    '020': 'Appeal',
    '030': 'Express intent to cooperate',
    '036': 'Express intent to meet or negotiate',
    '040': 'Consult',
    '042': 'Make a visit',
    '043': 'Host a visit',
    '045': 'Mediate',
    '046': 'Engage in negotiation',
    '050': 'Engage in diplomatic cooperation',
    '051': 'Praise or endorse',
    '052': 'Defend verbally',
    '057': 'Sign formal agreement',
    '060': 'Engage in material cooperation',
    '061': 'Cooperate economically',
    '070': 'Provide aid',
    '071': 'Provide economic aid',
    '073': 'Provide humanitarian aid',
    '080': 'Yield',
    '081': 'Ease administrative sanctions',
    '084': 'Return or release',
    '0841': 'Return or release person(s)',
    '0874': 'Retreat or surrender militarily',
    '090': 'Investigate',
    '100': 'Demand',
    '110': 'Disapprove',
    '111': 'Criticize or denounce',
    '112': 'Accuse',
    '114': 'Complain officially',
    '120': 'Reject',
    '128': 'Defy norms, law, or authority',
    '130': 'Threaten',
    '138': 'Threaten unconventional violence',
    '140': 'Protest',
    '141': 'Demonstrate or rally',
    '150': 'Exhibit military posture',
    '160': 'Reduce relations',
    '164': 'Halt negotiations',
    '170': 'Coerce',
    '172': 'Impose administrative sanctions',
    '173': 'Arrest, detain, or charge',
    '180': 'Assault',
    '190': 'Fight',
    '192': 'Occupy territory',
    '193': 'Fight with small arms and light weapons',
    '200': 'Use unconventional mass violence',
}

@st.cache_data
def read_data():
    df = pd.read_csv(
        'course.project.data.clean.csv',
        usecols=[
            'SQLDATE',
            'EventCode',
            'EventRootCode',
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
        ],
        dtype={
            'EventCode': 'string',
            'EventRootCode': 'string',
            'ActionGeo_CountryCode': 'string',
        }
    )
    df = df.rename(columns={
        'SQLDATE': 'date',
        'EventCode': 'event_code',
        'EventRootCode': 'event_root_code',
        'GoldsteinScale': 'goldstein_scale',
        'QuadClass': 'quad_class',
        'Actor1Name': 'actor1_name',
        'Actor1CountryCode': 'actor1_country_code',
        'Actor1Geo_FullName': 'actor1_geo',
        'Actor1Geo_CountryCode': 'actor1_geo_country_code',
        'Actor2Name': 'actor2_name',
        'Actor2CountryCode': 'actor2_country_code',
        'Actor2Geo_FullName': 'actor2_geo',
        'Actor2Geo_CountryCode': 'actor2_geo_country_code',
        'ActionGeo_FullName': 'location',
        'ActionGeo_CountryCode': 'country_code',
        'ActionGeo_Lat': 'lat',
        'ActionGeo_Long': 'lon',
    })

    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['goldstein_scale'] = pd.to_numeric(df['goldstein_scale'], errors='coerce')
    df['quad_class'] = pd.to_numeric(df['quad_class'], errors='coerce')
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
    df['conflict_related'] = (df['goldstein_scale'] < 0) | df['quad_class'].isin([3, 4])
    return df

def normalize_event_code(value):
    if pd.isna(value):
        return ''

    code = str(value).strip().split('.')[0]
    if not code:
        return ''
    if len(code) <= 3:
        return code.zfill(3)
    return code.zfill(4)

def normalize_root_code(event_code, event_root_code):
    if pd.notna(event_root_code):
        root = str(event_root_code).strip().split('.')[0]
        if root:
            return root.zfill(2)

    normalized = normalize_event_code(event_code)
    return normalized[:2]

def interpret_event_code(event_code, event_root_code):
    normalized = normalize_event_code(event_code)
    root = normalize_root_code(event_code, event_root_code)

    specific = CAMEO_EVENT_INTERPRETATIONS.get(normalized)
    root_meaning = CAMEO_ROOT_INTERPRETATIONS.get(root, 'Unknown CAMEO category')

    if specific:
        return f'{specific} ({root_meaning})'
    return f'{root_meaning}; specific CAMEO code {normalized or "unknown"}'

def filter_iran_focus(data, focus_choice):
    if focus_choice == 'Events located in Iran':
        return data[data['action_in_iran']]
    if focus_choice == 'Events involving Iran anywhere':
        return data[data['iran_related']]
    if focus_choice == 'Conflict events involving Iran':
        return data[data['iran_related'] & data['conflict_related']]
    return data

def build_streamlit_2():
    data = read_data()
    data['event_code_display'] = data['event_code'].apply(normalize_event_code)
    data['event_interpretation'] = data.apply(
        lambda row: interpret_event_code(row.get('event_code'), row.get('event_root_code')),
        axis=1
    )

    st.title('Risk to Iranian Travelers')
    st.write('This map displays Iran-focused event locations by CAMEO event interpretation.')

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

    zoom_level = st.sidebar.slider('Zoom level', min_value=4, max_value=10, value=5)
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
        min_value=1,
        max_value=max_points,
        value=min(max_points, 500),
        step=100 if max_points >= 100 else 1
    )
    show_table = st.sidebar.checkbox('Show data table', value=True)

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

    event_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles=tile_choice
    )

    for _, row in plot_data.iterrows():
        event_text = row.get('event_interpretation')
        event_code = row.get('event_code_display')
        popup_text = (
            f"<b>Event:</b> {event_text}<br>"
            f"<b>Event code:</b> {event_code}<br>"
            f"<b>Location:</b> {row.get('location', 'Unknown')}<br>"
            f"<b>Date:</b> {row.get('date', 'Unknown')}<br>"
            f"<b>Actor 1:</b> {row.get('actor1_name', 'Unknown')}<br>"
            f"<b>Actor 2:</b> {row.get('actor2_name', 'Unknown')}"
        )
        tooltip_text = f"{event_text} (code {event_code})"

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=3,
            popup=folium.Popup(popup_text, max_width=350),
            tooltip=tooltip_text,
            fill=True
        ).add_to(event_map)

    st.subheader('Map Summary')
    st.write(f'Displaying {len(plot_data)} events')
    st.write(f'Selected focus: {focus_choice}')
    st.write(f'Events matching selected focus: {len(data):,}')
    st.write(f'Map center: ({center_lat:.2f}, {center_lon:.2f})')
    st.write(f'Initial zoom level: {zoom_level}')

    st.subheader('Interactive Map')
    st.caption('Hover over a point for the event interpretation, or click it for the full popup.')
    st_folium(event_map, width=1200, height=650)

    if show_table:
        st.subheader('Data Preview')
        st.dataframe(plot_data.head(20))

build_streamlit_2()
