import json
import os
from collections import defaultdict

import requests
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

sources_url = "https://reliefweb.int/organizations"


def _extract_org_metadata(org_url):
    """
    Inputs:
    - org_url (str): URL to the organization's metadata page.

    Outputs:
    - org_metadata (Dict[str, str]): Dictionary containing the organization's type, headquarters, and homepage URL.

    Operation:
    1. Send a POST request to the given organization URL with a JSON payload specifying a limit of 6.
    2. Parse the response content as HTML.
    3. Extract the organization type from the HTML:
    3.1 Find the element with class 'rw-entity-meta__tag-label--type'.
    3.2 If the element and its next sibling exist, extract and strip the text content.
    3.3 If not, set the organization type to "UNKNOWN".
    4. Extract the headquarters location from the HTML:
    4.1 Find the element with class 'rw-entity-meta__tag-label--headquarters'.
    4.2 If the element and its next sibling exist, extract and strip the text content.
    4.3 If not, set the headquarters location to "UNKNOWN".
    5. Extract the homepage URL from the HTML:
    5.1 Find the element with class 'rw-entity-meta__tag-label--homepage'.
    5.2 If the element, its next sibling, and a link within the sibling exist, extract the href attribute of the link.
    5.3 If not, set the homepage URL to "UNKNOWN".
    6. Store the extracted information in a dictionary 'org_metadata' with keys 'type', 'headquarters', and 'homepage'.
    7. Return the 'org_metadata' dictionary.
    """

    response = requests.post(org_url, data=json.dumps({"limit": 6}))
    content = bs(response.text, "html.parser")

    # Extracting the required information
    organisation_type_element = content.find("dt", class_="rw-entity-meta__tag-label--type")
    if organisation_type_element and organisation_type_element.find_next_sibling("dd"):
        organisation_type = organisation_type_element.find_next_sibling("dd").text.strip()
    else:
        organisation_type = "UNKNOWN"  # Or some default value, e.g., "N/A"

    # Headquarters extraction with safety check
    headquarters_element = content.find("dt", class_="rw-entity-meta__tag-label--headquarters")
    if headquarters_element and headquarters_element.find_next_sibling("dd"):
        headquarters = headquarters_element.find_next_sibling("dd").text.strip()
    else:
        headquarters = "UNKNOWN"  # Or some default value

    # Homepage extraction with safety check
    homepage_element = content.find("dt", class_="rw-entity-meta__tag-label--homepage")
    if homepage_element and homepage_element.find_next_sibling("dd") and homepage_element.find_next_sibling("dd").find("a"):
        homepage = homepage_element.find_next_sibling("dd").find("a")["href"]
    else:
        homepage = "UNKNOWN"  # Or some default URL or placeholder

    org_metadata = {
        "type": organisation_type,
        "headquarters": headquarters,
        "homepage": homepage,
    }
    return org_metadata


def get_reliefweb_organisations(source_metadata_path: os.PathLike):
    """
    Inputs:
    - source_metadata_path (os.PathLike): Path to save the metadata of ReliefWeb organizations.

    Outputs:
    - None. Saves the extracted organization metadata as a JSON file.

    Operation:
    1. Send a POST request to 'sources_url' with a JSON payload specifying a limit of 6.
    2. Parse the response content as HTML.
    3. Find the container with the class 'rw-river-results'.
    4. Extract and parse the text content from span tags within the container to get the
       number of data per page and the total number of data.
    5. Calculate the total number of pages required to fetch all data.
    6. Initialize an empty defaultdict 'all_sources' to store organization metadata.
    7. Use a progress bar to track the extraction process:
    7.1 For each page, send a POST request to the page-wise URL with a JSON payload specifying a limit of 6.
    7.2 Parse the response content as HTML.
    7.3 Find all article elements with the class 'rw-river-article--card'.
    7.4 For each article, extract the organization name and URL.
    7.5 Call '_extract_org_metadata' to extract additional metadata for the organization.
    7.6 Update 'all_sources' with the organization metadata.
    7.7 Update the progress bar for each processed article.
    8. Save the 'all_sources' dictionary as a JSON file at 'source_metadata_path'.
    """

    response = requests.post(sources_url, data=json.dumps({"limit": 6}))
    # Assuming 'response' is the Response object
    content = bs(response.text, "html.parser")

    container = content.find("div", class_="rw-river-results")

    span_tags = container.find_all("span")

    _, n_data_per_page, tot_number_of_data = (int(tag.text.replace(",", "")) for tag in span_tags)
    # Find all span tags

    page_wise_url = sources_url + "?page={}"

    tot_n_pages = (
        tot_number_of_data // n_data_per_page
        if tot_number_of_data % n_data_per_page == 0
        else tot_number_of_data // n_data_per_page + 1
    )

    all_sources = defaultdict(dict)
    with tqdm(total=tot_number_of_data) as pbar:
        for page in range(tot_n_pages):
            response = requests.post(page_wise_url.format(page), data=json.dumps({"limit": 6}))
            soup = bs(response.text, "html.parser")

            articles = soup.find_all("article", class_="rw-river-article--card")

            # Extract information for each article
            for article in articles:
                # Extract organization name and URL
                org_name = article.find("h3", class_="rw-river-article__title").text.strip()
                org_url = article.find("h3", class_="rw-river-article__title").find("a")["href"]

                org_metadata = {"url": org_url}

                org_metadata.update(_extract_org_metadata(org_url))
                all_sources[org_name] = org_metadata

                pbar.update(1)

    # save as json
    with open(source_metadata_path, "w") as f:
        json.dump(all_sources, f, indent=4)
