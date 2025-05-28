import os
from ast import literal_eval
from typing import Any, Dict, List, Union

import pandas as pd
from data_sources_processing.acaps_protection_indicators.pull_data import \
    pull_acaps_protection_indicators
from data_sources_processing.acaps_protection_indicators.sources_extraction_reliefweb.extract_map_sources_reliefweb import \
    get_reliefweb_organisations


def _flatten_list(lst):
    return [item for sublist in lst for item in sublist]


# country_names_mapping = {
#     "DRC": "Congo DRC",
#     "CAR": "Central African Republic",
#     "TÃ¼rkiye": "Türkiye",
# }


# disregarded_tags = [
#     "Access to asylum process after entry",
#     "Arbitrary denial or deprivation of nationality or statelessness",
#     "Femicide and honour killings",
#     "Forced eviction from property ",
#     "Refoulement/pushbacks/forced returns",
# ]

# protection_file_name = "ACAPS_Protection-indicators_ALL.xlsx"

# studied_indicators = (
#     pd.read_excel(protection_file_name, sheet_name="Indicators")
#     .dropna()["Unnamed: 0"]
#     .tolist()[2:-1]
# )
# studied_indicators = [
#     t.strip()
#     for t in _flatten_list(
#         [literal_eval(indicator) for indicator in studied_indicators]
#     )
#     if t not in disregarded_tags
# ]


eval_cols = [
    "iso3",
    "country",
    "adm1_eng_name",
    "indicator",
    "targeting_specific_population_groups",
]
single_value_cols = ["iso3", "country"]


processed_breakdowns = [
    "adm1_eng_name",
    "indicator",
    "targeting_specific_population_groups",
]

metadata_data_path = os.path.join("/data", "reliefweb_sources_metadata.json")

if not os.path.exists(metadata_data_path):
    os.makedirs(os.path.join("sources_extraction_reliefweb", "data"), exist_ok=True)
    get_reliefweb_organisations(metadata_data_path)


def _preprocess_col(val: str, col_name: str, studied_indicators: List[str]):
    output = literal_eval(val) if str(val).lower().strip() != "nan" else []
    if len(output) > 0 and col_name in single_value_cols:
        output = output[0]
    if col_name == "country":
        output = output.replace("TÃ¼rkiye", "Türkiye")
    if col_name == "indicator":
        output = list(
            set(
                [
                    t.replace("childrenâ€™s", "children's")
                    for t in output
                    if t in studied_indicators
                ]
            )
        )
    return output


def _load_dataset(
    datasets_metadata: Dict[str, Any],
    raw_dataset_path: os.PathLike,
    use_sample: bool,
    protection_indicators_data: Dict[str, List[str]],
):
    """
    Inputs:
    - None

    Outputs:
    - protection_indicators_dataset (pd.DataFrame): A processed DataFrame containing protection indicators data.

    Operation:
    1. Load the 'protection-indicators' sheet from the Excel file into a DataFrame:
    - Drop unnecessary columns ('additional_sources', 'adm1').
    - Drop rows with missing values in 'country' or 'justification' columns.
    2. Replace country names in the 'country' column using 'country_names_mapping'.
    3. Apply the '_preprocess_col' function to specified columns (eval_cols) for preprocessing.
    4. Calculate the number of unique locations in 'adm1_eng_name'.
    5. Update 'adm1_eng_name' values to "Country Wide" if the number of locations is less than
       half of the unique locations or if the value is empty.
    6. Add a new column 'source_reliability' by applying '_get_source_reliability_score' to the 'source_name' column.
    7. Filter the DataFrame to include only rows where 'source_reliability' is greater than 1.
    8. Load a list of countries to be processed from a CSV file.
    9. Filter the DataFrame to include only rows where the 'country' is in the list of countries to be processed.
    10. Return the processed DataFrame.
    """

    pull_acaps_protection_indicators(datasets_metadata, raw_dataset_path, use_sample)

    protection_indicators_dataset = pd.read_csv(raw_dataset_path)

    # protection_indicators_dataset["country"] = protection_indicators_dataset[
    #     "country"
    # ].apply(lambda x: country_names_mapping.get(x, x))

    for col in eval_cols:
        protection_indicators_dataset[col] = protection_indicators_dataset[col].apply(
            lambda x: _preprocess_col(x, col, protection_indicators_data["indicator"])
        )

    protection_indicators_dataset["adm1_eng_name"] = (
        protection_indicators_dataset.apply(
            lambda x: ["Country Wide"] if x["countrywide"] else x["adm1_eng_name"],
            axis=1,
        )
    )

    return protection_indicators_dataset


def _prepare_inference_dataset(all_df: pd.DataFrame, one_country: str):
    """
    Inputs:
    - all_df (pd.DataFrame): DataFrame containing the complete dataset with protection indicators.
    - one_country (str): The name of the country to filter and process.

    Outputs:
    - final_outputs (pd.DataFrame): A DataFrame containing processed entries for the specified country,
      categorized by breakdown columns and possible values.

    Operation:
    1. Filter 'all_df' to include only rows where the 'country' column matches 'one_country'.
    2. Initialize an empty DataFrame 'final_outputs' to store the results.
    3. Iterate over each column specified in 'processed_breakdowns':
    3.1 Get all unique values from the current breakdown column.
    3.2 For each unique value:
        - Filter rows where the breakdown column contains the current value.
        - Initialize an empty DataFrame 'processed_df'.
        - Sort 'reliability_scores' in descending order and iterate through them:
            - Filter the rows by the current reliability score.
            - Concatenate the filtered rows into 'processed_df'.
            - Stop if 'processed_df' contains more than 5 entries.
        - Skip the current value if 'processed_df' contains fewer than 3 entries and is not "Country Wide".
        - Prepare a list of entries with necessary details (e.g., source name, date, link, and justification).
        - Append a dictionary with processed information to 'final_outputs', including:
            - The country name.
            - The breakdown column, replacing specific terms with their respective labels.
            - The possible value.
            - The list of processed entries.
            - The number of entries.
    4. Return 'final_outputs'.
    """

    final_outputs = pd.DataFrame()

    df_one_country = all_df[all_df["country"] == one_country].copy()

    for one_breakdown_column in processed_breakdowns:

        all_possible_values = set(
            _flatten_list(df_one_country[one_breakdown_column].values)
        )

        for one_possible_value in all_possible_values:
            df_one_possible_value = df_one_country[
                df_one_country[one_breakdown_column].apply(
                    lambda x: one_possible_value in x
                )
            ].copy()

            processed_df = pd.DataFrame()
            processed_df = pd.concat([processed_df, df_one_possible_value])

            # if less than 3 entries and not the general summary, we skip the possible value
            if len(processed_df) < 3 and one_possible_value != "Country Wide":
                continue

            processed_df["source_date"] = pd.to_datetime(processed_df["source_date"])
            processed_df = processed_df.sort_values(
                by="source_date", ascending=False
            ).head(20)

            to_be_processed_entries = []
            for i, (_, row) in enumerate(processed_df.iterrows()):
                entry = row["justification"].replace("\n", " ")
                source_name = row["source_name"]
                source_link = row["source_link"]
                to_be_processed_entries.append(
                    {
                        "source_name": source_name,
                        "source_date": row["source_date"],
                        "source_link": source_link,
                        "text": entry,
                    }
                )

            final_outputs = final_outputs._append(
                {
                    "country": one_country,
                    "Breakdown Column": one_breakdown_column.replace(
                        "adm1_eng_name", "Geolocation"
                    )
                    .replace(
                        "targeting_specific_population_groups",
                        "Targeting Specific Population Groups",
                    )
                    .replace("indicator", "Indicator"),
                    "Value": one_possible_value,
                    "entries": to_be_processed_entries,
                    "n_entries": len(to_be_processed_entries),
                    "Last Date": processed_df["source_date"].max(),
                },
                ignore_index=True,
            )

    return final_outputs


def _get_final_results(
    df: pd.DataFrame, final_results: List[Dict[str, Union[str, List[int]]]]
):
    """
    Inputs:
    - df (pd.DataFrame): The original DataFrame containing the entries with columns
      'country', 'breakdown_column', 'possible_value', and 'entries'.
    - final_results (List[Dict[str, Union[str, List[int]]]]): A list of dictionaries, each containing:
    - 'Text' (str): The generated text for the analytical statement.
    - 'Relevant IDs' (List[int]): List of IDs corresponding to relevant entries in the original DataFrame.

    Outputs:
    - postprocessed_results (pd.DataFrame): A DataFrame containing postprocessed results with the following columns:
        - 'Country': The country name.
        - 'Breakdown Column': The breakdown column used in the analysis.
        - 'Value': The possible value in the breakdown column.
        - 'Generated Text': The generated text for the analytical statement.
        - 'Source Original Text': The text of the source, with new lines replaced by spaces.
        - 'Source Name': The name of the source.
        - 'Source Date': The date of the source.
        - 'Source Link': The link to the source.

    Operation:
    1. Initialize an empty list 'postprocessed_results' to store the final results.
    2. Iterate over each analytical statement in 'final_results':
    2.1 Extract relevant details from the corresponding row in 'df' using the index 'i'.
    2.2 Retrieve relevant entries based on 'Relevant IDs' from the original DataFrame.
    2.3 Append a dictionary with the processed information, including: country name,
        breakdown column, possible value, generated text, list of relevant entries.
    3. Convert 'postprocessed_results' to a DataFrame and explode the 'Evidence' column to separate each entry.
    4. Create new columns for 'Source Original Text', 'Source Name', 'Source Date', and 'Source Link'
       by extracting data from the 'Evidence' column.
    5. Update 'Value' and 'Breakdown Column' for rows where 'Value' is 'Country Wide':
    5.1 Set 'Value' to '1 - General Summary'.
    5.2 Update 'Breakdown Column' to '1 - General Summary' where applicable.
    6. Drop the 'Evidence' column and sort the DataFrame by 'Country', 'Breakdown Column', and 'Value'.
    7. Set the index of the DataFrame to include: 'Country', 'Breakdown Column', 'Value',
       'Generated Text', 'Source Original Text'

    Return:
    - The sorted and indexed DataFrame 'postprocessed_results'.
    """

    postprocessed_results = []
    for i, one_analytical_statement in enumerate(final_results):
        if len(one_analytical_statement) > 0:
            original_entry = df.iloc[i]
            relevant_entries = original_entry["entries"]
            one_analytical_statement_text: str = one_analytical_statement["Text"]
            one_analytical_statement_relevant_ids: List[str] = one_analytical_statement[
                "ID"
            ]

            one_analytical_statement_relevant_entries = [
                relevant_entries[int(one_id)]
                for one_id in one_analytical_statement_relevant_ids
            ]

            postprocessed_results.append(
                {
                    "Country": original_entry["country"],
                    "Breakdown Column": original_entry["Breakdown Column"],
                    "Value": original_entry["Value"],
                    "Last Date": original_entry["Last Date"],
                    "Generated Text": one_analytical_statement_text,
                    "Evidence": one_analytical_statement_relevant_entries,
                }
            )

    postprocessed_results_df = pd.DataFrame(postprocessed_results)
    if len(postprocessed_results_df):
        postprocessed_results = postprocessed_results_df.explode("Evidence")

        postprocessed_results["Source Original Text"] = postprocessed_results[
            "Evidence"
        ].apply(lambda x: x["text"].replace("\n", " "))
        postprocessed_results["Source Name"] = postprocessed_results["Evidence"].apply(
            lambda x: x["source_name"]
        )
        postprocessed_results["Source Date"] = postprocessed_results["Evidence"].apply(
            lambda x: x["source_date"]
        )
        postprocessed_results["Source Link"] = postprocessed_results["Evidence"].apply(
            lambda x: x["source_link"]
        )

        # new row value for rows where "Value" is "Country Wide"
        postprocessed_results["Value"] = postprocessed_results.apply(
            lambda x: "1 - General Summary" if x["Value"] == "Country Wide" else x["Value"],
            axis=1,
        )
        postprocessed_results["Breakdown Column"] = postprocessed_results.apply(
            lambda x: (
                "1 - General Summary"
                if x["Value"] == "1 - General Summary"
                else x["Breakdown Column"]
            ),
            axis=1,
        )

        return postprocessed_results
    return pd.DataFrame({
        "Country": [],
        "Breakdown Column": [],
        "Value": [],
        "Last Date": [],
        "Generated Text": [],
        "Evidence": [],
    })
