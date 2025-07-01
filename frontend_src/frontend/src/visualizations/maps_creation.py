from typing import Dict, List, Literal

import pandas as pd
import pydeck as pdk
import streamlit as st

from frontend.src.utils.load_geodata import _load_polygons_adm1

lat_range = 180
lon_range = 360


def _rgb_to_hex(rgb):
    # rgb to hex
    return "#{0:02x}{1:02x}{2:02x}".format(*rgb)


default_filling_color = [211, 211, 211]

severity_mapping_tag_name_to_color_main_countries = {
    "No Information": default_filling_color,
    "Very Low": [198, 191, 209],
    "Low": [174, 164, 188],
    "Medium": [152, 141, 171],
    "High": [134, 120, 156],
    "Very High": [108, 104, 119],
}


def _get_mean(data: List[float]):
    return sum(data) / len(data)


def _display_legend(mapping_dict: Dict[str, List[int]]):
    # Generate HTML for the legend
    legend_html = (
        "<div style='display: flex; flex-direction: row; align-items: center; justify-content: flex-end; flex-wrap: wrap;'>"  # noqa
    )
    for tag_name, color in mapping_dict.items():
        hex_color = _rgb_to_hex(color)
        # Increased margin-right for more spacing between items
        if tag_name != "No Information":
            shown_tag = f"{tag_name} Severity"
        else:
            shown_tag = tag_name
        legend_html += f"<div style='display: flex; align-items: center; margin-right: 30px;'><div style='width: 12px; height: 12px; background: {hex_color}; margin-right: 5px;'></div>{shown_tag}</div>"  # noqa

    legend_html += "</div>"

    # Display in Streamlit
    st.markdown(legend_html, unsafe_allow_html=True)


def adjust_view_state(view_state, min_lat, max_lat, min_lon, max_lon):
    # Ensure the latitude is within bounds
    if view_state.latitude < min_lat:
        view_state.latitude = min_lat
    elif view_state.latitude > max_lat:
        view_state.latitude = max_lat

    # Ensure the longitude is within bounds
    # This simple check might not handle cases where the map wraps around the globe
    if view_state.longitude < min_lon:
        view_state.longitude = min_lon
    elif view_state.longitude > max_lon:
        view_state.longitude = max_lon

    return view_state


def _create_polygons_map_placeholder_pdk(
    geojson_country_polygons,
    latitude_range=[-90, 90],
    longitude_range=[-180, 180],
    display_type=Literal["Country", "Region"],
):
    """
    Creates and displays a PyDeck map with GeoJSON polygons.

    Parameters:
    geojson_country_polygons (dict): GeoJSON data for the country polygons.
    latitude_range (list, optional): Latitude range for the map. Defaults to [-90, 90].
    longitude_range (list, optional): Longitude range for the map. Defaults to [-180, 180].
    display_type (Literal["Country", "Region"]): Type of display, either 'Country' or 'Region'.

    Returns:
    None

    Operation:
    1. Creates a PyDeck `GeoJsonLayer` with the provided GeoJSON data.
    2. Sets the opacity, stroke, fill color, line color, and other properties for the layer.
    3. Calculates the center latitude and longitude for the initial view state.
    4. Determines the zoom factor based on the display type.
    5. Configures the PyDeck `ViewState` for the viewport with appropriate zoom levels.
    6. Sets the height of the displayed map based on the display type.
    7. Renders the map using Streamlit's `st.pydeck_chart`.
    8. Displays a legend for the map.
    """
    with st.spinner("Loading the map..."):
        # Create a PyDeck layer
        layer = pdk.Layer(
            "GeoJsonLayer",
            geojson_country_polygons,
            opacity=0.4,
            stroked=True,  # Enable stroking to draw borders
            stroked_scale=3,  # Adjust the border width
            filled=True,
            extruded=False,
            get_fill_color="properties.fill_color",
            get_line_color="properties.fill_color",  # Use a distinct or darker color for borders
            get_line_width=0.3,  # You can adjust border width in properties
            line_width_min_pixels=0.3,  # Ensures visibility of borders at all zoom levels
            pickable=True,
            # custom legend depending on the mouse hover
            auto_highlight=True,
            # add legend to the highlighted area
            # get_position="coordinates",
            # highlight_color=[0, 0, 0],
            # show name of the country on hover
        )

        shown_lat = _get_mean(latitude_range)
        shown_lon = _get_mean(longitude_range)

        zoom_factor = 0.35 if display_type == "Country" else 0.5

        # select zoom value only on the selected area
        zoom = zoom_factor * min(
            lat_range / (latitude_range[1] - latitude_range[0]),
            lon_range / (longitude_range[1] - longitude_range[0]),
        )

        # Set the viewport location
        view_state = pdk.ViewState(
            latitude=shown_lat,
            longitude=shown_lon,
            min_zoom=zoom / 2,
            zoom=1,
            max_zoom=zoom * 10,
        )

        displayed_height = 600 if display_type == "Country" else 250
        # Render the map
        deck = pdk.Deck(
            layers=[layer],  # Single layer for both polygons and borders
            initial_view_state=view_state,
            map_style="light",
            tooltip={
                "text": ("{legend}" if display_type == "Country" else "TEXT HERE: {name}\nTag: {legend_name}"),
                "style": {"backgroundColor": "white", "color": "black"},
            },
            height=displayed_height,
        )

    with st.empty():
        st.pydeck_chart(deck, use_container_width=True)

    _display_legend(severity_mapping_tag_name_to_color_main_countries)


def _create_points_map_placeholder_pdk(
    geojson_country_polygons,
    displayed_df: pd.DataFrame,
    latitude_range=[-90, 90],
    longitude_range=[-180, 180],
    display_type=Literal["Country", "Region"],
):
    """
    Creates and displays a PyDeck map with GeoJSON polygons and scatter plot points.

    Parameters:
    geojson_country_polygons (dict): GeoJSON data for the country polygons.
    displayed_df (pd.DataFrame): DataFrame containing the points to be displayed.
    latitude_range (list, optional): Latitude range for the map. Defaults to [-90, 90].
    longitude_range (list, optional): Longitude range for the map. Defaults to [-180, 180].
    display_type (Literal["Country", "Region"]): Type of display, either 'Country' or 'Region'.

    Returns:
    None

    Operation:
    1. Creates a PyDeck `GeoJsonLayer` with the provided GeoJSON data for country borders.
    2. Sets properties for the layer such as opacity, stroke, fill color, and border width.
    3. Creates a PyDeck `ScatterplotLayer` with the data points from the DataFrame.
    4. Calculates the center latitude and longitude for the initial view state.
    5. Determines the zoom factor based on the display type.
    6. Configures the PyDeck `ViewState` for the viewport with appropriate zoom levels.
    7. Sets the height of the displayed map based on the display type.
    8. Renders the map using Streamlit's `st.pydeck_chart`.
    """
    with st.spinner("Loading the map..."):
        # Create a PyDeck layer
        layer0 = pdk.Layer(
            "GeoJsonLayer",
            geojson_country_polygons,
            opacity=0.4,
            stroked=True,  # Enable stroking to draw borders
            stroked_scale=3,  # Adjust the border width
            filled=True,
            extruded=False,
            get_fill_color="properties.fill_color",
            get_line_color="properties.line_color",  # Use a distinct or darker color for borders
            get_line_width=0.5,  # You can adjust border width in properties
            line_width_min_pixels=0.5,  # Ensures visibility of borders at all zoom levels
            pickable=True,
            # custom legend depending on the mouse hover
            auto_highlight=True,
            # add legend to the highlighted area
            # get_position="coordinates",
            # highlight_color=[0, 0, 0],
            # show name of the country on hover
        )

        all_lat = latitude_range[1] - latitude_range[0]
        all_lon = longitude_range[1] - longitude_range[0]
        radius = int(max(all_lat, all_lon) * 500)

        layer1 = pdk.Layer(
            "ScatterplotLayer",
            displayed_df,
            get_position="[longitude, latitude]",
            get_color="[200, 30, 0, 160]",
            get_radius=radius,
        )

        shown_lat = _get_mean(latitude_range)
        shown_lon = _get_mean(longitude_range)

        zoom_factor = 0.35 if display_type == "Country" else 0.5

        # select zoom value only on the selected area
        zoom = (
            zoom_factor
            * min(
                lat_range / all_lat,
                lon_range / all_lon,
            )
            * 0.5
        )

        # Set the viewport location
        view_state = pdk.ViewState(
            latitude=shown_lat,
            longitude=shown_lon,
            min_zoom=zoom / 2,
            zoom=1,
            max_zoom=zoom * 5,
        )

        displayed_height = 600 if display_type == "Country" else 250
        # Render the map
        deck = pdk.Deck(
            layers=[layer0, layer1],  # Single layer for both polygons and borders
            initial_view_state=view_state,
            map_style="light",
            tooltip={
                "text": (
                    "{legend}"
                    if display_type == "Country"
                    else "-- {name} --\nEvents Count: {Events Count}\nTotal Fatalities: {Total Fatalities}"
                ),
                "style": {"backgroundColor": "white", "color": "black"},
            },
            height=displayed_height,
        )

    with st.empty():
        st.pydeck_chart(deck, use_container_width=True)


@st.fragment
def _display_map_img(displayed_df: pd.DataFrame, country_name: str):
    """
    Displays a map image with aggregated data for administrative regions within a country.

    Args:
    - displayed_df (pd.DataFrame): DataFrame containing data to be displayed on the map,
      typically aggregated by administrative region.
    - country_name (str): Name of the country for which the map is being displayed.

    Operation:
    1. Aggregates event counts and total fatalities by administrative region (`admin1`) from `displayed_df`.
    2. Loads geojson polygons and extreme points for the specified `country_name` using `_load_polygons_adm1`.
    3. Iterates through each feature in `geojson_country_polygons`, updating properties with aggregated data.
    4. Sets default colors and properties for each feature based on aggregated data.
    5. Calls `_create_points_map_placeholder_pdk` to display a map using the PolyDeck (PDK) library,
       showing administrative regions and their aggregated data.
    """
    count_df = displayed_df.copy()
    count_df = count_df.groupby("admin1", as_index=False).agg({"event_date": "count", "fatalities": "sum"})
    # st.dataframe(displayed_df)
    admin_level_data = {}
    for _, row in count_df.iterrows():
        admin_level_data[row["admin1"]] = {
            "Events Count": row["event_date"],
            "Total Fatalities": row["fatalities"],
        }

    # if not os.path.exists(country_map_path):
    geojson_country_polygons, extreme_points = _load_polygons_adm1(country_name, [country_name])

    for feature in geojson_country_polygons["features"]:
        # event counts
        name = feature["properties"]["name"]
        feature["name"] = name
        features_props = admin_level_data.get(name, {"Events Count": "0", "Total Fatalities": "0"})
        feature["Events Count"] = features_props["Events Count"]
        feature["Total Fatalities"] = features_props["Total Fatalities"]

        # colors
        feature_color = [
            198,
            191,
            209,
        ]
        # # _get_fill_color_for_feature(feature["properties"]["name"])
        feature["properties"]["fill_color"] = feature_color
        feature["properties"]["line_color"] = [156, 156, 156]

        # feature["IPC Percentage"] = shown_percentage_val

    if len(geojson_country_polygons["features"]) > 0:
        _create_points_map_placeholder_pdk(
            geojson_country_polygons,
            displayed_df,
            [extreme_points["miny"] - 1, extreme_points["maxy"] + 1],
            [extreme_points["minx"] - 1, extreme_points["maxx"] + 1],
            display_type="Region",
        )
