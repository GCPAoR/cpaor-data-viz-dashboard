import streamlit as st

from frontend.src.utils.utils_functions import (
    _add_blank_space,
    _custom_title,
    _display_bullet_point_as_highlighted_text,
    _load_protection_indicators_data,
)


@st.fragment
def _display_main_summary(selected_country: str, display_evidence: bool = True):
    """
    Displays the main summary and optionally the evidence for protection data related to a selected country.

    Args:
    - display_evidence (bool, optional): Whether to display evidence sources along with the main summary. Defaults to True.

    Operation:
    1. Retrieves the general protection summary data specific to the selected country.
    2. Checks if data is available; if not, displays a message indicating no information.
    3. Displays the main summary text.
    4. If `display_evidence` is True, also presents the evidence sources for the main summary.
    """

    general_summary_df = st.session_state[f"protection_df_{selected_country}"][
        st.session_state[f"protection_df_{selected_country}"]["Breakdown Column"] == "1 - General Summary"
    ]
    if len(general_summary_df) == 0:
        st.markdown(f"No information available for the protection summary for {selected_country}")
        return
    general_summary_df = general_summary_df.drop_duplicates(subset="Source Original Text", keep="first").reset_index()
    main_statement = general_summary_df["Generated Text"].values[0]

    with st.container():
        if display_evidence:
            statement_col, _, evidence_col = st.columns([0.4, 0.02, 0.58])
            with statement_col:
                _custom_title("Main Summary", font_size=st.session_state["subsubtitle_size"])
                st.write(main_statement)
            with evidence_col:
                _custom_title("Evidence", font_size=st.session_state["subsubtitle_size"])
                evidence_text = ""
                for i, (_, row) in enumerate(general_summary_df.iterrows()):
                    relevant_text = f"""{i + 1}) {row["Source Original Text"]}"""
                    source = f""" ([{row["Source Name"]}]({row["Source Link"]}) {row["Source Date"]})"""

                    evidence_text += f"""{relevant_text}{source}\n\n"""

                with st.container(height=250):
                    st.markdown(evidence_text, unsafe_allow_html=True)
        else:
            st.write(main_statement)


@st.fragment
def _display_detailed_summaries(selected_country: str, breakdown: str):
    """
    Displays detailed summaries by a specified breakdown column.

    Args:
    - breakdown (str): The column name used to break down the detailed summaries.

    Operation:
    1. Displays detailed summaries organized by the specified breakdown column.
    2. Filters and displays data specific to the selected country.
    3. Formats and presents summaries along with their corresponding sources.
    """
    _custom_title(
        f"Detailed Summaries by {breakdown}",
        font_size=st.session_state["subtitle_size"],
    )

    detailed_summary_df = st.session_state[f"protection_df_{selected_country}"][
        st.session_state[f"protection_df_{selected_country}"]["Breakdown Column"] == breakdown
    ]

    values = detailed_summary_df["Value"].unique()
    for one_value in values:
        _custom_title(one_value, font_size=st.session_state["subsubtitle_size"])
        df_one_value = detailed_summary_df[detailed_summary_df["Value"] == one_value]
        df_one_value = df_one_value.drop_duplicates(subset=["Source Original Text"], keep="first").reset_index()
        with st.container():
            statement_col, _, evidence_col = st.columns([0.4, 0.02, 0.58])
            with statement_col:
                st.write(df_one_value["Generated Text"].values[0])
            with evidence_col:
                evidence_text = ""
                for i, (_, row) in enumerate(df_one_value.iterrows()):
                    relevant_text = f"""{i + 1}) {row["Source Original Text"]}"""
                    source = f""" ([{row["Source Name"]}]({row["Source Link"]}) {row["Source Date"]})"""

                    evidence_text += f"""{relevant_text}{source}\n\n"""

                with st.container(height=250):
                    st.markdown(evidence_text, unsafe_allow_html=True)


@st.fragment
def _display_protection_data(selected_country: str):
    """
    Displays protection indicators and related summaries for the selected country.

    Operation:
    1. Displays the main title for protection indicators.
    2. Allows selection of a breakdown category.
    3. Displays the main summary for protection data.
    4. If a breakdown category is selected, displays detailed summaries for that category.
    """
    # _custom_title(
    #     "Protection Indicators",
    #     st.session_state["title_size"],
    # )
    breakdown = None

    with st.container():
        _custom_title(
            f"{selected_country} Protection Concerns",
            font_size=40,
            source="ACAPS, Protection Indicators",
            date=st.session_state[f"protection_df_max_date_{selected_country}"],
        )

    indicator_list = [
        i
        for i, breakdown in enumerate(st.session_state[f"possible_breakdowns_{selected_country}"])
        if breakdown == "Indicator"
    ]
    indicator_id = indicator_list[0] if indicator_list else 0

    brekdown_col, _ = st.columns([0.3, 0.7])
    if st.session_state[f"possible_breakdowns_{selected_country}"]:
        with brekdown_col:
            breakdown = st.selectbox(
                "Breakdown",
                st.session_state[f"possible_breakdowns_{selected_country}"],
                index=indicator_id,
                key="breakdown",
            )

    _display_main_summary(selected_country)
    _add_blank_space(2)

    # for breakdown in st.session_state[f"possible_breakdowns_{selected_country}"]:
    if breakdown:
        _display_detailed_summaries(selected_country, breakdown)
    _add_blank_space(2)


@st.fragment
def _display_specific_protection_indicators(selected_country: str):
    """
    Displays summaries of specific protection indicators related to children for the selected country.

    Args:
    - child_related_tags (List[str]): List of specific protection indicators related to children to display summaries for.

    Operation:
    1. Loads protection data specific to the selected country.
    2. Retrieves and filters protection data based on specified child-related tags.
    3. Displays summaries for each specified protection indicator.
    4. If no information is available for a tag, it indicates so with a markdown message.
    """
    child_related_tags = [
        # "Abduction, kidnapping, enforced disappearances, or cases of missing people",
        # "Access to asylum process after entry",
        # "Arbitrary denial or deprivation of nationality or statelessness",
        # "Arbitrary or unlawful arrest and/or detention",
        "Child labour",
        "Child trafficking, abduction or sale",
        "Children being associated with armed forces or armed groups",
        "Constraints on children’s education",
        # "Extrajudicial executions, deliberate or indiscriminate attacks on civilians, and other unlawful killings",
        # "Femicide and honour killings",
        "Forced and/or early marriage",
        # "Forced eviction from property",
        "Forced family separation",
        # "Forced labour or slavery",
        # "Forced recruitment into armed forces or groups",
        # "Human smuggling",
        # "Human trafficking",
        # "Refoulement/pushbacks/forced returns",
        # "Sexual and gender-based violence",
        # "Torture or inhumane, cruel, or degrading treatment",
        # "Violence/abuse/intolerance towards individuals based on their sexual orientation, gender identity, and gender expression (SOGIE)"  # noqa
    ]
    _load_protection_indicators_data(selected_country)
    by_indicators_country_protection_df = st.session_state[f"protection_df_{selected_country}"].copy()
    by_indicators_country_protection_df = by_indicators_country_protection_df[
        by_indicators_country_protection_df["Breakdown Column"] == "Indicator"
    ][["Value", "Generated Text"]].drop_duplicates()
    _custom_title(
        "Specific Protection Indicators Summaries",
        font_size=st.session_state["subtitle_size"],
        source="ACAPS, Protection Indicators",
        date=st.session_state[f"protection_df_max_date_{selected_country}"],
    )

    columns = st.columns(2)
    for i, tag in enumerate(child_related_tags):
        tag_df = by_indicators_country_protection_df[by_indicators_country_protection_df["Value"].str.contains(tag)]
        with columns[i % 2]:
            _display_bullet_point_as_highlighted_text(tag, background_color="#BFDA95")
            if len(tag_df) == 0:
                st.markdown(f"No information available for this tag for {selected_country}")
            else:
                st.markdown(tag_df.iloc[0]["Generated Text"].replace("  ", "\n"))
