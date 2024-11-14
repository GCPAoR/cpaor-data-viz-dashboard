import os
import asyncio
import json
import logging
import re
import ssl
from ast import literal_eval
from typing import Dict, List, Literal

import aiohttp
import certifi
import dotenv
from tqdm import tqdm

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


def _extract_and_evaluate_first(string):
    """
    Inputs:
    - string (str): The input string to search for the first occurrence of '{' or '['.

    Outputs:
    - match (str): The first matched substring enclosed within '{}' or '[]',
      or the entire input string if no brackets are found.

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


# Call ChatGPT with the given prompt, asynchronously.
async def call_chatgpt_async(
    semaphore: asyncio.Semaphore,
    session,
    message: List[Dict[str, str]],
    openai_model_name: str,
    response_type: Literal["extraction", "summary"],
):
    """
    Inputs:
    - semaphore (asyncio.Semaphore): Semaphore to control the rate of concurrent requests.
    - session (aiohttp.ClientSession): The aiohttp session for making HTTP requests.
    - message (List[Dict[str, str]]): A list of message dictionaries to be sent to the OpenAI API.
    - openai_model_name (str): The name of the OpenAI model to use.
    - response_type (Literal["extraction", "summary"]): Type of response expected ("extraction" or "summary").

    Outputs:
    - gpt_extracted_infos (Union[List, str]): Extracted information if
      response_type is "extraction", otherwise the response text.

    Operation:
    1. Construct the payload with the model name and messages.
    2. Use the semaphore to limit concurrent requests.
    3. Make a POST request to the OpenAI API with the payload.
    4. If the request is successful, extract the output text from the response.
    5. If an exception occurs, print the error and set default values based on response_type.
    6. If response_type is "extraction":
    6.1 Post-process the output text.
    6.2 Try to evaluate the post-processed text as a Python literal or JSON.
    6.3 If evaluation fails, set the extracted information to an empty list.
    7. If response_type is "summary", set the extracted information to the output text.
    8. Return the extracted information.
    """

    payload = {"model": openai_model_name, "messages": message}
    async with semaphore:
        try:
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

                output_text = clean_response["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"GPT running failed. {str(e)} {clean_response}")
            # assert False, "GPT running failed"
            if response_type == "extraction":
                output_text = "[]"
            else:
                output_text = ""

        if response_type == "extraction":
            output_text = _postprocess_json_string(output_text)

            try:
                gpt_extracted_infos = literal_eval(output_text)
            except Exception:
                try:
                    gpt_extracted_infos = json.loads(output_text)
                except Exception as e:
                    logger.error(f"formatting failed.{str(e)}. {output_text}")
                    gpt_extracted_infos = []
        else:
            gpt_extracted_infos = output_text

    return gpt_extracted_infos


# Call chatGPT for all the given prompts in parallel.
async def call_chatgpt_bulk(
    messages: List[List[Dict[str, str]]],
    response_type: Literal["extraction", "summary"],
    openai_model_name: str,
    country: str,
    rate_limit: int = 1,
):
    """
    Inputs:
    - messages (List[List[Dict[str, str]]]): A list of message lists, where each message is a dictionary.
    - response_type (Literal["extraction", "summary"]): Type of response expected ("extraction" or "summary").
    - openai_model_name (str): The name of the OpenAI model to use.
    - country (str): Name of the country for context in the progress bar description.
    - rate_limit (int, optional): Maximum number of concurrent requests (default is 1).

    Outputs:
    - responses (List): List of responses from the asynchronous calls to ChatGPT.

    Operation:
    1. Assert that the response_type is either "extraction" or "summary".
    2. Initialize a semaphore to control the concurrency level.
    3. Create an aiohttp ClientSession for making asynchronous HTTP requests.
    4. Initialize a tqdm progress bar if the response_type is "extraction".
    5. Define an async function 'wrapped_call' to make the asynchronous call and update the progress bar.
    6. Create and manage tasks using asyncio.TaskGroup to call 'wrapped_call' for each message in the messages list.
    7. Gather all the responses from the tasks.
    8. Ensure the progress bar is closed properly.
    9. Return the list of responses.
    """

    assert response_type in ["extraction", "summary"]
    semaphore = asyncio.Semaphore(rate_limit)  # Control concurrency level
    async with aiohttp.ClientSession() as session:
        # Create a tqdm async progress bar
        if response_type == "extraction":
            progress_bar = tqdm(
                total=len(messages),
                desc=f"Generating Extraction results for {country}",
                position=0,
            )
        else:
            progress_bar = None

        async def wrapped_call(session, message):
            # Wrap your call in a function that updates the progress bar
            try:
                return await call_chatgpt_async(
                    semaphore,
                    session,
                    message,
                    openai_model_name=openai_model_name,
                    response_type=response_type,
                )

            finally:
                if progress_bar:
                    progress_bar.update(
                        1
                    )  # Update the progress for each completed task

        # Use asyncio.TaskGroup for managing tasks
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(wrapped_call(session, message)) for message in messages
            ]
            responses = await asyncio.gather(*tasks)

        # Ensure the progress bar closes properly
        if progress_bar:
            progress_bar.close()

    return responses
