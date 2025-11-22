from flask import Blueprint, render_template, request
import pandas as pd
import folium
from folium.plugins import MarkerCluster, MiniMap
import os
import re

irrigation3_bp = Blueprint('irrigation3', __name__)

DATA_DIR = os.path.join('projects', 'irrigation_projects3', 'data')
DATA_FILE = 'karnataka_irr3.xlsx'


def load_data(filepath):
    # Read data safely
    df = pd.read_csv(filepath, encoding='latin1', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    return df


def get_marker_color(status):
    if not isinstance(status, str):
        return '#6b7280'
    status = status.lower()
    if 'complete' in status:
        return '#10b981'
    if 'ongoing' in status or 'progress' in status or 'construction' in status:
        return '#f59e0b'
    if 'planned' in status or 'approved' in status:
        return '#6366f1'
    return '#6b7280'


def create_map(df):
    m = folium.Map(location=[15.3173, 75.7139], zoom_start=7, tiles='CartoDB positron')
    marker_cluster = MarkerCluster().add_to(m)

    lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
    lon_col = next((c for c in df.columns if 'lon' in c.lower() or 'long' in c.lower()), None)

    if not lat_col or not lon_col:
        MiniMap(toggle_display=True).add_to(m)
        folium.LayerControl().add_to(m)
        return m._repr_html_()

    for _, row in df.iterrows():
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
        except Exception:
            continue

        popup_html = f"""
        <div style='font-family:Segoe UI; min-width:320px; border-radius:8px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.15);'>
            <div style="background:#16a34a;color:white;padding:10px 12px;border-radius:8px 8px 0 0;">
                <h4 style="margin:0;font-size:16px;">{row.get('Project Name', 'N/A')}</h4>
            </div>
            <div style="background:white;padding:10px 14px;color:#1e293b;line-height:1.5;">
                <p><i class="fas fa-info-circle" style="color:#10b981;width:18px;"></i> <b>Status:</b> {row.get('Status', 'N/A')}</p>
                <p><i class="fas fa-calendar-alt" style="color:#f59e0b;width:18px;"></i> <b>Duration (Years):</b> {row.get('Project Duration Years', 'N/A')}</p>
                <p><i class="fas fa-indian-rupee-sign" style="color:#0ea5e9;width:18px;"></i> <b>Gross Capacity (TMC):</b> {row.get('Storage_Gross_Capacity_TMC', 'N/A')}</p>
                <p><i class="fas fa-water" style="color:#06b6d4;width:18px;"></i> <b>Live Capacity (TMC):</b> {row.get('Storage_Live_Capacity_TMC', 'N/A')}</p>
                <p><i class="fas fa-tint" style="color:#22c55e;width:18px;"></i> <b>Dam Type:</b> {row.get('Dam_Type', 'N/A')}</p>
                <p><i class="fas fa-ruler-horizontal" style="color:#a855f7;width:18px;"></i> <b>Dam Length (m):</b> {row.get('Dam_Length_Total_Mtr', 'N/A')}</p>
                <p><i class="fas fa-map" style="color:#3b82f6;width:18px;"></i> <b>District:</b> {row.get('Location_District', 'N/A')}</p>
                <p><i class="fas fa-seedling" style="color:#84cc16;width:18px;"></i> <b>Submergence Area (Ha):</b> {row.get('Submergence_Area_Total_Ha', 'N/A')}</p>
                <p><i class="fas fa-bullseye" style="color:#e11d48;width:18px;"></i> <b>Spillway Type:</b> {row.get('Spillway_Type', 'N/A')}</p>
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=400),
            color=get_marker_color(row.get('Status', '')),
            fill=True,
            fillOpacity=0.8
        ).add_to(marker_cluster)

    MiniMap(toggle_display=True).add_to(m)
    folium.LayerControl().add_to(m)
    return m._repr_html_()


@irrigation3_bp.route('/irrigation3')
def irrigation3_dashboard():
    from flask import request

    filepath = os.path.join(DATA_DIR, DATA_FILE)

    # read the original data first (to populate filters)
    try:
        df_all = load_data(filepath)
    except Exception as e:
        # if loading fails, return an error page
        return render_template('index3.html',
                               map_html=f"<p style='color:red;'>Error loading file: {e}</p>",
                               projects=[], stats={}, columns=[], table_data=[], dam_types=[])

    # build full dam type list from original (so dropdown shows all types)
    dam_types = sorted(df_all['Dam_Type'].dropna().unique().tolist()) if 'Dam_Type' in df_all.columns else []

    # start with a working copy (we will filter `df` later)
    df = df_all.copy()

    # server-side filters from querystring (optional)
    selected_dam_type = request.args.get('dam_type', None)
    selected_length_range = request.args.get('dam_length', None)

    try:
        # normalize missing values for display
        df = df.fillna('-')

        # Apply dam type filter (if provided via query params)
        if selected_dam_type and selected_dam_type.lower() != 'all':
            df = df[df['Dam_Type'].astype(str).str.lower().str.contains(selected_dam_type.lower(), na=False)]

        # Normalize/clean Dam Length numeric column once (if present)
        if 'Dam_Length_Total_Mtr' in df.columns:
            # extract numbers and convert; invalid -> 0
            df['Dam_Length_Total_Mtr'] = df['Dam_Length_Total_Mtr'].apply(
                lambda x: float(re.sub(r'[^0-9.]', '', str(x))) if re.search(r'\d', str(x)) else 0.0
            )

        # Apply length range filter (if provided via query params)
        if selected_length_range and selected_length_range.lower() != 'all':
            if selected_length_range == '0-1000':
                df = df[df['Dam_Length_Total_Mtr'] <= 1000]
            elif selected_length_range == '1000-2000':
                df = df[(df['Dam_Length_Total_Mtr'] > 1000) & (df['Dam_Length_Total_Mtr'] <= 2000)]
            elif selected_length_range in ('2000+', '2000_plus', '2000plus'):
                df = df[df['Dam_Length_Total_Mtr'] > 2000]

        # Generate map HTML using filtered df
        map_html = create_map(df)

        # Build the left-side project list. include dam_length so template can place into data-length
        projects = []
        for _, row in df.iterrows():
            def safe_float(value):
                try:
                    if str(value).strip() in ['-', '', 'nan', 'NaN', 'None']:
                        return 0.0
                    return float(value)
                except Exception:
                    return 0.0

            projects.append({
                'name': row.get('Project Name', '-'),
                'status': row.get('Status', '-'),
                'region': row.get('Location_District', '-'),
                'type': row.get('Dam_Type', '-'),
                'amount': safe_float(row.get('Storage_Gross_Capacity_TMC', 0)),
                'hectares': safe_float(row.get('Submergence_Area_Total_Ha', 0)),
                'districts': row.get('Location_District', '-'),
                'purpose': row.get('Spillway_Type', '-'),
                'dpr_date': row.get('Project Duration Years', '-'),
                'lat': row.get('Latitude', None),
                'lng': row.get('Longitude', None),
                # include dam length numeric for client-side filters
                'dam_length': safe_float(row.get('Dam_Length_Total_Mtr', 0))
            })

        # stats aggregation
        def safe_sum(col_name):
            if col_name not in df.columns:
                return 0
            total = 0.0
            for v in df[col_name]:
                try:
                    if str(v).strip() in ['-', '', 'nan', 'NaN', 'None']:
                        continue
                    total += float(str(v).replace(',', '').strip())
                except Exception:
                    continue
            return total

        irrigation_total = safe_sum('Irrigation_Gross_Command_Area_Ha')
        storage_total = safe_sum('Storage_Gross_Capacity_TMC')
        submergence_total = safe_sum('Submergence_Area_Total_Ha')

        stats = {
            'total_projects': len(df),
            'completed_projects': int(df['Status'].astype(str).str.lower().str.contains('complete').sum()) if 'Status' in df.columns else 0,
            'irrigation_total': irrigation_total,
            'storage_total': storage_total,
            'submergence_total': submergence_total
        }

        # table data (full columns for DataTable view)
        columns = df.columns.tolist()
        table_data = df.to_dict(orient='records')

    except Exception as e:
        map_html = f"<p style='color:red;'>Error: {str(e)}</p>"
        projects, stats, columns, table_data = [], {}, [], []

    # always return the template
    return render_template(
        'index3.html',
        map_html=map_html,
        projects=projects,
        stats=stats,
        columns=columns,
        table_data=table_data,
        selected_dam_type=selected_dam_type,
        selected_length_range=selected_length_range,
        dam_types=dam_types
    )
