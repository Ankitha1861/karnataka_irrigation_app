from flask import Flask, render_template, request, jsonify
import pandas as pd
import folium
from folium.plugins import MarkerCluster, MiniMap
import os

app = Flask(__name__)
DATA_DIR = ''
DEFAULT_FILE = 'karnataka_irr1.xlsx'


# ✅ Same helper functions (no change)
def load_data(filepath):
    df = pd.read_excel(filepath, engine='openpyxl')
    df.columns = df.columns.str.strip().str.lower()

    # Fix longitude typo if exists
    if 'logitude' in df.columns and 'longitude' not in df.columns:
        df.rename(columns={'logitude': 'longitude'}, inplace=True)

    # Ensure latitude/longitude exist
    if not {'latitude', 'longitude'}.issubset(df.columns):
        raise ValueError(f"Missing coordinate columns. Found: {list(df.columns)}")

    # Drop rows with missing coordinates
    df = df[df['latitude'].notna() & df['longitude'].notna()]

    # ✅ Replace NaN only in **non-numeric columns**
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('-')
        else:
            # For numeric columns, fill NaN with 0 (keeps math valid)
            df[col] = df[col].fillna(0)

    return df





def get_marker_color(status):
    status_colors = {
        'completed': '#10b981',
        'ongoing': '#f59e0b',
        'planned': '#6366f1',
        'under construction': '#f97316',
        'approved': '#8b5cf6'
    }
    return status_colors.get(str(status).lower(), '#6b7280')


def create_map(df):
    m = folium.Map(location=[15.3173, 75.7139], zoom_start=7, tiles='CartoDB dark_matter')
    folium.TileLayer('OpenStreetMap', name='Street View').add_to(m)
    folium.TileLayer('CartoDB positron', name='Light Mode').add_to(m)

    marker_cluster = MarkerCluster(name='Projects', overlay=True, control=True,
                                   icon_create_function="""
        function(cluster) {
            var count = cluster.getChildCount();
            return L.divIcon({
                html: '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">' + count + '</div>',
                className: 'custom-cluster-icon',
                iconSize: L.point(40, 40)
            });
        }
        """).add_to(m)

    for _, row in df.iterrows():
        try:
            lat, lon = float(row['latitude']), float(row['longitude'])
            status = str(row.get('current_status', 'N/A'))
            color = get_marker_color(status)
            popup_html = f"""
<div style="font-family: 'Segoe UI'; min-width: 300px;">
    <div style="background: {color}; color: white; padding: 10px; border-radius: 6px 6px 0 0;">
        <h4 style="margin: 0;">{row.get('project_name', 'N/A')}</h4>
    </div>
    <div style="padding: 10px; line-height: 1.6;">
        <p><i class="fas fa-check-circle" style="color:#10b981;"></i> <b>Status:</b> {status}</p>
        <p><i class="fas fa-calendar-check" style="color:#6366f1;"></i> <b>DPR Approval:</b> {row.get('dpr_approval_date', 'N/A')}</p>
        <p><i class="fas fa-coins" style="color:#f59e0b;"></i> <b>Amount:</b> ₹{row.get('dpr_approval_amount', 'N/A')} Cr</p>
        <p><i class="fas fa-map" style="color:#8b5cf6;"></i> <b>Region:</b> {row.get('region', 'N/A')}</p>
        <p><i class="fas fa-layer-group" style="color:#3b82f6;"></i> <b>Type:</b> {row.get('project_type', 'N/A')}</p>
        <p><i class="fas fa-seedling" style="color:#22c55e;"></i> <b>Area:</b> {row.get('hectares_irrigated', 'N/A')} Ha</p>
        <p><i class="fas fa-map-marker-alt" style="color:#ef4444;"></i> <b>Districts:</b> {row.get('districts_benefitted', 'N/A')}</p>
        <p><i class="fas fa-water" style="color:#0ea5e9;"></i> <b>Purpose:</b> {row.get('primary_purpose', 'N/A')}</p>
    </div>
</div>
"""

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"<b>{row.get('project_name', 'N/A')}</b><br><i>{status}</i>",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                weight=2
            ).add_to(marker_cluster)
        except Exception:
            continue

    MiniMap(toggle_display=True).add_to(m)
    folium.LayerControl().add_to(m)
    return m._repr_html_()


def get_statistics(df):
    return {
        'total_projects': len(df),
        'total_amount': df.get('dpr_approval_amount', pd.Series(dtype=float)).sum(skipna=True),
        'total_hectares': df.get('hectares_irrigated', pd.Series(dtype=float)).sum(skipna=True),
        'status_breakdown': df.get('current_status', pd.Series(dtype=str)).value_counts().to_dict()
    }


def get_projects_list(df):
    return [
        {
            'id': idx,
            'name': row.get('project_name', 'N/A'),
            'status': str(row.get('current_status', 'N/A')),
            'amount': row.get('dpr_approval_amount', 0),
            'hectares': row.get('hectares_irrigated', 0),
            'region': row.get('region', 'N/A'),
            'type': row.get('project_type', 'N/A'),
            'lat': row.get('latitude'),
            'lng': row.get('longitude'),
            'districts': row.get('districts_benefitted', 'N/A'),
            'purpose': row.get('primary_purpose', 'N/A'),
            'dpr_date': str(row.get('dpr_approval_date', 'N/A'))
        }
        for idx, row in df.iterrows()
    ]


# ✅ NEW FUNCTION — Used by the new multi-tab system
def show_dashboard(file_path):
    filepath = os.path.join(DATA_DIR, file_path)
    try:
        # Load Excel file
        df = load_data(filepath)
        map_html = create_map(df)
        stats = get_statistics(df)
        projects = get_projects_list(df)

        # ✅ New part: get all columns + full data
        columns = df.columns.tolist()
        table_data = df.to_dict(orient='records')

    except Exception as e:
        map_html = f"<p style='color:red;'>Error loading map: {str(e)}</p>"
        stats = {'total_projects': 0, 'total_amount': 0, 'total_hectares': 0, 'status_breakdown': {}}
        projects = []
        columns = []
        table_data = []

    # Pass everything to the HTML
    return render_template(
        'index.html',
        map_html=map_html,
        stats=stats,
        projects=projects,
        columns=columns,
        table_data=table_data
    )

# 🟢 Keep this for testing alone (optional)
if __name__ == '__main__':
    app.run(debug=True)
