import streamlit as st
from frontend.src.specific_datasets_scripts.acaps_inform_severity import (
    _display_crises_list, _show_barriers_goods_services,
    _show_impact_of_the_crisis, _show_physical_environment)
from frontend.src.specific_datasets_scripts.acaps_protection_indicators import (
    _display_main_summary, _display_specific_protection_indicators)
from frontend.src.specific_datasets_scripts.acled import (
    _display_acled_map_data, _display_number_of_events_targetting_civilians)
from frontend.src.specific_datasets_scripts.idmc import \
    _get_displacement_numbers
from frontend.src.specific_datasets_scripts.ipc import _plot_ipc_results
from frontend.src.specific_datasets_scripts.ocha_hpc import (
    _display_pin_stackbar,
    display_country_level_funding,
    display_cp_beneficiaries
)
from frontend.src.specific_datasets_scripts.ohchr import \
    country_wise_legal_framework
from frontend.src.specific_datasets_scripts.unicef_data_processing import (
    _display_child_protection_risks, _display_tabular_mortality_rates)
from frontend.src.utils.utils_functions import _add_blank_space, _custom_title


@st.fragment
def _display_all_data(selected_country: str):
    """
    Displays a comprehensive analysis of various data related to child
    protection and humanitarian crises for a selected country.

    Args:
    - None

    Operation:
    1. Sets a custom title displaying the selected country's name with a large font size.
    2. Defines columns for layout, allocating space for map data, additional summaries, and detailed analysis.
    3. Calls `_display_map_data` to show a map of protection-related events filtered by type and date range.
    4. Sets a custom title indicating the source of additional data related to child protection.
    5. Calls `_display_main_summary` to display a summary of child protection indicators without showing evidence.
    6. Calls `_display_pin_stackbar` to show a stacked bar chart related to Protection Indicators from ACAPS.
    7. Calls `_display_crises_list` to display a list of crises impacting child protection.
    8. Sets a custom title for displaying causes and underlying factors of child protection issues.
    9. Calls `_show_physical_environment` to display data related to the physical environment affecting child protection.
    10. Calls `_show_impact_of_the_crisis` to display data related to the impact of crises on child protection.
    11. Calls `_display_number_of_events_targetting_civilians` to display the number of events targeting civilians.
    12. Calls `_show_barriers_goods_services` to display data related to barriers in accessing goods and services.
    13. Calls `_plot_ipc_results` to display results related to food insecurity using IPC results.
    14. Calls `_get_displacement_numbers` to display data related to displacement numbers.
    15. Calls `country_wise_legal_framework` to display an overview of the legal framework related to child protection.
    16. Calls `_display_child_protection_risks` to display risks related to child protection.
    17. Calls `_display_specific_protection_indicators` to display specific protection indicators.
    18. Calls `_display_tabular_mortality_rates` to display tabular data related to mortality rates.
    """
    cp_info, _, cp_charts = st.columns([0.47, 0.06, 0.47])

    with cp_info:
        _custom_title(
            "Child Protection Situation",
            st.session_state["subtitle_size"],
            source="ACAPS, Protection Indicators",
            date=st.session_state[f"protection_df_max_date_{selected_country}"],
        )
        _display_main_summary(selected_country, display_evidence=False)
        _display_acled_map_data(selected_country)

    with cp_charts:
        _display_pin_stackbar(selected_country)
        display_cp_beneficiaries(selected_country)
        display_country_level_funding(selected_country)
        _display_crises_list(selected_country)

    _custom_title(
        "Causes & Underlying Factors", font_size=30
    )
    st.write(" ")
    physical_env_col, _, impact_of_the_crisis_col = st.columns([0.47, 0.06, 0.47])
    with physical_env_col:
        _show_physical_environment(selected_country)

    with impact_of_the_crisis_col:
        _show_impact_of_the_crisis(selected_country)

    _add_blank_space(1)

    _display_number_of_events_targetting_civilians(selected_country)

    barriers_col, _, food_insecurity_col = st.columns([0.47, 0.06, 0.47])
    with barriers_col:
        _show_barriers_goods_services(selected_country)

    with food_insecurity_col:
        _plot_ipc_results(selected_country)

    _get_displacement_numbers(selected_country)

    _add_blank_space(3)

    country_wise_legal_framework(selected_country, display_detailed_results=False)

    _add_blank_space(3)

    _display_child_protection_risks(selected_country)
    _display_specific_protection_indicators(selected_country)

    _add_blank_space(3)

    _display_tabular_mortality_rates(selected_country)
    _custom_title(
        "Children’s mental and physical health", st.session_state["subtitle_size"]
    )
    st.markdown("No data available for this indicator.")
