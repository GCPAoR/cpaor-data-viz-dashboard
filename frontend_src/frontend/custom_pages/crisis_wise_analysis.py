import pandas as pd
import streamlit as st

from frontend.src.specific_datasets_scripts.acaps_inform_severity import (
    _get_list_of_crises,
    _load_crisis_specific_df_few_empty_rows,
    _load_crisis_specific_df_many_empty_rows,
)
from frontend.src.utils.utils_functions import _add_blank_space, _custom_title
from frontend.src.visualizations.barchart import (
    _create_horizontal_continous_scale_barplot,
)  # _create_horizontal_single_scale_barplot,


@st.fragment
def _display_crisis_wise_analysis(selected_country: str):
    """
    Displays crisis-wise analysis based on selected crisis and specific data categories.

    Operation:
    1. Sets a custom title for the 'Crisis-Wise Analysis' section using `_custom_title`.
    2. Defines a dictionary `sheet_name_to_columns` containing data categories,
       loading functions, columns, initial row numbers, and visualization functions.
    3. Retrieves a list of treated crises using `_get_list_of_crises`.
    4. Loads data specific to the 'Complexity of the crisis' sheet into `df_hum_access`.
    5. Presents a dropdown to select a crisis from `treated_crises` and displays it as a custom title.
    6. Displays the humanitarian access score for the selected crisis.
    7. Sets up columns using Streamlit for layout purposes.
    8. Iterates through each sheet in `sheet_name_to_columns`:
    - Loads data for the current sheet using the specified loading function and
      filters it by selected crisis and country.
    - Displays each category within the sheet with its corresponding score using `_custom_title`
      and a visualization function based on column type.
    - Converts scores to percentage format if specified and sets maximum values for visualization.

    """
    sheet_name_to_columns = {
        "Impact of the crisis": {
            "column_types": "percentage",
            "loading_function": _load_crisis_specific_df_many_empty_rows,
            "columns": [
                "% of total area affected",
                "% of total population\nliving in the affected area",
                "% of people affected\non the total population exposed",
                "% of total population displaced\non the total population affected",
                "% of fatalities\non the total population affected",
            ],
            "initial_row_number": 3,
            "visualization_function": _create_horizontal_continous_scale_barplot,
        },
        "Conditions of people affected": {
            "column_types": "percentage",
            "loading_function": _load_crisis_specific_df_many_empty_rows,
            "columns": [
                "% of people in none/minimal\nconditions - Level 1",
                "% of people in stressed\nconditions - level 2",
                "% of people in moderate\nconditions - level 3",
                "% of people severe\nconditions - level 4",
                "% of people extreme\nconditions - level 5",
            ][::-1],
            "initial_row_number": 3,
            "visualization_function": _create_horizontal_continous_scale_barplot,
        },
        "Complexity of the crisis": {
            "column_types": "absolute",
            "loading_function": _load_crisis_specific_df_many_empty_rows,
            "columns": [
                "size of excluded ethnic groups",
                "Trust in society",
                "Conflict Intensity",
                "Safety and security",
                "Humanitarian access",
            ],
            "initial_row_number": 3,
            "visualization_function": _create_horizontal_continous_scale_barplot,
        },
        "Crisis Indicator Data": {
            "column_types": "absolute",
            "loading_function": _load_crisis_specific_df_few_empty_rows,
            "columns": [
                # "People living in the affected area",
                "Restriction of movement (impediments to freedom\nof movement and/or administrative restrictions)",
                "Violence against personnel, facilities and assets",
                "Denial of existence of humanitarian needs\nor entitlements to assistance",
                "Physical constraints in the environment (obstacles\nrelated to terrain, climate, lack of infrastructure, etc.)",  # noqa
                "Ongoing insecurity/hostilities affecting\nhumanitarian assistance",
                "Restriction and obstruction of access\nto services and assistance",
                "Presence of mines and improvised\nexplosive devices",
            ],
            "initial_row_number": 1,
            "visualization_function": _create_horizontal_continous_scale_barplot,
        },
    }

    treated_crises = _get_list_of_crises(selected_country)

    df_hum_access = _load_crisis_specific_df_many_empty_rows(
        selected_country, sheet_name="Complexity of the crisis", initial_row_number=3
    )

    _custom_title(
        "",
        font_size=6,
        source="ACAPS, INFORM Severity Index",
        date=st.session_state["inform_severity_last_updated"],
    )

    if treated_crises:
        selected_crisis = st.selectbox("Select Crisis/Driver", treated_crises, key="crisis_wise_analysis", index=0)
        _add_blank_space(1)
    else:
        st.markdown(f"No crisis available for the country {selected_country}")
        return

    _custom_title("Selected crisis: " + selected_crisis, 30)
    _add_blank_space(1)

    hum_access_score = df_hum_access[df_hum_access["CRISIS"] == selected_crisis]["Humanitarian access"].values[0]
    _custom_title(f"Humanitarian Access Score: {hum_access_score}", 25)

    _add_blank_space(1)

    n_sheets = len(sheet_name_to_columns)
    sheet_ids = [[i, i + 1] for i in range(0, n_sheets, 2)]

    for one_tuple in sheet_ids:
        with st.container():
            columns = st.columns([0.47, 0.06, 0.47])
            for sheet_id in one_tuple:
                sheet_name, columns_info = list(sheet_name_to_columns.items())[sheet_id]

                col_used = 0 if (sheet_id % 2 == 0) else 2

                with columns[col_used]:
                    df_one_sheet = columns_info["loading_function"](
                        selected_country, sheet_name, columns_info["initial_row_number"]
                    )
                    df_one_sheet = df_one_sheet[
                        (df_one_sheet["CRISIS"] == selected_crisis) & (df_one_sheet["COUNTRY"] == selected_country)
                    ]

                    _custom_title(sheet_name, 25)

                    if len(df_one_sheet) == 0:
                        st.markdown("No data available for this crisis")

                    else:
                        values_one_sheet = {
                            col: df_one_sheet[col.replace("\n", " ")].values[0] for col in columns_info["columns"]
                        }

                        # height_per_indicator = 50
                        # map_height = (
                        #     len(columns_info["columns"]) * height_per_indicator * 0.8
                        #     + 70
                        # )
                        displayed_df = pd.DataFrame(values_one_sheet.items(), columns=["Category", "Score"])
                        percentage_bool = columns_info["column_types"] == "percentage"
                        if percentage_bool:
                            displayed_df["Score Text"] = displayed_df["Score"].apply(
                                lambda x: f"{min(100, round(100 * x, 2))}%"
                            )
                            displayed_df["Score"] = displayed_df["Score"] * 100
                            max_val = 100
                        else:
                            displayed_df["Score Text"] = displayed_df["Score"].apply(lambda x: f"{round(x, 2)}")
                            max_val = 5
                        columns_info["visualization_function"](
                            displayed_df,
                            numbers_col="Score",
                            labels_col="Category",
                            text_col="Score Text",
                            max_val=max_val,
                            figsize=(10, 1 + len(columns_info["columns"])),
                            # map_height=map_height,
                        )
        _add_blank_space(2)
