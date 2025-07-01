import os
import re

import pandas as pd
import streamlit as st

from frontend.src.utils.utils_functions import (
    _add_blank_space,
    _convert_to_datetime,
    _custom_title,
    _display_bullet_point_as_highlighted_text,
)

yes_color = "#95C651"
no_color = "#86789C"
no_info_color = "#AEA9A5"


def _replace_special_chars(input_string):
    # Define the pattern to match special characters
    pattern = re.compile(r"[^a-zA-Z0-9]")  # Matches anything except letters and numbers

    # Replace special characters with "-"
    replaced_string = re.sub(pattern, "-", input_string)

    return replaced_string


def _load_country_summaries_indicators(data_path: os.PathLike):
    """
    Function to load the country summaries indicators
    """
    country_summaries_dataset = pd.read_excel(data_path).ffill()
    country_summaries_dataset["Formatted Submitted Date"] = country_summaries_dataset["Submitted Date"].apply(
        _convert_to_datetime
    )
    displayed_indicators = country_summaries_dataset.Tag.unique()
    return country_summaries_dataset, displayed_indicators


def _display_legend_box(
    text: str,
    color: str,
    max_width: int = 160,
    height: int = 80,
):
    """
    Displays a legend box with text and a colored bar based on provided parameters.

    Args:
    1. text (str): Text content to display within the legend box.
    2. color (str): Color code for the colored bar.
    3. max_width (int, optional): Maximum width of the legend box in pixels. Default is 160.
    4. height (int, optional): Height of the legend box in pixels. Default is 80.

    Operation:
    1. Constructs HTML content for displaying a legend box using provided `text` and `color`.
    2. Sets up flexbox layout for proper alignment and spacing.
    3. Uses CSS to style the text content within the legend box, ensuring it is centered and wraps correctly.
    4. Creates a colored bar within the legend box to indicate the specified `color`.
    5. Renders the constructed HTML content to display the legend box with text and color.

    """
    box_html = f"""
    <div style='
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;  # This aligns the child elements to the bottom
        margin: 5px 0;
    '>
        <div style='
            width: 100%;  # Use 100% width for the spacer to push content to bottom
            height: 0;  # No height needed, it just acts as a spacer
        '></div>
        <p style='
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            font-size: 16px;
            margin: 25px 0 0 0;
            max-width: {max_width}px;
            min-height: {height}px;
            max-height: {height}px;
            word-break: break-word;
            text-align: center;
        '>{text}</p>
        <div style='
            width: {max_width}px;
            height: 10px;
            background-color: {color};
        '></div>
    </div>
    """

    st.markdown(box_html, unsafe_allow_html=True)


def _display_indicator_box(
    indicator: str,
    color: str,
    max_width: int = 160,
    height: int = 80,
):
    """
    Displays an indicator box with a colored bar based on provided parameters.

    Args:
    1. indicator (str): Name of the indicator to display.
    2. color (str): Color code for the indicator box.
    3. max_width (int, optional): Maximum width of the indicator box in pixels. Default is 160.
    4. height (int, optional): Height of the indicator box in pixels. Default is 80.

    Operation:
    1. Converts the `indicator` string to a safe format for HTML/JS usage using `_replace_special_chars`.
    2. Shortens specific indicator names for display clarity.
    3. Applies Markdown style adjustments to the indicator box.
    4. Creates a placeholder span element to apply CSS styling.
    5. Displays the shortened indicator name centered within the box using HTML and Markdown.
    6. Generates HTML code for the colored indicator box based on the provided `color`.
    7. Renders the HTML content to display the indicator box with the specified color.

    """
    with st.container():
        # Replace special characters in the indicator for safe HTML/JS usage
        no_special_character_indicator = _replace_special_chars(indicator)
        short_name_indicator = indicator.replace("Armed forces", "AF").replace("Armed Groups", "AG")

        # Markdown style adjustments for the indicator box
        st.markdown(
            f"""
            <style>.element-container:has(#indicator_{no_special_character_indicator})"""
            + """ + div {
                color: "black";
                border-radius: 0%;
                height: 4em;
                width: 10em;
                display: flex;
                border: 0px solid #4F8BF9;
                margin: 0px 0px 0px 0px;
            }</style>
            """,
            unsafe_allow_html=True,
        )

        # Placeholder span to style using CSS
        st.markdown(
            f'<span id="indicator_{no_special_character_indicator}"></span>',
            unsafe_allow_html=True,
        )

        # Display the indicator name directly as markdown and centered
        st.markdown(
            f"<p style='text-align: center;'>{short_name_indicator}</p>",
            unsafe_allow_html=True,
        )

        # HTML for the color box
        box_html = f"""
        <div style='
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            margin: 5px 0;
            cursor: default;  # Makes the div non-clickable
        '>
            <div style='
                width: 100%;
                height: 0;
            '></div>
            <div style='
                width: {max_width}px;
                height: 20px;
                background-color: {color};
            '></div>
        </div>
        """
        # Render the HTML content with the indicator box
        st.markdown(box_html, unsafe_allow_html=True)


def _get_color(input_text: str) -> str:
    if input_text == "No Information Available":
        displayed_color = no_info_color
    elif input_text == "Law Available Within the Legal Framework":
        displayed_color = yes_color
    else:
        displayed_color = no_color
    return displayed_color


def _display_one_box_results(country_summaries_dataset, one_indicator):
    """
    Displays results for a single indicator box based on provided country summaries dataset.

    Args:
    - country_summaries_dataset (pd.DataFrame): DataFrame containing country summaries data.
    - one_indicator (str): Indicator tag to display results for.

    Operation:
    1. Checks if `one_indicator` exists in `displayed_indicators`.
    2. Retrieves the summary of `one_indicator` from `country_summaries_dataset`.
    3. Checks if the summary contains keywords such as 'law', 'article', or 'decree'
       to determine the indicator box color using `_display_indicator_box`.
    4. If `one_indicator` is not in `displayed_indicators`, displays the indicator
       box with a color indicating 'NOT AVAILABLE'.

    """
    one_indicator_results = country_summaries_dataset[country_summaries_dataset["Indicator"] == one_indicator][
        "Laws Summary"
    ].values[0]

    displayed_color = _get_color(one_indicator_results)

    _display_indicator_box(one_indicator.replace("Chid", "Child"), displayed_color)

    # if one_indicator in displayed_indicators:
    #     summary_one_indicator = country_summaries_dataset[
    #         country_summaries_dataset["Tag"] == one_indicator
    #     ]["Summary"].values[0]
    #     if any(
    #         [kw in summary_one_indicator.lower() for kw in ["law", "article", "decree"]]
    #     ):
    #         _display_indicator_box(one_indicator, yes_color)
    #     else:
    #         _display_indicator_box(one_indicator, no_color)

    # else:
    #     _display_indicator_box(one_indicator, no_info_color)


def _display_legal_framework_indicator_boxes(
    country_summaries_dataset: pd.DataFrame,
    selected_country: str,
    display_all_tags: bool = True,
):
    """
    Displays indicator boxes related to legal frameworks and rule of law based
    on provided country summaries dataset.

    Args:
    - country_summaries_dataset (pd.DataFrame): DataFrame containing country summaries data.
    - displayed_indicators (list[str]): List of indicators to display within the legal framework boxes.
    - display_all_tags (bool, optional): Flag indicating whether to display all legal framework
      tags or only specific ones. Default is True.

    Operation:
    1. Sets up a Streamlit (`st`) container for displaying the legal framework indicators.
    2. Displays a custom title for the "Legal Framework & Rule of Law" section, with an optional
       additional text pointing to more information.
    3. Displays legend boxes for indicating "YES", "NO", and "NOT AVAILABLE" statuses
       using `_display_legend_box` function.
    4. Iterates through legal framework tags and their respective indicators stored
       in `st.session_state["legal_framework_indicators"]`.
    5. If `display_all_tags` is True or if the tag name matches "Action Plans and laws",
       displays each indicator using `_display_one_box_results`.

    Notes:
    - Requires Streamlit (`st`) for displaying content.
    - Utilizes internal functions like `_custom_title`, `_display_legend_box`, and
      `_display_one_box_results` for layout and visualization.

    """
    st.markdown("")

    with st.container():
        (
            title_col,
            _,
            yes_col,
            _,
            no_col,
            _,
            no_infos_col,
            _,
            # detailed_results_col,
            # _,
        ) = st.columns([0.35, 0.1, 0.1, 0.01, 0.1, 0.01, 0.2, 0.1])
        with title_col:
            added_text = (
                "For more information, see the 'LEGAL FRAMEWORK' tab of the dashboard." if not display_all_tags else ""
            )
            _custom_title(
                "Legal Framework & Rule of Law",
                st.session_state["subtitle_size"],
                source="OHCHR, UN Treaty Bodies Dataset, Committee on the Rights of the Child, State Parties Reporting",
                date="Last update date: " + st.session_state[f"date_ohchr_{selected_country}"],
                additional_text=added_text,
            )
        with yes_col:
            _display_legend_box("YES ", yes_color, max_width=100, height=40)
        with no_col:
            _display_legend_box("NO ", no_color, max_width=100, height=40)
        with no_infos_col:
            _display_legend_box("NOT AVAILABLE ", no_info_color, max_width=100, height=40)

    for tag_id, (tagname, tag_indicators) in enumerate(st.session_state["legal_framework_indicators"].items()):
        if display_all_tags:
            _add_blank_space(1)
            _custom_title(f"{tag_id + 1}) {tagname}", 20)
        if display_all_tags or (tagname.strip() == "Action Plans and laws"):
            shown_columns = st.columns([1, 0.02, 1, 0.02, 1, 0.02, 1, 0.02, 1, 0.02, 1, 0.02, 1])
            for indicator_id, one_indicator in enumerate(tag_indicators):
                # display rows and columns
                nb = (2 * indicator_id) % 12
                with shown_columns[nb].container():
                    _display_one_box_results(
                        country_summaries_dataset,
                        one_indicator,
                    )


def _display_results_one_indicator(country_summaries_datset: pd.DataFrame, one_indicator: str):
    """
    Displays results for a specific indicator in a country summaries dataset.

    Args:
    - country_summaries_datset (pd.DataFrame): DataFrame containing country summaries data.
    - one_indicator (str): Specific indicator tag to display results for.

    Operation:
    1. Filters the `country_summaries_datset` DataFrame to retrieve entries matching the `one_indicator`.
    2. Sorts the filtered DataFrame based on the 'Formatted Submitted Date' in descending order.
    3. Retrieves the summary of the most recent entry for the specified indicator.
    4. Retrieves relevant details such as text snippets, document title,
       publishing date, and URL for articles related to the indicator.
    5. Displays a custom title for the indicator section.
    6. Displays the summary of the most recent entry in one column and lists relevant articles
       with their titles, dates, and URLs in another column.
    """
    df_one_indicator = country_summaries_datset[
        country_summaries_datset["Indicator"] == one_indicator
    ]  # .sort_values("Formatted Submitted Date", ascending=False)

    one_indicator_summary = df_one_indicator["General Summary"].values[0]

    one_indicator_relevant_text = df_one_indicator["Extracted Infos"]
    one_indicator_doc_title = df_one_indicator["Title"]
    one_indicator_publishing_date = df_one_indicator["Submitted Date"]
    one_indicator_url = df_one_indicator["doc_link"]
    n_articles = len(one_indicator_relevant_text)

    laws_summary = df_one_indicator["Laws Summary"].values
    if len(laws_summary) == 0:
        color = no_info_color
    else:
        color = _get_color(laws_summary[0])

    _display_bullet_point_as_highlighted_text(one_indicator.replace("Chid", "Child"), color)
    if one_indicator_doc_title.iloc[0] == "-":
        st.markdown("No information extracted for this indicator.")
    else:
        summary_col, _, original_doc_col = st.columns([0.65, 0.02, 0.33])
        with summary_col:
            st.markdown(one_indicator_summary)
        with original_doc_col:
            with st.container(height=200):
                for i in range(n_articles):
                    st.markdown(
                        f"""[{one_indicator_doc_title.iloc[i]}]({one_indicator_url.iloc[i]}) ({one_indicator_publishing_date.iloc[i]})"""  # noqa
                    )


@st.fragment
def country_wise_legal_framework(selected_country: str, display_detailed_results: bool):
    """
    Displays country-specific legal framework and rule of law information based on selected country.

    Args:
    - display_detailed_results (bool): Flag indicating whether to display detailed results for legal framework indicators.

    Operation:
    1. Checks if the path to the legal framework report for the selected country exists in the session state.
    2. Constructs the path to the legal framework report if it does not exist.
    3. If the legal framework report does not exist, displays a custom title indicating no information available and returns.
    4. Checks if the country summaries dataset and displayed indicators are loaded in the session state.
    5. Loads the country summaries dataset and displayed indicators from the legal framework report if not already loaded.
    6. Sets up a Streamlit container and displays legal framework indicator boxes
       using `_display_legal_framework_indicator_boxes`.
    7. If `display_detailed_results` is True, displays detailed results for each displayed indicator
       using `_display_results_one_indicator`.

    """
    if f"legal_framework_summaries_country_path_{selected_country}" not in st.session_state:
        st.session_state[f"legal_framework_summaries_country_path_{selected_country}"] = os.path.join(
            st.session_state["legal_framework_summaries_data_path"],
            f"{selected_country}.xlsx",
        )

    if not os.path.exists(st.session_state[f"legal_framework_summaries_country_path_{selected_country}"]):
        _custom_title(
            "Legal Framework & Rule of Law",
            st.session_state["subtitle_size"],
            source="OHCHR",
            # date=st.session_state[f"date_ohchr_{selected_country}"],
        )
        st.markdown(f"No information available for the legal framework for {selected_country}")
        return

    if f"country_summaries_dataset_{selected_country}" not in st.session_state:
        country_summaries_dataset, displayed_indicators = _load_country_summaries_indicators(
            st.session_state[f"legal_framework_summaries_country_path_{selected_country}"]
        )
        st.session_state[f"country_summaries_dataset_{selected_country}"] = country_summaries_dataset

        st.session_state[f"date_ohchr_{selected_country}"] = (
            pd.to_datetime(
                country_summaries_dataset[country_summaries_dataset["Submitted Date"] != "-"]["Submitted Date"],
                format="%d %b %Y",
            )
            .max()
            .strftime("%b %Y")
        )

    with st.container():
        _display_legal_framework_indicator_boxes(
            st.session_state[f"country_summaries_dataset_{selected_country}"],
            selected_country,
            display_all_tags=display_detailed_results,
        )

    if display_detailed_results:
        st.write("")
        _custom_title("Legal Framework Detailed Results", st.session_state["subtitle_size"])
        st.write("")

        for tag_id, (tagname, tag_indicators) in enumerate(st.session_state["legal_framework_indicators"].items()):
            _custom_title(f"{tag_id + 1}) {tagname}", st.session_state["subsubtitle_size"])

            for one_indicator in tag_indicators:
                _display_results_one_indicator(
                    st.session_state[f"country_summaries_dataset_{selected_country}"],
                    one_indicator,
                )
