# SE370-Course-Project-Iran-Threats
A project to establish risk severity for an area given data from kinetic strikes.
Packages to install:
    pip install pandas streamlit streamlit-folium folium branca altair

Package list:
    pandas
    streamlit
    streamlit-folium
    folium
    branca
    altair

How to run the application:
    python -m streamlit run app.py

Data sources used:
    GDELT Event Databases:
        http://data.gdeltproject.org/gkg/index.html
        http://data.gdeltproject.org/events/index.html

How the data was obtained:
    The GDELT files were downloaded directly from the GDELT public data download pages.
    No API or webscraper was used for the raw data collection.
    The downloaded .zip files were extracted into this project folder as CSV files.

This project folder contains raw files:
20260227.export.CSV
20260313.export.CSV
20260327.export.CSV
20260410.export.CSV
20260420.gkg.csv
20260421.export.CSV

And cleaned files (from CP.data.cleaning.large.data.py and CP.dates.data.smaller.py):
course.project.middle_east_travel_risk.csv
course_project_data_clean_part1_combined.csv

Files used to clean/process each dataset:
    gdelt_cleaning.py:
        Cleans raw GDELT event export CSV files by adding headers and converting date/numeric fields.

    CP.data.cleaning.large.data.py:
        Earlier/alternate cleaning script for raw GDELT event export CSV files.

    CP.dates.data.smaller.py:
        Cleans the GDELT Global Knowledge Graph file 20260420.gkg.csv.

    data_preprocessing.py:
        Combines cleaned GDELT event files, filters to Middle East countries, adds risk fields, and creates course.project.middle_east_travel_risk.csv.

