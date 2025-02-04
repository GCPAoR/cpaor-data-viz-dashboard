import argparse
import json
import logging
import os
from datetime import datetime

from data_sources_processing.ocha_hpc.ocha_hpc_data_preparation import \
    _get_ocha_hpc_data
    
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

datasets_metadata_path = os.path.join("/data", "datasets_metadata.json")
output_datasets_path = os.path.join("/data", "datasources")
time_format = "%d-%m-%Y"
today_date = datetime.today()

def update_ocha_hpc_data():
    with open(datasets_metadata_path, "r") as file:
        datasets_metadata = json.load(file)

    dataset_name = "ocha_hpc"
    dataset_processing_function = _get_ocha_hpc_data

    logger.info(f"---------------- Processing {dataset_name} ----------------")

    dataset_last_update = datasets_metadata[dataset_name]["last_update_time"]
    if dataset_last_update == "":
        dataset_last_update = "01-01-2000"  

    dataset_update_frequency = datasets_metadata[dataset_name]["update_frequency"]
    
    # Calculate the days difference
    days_difference = (today_date - datetime.strptime(dataset_last_update, time_format)).days
    if days_difference >= dataset_update_frequency:
        try:
            new_latest_file_infos = dataset_processing_function(datasets_metadata[dataset_name], output_datasets_path)
            if new_latest_file_infos is not None:
                datasets_metadata[dataset_name] = new_latest_file_infos
                logger.info(f"{dataset_name} file updated successfully.")

            datasets_metadata[dataset_name]["last_update_time"] = today_date.strftime(time_format)

            with open(datasets_metadata_path, "w") as file:
                json.dump(datasets_metadata, file)

        except Exception as e:
            logger.error(f"Error processing {dataset_name}: {e}")
    else:
        logger.info(f"{dataset_name} file is already up to date.")

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--sample", type=str, default="false")
    sample_bool = args.parse_args().sample == "true"
    
    update_ocha_hpc_data()
