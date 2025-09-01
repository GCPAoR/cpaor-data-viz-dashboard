import logging
import os
from typing import Any, Dict
import ast
import dotenv
import pandas as pd
import requests

dotenv.load_dotenv()
# API credentials
username = os.getenv("CPAOR_EMAIL")
password = os.getenv("ACAPS_PASSWORD")

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

# Get the authentication token
auth_response = requests.post(
    url="https://api.acaps.org/api/v1/token-auth/",
    data={"username": username, "password": password},
)
auth_token = auth_response.json().get("token")

# Base URL for API requests
headers = {"Authorization": f"Token {auth_token}"}

original_name_to_acaps_name = {
    "Congo DRC": "DRC",
    "Central African Republic": "CAR",
}

acaps_name_to_original_name = {v: k for k, v in original_name_to_acaps_name.items()}


# Function to fetch data for a given page
def _fetch_data(base_url: str, page: int, country: str, start_date: str, use_sample: bool, timeout: int = 120):
    params = {
        "_internal_filter_date_gte": start_date,
        "page": page,
        "country": country,
    }
    if use_sample:
        params["_internal_filter_date_lte"] = "2023-09-02"
    response = requests.get(
        url=base_url,
        headers=headers,
        params=params,
        timeout=timeout
    )
    return response.json()


def raw_data_preprocessing(raw_df):
    """Process raw data pre-processing"""
    def safe_eval(x):
        try:
            output = ast.literal_eval(x)
            if isinstance(output, (list, tuple)):
                return output[0]
            return output
        except (ValueError, SyntaxError):
            return None   # mark invalid rows

    raw_df["country"] = raw_df["country"].apply(safe_eval)
    raw_df["country"] = raw_df["country"].apply(lambda c: original_name_to_acaps_name.get(c, c))
    raw_df["source_date"] = pd.to_datetime(raw_df["source_date"])
    raw_df.sort_values(by=["country", "source_date"], inplace=True)
    raw_df.drop_duplicates(subset="country", keep="last", inplace=True)
    # Drop rows where eval failed
    raw_df = raw_df.dropna(subset=["country"]).reset_index(drop=True)
    return raw_df


def fetch_dataset(base_url: str, raw_pulled_data: pd.DataFrame, ref_start_date: str, use_sample: bool):
    # Fetch all pages of data
    all_data = []

    if use_sample:
        countries = ["Ukraine"]
    else:
        countries = pd.read_csv(
            os.path.join("/data", "report_countries.csv"),
            header=None,
            names=["country"],
        ).country.tolist()

    acaps_countries = [original_name_to_acaps_name.get(c, c) for c in countries]

    raw_data_df = raw_data_preprocessing(raw_pulled_data)

    country_last_infer_date = []

    for country in acaps_countries:
        df_temp = raw_data_df[raw_data_df["country"] == country]
        if len(df_temp):
            start_date = df_temp["source_date"].iloc[0].date().strftime("%d-%m-%Y")
        else:
            start_date = ref_start_date

        country_last_infer_date.append({
            "country": acaps_name_to_original_name.get(country, country),
            "last_infer_date": start_date,
        })

        logger.info(f"Pulling data for the country {country}")

        page = 1
        while True:
            if page % 10 == 0:
                logger.info(f"Scraping acaps protection indicators page {page} for the country {country}")

            data = _fetch_data(base_url, page, country, start_date, use_sample)
            if len(data.get("results", [])) > 0:
                all_data.extend(data["results"])
                page += 1
            else:
                break

    country_to_infer_date_file_path = os.path.join("/data", "datasources", "acaps_protection_indicators", "raw_datasets", "country_to_last_infer_date.csv")

    df_country_last_infer_date = pd.DataFrame(country_last_infer_date)
    df_country_last_infer_date.to_csv(country_to_infer_date_file_path, index=False)

    # Convert the data into a DataFrame
    results_df = pd.json_normalize(all_data)

    if len(results_df) > 0:
        results_df["country"] = results_df["country"].apply(lambda x: [acaps_name_to_original_name.get(c, c) for c in x])

        results_df = results_df.drop(columns=["additional_sources", "adm1"]).dropna(subset=["country", "justification"])

    return results_df


def pull_acaps_protection_indicators(datasets_metadata: Dict[str, Any], output_path: os.PathLike, use_sample: bool):
    if os.path.exists(output_path):
        raw_pulled_data = pd.read_csv(output_path)
    else:
        raw_pulled_data = pd.DataFrame()

    last_file_time = datasets_metadata["latest_file_info"]["file_time"]

    if last_file_time == "":
        ref_start_date = "2021-01-01"
    else:
        ref_start_date = "-".join(last_file_time.split("-")[::-1])

    raw_pulled_data_temp = raw_pulled_data.copy()
    raw_pulled_data_temp = raw_pulled_data_temp[["country", "source_date"]]

    new_dataset = fetch_dataset(datasets_metadata["website_url"], raw_pulled_data_temp, ref_start_date, use_sample)

    final_dataset = pd.concat([raw_pulled_data, new_dataset], ignore_index=True)
    final_dataset.to_csv(output_path, index=False)
