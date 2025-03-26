import pandas as pd
import streamlit as st
from frontend.src.utils.utils_functions import _custom_title
from frontend.src.visualizations.barchart import (_display_stackbar,
                                                  _get_abbreviated_number)


@st.fragment
def _load_idmc_data():
    """
    Function to load the IDMC data from the Excel file.
    """
    mapping_countries = {
        "Dem. Rep. Congo": "Congo DRC",
    }
    df = pd.read_excel(
        st.session_state["idmc_data_path"], sheet_name="3_IDPs_SADD_estimates"
    )
    df["Country"] = df["Country"].apply(lambda x: mapping_countries.get(x, x))
    df = df[df["Country"].isin(st.session_state["countries"])]

    return df


def _display_one_cause_results(df: pd.DataFrame, displacement_cause: str):
    """
    Displays results for displacement driven by a specific cause (either 'Conflict' or 'Disaster').

    Args:
    - df (pd.DataFrame): DataFrame containing displacement data.
    - displacement_cause (str): Cause of displacement ('Conflict' or 'Disaster').

    Operation:
    1. Sets a custom title for the displacement cause-driven displacement section.
    2. Computes the total number of children displaced and total number of people displaced due to the specified cause.
    3. Constructs a dictionary `numbers_values` containing:
       - Title for children displaced due to the cause.
       - Original numbers including the number of children and total displaced people.
       - Annotation indicating the percentage of children among the displaced population.
       - Plot size.
    4. Calls _display_stackbar() to visualize the stacked bar chart based on `numbers_values`.
    """
    age_groups = ["0-4", "5-11", "12-17", "18-59", "60+"]

    _custom_title(
        f"{displacement_cause}-driven displacement",
        font_size=st.session_state["subsubtitle_size"],
    )

    age_values = df[(df["Cause"] == displacement_cause) & (df.Sex == "Both sexes")]
    if len(age_values)==0:
        st.markdown(f"No data available for {displacement_cause.lower()} displacement")
        return

    max_year = age_values["Year"].max()

    age_values = age_values[age_values.Year == max_year]
    if len(age_values)==0:
        st.markdown(f"No data available for {displacement_cause.lower()} displacement")
        return
    age_values = age_values[age_groups].values[0]

    if len(age_values) == 0 or sum(age_values) == 0:
        st.markdown(f"No data available for {displacement_cause.lower()} displacement")

    else:
        # st.markdown(age_values)
        children_number = sum(age_values[:3])
        total_number = sum(age_values)

        ratio_children_displaced = round(children_number / total_number * 100)
        numbers_values = {
            "title": f"Children displaced due to {displacement_cause.lower()}",
            "original_numbers": [
                {
                    "value": children_number,
                    "label": "Children (<18 YO)",
                    "color": "#D6E9DF",
                    "number_annotation": f"{ratio_children_displaced}%:\n{_get_abbreviated_number(children_number)}",
                },
                {
                    "value": total_number,
                    "label": "Adults (18+ YO)",
                    "color": "#B1DBC3",
                    "number_annotation": f"100%: {_get_abbreviated_number(total_number)}\nPeople Displaced",
                },
            ],
            "annotation": f"\n\n\n\nFrom {_get_abbreviated_number(total_number)} people displaced from {displacement_cause.lower()}, {ratio_children_displaced}% are children.",  # noqa
            "plot_size": (10, 1),
        }
        _display_stackbar(numbers_values)


@st.fragment
def _get_displacement_numbers(selected_country: str):
    """
    Displays displacement statistics categorized into conflict and disaster causes for the selected country.

    Operation:
    1. Sets a custom title for the displacement section.
    2. Retrieves the dataframe containing displacement data (IDMC, GRID) for the selected country.
    3. Filters the dataframe based on the selected country.
    4. If no data is available, displays a message indicating no data.
    5. If data is available, displays results for both conflict and disaster causes using _display_one_cause_results().
    """
    source_name = "IDMC, GRID"

    country_df = st.session_state["idmc_df"].copy()

    country_df = country_df[country_df["Country"] == selected_country]
    country_df.reset_index(drop=True, inplace=True)

    if len(country_df) == 0:
        _custom_title(
            "Displacement",
            font_size=st.session_state["subtitle_size"],
            source=source_name,
        )
        st.write("No data available for this country")
        return
    # Note: The below is same as assigning st.session_state["selected-year"]
    # as we are filtering based on "selected-year" key above.
    st.session_state["idmc_last_updated"] = country_df["Year"].max()

    _custom_title(
        "Displacement",
        font_size=st.session_state["subtitle_size"],
        source=source_name,
        date=st.session_state["idmc_last_updated"],
    )
    conflict_col, _, disaster_col = st.columns([0.47, 0.06, 0.47])
    with conflict_col:
        if len(country_df) > 0:
            _display_one_cause_results(country_df, "Conflict")
        else:
            st.write("No conflict data available for this country")

    with disaster_col:
        if len(country_df) > 0:
            _display_one_cause_results(country_df, "Disaster")
        else:
            st.write("No disaster data available for this country")
