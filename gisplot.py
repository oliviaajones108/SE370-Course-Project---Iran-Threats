# streamlit run .\gisplot.py
import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from plotnine import (
    aes,
    coord_fixed,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient2,
    scale_size_continuous,
    theme,
    theme_minimal
)

st.set_page_config(page_title='Iran Event Severity GIS Map', layout='wide')
st.set_page_config(page_title='Iran Event Severity Plotnine Map', layout='wide')

IRAN_CENTER = [32.4279, 53.6880]
IRAN_LON_RANGE = (43, 64)
IRAN_LAT_RANGE = (24, 41)
MIDDLE_EAST_LON_RANGE = (25, 75)
MIDDLE_EAST_LAT_RANGE = (10, 45)

CAMEO_ROOT_INTERPRETATIONS = {
    '01': 'Make public statement',
    '02': 'Appeal',
    '03': 'Express intent to cooperate',
    '04': 'Consult',
    '05': 'Engage in diplomatic cooperation',
    '06': 'Engage in material cooperation',
    '05': 'Diplomatic cooperation',
    '06': 'Material cooperation',
    '07': 'Provide aid',
    '08': 'Yield',
    '09': 'Investigate',
    '12': 'Reject',
    '13': 'Threaten',
    '14': 'Protest',
    '15': 'Exhibit military posture',
    '15': 'Military posture',
    '16': 'Reduce relations',
    '17': 'Coerce',
    '18': 'Assault',
    '19': 'Fight',
    '20': 'Use unconventional mass violence',
    '20': 'Mass violence',
}

@st.cache_data
            'EventRootCode',
            'GoldsteinScale',
            'QuadClass',
            'NumMentions',
            'Actor1Name',
            'Actor1CountryCode',
            'Actor1Geo_FullName',
            'ActionGeo_CountryCode': 'string',
        }
    )

    df = df.rename(columns={
        'SQLDATE': 'date',
        'EventCode': 'event_code',
        'EventRootCode': 'event_root_code',
        'GoldsteinScale': 'goldstein_scale',
        'QuadClass': 'quad_class',
        'NumMentions': 'num_mentions',
        'Actor1Name': 'actor1_name',
        'Actor1CountryCode': 'actor1_country_code',
        'Actor1Geo_FullName': 'actor1_geo',
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['goldstein_scale'] = pd.to_numeric(df['goldstein_scale'], errors='coerce')
    df['quad_class'] = pd.to_numeric(df['quad_class'], errors='coerce')
    df['num_mentions'] = pd.to_numeric(df['num_mentions'], errors='coerce').fillna(1)
    df = df.dropna(subset=['lat', 'lon', 'goldstein_scale'])

    df = add_iran_flags(df)
    df = add_plot_fields(df)
    return df

def add_iran_flags(df):
    df = df.copy()

    df['action_in_iran'] = (
        df['country_code'].astype('string').eq('IR')
        | df['location'].astype('string').str.contains('Iran', case=False, na=False)
    )

    df['iran_actor_involved'] = (
        df['actor1_country_code'].astype('string').eq('IRN')
        | df['actor2_country_code'].astype('string').eq('IRN')
        | df['actor1_geo'].astype('string').str.contains('Iran', case=False, na=False)
        | df['actor2_geo'].astype('string').str.contains('Iran', case=False, na=False)
    )

    df['iran_related'] = df['action_in_iran'] | df['iran_actor_involved']
    df['conflict_related'] = (df['goldstein_scale'] < 0) | df['quad_class'].isin([3, 4])
    return df

    # Goldstein ranges from -10 to +10. More negative is more severe, so invert it.
    df['severity'] = -df['goldstein_scale']
def add_plot_fields(df):
    df = df.copy()
    df['event_type'] = df['event_root_code'].apply(interpret_event_root)
    df['severity'] = -df['goldstein_scale']
    df['mentions_for_size'] = df['num_mentions'].clip(lower=1, upper=50)
    return df

def normalize_root_code(value):
    root = normalize_root_code(value)
    return CAMEO_ROOT_INTERPRETATIONS.get(root, 'Unknown event type')

def interpret_severity(goldstein_scale):
    if goldstein_scale <= -7:
        return 'Most severe: violent conflict or highly conflictual action'
    if goldstein_scale <= -4:
        return 'Severe: threat, coercion, sanctions, or strong pressure'
    if goldstein_scale < 0:
        return 'Moderate: disagreement, rejection, protest, or mild conflict'
    if goldstein_scale == 0:
        return 'Neutral'
    return 'Least severe: cooperative or positive action'

def filter_iran_focus(data, focus_choice):
def filter_iran_focus(df, focus_choice):
    if focus_choice == 'Events located in Iran':
        return data[data['action_in_iran']]
        return df[df['action_in_iran']]
    if focus_choice == 'Events involving Iran anywhere':
        return data[data['iran_related']]
        return df[df['iran_related']]
    if focus_choice == 'Conflict events involving Iran':
        return data[data['iran_related'] & data['conflict_related']]
    return data
        return df[df['iran_related'] & df['conflict_related']]
    return df

def filter_map_extent(df, extent_choice):
    if extent_choice == 'Iran':
        lon_min, lon_max = IRAN_LON_RANGE
        lat_min, lat_max = IRAN_LAT_RANGE
    elif extent_choice == 'Middle East':
        lon_min, lon_max = MIDDLE_EAST_LON_RANGE
        lat_min, lat_max = MIDDLE_EAST_LAT_RANGE
    else:
        return df

    return df[
        df['lon'].between(lon_min, lon_max)
        & df['lat'].between(lat_min, lat_max)
    ]

def get_plot_limits(extent_choice, df):
    if extent_choice == 'Iran':
        return IRAN_LON_RANGE, IRAN_LAT_RANGE
    if extent_choice == 'Middle East':
        return MIDDLE_EAST_LON_RANGE, MIDDLE_EAST_LAT_RANGE

    padding = 2
    lon_range = (df['lon'].min() - padding, df['lon'].max() + padding)
    lat_range = (df['lat'].min() - padding, df['lat'].max() + padding)
    return lon_range, lat_range

def create_plotnine_map(plot_data, extent_choice):
    lon_range, lat_range = get_plot_limits(extent_choice, plot_data)

    return (
        ggplot(
            plot_data,
            aes(
                x='lon',
                y='lat',
                color='goldstein_scale',
                size='mentions_for_size',
            )
        )
        + geom_point(alpha=0.65)
        + scale_color_gradient2(
            low='red',
            mid='yellow',
            high='green',
            midpoint=0,
            limits=(-10, 10),
            name='Goldstein scale'
        )
        + scale_size_continuous(
            range=(1.5, 8),
            name='Mentions'
        )
        + coord_fixed(
            ratio=1.0,
            xlim=lon_range,
            ylim=lat_range
        )
        + labs(
            title='Iran-Related Events by Severity',
            subtitle='Red is more conflictual; green is more cooperative',
            x='Longitude',
            y='Latitude'
        )
        + theme_minimal()
        + theme(
            figure_size=(12, 7),
            plot_title=element_text(size=16, weight='bold'),
            plot_subtitle=element_text(size=11),
            legend_title=element_text(size=9),
            legend_text=element_text(size=8),
        )
    )

def build_gis_map():
def build_streamlit_plot():
    data = read_data()

    st.title('Iran Event Severity GIS Map')
    st.write('Events are shown as circles. Red means most severe; green means least severe.')
    st.title('Iran Event Severity Plotnine Map')
    st.write('Circles are events. Red is most severe or conflictual; green is least severe or cooperative.')

    st.sidebar.header('Map Settings')
    st.sidebar.header('Plot Settings')
    focus_choice = st.sidebar.selectbox(
        'Iran focus',
        [
            'All events'
        ]
    )
    data = filter_iran_focus(data, focus_choice)

    all_data = read_data()
    st.sidebar.write(f"Located in Iran: {all_data['action_in_iran'].sum():,}")
    st.sidebar.write(f"Involving Iran: {all_data['iran_related'].sum():,}")
    st.sidebar.write(f"Conflict involving Iran: {(all_data['iran_related'] & all_data['conflict_related']).sum():,}")

    zoom_level = st.sidebar.slider('Zoom level', min_value=4, max_value=10, value=5)
    extent_choice = st.sidebar.selectbox(
        'Map extent',
        ['Iran', 'Middle East', 'All selected events']
    )
    point_limit = st.sidebar.slider(
        'Number of events to display',
        min_value=1,
        max_value=max(1, min(len(data), 3000)),
        value=min(max(1, len(data)), 750),
        step=100 if len(data) >= 100 else 1
        'Number of events to plot',
        min_value=100,
        max_value=3000,
        value=1000,
        step=100
    )
    show_table = st.sidebar.checkbox('Show data table', value=True)

    if data.empty:
        st.warning('No valid events found for the selected Iran focus.')
        return
    filtered_data = filter_iran_focus(data, focus_choice)
    filtered_data = filter_map_extent(filtered_data, extent_choice)

    plot_data = data.sort_values('severity', ascending=False).head(point_limit)
    st.sidebar.write(f"Located in Iran: {data['action_in_iran'].sum():,}")
    st.sidebar.write(f"Involving Iran: {data['iran_related'].sum():,}")
    st.sidebar.write(f"Conflict involving Iran: {(data['iran_related'] & data['conflict_related']).sum():,}")

    if focus_choice == 'All events':
        center = [plot_data['lat'].mean(), plot_data['lon'].mean()]
    else:
        center = IRAN_CENTER
    if filtered_data.empty:
        st.warning('No events match the selected filters.')
        return

    severity_map = folium.Map(
        location=center,
        zoom_start=zoom_level,
        tiles='CartoDB Positron'
    )
    plot_data = filtered_data.sort_values('severity', ascending=False).head(point_limit)
    plot = create_plotnine_map(plot_data, extent_choice)

    color_scale = cm.LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=-10,
        vmax=10,
        caption='Severity: green = least severe, red = most severe'
    )
    st.subheader('Plotnine GIS-Style Map')
    st.pyplot(plot.draw())

    for _, row in plot_data.iterrows():
        color = color_scale(row['severity'])
        radius = max(4, min(12, 4 + row['severity']))
        severity_text = interpret_severity(row['goldstein_scale'])

        popup_text = (
            f"<b>Event type:</b> {row.get('event_type', 'Unknown')}<br>"
            f"<b>Event code:</b> {row.get('event_code', 'Unknown')}<br>"
            f"<b>Goldstein scale:</b> {row.get('goldstein_scale', 'Unknown')}<br>"
            f"<b>Severity:</b> {severity_text}<br>"
            f"<b>Location:</b> {row.get('location', 'Unknown')}<br>"
            f"<b>Date:</b> {row.get('date', 'Unknown')}<br>"
            f"<b>Actor 1:</b> {row.get('actor1_name', 'Unknown')}<br>"
            f"<b>Actor 2:</b> {row.get('actor2_name', 'Unknown')}"
        )
        tooltip_text = f"{row.get('event_type', 'Unknown')} - {severity_text}"

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_text, max_width=375),
            tooltip=tooltip_text,
        ).add_to(severity_map)

    color_scale.add_to(severity_map)

    st.subheader('Map Summary')
    st.subheader('Filter Summary')
    st.write(f'Selected focus: {focus_choice}')
    st.write(f'Events matching selected focus: {len(data):,}')
    st.write(f'Displaying {len(plot_data)} most severe events')
    st.write(f'Map extent: {extent_choice}')
    st.write(f'Events matching filters: {len(filtered_data):,}')
    st.write(f'Events plotted: {len(plot_data):,}')

    st.subheader('Interactive GIS Map')
    st.caption('Hover over a circle for event type and severity. Click a circle for details.')
    st_folium(severity_map, width=1200, height=650)

    if show_table:
        st.subheader('Data Preview')
        st.dataframe(
            plot_data[
                [
                    'date',
                    'event_code',
                    'event_type',
                    'goldstein_scale',
                    'location',
                    'actor1_name',
                    'actor2_name',
                ]
            ].head(30)
        )
    st.subheader('Data Preview')
    st.dataframe(
        plot_data[
            [
                'date',
                'event_code',
                'event_type',
                'goldstein_scale',
                'num_mentions',
                'location',
                'actor1_name',
                'actor2_name',
            ]
        ].head(30)
    )

build_gis_map()
build_streamlit_plot()
# streamlit run "c:\Users\caroline.tullier\OneDrive - West Point\26-2\SE370 - Computer Aided Sys Eng\Course Project\project\gisplot.py"

import pandas as pd
import streamlit as st
from plotnine import (
    aes,
    coord_fixed,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient2,
    scale_size_continuous,
    theme,
    theme_minimal,
)

st.set_page_config(page_title='Iran Event Severity Plotnine Map', layout='wide')

IRAN_LON_RANGE = (43, 64)
IRAN_LAT_RANGE = (24, 41)
MIDDLE_EAST_LON_RANGE = (25, 75)
MIDDLE_EAST_LAT_RANGE = (10, 45)

CAMEO_ROOT_INTERPRETATIONS = {
    '01': 'Make public statement',
    '02': 'Appeal',
    '03': 'Express intent to cooperate',
    '04': 'Consult',
    '05': 'Diplomatic cooperation',
    '06': 'Material cooperation',
    '07': 'Provide aid',
    '08': 'Yield',
    '09': 'Investigate',
    '10': 'Demand',
    '11': 'Disapprove',
    '12': 'Reject',
    '13': 'Threaten',
    '14': 'Protest',
    '15': 'Military posture',
    '16': 'Reduce relations',
    '17': 'Coerce',
    '18': 'Assault',
    '19': 'Fight',
    '20': 'Mass violence',
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
            'NumMentions',
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
            'Actor1CountryCode': 'string',
            'Actor1Geo_CountryCode': 'string',
            'Actor2CountryCode': 'string',
            'Actor2Geo_CountryCode': 'string',
            'ActionGeo_CountryCode': 'string',
        },
    )

    df = df.rename(columns={
        'SQLDATE': 'date',
        'EventCode': 'event_code',
        'EventRootCode': 'event_root_code',
        'GoldsteinScale': 'goldstein_scale',
        'QuadClass': 'quad_class',
        'NumMentions': 'num_mentions',
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
    df['num_mentions'] = pd.to_numeric(df['num_mentions'], errors='coerce').fillna(1)
    df = df.dropna(subset=['lat', 'lon', 'goldstein_scale'])

    df = add_iran_flags(df)
    df = add_plot_fields(df)
    return df

def add_iran_flags(df):
    df = df.copy()

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

def add_plot_fields(df):
    df = df.copy()
    df['event_type'] = df['event_root_code'].apply(interpret_event_root)
    df['severity'] = -df['goldstein_scale']
    df['mentions_for_size'] = df['num_mentions'].clip(lower=1, upper=50)
    return df

def normalize_root_code(value):
    if pd.isna(value):
        return ''
    return str(value).strip().split('.')[0].zfill(2)

def interpret_event_root(value):
    root = normalize_root_code(value)
    return CAMEO_ROOT_INTERPRETATIONS.get(root, 'Unknown event type')

def filter_iran_focus(df, focus_choice):
    if focus_choice == 'Events located in Iran':
        return df[df['action_in_iran']]
    if focus_choice == 'Events involving Iran anywhere':
        return df[df['iran_related']]
    if focus_choice == 'Conflict events involving Iran':
        return df[df['iran_related'] & df['conflict_related']]
    return df

def filter_map_extent(df, extent_choice):
    if extent_choice == 'Iran':
        lon_min, lon_max = IRAN_LON_RANGE
        lat_min, lat_max = IRAN_LAT_RANGE
    elif extent_choice == 'Middle East':
        lon_min, lon_max = MIDDLE_EAST_LON_RANGE
        lat_min, lat_max = MIDDLE_EAST_LAT_RANGE
    else:
        return df

    return df[
        df['lon'].between(lon_min, lon_max)
        & df['lat'].between(lat_min, lat_max)
    ]

def get_plot_limits(extent_choice, df):
    if extent_choice == 'Iran':
        return IRAN_LON_RANGE, IRAN_LAT_RANGE
    if extent_choice == 'Middle East':
        return MIDDLE_EAST_LON_RANGE, MIDDLE_EAST_LAT_RANGE

    padding = 2
    lon_range = (df['lon'].min() - padding, df['lon'].max() + padding)
    lat_range = (df['lat'].min() - padding, df['lat'].max() + padding)
    return lon_range, lat_range

def create_plotnine_map(plot_data, extent_choice):
    lon_range, lat_range = get_plot_limits(extent_choice, plot_data)

    return (
        ggplot(
            plot_data,
            aes(
                x='lon',
                y='lat',
                color='goldstein_scale',
                size='mentions_for_size',
            ),
        )
        + geom_point(alpha=0.65)
        + scale_color_gradient2(
            low='red',
            mid='yellow',
            high='green',
            midpoint=0,
            limits=(-10, 10),
            name='Goldstein scale',
        )
        + scale_size_continuous(
            range=(1.5, 8),
            name='Mentions',
        )
        + coord_fixed(
            ratio=1.0,
            xlim=lon_range,
            ylim=lat_range,
        )
        + labs(
            title='Iran-Related Events by Severity',
            subtitle='Red is more conflictual; green is more cooperative',
            x='Longitude',
            y='Latitude',
        )
        + theme_minimal()
        + theme(
            figure_size=(12, 7),
            plot_title=element_text(size=16, weight='bold'),
            plot_subtitle=element_text(size=11),
            legend_title=element_text(size=9),
            legend_text=element_text(size=8),
        )
    )

def build_streamlit_plot():
    data = read_data()

    st.title('Iran Event Severity Plotnine Map')
    st.write('Circles are events. Red is most severe or conflictual; green is least severe or cooperative.')

    st.sidebar.header('Plot Settings')
    focus_choice = st.sidebar.selectbox(
        'Iran focus',
        [
            'Conflict events involving Iran',
            'Events involving Iran anywhere',
            'Events located in Iran',
            'All events',
        ],
    )
    extent_choice = st.sidebar.selectbox(
        'Map extent',
        ['Iran', 'Middle East', 'All selected events'],
    )

    filtered_data = filter_iran_focus(data, focus_choice)
    filtered_data = filter_map_extent(filtered_data, extent_choice)

    st.sidebar.write(f"Located in Iran: {data['action_in_iran'].sum():,}")
    st.sidebar.write(f"Involving Iran: {data['iran_related'].sum():,}")
    st.sidebar.write(f"Conflict involving Iran: {(data['iran_related'] & data['conflict_related']).sum():,}")

    if filtered_data.empty:
        st.warning('No events match the selected filters.')
        return

    max_points = min(len(filtered_data), 3000)
    point_limit = st.sidebar.slider(
        'Number of events to plot',
        min_value=1,
        max_value=max_points,
        value=min(max_points, 1000),
        step=100 if max_points >= 100 else 1,
    )

    plot_data = filtered_data.sort_values('severity', ascending=False).head(point_limit)
    plot = create_plotnine_map(plot_data, extent_choice)

    st.subheader('Plotnine GIS-Style Map')
    st.pyplot(plot.draw())

    st.subheader('Filter Summary')
    st.write(f'Selected focus: {focus_choice}')
    st.write(f'Map extent: {extent_choice}')
    st.write(f'Events matching filters: {len(filtered_data):,}')
    st.write(f'Events plotted: {len(plot_data):,}')

    st.subheader('Data Preview')
    st.dataframe(
        plot_data[
            [
                'date',
                'event_code',
                'event_type',
                'goldstein_scale',
                'num_mentions',
                'location',
                'actor1_name',
                'actor2_name',
            ]
        ].head(30)
    )

if __name__ == '__main__':
    build_streamlit_plot()
