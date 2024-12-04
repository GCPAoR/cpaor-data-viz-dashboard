import json
import os

import pandas as pd
import streamlit as st
from frontend.src.authentification.auth import check_password
from frontend.src.utils.utils_functions import (
    _country_selection_filter,
    _load_countries_list,
    _show_header,
)
app_icon_path = os.path.join("./frontend/images", "cpaor_icon.png")
st.set_page_config(page_title="CPAoR", layout="wide", page_icon=app_icon_path)

st.session_state["base_data_folder"] = "/data"

st.session_state["tabular_data_data_path"] = os.path.join(
    st.session_state["base_data_folder"], "datasources"
)
######### LOAD SESSION STATE VARIABLES #########

countries_list = _load_countries_list()
st.session_state["countries"] = {country: i for i, country in enumerate(countries_list)}
st.session_state["country_index"] = 0
st.session_state.show = False

from frontend.custom_pages.country_profile import _display_all_data
from frontend.custom_pages.crisis_wise_analysis import _display_crisis_wise_analysis
from frontend.custom_pages.methodology import _show_methodological_details
from frontend.custom_pages.worldwide_analysis import main_page
from frontend.src.specific_datasets_scripts.acaps_inform_severity import (
    _load_information_severity_index_data,
)
from frontend.src.specific_datasets_scripts.acaps_protection_indicators import (
    _display_protection_data,
)
from frontend.src.specific_datasets_scripts.acled import _load_acled_data
from frontend.src.specific_datasets_scripts.idmc import _load_idmc_data
from frontend.src.specific_datasets_scripts.ipc import _load_preprocess_ipc_data
from frontend.src.specific_datasets_scripts.ocha_hpc import (
    _get_country_wise_children_in_need_data,
    _get_country_wise_pin_data,
)
from frontend.src.specific_datasets_scripts.ohchr import country_wise_legal_framework

# from src.utils.pop_up import _show_pop_up
from frontend.src.utils.load_geodata import _load_polygons_adm0
from frontend.src.visualizations.maps_creation import (
    default_filling_color,
    severity_mapping_tag_name_to_color_main_countries,
)

st.session_state["title_size"] = 30
st.session_state["subtitle_size"] = 25
st.session_state["subsubtitle_size"] = 22

if check_password():

    st.session_state["tag_name_to_indicators"] = {
        "Causes and Underlying Factors": [
            "Presence of UXO",
            "Humanitarian Access",
            "Displacement",
            "% people in food insecurity\nwho are children",
        ],
        "Child Protection Risks": [
            "Proportion children subjected\nto violence",
            "Proportion girls subjected to\nviolence",
            "% children engaged in child labor",
            "Unaccompanied Children",
            "Separated Children",
            "Pregnancy rate among teens",
        ],
        "Availability, Access, Quality Services": [
            "Coverage of essential health\nservices",
            "Presence of Community\nFeedback Mechanisms",
            "Social service workforce",
            "Inclusive services for\nchildren with disabilities",
        ],
        "Consequences for Children Protection": [
            "Children's physical health",
            "Children's mortality rate",
        ],
        # "Legal Framework": [
        #     "Specific laws for the\nprotection of children",
        #     "child Marriage",
        #     "Sexual Violence",
        #     "Use / recruitment of children\nby armed forces",
        # ],
    }

    st.session_state["inform_severity_data_path"] = os.path.join(
        st.session_state["tabular_data_data_path"],
        "acaps_inform_severity",
        "INFORM Severity latest.xlsx",
    )
    st.session_state["inform_severity_df"] = _load_information_severity_index_data()

    st.session_state["selected_tags"] = list(
        st.session_state["tag_name_to_indicators"].keys()
    ) + ["Legal Framework"]

    st.session_state["pin_df_path"] = os.path.join(
        st.session_state["tabular_data_data_path"], "ocha_hpc", "OCHA PIN.csv"
    )
    st.session_state["all_pin_data"] = pd.read_csv(st.session_state["pin_df_path"])
    st.session_state["country_wise_pin_data"] = _get_country_wise_pin_data(
        st.session_state["all_pin_data"]
    )
    st.session_state["ocha_hpc_min_year"] = st.session_state["all_pin_data"]["year"].min()
    st.session_state["ocha_hpc_max_year"] = st.session_state["all_pin_data"]["year"].max()

    st.session_state["country_wise_children_in_need_data"] = (
        _get_country_wise_children_in_need_data(st.session_state["all_pin_data"])
    )

    _load_acled_data()

    st.session_state["protection_data_path"] = os.path.join(
        st.session_state["tabular_data_data_path"],
        "acaps_protection_indicators",
        "processed_data",
    )

    st.session_state["ipc_data_path"] = os.path.join(
        st.session_state["tabular_data_data_path"],
        "ipc",
        "ipc_global_level1_long.csv",
        # "20240120111155_ipc_global_level1_long.csv",
    )

    with open(
        os.path.join(
            st.session_state["protection_data_path"],
            "..",
            "acaps_protection_indicators_tags.json",
        ),
        "r",
    ) as f:
        st.session_state["acaps_protection_indicators_child_related_tags"] = json.load(f)

    st.session_state["original_polygons_data_path"] = os.path.join(
        st.session_state["base_data_folder"], "polygons_data"
    )
    # os.makedirs(original_data_path, exist_ok=True)

    st.session_state["geolocation_processed_data_path"] = os.path.join(
        st.session_state["original_polygons_data_path"], "processed_data"
    )

    st.session_state["unicef_data_folder_path"] = os.path.join(
        st.session_state["tabular_data_data_path"], "unicef"
    )

    st.session_state["ipc_df"] = _load_preprocess_ipc_data()

    st.session_state["idmc_data_path"] = os.path.join(
        st.session_state["tabular_data_data_path"],
        "idmc",
        "IDMC_Internal_Displacement_Conflict-Violence_Disasters.xlsx",
    )

    st.session_state["idmc_df"] = _load_idmc_data()

    st.session_state["legal_framework_summaries_data_path"] = os.path.join(
        st.session_state["base_data_folder"],
        "datasources",
        "ohchr",
    )

    st.session_state["legal_framework_summaries_data_path"] = os.path.join(
        st.session_state["tabular_data_data_path"], "ohchr", "results"
    )

    with open(
        os.path.join(
            st.session_state["legal_framework_summaries_data_path"],
            "..",
            "grouped_legal_framework_indicators.json",
        ),
        "r",
    ) as f:
        st.session_state["legal_framework_indicators"] = json.load(f)

    if "geojson_country_polygons" not in st.session_state:
        geojson_country_polygons = _load_polygons_adm0()

        inform_severity_values = {
            row["COUNTRY"]: {
                "Situation Severity": row["INFORM Severity category name"],
                "Drivers": row["DRIVERS"],
                "Trend (last 3 months)": row["Trend (last 3 months)"],
                "Last updated": row["Last updated"],
            }
            for i, row in st.session_state["inform_severity_df"].iterrows()
        }

        for feature in geojson_country_polygons["features"]:

            country_name = feature["properties"]["name"]
            if country_name in inform_severity_values:
                one_country_values = inform_severity_values[country_name]
                inform_index_properties = one_country_values["Situation Severity"]
                if inform_index_properties != "x":
                    feature["properties"]["fill_color"] = (
                        severity_mapping_tag_name_to_color_main_countries[
                            inform_index_properties
                        ]
                    )
                else:
                    feature["properties"]["fill_color"] = default_filling_color
                legend = f" -- {country_name} --"
                for key, value in one_country_values.items():
                    final_value = value if value != "x" else "UNKNOWN"
                    legend += f"\n{key}: {final_value}"

            else:
                feature["properties"]["fill_color"] = [255, 255, 255]
                legend = f"Country: {country_name}"
            feature["legend"] = legend

        st.session_state["geojson_country_polygons"] = geojson_country_polygons

    main_font_css = """
    <style>
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
        margin-top: -50px;
        text-transform: uppercase;
        font-size: 1.6rem;
        font-weight: bold;
        margin: -20px 0px 0px 0px;
        width: 100%;
        color: #738462 !important;
    }
    </style>
    """
    st.markdown(main_font_css, unsafe_allow_html=True)

    st.session_state["tabs"] = st.tabs(  # Names of the tabs
        [
            "Global Overview",
            "Country Profile",
            "Legal Framework",
            "Protection Concerns",
            "Breakdown by Crisis",
            "Methodology",
        ]
    )

    ######### DISPLAY THE TABS #########

    with st.sidebar:
        selected_country = _country_selection_filter("country-profile")

    with st.session_state["tabs"][0]:
        with st.container():
            main_page()
    with st.session_state["tabs"][1]:
        _show_header(
            text=f"{selected_country} Country Profile",
        )
        _display_all_data(selected_country)
    with st.session_state["tabs"][2]:
        _show_header(
            text=f"{selected_country} Legal Framework",
        )
        country_wise_legal_framework(selected_country, display_detailed_results=True)
    with st.session_state["tabs"][3]:
        # _show_header(
        #     text=f"{selected_country} Protection Concerns",
        # )
        _display_protection_data(selected_country)
    with st.session_state["tabs"][4]:
        _show_header(
            text=f"{selected_country} Breakdown by Crisis",
        )
        _display_crisis_wise_analysis(selected_country)
    with st.session_state["tabs"][5]:
        _show_header(text="Methodological Overview")
        _show_methodological_details()
