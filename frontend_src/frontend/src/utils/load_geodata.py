import json
import os
from typing import Dict, List

import fiona
import streamlit as st
from shapely.geometry import mapping, shape

countries_mapping = {
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Syrian Arab Republic": "Syria",
    "Iran (Islamic Republic of)": "Iran",
}


def _convert_geometries_to_geojson(polygon, tolerance: float, return_extreme_points: bool):
    """
    Converts a polygon geometry to GeoJSON format with optional simplification and extraction of extreme points.

    Parameters:
    polygon (Polygon): The polygon geometry to convert.
    tolerance (float): The tolerance level for simplifying the polygon.
    return_extreme_points (bool): Whether to return the extreme points of the polygon.

    Returns:
    dict: A dictionary containing the GeoJSON geometry and optionally the extreme points.

    Operation:
    1. Converts the input polygon to a shapely shape.
    2. Simplifies the polygon geometry based on the provided tolerance.
    3. Converts the simplified geometry to GeoJSON format.
    4. If `return_extreme_points` is True, calculates the bounding box of the
       original polygon and adds the extreme points to the returned data.
    5. Returns a dictionary with the GeoJSON geometry and optionally the extreme points.
    """
    preprocessed_val = shape(polygon)

    processed_polygon = mapping(preprocessed_val.simplify(tolerance=tolerance, preserve_topology=True))
    returned_data = {"geometry": processed_polygon}

    if return_extreme_points:
        # get extreme points
        minx, miny, maxx, maxy = preprocessed_val.bounds
        extreme_points = {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}
        returned_data["extreme_points"] = extreme_points

    return returned_data


################# LOAD ADM0 POLYGONS ####################  # noqa


@st.cache_data
def _load_gpkg_adm0(file_path: str):
    """
    Loads polygons from a GeoPackage file and returns a GeoJSON object.

    Parameters:
    file_path (str): The path to the GeoPackage file.

    Returns:
    dict: A GeoJSON object containing the filtered features.

    Operation:
    1. Initializes an empty GeoJSON object.
    2. Opens the GeoPackage file using Fiona and iterates over the features.
    3. Filters features based on the 'adm0_name' property to match countries stored in the Streamlit session state.
    4. Converts the geometries of the filtered features to GeoJSON format with optional simplification.
    5. Constructs a GeoJSON feature for each filtered feature with the necessary properties and geometry.
    6. Adds the constructed features to the GeoJSON object.
    7. Returns the completed GeoJSON object.
    """

    # Note for Admin 0 gpkg file, get it from here: https://fieldmaps.io/data/adm0

    geojson_obj = {"type": "FeatureCollection", "features": []}

    # Open GeoPackage file and iterate over features to filter them
    with fiona.open(file_path, vfs="{}".format(file_path), enabled_drivers="GeoJSON") as src:
        for feature in src:
            # Check if the feature satisfies the SQL filter condition for rows
            adm0_name = feature["properties"]["adm0_name"]
            adm0_name = countries_mapping.get(adm0_name, adm0_name)

            if adm0_name in st.session_state["countries"]:
                # Filter columns based on the SQL query

                filtered_properties = {"name": adm0_name}
                processed_data = _convert_geometries_to_geojson(
                    feature["geometry"], tolerance=0.1, return_extreme_points=True
                )

                filtered_feature = {
                    "type": feature["id"],
                    "properties": filtered_properties,
                    "geometry": processed_data["geometry"],
                }

                geojson_obj["features"].append(filtered_feature)
    return geojson_obj


@st.cache_data
def _load_polygons_adm0():
    """
    Loads and returns GeoJSON data for administrative level 0 polygons (countries).

    Returns:
    dict: GeoJSON data for administrative level 0 polygons.

    Operation:
    1. Constructs paths for processed and loaded data files.
    2. Checks if the GeoJSON file for administrative level 0 polygons exists
       in the processed data directory.
    3. If the file does not exist, loads polygons from a GeoPackage file,
       converts them to GeoJSON, and saves the GeoJSON file.
    4. If the file exists, loads the GeoJSON data from the file.
    5. Returns the loaded GeoJSON data.
    """

    adm0_processed_data = os.path.join(st.session_state["geolocation_processed_data_path"], "adm0_polygons")
    # os.makedirs(adm0_processed_data, exist_ok=True)

    loaded_data_path = os.path.join(adm0_processed_data, "adm0_polygons.geojson")

    if not os.path.exists(loaded_data_path):
        geojson_countries_file = _load_gpkg_adm0(
            os.path.join(st.session_state["original_polygons_data_path"], "adm0_polygons.gpkg")
        )
        # save geojson
        with open(loaded_data_path, "w") as f:
            json.dump(geojson_countries_file, f)

    else:
        # load geojson file
        with open(loaded_data_path, "r") as f:
            geojson_countries_file = json.load(f)

    return geojson_countries_file


################# LOAD ADM1 POLYGONS ####################  # noqa


def _update_min_max(extreme_points: Dict[str, float], new_extreme_points: Dict[str, float]):
    extreme_points = {
        "minx": (
            min(extreme_points["minx"], new_extreme_points["minx"])
            if extreme_points["minx"] is not None
            else new_extreme_points["minx"]
        ),
        "miny": (
            min(extreme_points["miny"], new_extreme_points["miny"])
            if extreme_points["miny"] is not None
            else new_extreme_points["miny"]
        ),
        "maxx": (
            max(extreme_points["maxx"], new_extreme_points["maxx"])
            if extreme_points["maxx"] is not None
            else new_extreme_points["maxx"]
        ),
        "maxy": (
            max(extreme_points["maxy"], new_extreme_points["maxy"])
            if extreme_points["maxy"] is not None
            else new_extreme_points["maxy"]
        ),
    }

    return extreme_points


def _load_gpkg_adm1(file_path: str, used_countries: List[str]):  # Not mentioning 'geometry' in imported_columns
    """
    Loads administrative level 1 polygons (regions) from a GeoPackage file and returns GeoJSON data.

    Parameters:
    file_path (str): The path to the GeoPackage file.
    used_countries (List[str]): List of countries to filter the regions.

    Returns:
    tuple: A tuple containing filtered GeoJSON features and extreme points dictionary.

    Operation:
    1. Initializes an empty dictionary for extreme points.
    2. Initializes an empty GeoJSON feature collection.
    3. Opens the GeoPackage file using Fiona and iterates over features.
    4. Filters features based on the 'adm0_name' property to match countries in 'used_countries'.
    5. Converts the geometries of filtered features to GeoJSON format with extreme points extraction.
    6. Constructs GeoJSON features for each filtered feature with necessary properties and geometry.
    7. Updates extreme points based on the extracted points of each geometry.
    8. Returns a tuple containing filtered GeoJSON features and the updated extreme points dictionary.
    """

    extreme_points = {"minx": None, "miny": None, "maxx": None, "maxy": None}

    # Open GeoPackage file and iterate over features to filter them
    filtered_features = {"type": "FeatureCollection", "features": []}
    with fiona.open(file_path, vfs="{}".format(file_path), enabled_drivers="GeoJSON") as src:
        for feature in src:
            # Check if the feature satisfies the SQL filter condition for rows
            country_official_name = feature["properties"]["adm0_name"]

            if country_official_name in used_countries:
                # Filter columns based on the SQL query
                filtered_properties = {"name": feature["properties"]["adm1_name"]}

                geojson_geometry = _convert_geometries_to_geojson(
                    feature["geometry"], tolerance=0.05, return_extreme_points=True
                )

                filtered_feature = {
                    "type": feature["id"],
                    "properties": filtered_properties,
                    "geometry": geojson_geometry["geometry"],
                }

                # update extreme_points
                extreme_points = _update_min_max(extreme_points, geojson_geometry["extreme_points"])

                filtered_features["features"].append(filtered_feature)

    return filtered_features, extreme_points


def _load_polygons_adm1(treated_country: str, geodata_countries: List[str]):
    """
    Loads administrative level 1 polygons (regions) from a GeoPackage file and returns GeoJSON data.

    Parameters:
    treated_country (str): The country for which polygons are loaded.
    geodata_countries (List[str]): List of countries to filter the regions.

    Returns:
    tuple: A tuple containing GeoJSON data for administrative level 1 polygons and extreme points.

    Operation:
    1. Constructs paths for processed and loaded data files specific to administrative level 1 polygons.
    2. Checks if the GeoJSON file for the specified country exists in the processed data directory.
    3. If the file does not exist, loads polygons from a GeoPackage file,
       converts them to GeoJSON, and saves the GeoJSON file.
    4. If the file exists, loads the GeoJSON data from the file.
    5. Returns a tuple containing GeoJSON data for administrative level 1 polygons and extreme points.
    """

    adm1_processed_data = os.path.join(st.session_state["geolocation_processed_data_path"], "adm1_polygons")
    os.makedirs(adm1_processed_data, exist_ok=True)

    loaded_data_path = os.path.join(adm1_processed_data, f"{treated_country.replace('/', '-')}.geojson")

    if not os.path.exists(loaded_data_path):
        geojson_country_file, extreme_points = _load_gpkg_adm1(
            os.path.join(st.session_state["original_polygons_data_path"], "adm1_polygons.gpkg"),
            geodata_countries,
        )
        # save geojson
        geojson_data = {
            "geojson": geojson_country_file,
            "extreme_points": extreme_points,
        }
        with open(loaded_data_path, "w") as f:
            json.dump(geojson_data, f)

    else:
        # load geojson file
        with open(loaded_data_path, "r") as f:
            geojson_data = json.load(f)

            geojson_country_file = geojson_data["geojson"]
            extreme_points = geojson_data["extreme_points"]

    return geojson_country_file, extreme_points
