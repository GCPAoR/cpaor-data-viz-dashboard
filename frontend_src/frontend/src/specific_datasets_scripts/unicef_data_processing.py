import os
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st
from frontend.src.utils.utils_functions import _add_blank_space, _custom_title

countries_mapping = {
    "Democratic Republic of the Congo": "Congo DRC",
    "Iran (Islamic Republic of)": "Iran",
    "State of Palestine": "Palestine",
    "Syrian Arab Republic": "Syria",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
}

sexes = ["_T", "F", "M"]
sex_to_gender = {"F": "Female", "M": "Male", "_T": "All Sexes"}

kept_columns = ["Geographic area", "Indicator", "TIME_PERIOD", "OBS_VALUE", "SEX"]

mortality_rate_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.CME_MRY15T19+CME_MRY1T4+CME_MRY5T24._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

nb_deprivations_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PV_CHLD_DPRV-AVG-S-HS._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

percentage_adults_think_physical_punishement_good_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PT_ADLT_PS_NEC._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

percentage_women_sexual_violence_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PT_F_18-29_SX-V_AGE-18._T+F+M?format=csv&includehistory=true&labels=both"  # noqa
percentage_men_sexual_violence_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PT_M_18-29_SX-V_AGE-18._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

young_women_married_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PT_F_20-24_MRD_U18_TND._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

children_detention_rate_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PT_CHLD_DN._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

children_residential_care_rate_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.PT_CHLD_RES-CARE._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

out_of_school_rate_adolescents_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.ED_ROFST_L3._T+F+M?format=csv&includehistory=true&labels=both"  # noqa
out_of_school_rate_children_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.ED_ROFST_L1_ADM._T+F+M?format=csv&includehistory=true&labels=both"  # noqa
out_of_school_rate_youth_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.ED_ROFST_L2._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

refugee_host_per_country_link = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/.MG_RFGS_CNTRY_ASYLM_PER1000._T+F+M?format=csv&includehistory=true&labels=both"  # noqa

st.session_state["mortality_rate_doc_path"] = os.path.join(
    st.session_state["tabular_data_data_path"],
    "unicef",
    "mortality_rate_df.csv",
    # "Mortality-rate-among-children-and-youth-age-5-to-24_2023-1.xlsx",
)


def _import_preprocess_df(link):
    """
    Fetches and preprocesses data from the specified CSV link.
    """
    df = pd.read_csv(link)[kept_columns]
    df["Geographic area"] = df["Geographic area"].replace(countries_mapping)
    df = df[df["Geographic area"].isin(st.session_state["countries"])]
    return df


def _import_merge_multiple_df(links):
    """
    Fetches and merges data from multiple CSV links into a single DataFrame.
    """
    return pd.concat([_import_preprocess_df(link) for link in links])


def _standard_unicef_data_import(
    selected_country, df_path: os.PathLike, df_links: List[str]
):
    """
    Fetches and preprocesses UNICEF data from the specified CSV file path and links.
    """
    if os.path.exists(df_path):
        df = pd.read_csv(df_path)
    else:
        assert isinstance(df_links, list), "df_links should be a list of links"
        df = _import_merge_multiple_df(df_links)
        df.to_csv(df_path, index=False)

    df = df[df["Geographic area"] == selected_country]
    return df


def _get_unicef_global_db_5_14_mortality_rate_df():
    """
    Fetches and preprocesses global mortality rate data among children and youth aged 5-14 from an Excel file.

    Operation:
    1. Defines 'unicef_countries_mapping' to map specific country names to standardized names.
    2. Reads mortality rate data from 'df_path' Excel file, specific to 'sheet_name' "Age 5to14 Country estimates",
       skipping the first 14 header rows and excluding the last 2 rows.
    3. Maps country names using 'unicef_countries_mapping'.
    4. Filters data where 'Uncertainty.Bounds*' is "Median" and 'Country.Name' is within 'st.session_state["countries"]'.
    5. Identifies columns associated with numerical values ('number_associated_cols').
    6. Selects relevant columns ('Country.Name', 'Uncertainty.Bounds*', and 'number_associated_cols').
    7. Constructs 'final_df' DataFrame by iterating through rows and columns to append mortality rate data.

    Returns:
    - pd.DataFrame: Processed DataFrame containing global mortality rate data among children aged 5-14,
      filtered for specified countries.
    """

    unicef_countries_mapping = {
        # "Central African Republic": "CAR",
        # "Czechia": "Czech Republic",
        # "Democratic People's Republic of Korea": "DPRK",
        "Democratic Republic of the Congo": "Congo, DRC",
        "Iran (Islamic Republic of)": "Iran",
        # "Lao People's Democratic Republic": "Laos",
        # "Republic of Moldova": "Moldova",
        "State of Palestine": "Palestine",
        "Russian Federation": "Russia",
        "Syrian Arab Republic": "Syria",
        # "United Republic of Tanzania": "Tanzania",
        # "Timor-Leste": "Timor Leste",
        "Venezuela (Bolivarian Republic of)": "Venezuela",
    }

    def _str_contains_digit(string: str) -> bool:
        return any(char.isdigit() for char in string)

    df_path = os.path.join(
        "..",
        "tabular_data",
        "data",
        "Mortality-rate-among-children-and-youth-age-5-to-24_2023-1.xlsx",
    )
    sheet_name = "Age 5to14 Country estimates"

    # def _read_preprocess_one_df(sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(df_path, sheet_name=sheet_name, header=14).iloc[:-2]
    df["Country.Name"] = df["Country.Name"].apply(
        lambda x: unicef_countries_mapping.get(x, x)
    )
    df = df[
        (df["Uncertainty.Bounds*"] == "Median")
        & (df["Country.Name"].isin(st.session_state["countries"]))
    ]
    number_associated_cols = [col for col in df.columns if _str_contains_digit(col)]
    df = df[["Country.Name", "Uncertainty.Bounds*"] + number_associated_cols]

    final_df = pd.DataFrame()
    for i, row in df.iterrows():
        for col in number_associated_cols:
            final_df = final_df._append(
                {
                    "Geographic area": row["Country.Name"],
                    "Indicator": "Mortality rate age 5-14",
                    "OBS_VALUE": row[col],
                    "TIME_PERIOD": col.split(".")[0],
                    "SEX": "_T",
                },
                ignore_index=True,
            )

    return final_df


def _get_mortality_rate_df(df_path: os.PathLike):
    """
    Fetches and preprocesses mortality rate data from the specified CSV file path.

    Args:
    - df_path (os.PathLike): Path to the CSV file containing mortality rate data.

    Operation:
    1. Checks if the file specified by 'df_path' exists. If exists, reads the data into 'unicef_mortality_rates_df'.
    2. If the file doesn't exist:
        - Retrieves global mortality rate data for ages 5-14 from '_get_unicef_global_db_5_14_mortality_rate_df'.
        - Imports and merges data from [mortality_rate_link] using '_import_merge_multiple_df'.
        - Filters out entries where 'SEX' is "_T" and 'Indicator' is not "Mortality rate age 5-24".
        - Concatenates global mortality rate data with imported data.
        - Converts 'TIME_PERIOD' column to integer type and filters data for years since 1990.
        - Saves the processed data to 'df_path' as a CSV file.
    3. Filters 'unicef_mortality_rates_df' to include only data for countries listed in 'st.session_state["countries"]'.

    Returns:
    - pd.DataFrame: Processed DataFrame containing mortality rate data filtered for specified countries.
    """

    if os.path.exists(df_path):
        unicef_mortality_rates_df = pd.read_csv(df_path)
    else:
        global_db_5_14_mortality_rate = _get_unicef_global_db_5_14_mortality_rate_df()
        unicef_mortality_rates_df = _import_merge_multiple_df([mortality_rate_link])
        unicef_mortality_rates_df = unicef_mortality_rates_df[
            (unicef_mortality_rates_df["SEX"] == "_T")
            & (unicef_mortality_rates_df["Indicator"] != "Mortality rate age 5-24")
        ]
        unicef_mortality_rates_df = pd.concat(
            [unicef_mortality_rates_df, global_db_5_14_mortality_rate]
        )
        unicef_mortality_rates_df["TIME_PERIOD"] = unicef_mortality_rates_df[
            "TIME_PERIOD"
        ].astype(int)
        unicef_mortality_rates_df = unicef_mortality_rates_df[
            unicef_mortality_rates_df["TIME_PERIOD"] >= 1990
        ]
        unicef_mortality_rates_df.to_csv(df_path, index=False)

    unicef_mortality_rates_df = unicef_mortality_rates_df[
        unicef_mortality_rates_df["Geographic area"].isin(st.session_state["countries"])
    ]
    return unicef_mortality_rates_df


@st.fragment
def _display_number_cards(text: str):
    """
    Formats and displays a text string as a number card with a custom background color and border radius.
    """
    clean_text = text.replace("All Sexes: ", "")
    custom_css = f"""
    <div style="
        background-color: #E6E6FA;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 2px 4px 0 rgba(0,0,0,0.2);
        transition: 0.3s;">
        <p style="color: #333333; font-size: 20px; margin: 0;">{clean_text}</p>
    </div>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def _custom_font(title: str, text: str, date: int = None, font_size: int = 17):
    # clean_text = text.replace("All Sexes: ", "")
    clean_text = (
        f"{text})".replace("()", "")
        .replace(", )", ")")
        .replace(".)", ".")
        .replace("(.", ".")
        .replace("..", ".")
    )
    output = f"""<p style="font-size: {font_size}px; font-family: Arial, sans-serif;"><strong>{title}</strong>: {clean_text} """  # noqa
    if date:
        output += f"""<em>(Year: {date})</em>"""
    output += "</p>"

    st.markdown(output, unsafe_allow_html=True)


def _show_one_number_results(df: pd.DataFrame, title: str):
    """
    Displays one-number results or line charts for a given indicator based on the provided DataFrame.

    Args:
    - df (pd.DataFrame): DataFrame containing the data to display.
    - title (str): Title to be displayed for the results or charts.

    Operation:
    1. Checks if the provided DataFrame 'df' is empty. If empty, displays a custom title with
       the specified 'title' and a message indicating no data available.
    2. Retrieves the count of unique years from the 'TIME_PERIOD' column in 'df'.
    3. If only one unique year exists, displays the 'title' followed by the specific year in parentheses.
    4. Iterates through each sex category defined in 'sexes' list and retrieves data
       from 'df' filtered by each sex category.
    5. If data exists for a sex category, formats and accumulates results into 'shown_string' for display.
    6. If multiple data points exist for a sex category, displays a line chart using Plotly
       with 'TIME_PERIOD' on the x-axis and 'OBS_VALUE' on the y-axis.
    7. Adjusts layout settings for the Plotly chart for better readability.
    8. Displays accumulated results or charts based on available data.

    Returns:
    - None
    """

    if len(df) == 0:
        _custom_font(title, f"No data available for this indicator. (Year {st.session_state['selected-year']}")
        return

    years_counts = df["TIME_PERIOD"].value_counts().to_frame()["count"].shape[0]
    # if years_counts == 1:
    #     _custom_title(
    #         f"{title} ({df['TIME_PERIOD'].values[0]})",
    #         font_size=22,
    #     )

    shown_string = ""
    for one_sex in sexes:

        shown_sex_name = sex_to_gender[one_sex]
        df_one_sex = df[df["SEX"] == one_sex]

        if len(df_one_sex) == 0:
            continue

        elif len(df_one_sex) == 1:
            value = round(df_one_sex["OBS_VALUE"].values[0], 1)
            # shown_string += f"{shown_sex_name}: "
            if one_sex == "_T":
                shown_string += f"{value}% ("
            else:
                shown_string += f"{value}% {shown_sex_name}, "
                # shown_string += ""
            # st.markdown(shown_string)

        elif df_one_sex["TIME_PERIOD"].nunique() == 1:
            # st.dataframe(df_one_sex)
            for i, row in df_one_sex.iterrows():
                shown_string += f"<br>- {row['Indicator']}: {row['OBS_VALUE']}%"

        else:
            indicator = df["Indicator"].unique()[0]
            # _custom_title(
            #     f"• {indicator}",
            #     font_size=20,
            #     date=f"Year: {df['TIME_PERIOD'].min()} - {df['TIME_PERIOD'].max()}",
            # )
            # _custom_title(shown_sex_name, margin_top=0, margin_bottom=0, font_size=15)
            _custom_title(
                indicator,
                source="Unicef Global indicator database",
                date=f"{df['TIME_PERIOD'].min()} - {df['TIME_PERIOD'].max()}",
                font_size=22,
                margin_bottom=-50,
            )
            fig = px.line(
                data_frame=df,
                x="TIME_PERIOD",
                y="OBS_VALUE",
                title=" ",
                labels={"TIME_PERIOD": "Year", "OBS_VALUE": "Value"},
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
                tickmode='linear',  # Force linear spacing of ticks
                dtick=1,  # Show every year
                range=[min(df['TIME_PERIOD']), max(df['TIME_PERIOD'])]  # Extend range to include last year
            )
            st.plotly_chart(fig, use_container_width=True)

    if years_counts == 1:
        date = df["TIME_PERIOD"].values[0]
        _custom_font(title, shown_string, date)
        # shown_text = f"- **{title}**: {shown_string}"
        # st.markdown(shown_text, unsafe_allow_html=True)
        # _display_number_cards(shown_string)


def _get_nb_deprivations_df(selected_country: str, df_path: os.PathLike):
    """
    Fetches and displays the average number of deprivations suffered per child from the specified CSV file.
    """
    df = _standard_unicef_data_import(selected_country, df_path, [nb_deprivations_link])
    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    _show_one_number_results(
        df,
        "Average number of deprivations suffered per child. Homogeneous severe standards",
    )


def _get_percentage_adults_think_physical_punishement_good_df(
    selected_country: str, df_path: os.PathLike
):
    """
    Fetches and displays the percentage of adults who think that physical punishment
    is necessary to raise/educate children from the specified CSV file.
    """
    df = _standard_unicef_data_import(
        selected_country,
        df_path,
        [percentage_adults_think_physical_punishement_good_link],
    )
    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    _show_one_number_results(
        df,
        "Percentage of adults who think that physical punishment is necessary to raise/educate children",
    )


def _get_percentage_sexual_violence_df(selected_country: str, df_path: os.PathLike):
    """Fetches and displays the percentage of people exposed to sexual violence from the specified CSV file."""

    df = _standard_unicef_data_import(
        selected_country,
        df_path,
        [percentage_women_sexual_violence_link, percentage_men_sexual_violence_link],
    )
    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    _show_one_number_results(df, "Percentage of people exposed to sexual violence")


def _get_young_women_married_df(selected_country: str, df_path: os.PathLike):
    """
    Fetches and displays the percentage of young women married.
    """
    df = _standard_unicef_data_import(
        selected_country, df_path, [young_women_married_link]
    )
    _show_one_number_results(
        df,
        title="Percentage of women (aged 20-24 years) married or in union before age 18",
    )


def _get_children_detention_rate_df(selected_country: str, df_path: os.PathLike):
    """Fetches and displays the rate of children in detention from the specified CSV file."""
    df = _standard_unicef_data_import(
        selected_country, df_path, [children_detention_rate_link]
    )
    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    _show_one_number_results(df, "Rate of children in detention")


def _get_children_residential_care_rate_df(selected_country: str, df_path: os.PathLike):
    """Fetches and displays the rate of children in residential care from the specified CSV file."""
    df = _standard_unicef_data_import(
        selected_country, df_path, [children_residential_care_rate_link]
    )
    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    _show_one_number_results(df, "Rate of children in residential care")


def _get_out_of_school_rate(selected_country: str, df_path: os.PathLike):
    """
    Fetches and displays out-of-school rates for different age groups from the specified CSV file.

    Args:
    - df_path (os.PathLike): Path to the CSV file containing out-of-school rate data.

    Operation:
    1. Calls '_standard_unicef_data_import' function with 'df_path' and a list of links
       [out_of_school_rate_adolescents_link, out_of_school_rate_children_link, out_of_school_rate_youth_link]
       as arguments to import and standardize UNICEF data.
    2. Loads and processes the data from the CSV file specified by 'df_path' using '_standard_unicef_data_import'.
    3. Retrieves unique indicators from the processed DataFrame 'df'.
    4. Iterates through each unique indicator in 'df', filters data for the indicator, and calls
       '_show_one_number_results' function to display the processed data as one-number results with
       the title set to the indicator name.
    5. Writes empty lines to create spacing between different indicators for clarity.

    Returns:
    - None
    """

    df = _standard_unicef_data_import(
        selected_country,
        df_path,
        [
            out_of_school_rate_adolescents_link,
            out_of_school_rate_children_link,
            out_of_school_rate_youth_link,
        ],
    )

    indicators = df["Indicator"].unique()

    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)

    for one_indicator in indicators:
        df_one_indicator = df[df["Indicator"] == one_indicator]
        if df_one_indicator.empty:
            _custom_font(one_indicator, f"No data available for this indicator. (Year {st.session_state['selected-year']}")
            continue
        _show_one_number_results(df_one_indicator, one_indicator)
        _add_blank_space(1)


def _get_refugee_host_per_country_df(selected_country: str, df_path: os.PathLike):
    """
    Fetches and displays refugee population data hosted by countries per 1000 population.

    Args:
    - df_path (os.PathLike): Path to the CSV file containing refugee host country data.

    Operation:
    1. Calls '_standard_unicef_data_import' function with 'df_path' and
       [refugee_host_per_country_link] as arguments to import and standardize UNICEF data.
    2. Loads and processes the data from the CSV file specified by 'df_path' using '_standard_unicef_data_import'.
    3. Calls '_show_one_number_results' function to display the processed data as one-number
       results with the title "Refugees by host country (per 1000 population)".

    Returns:
    - None
    """

    df = _standard_unicef_data_import(
        selected_country, df_path, [refugee_host_per_country_link]
    )
    df = df[df["TIME_PERIOD"] == st.session_state["selected-year"]]
    df.reset_index(drop=True, inplace=True)
    _show_one_number_results(df, "Refugees by host country (per 1000 population)")


@st.fragment
def _display_child_protection_risks(selected_country: str):
    """
    Displays child protection risks using multiple visualizations and data summaries.

    Operation:
    1. Calls '_custom_title' function to create a custom title "Child Protection Risks"
       with specified font size, margins, and data source.
    2. Uses Streamlit's 'st.container' to organize content into columns for better layout control.
    3. Divides the container into columns using 'st.columns'.
    4. Loads and displays data visualizations and summaries for various child protection risks:
    - Calls '_get_out_of_school_rate', '_get_nb_deprivations_df', '_get_refugee_host_per_country_df',
      '_get_children_detention_rate_df', '_get_children_residential_care_rate_df',
      '_get_percentage_adults_think_physical_punishement_good_df', '_get_percentage_sexual_violence_df',
      and '_get_young_women_married_df' functions to fetch and display respective data
      visualizations or summaries.
    - Each function call loads data from CSV files located in 'st.session_state["unicef_data_folder_path"]'.
    - Inserts blank spaces between different data visualizations or summaries for spacing and clarity.

    Returns:
    - None
    """

    _custom_title(
        "Child Protection Risks",
        margin_top=0,
        margin_bottom=30,
        font_size=30,
        source="Unicef Global indicator database",
    )
    with st.container():
        shown_columns = st.columns([0.32, 0.02, 0.32, 0.02, 0.32])
        with shown_columns[0]:
            _get_out_of_school_rate(
                selected_country,
                os.path.join(st.session_state["unicef_data_folder_path"], "out_of_school_rate_df.csv"),
            )

        with shown_columns[2]:
            _get_nb_deprivations_df(
                selected_country,
                os.path.join(st.session_state["unicef_data_folder_path"], "nb_deprivations_df.csv"),
            )
            _add_blank_space(1)
            _get_refugee_host_per_country_df(
                selected_country,
                os.path.join(
                    st.session_state["unicef_data_folder_path"], "refugee_host_per_country_df.csv"
                ),
            )
            _add_blank_space(1)
            _get_children_detention_rate_df(
                selected_country,
                os.path.join(st.session_state["unicef_data_folder_path"], "children_detention_rate_df.csv"),
            )

        with shown_columns[4]:

            _get_children_residential_care_rate_df(
                selected_country,
                os.path.join(
                    st.session_state["unicef_data_folder_path"], "children_residential_care_rate_df.csv"
                ),
            )
            _add_blank_space(1)
            _get_percentage_adults_think_physical_punishement_good_df(
                selected_country,
                os.path.join(
                    st.session_state["unicef_data_folder_path"],
                    "percentage_adults_think_physical_punishement_good_df.csv",
                ),
            )
            _add_blank_space(1)
            _get_percentage_sexual_violence_df(
                selected_country,
                os.path.join(
                    st.session_state["unicef_data_folder_path"], "percentage_sexual_violence_df.csv"
                ),
            )

    _get_young_women_married_df(
        selected_country,
        os.path.join(st.session_state["unicef_data_folder_path"], "young_women_married_df.csv"),
    )


# Mortality Rate Processing
@st.fragment
def _create_mortality_rate_viz(original_df: pd.DataFrame):
    """
    Creates and displays a bar plot visualization of mortality rates among children and youth.

    Args:
    - original_df (pd.DataFrame): Original DataFrame containing mortality rate data.

    Operation:
    1. Copies the original DataFrame 'original_df' into 'df' for manipulation.
    2. Defines indicators dictionary mapping mortality rate indicators to abbreviated labels for visualization.
    3. Initializes an empty DataFrame 'one_country_mortality_rate' to store filtered data for one country.
    4. Iterates over each indicator in 'indicators' dictionary, appending filtered data
       from 'df' where 'Indicator' matches the current indicator.
    5. Replaces full indicator names with abbreviated labels in 'one_country_mortality_rate'.
    6. Sets custom colors for the bar plot visualization.
    7. Uses Plotly Express 'px.bar' to create a grouped bar plot ('barmode="group"') with
       'TIME_PERIOD' on the x-axis and 'OBS_VALUE' (mortality rate) on the y-axis.
    8. Configures plot title and axis labels, and applies custom colors using 'color_discrete_sequence'.
    9. Updates layout to adjust font sizes for title, axis titles, tick labels, and legend.
    10. Displays the plot using Streamlit's 'st.plotly_chart' with 'use_container_width=True'
        for responsive width.

    Returns:
    - None
    """

    df = original_df.copy()

    _custom_title(
        "Consequences for Children's Protection",
        font_size=30,
        source="UNICEF",
        date=f"{df['TIME_PERIOD'].min()} - {df['TIME_PERIOD'].max()}",
    )

    indicators = {
        "Child mortality rate (aged 1-4 years)": "1-4",
        "Mortality rate age 5-14": "5-14",
        "Mortality rate age 15-19": "15-19",
    }

    one_country_mortality_rate = pd.DataFrame()
    for indicator in indicators:
        one_country_mortality_rate = one_country_mortality_rate._append(
            df[df["Indicator"] == indicator]
        )
        one_country_mortality_rate["Indicator"] = one_country_mortality_rate[
            "Indicator"
        ].replace(indicators)

    # one_country_mortality_rate.sort_values(by="Indicator", ascending=True, inplace=True)

    custom_colors = [
        "#D6ECDF",
        "#B1DBC3",
        "#90AF9F",
    ]  # changed the color to use the one that can support in the analogous triad

    fig = px.bar(
        one_country_mortality_rate,
        x="TIME_PERIOD",
        y="OBS_VALUE",
        color="Indicator",
        barmode="group",
        title="Mortality rate among children and youth",
        labels={
            "OBS_VALUE": "Mortality Rate (per 100,000)",
            "TIME_PERIOD": "Year",
            "Indicator": "Age Group",
        },
        color_discrete_sequence=custom_colors,  # Set custom colors
    )

    fig.update_layout(
        title_font=dict(size=24),  # Bigger title font
        xaxis_title_font=dict(size=18),  # Bigger x-axis title font
        yaxis_title_font=dict(size=18),  # Bigger y-axis title font
        xaxis_tickfont=dict(size=14),  # Bigger x-axis tick labels
        yaxis_tickfont=dict(size=14),  # Bigger y-axis tick labels
        legend_title_font=dict(size=16),  # Bigger legend title font
        legend_font=dict(size=14),  # Bigger legend text
        margin=dict(t=50, b=50, l=50, r=50)  # Add padding around plot
    )
    fig.update_xaxes(
        tickmode='linear',  # Force linear spacing of ticks
        dtick=1,  # Show every year
        range=[min(one_country_mortality_rate['TIME_PERIOD']), max(one_country_mortality_rate['TIME_PERIOD'])]  # Extend range to include last year
    )

    st.plotly_chart(fig, use_container_width=True)


@st.fragment
def _display_tabular_mortality_rates(selected_country: str):
    """
    Displays tabular visualization of mortality rates related to children's protection.

    Operation:
    1. Calls '_custom_title' function to create a custom title
       "Consequences for Children's Protection" with specified font size and source.
    2. Retrieves mortality rate data from a CSV file located at the specified path using '_get_mortality_rate_df' function.
    3. Checks if the retrieved DataFrame 'mortality_rate_df' is empty:
    - If empty, displays a markdown message indicating no data available for the country.
    - If not empty, calls '_create_mortality_rate_viz' function to create and display
      a visualization based on 'mortality_rate_df'.

    Returns:
    - None
    """

    mortality_rate_df = _get_mortality_rate_df(
        os.path.join(st.session_state["unicef_data_folder_path"], "mortality_rate_df.csv")
    )

    mortality_rate_df = mortality_rate_df[
        mortality_rate_df["TIME_PERIOD"] <= st.session_state["selected-year"]
    ]
    mortality_rate_df.reset_index(drop=True, inplace=True)

    if len(mortality_rate_df) == 0:
        _custom_title(
            "Consequences for Children's Protection", font_size=30, source="UNICEF"
        )
        st.markdown("No data available for this country.")
    else:
        _create_mortality_rate_viz(mortality_rate_df)
