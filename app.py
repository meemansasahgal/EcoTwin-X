# ============================================================
# app.py
# EcoTwin-X
# ============================================================

import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from pathlib import Path
import numpy as np


# ============================================================
# ROBUST PROJECT FILE FINDER
# ============================================================

APP_DIR = Path(__file__).resolve().parent


def find_file(filename):
    """
    Finds a file automatically in the deployed project.

    It checks:
    1. Same folder as app.py
    2. data/
    3. output/
    4. frontend/
    5. backend/
    6. Parent folders
    7. Recursive subfolders
    """

    search_locations = [
        APP_DIR,
        APP_DIR / "data",
        APP_DIR / "output",
        APP_DIR / "frontend",
        APP_DIR / "backend",
        APP_DIR.parent,
        APP_DIR.parent / "data",
        APP_DIR.parent / "output",
        APP_DIR.parent / "frontend",
        APP_DIR.parent / "backend",
    ]

    # --------------------------------------------------------
    # Check common locations
    # --------------------------------------------------------

    for folder in search_locations:

        try:
            file_path = folder / filename

            if file_path.is_file():
                return file_path

        except Exception:
            pass

    # --------------------------------------------------------
    # Recursive search
    # --------------------------------------------------------

    search_roots = [
        APP_DIR,
        APP_DIR.parent
    ]

    for root in search_roots:

        try:

            if root.exists():

                matches = root.rglob(filename)

                for match in matches:

                    if match.is_file():
                        return match

        except Exception:
            pass

    return None


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(filename):

    file_path = find_file(filename)

    if file_path is None:

        st.warning(
            f"File not found in the deployed project: {filename}"
        )

        return None

    try:

        return pd.read_csv(file_path)

    except pd.errors.EmptyDataError:

        st.info(
            f"{filename} is empty."
        )

        return None

    except Exception as e:

        st.error(
            f"Could not load {filename}: {e}"
        )

        return None


# ============================================================
# LOAD GEOJSON
# ============================================================

def load_geojson(filename):

    file_path = find_file(filename)

    if file_path is None:

        st.warning(
            f"File not found in the deployed project: {filename}"
        )

        return None

    try:

        gdf = gpd.read_file(file_path)

        return gdf

    except Exception as e:

        st.error(
            f"Could not load {filename}: {e}"
        )

        return None


# ============================================================
# DISPLAY GEOJSON MAP
# ============================================================

def show_geo_map(gdf, title="Map"):

    if gdf is None or gdf.empty:

        st.info(
            "No geographic data available."
        )

        return

    try:

        map_gdf = gdf.copy()

        # ----------------------------------------------------
        # CRS
        # ----------------------------------------------------

        if map_gdf.crs is not None:

            map_gdf = map_gdf.to_crs(
                epsg=4326
            )

        # ----------------------------------------------------
        # Useful columns
        # ----------------------------------------------------

        useful_columns = []

        for column in [
            "shade_frac",
            "pollution_proxy",
            "highway",
            "road_type",
            "name"
        ]:

            if column in map_gdf.columns:

                useful_columns.append(
                    column
                )

        if useful_columns:

            map_gdf = map_gdf[
                useful_columns + ["geometry"]
            ]

        else:

            map_gdf = map_gdf[
                ["geometry"]
            ]

        # ----------------------------------------------------
        # Clean values for JSON
        # ----------------------------------------------------

        def clean_value(value):

            if isinstance(
                value,
                np.ndarray
            ):

                return value.tolist()

            if isinstance(
                value,
                np.generic
            ):

                return value.item()

            try:

                if pd.isna(value):

                    return None

            except Exception:

                pass

            return value

        for column in map_gdf.columns:

            if column != "geometry":

                map_gdf[column] = (
                    map_gdf[column]
                    .apply(clean_value)
                )

        # ----------------------------------------------------
        # Remove invalid geometries
        # ----------------------------------------------------

        map_gdf = map_gdf[
            map_gdf.geometry.notna()
        ].copy()

        if map_gdf.empty:

            st.info(
                "No valid geographic geometries available."
            )

            return

        # ----------------------------------------------------
        # Map center
        # ----------------------------------------------------

        center_point = (
            map_gdf.geometry
            .union_all()
            .centroid
        )

        center_lat = center_point.y
        center_lon = center_point.x

        # ----------------------------------------------------
        # Create map
        # ----------------------------------------------------

        m = folium.Map(
            location=[
                center_lat,
                center_lon
            ],
            zoom_start=15,
            tiles="OpenStreetMap"
        )

        # ----------------------------------------------------
        # Tooltip
        # ----------------------------------------------------

        tooltip_fields = []
        tooltip_aliases = []

        if "shade_frac" in map_gdf.columns:

            tooltip_fields.append(
                "shade_frac"
            )

            tooltip_aliases.append(
                "Shade Fraction:"
            )

        if "pollution_proxy" in map_gdf.columns:

            tooltip_fields.append(
                "pollution_proxy"
            )

            tooltip_aliases.append(
                "Pollution Proxy:"
            )

        if "highway" in map_gdf.columns:

            tooltip_fields.append(
                "highway"
            )

            tooltip_aliases.append(
                "Road Type:"
            )

        # ----------------------------------------------------
        # Add GeoJSON
        # ----------------------------------------------------

        folium.GeoJson(
            map_gdf.to_json(),
            name=title,
            tooltip=(
                folium.GeoJsonTooltip(
                    fields=tooltip_fields,
                    aliases=tooltip_aliases,
                    localize=True
                )
                if tooltip_fields
                else None
            )
        ).add_to(m)

        folium.LayerControl().add_to(m)

        st_folium(
            m,
            width=None,
            height=600
        )

    except Exception as e:

        st.error(
            f"Could not display {title}: {e}"
        )


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EcoTwin-X",
    page_icon="🌿",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title(
    "🌿 EcoTwin-X"
)

st.caption(
    "HeatStop & CoolPath Environmental Intervention Twin"
)

st.markdown(
    """
    **Simulating environmental interventions before they are built
    to reduce heat and pollution exposure for vulnerable urban populations.**
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "EcoTwin-X"
)

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Heat & Pollution",
        "Equity & Exposure",
        "CoolPath",
        "HeatStop Planner",
        "Intervention Twin",
        "Environmental Negotiator",
        "Validation"
    ]
)


# ============================================================
# PAGE — HEAT & POLLUTION
# ============================================================

if page == "Heat & Pollution":

    st.header(
        "🌡️ Heat & Pollution Layer"
    )

    st.markdown(
        """
        This page shows the environmental conditions
        of the road network.

        **Heat layer:** based on road shade availability.

        **Pollution layer:** based on road hierarchy
        and pollution proxy values.
        """
    )

    # --------------------------------------------------------
    # HEAT
    # --------------------------------------------------------

    st.subheader(
        "🌤️ Street Heat & Shade"
    )

    shade_gdf = load_geojson(
        "roads_with_shade_9am.geojson"
    )

    if shade_gdf is not None:

        st.success(
            f"{len(shade_gdf):,} road segments available for 9 AM."
        )

        show_geo_map(
            shade_gdf,
            "Street Heat & Shade"
        )

    # --------------------------------------------------------
    # POLLUTION
    # --------------------------------------------------------

    st.subheader(
        "🌫️ Pollution Layer"
    )

    pollution_gdf = load_geojson(
        "roads_with_pollution.geojson"
    )

    if pollution_gdf is not None:

        st.success(
            f"{len(pollution_gdf):,} pollution road segments available."
        )

        show_geo_map(
            pollution_gdf,
            "Pollution Layer"
        )


# ============================================================
# NOTE
# ============================================================
#
# KEEP THE REST OF YOUR EXISTING PAGES BELOW THIS SECTION:
#
# Overview
# Equity & Exposure
# CoolPath
# HeatStop Planner
# Intervention Twin
# Environmental Negotiator
# Validation
#
# The important change is that ALL files are now loaded through:
#
#     find_file()
#
# Therefore you should NOT use:
#
#     DATA_DIR / filename
#
# or:
#
#     OUTPUT_DIR / filename
#
# anywhere else in the application.
#
# ============================================================
