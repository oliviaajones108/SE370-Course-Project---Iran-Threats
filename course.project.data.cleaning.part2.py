import os
folder = r"C:\Users\olivia.jones\OneDrive - West Point\COW YEAR\SE370\Code + Files"
print(os.listdir(folder))

INPUT_PATH = r"C:\Users\olivia.jones\OneDrive - West Point\COW YEAR\SE370\Code + Files\20260420.gkg.csv"
OUTPUT_PATH = r"C:\Users\olivia.jones\OneDrive - West Point\COW YEAR\SE370\Code + Files\course.project.data.clean.part2.csv"

import pandas as pd

#INPUT_PATH = r"C:\Users\olivia.jones\OneDrive - West Point\COW YEAR\SE370\Code + Files\20260420_gkg.csv"
#OUTPUT_PATH = r"C:\Users\olivia.jones\OneDrive - West Point\COW YEAR\SE370\Code + Files\course.project.data.clean.part2.csv"

GKG_COLUMNS = [
    "DATE", "NUMARTS", "COUNTS", "THEMES", "LOCATIONS",
    "PERSONS", "ORGANIZATIONS", "TONE", "CAMEOEVENTIDS",
    "SOURCES", "SOURCEURLS",
]

rows = []

with open(INPUT_PATH, "r", encoding="utf-8", errors="replace") as f:
    for i, raw_line in enumerate(f):
        line = raw_line.strip().strip(",").strip('"')
        if not line:
            continue
        fields = line.split("\t")
        if i == 0 and fields[0] == "DATE":
            continue
        fields = (fields + [""] * 11)[:11]
        rows.append(fields)

df = pd.DataFrame(rows, columns=GKG_COLUMNS)

df["DATE"] = pd.to_datetime(df["DATE"], format="%Y%m%d", errors="coerce")
df["NUMARTS"] = pd.to_numeric(df["NUMARTS"], errors="coerce")

tone_cols = ["Tone", "TonePositive", "ToneNegative", "Polarity",
             "ActivityReferenceDensity", "SelfGroupReferenceDensity"]
tone_split = df["TONE"].str.split(",", expand=True).iloc[:, :6]
tone_split.columns = tone_cols[:tone_split.shape[1]]
for col in tone_split.columns:
    tone_split[col] = pd.to_numeric(tone_split[col], errors="coerce")

tone_pos = df.columns.get_loc("TONE")
df = df.drop(columns=["TONE"])
for j, col in enumerate(tone_split.columns):
    df.insert(tone_pos + j, col, tone_split[col])

df.to_csv(OUTPUT_PATH, index=False)

print(f"Done: {len(df)} rows, {len(df.columns)} columns")
print(df.head(3))