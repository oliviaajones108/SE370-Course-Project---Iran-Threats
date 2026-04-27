import pandas as pd

# GDELT 2.0 Events (58 blocks, tab-separated, no header row > .csv with headers)    
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

# Read .csv as strings initially so nothing gets mangled on import
df = pd.read_csv(
    "20260415_export.CSV",
    sep="\t",
    header=None,
    names=GDELT_COLUMNS,
    dtype=str,
)

# Re-label columns here to what we'll actually use, and conversions if needed
df["GLOBALEVENTID"] = pd.to_numeric(df["GLOBALEVENTID"])
df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], format="%Y%m%d")
df["GoldsteinScale"] = pd.to_numeric(df["GoldsteinScale"])
df["AvgTone"] = pd.to_numeric(df["AvgTone"])
df["NumMentions"] = pd.to_numeric(df["NumMentions"])
df["Actor1Geo_Lat"] = pd.to_numeric(df["Actor1Geo_Lat"])
df["Actor1Geo_Long"] = pd.to_numeric(df["Actor1Geo_Long"])
df["ActionGeo_Lat"] = pd.to_numeric(df["ActionGeo_Lat"])
df["ActionGeo_Long"] = pd.to_numeric(df["ActionGeo_Long"])

# Make clean comma-separated CSV with headers
df.to_csv("course.project.data.clean.csv", index=False)

print(f"Done: {len(df)} rows, {len(df.columns)} columns")
print(df.head(3)) 