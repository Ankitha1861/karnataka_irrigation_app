from flask import Blueprint, render_template
import pandas as pd
import folium
from folium.plugins import MarkerCluster, MiniMap
import os
import re

# --- Blueprint setup ---
irrigation2_bp = Blueprint('irrigation2', __name__)

DATA_DIR = os.path.join('projects', 'irrigation_projects2', 'data')
DATA_FILE = 'karnataka_irr2.xlsx'


# --- Load data ---
def load_data(filepath):
    df = pd.read_excel(filepath, engine='openpyxl')
    df.columns = df.columns.str.strip()

    lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
    lon_col = next((c for c in df.columns if 'lon' in c.lower() or 'long' in c.lower()), None)

    if not lat_col or not lon_col:
        return df, pd.DataFrame(), None, None

    df_full = df.copy()
    df_with_coords = df[df[lat_col].notna() & df[lon_col].notna()].copy()
    return df_full, df_with_coords, lat_col, lon_col


# --- Marker color helper ---
def get_marker_color(status):
    mapping = {
        'completed': '#10b981',
        'ongoing': '#f59e0b',
        'under progress': '#f97316',
        'under construction': '#f97316',
        'planned': '#6366f1',
        'approved': '#8b5cf6',
        'nearly complete': '#f59e0b',
        'nearly completed': '#f59e0b'
    }
    if not status:
        return '#6b7280'
    return mapping.get(status.strip().lower(), '#6b7280')


# --- Normalize project status ---
def normalize_status(raw):
    if raw is None:
        return 'unknown'
    s = str(raw).strip().lower()

    if 'nearly' in s and 'complete' in s:
        return 'nearly completed'
    if 'complete' in s:
        return 'completed'
    if 'under construction' in s:
        return 'under construction'
    if 'under progress' in s or 'progress' in s:
        return 'under progress'
    if 'ongoing' in s:
        return 'ongoing'
    if 'planned' in s:
        return 'planned'
    if 'approved' in s:
        return 'approved'
    return s


# --- Create Folium map ---
def create_map(df_with_coords, lat_col, lon_col):
    m = folium.Map(location=[15.3173, 75.7139], zoom_start=7, tiles='CartoDB positron')
    marker_cluster = MarkerCluster().add_to(m)

    if df_with_coords.empty or lat_col is None or lon_col is None:
        MiniMap(toggle_display=True).add_to(m)
        folium.LayerControl().add_to(m)
        return m._repr_html_()

    for _, row in df_with_coords.iterrows():
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
        except Exception:
            continue

        status = normalize_status(row.get('Project Status', ''))
        color = get_marker_color(status)

        
        popup_html = f"""
<div style='font-family:Segoe UI; min-width:300px;'>
    <div style="background:{color};color:white;padding:8px;border-radius:6px 6px 0 0;">
        <h4 style="margin:0;">{row.get('Project Name', 'N/A')}</h4>
    </div>
    <div style="padding:8px;">
        <p><i class="fas fa-check-circle" style="color:#10b981;"></i> <b>Status:</b> {status}</p>
        <p><i class="fas fa-layer-group" style="color:#6366f1;"></i> <b>Type:</b> {row.get('Project Type', 'N/A')}</p>
        <p><i class="fas fa-calendar-alt" style="color:#0ea5e9;"></i> <b>DPR Approval Date:</b> {row.get('DRP Approval Date', 'N/A')}</p>
        <p><i class="fas fa-coins" style="color:#f59e0b;"></i> <b>Approval Amount:</b> ₹ {row.get('Approval Amount', 'N/A')}</p>
        <p><i class="fas fa-seedling" style="color:#22c55e;"></i> <b>Hectares Irrigated:</b> {row.get('Hectares of land irrigated', 'N/A')} Ha</p>
        <p><i class="fas fa-map-marker-alt" style="color:#ef4444;"></i> <b>District:</b> {row.get('District', 'N/A')}</p>
        <p><i class="fas fa-water" style="color:#3b82f6;"></i> <b>Canals under Project:</b> {row.get('Canals under this project', 'N/A')}</p>
    </div>
</div>
"""


        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=400),
            color=color,
            fill=True,
            fillOpacity=0.8
        ).add_to(marker_cluster)

    MiniMap(toggle_display=True).add_to(m)
    folium.LayerControl().add_to(m)
    return m._repr_html_()


# --- Safe numeric sum ---
def safe_sum_numeric(series):
    total = 0.0
    for v in series.fillna(''):
        nums = re.findall(r'\d+(?:\.\d+)?', str(v).replace(',', ''))
        for n in nums:
            try:
                total += float(n)
            except Exception:
                pass
    return total


# --- Compute summary statistics ---
def get_statistics(df_full):
    total_projects = len(df_full)

    amount_col = next((c for c in df_full.columns if 'approval amount' in c.lower() or 'amount' == c.lower()), None)
    hectare_col = next((c for c in df_full.columns if 'hectare' in c.lower()), None)
    status_col = next((c for c in df_full.columns if 'status' in c.lower()), None)

    total_amount = safe_sum_numeric(df_full[amount_col]) if amount_col else 0
    total_hectares = safe_sum_numeric(df_full[hectare_col]) if hectare_col else 0

    completed_projects = 0
    if status_col:
    # Normalize statuses to avoid fuzzy matching
      normalized = df_full[status_col].astype(str).apply(normalize_status)
    completed_projects = (normalized == 'completed').sum()

    return {
        'total_projects': int(total_projects),
        'total_amount': round(total_amount, 2),
        'total_hectares': round(total_hectares, 2),
        'completed_projects': int(completed_projects)
    }


# --- Flask route for irrigation dashboard ---
@irrigation2_bp.route('/irrigation2')
def irrigation2_dashboard():
    filepath = os.path.join(DATA_DIR, DATA_FILE)

    try:
        df_full, df_with_coords, lat_col, lon_col = load_data(filepath)
            # Replace NaN or None values with hyphen for clean table display
        df_full = df_full.fillna('-')


        if df_with_coords is not None and not df_with_coords.empty:
            map_html = create_map(df_with_coords, lat_col, lon_col)
        else:
            map_html = "<p style='color:red;'>No valid coordinates found in data.</p>"

        stats = get_statistics(df_full if df_full is not None else pd.DataFrame())
        table_data = df_full.to_dict(orient='records') if df_full is not None else []

        projects = []
        if df_full is not None and not df_full.empty:
            for _, row in df_full.iterrows():
                raw_status = row.get('Project Status', '')
                status = normalize_status(raw_status)

                lat = row.get(lat_col) if lat_col in row.index else None
                lng = row.get(lon_col) if lon_col in row.index else None

                try:
                    lat = float(lat) if pd.notna(lat) else None
                except Exception:
                    lat = None
                try:
                    lng = float(lng) if pd.notna(lng) else None
                except Exception:
                    lng = None

                projects.append({
                    'name': str(row.get('Project Name', 'N/A')),
                    'status': status,
                    'amount': str(row.get('Approval Amount', '0')),
                    'hectares': str(row.get('Hectares of land irrigated', '0')),
                    'region': str(row.get('District', 'N/A')),
                    'lat': lat,
                    'lng': lng
                })

    except Exception as e:
        map_html = f"<p style='color:red;'>Error: {str(e)}</p>"
        stats = {'total_projects': 0, 'total_amount': 0, 'total_hectares': 0, 'completed_projects': 0}
        table_data = []
        projects = []

    return render_template(
        'index2.html',
        map_html=map_html,
        stats=stats,
        table_data=table_data,
        projects=projects
    )
