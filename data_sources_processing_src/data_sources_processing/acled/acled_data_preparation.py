import json
import os
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict

import dotenv
import pandas as pd
import requests
from data_sources_processing.acled.create_locations_mapping import \
    _create_ai_based_mapping
from tqdm import tqdm

# API credentials
dotenv.load_dotenv()

api_key = os.getenv("ACLED_API_KEY")
email = os.getenv("CPAOR_EMAIL")

needed_columns = [
    "year",
    "country",
    "admin1",
    "event_type",
    "event_date",
    "latitude",
    "longitude",
    "fatalities",
]
# Load the list of countries
countries_list = pd.read_csv(
    os.path.join("/data", "report_countries.csv"), header=None
)[0].tolist()

# Define the date range
# start_date = "2017-01-01"
end_date = "2030-01-01"

mapping_countries = {
    "Congo DRC": "Democratic Republic of Congo",
    "Türkiye": "Turkey",
}
reversed_mapping_countries = {v: k for k, v in mapping_countries.items()}


def _get_number_of_events_evolution(events_df: pd.DataFrame, save_path: os.PathLike):
    """
    Process the number of events targeting civilians and save the data to a CSV file.
    """
    # Define the columns to keep
    if os.path.exists(save_path):
        past_number_of_events_targeting_civilians_df = pd.read_csv(save_path)
    else:
        past_number_of_events_targeting_civilians_df = pd.DataFrame(
            columns=["country", "year", "fatalities", "Number of Events"]
        )

    events_df["fatalities"] = events_df["fatalities"].astype(int)

    number_of_events_targeting_civilians_df = events_df.copy()

    number_of_events_targeting_civilians_df["Number of Events"] = number_of_events_targeting_civilians_df.groupby(["country", "year"])["year"].transform("count")

    number_of_events_targeting_civilians_df = (
        number_of_events_targeting_civilians_df.groupby(
            ["country", "year"], as_index=False
        ).agg({"fatalities": "sum", "Number of Events": "first"})
    ).reset_index(drop=True)

    number_of_events_targeting_civilians_df = pd.concat(
        [
            past_number_of_events_targeting_civilians_df,
            number_of_events_targeting_civilians_df,
        ]
    ).drop_duplicates(subset=["country", "year"], keep="last").sort_values(["country", "year"], ascending=True).reset_index(drop=True)

    number_of_events_targeting_civilians_df.to_csv(save_path, index=False)


def _get_individual_events_targetting_civilians_df(
    events_df: pd.DataFrame,
    save_path: os.PathLike,
    mapping_acled_to_fieldmaps_path: os.PathLike,
):
    """
    Process the number of fatalities and save the data to a CSV file.
    """
    # Define the columns to keep
    initial_number_of_fatalities_df = events_df.copy()[needed_columns]

    if os.path.exists(mapping_acled_to_fieldmaps_path) and os.path.getsize(mapping_acled_to_fieldmaps_path) != 0:
        with open(mapping_acled_to_fieldmaps_path) as f:
            acled_to_fieldmaps_one_country_mapping = json.load(f)
    else:
        acled_to_fieldmaps_one_country_mapping = defaultdict(dict)
        for one_country in tqdm(
            countries_list, desc="Processing ACLED countries mapping"
        ):
            acled_locations = (
                initial_number_of_fatalities_df[
                    initial_number_of_fatalities_df["country"] == one_country
                ]["admin1"]
                .unique()
                .tolist()
            )
            fieldmaps_locations = _load_adm_1_names(one_country)
            acled_to_fieldmaps_one_country_mapping[one_country] = (
                _create_ai_based_mapping(
                    one_country, acled_locations, fieldmaps_locations
                )
            )
            with open(mapping_acled_to_fieldmaps_path, "w") as f:
                json.dump(acled_to_fieldmaps_one_country_mapping, f)

    if os.path.exists(save_path):
        past_number_of_fatalities_df = pd.read_csv(save_path)
    else:
        past_number_of_fatalities_df = pd.DataFrame(
            columns=[
                "country",
                "admin1",
                "event_date",
                "latitude",
                "longitude",
                "event_type",
                "fatalities",
            ]
        )

    number_of_fatalities_df = pd.DataFrame()
    for one_country in countries_list:
        one_country_df = initial_number_of_fatalities_df[
            initial_number_of_fatalities_df["country"] == one_country
        ].copy()
        mapping_one_country = acled_to_fieldmaps_one_country_mapping[one_country]
        one_country_df["admin1"] = one_country_df["admin1"].apply(
            lambda x: mapping_one_country.get(x, x)
        )
        number_of_fatalities_df = pd.concat([number_of_fatalities_df, one_country_df])

    min_year = 2023
    number_of_fatalities_df = number_of_fatalities_df[
        number_of_fatalities_df["year"] >= min_year
    ]

    number_of_fatalities_df.drop(columns=["year"], inplace=True)

    number_of_fatalities_df = pd.concat(
        [past_number_of_fatalities_df, number_of_fatalities_df], axis=0
    ).copy()

    number_of_fatalities_df["latitude"] = pd.to_numeric(number_of_fatalities_df["latitude"], errors="coerce")
    number_of_fatalities_df["longitude"] = pd.to_numeric(number_of_fatalities_df["longitude"], errors="coerce")
    number_of_fatalities_df["fatalities"] = pd.to_numeric(number_of_fatalities_df["fatalities"], errors="coerce")
    number_of_fatalities_df[["country", "admin1", "event_type"]] = number_of_fatalities_df[["country", "admin1", "event_type"]].astype("string")
    number_of_fatalities_df["event_date"] = pd.to_datetime(number_of_fatalities_df["event_date"])

    for col in ["country", "admin1", "event_type"]:
        number_of_fatalities_df[col] = number_of_fatalities_df[col].str.strip().str.replace("'", "")
    number_of_fatalities_df["latitude"] = number_of_fatalities_df["latitude"].round(4)
    number_of_fatalities_df["longitude"] = number_of_fatalities_df["longitude"].round(4)

    df_clean = number_of_fatalities_df.copy().reset_index(drop=True)
    number_of_fatalities_df_grp = df_clean.groupby(["country", "admin1", "event_date", "latitude", "longitude", "event_type"], as_index=False).agg({"fatalities": "sum"})
    number_of_fatalities_df_grp.to_csv(save_path, index=False)


# Function to fetch data for a country
def fetch_country_data(country, url, start_date: str):

    response = requests.get(
        url,
        params={
            "key": api_key,
            "email": email,
            "country": mapping_countries.get(country, country),
            "event_date_where": "BETWEEN",
            "event_date": f"{start_date}|{end_date}",
            "limit": 0,  # Fetch all data
            "variables": "year,country,admin1,event_type,event_date,latitude,longitude,fatalities",
        },
    )
    return response.json()


def _load_adm_1_names(country: str):
    folder_path = os.path.join(
        "/data",
        "polygons_data",
        "processed_data",
        "adm1_polygons",
        f"{country}.geojson",
    )
    with open(folder_path) as f:
        geojson_data = json.load(f)

    data = geojson_data["geojson"]["features"]
    final_names = []
    for one_loc in data:
        final_names.append(one_loc["properties"]["name"])

    return final_names


def _string_similarity(str1, str2):
    # Calculate the similarity between two strings using SequenceMatcher
    return SequenceMatcher(None, str1, str2).ratio()


def _find_maximum_matches(list1, list2):
    matched_pairs = {}
    while list1 and list2:
        closest_pair = None
        max_similarity = 0.7
        for loc1 in list1:
            for loc2 in list2:
                similarity = _string_similarity(loc1, loc2)
                if similarity > max_similarity:
                    max_similarity = similarity
                    closest_pair = (loc1, loc2)

        if closest_pair:
            matched_pairs[closest_pair[0]] = closest_pair[1]
            list1.remove(closest_pair[0])
            list2.remove(closest_pair[1])
        else:
            break
    return matched_pairs


# def _create_matching_dict(
#     acled_geolocations: List[str], fieldmaps_geolocations: List[str]
# ):
#     final_matches = {}
#     # Step 1: Remove exact matches
#     exact_matches, list1, list2 = _remove_exact_matches(
#         acled_geolocations, fieldmaps_geolocations
#     )
#     final_matches.update(exact_matches)

#     # Step 2: Find maximum matches based on string similarity
#     maximum_matches = _find_maximum_matches(list1, list2)
#     final_matches.update(maximum_matches)

#     return final_matches


# def _match_acled_locations_to_fieldmaps(one_loc: str, maping_dict: Dict[str, str]):
#     if one_loc in maping_dict:
#         return maping_dict[one_loc]
#     else:
#         # print(f"No match found for {one_loc}")
#         return one_loc


# def _postprocess_adm_level(number_of_fatalities_df: pd.DataFrame, country: str):

#     level1_names = _load_adm_1_names(reversed_mapping_countries.get(country, country))
#     level1_mapping = _create_matching_dict(
#         number_of_fatalities_df[f"admin1"].unique().tolist(),
#         level1_names,
#     )
#     number_of_fatalities_df[f"admin1"] = number_of_fatalities_df[f"admin1"].apply(
#         lambda x: _match_acled_locations_to_fieldmaps(x, level1_mapping)
#     )
#     return number_of_fatalities_df


def _get_acled_data(datasets_metadata: Dict[str, Any], data_output_path: os.PathLike):
    """

    Inputs:
    - datasets_metadata (Dict[str, Any]): Metadata of the dataset.
    - data_output_path (os.PathLike): Path to the directory where the data will be saved.

    Outputs:
    - datasets_metadata (Dict[str, Any]): The input metadata is returned unchanged.

    Operation:
    1. Initialize an empty list 'all_data' to store data from all countries.
    2. Iterate through each country in 'countries_list':
    2.1 Fetch the data for the country using 'fetch_country_data' function and the website URL from the metadata.
    2.2 If the fetched data contains a 'data' field and it is not None, extend 'all_data' with this data.
    3. Convert the 'all_data' list to a DataFrame, keeping only the 'needed_columns'.
    4. Ensure the 'year' column in the DataFrame is of integer type.
    5. Generate a CSV file of the number of events evolution and save it to the specified path.
    6. Generate a CSV file of individual events targeting civilians and save it to the specified path.
    7. Return the input 'datasets_metadata'.
    """

    events_df = pd.DataFrame()
    if datasets_metadata["last_update_time"] == "":
        start_date = "2017-01-01"
    else:
        start_date = "-".join(datasets_metadata["last_update_time"].split("-")[::-1])
    # Fetch data for all countries and combine
    for country in tqdm(countries_list, desc="Processing ACLED countries"):
        data = fetch_country_data(country, datasets_metadata["website_url"], start_date)

        if "data" in data and data["data"]:
            one_country_df = pd.DataFrame(data["data"])[needed_columns]
            one_country_df["country"] = one_country_df["country"].apply(
                lambda x: reversed_mapping_countries.get(x, x)  # Apply reverse mapping
            )
            events_df = pd.concat([events_df, one_country_df])

    if len(events_df):
        events_df["year"] = events_df["year"].astype(int)

        _get_number_of_events_evolution(
            events_df,
            os.path.join(data_output_path, "acled", "number_events_evolution.csv"),
        )
        _get_individual_events_targetting_civilians_df(
            events_df,
            save_path=os.path.join(
                data_output_path, "acled", "individual_events_targetting_civilians_new.csv"
            ),
            mapping_acled_to_fieldmaps_path=os.path.join(
                data_output_path, "acled", "mapping_acled_to_fieldmaps.json"
            ),
        )
    else:
        print("The ACLED events data is empty.")

    return datasets_metadata
