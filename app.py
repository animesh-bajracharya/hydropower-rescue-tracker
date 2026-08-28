import sqlite3
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Trishuli Hydropower Rescue Tracker",
    page_icon="🚨",
    layout="wide"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_FILE = "data.db"


# ============================================================
# SEED HYDROPOWER DATA (Only used on first run)
# ============================================================

initial_data = [

    # ========================================================
    # RASUWA
    # ========================================================

    (
        "Rasuwagadhi Hydropower",
        28.271201,
        85.376954,
        "Severely Flood Damaged / Rescue Ongoing",
        "111 MW",
        4,
        93,
        0
    ),

    (
        "Power House of Rasuwagadhi Hydropower",
        28.239364,
        85.357702,
        "Severely Flood Damaged / Rescue Ongoing",
        "111 MW",
        0,
        0,
        0
    ),

    (
        "Upper Trishuli-1 (UT-1)",
        28.120012,
        85.288452,
        "Under Construction / Tunnel Rescue",
        "216 MW",
        350,
        0,
        0
    ),

    (
        "Rasuwa Bhotekoshi",
        28.204722,
        85.354167,
        "Under Construction / Flood Damaged",
        "120 MW",
        0,
        4,
        0
    ),

    (
        "Mailung Khola",
        28.075417,
        85.204583,
        "Operational / Flood Affected",
        "5 MW",
        0,
        7,
        0
    ),

    (
        "Langtang Khola",
        28.163881,
        85.341079,
        "Pre-Operation / Powerhouse Washed Away / Rescue Ongoing",
        "20 MW",
        0,
        42,
        0
    ),

    (
        "Chilime Hydropower Plant Site Office",
        28.165684,
        85.340518,
        "Operational / Severely Flood Damaged",
        "22 MW",
        0,
        8,
        0
    ),

    (
        "Chilime Hydropower Station",
        28.157655,
        85.332012,
        "Operational / Severely Flood Damaged",
        "22 MW",
        0,
        8,
        0
    ),


    # ========================================================
    # NUWAKOT
    # ========================================================

    (
        "Upper Trishuli-3A",
        28.063835,
        85.206792,
        "Operational / Flood Damaged / Staff Rescue",
        "60 MW",
        0,
        0,
        0
    ),

    (
        "Upper Trishuli-3A Hydropower Office",
        28.027158,
        85.189622,
        "Operational / Flood Damaged / Staff Rescue",
        "60 MW",
        0,
        0,
        0
    ),

    (
        "Upper Trishuli-3A Powerhouse",
        28.025518,
        85.186025,
        "Operational / Flood Damaged / Staff Rescue",
        "60 MW",
        0,
        0,
        0
    ),
    
    (
        "Upper Trishuli-3B Adit Tunnel",
        28.010176,
        85.181577,
        "Under Construction / Damaged / Staff Missing",
        "37 MW",
        0,
        12,
        0
    ),
    
    (
        "Upper Trishuli-3B",
        27.995746,
        85.183409,
        "Under Construction / Damaged / Staff Missing",
        "37 MW",
        0,
        12,
        0
    ),

    (
        "Middle Trishuli Ganga",
        None,
        None,
        "Under Construction / Flood Affected",
        "15.625 MW",
        0,
        0,
        0
    ),

    (
        "Trishuli Hydropower Station",
        27.963010,
        85.170522,
        "Operational / Flood Damaged",
        "24 MW",
        0,
        0,
        0
    ),

    (
        "Trishuli Hydropower Canal",
        27.925401,
        85.147146,
        "Operational / Flood Damaged",
        "24 MW",
        0,
        0,
        0
    ),
    
    (
        "Trishuli Hydropower Power House",
        27.921457,
        85.145913,
        "Operational / Flood Damaged",
        "24 MW",
        0,
        0,
        0
    ),
    
    (
        "Devighat Hydropower",
        27.888675,
        85.133819,
        "Operational / Flood Affected",
        "14.1 MW",
        0,
        0,
        0
    ),
   
    (
        "Nuwakot Solar Power Station",
        27.890981,
        85.134356,
        "Operational / Flood Affected",
        "24 MW",
        0,
        0,
        0
    ),
]


# ============================================================
# DATABASE INITIALIZATION & SAFE PRESERVATION
# ============================================================

def init_db():

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            lat REAL,
            lon REAL,
            status TEXT,
            capacity TEXT,
            rescued INTEGER DEFAULT 0,
            trapped INTEGER DEFAULT 0,
            unknown INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # Safe Insertion: Only insert seed data if the record
    # does NOT exist in the database. Existing numbers are preserved.
    # --------------------------------------------------------

    for item in initial_data:
        c.execute("""
            INSERT INTO projects (name, lat, lon, status, capacity, rescued, trapped, unknown)
            SELECT ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM projects WHERE name = ?)
        """, (item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[0]))

    conn.commit()
    conn.close()


# Initialize database safely
init_db()


# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================

def get_data():

    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        """
        SELECT
            id,
            name,
            lat,
            lon,
            status,
            capacity,
            rescued,
            trapped,
            unknown,
            last_updated
        FROM projects
        ORDER BY id
        """,
        conn
    )
    conn.close()

    # Protect against NULL / NaN values
    numeric_columns = ["rescued", "trapped", "unknown"]
    for column in numeric_columns:
        df[column] = (
            pd.to_numeric(df[column], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    return df


def update_record(project_id, name, rescued, trapped, unknown, status):

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        UPDATE projects
        SET
            name = ?,
            rescued = ?,
            trapped = ?,
            unknown = ?,
            status = ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        name,
        int(rescued),
        int(trapped),
        int(unknown),
        status,
        int(project_id)
    ))

    conn.commit()
    conn.close()


def add_new_project(name, lat, lon, status, capacity, rescued, trapped, unknown):

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO projects (name, lat, lon, status, capacity, rescued, trapped, unknown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            lat if lat != 0.0 else None,
            lon if lon != 0.0 else None,
            status,
            capacity,
            int(rescued),
            int(trapped),
            int(unknown)
        ))
        conn.commit()
        success = True
        msg = f"Successfully added {name}!"
    except sqlite3.IntegrityError:
        success = False
        msg = f"A project named '{name}' already exists."
    finally:
        conn.close()

    return success, msg


# ============================================================
# LOAD DATA
# ============================================================

df = get_data()


# ============================================================
# HEADER
# ============================================================

st.title("🚨 Trishuli Basin Hydropower Rescue & Flood Impact Tracker")

st.markdown(
    """
    **Real-time monitoring and situational reporting dashboard**
    for hydropower projects affected by the Trishuli River flood disaster.
    """
)


# ============================================================
# SUMMARY METRICS
# ============================================================

total_rescued = int(df["rescued"].sum())
total_trapped = int(df["trapped"].sum())
total_unknown = int(df["unknown"].sum())
total_projects = len(df)

col1, col2, col3, col4 = st.columns(4)

col1.metric("👷 Total Rescued", f"{total_rescued:,}", delta="Live")
col2.metric("🚨 Awaiting Rescue / Trapped", f"{total_trapped:,}", delta_color="inverse")
col3.metric("❓ Status Unknown / Missing", f"{total_unknown:,}", delta_color="inverse")
col4.metric("🏗️ Monitored Hydropower Sites", total_projects)

st.divider()


# ============================================================
# PROJECT SELECTION
# ============================================================

st.subheader("📍 Select Project")

selected_project = st.selectbox(
    "Select a project to highlight on the map",
    df["name"].tolist(),
    label_visibility="collapsed"
)

selected_data = df[df["name"] == selected_project].iloc[0]


# ============================================================
# MAP + UPDATE PANEL
# ============================================================

left_col, right_col = st.columns([2, 1])


# ============================================================
# MAP
# ============================================================

with left_col:

    st.subheader("🗺️ Hydropower Locations & Rescue Map")

    if pd.notna(selected_data["lat"]) and pd.notna(selected_data["lon"]):
        map_center = [float(selected_data["lat"]), float(selected_data["lon"])]
        map_zoom = 14
    else:
        map_center = [28.0800, 85.2500]
        map_zoom = 10

    m = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles="OpenStreetMap"
    )

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=False,
        control=True
    ).add_to(m)

    for _, row in df.iterrows():

        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            continue

        rescued = int(row["rescued"])
        trapped = int(row["trapped"])
        unknown = int(row["unknown"])

        if trapped > 0:
            marker_color = "red"
        elif unknown > 0:
            marker_color = "orange"
        elif rescued > 0:
            marker_color = "green"
        else:
            marker_color = "blue"

        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4><b>{row['name']}</b></h4>
            <b>Status:</b> {row['status']}<br><br>
            <b>Capacity:</b> {row['capacity']}<hr>
            <b>👷 Rescued:</b> {rescued}<br>
            <b>🚨 Trapped / Awaiting:</b> {trapped}<br>
            <b>❓ Unknown / Missing:</b> {unknown}<hr>
            <small>Last updated: {row['last_updated']}</small>
        </div>
        """

        is_selected = (row["name"] == selected_project)

        if is_selected:
            folium.Circle(
                location=[float(row["lat"]), float(row["lon"])],
                radius=600,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.12,
                weight=3,
                tooltip=f"📍 SELECTED SITE: {row['name']}"
            ).add_to(m)

            folium.CircleMarker(
                location=[float(row["lat"]), float(row["lon"])],
                radius=25,
                color="blue",
                fill=False,
                weight=5,
                opacity=1.0
            ).add_to(m)

            folium.Marker(
                location=[float(row["lat"]), float(row["lon"])],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"📍 SELECTED: {row['name']}",
                icon=folium.Icon(color="blue", icon="star", prefix="fa")
            ).add_to(m)

        else:
            folium.Marker(
                location=[float(row["lat"]), float(row["lon"])],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=row["name"],
                icon=folium.Icon(color=marker_color, icon="info-sign")
            ).add_to(m)

    legend_html = """
    <div style="
        position: fixed; bottom: 20px; left: 20px; z-index: 9999;
        background-color: white; padding: 12px 15px; border: 2px solid #777;
        border-radius: 6px; font-family: Arial; font-size: 13px; line-height: 1.7;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    ">
        <b>MAP LEGEND</b><br>
        <span style="color:red; font-size:18px;">●</span> Active Rescue / Trapped<br>
        <span style="color:orange; font-size:18px;">●</span> Status Unknown / Missing<br>
        <span style="color:green; font-size:18px;">●</span> Rescue Recorded<br>
        <span style="color:blue; font-size:18px;">●</span> Monitored Site<br>
        <span style="color:blue; font-size:18px;">★</span> Selected Site
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=600)


# ============================================================
# UPDATE & ENTRY PANEL
# ============================================================

with right_col:

    st.subheader("✏️ Edit Selected Site")

    # UPDATE EXISTING SITE FORM
    with st.form("update_form", clear_on_submit=False):

        name = st.text_input(
            "📍 Project Name",
            value=str(selected_data["name"])
        )

        rescued = st.number_input(
            "👷 Workers Rescued",
            min_value=0,
            value=int(selected_data["rescued"]),
            step=1
        )

        trapped = st.number_input(
            "🚨 Trapped / Awaiting Rescue",
            min_value=0,
            value=int(selected_data["trapped"]),
            step=1
        )

        unknown = st.number_input(
            "❓ Status Unknown / Missing",
            min_value=0,
            value=int(selected_data["unknown"]),
            step=1
        )

        status = st.text_input(
            "🏗️ Project Operational / Damage Status",
            value=str(selected_data["status"])
        )

        submit = st.form_submit_button("💾 Save Project Updates")

        if submit:
            update_record(
                selected_data["id"],
                name,
                rescued,
                trapped,
                unknown,
                status
            )
            st.success(f"Updated {name} successfully!")
            st.rerun()

    st.divider()

    # ADD NEW SITE EXPANDER FORM
    with st.expander("➕ Add New Project Site"):
        with st.form("add_form", clear_on_submit=True):
            new_name = st.text_input("Project Name *")
            new_capacity = st.text_input("Capacity (e.g., 25 MW)")
            new_status = st.text_input("Initial Status", value="Under Assessment")
            
            c_lat, c_lon = st.columns(2)
            new_lat = c_lat.number_input("Latitude", value=0.0, format="%.6f")
            new_lon = c_lon.number_input("Longitude", value=0.0, format="%.6f")

            p1, p2, p3 = st.columns(3)
            new_rescued = p1.number_input("Rescued", min_value=0, value=0)
            new_trapped = p2.number_input("Trapped", min_value=0, value=0)
            new_unknown = p3.number_input("Unknown", min_value=0, value=0)

            add_submit = st.form_submit_button("➕ Register New Project")

            if add_submit:
                if not new_name.strip():
                    st.error("Project Name is required.")
                else:
                    success, msg = add_new_project(
                        new_name.strip(),
                        new_lat,
                        new_lon,
                        new_status,
                        new_capacity,
                        new_rescued,
                        new_trapped,
                        new_unknown
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# ============================================================
# DATA TABLE
# ============================================================

st.subheader("📋 Complete Hydropower Disaster Overview")

display_df = df[
    [
        "name",
        "capacity",
        "status",
        "rescued",
        "trapped",
        "unknown",
        "last_updated"
    ]
].copy()

display_df.columns = [
    "Hydropower Project",
    "Capacity",
    "Status",
    "Rescued",
    "Trapped / Awaiting",
    "Unknown / Missing",
    "Last Updated"
]


def highlight_selected(row):
    if row["Hydropower Project"] == selected_project:
        return ["background-color: #dbeafe; font-weight: bold;"] * len(row)
    return [""] * len(row)


st.dataframe(
    display_df.style.apply(highlight_selected, axis=1),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(
    "⚠️ This dashboard is intended for situational awareness. "
    "Personnel figures should be updated only from verified official or field sources."
)
