"""Backend helpers for the Middle East travel-risk Streamlit dashboard."""

import math
from pathlib import Path

import altair as alt
import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st

from data_preprocessing import (
    INPUT_PATTERN,
    MIDDLE_EAST_COUNTRIES,
    OUTPUT_FILE,
    prepare_data,
    risk_band,
)
from gdelt_cleaning import sorted_clean_csv_files


# A center point that keeps the Middle East visible at the default Folium zoom.
REGION_CENTER = [29.5, 45.5]

# A single blue scale keeps the maps and charts visually consistent.
MONOCHROME_SCALE = ["#f7fbff", "#deebf7", "#9ecae1", "#4292c6", "#084594"]

# Approximate bounding boxes for course-project visualization. These are not
# official borders; they give Folium polygons to shade without adding a large
# external GeoJSON dependency to the project folder.
COUNTRY_GEOMETRY = {
    "AF": {"center": [33.9, 67.7], "polygon": [[29.4, 60.5], [38.5, 60.5], [38.5, 74.9], [29.4, 74.9], [29.4, 60.5]]},
    "AE": {"center": [24.3, 54.4], "polygon": [[22.6, 51.5], [26.3, 51.5], [26.3, 56.4], [22.6, 56.4], [22.6, 51.5]]},
    "BA": {"center": [26.1, 50.6], "polygon": [[25.5, 50.3], [26.5, 50.3], [26.5, 51.0], [25.5, 51.0], [25.5, 50.3]]},
    "CY": {"center": [35.1, 33.4], "polygon": [[34.4, 32.2], [35.8, 32.2], [35.8, 34.7], [34.4, 34.7], [34.4, 32.2]]},
    "EG": {"center": [26.8, 30.8], "polygon": [[22.0, 24.7], [31.8, 24.7], [31.8, 36.9], [22.0, 36.9], [22.0, 24.7]]},
    "GZ": {"center": [31.4, 34.4], "polygon": [[31.2, 34.2], [31.6, 34.2], [31.6, 34.6], [31.2, 34.6], [31.2, 34.2]]},
    "IR": {"center": [32.4, 53.7], "polygon": [[25.0, 44.0], [39.8, 44.0], [39.8, 63.3], [25.0, 63.3], [25.0, 44.0]]},
    "IS": {"center": [31.0, 35.0], "polygon": [[29.4, 34.2], [33.3, 34.2], [33.3, 35.9], [29.4, 35.9], [29.4, 34.2]]},
    "IZ": {"center": [33.2, 43.7], "polygon": [[29.0, 38.8], [37.4, 38.8], [37.4, 48.6], [29.0, 48.6], [29.0, 38.8]]},
    "JO": {"center": [31.2, 36.5], "polygon": [[29.2, 34.9], [33.4, 34.9], [33.4, 39.3], [29.2, 39.3], [29.2, 34.9]]},
    "KU": {"center": [29.3, 47.5], "polygon": [[28.5, 46.5], [30.2, 46.5], [30.2, 48.5], [28.5, 48.5], [28.5, 46.5]]},
    "LE": {"center": [33.9, 35.9], "polygon": [[33.0, 35.1], [34.7, 35.1], [34.7, 36.7], [33.0, 36.7], [33.0, 35.1]]},
    "MU": {"center": [21.5, 55.9], "polygon": [[16.6, 52.0], [26.4, 52.0], [26.4, 59.9], [16.6, 59.9], [16.6, 52.0]]},
    "PK": {"center": [30.4, 69.3], "polygon": [[23.6, 60.9], [37.1, 60.9], [37.1, 77.1], [23.6, 77.1], [23.6, 60.9]]},
    "QA": {"center": [25.3, 51.2], "polygon": [[24.4, 50.6], [26.2, 50.6], [26.2, 51.8], [24.4, 51.8], [24.4, 50.6]]},
    "SA": {"center": [23.9, 45.1], "polygon": [[16.3, 34.5], [32.2, 34.5], [32.2, 55.7], [16.3, 55.7], [16.3, 34.5]]},
    "SY": {"center": [35.0, 38.5], "polygon": [[32.3, 35.6], [37.4, 35.6], [37.4, 42.4], [32.3, 42.4], [32.3, 35.6]]},
    "TU": {"center": [39.0, 35.2], "polygon": [[35.8, 26.0], [42.2, 26.0], [42.2, 45.0], [35.8, 45.0], [35.8, 26.0]]},
    "WE": {"center": [31.9, 35.2], "polygon": [[31.3, 34.9], [32.6, 34.9], [32.6, 35.6], [31.3, 35.6], [31.3, 34.9]]},
    "YM": {"center": [15.6, 48.5], "polygon": [[12.0, 42.5], [19.0, 42.5], [19.0, 54.6], [12.0, 54.6], [12.0, 42.5]]},
}


@st.cache_data(show_spinner="Preparing Middle East travel risk data...")
def load_data():
    """Load the dashboard dataset, rebuilding it when inputs changed."""
    output_path = Path(OUTPUT_FILE)
    input_paths = sorted_clean_csv_files(INPUT_PATTERN, OUTPUT_FILE)
    output_is_stale = (
        not output_path.exists()
        or any(path.stat().st_mtime > output_path.stat().st_mtime for path in input_paths)
    )
    if output_is_stale:
        prepare_data()
    return pd.read_csv(OUTPUT_FILE, parse_dates=["date"])


def filter_options(data):
    """Return stable option lists for user-facing dashboard controls."""
    return {
        "countries": sorted(data["country"].dropna().unique()),
        "event_types": sorted(data["event_type"].dropna().unique()),
    }


def normalize_date_range(date_range):
    """Convert Streamlit date input output into pandas timestamps."""
    if len(date_range) == 2:
        return pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    selected_date = pd.to_datetime(date_range[0])
    return selected_date, selected_date


def filter_events(data, start_date, end_date, countries, event_types, only_conflict, only_airspace):
    """Apply the user's selected scenario filters to the event dataset."""
    filtered = data[
        data["date"].between(start_date, end_date)
        & data["country"].isin(countries)
        & data["event_type"].isin(event_types)
    ].copy()
    if only_conflict:
        filtered = filtered[filtered["conflict_related"]]
    if only_airspace:
        filtered = filtered[filtered["airspace_related"]]
    return filtered


def summarize_country_risk(df):
    """Aggregate event-level rows into one risk score per country."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "country_code",
                "event_count",
                "conflict_events",
                "severe_events",
                "airspace_events",
                "avg_event_risk",
                "risk_score",
                "recommendation",
            ]
        )

    grouped = (
        df.groupby(["country", "country_code"], as_index=False)
        .agg(
            event_count=("event_risk", "size"),
            conflict_events=("conflict_related", "sum"),
            severe_events=("severity_label", lambda s: s.isin(["High", "Severe"]).sum()),
            airspace_events=("airspace_related", "sum"),
            avg_event_risk=("event_risk", "mean"),
        )
    )
    grouped["conflict_share"] = grouped["conflict_events"] / grouped["event_count"]
    grouped["severe_share"] = grouped["severe_events"] / grouped["event_count"]
    max_events = max(grouped["event_count"].max(), 1)
    max_airspace = max(grouped["airspace_events"].max(), 1)
    volume_signal = grouped["event_count"].apply(lambda value: math.log1p(value) / math.log1p(max_events))
    airspace_signal = grouped["airspace_events"].apply(lambda value: math.log1p(value) / math.log1p(max_airspace))
    grouped["risk_score"] = (
        grouped["avg_event_risk"] * 3
        + grouped["conflict_share"] * 20
        + grouped["severe_share"] * 25
        + volume_signal * 25
        + airspace_signal * 15
    ).clip(upper=100).round(1)
    grouped["recommendation"] = grouped["risk_score"].apply(risk_band)
    return grouped.sort_values("risk_score", ascending=False)


def make_country_geojson(country_scores):
    """Convert country risk scores into GeoJSON features for Folium."""
    features = []
    score_lookup = country_scores.set_index("country_code").to_dict("index")

    for code, name in MIDDLE_EAST_COUNTRIES.items():
        geometry = COUNTRY_GEOMETRY.get(code)
        if geometry is None:
            continue

        row = score_lookup.get(code, {})
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "code": code,
                    "name": name,
                    "risk_score": float(row.get("risk_score", 0)),
                    "recommendation": row.get("recommendation", "No events in selected data"),
                    "event_count": int(row.get("event_count", 0)),
                    "severe_events": int(row.get("severe_events", 0)),
                    "airspace_events": int(row.get("airspace_events", 0)),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(reversed(point)) for point in geometry["polygon"]]],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def make_choropleth(country_scores):
    """Build the country-level shaded risk map."""
    risk_map = folium.Map(location=REGION_CENTER, zoom_start=4, tiles="CartoDB Positron")
    geojson = make_country_geojson(country_scores)
    max_score = max(float(country_scores["risk_score"].max()) if not country_scores.empty else 0, 10)
    color_scale = cm.LinearColormap(
        MONOCHROME_SCALE,
        vmin=0,
        vmax=max_score,
        caption="Travel risk score, lighter to darker blue",
    )

    def style(feature):
        score = feature["properties"]["risk_score"]
        return {
            "fillColor": color_scale(score),
            "color": "#3f4f5f",
            "weight": 1,
            "fillOpacity": 0.78 if score else 0.2,
        }

    tooltip = folium.GeoJsonTooltip(
        fields=["name", "risk_score", "recommendation", "event_count", "severe_events", "airspace_events"],
        aliases=["Country", "Risk score", "Recommendation", "Events", "High/severe events", "Airspace-related"],
        sticky=True,
    )
    folium.GeoJson(geojson, style_function=style, tooltip=tooltip).add_to(risk_map)
    color_scale.add_to(risk_map)
    return risk_map


def make_event_map(df):
    """Build a point map for the highest-risk individual events."""
    event_map = folium.Map(location=REGION_CENTER, zoom_start=4, tiles="CartoDB Positron")
    if df.empty:
        return event_map

    max_risk = max(df["event_risk"].max(), 10)
    color_scale = cm.LinearColormap(MONOCHROME_SCALE, vmin=0, vmax=max_risk, caption="Event risk")
    plot_df = df.sort_values("event_risk", ascending=False).head(1500)

    for _, row in plot_df.iterrows():
        color = color_scale(row["event_risk"])
        popup = (
            f"<b>{row['country']}</b><br>"
            f"<b>Event type:</b> {row['event_type']}<br>"
            f"<b>Event risk:</b> {row['event_risk']}<br>"
            f"<b>Goldstein scale:</b> {row['goldstein_scale']}<br>"
            f"<b>Airspace-related:</b> {row['airspace_related']}<br>"
            f"<b>Location:</b> {row['location']}<br>"
            f"<b>Date:</b> {row['date'].date()}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(3, min(10, 2 + row["event_risk"] / 4)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.68,
            weight=1,
            popup=folium.Popup(popup, max_width=375),
            tooltip=f"{row['country']}: {row['event_type']}",
        ).add_to(event_map)

    color_scale.add_to(event_map)
    return event_map


def blue_chart(chart):
    """Apply the shared blue styling to Altair charts."""
    return chart.configure_range(category=MONOCHROME_SCALE[1:]).configure_axis(labelLimit=180)


def make_ranking_chart(country_scores):
    """Build the country risk ranking chart."""
    ranking = country_scores.head(12)
    chart = (
        alt.Chart(ranking)
        .mark_bar(color="#2171b5")
        .encode(
            x=alt.X("risk_score:Q", title="Risk score"),
            y=alt.Y("country:N", sort="-x", title="Country"),
            tooltip=["country", "risk_score", "event_count", "severe_events", "airspace_events", "recommendation"],
        )
        .properties(height=380)
    )
    return blue_chart(chart)


def make_event_type_heatmap(filtered):
    """Build a heatmap of the most common country-event type pairings."""
    type_counts = (
        filtered.groupby(["country", "event_type"], as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .head(25)
    )
    chart = (
        alt.Chart(type_counts)
        .mark_rect()
        .encode(
            x=alt.X("event_type:N", title="Event type"),
            y=alt.Y("country:N", title="Country"),
            color=alt.Color("size:Q", scale=alt.Scale(range=MONOCHROME_SCALE), title="Events"),
            tooltip=["country", "event_type", "size"],
        )
        .properties(height=380)
    )
    return chart


def make_daily_trend_chart(filtered):
    """Build the daily event-count trend chart."""
    daily = (
        filtered.assign(day=filtered["date"].dt.date)
        .groupby("day", as_index=False)
        .agg(events=("event_risk", "size"), average_risk=("event_risk", "mean"))
    )
    chart = (
        alt.Chart(daily)
        .mark_line(color="#084594", point=True)
        .encode(
            x=alt.X("day:T", title="Date"),
            y=alt.Y("events:Q", title="Events"),
            tooltip=["day:T", "events", alt.Tooltip("average_risk:Q", format=".1f")],
        )
        .properties(height=360)
    )
    return blue_chart(chart)


def highest_risk_events(filtered, limit=200):
    """Return the highest-risk event rows for the data table."""
    columns = [
        "date",
        "country",
        "event_type",
        "severity_label",
        "event_risk",
        "goldstein_scale",
        "airspace_related",
        "location",
        "actor1_name",
        "actor2_name",
        "source_dataset",
    ]
    return filtered.sort_values("event_risk", ascending=False)[columns].head(limit)
