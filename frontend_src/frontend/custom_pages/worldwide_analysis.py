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
from frontend.src.utils.utils_functions import _custom_title, _show_logo
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
        title_col, _, logo_col = st.columns([0.85, 0.01, 0.14])
        with logo_col:
            _show_logo()
        with title_col:
            _custom_title("CHILD PROTECTION NEEDS IDENTIFICATION: OVERVIEW", 40)

    # _test_scatter_plot_map()

    # Create columns for the bar chart and stats
    # col_places = [9, 0.2, 5, 0.2, 1.5]
    maps_col, _, raw_numbers_col = st.columns((0.75, 0.05, 0.2))

    with st.container():
        with maps_col:
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

        with raw_numbers_col:
            _custom_title(
                f"Key Indicators ({st.session_state['ocha_hpc_max_year']})",
                st.session_state["subtitle_size"],
                source="OCHA HPC Plans Summary API",
                date=st.session_state["ocha_hpc_max_year"],
            )
            # Define the custom style for the first box
            total_number_of_children_in_need, n_countries_number_of_children_in_need = (
                _get_total_CP_caseload_in_need()
            )
            shown_total_number_of_children_in_need = _get_abbreviated_number(
                int(total_number_of_children_in_need.replace(",", ""))
            ).replace(" ", "\n")
            first_indicator_custom_css = f"""
            <div style="
                background-color: #C6BFD0;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
                margin-bottom: 20px;
                transition: 0.3s;">
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{shown_total_number_of_children_in_need}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">CP Caseload in Need ({n_countries_number_of_children_in_need} Countries)</p>
            </div>
            """

            # Define the custom style for the second box
            (
                ratio_children_in_need_to_ppl_in_need,
                n_countries_ratio_children_in_need_to_ppl_in_need,
            ) = _get_ratio_children_in_need_to_pop_in_need()
            second_indicator_custom_css = f"""
            <div style="
                background-color: #90AF95;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
                margin-bottom: 20px;
                transition: 0.3s;">
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{ratio_children_in_need_to_ppl_in_need}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">% CP caseload (in need) vs Total PiN (country level) ({n_countries_ratio_children_in_need_to_ppl_in_need} Countries)</p>
            </div>
            """

            # Define the custom style for the third box
            (
                ratio_children_targeted_to_children_in_need,
                n_countries_ratio_children_targeted_to_children_in_need,
            ) = _get_ratio_children_targeted_to_children_in_need()
            third_indicator_custom_css = f"""
            <div style="
                background-color: #9FD5B5;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
                margin-bottom: 20px;
                transition: 0.3s;">
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{ratio_children_targeted_to_children_in_need}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">% CP targeted vs in need
                ({n_countries_ratio_children_targeted_to_children_in_need} Countries)</p>
            </div>
            """

            # Define the custom style for the fourth box
            ratio_global_funding = _get_ratio_global_funding()
            fourth_indicator_custom_css = f"""
            <div style="
                background-color: #94BF95;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
                margin-bottom: 20px;
                transition: 0.3s;">
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{ratio_global_funding}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">% Received vs Requested on Global Funding</p>
            </div>
            """

            # Define the custom style for the fifth box
            total_cp_beneficiaries = _get_cp_beneficiaries()
            fifth_indicator_custom_css = f"""
            <div style="
                background-color: #44AB90;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
                transition: 0.3s;">
                <h2 style="color: #333333; font-size: 30px; margin: 0;">{total_cp_beneficiaries}</h2>
                <p style="color: #333333; font-size: 16px; margin: 0;">Overall # CP reached beneficiaries</p>
            </div>
            """

            # Use markdown to display the custom-styled boxes
            st.markdown(first_indicator_custom_css, unsafe_allow_html=True)
            st.markdown(second_indicator_custom_css, unsafe_allow_html=True)
            st.markdown(third_indicator_custom_css, unsafe_allow_html=True)
            st.markdown(fourth_indicator_custom_css, unsafe_allow_html=True)
            st.markdown(fifth_indicator_custom_css, unsafe_allow_html=True)

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
                date=st.session_state["ocha_hpc_max_year"],
            )
            _display_top_countries_with_children_in_need()

        with children_in_need_evolution_col:
            _custom_title(
                "Evolution of CP Caseload (in Need)",
                st.session_state["subtitle_size"],
                source="OCHA HPC Plans Summary API",
                date=f"{st.session_state['ocha_hpc_min_year']}-{st.session_state['ocha_hpc_max_year']}",
            )
            st.markdown("## ")
            _display_evolution_data()

    with st.container():
        _custom_title(
            "Funding requested vs Funding received",
            st.session_state["subtitle_size"],
            source="OCHA HPC Plans Summary API",
            date=f"{st.session_state['ocha_hpc_min_year']}-{st.session_state['ocha_hpc_max_year']}",
        )
        display_global_funding()

