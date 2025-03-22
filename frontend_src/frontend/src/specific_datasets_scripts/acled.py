import os

import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.src.utils.utils_functions import _custom_title
from frontend.src.visualizations.maps_creation import \
    _display_map_img  # _create_map_placeholder_plotly,


def _load_acled_data():

    number_of_events_targeting_civilians_countries_mapping = {
        #"Central African Republic": "CAR",
        "Democratic Republic of Congo": "Congo DRC",
        "eSwatini": "Eswatini",
        "Turkey": "Türkiye",
    }
    number_of_events_targeting_civilians_df_path = os.path.join(
        st.session_state["tabular_data_data_path"],
        "acled",
        "number_events_evolution.csv",
    )

    number_of_events_targeting_civilians_df = pd.read_csv(
        number_of_events_targeting_civilians_df_path
    )

    number_of_events_targeting_civilians_df["country"] = (
        number_of_events_targeting_civilians_df["country"].replace(
            number_of_events_targeting_civilians_countries_mapping
        )
    )

    st.session_state["number_of_events_targeting_civilians_df"] = (
        number_of_events_targeting_civilians_df
    )

    st.session_state["individual_events_targetting_civilians"] = pd.read_csv(
        os.path.join(
            st.session_state["tabular_data_data_path"],
            "acled",
            "individual_events_targetting_civilians_new.csv",
        )
    )
    st.session_state["individual_events_targetting_civilians"]["country"] = (
        st.session_state["individual_events_targetting_civilians"]["country"].replace(
            number_of_events_targeting_civilians_countries_mapping
        )
    )
    st.session_state["acled_last_updated"] = st.session_state[
        "number_of_events_targeting_civilians_df"
    ]["year"].max()


@st.fragment
def _display_number_of_events_targetting_civilians(selected_country: str):
    """
    Displays a line chart showing the number of events targeting civilians over the years for the selected country.

    Operation:
    1. Retrieves the dataframe containing the number of events targeting civilians for the selected country.
    2. Filters and sorts the dataframe based on the selected country and year.
    3. If data is available, sets a custom title for the chart.
    4. Constructs a line chart using Altair to visualize the number of events over the years.
    """

    one_country_number_of_events_targeting_civilians = st.session_state[
        "number_of_events_targeting_civilians_df"
    ][
        (st.session_state["number_of_events_targeting_civilians_df"].country == selected_country)
        # & (st.session_state["number_of_events_targeting_civilians_df"].year <= st.session_state["selected-year"])
    ].copy()
    # st.dataframe(one_country_number_of_events_targeting_civilians)

    one_country_number_of_events_targeting_civilians.reset_index(drop=True, inplace=True)

    one_country_number_of_events_targeting_civilians['year'] = one_country_number_of_events_targeting_civilians['year'].astype(int)

    if len(one_country_number_of_events_targeting_civilians) > 0:
        one_country_number_of_events_targeting_civilians.sort_values(by="year", inplace=True)
        _custom_title(
            f"Number of events affecting civilians in {selected_country}",
            margin_top=0,
            margin_bottom=20,
            font_size=st.session_state["subtitle_size"],
            source="ACLED",
            date=st.session_state["acled_last_updated"],
            #date=st.session_state['selected-year']
        )
        fig = px.line(
            one_country_number_of_events_targeting_civilians,
            x="year",  # Use the same 'year' column as x-axis
            y="Number of Events",  # Use the 'Number of Events' column as y-axis
            title="",
            labels={
                "year": "Year",
                "Number of Events": "Number of Events",
            },
        )
        fig.update_traces(line=dict(color="#86789C"))

        fig.update_layout(
            title_font=dict(size=1),  # Bigger title font
            xaxis_title_font=dict(size=18),  # Bigger x-axis title font
            yaxis_title_font=dict(size=18),  # Bigger y-axis title font
            xaxis_tickfont=dict(size=14),  # Bigger x-axis tick labels
            yaxis_tickfont=dict(size=14),  # Bigger y-axis tick labels
            legend_title_font=dict(size=16),  # Bigger legend title font
            legend_font=dict(size=14),  # Bigger legend text,
            margin=dict(t=50, b=50, l=50, r=50)
            # title=None
        )
        fig.update_xaxes(
            dtick=1,  # Show every year
            range=[
                min(one_country_number_of_events_targeting_civilians['year']),
                max(one_country_number_of_events_targeting_civilians['year'])
            ]  # Ensure the x-axis covers all years
        )
        st.plotly_chart(fig, use_container_width=True)


@st.fragment
def _display_acled_map_data(selected_country: str):
    """
    Displays a map of protection-related events filtered by event type and date range.

    Args:
    - None

    Operation:
    1. Sets a custom title for the map section displaying protection-related events.
    2. Constructs the path to the CSV file containing protection-related events data specific to the selected country.
    3. Checks if the events dataset for the selected country is already loaded in session state. If not, loads and stores it.
    4. Creates a dropdown to select event types from the loaded events dataset.
    5. Creates a dropdown to select a past date range (3 months, 6 months, or 1 year).
    6. Based on the selected past date range, calculates the start date for filtering events data.
    7. Filters the displayed DataFrame (`displayed_df`) based on the selected event type and date range.
    8. Displays the count of events and their characteristics (event type, date range, total events).
    9. Calls `_display_map_img` to visualize the filtered protection-related events on a map using PolyDeck (PDK).
    """
    _custom_title(
        "Protection-Related Events",
        st.session_state["subtitle_size"],
        source="ACLED",
        date=st.session_state["acled_last_updated"],
    )

    if f"events_dataset_{selected_country}" not in st.session_state:

        st.session_state[f"events_dataset_{selected_country}"] = st.session_state[
            "individual_events_targetting_civilians"
        ][
            st.session_state["individual_events_targetting_civilians"].country
            == selected_country
        ]
        if len(st.session_state[f"events_dataset_{selected_country}"]) == 0:
            st.markdown(
                f"No information available for the protection-related-events for {selected_country}"
            )
            return
        st.session_state["events_list"] = (
            st.session_state[f"events_dataset_{selected_country}"]["event_type"]
            .unique()
            .tolist()
        )
        st.session_state["events_list"] = ["All"] + sorted(
            st.session_state["events_list"]
        )

    displayed_df = st.session_state[f"events_dataset_{selected_country}"].copy()
    displayed_df["event_date"] = pd.to_datetime(displayed_df["event_date"])

    # displayed_df = displayed_df[
    #     displayed_df["event_date"].dt.year == st.session_state["selected-year"]
    # ]

    if displayed_df.empty:
        st.markdown(
            f"No information available for the year {st.session_state['acled_last_updated']}"
        )
        return

    with st.container():
        filter_col, date_range_col = st.columns([0.5, 0.5])

        with filter_col:

            event_type = st.selectbox(
                "Select Event Type",
                st.session_state["events_list"],
            )
        with date_range_col:
            past_date = st.selectbox(
                "Select Past Date",
                ["Past 3 months", "Past 6 months", "Past year", "Past 2 years"],
            )

            today_date = pd.to_datetime("today")
            if past_date == "Past 3 months":
                start_date = today_date - pd.DateOffset(months=3)
            elif past_date == "Past 6 months":
                start_date = today_date - pd.DateOffset(months=6)
            elif past_date == "Past year":
                start_date = today_date - pd.DateOffset(months=12)
            elif past_date == "Past 2 years":
                start_date = today_date - pd.DateOffset(months=24)

    displayed_df = displayed_df[displayed_df["event_date"] >= start_date]
    if event_type != "All":
        displayed_df = displayed_df[displayed_df["event_type"] == event_type]

    event_text = "All Events" if event_type == "All" else event_type

    st.markdown(
        f"**Events Map ({event_text}, {past_date}, {displayed_df.shape[0]} total events)**"
    )
    # Add more content here
    _display_map_img(displayed_df, selected_country)
