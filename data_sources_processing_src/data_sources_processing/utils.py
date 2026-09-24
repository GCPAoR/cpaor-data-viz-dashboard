import logging
import os
from copy import copy
from datetime import datetime
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import requests

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)


HDX_API_PACKAGE_SHOW_URL = "https://data.humdata.org/api/3/action/package_show"


def _get_hdx_data(
    original_datasets_metadata: Dict[str, Any],
    data_output_path: os.PathLike,
    data_folder: str,
) -> Union[Dict[str, Any], None]:
    """
    Inputs:
    - original_datasets_metadata (Dict[str, Any]): Metadata of the dataset.
    - data_output_path (os.PathLike): Path to the directory where the data will be saved.
    - data_folder (str): Subfolder within the output path for saving the data.

    Outputs:
    - Union[Dict[str, Any], None]: Updated dataset metadata if a new file is downloaded;
      otherwise, returns the original metadata or None if the request fails.

    Operation:
    1. Create a copy of the original dataset metadata.
    2. Derive the HDX dataset id from the dataset page URL in the metadata.
    3. Fetch the dataset resources from the HDX CKAN API (the HTML page layout is not stable).
    4. If the request is successful:
    4.1 Extract the latest file information using '_get_hdx_file_infos'.
    4.2 Compare the extracted file's update date with the stored metadata.
    4.3 If the dates differ, download the new file and update the metadata with the latest file information.
    4.4 Return the updated metadata.
    5. If the request fails, print an error message and return None.
    """

    datasets_metadata = copy(original_datasets_metadata)
    # URL of the dataset page: https://data.humdata.org/dataset/<dataset_id>
    url = datasets_metadata["website_url"]
    dataset_id = urlparse(url).path.rstrip("/").split("/")[-1]

    response = requests.get(HDX_API_PACKAGE_SHOW_URL, params={"id": dataset_id})

    # Check if the request was successful
    if response.status_code == 200:
        resources = response.json()["result"]["resources"]

        latest_file_info = _get_hdx_file_infos(resources, datasets_metadata["hdx_file_name"])
        if latest_file_info["file_time"] != datasets_metadata["latest_file_info"].get("file_time"):
            dir_path = os.path.join(data_output_path, data_folder)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            # Note: Little hack as hdx page from where the download_url is fetched
            # still using data from 2023 (2024 data already published)
            latest_file_info["download_url"] = latest_file_info["download_url"].replace("2023", str(datetime.now().year - 1))
            _dl_hdx_file(
                latest_file_info["download_url"],
                os.path.join(
                    dir_path,
                    datasets_metadata["saved_file_name"],
                ),
            )
            datasets_metadata["latest_file_info"] = latest_file_info

            return datasets_metadata

        else:
            return datasets_metadata

    else:
        logger.error(f"Failed to retrieve the dataset {dataset_id}. Status code: {response.status_code}")
        return None


def _get_one_ressource_infos(one_ressource: Dict[str, Any]) -> Dict[str, Any]:
    """

    Inputs:
    - one_ressource (dict): A single resource from the HDX CKAN API.

    Outputs:
    - treated_doc (dict): A dictionary containing the information of the resource.

    Operation:
    1. Initialize an empty dictionary 'treated_doc'.
    2. Extract the last modified date of the resource and convert it to the format 'dd-mm-yyyy'.
    3. Store the formatted date and the download URL in 'treated_doc'.
    4. Return the dictionary 'treated_doc'.
    """
    treated_doc = {}
    date_str = one_ressource.get("last_modified") or one_ressource["metadata_modified"]

    treated_doc["file_time"] = datetime.fromisoformat(date_str).strftime("%d-%m-%Y")
    treated_doc["download_url"] = one_ressource["url"]
    return treated_doc


def _get_hdx_file_infos(resources: List[Dict[str, Any]], file_name: str):
    """
    Inputs:
    - resources (list): Resources of the dataset from the HDX CKAN API.
    - file_name (str): The name of the file to find within the resources. If set to "-", the first resource is used.

    Outputs:
    - treated_doc (dict): A dictionary containing the information of the specified resource.

    Operation:
    1. If a specific file name is provided, find the resource with the matching name.
    2. If no specific file name is provided, use the first resource.
    3. Extract its information using the '_get_one_ressource_infos' function.
    4. Return the extracted information as a dictionary.
    """

    if not resources:
        raise ValueError("No resources found for the HDX dataset")

    if file_name != "-":
        matching_resources = [one_ressource for one_ressource in resources if one_ressource["name"] == file_name]
        if not matching_resources:
            available_names = [one_ressource["name"] for one_ressource in resources]
            raise ValueError(f"HDX resource {file_name!r} not found. Available: {available_names}")
        one_ressource = matching_resources[-1]
    else:
        one_ressource = resources[0]

    return _get_one_ressource_infos(one_ressource)


def _dl_hdx_file(url, file_path):
    """
    Downloads a file from the given URL and saves it to the specified path.

    Args:
        url (str): The URL of the file to be downloaded.
        save_path (str): The path where the file will be saved.

    Returns:
        None
    """
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(response.content)
        # logger.info(f"File downloaded successfully and saved to {file_path}")
    else:
        logger.error(f"Failed to download file. Status code: {response.status_code}")
