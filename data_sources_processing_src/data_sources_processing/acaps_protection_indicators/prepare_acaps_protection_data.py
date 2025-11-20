import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from data_sources_processing.acaps_protection_indicators.generate_predictions import _generate_general_summary
from data_sources_processing.acaps_protection_indicators.process_df import (
    _get_final_results,
    _load_dataset,
    _prepare_inference_dataset,
)

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

needed_cols_for_filter = ["Value", "Last Date"]


def generate_summaries(
    datasets_metadata: Dict[str, Any],
    raw_dataset_path: os.PathLike,
    use_sample: bool = False,
):
    """
    Main function for generating summaries of protection indicators for countries.

    Args:
        use_sample (bool): If True, only processes a sample of countries (default is True).
        If False, processes all countries in the dataset.

    Operation:
    1. Defines the path to save the output files.
    2. Loads the protection indicators dataset.
    3. Determines the list of countries to process based on the `use_sample` flag.
    4. Checks for already processed countries to avoid redundant processing.
    5. Iterates over the list of countries to be processed:
       - If the country has already been processed (i.e., output file exists), it skips to the next country.
       - Otherwise, it prepares the inference dataset for the current country.
       - If there is data for the country, it generates summaries and final results.
       - Saves the final results to an Excel file.
       - Pauses for 10 seconds between processing to manage API rate limits or system load.
    6. Handles exceptions to ensure that errors during processing are logged, and
       processing continues for remaining countries.
    """

    # now_time = datetime.now().strftime("%m-%d_%H-%M")
    # save_path = os.path.join("outputs", now_time)
    save_path = os.path.join("/data", "datasources", "acaps_protection_indicators")

    raw_dataset_folder_name = os.path.join(save_path, "raw_datasets")
    os.makedirs(raw_dataset_folder_name, exist_ok=True)

    processed_data_folder_name = os.path.join(save_path, "processed_data")
    os.makedirs(processed_data_folder_name, exist_ok=True)

    raw_dataset_file_name = "raw_dataset.csv"
    if use_sample:
        raw_dataset_file_name = "sample_" + raw_dataset_file_name
    raw_dataset_path = os.path.join(raw_dataset_folder_name, raw_dataset_file_name)

    protection_indicators_data_path = os.path.join(save_path, "acaps_protection_indicators_tags.json")
    with open(protection_indicators_data_path, "r") as file:
        protection_indicators_data = json.load(file)

    # latest_inference_date = pd.to_datetime(datasets_metadata["latest_file_info"]["file_time"], format="%d-%m-%Y")

    protection_indicators_original_dataset = _load_dataset(
        datasets_metadata, raw_dataset_path, use_sample, protection_indicators_data
    )
    if not use_sample:
        to_be_processed_countries = sorted(protection_indicators_original_dataset.country.unique().tolist())
    else:
        to_be_processed_countries = ["Ukraine"]

    # already_processed_countries = [c.replace(".xlsx", "") for c in os.listdir(save_path)]

    # to_be_processed_countries = [c for c in to_be_processed_countries if c not in already_processed_countries]

    country_to_last_infer_date = os.path.join("/data", "datasources", "acaps_protection_indicators", "raw_datasets", "country_to_last_infer_date.csv")
    df_country_to_last_infer_date = pd.read_csv(country_to_last_infer_date)

    if len(df_country_to_last_infer_date):
        df_country_to_last_infer_date["last_infer_date"] = pd.to_datetime(df_country_to_last_infer_date["last_infer_date"], format="%Y-%m-%d")

    n_processed_countries = len(to_be_processed_countries)

    # print(protection_indicators_original_dataset.source_reliability.unique())
    # display(protection_indicators_original_dataset.head())

    for i, one_country in enumerate(to_be_processed_countries):
        country_output_path = os.path.join(processed_data_folder_name, f"{one_country}.csv")

        df_temp = df_country_to_last_infer_date[df_country_to_last_infer_date["country"] == one_country]

        latest_inference_date = df_temp["last_infer_date"].iloc[0].date().strftime("%Y-%m-%d")

        logger.info(
            f"------------------------------ {i + 1}/{n_processed_countries} - {one_country} processing------------------------------"  # noqa
        )

        inference_dataset = _prepare_inference_dataset(protection_indicators_original_dataset, one_country)

        if os.path.exists(country_output_path):
            past_summaries_one_country = pd.read_csv(
                country_output_path  # , engine="openpyxl"
            ).ffill()
            past_summaries_one_country["Last Date"] = pd.to_datetime(past_summaries_one_country["Last Date"])

            already_processed_df = past_summaries_one_country[
                past_summaries_one_country["Last Date"] < latest_inference_date
            ]

            # print("past summaries", past_summaries_one_country[needed_cols_for_filter].drop_duplicates())
            # treated_indicators = past_summaries_one_country[
            #     needed_cols_for_filter
            # ].drop_duplicates()

            # same_rows_df = pd.DataFrame()
            # for index, row in inference_dataset.iterrows():
            #     if (
            #         row[needed_cols_for_filter].to_list()
            #         in treated_indicators[needed_cols_for_filter].to_numpy().tolist()
            #     ):
            #         same_rows_df = same_rows_df._append(row)

            inference_dataset = inference_dataset[inference_dataset["Last Date"] > latest_inference_date]
        else:
            already_processed_df = pd.DataFrame()

        if len(inference_dataset) == 0:
            logger.info(
                f"------------------------------ {i + 1}/{n_processed_countries} - {one_country} no new data------------------------------"  # noqa
            )
            continue

        # try:
        inference_dataset.reset_index(drop=True, inplace=True)
        final_results = _generate_general_summary(inference_dataset)

        results_one_country = _get_final_results(inference_dataset, final_results)

        results_one_country = pd.concat([results_one_country, already_processed_df])

        results_one_country = (
            results_one_country.drop(columns=["Evidence"])
            .sort_values(by=["Country", "Breakdown Column", "Value"])
            .reset_index(drop=True)
            # .set_index(
            #     [
            #         "Country",
            #         "Breakdown Column",
            #         "Value",
            #         "Generated Text",
            #         "Source Original Text",
            #     ]
            # )
        )

        results_one_country.to_csv(country_output_path, index=False)

        # except Exception as e:
        #     print(
        #         f"------------------------------ {i+1}/{n_processed_countries} - {one_country} failed------------------------------"  # noqa
        #     )
        #     print(e)

        time.sleep(10)

    if not use_sample:
        datasets_metadata["latest_file_info"]["file_time"] = datetime.now().strftime("%d-%m-%Y")
    return datasets_metadata
