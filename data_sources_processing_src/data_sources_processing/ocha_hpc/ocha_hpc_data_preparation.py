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


def _get_key_informations_project_one_year(treated_year: int, timeout: int = 90):
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

    if not len(data["data"]["planData"]):
        return pd.DataFrame()

    all_data = pd.DataFrame(data["data"]["planData"])

    # Apply filters
    # includedGHO == True ensures only one country is in planCountries
    all_data = all_data[
        (all_data.includedGHO) & (all_data.planType.isin(["Humanitarian response plan", "Flash appeal", "Humanitarian needs and response plan"]))
    ]

    global_funding_per_year_df = get_global_funding(all_data=all_data, treated_year=treated_year)

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
        
        if country_funding:
            total_funding_country_level_df = total_funding_country_level_df._append(country_funding, ignore_index=True)

    # total_funding_country_level_df = total_funding_country_level_df.groupby(["country", "year", "plan_type"]).agg({
    #     "funding_requested": "sum",
    #     "funding_received": "sum",
    # }).reset_index()
    total_funding_country_level_df.sort_values(by=["country", "year"], inplace=True)

    return final_dataset, global_funding_per_year_df, total_funding_country_level_df


def process_protection_caseloads(row: pd.Series, country: str):
    """Get the Protection caseloads based on country"""
    row_data_df = row.to_frame().T
    if row_data_df.empty:
        return

    total_children_targeted, total_children_reached, total_children_in_need, total_population_in_need = calculate_caseloads_statistics(row_data_df)

    # Prepare the row data
    row_data = {
        "name": row["name"],
        "plan_id": row["planId"],
        "country": countries_mapping.get(country, country),
        "children_in_need": total_children_in_need,
        "targeted_children": total_children_targeted,
        "tot_pop_in_need": total_population_in_need,
        "cp_targeted": total_children_targeted,
        "cp_beneficiaries": total_children_reached,
        "year": row["planYear"],
        "plan_type": row["planType"]
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


def process_financial_row_data(row: pd.Series, key: str, cp_cluster_code: int = 12):
    """Process financial data row-wise"""
    df_ = pd.DataFrame(row)
    if not df_.empty:
        df_ = df_.dropna(subset=["globalClusterId"])
    if not df_.empty:
        df_ = df_[df_["globalClusterId"] == cp_cluster_code]
    return df_[key].sum() if len(df_) else 0


def handle_measurement_data(row: pd.Series, mon_p_id: int):
    """Handle measuremet data"""
    if row.empty:
        return 0
    measurements = row["measurements"]
    # Incase there is only one measurements use that one.
    if len(measurements) == 1:
        mon_p_id = measurements[0]["monitoringPeriodId"]
    for measurement in measurements:
        if measurement["monitoringPeriodId"] == mon_p_id:
            for item_key in measurement.keys():
                if "cumulativeReach" in item_key:
                    return measurement[item_key] or 0
    return 0


def calculate_sum(df_col: pd.Series):
    data_list = df_col.to_list()
    data_df = pd.to_numeric(data_list, errors="coerce")
    data_df = data_df[~pd.isna(data_df)]
    return float(data_df.sum())


def calculate_caseloads_statistics(data_df: pd.DataFrame):
    caseloads_df = data_df[["caseloads", "monitoringPeriods"]]
    # Monitoring Periods are arranged in ascending (date wise)
    caseloads_df = caseloads_df.copy()
    caseloads_df.loc[:, "monitoring_period_id"] = caseloads_df["monitoringPeriods"].apply(lambda x: x[-1]["id"])
    caseloads_df = caseloads_df[["caseloads", "monitoring_period_id"]]

    caseloads_explode_df = caseloads_df.explode("caseloads")
    caseloads_details_df = pd.json_normalize(caseloads_explode_df["caseloads"])
    caseloads_details_df.reset_index(drop=True)
    caseloads_final_df = caseloads_explode_df.drop(columns="caseloads").reset_index(drop=True)

    caseloads_final_df = pd.concat([caseloads_final_df, caseloads_details_df], axis=1)

    # Calculate the caseloads statistics for Children
    cp_caseloads_final_df = caseloads_final_df[caseloads_final_df["availableGlobalClusterCode"] == "PRO-CPN"]
    cp_caseloads_final_df.reset_index(inplace=True, drop=True)

    if not cp_caseloads_final_df.empty:
        cp_caseloads_final_df = cp_caseloads_final_df.copy()
        cp_caseloads_final_df.loc[:, "children_reached"] = cp_caseloads_final_df.apply(
            lambda row: handle_measurement_data(row, row["monitoring_period_id"]),
            axis=1
        )

        total_children_targeted = calculate_sum(cp_caseloads_final_df["target"])
        total_children_in_need = calculate_sum(cp_caseloads_final_df["inNeed"])

        total_children_reached = cp_caseloads_final_df["children_reached"].apply(
            lambda x: float(x) if x is not None or (isinstance(x, str) and x.isnumeric()) else 0
        ).sum()
    else:
        total_children_in_need = total_children_targeted = total_children_reached = 0

    # Calculate the caseloads statistics for General People
    general_protection_caseloads_data = caseloads_final_df[caseloads_final_df["caseloadCustomRef"] == "BP1"]
    if len(general_protection_caseloads_data) > 0:
        total_population_in_need = calculate_sum(general_protection_caseloads_data["inNeed"])
    else:
        total_population_in_need = None

    return (
        total_children_targeted,
        total_children_reached,
        total_children_in_need,
        total_population_in_need
    )


def get_global_funding(all_data: pd.DataFrame, treated_year: int):
    """Get the global funding per year"""
    financial_requirements_df = all_data["financialData"].apply(
        lambda x: x.get("requirements", {}).get("breakdown", {}).get("byGlobalCluster", None)
    )
    financial_requirements_df = financial_requirements_df.apply(process_financial_row_data, key="requirements")
    total_global_funding_requested = financial_requirements_df.sum()

    financial_received_df = all_data["financialData"].apply(
        lambda x: x.get("funding", {}).get("breakdown", {}).get("byGlobalCluster", None)
    )
    financial_received_df = financial_received_df.apply(process_financial_row_data, key="funding")
    total_global_funding_received = financial_received_df.sum()

    total_children_targeted, total_children_reached, _, _ = calculate_caseloads_statistics(all_data)

    # Extract ISO3 codes
    filtered_all_data = all_data[all_data['financialData'].apply(lambda x: len(x) > 0)]
    iso3_list = filtered_all_data['planCountries'].apply(extract_iso3).explode().dropna().unique().tolist()

    return pd.DataFrame([
        {
            "year": treated_year,
            "funding_requested": total_global_funding_requested,
            "funding_received": total_global_funding_received,
            "cp_targeted": total_children_targeted,
            "cp_beneficiaries": total_children_reached,
            "total_countries": len(iso3_list)
        }
    ])


def get_country_level_funding(row: pd.Series, country: str):
    """Get the country level funding"""
    row_data_df = row.to_frame().T

    if row_data_df.empty:
        return {}

    financial_requirements_df = row_data_df["financialData"].apply(
        lambda x: x.get("requirements", {}).get("breakdown", {}).get("byGlobalCluster", None)
    )

    financial_requirements_df = financial_requirements_df.apply(process_financial_row_data, key="requirements")

    total_country_funding_requested = financial_requirements_df.sum()

    financial_received_df = row_data_df["financialData"].apply(
        lambda x: x.get("funding", {}).get("breakdown", {}).get("byGlobalCluster", None)
    )

    financial_received_df = financial_received_df.apply(process_financial_row_data, key="funding")
    total_country_funding_received = financial_received_df.sum()

    row_data = {
        "name": row["name"],
        "country": countries_mapping.get(country, country),
        "funding_requested": total_country_funding_requested,
        "funding_received": total_country_funding_received,
        "year": row["planYear"],
        "plan_type": row["planType"]
    }
    return row_data
