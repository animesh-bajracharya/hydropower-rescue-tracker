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
# INITIAL HYDROPOWER DATA
# ============================================================
#
# Tuple structure:
#
# (
#     name,
#     latitude,
#     longitude,
#     status,
#     capacity,
#     rescued,
#     trapped,
#     unknown
# )
#
# Use 0 instead of None for personnel counts because Streamlit
# number_input() requires an integer.
#
# If you don't know a figure, "0" currently means:
# "No confirmed number entered yet."
#
# It does NOT necessarily mean zero people.
# ============================================================

initial_data = [
    # ---------------- RASUWA ----------------

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
        "Upper Trishuli-1 (UT-1)",
        28.101250,
        85.255972,
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
        "Chilime Hydropower",
        28.169722,
        85.319583,
        "Operational / Severely Flood Damaged",
        "22 MW",
        0,
        8,
        0
    ),

    # ---------------- NUWAKOT ----------------

    (
        "Upper Trishuli-3A",
        28.046528,
        85.199167,
        "Operational / Flood Damaged / Staff Rescue",
        "60 MW",
        0,
        0,
        0
    ),

    (
        "Upper Trishuli-3B",
        28.004583,
        85.185000,
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
        27.946389,
        85.166111,
        "Operational / Flood Damaged",
        "24 MW",
        0,
        0,
        0
    ),

    (
        "Devighat Hydropower",
        27.902222,
        85.138889,
        "Operational / Flood Affected",
        "14.1 MW",
        0,
        0,
        0
    ),
]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = sqlite3.connect(DB_FILE)

    c = conn.cursor()

    # Create database table
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
    # Insert initial project data
    # --------------------------------------------------------

    for item in initial_data:

        c.execute("""
            INSERT OR IGNORE INTO projects
            (
                name,
                lat,
                lon,
                status,
                capacity,
                rescued,
                trapped,
                unknown
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    conn.commit()

    conn.close()


# Initialize database
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

    # --------------------------------------------------------
    # Protect the application against NULL values
    # --------------------------------------------------------

    numeric_columns = [
        "rescued",
        "trapped",
        "unknown"
    ]

    for column in numeric_columns:

        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )

    return df


def update_record(
    project_id,
    rescued,
    trapped,
    unknown,
    status
):

    conn = sqlite3.connect(DB_FILE)

    c = conn.cursor()

    c.execute("""
        UPDATE projects

        SET
            rescued = ?,
            trapped = ?,
            unknown = ?,
            status = ?,
            last_updated = CURRENT_TIMESTAMP

        WHERE id = ?
    """, (
        int(rescued),
        int(trapped),
        int(unknown),
        status,
        int(project_id)
    ))

    conn.commit()

    conn.close()


# ============================================================
# HEADER
# ============================================================

st.title(
    "🚨 Trishuli Basin Hydropower Rescue & Flood Impact Tracker"
)

st.markdown(
    """
    **Real-time monitoring and situational reporting dashboard**
    for hydropower projects affected by the Trishuli River flood
    disaster.
    """
)


# ============================================================
# LOAD DATABASE
# ============================================================

df = get_data()


# ============================================================
# METRIC SUMMARY
# ============================================================

total_rescued = int(df["rescued"].sum())

total_trapped = int(df["trapped"].sum())

total_unknown = int(df["unknown"].sum())

total_projects = len(df)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "👷 Total Rescued",
    f"{total_rescued:,}",
    delta="Live"
)


col2.metric(
    "🚨 Awaiting Rescue / Trapped",
    f"{total_trapped:,}",
    delta_color="inverse"
)


col3.metric(
    "❓ Status Unknown / Missing",
    f"{total_unknown:,}",
    delta_color="inverse"
)


col4.metric(
    "🏗️ Monitored Hydropower Sites",
    total_projects
)


st.divider()


# ============================================================
# MAP + UPDATE PANEL
# ============================================================

left_col, right_col = st.columns(
    [2, 1]
)


# ============================================================
# MAP
# ============================================================

with left_col:

    st.subheader(
        "🗺️ Hydropower Locations & Rescue Map"
    )

    # --------------------------------------------------------
    # Base map
    # --------------------------------------------------------

    m = folium.Map(
        location=[
            28.0800,
            85.2500
        ],
        zoom_start=10,
        tiles="OpenStreetMap"
    )

    # --------------------------------------------------------
    # Google Satellite Layer
    # --------------------------------------------------------

    folium.TileLayer(
        tiles=(
            "https://mt1.google.com/vt/"
            "lyrs=y&x={x}&y={y}&z={z}"
        ),
        attr="Google",
        name="Google Satellite",
        overlay=False,
        control=True
    ).add_to(m)

    # --------------------------------------------------------
    # Project markers
    # --------------------------------------------------------

    for _, row in df.iterrows():

        # ----------------------------------------------
        # Skip projects without coordinates
        # ----------------------------------------------

        if pd.isna(row["lat"]) or pd.isna(row["lon"]):

            continue

        # ----------------------------------------------
        # Safely convert values to integers
        # ----------------------------------------------

        rescued = int(row["rescued"])

        trapped = int(row["trapped"])

        unknown = int(row["unknown"])

        # ----------------------------------------------
        # Marker color
        # ----------------------------------------------

        if trapped > 0:

            marker_color = "red"

        elif unknown > 0:

            marker_color = "orange"

        elif rescued > 0:

            marker_color = "green"

        else:

            marker_color = "blue"

        # ----------------------------------------------
        # Popup
        # ----------------------------------------------

        popup_html = f"""
        <div
            style="
                font-family: Arial;
                width: 240px;
            "
        >

            <h4>
                <b>{row['name']}</b>
            </h4>

            <b>Status:</b>
            {row['status']}
            <br><br>

            <b>Capacity:</b>
            {row['capacity']}
            <br>

            <hr>

            <b>👷 Rescued:</b>
            {rescued}
            <br>

            <b>🚨 Trapped / Awaiting:</b>
            {trapped}
            <br>

            <b>❓ Unknown / Missing:</b>
            {unknown}

            <hr>

            <small>
                Last updated:
                {row['last_updated']}
            </small>

        </div>
        """

        # ----------------------------------------------
        # Marker
        # ----------------------------------------------

        folium.Marker(
            location=[
                float(row["lat"]),
                float(row["lon"])
            ],

            popup=folium.Popup(
                popup_html,
                max_width=350
            ),

            tooltip=row["name"],

            icon=folium.Icon(
                color=marker_color,
                icon="info-sign"
            )

        ).add_to(m)

    # --------------------------------------------------------
    # Layer control
    # --------------------------------------------------------

    folium.LayerControl().add_to(m)

    # --------------------------------------------------------
    # Display map
    # --------------------------------------------------------

    st_folium(
        m,
        width="100%",
        height=600
    )


# ============================================================
# UPDATE PANEL
# ============================================================

with right_col:

    st.subheader(
        "✏️ Update Worker Status"
    )

    st.caption(
        """
        Update personnel information as verified
        field information becomes available.
        """
    )

    # --------------------------------------------------------
    # Project selection
    # --------------------------------------------------------

    selected_project = st.selectbox(
        "Select Project Site",
        df["name"].tolist()
    )

    # --------------------------------------------------------
    # Get selected project
    # --------------------------------------------------------

    proj_data = df[
        df["name"] == selected_project
    ].iloc[0]

    # --------------------------------------------------------
    # Update form
    # --------------------------------------------------------

    with st.form(
        "update_form",
        clear_on_submit=False
    ):

        rescued = st.number_input(
            "👷 Workers Rescued",
            min_value=0,
            value=int(proj_data["rescued"]),
            step=1
        )

        trapped = st.number_input(
            "🚨 Trapped / Awaiting Rescue",
            min_value=0,
            value=int(proj_data["trapped"]),
            step=1
        )

        unknown = st.number_input(
            "❓ Status Unknown / Missing",
            min_value=0,
            value=int(proj_data["unknown"]),
            step=1
        )

        status = st.text_input(
            "🏗️ Project Operational / Damage Status",
            value=str(proj_data["status"])
        )

        submit = st.form_submit_button(
            "💾 Update Project Data"
        )

        if submit:

            update_record(
                proj_data["id"],
                rescued,
                trapped,
                unknown,
                status
            )

            st.success(
                f"Updated {selected_project} successfully!"
            )

            st.rerun()


# ============================================================
# DATA TABLE
# ============================================================

st.subheader(
    "📋 Complete Hydropower Disaster Overview"
)


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


# Rename columns for the dashboard

display_df.columns = [
    "Hydropower Project",
    "Capacity",
    "Status",
    "Rescued",
    "Trapped / Awaiting",
    "Unknown / Missing",
    "Last Updated"
]


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "⚠️ This dashboard is intended for situational awareness. "
    "Personnel figures should be updated only from verified "
    "official or field sources."
)
