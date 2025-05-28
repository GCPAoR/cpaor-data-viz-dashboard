import streamlit as st
from frontend.src.specific_datasets_scripts.ocha_hpc import (
    _display_evolution_data, _display_top_countries_with_children_in_need,
    _get_ratio_children_in_need_to_pop_in_need,
    _get_ratio_children_targeted_to_children_in_need,
    _get_total_CP_caseload_in_need,
    _get_ratio_global_funding,
    _get_cp_beneficiaries,
    display_global_funding
)
from frontend.src.utils.utils_functions import _custom_title
from frontend.src.visualizations.barchart import _get_abbreviated_number
from frontend.src.visualizations.maps_creation import \
    _create_polygons_map_placeholder_pdk


@st.fragment
def main_page():
    """
    Constructs the main page layout for the Child Protection Needs Identification overview.

    Operation:
    1. Sets up a Streamlit layout with a title and logo.
    2. Displays severity conditions for children using a polygons map and information
       from ACAPS and INFORM Severity Index.
    3. Displays key indicators:
    - Total Child Protection (CP) caseload in need across countries.
    - Ratio of children in need to total population in need.
    - Ratio of targeted CP interventions to children in need.
    4. Uses custom CSS styles to format and display the key indicators in colored boxes.
    5. Displays top countries by proportion of children in need and their
      evolution using data from OCHA HPC Plans Summary API.
    """

    # Begin streamlit layout
    with st.container():
        _custom_title("Child Protection Needs Identification: Overview", 24)

    with st.container():
        _custom_title(
            f"Key Indicators ({st.session_state['selected-year']})",
            st.session_state["subtitle_size"],
            source="OCHA HPC Plans Summary API",
            date=st.session_state["selected-year"],
        )

        # Define the custom style for the first box
        total_number_of_children_in_need, n_countries_number_of_children_in_need = (
            _get_total_CP_caseload_in_need()
        )

        shown_total_number_of_children_in_need = _get_abbreviated_number(
            int(total_number_of_children_in_need.replace(",", ""))
        ).replace(" ", "\n")

        # Define the custom style for the second box
        (
            ratio_children_in_need_to_ppl_in_need,
            n_countries_ratio_children_in_need_to_ppl_in_need,
        ) = _get_ratio_children_in_need_to_pop_in_need()

        # Define the custom style for the third box
        (
            ratio_children_targeted_to_children_in_need,
            n_countries_ratio_children_targeted_to_children_in_need,
        ) = _get_ratio_children_targeted_to_children_in_need()

        # Define the custom style for the fourth box
        total_cp_beneficiaries, gf_total_countries = _get_cp_beneficiaries()

        # Define the custom style for the fifth box
        ratio_global_funding, gf_total_countries = _get_ratio_global_funding()

        key_figures_styles = """
        <style>
            .key-figure-container {
                display: grid;
                margin-bottom: 24px;
                grid-gap: 12px;
                grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
            }
            .key-figure-box {
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
                transition: 0.3s;
            }
        </style>
        """

        key_figures = f"""
        <div class="key-figure-container">
            <div
                style="background-color: #C6BFD0;"
                class="key-figure-box"
            >
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{shown_total_number_of_children_in_need}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">CP Caseload in Need ({n_countries_number_of_children_in_need} Countries)</p>
            </div>
            <div
                style="background-color: #90AF95;"
                class="key-figure-box"
            >
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{ratio_children_in_need_to_ppl_in_need}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">% CP caseload (in need) vs Total PiN (country level) ({n_countries_ratio_children_in_need_to_ppl_in_need} Countries)</p>
            </div>
            <div
                style="background-color: #9FD5B5;"
                class="key-figure-box"
            >
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{ratio_children_targeted_to_children_in_need}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">% CP targeted vs in need
                ({n_countries_ratio_children_targeted_to_children_in_need} Countries)</p>
            </div>
            <div
                style="background-color: #44AB90;"
                class="key-figure-box"
            >
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{total_cp_beneficiaries}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">Overall # CP reached beneficiaries
                ({gf_total_countries} Countries)</p>
            </div>
            <div
                style="background-color: #94BF95;"
                class="key-figure-box"
            >
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{ratio_global_funding}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">% Received vs Requested on Global Funding
                ({gf_total_countries} Countries)</p>
            </div>
        </div>
        """

        # Use markdown to display the custom-styled boxes
        with st.container():
            st.markdown(key_figures_styles, unsafe_allow_html=True)
            st.markdown(key_figures, unsafe_allow_html=True)

    with st.container():
        _custom_title(
            "Severity conditions for Children",
            st.session_state["subtitle_size"],
            source="ACAPS, INFORM Severity Index",
            date=st.session_state["inform_severity_last_updated"],
        )
        with st.container():
            _create_polygons_map_placeholder_pdk(
                st.session_state["geojson_country_polygons"], display_type="Country"
            )

    for _ in range(2):
        st.markdown("")

    with st.container():
        top_countries_with_children_in_need_col, _, children_in_need_evolution_col = (
            st.columns((0.5, 0.05, 0.45))
        )
        with top_countries_with_children_in_need_col:
            _custom_title(
                "Top Countries- % Child Protection Caseload (in Need) vs Total PiN",
                st.session_state["subtitle_size"],
                source="OCHA HPC Plans Summary API",
                date=st.session_state["selected-year"],
            )
            _display_top_countries_with_children_in_need()

        with children_in_need_evolution_col:
            _custom_title(
                "Evolution of CP Caseload (in Need)",
                st.session_state["subtitle_size"],
                source="OCHA HPC Plans Summary API",
                date=f"{min(st.session_state['filter-years'])}-{st.session_state['selected-year']}"
            )
            st.markdown("## ")
            _display_evolution_data()

    with st.container():
        _custom_title(
            "Funding requested vs Funding received",
            st.session_state["subtitle_size"],
            source="OCHA HPC Plans Summary API",
            date=f"{min(st.session_state['filter-years'])}-{st.session_state['selected-year']}"
        )
        st.markdown("**Note: The overall funding includes the HNRPs, FAs. Regional Appeals are excluded.**")
        display_global_funding()
