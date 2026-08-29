import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Trishuli Hydropower Rescue Tracker",
    page_icon="🚨",
    layout="wide"
)


# ============================================================
# SUPABASE CONNECTION INITIALIZATION
# ============================================================

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()


# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================

def get_data() -> pd.DataFrame:
    # Fetch all records from the projects table sorted by ID
    response = supabase.table("projects").select("*").order("id").execute()
    
    if not response.data:
        return pd.DataFrame(columns=[
            "id", "name", "lat", "lon", "status", "capacity",
            "rescued", "trapped", "unknown", "last_updated"
        ])
        
    df = pd.DataFrame(response.data)

    numeric_columns = ["rescued", "trapped", "unknown"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    return df


def update_record(project_id: int, name: str, rescued: int, trapped: int, unknown: int, status: str):
    supabase.table("projects").update({
        "name": name,
        "rescued": int(rescued),
        "trapped": int(trapped),
        "unknown": int(unknown),
        "status": status,
        "last_updated": "NOW()"
    }).eq("id", project_id).execute()


def add_new_project(name: str, lat: float, lon: float, status: str, capacity: str, rescued: int, trapped: int, unknown: int):
    try:
        data = {
            "name": name,
            "lat": lat if lat != 0.0 else None,
            "lon": lon if lon != 0.0 else None,
            "status": status,
            "capacity": capacity,
            "rescued": int(rescued),
            "trapped": int(trapped),
            "unknown": int(unknown)
        }
        supabase.table("projects").insert(data).execute()
        return True, f"Successfully added {name}!"
    except Exception as e:
        return False, f"Failed to add project: {str(e)}"


# ============================================================
# LOAD DATA
# ============================================================

df = get_data()


# ============================================================
# HEADER
# ============================================================

st.title("🚨 Trishuli Basin Hydropower Rescue & Flood Impact Tracker")
st.markdown("**Real-time monitoring and situational reporting dashboard** backed by cloud database persistence.")


# ============================================================
# SUMMARY METRICS
# ============================================================

if not df.empty:
    total_rescued = int(df["rescued"].sum())
    total_trapped = int(df["trapped"].sum())
    total_unknown = int(df["unknown"].sum())
    total_projects = len(df)
else:
    total_rescued = total_trapped = total_unknown = total_projects = 0

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

if not df.empty:
    selected_project = st.selectbox(
        "Select a project to highlight on the map",
        df["name"].tolist(),
        label_visibility="collapsed"
    )
    selected_data = df[df["name"] == selected_project].iloc[0]
else:
    st.info("No projects available in the database yet.")
    st.stop()


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

    m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="OpenStreetMap")

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
                radius=300,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.12,
                weight=3
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

    # ----------------------------------------------------
    # MAP LEGEND OVERLAY
    # ----------------------------------------------------
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 30px; 
        left: 30px; 
        width: 220px; 
        z-index: 9999; 
        background-color: white; 
        padding: 12px 15px; 
        border-radius: 8px; 
        box-shadow: 0 0 12px rgba(0,0,0,0.3);
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.6;
    ">
        <b style="font-size: 13px;">🚨 Map Status Legend</b><hr style="margin: 5px 0;">
        <div><span style="background: #d9534f; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span> <b>Trapped / Awaiting</b></div>
        <div><span style="background: #f0ad4e; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span> <b>Status Unknown</b></div>
        <div><span style="background: #5cb85c; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span> <b>Rescued / Safe</b></div>
        <div><span style="background: #0275d8; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span> <b>Normal / Monitored</b></div>
        <div><span style="border: 2px solid #0275d8; background: rgba(2, 117, 216, 0.2); width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 6px;"></span> <b>Selected Site Halo</b></div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width="100%", height=600)


# ============================================================
# UPDATE & ENTRY PANEL (ADMIN ACCESS ONLY)
# ============================================================

with right_col:
    st.subheader("🔒 Admin Control Panel")

    # Password input field
    admin_input = st.text_input(
        "Enter Admin Key to unlock editing",
        type="password",
        help="Only authorized personnel can update site statuses."
    )

    # Check if input matches secret key
    if admin_input == st.secrets.get("ADMIN_PASSWORD"):
        st.success("🔓 Authenticated as Admin")

        # ----------------------------------------------------
        # EDIT SELECTED SITE FORM
        # ----------------------------------------------------
        st.markdown("### ✏️ Edit Selected Site")
        with st.form("update_form", clear_on_submit=False):
            name = st.text_input("📍 Project Name", value=str(selected_data["name"]))
            rescued = st.number_input("👷 Workers Rescued", min_value=0, value=int(selected_data["rescued"]), step=1)
            trapped = st.number_input("🚨 Trapped / Awaiting Rescue", min_value=0, value=int(selected_data["trapped"]), step=1)
            unknown = st.number_input("❓ Status Unknown / Missing", min_value=0, value=int(selected_data["unknown"]), step=1)
            status = st.text_input("🏗️ Project Operational / Damage Status", value=str(selected_data["status"]))

            submit = st.form_submit_button("💾 Save Project Updates")

            if submit:
                update_record(int(selected_data["id"]), name, rescued, trapped, unknown, status)
                st.success(f"Updated {name} successfully!")
                st.rerun()

        st.divider()

        # ----------------------------------------------------
        # ADD NEW SITE FORM
        # ----------------------------------------------------
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
                            new_name.strip(), new_lat, new_lon, new_status,
                            new_capacity, new_rescued, new_trapped, new_unknown
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    elif admin_input:
        st.error("Incorrect Admin Key.")
    else:
        st.info("ℹ️ Read-only mode. Enter the Admin Key above to edit data or register new sites.")


# ============================================================
# DATA TABLE
# ============================================================

st.subheader("📋 Complete Hydropower Disaster Overview")

display_df = df[["name", "capacity", "status", "rescued", "trapped", "unknown", "last_updated"]].copy()
display_df.columns = [
    "Hydropower Project", "Capacity", "Status", "Rescued",
    "Trapped / Awaiting", "Unknown / Missing", "Last Updated"
]

st.dataframe(display_df, use_container_width=True, hide_index=True)
