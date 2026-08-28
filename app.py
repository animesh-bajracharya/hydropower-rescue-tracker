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
    
    # Pre-populate initial flood rescue data
    initial_data = [
        ("Rasuwagadhi Hydropower", 28.2618, 85.3783, "Severely Damaged / Dam Breach", "111 MW", 55, 0, 15),
        ("Upper Trishuli-1 (UT-1)", 28.1402, 85.2917, "Flooded / Tunnel Evacuation", "216 MW", 350, 100, 25),
        ("Upper Trishuli-3A", 27.9712, 85.1884, "Operated / Flooded Powerhouse", "60 MW", 0, 0, 40),
        ("Upper Trishuli-3B", 27.9500, 85.1700, "Under Construction / Damaged", "37 MW", 0, 0, 10),
        ("Trishuli Hydropower Station", 27.9100, 85.1500, "Operational / Inundated", "24 MW", 0, 0, 5),
        ("Devighat Hydropower", 27.8683, 85.1275, "Operational / On Alert", "14.1 MW", 0, 0, 0)
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
