import json
import os
from typing import List

import pandas as pd
from nltk.tokenize import sent_tokenize


def _flatten_list_of_lists(lst: List[List[str]]) -> List[str]:
    return [item for sublist in lst for item in sublist]


def _get_list_of_sentences(lst: List[str], step: int = 5) -> List[List[str]]:
    i = 0

    result = []  # Initialize an empty list to store the slices
    while (i + step) <= len(lst) + 1:  # Adjust the condition to ensure full coverage of the list
        added_list = lst[i : i + step]
        if len(added_list) > 1:
            result.append(lst[i : i + step])  # Append the slice of the list to the result list
        i += step - 1  # Move i forward by step size minus 1 for the overlap

    return result  # Return the list of lists


def _get_sentences_groups(text: str, n_sentences_per_group: int) -> List[str]:
    sentences = sent_tokenize(text)
    sentences = _get_list_of_sentences(sentences, step=n_sentences_per_group)
    return sentences


def _load_countries(country: str):
    countries_list = pd.read_csv(os.path.join("/data", "report_countries.csv"), header=None)[0].tolist()
    if country == "all":
        processed_countries = countries_list
    elif country in countries_list:
        processed_countries = [country]
    else:
        raise ValueError("Country not in list.")
    return processed_countries


def _load_tags():
    # Load the tags json
    with open(
        os.path.join(
            "/data",
            "datasources",
            "ohchr",
            "grouped_legal_framework_indicators.json",
        ),
        "r",
        encoding="utf-8",
    ) as tags_json:
        tags = json.load(tags_json)

    return tags


def _load_preprocess_df(
    input_file_path: str,
    n_sentences_per_group: int,
):
    print("============================= LOAD DATASET =============================")
    loaded_df = pd.read_csv(input_file_path)
    loaded_df["Sentences Groups"] = loaded_df["extracted_text"].apply(
        lambda x: _get_sentences_groups(x, n_sentences_per_group=n_sentences_per_group)
    )
    loaded_df = loaded_df.explode("Sentences Groups")
    return loaded_df
