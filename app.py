"""Streamlit dashboard for Middle East travel-risk exploration.

Run with:
    streamlit run app.py

This file is intentionally kept focused on user-manipulated Streamlit actions:
it lays out the page, creates sidebar widgets, and displays the maps/charts/data
returned by ``app_backend.py``. Data loading, CSV sorting, scoring, and chart
construction live outside this file so the app remains easy to follow.
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
    # Load the dashboard-ready dataset first. ``load_data`` also checks whether
    # the prepared CSV needs to be rebuilt, but that backend detail is hidden
    # from this UI file.
    data = load_data()

    # Build dropdown/multiselect option lists once so the same sorted values can
    # be reused as both the available options and the default selections.
    options = filter_options(data)

    # Page title and caption explain the intent of the dashboard, while keeping
    # the first screen immediately usable.
    st.title("Middle East Travel Risk Dashboard")
    st.caption(
        "Decision support from the combined course project GDELT CSV. Scores combine event volume, event severity, conflict categories, "
        "and airspace-related signals; this is not official government travel advice."
    )

    # The date widget should only allow dates that actually exist in the loaded
    # dataset, so its minimum and maximum are taken from the data itself.
    min_date = data["date"].min().date()
    max_date = data["date"].max().date()

    # Everything in the sidebar is a direct user control. These choices define
    # the travel scenario that the rest of the page summarizes.
    st.sidebar.header("Traveler Filters")
    st.sidebar.write(f"Loaded source CSV files: {data['source_dataset'].nunique()}")
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

    # Streamlit can return either a single date or a two-date range depending on
    # how the user interacts with the widget. The backend normalizes that shape.
    start_date, end_date = normalize_date_range(date_range)

    # Apply the user's filter selections before calculating any scores. This
    # ensures every metric, map, and table reflects the exact sidebar scenario.
    filtered = filter_events(data, start_date, end_date, countries, event_types, only_conflict, only_airspace)
    country_scores = summarize_country_risk(filtered)

    # Avoid rendering charts with no rows. This gives the user immediate
    # feedback when a filter combination is too narrow.
    if filtered.empty:
        st.warning("No events match the current filters.")
        return

    # The first row is the highest risk country because ``summarize_country_risk``
    # returns country scores sorted from highest to lowest.
    riskiest = country_scores.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Highest-risk country", riskiest["country"])
    col2.metric("Recommendation", riskiest["recommendation"])
    col3.metric("Risk score", f"{riskiest['risk_score']:.1f}/100")
    col4.metric("Airspace-related events", f"{int(country_scores['airspace_events'].sum()):,}")

    # The recommendation paragraph turns the computed score into a short,
    # readable explanation for someone using the dashboard for route planning.
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

    # Country Risk: country-level score shown geographically.
    with map_tab:
        st.subheader("Country Risk Choropleth")
        st.caption("Darker blue means higher travel risk for the selected date range and event concerns.")
        st_folium(make_choropleth(country_scores), width=1200, height=610)

    # Event Picture: side-by-side summary charts plus an event-level point map.
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

    # Trend: event counts over time for the current filter scenario.
    with trends_tab:
        st.altair_chart(make_daily_trend_chart(filtered), use_container_width=True)

    # Data: raw tables for anyone who wants to inspect the records behind the
    # summary visuals.
    with data_tab:
        st.subheader("Country Score Table")
        st.dataframe(country_scores, use_container_width=True)
        st.subheader("Highest-Risk Events")
        st.dataframe(highest_risk_events(filtered), use_container_width=True)


if __name__ == "__main__":
    # Streamlit executes the script top-to-bottom. Keeping the page assembly in a
    # function makes the file easier to scan and test-import.
    build_dashboard()
