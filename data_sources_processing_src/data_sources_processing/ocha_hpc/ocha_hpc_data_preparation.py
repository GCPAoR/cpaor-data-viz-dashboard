import os
from typing import Any, Dict
import requests
import logging
from tqdm import tqdm
from datetime import datetime
import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

current_year = datetime.now().year
treated_years = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
treated_years = list(filter(lambda x: x <= current_year, treated_years))

countries_mapping = {
    # "Central African Republic": "CAR",
    "Congo, The Democratic Republic of the": "Congo DRC",
    "Syrian Arab Republic": "Syria",
    "Venezuela, Bolivarian Republic of": "Venezuela",
    "occupied Palestinian territory": "Palestine",
}

children_in_need_desc_names = [
    "Protection de l'enfant",
    "Child Protection",
    "Protección de la infancia",
]


def _get_ocha_hpc_data(
    datasets_metadata: Dict[str, Any], data_output_path: os.PathLike
):

    caseload_data, global_funding, country_funding = _get_key_pin_informations_all_years()
    caseload_data.to_csv(
        os.path.join(
            data_output_path, "ocha_hpc", datasets_metadata["saved_file_name"]
        ),
        index=False,
    )
    global_funding.to_csv(
        os.path.join(
            data_output_path, "ocha_hpc", datasets_metadata["global_funding"]
        ),
        index=False
    )
    country_funding.to_csv(
        os.path.join(
            data_output_path, "ocha_hpc", datasets_metadata["country_funding"]
        ),
        index=False
    )
    return datasets_metadata


def _get_key_pin_informations_all_years():
    """
    Retrieves key PIN (People in Need) information aggregated across multiple years.

    Returns:
    - pd.DataFrame: DataFrame containing aggregated key information across years with columns:
    - 'country': Country name.
    - 'children_in_need': Number of children in need based on specific caseload descriptions.
    - 'targeted_children': Number of targeted children based on specific caseload descriptions.
    - 'tot_pop_in_need': Total population in need based on general protection caseloads.
    - 'year': Year of the humanitarian response plan or flash appeal.
    - 'plan_type': Type of plan (e.g., 'Humanitarian response plan', 'Flash appeal').

    Operation:
    1. Initializes an empty DataFrame 'final_dataset' to store aggregated results.
    2. Iterates over each year in 'treated_years' to retrieve key information using '_get_key_informations_project_one_year'.
    3. Appends results from each year to 'final_dataset'.
    4. Filters 'final_dataset' to include rows with non-null values in columns related to children in need,
       targeted children, or total population in need.
    5. Sorts and resets the index of 'final_dataset' for clarity and consistency.
    6. Returns 'final_dataset' containing aggregated key PIN information across multiple years.
    """

    final_dataset = pd.DataFrame()
    total_global_funding = pd.DataFrame()
    total_country_level_funding = pd.DataFrame()
    for year in tqdm(treated_years, desc="Processing years"):
        output_df, global_funding, country_level_funding = _get_key_informations_project_one_year(year)

        if len(output_df) > 0:
            final_dataset = final_dataset._append(
                output_df
            )
        if len(global_funding):
            total_global_funding = total_global_funding._append(global_funding)
        if len(country_level_funding):
            total_country_level_funding = total_country_level_funding._append(country_level_funding)

    final_dataset = (
        final_dataset[
            (~final_dataset["children_in_need"].isna())
            | (~final_dataset["targeted_children"].isna())
            | (~final_dataset["tot_pop_in_need"].isna())
        ]
        .sort_values(by=["country", "year"])
        .reset_index(drop=True)
    )

    return final_dataset, total_global_funding, total_country_level_funding


def _get_key_informations_project_one_year(treated_year: int, timeout: int=30):
    """
    Retrieves key information related to children in need and population in need from a specified year using an API endpoint.

    Args:
    - treated_year (int): The year for which data is retrieved.

    Returns:
    - pd.DataFrame: DataFrame containing key information:
    - 'country': Country name.
    - 'children_in_need': Number of children in need based on specific caseload descriptions.
    - 'targeted_children': Number of targeted children based on specific caseload descriptions.
    - 'tot_pop_in_need': Total population in need based on general protection caseloads.
    - 'year': Year of the humanitarian response plan or flash appeal.
    - 'plan_type': Type of plan (e.g., 'Humanitarian response plan', 'Flash appeal').

    Operation:
    1. Constructs an API URL based on the specified year to retrieve plan summaries
       including indicators, caseloads, and financials.
    2. Makes a GET request to the API endpoint and checks for a successful response (status code 200).
    3. Parses JSON content from the response and extracts relevant data into a DataFrame 'all_data'.
    4. Filters 'all_data' to include only plans of type 'Humanitarian response plan' or 'Flash appeal'.
    5. Iterates over each plan entry to extract country-specific and caseload-specific data:
    - Retrieves child protection caseloads data and general protection caseloads data.
    - Appends extracted information to the 'final_dataset' DataFrame.
    6. Returns 'final_dataset' containing aggregated key information for the specified year.
    """

    # Specify the API URL
    # url = f"https://blue.dev.api-hpc-tools.ahconu.org/v2/public/planSummary?year={treated_year}&includeIndicators=true&includeCaseloads=true&includeFinancials=true"  # noqa
    url = f"https://api.hpc.tools/v2/public/planSummary?year={treated_year}&includeIndicators=true&includeCaseloads=true&includeFinancials=true"  # noqa

    # Make the GET request
    try:
        response = requests.get(url, timeout=timeout)
    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred for the year {treated_year}")
        return pd.DataFrame()
    if response.status_code != 200:
        logger.error(f"Payload data not received as status code is {response.status_code}")
        return pd.DataFrame()

    data = response.json()

    if len(data["data"]["planData"]) == 0:
        return pd.DataFrame()

    all_data = pd.DataFrame(data["data"]["planData"])

    global_funding_per_year_df = get_global_funding(all_data=all_data, treated_year=treated_year)

    all_data = all_data[
        all_data.planType.isin(["Humanitarian response plan", "Flash appeal"])
    ]

    total_funding_country_level_df = pd.DataFrame()
    final_dataset = pd.DataFrame()
    for i, row in all_data.iterrows():
        country = row["planCountries"][0]["country"]
        # Append the filtered row to the final dataset
        protection_caseloads = process_protection_caseloads(row, country)
        if protection_caseloads:
            final_dataset = final_dataset._append(protection_caseloads, ignore_index=True)
        # Country level funding
        country_funding = get_country_level_funding(row, country)
        total_funding_country_level_df = total_funding_country_level_df._append(country_funding, ignore_index=True)

    total_funding_country_level_df = total_funding_country_level_df.groupby(["country", "year"]).agg({
        "funding_requested": "sum",
        "funding_received": "sum",
    }).reset_index()
    total_funding_country_level_df.sort_values(by=["country"], inplace=True)

    return final_dataset, global_funding_per_year_df, total_funding_country_level_df


def extract_max_cumulative_reach(row):
    """Extract the max value for the cumulative reach in CP beneficiaries"""
    try:
        values = [(
                item.get("cumulativeReach/peopleReached(cumulative)") or
                item.get("cumulativeReach/personnesAtteintes(cumul)") or
                item.get("cumulativeReach/personasAtendidas(acumulativo)")
            )
            for item in row
            if isinstance(item, dict) and (
                item.get("cumulativeReach/peopleReached(cumulative)") or
                item.get("cumulativeReach/personnesAtteintes(cumul)") or
                item.get("cumulativeReach/personasAtendidas(acumulativo)")
            )
        ]
        return max(values) if values else 0
    except Exception:
        return 0


def process_protection_caseloads(row: pd.DataFrame, country: str):
    """Get the Protection caseloads"""
    protection_caseloads = pd.DataFrame(row["caseloads"])
    if len(protection_caseloads) == 0:
        return

    child_protection_caseloads_data = protection_caseloads[
        protection_caseloads["caseloadCustomRef"].apply(lambda x: "PRO-CPN" in x)
    ]
    if len(child_protection_caseloads_data) > 0:
        children_in_need = child_protection_caseloads_data.inNeed.iloc[0]
        targeted_children = child_protection_caseloads_data.target.iloc[0]
    else:
        children_in_need = None
        targeted_children = None

    general_protection_caseloads_data = protection_caseloads[
        protection_caseloads["caseloadCustomRef"] == "BP1"
    ]
    if len(general_protection_caseloads_data) > 0:
        tot_pop_in_need = general_protection_caseloads_data.inNeed.iloc[0]
    else:
        tot_pop_in_need = None

    cp_targeted = child_protection_caseloads_data["target"].sum()

    cp_beneficiaries_lst = child_protection_caseloads_data["measurements"].apply(extract_max_cumulative_reach)
    cp_beneficiaries_df = pd.to_numeric(cp_beneficiaries_lst, errors="coerce")
    cp_beneficiaries_df = cp_beneficiaries_df[~pd.isna(cp_beneficiaries_df)]
    cp_beneficiaries_sum = float(cp_beneficiaries_df.sum())

    # Prepare the row data
    row_data = {
        "country": countries_mapping.get(country, country),
        "children_in_need": children_in_need,
        "targeted_children": targeted_children,
        "tot_pop_in_need": tot_pop_in_need,
        "cp_targeted": cp_targeted,
        "cp_beneficiaries": cp_beneficiaries_sum,
        "year": row["planYear"],
        "plan_type": row["planType"],
    }

    # Filter out None or NaN values
    filtered_row_data = {k: v for k, v in row_data.items() if pd.notna(v)}
    return filtered_row_data

def extract_iso3(plan_countries: list[dict]):
    """Extract all ISO3"""
    try:
        return [country['iso3'] for country in plan_countries if 'iso3' in country]
    except (ValueError, SyntaxError):
        return []

def get_global_funding(all_data: pd.DataFrame, treated_year: int):
    """Get the global funding per year"""
    total_global_funding_requested = all_data["financialData"].apply(
        lambda x: x["requirements"]["totalRequirements"]
    ).sum()

    total_global_funding_received = all_data["financialData"].apply(
        lambda x: x["funding"]["totalFundingInsidePlan"]
    ).sum()

    protection_caseloads = all_data["caseloads"].explode().dropna().apply(pd.Series)

    child_protection_caseloads_data = protection_caseloads[
        protection_caseloads["caseloadCustomRef"].apply(lambda x: "PRO-CPN" in x)
    ]
    child_protection_caseloads_data["target"] = pd.to_numeric(child_protection_caseloads_data["target"], errors="coerce")
    cp_targeted = child_protection_caseloads_data["target"].sum()

    cp_beneficiaries_lst = child_protection_caseloads_data["measurements"].apply(extract_max_cumulative_reach)
    cp_beneficiaries_df = pd.to_numeric(cp_beneficiaries_lst, errors="coerce")
    cp_beneficiaries_df = cp_beneficiaries_df[~pd.isna(cp_beneficiaries_df)]
    cp_beneficiaries_sum = float(cp_beneficiaries_df.sum())

    # Extract ISO3 codes
    filtered_all_data = all_data[all_data['financialData'].apply(lambda x: len(x) > 0)]
    iso3_list = filtered_all_data['planCountries'].apply(extract_iso3).explode().dropna().unique().tolist()

    return pd.DataFrame([
        {
            "year": treated_year,
            "funding_requested": total_global_funding_requested,
            "funding_received": total_global_funding_received,
            "cp_targeted": cp_targeted,
            "cp_beneficiaries": cp_beneficiaries_sum,
            "total_countries": len(iso3_list)
        }
    ])

def get_country_level_funding(row: pd.DataFrame, country: str):
    """Get the country level funding"""
    funding_requested = row["financialData"]["requirements"]["totalRequirements"]
    funding_received = row["financialData"]["funding"]["totalFundingInsidePlan"]
    row_data = {
        "country": countries_mapping.get(country, country),
        "funding_requested": funding_requested,
        "funding_received": funding_received,
        "year": row["planYear"],
        "plan_type": row["planType"]
    }
    return row_data
