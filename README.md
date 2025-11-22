Karnataka Irrigation Projects – GIS Dashboard

A comprehensive, map-based interactive dashboard built using Flask, Folium, DataTables, and Pandas to visualize irrigation projects across Karnataka.
This system integrates three major datasets:

Annual Report – 2024 (Irrigation Project 1)

KNNL FY 2020–21 Annual Report (Irrigation Project 2)

Ongoing Major & Medium Irrigation Projects (Irrigation Project 3)

Each dataset loads into an independent dashboard with:
✔ Interactive Map
✔ Project Statistics
✔ Complete Data Table
✔ Filters
✔ Coordinates-based markers
✔ PDF report links
✔ Source references

📌 Features
✅ 1. Interactive GIS Map

Location-based visualization using Folium

Status-wise color-coded markers

Popups containing complete project details

Clustered markers for dense regions

✅ 2. Full Data Table (DataTables.js)

Shows all XLS/CSV columns

Search, sort, pagination

"Next" & "Previous" navigation

NaN values replaced with -

✅ 3. Custom Filters

Each dashboard contains different filters depending on the dataset.

Irrigation Project 3 Filters

Dam Type Filter

Dam Length Filter (0–1000, 1000–2000, 2000+)

Live updates map + table

✅ 4. Summary Cards

Each dashboard shows:

Total Projects

Completed Projects

Additional metrics based on dataset:

Irrigation_Gross_Command_Area_Ha

Storage_Gross_Capacity_TMC

Submergence_Area_Total_Ha

✅ 5. PDF Reports

Each project section includes:

Clickable PDF links

Opens in a separate tab

Source details added

Annual Report 2023

KNNL FY 2020–21

Karnataka Govt Water Resources Department

📁 Folder Structure
karnataka_irrigation_app/
│── app.py
│── requirements.txt
│
├── projects/
│   ├── irrigation_projects1/
│   │   ├── data/karnataka_irr1.xlsx
│   │   ├── templates/index.html
│   │   └── routes.py
│   │
│   ├── irrigation_projects2/
│   │   ├── data/karnataka_irr2.xlsx
│   │   ├── templates/index2.html
│   │   └── routes.py
│   │
│   ├── irrigation_projects3/
│   │   ├── data/karnataka_irr3.xlsx
│   │   ├── templates/index3.html
│   │   └── routes.py
│   │
│   └── app_original.py
│
├── static/
│   └── reports/
│       ├── AnnualReportMarch-2024English97-2003format.pdf
│       ├── KNNL FY 2020-21 Annual report- English.pdf
│
└── templates/
    ├── home_tabs.html
    ├── home.html
    ├── base.html
    ├── index.html
    ├── index2.html
    ├── index3.html

⚙️ Installation & Setup
1️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Run the Application
python app.py
