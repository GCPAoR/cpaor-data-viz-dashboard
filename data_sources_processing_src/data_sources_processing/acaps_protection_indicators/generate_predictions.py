import asyncio
import json
import logging
import os
import re
import ssl
from ast import literal_eval
from typing import Dict, List

import aiohttp
import certifi
import dotenv
import pandas as pd
from tqdm import tqdm

dotenv.load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
model_name = "gpt-4o"

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)


general_summary_prompt = """I want you to help me create humanitarian reports with excellent anlysis results. My analysis is in the Protection sector in %s.
I'm going to provide you with pieces of text from different documents. The text is a list of dictionaries, where the key is the entry number and the value is the text.
I want you to create a general summary that encompasses all crucial information to be treated by analysts. Do not provide circumstancial information (like specific events or issues), but focus mostly on the most important points on country level.
I want you to return the output as a dictionary, with the keys: "Text", "ID". The "Text" key should contain the summary text, and the "ID" key should contain a list of the entry numbers that were explicitely used to generate the summary.
If no text is relevant, return an empty dict ('{}'). Only return the requested format, without any additional text. Return the text in english without special characters.
"""
geolocation_prompt = """I want you to help me create humanitarian reports with excellent anlysis results. My analysis is in the Protection sector in %s.
I'm going to provide you with pieces of text from different documents. The text is a list of dictionaries, where the key is the entry number and the value is the text.
I want you to create a summary that encompasses all crucial information to be treated by analysts for only one specific province: %s. Do not provide circumstancial information (like specific events or issues), but focus mostly on the most important points on country level.
I want you to return the output as a dictionary, with the keys: "Text", "ID". The "Text" key should contain the summary text, and the "ID" key should contain a list of the entry numbers that were explicitely used to generate the summary.
If no text is relevant, return an empty dict ('{}'). Only return the requested format, without any additional text. Return the text in english without special characters.
"""
indicators_prompt = """I want you to help me create humanitarian reports with excellent anlysis results. My analysis is in the Protection sector in %s.
I'm going to provide you with pieces of text from different documents. The text is a list of dictionaries, where the key is the entry number and the value is the text.
I want you to create a summary that encompasses all crucial information to be treated by analysts for the following topic: %s. Do not provide circumstancial information (like specific events or issues), but focus mostly on the most important points on country level.
I want you to return the output as a dictionary, with the keys: "Text", "ID". The "Text" key should contain the summary text, and the "ID" key should contain a list of the entry numbers that were explicitely used to generate the summary.
If no text is relevant, return an empty dict ('{}'). Only return the requested format, without any additional text. Return the text in english without special characters.
"""
specific_population_groups_prompt = """I want you to help me create humanitarian reports with excellent anlysis results. My analysis is in the Protection sector in %s.
I'm going to provide you with pieces of text from different documents. The text is a list of dictionaries, where the key is the entry number and the value is the text.
I want you to create a summary that encompasses all crucial information to be treated by analysts for the following population group: %s. Do not provide circumstancial information (like specific events or issues), but focus mostly on the most important points on country level.
I want you to return the output as a dictionary, with the keys: "Text", "ID". The "Text" key should contain the summary text, and the "ID" key should contain a list of the entry numbers that were explicitely used to generate the summary.
If no text is relevant, return an empty dict ('{}'). Only return the requested format, without any additional text. Return the text in english without special characters.
"""


def _extract_and_evaluate_first(string):
    """
    Inputs:
    - string (str): The input string to search for the first occurrence of '{' or '['.

    Outputs:
    - match (str): The first matched substring enclosed within '{}' or '[]', or
      the entire input string if no brackets are found.

    Operation:
    1. Find the index of the first occurrence of '{' in the string.
    2. Find the index of the first occurrence of '[' in the string.
    3. Determine which character, '{' or '[', appears first in the string:
    3.1 If '{' appears before '[' or '[' is not found, extract the content within the first '{}' found in the string.
    3.2 If '[' appears before '{' or '{' is not found, extract the content within the first '[]' found in the string.
    3.3 If neither '{' nor '[' is found, return the entire input string.
    4. Return the extracted matched substring.
    """

    # Find the first occurrence of '{' or '['
    index_curly = string.find("{")
    index_square = string.find("[")

    # Determine which character comes first
    if 0 <= index_curly < index_square or (index_curly != -1 and index_square == -1):
        # Extract and evaluate content within {}
        match = re.search(r"\{([^\}]*)\}", string).group(0)
    elif 0 <= index_square < index_curly or (index_square != -1 and index_curly == -1):
        # Extract and evaluate content within []
        match = re.search(r"\[([^\]]*)\]", string).group(0)
    else:
        # No brackets or braces found
        match = string

    return match


def _add_comma_between_quotes(json_string):
    """
    Inputs:
    - json_string (str): The input JSON string with potential issues of missing commas between double quotes.

    Outputs:
    - fixed_json_string (str): The JSON string with commas correctly added between double quotes.

    Operation:
    1. Define a regular expression pattern to find two double quotes with spaces in between.
    2. Define a function 'replace_with_comma' to replace the found pattern with a comma:
    2.1 Capture the space between the quotes.
    2.2 Return the quotes with the captured space followed by a comma.
    3. Use 're.sub' to substitute the pattern in 'json_string' with the result from 'replace_with_comma'.
    4. Return the fixed JSON string.
    """

    # Regular expression to find two double quotes with spaces in between
    pattern = r"\"(\s*)\""

    # Function to replace the found pattern with ","
    def replace_with_comma(match):
        # Get the space between the quotes
        space = match.group(1)
        return f'"{space}",'

    # Substitute the pattern with a comma using the replace function
    fixed_json_string = re.sub(pattern, replace_with_comma, json_string)

    return fixed_json_string


def _sanitize_string(value):
    # Use regex to remove control characters and non-printable characters
    # \p{C} matches invisible control characters and unused code points
    # Printable characters include letters, digits, punctuation, and spaces
    clean_val = re.sub(r"[\x00-\x1F]", "", value)
    return "".join(char for char in clean_val if ord(char) >= 32)
    # return value  # Return the value unchanged if it's not a string


def _postprocess_json_string(s):
    # Remove trailing commas from objects and arrays
    s = (
        s.replace("```", "")
        .replace("json", "")
        .replace("\n{", "{")
        .replace("\n", " ")
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("}\n", "}")
        .replace("\\xa0", "\\u00A0")
    )
    s = re.sub(r"\s+", " ", s).strip()
    s = _add_comma_between_quotes(s)
    s = _sanitize_string(s)

    return _extract_and_evaluate_first(s)


# Call ChatGPT with the given prompt, asynchronously.
async def call_chatgpt_async(
    semaphore: asyncio.Semaphore,
    session,
    message: List[Dict[str, str]],
    openai_model_name: str,
):
    """
    Inputs:
    - semaphore (asyncio.Semaphore): Semaphore to control the rate of concurrent requests.
    - session (aiohttp.ClientSession): The aiohttp session for making HTTP requests.
    - message (List[Dict[str, str]]): A list of message dictionaries to be sent to the OpenAI API.
    - openai_model_name (str): The name of the OpenAI model to use.

    Outputs:
    - gpt_extracted_infos (Dict): Extracted information from the OpenAI API response.

    Operation:
    1. Construct the payload with the model name and messages.
    2. Use the semaphore to limit concurrent requests.
    3. Make a POST request to the OpenAI API with the payload.
    4. Extract the response JSON content.
    5. Try to extract the output text from the response:
    5.1 If successful, assign the output text.
    5.2 If an exception occurs, print the error and set the output text to "{}".
    6. Post-process the output text using '_postprocess_json_string'.
    7. Try to evaluate the post-processed text as a Python literal or JSON:
    7.1 If successful, assign the evaluated content to 'gpt_extracted_infos'.
    7.2 If an exception occurs, print the error and set 'gpt_extracted_infos' to an empty dictionary.
    8. Return the extracted information.
    """

    payload = {"model": openai_model_name, "messages": message}
    async with semaphore:
        async with session.post(
            url="https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}",
            },
            json=payload,
            ssl=ssl.create_default_context(cafile=certifi.where()),
        ) as response:
            clean_response = await response.json()

        try:
            output_text = clean_response["choices"][0]["message"]["content"]
            # print("Worked")
        except Exception as e:
            logger.error("GPT running failed", e, clean_response)
            output_text = "{}"

        output_text = _postprocess_json_string(output_text)

        try:
            gpt_extracted_infos = literal_eval(output_text)
        except Exception:
            try:
                gpt_extracted_infos = json.loads(output_text)
            except Exception as e:
                logger.error("formatting failed", e, output_text)
                gpt_extracted_infos = {}

    return gpt_extracted_infos


# Call chatGPT for all the given prompts in parallel.
async def call_chatgpt_bulk(
    messages: List[List[Dict[str, str]]],
    openai_model_name: str,
    rate_limit: int = 1,
):
    """
    Inputs:
    - messages (List[List[Dict[str, str]]]): A list of lists of message dictionaries to be sent to the OpenAI API.
    - openai_model_name (str): The name of the OpenAI model to use.
    - rate_limit (int): The maximum number of concurrent requests (default is 1).

    Outputs:
    - responses (List[Dict]): A list of responses from the OpenAI API.

    Operation:
    1. Initialize a semaphore to control the concurrency level.
    2. Create an aiohttp client session for making HTTP requests.
    3. Create a tqdm progress bar to track the progress of the tasks.
    4. Define an asynchronous function 'wrapped_call' that:
    4.1 Makes a call to 'call_chatgpt_async' with the given parameters.
    4.2 Updates the progress bar after each completed task.
    5. Use an asyncio TaskGroup to manage the asynchronous tasks:
    5.1 Create and gather tasks for each message in 'messages' using 'wrapped_call'.
    6. Close the progress bar after all tasks are completed.
    7. Return the list of responses from the OpenAI API.
    """

    semaphore = asyncio.Semaphore(rate_limit)  # Control concurrency level
    async with aiohttp.ClientSession() as session:
        # Create a tqdm async progress bar
        progress_bar = tqdm(total=len(messages), desc="Generating report summaries", position=0)

        async def wrapped_call(session, message):
            # Wrap your call in a function that updates the progress bar
            try:
                return await call_chatgpt_async(
                    semaphore,
                    session,
                    message,
                    openai_model_name=openai_model_name,
                )
            finally:
                progress_bar.update(1)  # Update the progress for each completed task

        # Use asyncio.TaskGroup for managing tasks
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(wrapped_call(session, message)) for message in messages]
            responses = await asyncio.gather(*tasks)

        # Ensure the progress bar closes properly
        progress_bar.close()

    return responses


def _generate_general_summary(df: pd.DataFrame) -> str:
    """
    Inputs:
    - df (pd.DataFrame): DataFrame containing the columns 'entries', 'country', 'breakdown_column', and 'possible_value'.

    Outputs:
    - answers (List[str]): List of responses from the OpenAI API.

    Operation:
    1. Initialize an empty list 'messages' to store the message prompts.
    2. Iterate through each row in the DataFrame:
    2.1 Extract 'entries', 'country', 'breakdown_column', and 'possible_value' from the row.
    2.2 Determine the appropriate prompt based on 'possible_value' and 'breakdown_column':
        - If 'possible_value' is "Country Wide", use 'general_summary_prompt' with the 'country'.
        - If 'breakdown_column' is "Geolocation", use 'geolocation_prompt' with the 'country' and 'possible_value'.
        - If 'breakdown_column' is "Indicator", use 'indicators_prompt' with the 'country' and 'possible_value'.
        - If 'breakdown_column' is "Targeting Specific Population Groups",
          use 'specific_population_groups_prompt' with the 'country' and 'possible_value'.
    2.3 Append the system and user messages to the 'messages' list. The user message contains the 'entries' in JSON format.
    3. Call 'call_chatgpt_bulk' with the 'messages' list and 'model_name' to get the responses from the OpenAI API.
    4. Return the list of responses.
    """

    messages = []
    for i, row in df.iterrows():
        single_entries: List[str] = row["entries"]
        country: str = row["country"]
        breakdown_column: str = row["Breakdown Column"]
        possible_value: str = row["Value"]

        if possible_value == "Country Wide":
            used_prompt = general_summary_prompt % (country)
        elif breakdown_column == "Geolocation":
            used_prompt = geolocation_prompt % (country, possible_value)
        elif breakdown_column == "Indicator":
            used_prompt = indicators_prompt % (country, possible_value)
        elif breakdown_column == "Targeting Specific Population Groups":
            used_prompt = specific_population_groups_prompt % (country, possible_value)

        messages.append(
            [
                {
                    "role": "system",
                    "content": used_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps({entry_id: entry["text"] for entry_id, entry in enumerate(single_entries)}),
                },
            ]
        )

    answers = asyncio.run(
        call_chatgpt_bulk(
            messages,
            openai_model_name=model_name,
        )
    )
    return answers
