from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from frontend.src.utils.utils_functions import (_add_commas, _custom_title,
                                                _get_percentage)
from frontend.src.visualizations.barchart import (  # _create_horizontal_single_scale_barplot,
    _create_horizontal_continous_scale_barplot, _create_vertical_barplot,
    _display_stackbar, _get_abbreviated_number)


def _display_top_countries_with_children_in_need(n_kept_countries: int = 10):
    """
    Displays a horizontal single-scale bar plot showing the top countries with the highest proportion of children in need.

    Args:
    - n_kept_countries (int, optional): Number of top countries to display. Defaults to 10.

    Operation:
    1. Copies and sorts the 'country_wise_children_in_need_data' DataFrame from session
       state by 'proportion_children_in_need' in ascending order.
    2. Selects the top 'n_kept_countries' countries with the lowest proportion of children in need.
    3. Calculates the maximum value of 'proportion_children_in_need' from the sorted DataFrame.
    4. Converts 'proportion_children_in_need' values to percentages using the '_get_percentage'
       function and adds to 'shown_proportion_children_in_need' column.
    5. Calls '_create_horizontal_single_scale_barplot' function to create and display a horizontal single-scale bar plot:
    - Uses 'sorted_df' DataFrame with columns 'country', 'proportion_children_in_need',
      and 'shown_proportion_children_in_need'.
    - Specifies 'labels_col' as 'country', 'numbers_col' as 'proportion_children_in_need', and 'text_col'
      as 'shown_proportion_children_in_need'.
    - Sets 'max_val' as the maximum value of 'proportion_children_in_need'.
    - Uses color '#86789C' for bar plot visualization.

    Returns:
    - None
    """

    sorted_df = (
        st.session_state["country_wise_children_in_need_data"]
        .copy()
        .sort_values(by="proportion_children_in_need", ascending=False)[
            ["country", "proportion_children_in_need"]
        ]
        .head(n_kept_countries)
        .iloc[::-1]
    )
    sorted_df["proportion_children_in_need"] = (
        sorted_df["proportion_children_in_need"] * 100
    )
    # max_val = sorted_df["proportion_children_in_need"].max()  # * 100

    sorted_df["shown_proportion_children_in_need"] = sorted_df[
        "proportion_children_in_need"
    ].apply(lambda x: f"{x}%")
    # sorted_df["shown_proportion_children_in_need"] = sorted_df[
    #     "proportion_children_in_need"
    # ].apply(_get_percentage)

    # _create_horizontal_single_scale_barplot(
    #     sorted_df,
    #     labels_col="country",
    #     numbers_col="proportion_children_in_need",
    #     text_col="shown_proportion_children_in_need",
    #     max_val=max_val,
    #     color="#90AF95",
    #     # title=f"{st.session_state.selected_country} - Food Insecure Population (Phase 3+)\n",
    #     # x_ax_title="Evolution of",
    #     # y_ax_title="Region",
    #     # color2="#86789C",
    # )
    _create_horizontal_continous_scale_barplot(
        sorted_df,
        labels_col="country",
        numbers_col="proportion_children_in_need",
        text_col="shown_proportion_children_in_need",
        max_val=100,
        color1="#90AF95",
        color2="#90AF95",
    )


@st.fragment
def _display_evolution_data():
    """
    Displays a vertical bar plot showing the evolution of children in need
    aggregated by year across countries.

    Operation:
    1. Copies and filters the 'all_pin_data' DataFrame from session state to include
       columns 'country', 'year', and 'children_in_need', dropping rows with missing values.
    2. Groups the filtered DataFrame 'df' by 'year', aggregating:
    - 'children_in_need' to calculate the sum of children in need per year.
    - 'country' to count the number of countries reporting children in need data per year.
    3. Resets the index of the grouped DataFrame 'grouped_df' and renames columns to
       'Sum of children in need' and 'Number of countries'.
    4. Formats 'year' column values as strings with a trailing colon ':' for display purposes.
    5. Creates a 'Text' column in 'grouped_df' combining abbreviated sum of children in need and count of countries.
    6. Calls '_create_vertical_barplot' function to generate and display a vertical bar plot:
    - Uses 'grouped_df' DataFrame with columns 'year', 'Sum of children in need', and 'Text'.
    - Specifies 'labels_col' as 'year', 'numbers_col' as 'Sum of children in need', and 'text_col' as 'Text'.
    - Sets color '#C6BFD1' for bar plot visualization.
    - Includes optional parameters for plot title, x-axis title, and y-axis title.

    Returns:
    - None

    """

    df = (
        st.session_state["all_pin_data"]
        .copy()[["country", "year", "children_in_need"]]
        .dropna()
    )

    df = df[df["year"] <= st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)

    # group by year and keep three columns, one for the year,
    # one for the sum of children in need and one for the number of country
    grouped_df = (
        df.groupby("year")
        .agg({"children_in_need": "sum", "country": "count"})
        .reset_index()
        .rename(
            columns={
                "children_in_need": "Sum of children in need",
                "country": "Number of countries",
            }
        )
    )
    grouped_df["year"] = grouped_df["year"].apply(lambda x: f"{int(x)}")

    grouped_df["Text"] = grouped_df.apply(
        lambda x: f"{_get_abbreviated_number(x['Sum of children in need'])}\n({x['Number of countries']} Countries)",
        axis=1,
    )

    _create_vertical_barplot(
        grouped_df,
        labels_col="year",
        numbers_col="Sum of children in need",
        text_col="Text",
        color="#C6BFD0",
        # title="Evolution of CP Caseload (in Need)",
        x_ax_title="Year",
        # y_ax_title="Number of Children in Need",
    )


def _get_total_CP_caseload_in_need():
    """
    Calculates and returns the total number of children in need across
    countries and the number of countries reporting children in need.

    Returns:
    - Tuple[str, int]: A tuple containing:
    - Total number of children in need formatted with commas.
    - Number of countries reporting children in need.

    Operation:
    1. Copies the 'country_wise_pin_data' DataFrame from session state into 'df'.
    2. Computes the sum of 'children_in_need' column values in 'df'
       to get the total number of children in need.
    3. Counts the number of countries in 'df' where 'children_in_need' values
       are not NaN to determine the number of reporting countries.
    4. Formats the total number of children in need using '_add_commas' function for readability.
    5. Returns a tuple with the formatted total number of children in
       need and the count of reporting countries.
    """

    df = st.session_state["country_wise_pin_data"].copy()
    total_number_of_children_in_need = int(df["children_in_need"].sum())
    n_countries = df[df["children_in_need"].notna()].shape[0]
    return _add_commas(total_number_of_children_in_need), n_countries


def _get_ratio_children_in_need_to_pop_in_need():
    """
    Calculates the ratio of children in need to total population in need across countries reporting both values.

    Returns:
    - Tuple[str, int]: A tuple containing:
    - Ratio of children in need to total population in need formatted as a percentage.
    - Number of countries with available data for both children in need and total population in need.

    Operation:
    1. Copies the 'country_wise_pin_data' DataFrame from session state into 'df'.
    2. Filters 'df' to include rows where both 'children_in_need' and 'tot_pop_in_need' columns are not NaN.
    3. Computes the ratio of the sum of 'children_in_need' to the sum of 'tot_pop_in_need' in 'df'.
    4. Formats the ratio as a percentage using the '_get_percentage' function.
    5. Counts the number of rows (countries) in the filtered 'df' to determine the number of countries with available data.
    6. Returns a tuple with the formatted ratio and the count of countries with available data.
    """
    df = st.session_state["country_wise_pin_data"].copy()
    df = df[(df["tot_pop_in_need"].notna()) & (df["children_in_need"].notna())]
    if df["tot_pop_in_need"].sum() > 0:
        ratio = df["children_in_need"].sum() / df["tot_pop_in_need"].sum()
    else:
        ratio = 0

    ratio = _get_percentage(ratio)
    number_of_countries = df.shape[0]
    return ratio, number_of_countries


def _get_ratio_children_targeted_to_children_in_need():
    """
    Calculates the ratio of targeted children to children in need across countries reporting both values.

    Returns:
    - Tuple[str, int]: A tuple containing:
    - Ratio of targeted children to children in need formatted as a percentage.
    - Number of countries with available data for both targeted children and children in need.

    Operation:
    1. Copies the 'country_wise_pin_data' DataFrame from session state into 'df'.
    2. Filters 'df' to include rows where both 'targeted_children' and 'children_in_need' columns are not NaN.
    3. Computes the ratio of the sum of 'targeted_children' to the sum of 'children_in_need' in 'df'.
    4. Formats the ratio as a percentage using the '_get_percentage' function.
    5. Counts the number of rows (countries) in the filtered 'df' to determine the number of countries with available data.
    6. Returns a tuple with the formatted ratio and the count of countries with available data.
    """

    df = st.session_state["country_wise_pin_data"].copy()
    df = df[(df["targeted_children"].notna()) & (df["children_in_need"].notna())]
    if df["children_in_need"].sum() > 0:
        ratio = df["targeted_children"].sum() / df["children_in_need"].sum()
    else:
        ratio = 0
    ratio = _get_percentage(ratio)
    number_of_countries = df.shape[0]
    return ratio, number_of_countries


def _get_cp_beneficiaries():
    df = st.session_state["ocha_hpc_global_funding_df"].copy()
    df = df[df["year"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    cp_beneficiaries = df["cp_beneficiaries"].iat[0]
    if cp_beneficiaries >= 1_000_000:
        cp_beneficiaries = f"{round(cp_beneficiaries/1_000_000, 2)} million"
    total_countries = df["total_countries"].iat[0]
    return cp_beneficiaries, total_countries


def _get_ratio_global_funding():
    df = st.session_state["ocha_hpc_global_funding_df"].copy()
    df = df[df["year"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    ratio = df["funding_received"].iat[0] / df["funding_requested"].iat[0]
    ratio = _get_percentage(ratio)
    total_countries = df["total_countries"].iat[0]
    return ratio, total_countries


def display_global_funding():
    """Plot a grouped barchart related to funding"""
    global_funding_df = st.session_state["ocha_hpc_global_funding_df"]
    # Filter based on selected year
    global_funding_df = global_funding_df[
        global_funding_df["year"] <= st.session_state["selected-year"]
    ]
    global_funding_df.reset_index(drop=True, inplace=True)

    global_funding_df.rename(
        columns={
            "funding_requested": "Funding Requested",
            "funding_received": "Funding Received",
            "total_countries": "Total Countries"
        },
        inplace=True
    )

    if len(global_funding_df):
        df_melted = global_funding_df.melt(
            id_vars=["year", "Total Countries"],
            value_vars=["Funding Requested", "Funding Received"],
            var_name="Funding Type",
            value_name="amount",
        )

        df_melted["amount"] = df_melted["amount"].apply(lambda x: round(x / 1_000_000, 2))

        fig = px.bar(
            df_melted,
            x="year",
            y="amount",
            color="Funding Type",
            color_discrete_map={
                "Funding Requested": "#D6E9DF",
                "Funding Received": "#B1DBC3"
            },
            barmode="group",
            labels={"amount": "Funding Amount (in millions)", "year": "Year"},
            text="amount",
            hover_data={"Total Countries": True}
        )
        fig.update_traces(
            texttemplate='%{y:,} million',
            textposition='outside'
        )
        st.plotly_chart(fig)
    else:
        st.write("No funding related data available.")

def country_mapping(country: str):
    """Maps country names"""
    mapping = {
        "Congo DRC": "Democratic Republic of the Congo",
        "Palestine": "Occupied Palestinian Territory",
        "Türkiye": "Turkey"
    }
    return mapping.get(country, country)


def display_country_level_funding(selected_country: str):
    """Plot a grouped barchart related to funding"""
    year = st.session_state["selected-year"]
    selected_country = country_mapping(selected_country)

    _custom_title(
        "Received Funding vs Requested Funding",
        st.session_state["subtitle_size"],
        source="OCHA HPC Plans Summary API",
        date=f"{min(st.session_state['filter-years'])}-{year}"
    )

    df = st.session_state["ocha_hpc_country_funding_df"]
    df = df[(df["country"] == selected_country) & (df["year"] <= year)]
    df.reset_index(drop=True, inplace=True)

    df.rename(
        columns={
            "funding_requested": "Funding Requested",
            "funding_received": "Funding Received"
        },
        inplace=True
    )

    if len(df):
        df_melted = df.melt(
            id_vars=["year"],
            value_vars=["Funding Requested", "Funding Received"],
            var_name="Funding Type",
            value_name="amount",
        )

        df_melted["amount"] = df_melted["amount"].apply(lambda x: round(x / 1_000_000, 2))

        fig = px.bar(
            df_melted,
            x="year",
            y="amount",
            color="Funding Type",
            color_discrete_map={
                "Funding Requested": "#D6E9DF",
                "Funding Received": "#B1DBC3"
            },
            barmode="group",
            labels={"amount": "Funding Amount (in millions)", "year": "Year"},
            text="amount",
            text_auto=True
        )
        fig.update_traces(
            texttemplate='%{y:,} million',
            textposition='outside',
            textfont=dict(size=30)
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, height=320)
    else:
        st.write("No funding related data available.")
    # if len(df) > 0:
    #     funding_requested = df["funding_requested"].iat[0]
    #     funding_received = df["funding_received"].iat[0]

    #     ratio = funding_received / funding_requested if funding_requested else 0

    #     numbers_values = {
    #         "title": "Received vs Requested Fundings",
    #         "original_numbers": [
    #             {
    #                 "value": funding_received,
    #                 "label": f"Received Funding {_get_abbreviated_number(funding_received)}",
    #                 "color": "#9FD5B5",
    #                 "number_annotation": f"{round(ratio * 100)}%",
    #             },
    #             {
    #                 "value": funding_requested,
    #                 "label": "Requested Funding",
    #                 "color": "#d3d3d3",
    #                 "number_annotation": f"100%: {_get_abbreviated_number(funding_requested)}\n Requested Funding",
    #             },
    #         ],
    #         "annotation": f"\n\n\n\n{round(ratio * 100)}% ({_get_abbreviated_number(funding_received)}) of funding received.",  # noqa
    #         "plot_size": (10, 2.5),
    #     }
    #     _custom_title(
    #         "Received Funding vs Requested Funding",
    #         st.session_state["subtitle_size"],
    #         source="OCHA HPC Plans Summary API",
    #         date=year
    #     )
    #     _display_stackbar(numbers_values)


def display_cp_beneficiaries(selected_country: str):
    """Plot a grouped barchart related to funding"""
    year = st.session_state["selected-year"]
    selected_country = country_mapping(selected_country)

    _custom_title(
        "CP Beneficiaries vs CP Targeted",
        st.session_state["subtitle_size"],
        source="OCHA HPC Plans Summary API",
        date=f"{min(st.session_state['filter-years'])}-{year}"
    )

    df = st.session_state["all_pin_data"]
    df = df[(df["country"] == selected_country) & (df["year"] <= year)]
    df.reset_index(drop=True, inplace=True)

    df = df.groupby(['year', 'country'], as_index=False)[['cp_beneficiaries', 'cp_targeted']].sum()

    df.rename(
        columns={
            "cp_beneficiaries": "CP Beneficiaries",
            "cp_targeted": "CP Targeted"
        },
        inplace=True
    )

    if len(df):
        df_melted = df.melt(
            id_vars=["year"],
            value_vars=["CP Beneficiaries", "CP Targeted"],
            var_name="CP Type",
            value_name="cp_numbers",
        )

        df_melted["cp_numbers"] = df_melted["cp_numbers"].apply(lambda x: round(x / 1_000_000, 2))

        fig = px.bar(
            df_melted,
            x="year",
            y="cp_numbers",
            color="CP Type",
            color_discrete_map={
                "CP Beneficiaries": "#D6E9DF",
                "CP Targeted": "#B1DBC3"
            },
            barmode="group",
            labels={"cp_numbers": "Total numbers(in millions)", "year": "Year"},
            text="cp_numbers",
            text_auto=True
        )
        fig.update_traces(
            texttemplate='%{y:,} million',
            textposition='outside',
            textfont=dict(size=20)
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, height=320)
    else:
        st.write("No CP Beneficiaries and Targeted data available.")

    # if len(df) > 0:
    #     cp_beneficiaries = df["cp_beneficiaries"].iat[0]
    #     cp_targeted = df["cp_targeted"].iat[0]

    #     if pd.isna(cp_beneficiaries):
    #         cp_beneficiaries = 0
    #     if pd.isna(cp_targeted):
    #         cp_targeted = 0

    #     ratio = cp_beneficiaries / cp_targeted if cp_targeted else 0

    #     numbers_values = {
    #         "title": "CP Beneficiaries vs CP Targeted",
    #         "original_numbers": [
    #             {
    #                 "value": cp_beneficiaries,
    #                 "label": f"CP Beneficiaries {_get_abbreviated_number(cp_beneficiaries)}",
    #                 "color": "#9FD5B5",
    #                 "number_annotation": f"{round(ratio * 100)}%",
    #             },
    #             {
    #                 "value": cp_targeted,
    #                 "label": "CP Targeted",
    #                 "color": "#d3d3d3",
    #                 "number_annotation": f"100%: {_get_abbreviated_number(cp_targeted)}\n CP Targeted.",
    #             },
    #         ],
    #         "annotation": f"\n\n\n\n{round(ratio * 100)}% ({_get_abbreviated_number(cp_beneficiaries)}) of CP Beneficiaries recorded.",  # noqa
    #         "plot_size": (10, 2.5),
    #     }
    #     _custom_title(
    #         "CP Beneficiaries vs CP Targeted",
    #         st.session_state["subtitle_size"],
    #         source="OCHA HPC Plans Summary API",
    #         date=year
    #     )
    #     _display_stackbar(numbers_values)


def _get_country_wise_pin_data(df: pd.DataFrame):
    """
    Extracts and returns country-wise PIN (People in Need) data for the specified year from the provided DataFrame.

    Args:
    - df (pd.DataFrame): DataFrame containing columns 'country',
      'year', 'children_in_need', 'targeted_children', and 'tot_pop_in_need'.

    Returns:
    - pd.DataFrame: Filtered DataFrame with columns:
    - 'country': Country name.
    - 'year': Year of data (filtered for 2024).
    - 'children_in_need': Number of children in need.
    - 'targeted_children': Number of targeted children.
    - 'tot_pop_in_need': Total population in need.

    Operation:
    1. Copies and filters the input DataFrame 'df' to include data only for the year 2024.
    2. Filters rows based on non-null values in columns related to children in need,
       targeted children, and total population in need.
    3. Sorts and resets the index of the resulting DataFrame 'all_pin_data' for clarity and consistency.
    4. Selects relevant columns ('country', 'year', 'children_in_need',
       'targeted_children', 'tot_pop_in_need') from the filtered data.
    """
    # country_wise_results = pd.DataFrame()

    # number_cols = [
    #     "children_in_need",
    #     "targeted_children",
    #     "tot_pop_in_need",
    # ]

    all_pin_data = df.copy()
    if "selected-year" not in st.session_state:
        st.session_state["selected-year"] = 2024
    all_pin_data = all_pin_data[all_pin_data["year"] == st.session_state["selected-year"]]
    all_pin_data = (
        all_pin_data[
            (~all_pin_data["children_in_need"].isna())
            | (~all_pin_data["targeted_children"].isna())
            | (~all_pin_data["tot_pop_in_need"].isna())
        ]
        .sort_values(by=["country", "year"])
        .reset_index(drop=True)
    )

    all_pin_data = all_pin_data[
        ["country", "year", "children_in_need", "targeted_children", "tot_pop_in_need"]
    ]

    return all_pin_data


def _get_country_wise_children_in_need_data(df: pd.DataFrame):
    """
    Calculates and returns country-wise data on children in need based on the provided DataFrame.

    Args:
    - df (pd.DataFrame): DataFrame containing columns 'country', 'year', 'children_in_need', and 'tot_pop_in_need'.

    Returns:
    - pd.DataFrame: Country-wise results DataFrame with columns:
    - 'country': Country name.
    - 'children_in_need': Total number of children in need in the latest year available.
    - 'proportion_children_in_need': Proportion of children in need to
       total population in need, rounded to two decimal places.
    - 'year': Year corresponding to the latest data entry for children in need.

    Operation:
    1. Extracts relevant columns ('country', 'year', 'children_in_need', 'tot_pop_in_need')
       from the input DataFrame.
    2. Iterates over each unique country to calculate statistics:
    - Selects the most recent data entry for each country based on year.
    - Computes the proportion of children in need to total population in need.
    3. Constructs a new DataFrame 'country_wise_results' with calculated values for each country.
    """
    country_wise_results = pd.DataFrame()

    all_pin_data = df.copy()[
        ["country", "year", "children_in_need", "tot_pop_in_need"]
    ].dropna()

    for one_country in all_pin_data.country.unique():
        one_col_one_country_df = all_pin_data[
            (all_pin_data["country"] == one_country) &
            (all_pin_data["year"] == st.session_state["selected-year"])
        ]
        one_col_one_country_df.reset_index(drop=True, inplace=True)

        if one_col_one_country_df.empty:
            continue
        # one_col_one_country_df = one_country_df.sort_values(
        #     "year", ascending=False
        # ).iloc[0] # latest year

        results_one_country = {"country": one_country}

        results_one_col = round(
            one_col_one_country_df["children_in_need"][0]
            / one_col_one_country_df["tot_pop_in_need"][0],
            2,
        )

        results_one_country["children_in_need"] = int(
            one_col_one_country_df["children_in_need"][0]
        )
        results_one_country["proportion_children_in_need"] = results_one_col
        results_one_country["year"] = one_col_one_country_df["year"][0]

        country_wise_results = country_wise_results._append(
            results_one_country, ignore_index=True
        )

    return country_wise_results


def _display_pin_stackbar(selected_country: str):
    """
    Displays a stacked bar chart visualizing information about children in need for the selected country.

    Operation:
    1. Retrieves country-specific data related to children in need from session state.
    2. Computes percentages and formats numbers for targeted children, children in need, and total people in need.
    3. Displays a stacked bar chart with annotations representing the proportions of
       targeted children, children in need, and total people in need.
    4. Includes a title and source annotation for the visualization.
    """
    country_informations = st.session_state["country_wise_pin_data"]
    country_specific_df = country_informations[
        country_informations["country"] == selected_country
    ]
    country_specific_df.reset_index(drop=True, inplace=True)

    if len(country_specific_df) > 0:
        children_in_need = country_specific_df["children_in_need"].values[0]
        children_targeted = country_specific_df["targeted_children"].values[0]
        total_people_in_need = country_specific_df["tot_pop_in_need"].values[0]

        if pd.isna(children_in_need):
            children_in_need = 0
        if pd.isna(children_targeted):
            children_targeted = 0
        if pd.isna(total_people_in_need):
            total_people_in_need = 0

        ratio_children_targeted_total_people = (
            round(children_targeted / total_people_in_need * 100)
            if children_targeted and total_people_in_need else 0
        )
        ratio_children_in_need_total_people_in_need = (
            round(children_in_need / total_people_in_need * 100)
            if children_in_need and total_people_in_need else 0
        )

        numbers_values = {
            "title": "Child Protection Caseload (in Need)",
            "original_numbers": [
                {
                    "value": children_targeted,
                    "label": f"CP\nCaseload\ntargeted\n{_get_abbreviated_number(children_targeted)}",
                    "color": "#9FD5B5",
                    "number_annotation": f"{ratio_children_targeted_total_people}%",
                },
                {
                    "value": children_in_need,
                    "label": f"CP Caseload\nin Need\n{_get_abbreviated_number(children_in_need)}",
                    "color": "#90AF95",
                    "number_annotation": f"{ratio_children_in_need_total_people_in_need}%",
                },
                {
                    "value": total_people_in_need,
                    "label": "Other in Need",
                    "color": "#d3d3d3",
                    "number_annotation": f"100%: {_get_abbreviated_number(total_people_in_need)}\nPeople in need",
                },
            ],
            "annotation": f"\n\n\n\n{ratio_children_in_need_total_people_in_need}% ({_get_abbreviated_number(children_in_need)}) of people are in Need of CP Services. ",  # noqa
            "plot_size": (10, 1.2),
        }
        _custom_title(
            "Child Protection Caseload",
            st.session_state["subtitle_size"],
            source="OCHA HPC Plans Summary API",
            date=st.session_state["selected-year"],
        )
        if (
            total_people_in_need
            and ratio_children_targeted_total_people
            and ratio_children_in_need_total_people_in_need
        ):
            _display_stackbar(numbers_values)
        else:
            st.markdown("Not enough or valid data available to create the plot.")
