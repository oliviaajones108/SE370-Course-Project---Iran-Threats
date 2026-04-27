"""Streamlit dashboard for Middle East travel-risk exploration.

Run with:
    streamlit run app.py
"""

import streamlit as st
from streamlit_folium import st_folium

from app_backend import (
    filter_events,
    filter_options,
    highest_risk_events,
    load_data,
    make_choropleth,
    make_daily_trend_chart,
    make_event_map,
    make_event_type_heatmap,
    make_ranking_chart,
    normalize_date_range,
    summarize_country_risk,
)


st.set_page_config(page_title="Middle East Travel Risk Dashboard", layout="wide")


def build_dashboard():
    """Assemble the Streamlit controls, maps, charts, and data tables."""
    data = load_data()
    options = filter_options(data)

    st.title("Middle East Travel Risk Dashboard")
    st.caption(
        "Decision support from all available course project GDELT CSVs. Scores combine event volume, event severity, conflict categories, "
        "and airspace-related signals; this is not official government travel advice."
    )

    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    st.sidebar.header("Traveler Filters")
    st.sidebar.write(f"Loaded source CSVs: {data['source_dataset'].nunique()}")
    st.sidebar.write(f"Unique events loaded: {data['global_event_id'].nunique():,}")
    date_range = st.sidebar.date_input("Event date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    countries = st.sidebar.multiselect(
        "Countries or layover locations",
        options["countries"],
        default=options["countries"],
    )
    event_types = st.sidebar.multiselect(
        "Event types of concern",
        options["event_types"],
        default=options["event_types"],
    )
    only_conflict = st.sidebar.checkbox("Only conflict-related events", value=False)
    only_airspace = st.sidebar.checkbox("Only airspace or aviation signals", value=False)

    start_date, end_date = normalize_date_range(date_range)
    filtered = filter_events(data, start_date, end_date, countries, event_types, only_conflict, only_airspace)
    country_scores = summarize_country_risk(filtered)

    if filtered.empty:
        st.warning("No events match the current filters.")
        return

    riskiest = country_scores.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Highest-risk country", riskiest["country"])
    col2.metric("Recommendation", riskiest["recommendation"])
    col3.metric("Risk score", f"{riskiest['risk_score']:.1f}/100")
    col4.metric("Airspace-related events", f"{int(country_scores['airspace_events'].sum()):,}")

    st.subheader("Recommendation")
    st.write(
        f"For the selected filters, **{riskiest['country']}** has the strongest risk signal. "
        f"The dashboard recommendation is **{riskiest['recommendation']}** because it has "
        f"{int(riskiest['event_count']):,} events, {int(riskiest['severe_events']):,} high/severe events, "
        f"and {int(riskiest['airspace_events']):,} airspace-related signals."
    )

    map_tab, events_tab, trends_tab, data_tab = st.tabs(
        ["Country Risk", "Event Picture", "Trend", "Data"]
    )

    with map_tab:
        st.subheader("Country Risk Choropleth")
        st.caption("Darker blue means higher travel risk for the selected date range and event concerns.")
        st_folium(make_choropleth(country_scores), width=1200, height=610)

    with events_tab:
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Risk Ranking")
            st.altair_chart(make_ranking_chart(country_scores), use_container_width=True)
        with right:
            st.subheader("Events by Type")
            st.altair_chart(make_event_type_heatmap(filtered), use_container_width=True)

        st.subheader("Event Locations")
        st.caption("Circle size and shade both increase with the event-level risk score.")
        st_folium(make_event_map(filtered), width=1200, height=560)

    with trends_tab:
        st.altair_chart(make_daily_trend_chart(filtered), use_container_width=True)

    with data_tab:
        st.subheader("Country Score Table")
        st.dataframe(country_scores, use_container_width=True)
        st.subheader("Highest-Risk Events")
        st.dataframe(highest_risk_events(filtered), use_container_width=True)


if __name__ == "__main__":
    build_dashboard()
