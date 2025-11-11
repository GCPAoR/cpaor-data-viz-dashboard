import argparse
import json
import logging
import os
import subprocess
from datetime import datetime

from data_sources_processing.acaps_inform_severity.acaps_inform_severity_data_preparation import \
    _get_acaps_inform_severity_data
from data_sources_processing.acaps_protection_indicators.prepare_acaps_protection_data import \
    generate_summaries
from data_sources_processing.acled.acled_data_preparation import \
    _get_acled_data
from data_sources_processing.idmc.idmc_data_preparation import _get_idmc_data
from data_sources_processing.ipc.ipc_data_preparation import _get_ipc_data
from data_sources_processing.ocha_hpc.ocha_hpc_data_preparation import \
    _get_ocha_hpc_data

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

datasets_metadata_path = os.path.join(
    "/data", "datasets_metadata.json"
)

time_format = "%d-%m-%Y"
today_date = datetime.today()

datasets_processing_functions = {
    "ipc": _get_ipc_data,
    "acaps_protection_indicators": generate_summaries,
    "acaps_inform_severity": _get_acaps_inform_severity_data,
    "idmc": _get_idmc_data,
    "ocha_hpc": _get_ocha_hpc_data,
    "acled": _get_acled_data,
}

output_datasets_path = os.path.join("/data", "datasources")

if __name__ == "__main__":

    """
    Inputs:
    - datasets_metadata_path (str): Path to the JSON file containing metadata of datasets.
    - datasets_processing_functions (dict): Dictionary mapping dataset names to their corresponding processing functions.
    - today_date (datetime): The current date.
    - time_format (str): The format of the date used in the metadata.
    - output_datasets_path (str): Path to the output directory for processed datasets.

    Outputs:
    - Updates the 'last_update_time' field in datasets_metadata for datasets that have been processed.
    - Executes specified dataset processing functions and updates metadata if new data is processed.
    - Runs specific scripts to process the 'ohchr' dataset if not already processed.

    Operation:
    1. Reads the datasets metadata from a JSON file.
    2. Iterates through each dataset and its processing function.
    3. Checks if the dataset needs to be updated based on its last update time and update frequency.
    4. If an update is required, it processes the dataset using its corresponding function and updates the metadata.
    5. Saves the updated metadata back to the JSON file.
    6. Specifically checks if the 'ohchr' dataset is processed, and if not, runs two scripts to process it.
    """

    args = argparse.ArgumentParser()
    args.add_argument("--sample", type=str, default="false")

    sample_bool = args.parse_args().sample == "true"

    with open(datasets_metadata_path, "r") as file:
        datasets_metadata = json.load(file)

    for (
        dataset_name,
        dataset_processing_function,
    ) in datasets_processing_functions.items():

        logger.info(f"---------------- Processing {dataset_name} ----------------")

        # Reload the datasets_metadata each time because functions may change it

        dataset_last_update = datasets_metadata[dataset_name]["last_update_time"]
        if dataset_last_update == "":
            dataset_last_update = "01-01-2000"  # Set a default date very early on

        dataset_update_frequency = datasets_metadata[dataset_name]["update_frequency"]
        # get the number of days difference between the last update and today
        days_difference = (
            today_date - datetime.strptime(dataset_last_update, time_format)
        ).days
        if days_difference >= dataset_update_frequency:
            # try:
            new_latest_file_infos = dataset_processing_function(
                datasets_metadata[dataset_name], output_datasets_path
            )
            if new_latest_file_infos is not None:

                datasets_metadata[dataset_name] = new_latest_file_infos
                logger.info(f"{dataset_name} file updated successfully.")

            if not sample_bool:
                datasets_metadata[dataset_name]["last_update_time"] = (
                    today_date.strftime(time_format)
                )

            # save datasets metadata
            with open(datasets_metadata_path, "w") as file:
                json.dump(datasets_metadata, file, indent=4)
            # except Exception as e:
            #     logger.error(f"Error processing {dataset_name}: {e}")

        else:
            logger.info(f"{dataset_name} file is already up to date.")

    # process ohchr dataset if not there
    if not os.path.exists(os.path.join(output_datasets_path, "ohchr", "results")):
        logger.info("---------------- Processing ohchr ----------------")
        # Change directory to 'ohchr'
        os.chdir("data_sources_processing/ohchr")

        # Run the first script
        subprocess.run(["python", "scrape_articles.py", "--use_sample=false"])

        # Run the second script
        subprocess.run(["python", "prepare_final_results.py", "--use_sample=false"])
