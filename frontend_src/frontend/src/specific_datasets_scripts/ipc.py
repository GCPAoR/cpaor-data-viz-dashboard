import pandas as pd
import streamlit as st

from frontend.src.utils.utils_functions import _custom_title
from frontend.src.visualizations.barchart import (
    _create_horizontal_continous_scale_barplot,
    _get_abbreviated_number,
)


def _load_preprocess_ipc_data():
    """
    Loads and preprocesses IPC (Integrated Food Security Phase Classification) data.

    Operation:
    1. Defines a dictionary mapping countries to their abbreviations.
    2. Creates a reverse dictionary to map abbreviations back to country names.
    3. Specifies relevant columns to read from the IPC data file.
    4. Reads the IPC data file into a DataFrame, skipping the first row.
    5. Filters the DataFrame to include only current validity period and Phase 3+ (food insecurity).
    6. Renames columns for clarity.
    7. Converts the 'Number of Food Insecure People' column to integer type.
    8. Maps abbreviated country names to full country names using the reverse dictionary.
    9. Filters the DataFrame to include only countries in the session state.
    10. Returns the preprocessed DataFrame.
    """
    countries_abbr = {
        "Afghanistan": "AFG",
        "Bangladesh": "BAN",
        "Burkina Faso": "BFA",
        "Burundi": "BDI",
        "Cameroon": "CMR",
        "Central African Republic": "CAR",
        "Chad": "CHA",
        "Colombia": "COL",
        "Congo DRC": "COD",
        "Ecuador": "ECU",
        "El Salvador": "SLV",
        "Ethiopia": "ETH",
        "Guatemala": "GTM",
        "Haiti": "HTI",
        "Honduras": "HON",
        "Iran": "IRN",
        "Iraq": "IRQ",
        "Jordan": "JOR",
        "Kenya": "KEN",
        "Lebanon": "LBN",
        "Libya": "LBY",
        "Madagascar": "MAD",
        "Malawi": "MWI",
        "Mali": "MLI",
        "Mexico": "MEX",
        "Mozambique": "MOZ",
        "Myanmar": "MMR",
        "Nepal": "NEP",
        "Nicaragua": "NIC",
        "Niger": "NIG",
        "Nigeria": "NGA",
        "Pakistan": "PAK",
        "Palestine": "PAL",
        "Peru": "PER",
        "Philippines": "PHI",
        "Somalia": "SOM",
        "South Sudan": "SSD",
        "Sudan": "SUD",
        "Syria": "SYR",
        "Türkiye": "TUR",
        "Ukraine": "UKR",
        "Venezuela": "VEN",
        "Yemen": "YEM",
        "Zimbabwe": "ZIM",
    }
    abrev2country = {v: k for k, v in countries_abbr.items()}

    relevant_cols = [
        "Date of analysis",
        "Country",
        "Level 1",
        "Validity period",
        "Phase",
        "Number",
    ]
    df = pd.read_csv(st.session_state["ipc_data_path"], usecols=relevant_cols).iloc[1:]
    df = df[(df["Validity period"] == "current") & (df["Phase"] == "3+")].rename(
        columns={
            "Country": "Country abrv",
            "Level 1": "Region Name",
            "Number": "Number of Food Insecure People",
        }
    )
    df["Number of Food Insecure People"] = df["Number of Food Insecure People"].astype(int)
    df["Country"] = df["Country abrv"].apply(lambda x: abrev2country.get(x, x))
    df = df[df["Country"].isin(st.session_state["countries"])]
    # st.dataframe(df)
    return df


@st.fragment
def _plot_ipc_results(selected_country: str):
    """
    Plots the results of Food Insecurity using a horizontal single-scale bar plot.

    Operation:
    1. Sets a custom title for the Food Insecurity section.
    2. Copies and filters the IPC DataFrame for the selected country.
    3. Checks if data is available for the selected country; if not, displays a message and returns.
    4. Sorts the filtered DataFrame by the number of food insecure people in ascending order.
    5. Adds a column 'Shown Number' with abbreviated numbers for display.
    6. Computes the maximum value for the bar plot based on the number of food insecure people.
    7. Calls _create_horizontal_single_scale_barplot() to generate the bar plot with:
       - DataFrame with IPC data.
       - Columns for region name, number of food insecure people, and shown number.
       - Maximum value for the bar plot.
       - Custom color, title, x-axis and y-axis titles.
    """

    ipc_one_country_values_df = st.session_state["ipc_df"].copy()
    ipc_one_country_values_df = ipc_one_country_values_df[ipc_one_country_values_df["Country"] == selected_country]

    if len(ipc_one_country_values_df) == 0:
        _custom_title("Food Insecurity", font_size=st.session_state["subtitle_size"], source="IPC")
        st.markdown(f"No Information for Food Security for {selected_country}")
        return

    ipc_one_country_values_df["Formatted Date"] = pd.to_datetime(
        ipc_one_country_values_df["Date of analysis"], format="%b %Y"
    )

    max_date = ipc_one_country_values_df["Formatted Date"].max()

    st.session_state[f"max_date_ipc_{selected_country}"] = max_date.strftime("%b %Y")

    ipc_one_country_values_df = ipc_one_country_values_df[ipc_one_country_values_df["Formatted Date"] == max_date]

    _custom_title(
        "Food Insecurity",
        font_size=st.session_state["subtitle_size"],
        source="IPC",
        date=st.session_state[f"max_date_ipc_{selected_country}"],
    )

    ipc_one_country_values_df = ipc_one_country_values_df[
        ["Date of analysis", "Region Name", "Number of Food Insecure People"]
    ].sort_values(by="Number of Food Insecure People", ascending=True)

    ipc_one_country_values_df["Shown Number"] = ipc_one_country_values_df["Number of Food Insecure People"].apply(
        _get_abbreviated_number
    )

    # st.dataframe(ipc_one_country_values_df)

    max_shown_value = ipc_one_country_values_df["Number of Food Insecure People"].max()

    _create_horizontal_continous_scale_barplot(
        ipc_one_country_values_df,
        "Region Name",
        "Number of Food Insecure People",
        "Shown Number",
        max_val=max_shown_value,
        color1="#86789C",
        color2="#86789C",
        title=f"{selected_country} - Food Insecure Population (Phase 3+)\n",
        x_ax_title="Number of People Affected",
        y_ax_title="Region",
        # color2="#86789C",
    )
