"""Prepare the dashboard-ready Middle East travel risk dataset.

This module combines every cleaned GDELT CSV in the project folder, keeps only
Middle East records, adds readable event labels, computes simple risk signals,
and writes the final dataset consumed by ``app.py``.
"""

import math
from pathlib import Path

import pandas as pd


# Input files are the cleaned CSVs produced by ``gdelt_cleaning.py`` or provided
# with the course project. The glob allows multiple weekly/daily extracts.
INPUT_PATTERN = "course.project.data.clean*.csv"

# ``app.py`` reads this file; it is rebuilt automatically when an input CSV is
# newer than the existing output.
OUTPUT_FILE = "course.project.middle_east_travel_risk.csv"

MIDDLE_EAST_COUNTRIES = {
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "BA": "Bahrain",
    "CY": "Cyprus",
    "EG": "Egypt",
    "GZ": "Gaza Strip",
    "IR": "Iran",
    "IS": "Israel",
    "IZ": "Iraq",
    "JO": "Jordan",
    "KU": "Kuwait",
    "LE": "Lebanon",
    "MU": "Oman",
    "PK": "Pakistan",
    "QA": "Qatar",
    "SA": "Saudi Arabia",
    "SY": "Syria",
    "TU": "Turkey",
    "WE": "West Bank",
    "YM": "Yemen",
}

CAMEO_ROOT_INTERPRETATIONS = {
    "01": "Public statement",
    "02": "Appeal",
    "03": "Intent to cooperate",
    "04": "Consultation",
    "05": "Diplomatic cooperation",
    "06": "Material cooperation",
    "07": "Aid",
    "08": "Yield",
    "09": "Investigate",
    "10": "Demand",
    "11": "Disapprove",
    "12": "Reject",
    "13": "Threaten",
    "14": "Protest",
    "15": "Military posture",
    "16": "Reduce relations",
    "17": "Coerce",
    "18": "Assault",
    "19": "Fight",
    "20": "Mass violence",
}

AIRSPACE_PATTERN = (
    r"airspace|air-space|air space|flight|flights|airport|airline|aviation|"
    r"air-traffic|air traffic|missile|drone|rocket"
)


def normalize_root_code(value):
    """Return a two-character CAMEO root code such as ``18`` or ``04``."""
    if pd.isna(value):
        return "00"
    text = str(value).strip().split(".")[0]
    return text.zfill(2) if text else "00"


def normalize_event_code(value):
    """Return a three-character CAMEO event code for consistent display."""
    if pd.isna(value):
        return ""
    text = str(value).strip().split(".")[0]
    return text.zfill(3) if text else ""


def score_event(row):
    """Compute one event-level risk score from severity and visibility signals."""
    goldstein = row["goldstein_scale"]
    quad_class = row["quad_class"]
    root = row["event_root_code"]
    mentions = max(row["num_mentions"], 1)

    # Negative Goldstein scores indicate conflictual events. Positive scores
    # start at zero risk here because cooperation should not increase danger.
    severity = max(0.0, -goldstein)
    if quad_class == 4:
        severity += 4
    elif quad_class == 3:
        severity += 2

    # CAMEO roots 18-20 are the most violent categories, while threats,
    # military posture, coercion, protests, and rejected demands add less.
    if root in {"18", "19", "20"}:
        severity += 6
    elif root in {"13", "15", "17"}:
        severity += 4
    elif root in {"14", "16"}:
        severity += 2
    elif root == "12":
        severity += 1

    # Airspace and aviation terms matter for a travel-risk dashboard because
    # they can affect route planning even when the event is not on the ground.
    if row["airspace_related"]:
        severity += 8

    mention_multiplier = 1 + min(math.log1p(mentions), 4) / 8
    return round(severity * mention_multiplier, 2)


def risk_band(score):
    """Translate a numeric country score into a travel recommendation label."""
    if score >= 75:
        return "Avoid travel or route around"
    if score >= 50:
        return "Reconsider nonessential travel"
    if score >= 25:
        return "Use caution"
    return "Generally proceed"


def prepare_data():
    """Build and save the dashboard-ready dataset from all matching CSV files."""
    usecols = [
        "GLOBALEVENTID",
        "SQLDATE",
        "EventCode",
        "EventRootCode",
        "GoldsteinScale",
        "QuadClass",
        "NumMentions",
        "Actor1Name",
        "Actor1CountryCode",
        "Actor1Geo_FullName",
        "Actor1Geo_CountryCode",
        "Actor2Name",
        "Actor2CountryCode",
        "Actor2Geo_FullName",
        "Actor2Geo_CountryCode",
        "ActionGeo_FullName",
        "ActionGeo_CountryCode",
        "ActionGeo_Lat",
        "ActionGeo_Long",
        "SOURCEURL",
    ]

    # Collect every cleaned course-project CSV but avoid feeding the derived
    # travel-risk output back into itself.
    input_files = sorted(
        path
        for path in Path(".").glob(INPUT_PATTERN)
        if path.name != OUTPUT_FILE
    )
    if not input_files:
        raise FileNotFoundError(f"No input files matched {INPUT_PATTERN}")

    # Load each source as strings first. This avoids losing leading zeroes in
    # event codes before they are normalized below.
    frames = []
    for path in input_files:
        frame = pd.read_csv(path, usecols=usecols, dtype="string")
        frame["source_dataset"] = path.name
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    df = df.rename(
        columns={
            "GLOBALEVENTID": "global_event_id",
            "SQLDATE": "date",
            "EventCode": "event_code",
            "EventRootCode": "event_root_code",
            "GoldsteinScale": "goldstein_scale",
            "QuadClass": "quad_class",
            "NumMentions": "num_mentions",
            "Actor1Name": "actor1_name",
            "Actor1CountryCode": "actor1_country_code",
            "Actor1Geo_FullName": "actor1_geo",
            "Actor1Geo_CountryCode": "actor1_geo_country_code",
            "Actor2Name": "actor2_name",
            "Actor2CountryCode": "actor2_country_code",
            "Actor2Geo_FullName": "actor2_geo",
            "Actor2Geo_CountryCode": "actor2_geo_country_code",
            "ActionGeo_FullName": "location",
            "ActionGeo_CountryCode": "country_code",
            "ActionGeo_Lat": "lat",
            "ActionGeo_Long": "lon",
            "SOURCEURL": "source_url",
        }
    )

    # One GDELT event can appear in multiple source extracts. Keeping the last
    # copy preserves the newest available record for that event id.
    before_dedupe = len(df)
    df = df.drop_duplicates(subset=["global_event_id"], keep="last")
    df["country_code"] = df["country_code"].str.upper()
    df = df[df["country_code"].isin(MIDDLE_EAST_COUNTRIES)].copy()

    # Convert the fields used for filtering, scoring, and plotting. Invalid
    # coordinates or scores are dropped because they cannot be mapped reliably.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["goldstein_scale"] = pd.to_numeric(df["goldstein_scale"], errors="coerce")
    df["quad_class"] = pd.to_numeric(df["quad_class"], errors="coerce")
    df["num_mentions"] = pd.to_numeric(df["num_mentions"], errors="coerce").fillna(1)
    df = df.dropna(subset=["date", "lat", "lon", "goldstein_scale", "quad_class"])

    df["event_root_code"] = df["event_root_code"].apply(normalize_root_code)
    df["event_code"] = df["event_code"].apply(normalize_event_code)
    df["country"] = df["country_code"].map(MIDDLE_EAST_COUNTRIES)
    df["event_type"] = df["event_root_code"].map(CAMEO_ROOT_INTERPRETATIONS).fillna("Other")
    df["conflict_related"] = (df["goldstein_scale"] < 0) | df["quad_class"].isin([3, 4])

    # Search a few descriptive text fields for airspace-related terms. This is a
    # lightweight keyword signal, not a formal NLP classifier.
    search_text = (
        df["location"].fillna("")
        + " "
        + df["actor1_name"].fillna("")
        + " "
        + df["actor2_name"].fillna("")
        + " "
        + df["source_url"].fillna("")
    )
    df["airspace_related"] = search_text.str.contains(AIRSPACE_PATTERN, case=False, regex=True)
    df["event_risk"] = df.apply(score_event, axis=1)
    df["severity_label"] = pd.cut(
        df["event_risk"],
        bins=[-0.1, 3, 8, 15, 100],
        labels=["Low", "Moderate", "High", "Severe"],
    ).astype("string")

    # Keep the final CSV focused on the columns the dashboard actually needs.
    output_cols = [
        "global_event_id",
        "source_dataset",
        "date",
        "country",
        "country_code",
        "event_code",
        "event_root_code",
        "event_type",
        "goldstein_scale",
        "quad_class",
        "num_mentions",
        "event_risk",
        "severity_label",
        "conflict_related",
        "airspace_related",
        "location",
        "lat",
        "lon",
        "actor1_name",
        "actor2_name",
        "source_url",
    ]
    df[output_cols].to_csv(OUTPUT_FILE, index=False)
    df.attrs["input_files"] = [path.name for path in input_files]
    df.attrs["raw_rows"] = before_dedupe
    df.attrs["deduped_rows"] = len(df)
    return df


if __name__ == "__main__":
    prepared = prepare_data()
    countries = prepared["country"].nunique()
    input_files = ", ".join(prepared.attrs.get("input_files", []))
    print(f"Loaded inputs: {input_files}")
    print(f"Raw combined rows before de-duplication: {prepared.attrs.get('raw_rows', 'unknown'):,}")
    print(f"Prepared {len(prepared):,} Middle East records across {countries} countries.")
    print(f"Wrote {OUTPUT_FILE}")
