import os
from datetime import datetime
from typing import List, Optional

import pandas as pd
import streamlit as st


def _load_countries_list():
    """
    Function to load the list of countries from the report_countries.csv file
    """
    return pd.read_csv(
        os.path.join(st.session_state["base_data_folder"], "report_countries.csv"),
        header=None,
        names=["country"],
    ).country.tolist()


def _convert_to_datetime(date_str: str):
    """
    Function to convert a string date to a datetime object
    """
    return datetime.strptime(date_str, "%d %b %Y") if date_str != "-" else "-"


def _flatten_list_of_lists(list_of_lists: List[List[str]]) -> List[str]:
    """
    Function to flatten a list of lists
    """
    return [item for sublist in list_of_lists for item in sublist]


def _add_commas(number: int):
    """
    Function to add commas to a number
    """
    return "{:,}".format(number)


def _load_protection_indicators_data(selected_country: str):
    """
    Function to load the protection data
    """

    if f"protection_df_{selected_country}" not in st.session_state:
        df_path = os.path.join(
            st.session_state["protection_data_path"],
            f"{selected_country}.csv",
        )
        if os.path.exists(df_path):
            st.session_state[f"protection_df_{selected_country}"] = pd.read_csv(df_path)

            st.session_state[f"protection_df_{selected_country}"]["Source Date"] = (
                pd.to_datetime(
                    st.session_state[f"protection_df_{selected_country}"]["Source Date"], format="mixed"
                )
            )

            st.session_state[f"possible_breakdowns_{selected_country}"] = [
                b
                for b in st.session_state[f"protection_df_{selected_country}"][
                    "Breakdown Column"
                ].unique()
                if b != "1 - General Summary"
            ]

            st.session_state[f"protection_df_max_date_{selected_country}"] = (
                pd.to_datetime(st.session_state[f"protection_df_{selected_country}"]["Source Date"], format="mixed")
                .max()
                .strftime("%m-%Y")
            )
        else:
            st.session_state[f"protection_df_{selected_country}"] = pd.DataFrame(
                columns=[
                    "Breakdown Column",
                    "Value",
                    "Generated Text",
                    "Source Original Text",
                    "Source Name",
                    "Source Link",
                    "Source Date",
                ]
            )
            st.session_state[f"possible_breakdowns_{selected_country}"] = []
            st.session_state[f"protection_df_max_date_{selected_country}"] = "-"


def _country_selection_filter(filter_name: str, disabled: Optional[bool]):
    """
    Function to display the country selection filter, save the selected country and load the protection data.
    """
    selected_country = st.selectbox(
        "Country",
        list(st.session_state["countries"].keys()),
        index=0,
        key=filter_name,
        disabled=disabled,
    )

    _load_protection_indicators_data(selected_country)
    return selected_country


def _show_header(text: str):
    with st.container():
        _custom_title(text, font_size=24)


def _add_source(source: str, margin_bottom: int):
    st.markdown(
        f"""<div style="margin-top: {-5}px; margin-bottom: {10 + margin_bottom}px; font-size: {14}px; color: black"> {source} </div>""",  # noqa
        unsafe_allow_html=True,
    )


def _custom_title(
    title: str,
    font_size: int = 20,
    margin_top: int = 0,
    margin_bottom: int = 0,
    source: str = None,
    date: str = None,
    additional_text: str = None,
):
    """
    Function to display a custom title with a source and a date and additional text if provided.
    """
    is_large_font = font_size == 30
    if is_large_font:
        text_transform = "text-transform: uppercase;"
        text_color = "color: dimgray;"
    else:
        text_transform = ""
        text_color = "color: black;"

    if is_large_font:
        st.markdown("**************************************************************")

    st.markdown(
        f"""
    <div style="margin-top: {margin_top}px; margin-bottom: 0px; font-size: {font_size}px; {text_color} font-weight: bold; {text_transform}">
        {title}
    </div>
    """,
        unsafe_allow_html=True,
    )
    if is_large_font:
        st.markdown("**************************************************************")

    txt = ""
    if source:
        txt += f"Source: {source}"
    if date:
        txt += f" ({date})"

    _add_source(txt, margin_bottom)

    if additional_text:
        _add_source(additional_text, margin_bottom)


def _get_percentage(number):
    return f"{round(number*100)}%"


def _add_blank_space(n_empty_lines: int):
    for _ in range(n_empty_lines):
        st.write("")


def _get_bullet_point_as_highlighted_text_display(
    text: str, background_color: str = "#D2E5B7", font_size: int = 16
):
    """
    Function to display a bullet point as highlighted markdown text
    """
    custom_css = f"""<div
        style="background-color: {background_color};
            border-radius: 0px;
            text-align: center;
            box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
            transition: 0.3s;
            display: inline-block;"
    >
        <p
            style="
                color: #333333;
                font-size: {font_size}px;
                margin: 7px;
                font-weight: bold;
            "
        >
            {text}
        </p>
    </div>"""
    return custom_css


def _display_bullet_point_as_highlighted_text(
    text: str, background_color: str = "#D2E5B7", font_size: int = 16
):
    """
    Function to display a bullet point as highlighted markdown text
    """
    custom_css = _get_bullet_point_as_highlighted_text_display(text, background_color, font_size)
    st.markdown(custom_css, unsafe_allow_html=True)
