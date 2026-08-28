import sqlite3
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Trishuli Hydropower Rescue Tracker",
    page_icon="🚨",
    layout="wide"
)

DB_FILE = "data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            lat REAL,
            lon REAL,
            status TEXT,
            capacity TEXT,
            rescued INTEGER,
            trapped INTEGER,
            unknown INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
# Recommended schema:
# (project, latitude, longitude, status, capacity, rescued, missing, deaths)

initial_data = [
    # ---------------- RASUWA ----------------
    (
        "Rasuwagadhi Hydropower",
        28.251111, 85.370139,
        "Severely Flood Damaged / Rescue Ongoing",
        "111 MW",
        4, 93, None
    ),

    (
        "Upper Trishuli-1 (UT-1)",
        28.101250, 85.255972,
        "Under Construction / Tunnel Rescue",
        "216 MW",
        350, None, None
    ),

    (
        "Rasuwa Bhotekoshi",
        28.204722, 85.354167,
        "Under Construction / Flood Damaged",
        "120 MW",
        None, 4, None
    ),

    (
        "Sanjen Khola",
        28.263472, 85.277917,
        "Operational / Flood Affected",
        "78 MW",
        None, None, None
    ),

    (
        "Upper Mailung-A",
        28.185417, 85.208333,
        "Under Construction / Flood Affected",
        "6.42 MW",
        None, None, None
    ),

    (
        "Mailung Khola",
        28.075417, 85.204583,
        "Operational / Flood Affected",
        "5 MW",
        None, 7, None
    ),

    (
        "Langtang Khola",
        28.163881, 85.341079,
        "Pre-Operation / Powerhouse Washed Away / Rescue Ongoing",
        "20 MW",
        None, 42, None
    ),

    (
        "Chilime Hydropower",
        28.169722, 85.319583,
        "Operational / Severely Flood Damaged",
        "22 MW",
        None, 8, None
    ),

    # ---------------- NUWAKOT ----------------
    (
        "Upper Trishuli-3A",
        28.046528, 85.199167,
        "Operational / Flood Damaged / Staff Rescue",
        "60 MW",
        None, None, None
    ),

    (
        "Upper Trishuli-3B",
        28.004583, 85.185000,
        "Under Construction / Damaged / Staff Missing",
        "37 MW",
        None, 12, None
    ),

    (
        "Middle Trishuli Ganga",
        None, None,
        "Under Construction / Flood Affected",
        "15.625 MW",
        None, None, None
    ),

    (
        "Trishuli Hydropower Station",
        27.946389, 85.166111,
        "Operational / Flood Damaged",
        "24 MW",
        None, None, None
    ),

    (
        "Devighat Hydropower",
        27.902222, 85.138889,
        "Operational / Flood Affected",
        "14.1 MW",
        None, None, None
    ),
]
    
    for item in initial_data:
        c.execute('''
            INSERT OR IGNORE INTO projects (name, lat, lon, status, capacity, rescued, trapped, unknown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', item)
        
    conn.commit()
    conn.close()

init_db()

# --- DB HELPER FUNCTIONS ---
def get_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM projects", conn)
    conn.close()
    return df

def update_record(project_id, rescued, trapped, unknown, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE projects 
        SET rescued = ?, trapped = ?, unknown = ?, status = ?, last_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (rescued, trapped, unknown, status, project_id))
    conn.commit()
    conn.close()

# --- HEADER SECTION ---
st.title("🚨 Trishuli Basin Hydropower Rescue & Flood Impact Tracker")
st.markdown("Real-time monitoring and situational reporting map along the Trishuli River Cascade.")

# --- METRIC SUMMARY BOARDS ---
df = get_data()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rescued", int(df["rescued"].sum()), delta="Live")
col2.metric("Awaiting Rescue / Trapped", int(df["trapped"].sum()), delta_color="inverse")
col3.metric("Status Unknown / Missing", int(df["unknown"].sum()), delta_color="inverse")
col4.metric("Monitored Dam Sites", len(df))

st.divider()

# --- MAP & DATA SIDE-BY-SIDE ---
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("🗺️ Hydropower Locations & Rescue Map")
    
    # Initialize Folium Map centered on Rasuwa/Trishuli corridor
    m = folium.Map(location=[28.0800, 85.2500], zoom_start=11, tiles="OpenStreetMap")
    
    # Add Google Satellite Hybrid Tile Layer
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.LayerControl().add_to(m)

    # Plot Project Markers
    for _, row in df.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4><b>{row['name']}</b></h4>
            <b>Status:</b> {row['status']}<br>
            <b>Capacity:</b> {row['capacity']}<br><hr>
            <b style="color:green;">Rescued: {row['rescued']}</b><br>
            <b style="color:red;">Trapped/Waiting: {row['trapped']}</b><br>
            <b style="color:orange;">Status Unknown: {row['unknown']}</b>
        </div>
        """
        
        # Marker coloring logic
        color = "green" if row['trapped'] == 0 and row['unknown'] == 0 else "red" if row['trapped'] > 0 else "orange"
        
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row['name'],
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width="100%", height=500)

with right_col:
    st.subheader("✏️ Update Worker Status Data")
    st.caption("Select a site below to update personnel counts as official field data arrives.")
    
    selected_project = st.selectbox("Select Project Site", df["name"].tolist())
    proj_data = df[df["name"] == selected_project].iloc[0]
    
    with st.form("update_form"):
        rescued = st.number_input("Workers Rescued", min_value=0, value=int(proj_data["rescued"]))
        trapped = st.number_input("Trapped / Awaiting Rescue", min_value=0, value=int(proj_data["trapped"]))
        unknown = st.number_input("Status Unknown / Missing", min_value=0, value=int(proj_data["unknown"]))
        status = st.text_input("Project Operational / Damage Status", value=proj_data["status"])
        
        submit = st.form_submit_button("Update Project Data")
        if submit:
            update_record(proj_data["id"], rescued, trapped, unknown, status)
            st.success(f"Updated status for {selected_project} successfully!")
            st.rerun()

# --- DATA TABLE ---
st.subheader("📋 Complete Hydropower Disaster Overview")
st.dataframe(df[["name", "capacity", "status", "rescued", "trapped", "unknown", "last_updated"]], use_container_width=True)
