import logging
import os
from copy import copy
from datetime import datetime
from typing import Any, Dict, Union

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)


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
    2. Retrieve the URL of the dataset page from the metadata.
    3. Send a GET request to the URL.
    4. If the request is successful:
    4.1 Parse the HTML content of the page.
    4.2 Extract the latest file information using '_get_hdx_file_infos'.
    4.3 Compare the extracted file's update date with the stored metadata.
    4.4 If the dates differ, download the new file and update the metadata with the latest file information.
    4.5 Return the updated metadata.
    5. If the request fails, print an error message and return None.
    """

    datasets_metadata = copy(original_datasets_metadata)
    # URL of the dataset page
    url = datasets_metadata["website_url"]

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, "html.parser")

        latest_file_info = _get_hdx_file_infos(soup, datasets_metadata["hdx_file_name"])
        if latest_file_info["file_time"] != datasets_metadata["latest_file_info"]["file_time"]:
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
        logger.error(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None


HDX_BASE_URL = "https://data.humdata.org"


def _to_absolute_hdx_url(url: str) -> str:
    if url.startswith("/"):
        return f"{HDX_BASE_URL}{url}"
    return url


def _get_hdx_resource_last_modified(resource_page_url: str) -> str:
    """
    Inputs:
    - resource_page_url (str): URL of the HDX resource page.

    Outputs:
    - date_str (str): The "Last modified" date of the resource, e.g. '17 September 2026'.

    Operation:
    1. Send a GET request to the resource page (the dataset page no longer shows per-resource dates).
    2. Find the page header metadata item labelled 'Last modified' and return its value.
    """
    response = requests.get(resource_page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    for meta_item in soup.find_all("div", class_="c-page-header__meta-item"):
        label = meta_item.find("span", class_="c-page-header__meta-label")
        if label is not None and label.text.strip() == "Last modified":
            return meta_item.find("div", class_="c-page-header__meta-value").text.strip()

    raise ValueError(f"'Last modified' date not found in {resource_page_url}")


def _get_one_ressource_infos(one_ressource: BeautifulSoup) -> Dict[str, Any]:
    """

    Inputs:
    - one_ressource (BeautifulSoup element): A single resource item element from the HTML document.

    Outputs:
    - treated_doc (dict): A dictionary containing the information of the resource.

    Operation:
    1. Initialize an empty dictionary 'treated_doc'.
    2. Extract the update date from the resource page, and convert it to the format 'dd-mm-yyyy'.
    3. Find the download URL of the resource.
    4. If the download URL is relative, prepend the base URL 'https://data.humdata.org' to it.
    5. Store the formatted date and the final download URL in 'treated_doc'.
    6. Return the dictionary 'treated_doc'.
    """
    treated_doc = {}
    resource_page_url = _to_absolute_hdx_url(one_ressource.find("a", class_="c-resource-card__title")["href"])
    date_str = _get_hdx_resource_last_modified(resource_page_url)

    treated_doc["file_time"] = datetime.strptime(date_str, "%d %B %Y").strftime("%d-%m-%Y")

    download_url = one_ressource.find("a", class_="resource-url-analytics")["href"]

    treated_doc["download_url"] = _to_absolute_hdx_url(download_url)
    return treated_doc


def _get_hdx_file_infos(soup: BeautifulSoup, file_name: str):
    """
    Inputs:
    - soup (BeautifulSoup): Parsed HTML document containing the resources.
    - file_name (str): The name of the file to find within the resources. If set to "-", the first resource item is used.

    Outputs:
    - treated_doc (dict): A dictionary containing the information of the specified resource.

    Operation:
    1. Find all elements with the class 'resource-item' in the HTML document.
    2. If a specific file name is provided, find the last resource item with the matching title.
    3. If no specific file name is provided, use the first resource item.
    4. Extract its information using the '_get_one_ressource_infos' function.
    5. Return the extracted information as a dictionary.
    """

    resource_items = soup.find_all("div", class_="resource-item")
    if not resource_items:
        raise ValueError("No resource items found in the HDX dataset page")

    if file_name != "-":
        matching_resources = [
            one_ressource
            for one_ressource in resource_items
            if one_ressource.find("a", class_="c-resource-card__title")["title"] == file_name
        ]
        if not matching_resources:
            raise ValueError(f"HDX resource {file_name!r} not found in the dataset page")
        one_ressource = matching_resources[-1]
    else:
        one_ressource = resource_items[0]

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
