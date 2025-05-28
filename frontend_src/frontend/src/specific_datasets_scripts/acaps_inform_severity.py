import pandas as pd
import streamlit as st
from frontend.src.utils.utils_functions import (
    _custom_title, _get_bullet_point_as_highlighted_text_display)
from frontend.src.visualizations.barchart import \
    _create_horizontal_continous_scale_barplot  # _create_horizontal_single_scale_barplot,


country_names_mapping = {"DRC": "Congo DRC", "CAR": "Central African Republic"}


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the columns of a DataFrame by stripping whitespace from column names.

    Parameters:
    df (pd.DataFrame): The DataFrame to clean.

    Returns:
    pd.DataFrame: The cleaned DataFrame with whitespace stripped from column names.
    """
    df = df.rename(columns={col: col.strip() for col in df.columns})
    if "COUNTRY" in df.columns:
        df["COUNTRY"] = df["COUNTRY"].apply(lambda x: country_names_mapping.get(x, x))
    return df


def _load_information_severity_index_data():
    """
    Function to load the INFORM Severity Index data.
    """

    df_countries = pd.read_excel(
        st.session_state["inform_severity_data_path"],
        sheet_name="INFORM Severity - country",
        header=1,
    ).iloc[2:]

    df_countries = _clean_columns(df_countries)

    df_countries["Last updated"] = pd.to_datetime(
        df_countries["Last updated"]
    ).dt.strftime("%d-%m-%Y")

    df_countries = df_countries[
        df_countries.COUNTRY.isin(st.session_state["countries"])
    ].rename(columns={"INFORM Severity category.1": "INFORM Severity category name"})

    st.session_state["inform_severity_last_updated"] = "-".join(
        df_countries["Last updated"].max().split("-")[1:]
    )  # .strftime("%m-%Y")

    return df_countries


def _load_crisis_specific_df_many_empty_rows(
    selected_country: str, sheet_name: str, initial_row_number: int
):
    """
    Loads a specific crisis-related DataFrame with potentially many empty rows from an Excel sheet.

    Parameters:
    sheet_name (str): The name of the sheet in the Excel file.
    initial_row_number (int): The initial row number from which to start loading data.

    Returns:
    pd.DataFrame: The loaded DataFrame containing crisis-related data filtered for the selected country.

    Operation:
    1. Defines a mapping for translating country names.
    2. Reads an Excel file into a DataFrame, starting from a specified row, and renames columns.
    3. Filters the DataFrame to include only rows matching the selected country stored in Streamlit session state.
    4. Returns the filtered DataFrame containing crisis-related data.
    """
    crisis_wide_df = (
        pd.read_excel(
            st.session_state["inform_severity_data_path"],
            sheet_name=sheet_name,
            header=1,
        )
        .rename(
            columns={
                "Unnamed: 0": "CRISIS",
                "Unnamed: 1": "DRIVERS",
                "Unnamed: 2": "CRISIS ID",
                "Unnamed: 3": "COUNTRY",
                "Unnamed: 4": "Iso3",
            }
        )
        .iloc[initial_row_number:]
    )
    crisis_wide_df["COUNTRY"] = crisis_wide_df["COUNTRY"].apply(
        lambda x: country_names_mapping.get(x, x)
    )
    crisis_wide_df = crisis_wide_df[
        crisis_wide_df["COUNTRY"] == selected_country
    ].replace("x", 0)

    crisis_wide_df = _clean_columns(crisis_wide_df)

    return crisis_wide_df


def _load_crisis_specific_df_few_empty_rows(
    selected_country: str, sheet_name: str, initial_row_number: int
):
    """
    Loads a specific crisis-related DataFrame with few empty rows from an Excel sheet.

    Parameters:
    sheet_name (str): The name of the sheet in the Excel file.
    initial_row_number (int): The initial row number from which to start loading data.

    Returns:
    pd.DataFrame: The loaded DataFrame containing crisis-related data.

    Operation:
    1. Reads an Excel file into a DataFrame, starting from a specified row, and renames columns.
    2. Returns the loaded DataFrame containing crisis-related data.
    """
    crisis_wide_df = (
        pd.read_excel(
            st.session_state["inform_severity_data_path"],
            sheet_name=sheet_name,
            header=0,
        ).iloc[initial_row_number:]
    ).rename(columns={"Crisis": "CRISIS"})

    crisis_wide_df = _clean_columns(crisis_wide_df)

    # st.markdown(crisis_wide_df.columns)
    return crisis_wide_df


def _get_list_of_crises(selected_country: str):
    """
    Function to get a list of crises from the INFORM Severity Index data.
    """
    treated_crises = _load_crisis_specific_df_many_empty_rows(
        selected_country, "Impact of the crisis", 3
    )
    treated_crises = treated_crises[treated_crises["COUNTRY"] == selected_country]

    treated_crises = treated_crises["CRISIS"].unique()
    return treated_crises.tolist()


@st.fragment
def _show_physical_environment(selected_country: str):
    """
    Displays the physical environment indicators related to crises using horizontal continuous scale bar plots.

    Operation:
    1. Sets a custom title for the section.
    2. Loads specific crisis-related data from Excel sheets for different indicators.
    3. If no data is available for the selected country, displays a message and returns.
    4. Calculates maximum values for main indicators and complexity of the crisis indicators.
    5. Combines and prepares the data into a final DataFrame.
    6. Creates a horizontal continuous scale bar plot to visualize the indicators.
    """
    _custom_title(
        "Physical environment",
        font_size=st.session_state["subtitle_size"],
        source="ACAPS, INFORM Severity Index",
        date=st.session_state["inform_severity_last_updated"],
    )
    df_main_sheet = _load_crisis_specific_df_many_empty_rows(
        selected_country, "INFORM Severity - all crises", 2
    )
    if len(df_main_sheet) == 0:
        st.markdown(f"No information available for {selected_country}")
        return

    # st.dataframe(df_main_sheet)

    main_sheet_indicators = [
        "Impact of the crisis",
        "Conditions of people affected",
        "Complexity of the crisis",
    ]

    results_main_sheet = df_main_sheet[main_sheet_indicators].max(axis=0).to_frame().T

    complexity_of_the_crisis_indicators = ["Safety and security", "Humanitarian access"]
    complexity_of_the_crisis_df = (
        _load_crisis_specific_df_many_empty_rows(
            selected_country, "Complexity of the crisis", 3
        )[complexity_of_the_crisis_indicators]
        .max(axis=0)
        .to_frame()
        .T
    )

    final_df = pd.concat(
        [results_main_sheet, complexity_of_the_crisis_df], axis=1
    ).T.rename(columns={0: "Value"})
    final_df["Indicator"] = final_df.index
    # final_df["Indicator"] = final_df["Indicator"].apply(lambda x: mapping_index_to_shown_val.get(x, x))
    final_df.reset_index(drop=True, inplace=True)

    _create_horizontal_continous_scale_barplot(
        final_df,
        "Indicator",
        "Value",
        text_col="Value",
        max_val=5,
        color1="#D2E5B7",
        color2="#86789C",
    )


@st.fragment
def _show_impact_of_the_crisis(selected_country: str):
    """
    Displays indicators related to the impact of the crisis using a horizontal continuous scale bar plot.

    Operation:
    1. Sets a custom title for the section.
    2. Defines columns and their displayed values for the indicators.
    3. Loads specific crisis-related data from an Excel sheet for impact indicators.
    4. Calculates maximum values for the indicators and adjusts values for percentage display.
    5. Prepares the data into a DataFrame with adjusted values and indicator labels.
    6. Creates a horizontal continuous scale bar plot to visualize the indicators.
    """
    columns_to_shown_val = {
        "% of total area affected": "% of total area affected",
        "% of total population living in the affected area": "% of total population living\nin the affected area",
        "% of total population displaced on the total population affected": "% of total population displaced\non the total population affected",  # noqa
        "% of fatalities on the total population affected": "% of fatalities on\nthe total population affected",
    }
    columns = list(columns_to_shown_val.keys())

    df = (
        _load_crisis_specific_df_many_empty_rows(
            selected_country, "Impact of the crisis", 3
        )[columns]
        .max(axis=0)
        .to_frame()
        .rename(columns={0: "Value"})
    )
    df["Value"] = df["Value"].apply(lambda x: min(100, round(100 * x, 2)))
    df["Indicator"] = df.index
    df["Indicator"] = df["Indicator"].apply(lambda x: columns_to_shown_val.get(x, x))
    df["Shown Value"] = df["Value"].apply(lambda x: f"{x}%")
    max_val = df["Value"].max()
    _custom_title(
        "Impact of the crisis",
        22,
        source="ACAPS, INFORM Severity Index",
        date=st.session_state["inform_severity_last_updated"],
    )

    _create_horizontal_continous_scale_barplot(
        df,
        "Indicator",
        "Value",
        text_col="Shown Value",
        max_val=max_val,
        # color1="#D2E5B7",
        color1="#86789C",
        color2="#86789C",
    )


@st.fragment
def _show_barriers_goods_services(selected_country: str):
    """
    Displays indicators related to barriers to accessing goods and services using a horizontal continuous scale bar plot.

    Operation:
    1. Sets a custom title for the section.
    2. Defines columns and their displayed names for the indicators.
    3. Loads specific crisis-related data from an Excel sheet for complexity indicators.
    4. Calculates maximum values for the indicators.
    5. Prepares the data into a DataFrame with adjusted values and indicator labels.
    6. Creates a horizontal continuous scale bar plot to visualize the indicators.
    """
    _custom_title(
        "Barriers to accessing good and services",
        font_size=st.session_state["subtitle_size"],
        source="ACAPS, INFORM Severity Index",
        date=st.session_state["inform_severity_last_updated"],
    )

    columns_to_show_name = {
        "Ongoing insecurity/hostilities affecting humanitarian assistance": "Ongoing insecurity hostilities\naffecting humanitarian assistance",  # noqa
        "Physical constraints in the environment (obstacles related to terrain, climate, lack of infrastructure, etc.)": "Physical constraints in the environment\n(obstacles related to terrain, climate,\nlack of infrastructure, etc.)",  # noqa
        "Violence against personnel, facilities and assets": "Violence against personnel,\nfacilities and assets",
        "Denial of existence of humanitarian needs or entitlements to assistance": "Denial of existence of humanitarian\nneeds or entitlements to assistance",  # noqa
        "Presence of mines and improvised explosive devices": "Presence of mines and\nimprovised explosive devices",
    }
    original_col_names = list(columns_to_show_name.keys())
    df = (
        _load_crisis_specific_df_many_empty_rows(
            selected_country, "Complexity of the crisis", 3
        )[original_col_names]
        .max(axis=0)
        .to_frame()
        .T
    ).T.rename(columns={0: "Value"})

    df["Indicator"] = df.index
    df["Indicator"] = df["Indicator"].apply(lambda x: columns_to_show_name.get(x, x))
    df.reset_index(drop=True, inplace=True)

    _create_horizontal_continous_scale_barplot(
        df,
        "Indicator",
        "Value",
        text_col="Value",
        max_val=5,
        color1="#D2E5B7",
        color2="#86789C",
        figsize=(10, 7),
    )


@st.fragment
def _display_crises_list(selected_country: str):
    """
    Function to display a list of crises from the INFORM Severity Index data.
    """
    crises = _get_list_of_crises(selected_country)
    _custom_title(
        "Drivers (Crises)",
        st.session_state["subtitle_size"],
        source="ACAPS, INFORM Severity Index",
        date=st.session_state["inform_severity_last_updated"],
    )
    items = ''
    for one_crisis in crises:
        custom_css = _get_bullet_point_as_highlighted_text_display(one_crisis)
        items += custom_css

    css = """
        <style>
            .crisis-tags {
                display: flex;
                flex-direction: row;
                align-items: flex-start;
                flex-wrap: wrap;
                gap: 10px;
            }
        </style>
    """
    final_html = f"""<div class="crisis-tags">
        {items}
    </div>"""
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(final_html, unsafe_allow_html=True)
