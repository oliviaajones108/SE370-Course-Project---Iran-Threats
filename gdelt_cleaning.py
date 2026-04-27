"""Convert a raw GDELT export into a cleaner comma-separated CSV.

Run this script only when you have a raw tab-separated GDELT file, such as
``20260415_export.CSV``, that does not already include column headers. The rest
of the project expects cleaned CSV files whose names start with
``course.project.data.clean``.
"""

from pathlib import Path

import pandas as pd


# Keep the input/output paths near the top so they are easy to change for a new
# GDELT download date without hunting through the script.
RAW_GDELT_FILE = Path("20260415_export.CSV")
CLEAN_OUTPUT_FILE = Path("course.project.data.clean.csv")

# GDELT 2.0 event exports contain 58 tab-separated fields and no header row.
# This list supplies the official field names so pandas can label the dataset.
GDELT_COLUMNS = [
    # Identifiers + time
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",

    # Actor 1
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",

    # Actor 2
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",

    # Event class
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
    "QuadClass", "GoldsteinScale",

    # Counting
    "NumMentions", "NumSources", "NumArticles", "AvgTone",

    # Actor 1 geography
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",

    # Actor 2 geography
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID",

    # Action geography (where the event happened)
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID",

    # Sources
    "DATEADDED", "SOURCEURL",
]

def clean_raw_gdelt_export(input_file=RAW_GDELT_FILE, output_file=CLEAN_OUTPUT_FILE):
    """Read a raw GDELT event file and write a headered CSV.

    The raw file is loaded as strings first because GDELT identifiers and codes
    can look numeric even when they should remain stable labels. After loading,
    only the fields used numerically by the app are converted.
    """

    if not input_file.exists():
        raise FileNotFoundError(f"Could not find raw GDELT file: {input_file}")

    # The raw GDELT event export is tab-separated even though many downloaded
    # examples end in .CSV. ``header=None`` tells pandas that the first row is
    # data, not column names.
    df = pd.read_csv(
        input_file,
        sep="\t",
        header=None,
        names=GDELT_COLUMNS,
        dtype=str,
    )

    # Convert date and scoring columns after import so calculations, filtering,
    # and plotting work correctly in the downstream preprocessing step.
    df["GLOBALEVENTID"] = pd.to_numeric(df["GLOBALEVENTID"], errors="coerce")
    df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], format="%Y%m%d", errors="coerce")
    df["GoldsteinScale"] = pd.to_numeric(df["GoldsteinScale"], errors="coerce")
    df["AvgTone"] = pd.to_numeric(df["AvgTone"], errors="coerce")
    df["NumMentions"] = pd.to_numeric(df["NumMentions"], errors="coerce")
    df["Actor1Geo_Lat"] = pd.to_numeric(df["Actor1Geo_Lat"], errors="coerce")
    df["Actor1Geo_Long"] = pd.to_numeric(df["Actor1Geo_Long"], errors="coerce")
    df["ActionGeo_Lat"] = pd.to_numeric(df["ActionGeo_Lat"], errors="coerce")
    df["ActionGeo_Long"] = pd.to_numeric(df["ActionGeo_Long"], errors="coerce")

    # The output is the stable input format for ``data_preprocessing.py``.
    df.to_csv(output_file, index=False)
    return df


if __name__ == "__main__":
    cleaned = clean_raw_gdelt_export()
    print(f"Done: {len(cleaned)} rows, {len(cleaned.columns)} columns")
    print(f"Wrote {CLEAN_OUTPUT_FILE}")
    print(cleaned.head(3))
