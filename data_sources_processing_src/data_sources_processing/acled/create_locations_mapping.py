import os
import json
import logging
import re
from ast import literal_eval
from copy import copy
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

system_prompt = (
    "I want to create a mapping between different geolocations in %s. "
    + "I will provide you with two lists of geolocations al slightly differnt one from another, "
    + "and you will need to create a mapping for items from the first to the second list so I can complete the database. "
    + "Return the output as a JSON format where the key comes from the first list and the value from the second list. "
    + "If there is no match, return an empty dict."
)


def _extract_and_evaluate_first(string):
    """
    Inputs:
    - string (str): The input string to search for the first occurrence of '{' or '['.

    Outputs:
    - match (str): The first matched substring enclosed within '{}' or '[]', or
      the entire input string if no brackets are found.

    Operation:
    Return the extracted matched substring.
    """

    match = re.search(r"\{([^\}]*)\}", string).group(0)

    return match


def _postprocess_json_string(s):
    # Remove trailing commas from objects and arrays
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    s = (
        s.replace("```", "")
        .replace("json", "")
        .replace("\n{", "{")
        .replace("}\n", "}")
        .replace("\n", " ")
        .replace("\t", " ")
        .replace("\\xa0", "\\u00A0")
        .strip()
    )

    return _extract_and_evaluate_first(s)


def _ai_mapping_locations(
    country: str, acled_locations: List[str], fieldmaps_locations: List[str]
):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=openai_api_key)

    if len(acled_locations) == 0 or len(fieldmaps_locations) == 0:
        matches = {}
    else:

        response = (
            client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt.format(country)},
                    {
                        "role": "user",
                        "content": f"{json.dumps(acled_locations)}, {json.dumps(fieldmaps_locations)}",
                    },
                ],
            )
            .choices[0]
            .message.content
        )

        output_text = _postprocess_json_string(response)

        try:
            gpt_extracted_infos = literal_eval(output_text)
        except Exception:
            try:
                gpt_extracted_infos = json.loads(output_text)
            except Exception as e:
                logger.error("formatting failed", e, output_text)
                gpt_extracted_infos = {}

        matches = gpt_extracted_infos

    return matches


def _remove_exact_matches(l1: List[str], l2: List[str]):
    list1 = copy(l1)
    list2 = copy(l2)
    exact_matches = {loc1: loc2 for loc1 in list1 for loc2 in list2 if loc1 == loc2}
    for one_loc in exact_matches:
        list1.remove(one_loc)
        list2.remove(one_loc)
    return exact_matches, list1, list2


def _create_ai_based_mapping(
    country: str, acled_locations: List[str], fieldmaps_locations: List[str]
):
    final_matches = {}
    # Step 1: Remove exact matches
    exact_matches, remaining_acled_locations, remaining_fieldmaps_locations = (
        _remove_exact_matches(acled_locations, fieldmaps_locations)
    )

    # Step 2: Find maximum matches based on string similarity
    ai_based_matches = _ai_mapping_locations(
        country, remaining_acled_locations, remaining_fieldmaps_locations
    )
    # print(ai_based_matches)
    final_matches.update(ai_based_matches)
    return final_matches
