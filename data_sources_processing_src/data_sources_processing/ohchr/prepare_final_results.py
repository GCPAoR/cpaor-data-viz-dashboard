import argparse
import asyncio
import json
import logging
import os

import pandas as pd
import torch
from nltk.tokenize import word_tokenize
from summaries_generation_utils.generate_embeddings import EmbeddingsGenerator, _generate_embeddings
from summaries_generation_utils.openai_async import call_chatgpt_bulk
from summaries_generation_utils.utils import _flatten_list_of_lists, _load_preprocess_df, _load_tags
from tqdm import tqdm

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

openai_model_name = "gpt-4o"


entry_extraction_system_prompt = """
I will provide you with a dictionary of sentences where the keys are the indices of the sentences and the values are the sentences themselves.
You will provide me with a list of indices of the sentences that explicitely treats this exact topic: %s, and the following country: %s, and no other topic or country. I want all actions, laws taken to deal with issues, and not statistics or specific events. Do not return any other irrelevant information.
Do not deviate from the needed format and provided country and do not return any unsure information. An example of the needed format is as follows: [1, 2]. If no sentences are surely relevant, provide an empty list.
"""

law_extraction_system_prompt = """I'm going to provide you with some text from different documents.
The text is provided as a list of dictionaries, where each dictionary contains the following keys: "Publishing Date", "Text".
I want you to create a summary specifically on the following topic: %s and the following country: %s. Use only text that explicitly treats this exact topic, and not any other. Do not return any other irrelevant information.
Restrict the output to the provided topic and country and do not return any unsure information. Focus only on laws, articles, legislations, etc. Only report the law themselves, without going into too much detail. The objective is just to have a general overview of the laws in place.
Text from the most recent dates should be prioritized. When an information is mentioned, its publishing date should be added just after the information is mentioned.
Do not add any information more than the provided one. Only provide the needed text, without headers or footers.
If you can't find any surely relevant information, provide an empty string. No matter the input language, the output should be in English."""

general_summary_system_prompt = """I'm going to provide you with some text from different documents.
The text is provided as a list of dictionaries, where each dictionary contains the following keys: "Publishing Date", "Text".
I want you to create a summary specifically on the following topic: %s and the following country: %s. Use only text that explicitly treats this exact topic, and not any other. Do not return any other irrelevant information.
Restrict the output to the provided topic and country and do not return any unsure information. Focus only on general actions being taken to address the issue. Disregard single events or statistics. Keep output concise and to the point.
Text from the most recent dates should be prioritized. When an information is mentioned, its publishing date should be added just after the information is mentioned.
Do not add any information more than the provided one. Only provide the needed text, without headers or footers.
If you can't find any surely relevant information, provide an empty string. No matter the input language, the output should be in English."""

ohchr_data_path = os.path.join("/data", "datasources", "ohchr")


def _create_empty_df(indicator: str):
    return pd.DataFrame(
        {
            "Indicator": indicator,
            "General Summary": "-",
            "Laws Summary": "No Information Available",
            "Symbol/Title": "-",
            "Number of Relevant Sentences": 0,
            "Title": "-",
            "Submitted Date": "-",
            "Download Link": "-",
            "doc_link": "-",
            "Extracted Infos": "-",
        },
        index=[0],
    )


class ResultsGenerator:
    def __init__(
        self,
        sample,
        n_most_simialr_entries,
        n_grouped_sentences,
    ):
        self.input_file_path = os.path.join(ohchr_data_path, "input_data", "all-docs.csv")
        self.n_most_simialr_entries = n_most_simialr_entries
        self.n_grouped_sentences = n_grouped_sentences
        self.tags_list = _load_tags()
        self.embeddings_generator = EmbeddingsGenerator()

        self.input_file = _load_preprocess_df(self.input_file_path, n_grouped_sentences)
        self.processed_countries = self.input_file["Country"].unique()

        self.output_folder_path = os.path.join(ohchr_data_path, "results")
        os.makedirs(self.output_folder_path, exist_ok=True)

        if sample:
            self.processed_countries = ["Haiti"]

        self.processed_countries = [
            one_country
            for one_country in self.processed_countries
            if not os.path.exists(os.path.join(self.output_folder_path, f"{one_country}.xlsx"))
        ]

    def _generate_general_summary(self, df: pd.DataFrame, prompt: str, one_indicator: str, one_country: str) -> str:
        sentences = json.dumps(
            [
                {
                    "Publishing Date": row["Submitted Date"],
                    "Text": row["Extracted Infos"],
                }
                for i, row in df.iterrows()
            ]
        )
        messages = [
            [
                {
                    "role": "system",
                    "content": prompt % (one_indicator, one_country),
                },
                {
                    "role": "user",
                    "content": sentences,
                },
            ]
        ]
        answers = asyncio.run(
            call_chatgpt_bulk(
                messages,
                response_type="summary",
                country=one_country,
                openai_model_name=openai_model_name,
            )
        )
        return answers[0]

    def _get_most_relevant_df(self, df: pd.DataFrame, one_indicator: str):
        """
        Inputs:
            - df (pd.DataFrame): DataFrame with document embeddings.
            - one_indicator (str): The indicator for which to find the most relevant entries.

        Outputs:
            - pd.DataFrame: DataFrame containing the most relevant entries based on the indicator.

        Operations:
            1. Generate embeddings for the indicator query.
            2. Convert document embeddings from the DataFrame into a tensor.
            3. Compute the similarity between document embeddings and indicator embeddings.
            4. Sort the similarities in descending order to find the most similar entries.
            5. Select the top entries based on similarity and return them as a DataFrame.
        """

        df_one_country = df.copy()

        one_indicator_embeddings = self.embeddings_generator([f"query: {one_indicator}"])
        inputs_embeddings = torch.tensor(df_one_country["Embeddings"].tolist(), dtype=torch.float16)
        embedding_similarity = (
            torch.matmul(
                inputs_embeddings.float(),
                one_indicator_embeddings.T.float(),
            )
            .reshape(-1)
            .squeeze()
        )

        # descending argsort to get the most similar embeddings
        most_similar_indices = torch.argsort(embedding_similarity, descending=True)[: self.n_most_simialr_entries]

        most_relevant_df = df_one_country.iloc[most_similar_indices]
        return most_relevant_df

    def _create_indicator_wise_relevant_entries_df(self, df: pd.DataFrame, country: str):
        """
        Inputs:
            - df (pd.DataFrame): DataFrame with document and indicator information.
            - country (str): The country for which to create the relevant entries DataFrame.

        Outputs:
            - pd.DataFrame: DataFrame with indicator-wise relevant entries and extracted information.

        Operations:
            1. Copy the input DataFrame for processing.
            2. Generate embeddings for the DataFrame using an embeddings generator.
            3. Initialize an empty DataFrame and list for messages.
            4. For each tag and its indicators:
                a. Create a DataFrame specific to the indicator.
                b. Get the most relevant entries for the indicator.
                c. Concatenate the results to the final DataFrame.
                d. Prepare messages for ChatGPT based on relevant entries.
            5. Call ChatGPT in bulk to extract relevant information.
            6. Update the final DataFrame with extracted information from ChatGPT responses.
            7. Return the DataFrame with relevant entries and extracted information.
        """

        df_one_country = df.copy()

        df_one_country = _generate_embeddings(df_one_country, self.embeddings_generator)

        final_df = pd.DataFrame()
        messages = []
        for one_tag, one_tag_indicators in tags_list.items():
            for one_indicator_id, one_indicator in enumerate(one_tag_indicators):
                df_one_country_one_indicator = df_one_country.copy()
                df_one_country_one_indicator["Indicator"] = one_indicator

                most_relevant_df = self._get_most_relevant_df(df_one_country_one_indicator, one_indicator)

                final_df = pd.concat([final_df, most_relevant_df])

                messages_one_country_indicator = [
                    [
                        {
                            "role": "system",
                            "content": entry_extraction_system_prompt % (one_indicator, country),
                        },
                        {
                            "role": "user",
                            "content": json.dumps({i: sent for i, sent in enumerate(row["Sentences Groups"])}),
                        },
                    ]
                    for i, row in most_relevant_df.iterrows()
                ]

                messages.extend(messages_one_country_indicator)

        answers = asyncio.run(
            call_chatgpt_bulk(
                messages,
                response_type="extraction",
                country=country,
                openai_model_name=openai_model_name,
            )
        )

        final_extracted_infos = []
        for i, (_, row) in enumerate(final_df.iterrows()):
            row_extracted_infos = []
            for relevant_id in answers[i]:
                row_extracted_infos.append(row["Sentences Groups"][relevant_id])
            final_extracted_infos.append(row_extracted_infos)

        final_df["Extracted Infos"] = final_extracted_infos

        return final_df

    def _get_law_summary(self, df: pd.DataFrame, one_indicator: str, one_country: str):
        """
        Inputs:
            - df (pd.DataFrame): DataFrame containing document and indicator information.
            - one_indicator (str): The specific indicator for which to generate the summary.
            - one_country (str): The country for which to generate the summary.

        Outputs:
            - pd.DataFrame: DataFrame containing the law summary for the specified indicator and country.

        Operations:
            1. Filter the DataFrame for the specific country and indicator.
            2. Remove rows with empty extracted information and explode lists into separate rows.
            3. Group by relevant columns and aggregate extracted information into lists.
            4. Calculate the number of relevant sentences.
            5. Generate a law summary or general summary based on the extracted text.
            6. Return a DataFrame with summaries and indicator information or an empty DataFrame
               if no relevant data is found.
        """

        most_relevant_df = df[(df["Country"] == one_country) & (df["Indicator"] == one_indicator)].copy()
        most_relevant_df = most_relevant_df[most_relevant_df["Extracted Infos"].apply(len) > 0]
        most_relevant_df = most_relevant_df.explode("Extracted Infos")

        most_relevant_df = most_relevant_df.groupby(
            [
                "Title",
                "Symbol/Title",
                "Submitted Date",
                "Download Link",
                "doc_link",
            ],
            as_index=False,
        ).agg(
            {
                "Extracted Infos": lambda x: list(x),
            }
        )

        most_relevant_df["Number of Relevant Sentences"] = most_relevant_df["Extracted Infos"].apply(len)

        most_relevant_df = most_relevant_df[most_relevant_df["Number of Relevant Sentences"] > 0]

        if len(most_relevant_df) > 0:
            # Extracting the law summary
            law_summary = self._generate_general_summary(
                most_relevant_df,
                law_extraction_system_prompt,
                one_indicator,
                one_country,
            )
            if len(word_tokenize(law_summary)) < 4:
                # if no Law summary, get general summary
                general_summary = self._generate_general_summary(
                    most_relevant_df,
                    general_summary_system_prompt,
                    one_indicator,
                    one_country,
                )
                if len(word_tokenize(general_summary)) > 4:
                    most_relevant_df["General Summary"] = general_summary
                    most_relevant_df["Laws Summary"] = "No Law Available Within the Legal Framework"
                    most_relevant_df["Indicator"] = one_indicator
                else:
                    most_relevant_df = _create_empty_df(one_indicator)

            else:
                most_relevant_df["General Summary"] = law_summary
                most_relevant_df["Laws Summary"] = "Law Available Within the Legal Framework"
                most_relevant_df["Indicator"] = one_indicator
        else:
            most_relevant_df = _create_empty_df(one_indicator)

        return most_relevant_df

    def generate_results(self):
        """
        Inputs:
            - None (Uses class attributes for data input and output paths.)

        Outputs:
            - None (Saves results to an Excel file.)

        Operations:
            1. Determine the total number of indicators from the flattened list.
            2. Filter the input DataFrame to include only rows for processed countries.
            3. For each processed country:
                a. Initialize an empty DataFrame for final results.
                b. Filter data for the current country and create relevant entries DataFrame.
                c. Iterate over tags and indicators:
                    i. Generate summary DataFrame for each indicator.
                    ii. Append the summary DataFrame to the final results.
                    iii. Save the results to an Excel file.
                d. Update progress bar after processing each indicator.
        """

        n_tot_indicators = len(_flatten_list_of_lists(list(tags_list.values())))

        df_countries = self.input_file.copy()
        df_countries = df_countries[df_countries["Country"].isin(self.processed_countries)].copy()

        for one_country in self.processed_countries:
            logger.info(
                f"--------------------------------------  Processing {one_country}  --------------------------------------"
            )

            final_df_one_country = pd.DataFrame()

            df_one_country = df_countries[df_countries["Country"] == one_country].copy()
            df_one_country = self._create_indicator_wise_relevant_entries_df(df_one_country, country=one_country)

            progress_bar = tqdm(
                total=n_tot_indicators,
                desc=f"Processing Indicators for {one_country}",
            )

            for one_tag, one_tag_indicators in tags_list.items():
                for one_indicator_id, one_indicator in enumerate(one_tag_indicators):
                    one_indicator_summary_df = self._get_law_summary(df_one_country, one_indicator, one_country)
                    one_indicator_summary_df["Tag"] = one_tag

                    # now all the data is ready to be saved in a csv file
                    final_df_one_country = pd.concat([final_df_one_country, one_indicator_summary_df])

                    saved_df = final_df_one_country.copy()
                    saved_df = saved_df.set_index(
                        [
                            "Tag",
                            "Indicator",
                            "General Summary",
                            "Laws Summary",
                            "Symbol/Title",
                        ]
                    )
                    saved_df.to_excel(
                        os.path.join(
                            self.output_folder_path,
                            f"{one_country}.xlsx",
                        ),
                        engine="openpyxl",
                    )

                    progress_bar.update(1)


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--use_sample", type=str, required=True)
    args.add_argument("--n_most_simialr_entries", type=int, default=15)
    args.add_argument("--n_grouped_sentences", type=int, default=4)
    args = args.parse_args()

    sample_bool = args.use_sample == "true"

    tags_list = _load_tags()

    results_generator = ResultsGenerator(
        sample_bool,
        args.n_most_simialr_entries,
        args.n_grouped_sentences,
    )
    results_generator.generate_results()
